import asyncio
import re
import uuid
from typing import Any, Dict, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import get_settings, Settings
from app.core.exceptions import (
    DownloadAgentException,
    FileSystemException,
    MediaResolutionException,
    UpstreamAPIException,
    ValidationException
)
from app.core.logging import get_logger
from app.schemas.download import DownloadRequest, DownloadResponse, JobProgressResponse, JobStatus
from app.services.job_service import JobService, get_job_service
from app.services.pw_content_service import get_lecture_details
from app.services.pw_media_service import fetch_decryption_key
from app.services.downloader_service import DownloaderService

logger = get_logger("routes.download")
router = APIRouter(prefix="/download", tags=["downloads"])
security = HTTPBearer()
settings = get_settings()

SAFE_FILENAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-\. ]+$")
active_tasks: Dict[str, asyncio.Task] = {}

def sanitize_and_validate_filename(filename: str) -> str:
    if not filename:
        raise ValidationException("Filename cannot be empty.")
    if len(filename) > 100:
        raise ValidationException("Filename exceeds maximum length of 100 characters.")
    if ".." in filename or "/" in filename or "\\" in filename or "\0" in filename:
        raise ValidationException("Path traversal or directory creation elements are forbidden in filename.")
    if not SAFE_FILENAME_REGEX.match(filename):
        raise ValidationException(
            "Filename contains invalid characters. Only alphanumeric, spaces, dots, dashes, and underscores are allowed."
        )
    sanitized = filename.strip(" .")
    if not sanitized:
        raise ValidationException("Filename must contain valid alphanumeric characters.")
    return sanitized

async def run_background_download(
    job_id: str,
    video_id: str,
    video_url: str,
    batch_id: str,
    file_name: str,
    token: str,
    random_id: str,
    app_state: Any,
    job_service: JobService
) -> None:
    semaphore: asyncio.Semaphore = app_state.download_semaphore
    client = app_state.http_client
    downloader = DownloaderService(job_service)

    logger.info(f"Background task started for job {job_id}. Waiting for semaphore.")
    try:
        async with semaphore:
            logger.info(f"Semaphore acquired for job {job_id}. Status -> RUNNING.")
            await job_service.update_job(
                job_id=job_id,
                status=JobStatus.RUNNING,
                progress_percent=2.0,
                stage="Acquired download slot, parsing manifest"
            )

            await job_service.update_job(
                job_id=job_id,
                progress_percent=10.0,
                stage="Fetching and parsing DASH manifest"
            )
            manifest_url = video_url
            parser = None
            try:
                parser = await downloader.fetch_and_parse_manifest(client, manifest_url)
            except MediaResolutionException as exc:
                logger.info(f"Direct manifest fetch failed. Attempting to resolve signed URL from Penpencil API using batch_id={batch_id}.")
                try:
                    secondary_parent_id = ""
                    if "cloudfront.net" in video_url:
                        parts = video_url.split("/")
                        if len(parts) > 3:
                            secondary_parent_id = parts[3]
                    
                    details = await get_lecture_details(
                        client=client,
                        token=token,
                        random_id=random_id,
                        video_id=video_id,
                        batch_id=batch_id,
                        video_url=video_url,
                        secondary_parent_id=secondary_parent_id,
                        lecture_type="BATCHES"
                    )
                    url_base = details.get("url") or details.get("signedUrl") or details.get("videoUrl")
                    if url_base:
                        signed_suffix = details.get("signedUrl") or ""
                        manifest_url = url_base
                        if signed_suffix and signed_suffix not in url_base:
                            manifest_url = f"{url_base}{signed_suffix}"
                        logger.info("Resolved signed URL from Penpencil API. Retrying manifest fetch...")
                        parser = await downloader.fetch_and_parse_manifest(client, manifest_url)
                    else:
                        raise MediaResolutionException("Upstream details response did not contain a valid video URL.")
                except Exception as fallback_exc:
                    logger.error(f"Fallback signature resolution failed: {fallback_exc}")
                    try:
                        logger.info("Attempting Khazana (RECORDED) fallback signature resolution...")
                        details = await get_lecture_details(
                            client=client,
                            token=token,
                            random_id=random_id,
                            video_id=video_id,
                            batch_id=batch_id,
                            video_url=video_url,
                            secondary_parent_id=secondary_parent_id,
                            lecture_type="RECORDED"
                        )
                        url_base = details.get("url") or details.get("signedUrl") or details.get("videoUrl")
                        if url_base:
                            signed_suffix = details.get("signedUrl") or ""
                            manifest_url = url_base
                            if signed_suffix and signed_suffix not in url_base:
                                manifest_url = f"{url_base}{signed_suffix}"
                            logger.info("Resolved signed URL from Penpencil API (RECORDED). Retrying manifest fetch...")
                            parser = await downloader.fetch_and_parse_manifest(client, manifest_url)
                        else:
                            raise MediaResolutionException("Upstream RECORDED details response did not contain a valid video URL.")
                    except Exception as recorded_fallback_exc:
                        logger.error(f"Khazana (RECORDED) fallback signature resolution failed: {recorded_fallback_exc}")
                        raise exc
            
            kid = parser.get_kid()
            quality_str = str(settings.DEFAULT_QUALITY)
            segment_urls = parser.get_segment_urls(quality=quality_str)

            decryption_key = None
            if kid:
                logger.info(f"DASH manifest has KID: {kid}. Initiating key exchange.")
                await job_service.update_job(
                    job_id=job_id,
                    progress_percent=15.0,
                    stage="Executing key exchange handshake"
                )
                decryption_key = await fetch_decryption_key(
                    client=client,
                    token=token,
                    random_id=random_id,
                    kid=kid
                )
            else:
                logger.info("No KID found in manifest. Skipping key exchange.")

            await job_service.update_job(
                job_id=job_id,
                progress_percent=20.0,
                stage="Downloading media segments"
            )
            try:
                audio_enc, video_enc = await downloader.download_pipeline(
                    client=client,
                    job_id=job_id,
                    segment_urls=segment_urls,
                    threads=settings.DEFAULT_THREADS
                )
            except Exception as download_exc:
                logger.error(f"Download pipeline failed: {download_exc}")
                raise download_exc

            if kid and decryption_key:
                audio_dec, video_dec = await downloader.decrypt_media(
                    job_id=job_id,
                    kid=kid,
                    key_string=decryption_key,
                    audio_enc=audio_enc,
                    video_enc=video_enc
                )
            else:
                logger.info("Skipping decryption stage because media is unencrypted.")
                await job_service.update_job(
                    job_id=job_id,
                    progress_percent=80.0,
                    stage="Skipping decryption (stream is unencrypted)"
                )
                audio_dec, video_dec = audio_enc, video_enc

            final_path = await downloader.merge_media(
                job_id=job_id,
                audio_dec=audio_dec,
                video_dec=video_dec,
                final_file_name=file_name
            )

            await downloader.cleanup(job_id=job_id)
            
            await job_service.update_job(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                progress_percent=100.0,
                stage="Done"
            )
            logger.info(f"Job {job_id} successfully completed. File saved: {final_path}")

    except asyncio.CancelledError:
        logger.warning(f"Background download job {job_id} was cancelled.")
        await downloader.cleanup(job_id=job_id)
        await job_service.update_job(
            job_id=job_id,
            status=JobStatus.FAILED,
            error_message="Job was cancelled."
        )
        raise
    except DownloadAgentException as exc:
        logger.error(f"Download pipeline failed for job {job_id}: {exc.message}")
        await downloader.cleanup(job_id=job_id)
        await job_service.update_job(
            job_id=job_id,
            status=JobStatus.FAILED,
            error_message=exc.message
        )
    except Exception as exc:
        logger.error(f"Unhandled exception in background pipeline for job {job_id}: {exc}", exc_info=True)
        await downloader.cleanup(job_id=job_id)
        await job_service.update_job(
            job_id=job_id,
            status=JobStatus.FAILED,
            error_message=f"Internal Server Error: {str(exc)}"
        )
    finally:
        active_tasks.pop(job_id, None)

@router.post("", response_model=DownloadResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_download(
    request: Request,
    payload: DownloadRequest,
    auth: HTTPAuthorizationCredentials = Depends(security),
    job_service: JobService = Depends(get_job_service)
) -> DownloadResponse:
    token = auth.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid authorization bearer token required."
        )

    random_id = request.headers.get("randomid") or "a3e290fa-ea36-4012-9124-8908794c33aa"

    try:
        sanitized_filename = sanitize_and_validate_filename(payload.file_name)
    except ValidationException as exc:
        logger.warning(f"Validation failure for filename '{payload.file_name}': {exc.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message
        )

    job_id = str(uuid.uuid4())

    await job_service.create_job(
        job_id=job_id,
        video_id=payload.video_id,
        video_url=payload.video_url,
        batch_id=payload.batch_id,
        file_name=sanitized_filename
    )

    task = asyncio.create_task(
        run_background_download(
            job_id=job_id,
            video_id=payload.video_id,
            video_url=payload.video_url,
            batch_id=payload.batch_id,
            file_name=sanitized_filename,
            token=token,
            random_id=random_id,
            app_state=request.app.state,
            job_service=job_service
        )
    )
    active_tasks[job_id] = task

    return DownloadResponse(job_id=job_id)

@router.get("/{job_id}", response_model=JobProgressResponse)
async def get_job_status(
    job_id: str,
    job_service: JobService = Depends(get_job_service)
) -> JobProgressResponse:
    job = await job_service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )
    return job
