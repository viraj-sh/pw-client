import asyncio
import os
import re
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import xmltodict

import httpx
from app.core.config import get_settings
from app.core.exceptions import FileSystemException, MediaResolutionException
from app.core.logging import get_logger
from app.services.job_service import JobService
from app.schemas.download import JobStatus

logger = get_logger("downloader_service")
settings = get_settings()

class MPDParserHelper:
    def __init__(self, url: str, xml_text: str):
        self.url = url
        self.xml_text = xml_text
        self.base_url = ""
        self.signature = ""
        self.mpd_dict: Dict[str, Any] = {}

        if "?" in self.url:
            self.base_url, self.signature = self.url.split("?", 1)
            if self.base_url.endswith("/master.mpd"):
                self.base_url = self.base_url.split("master.mpd")[0]
        else:
            self.base_url = self.url.rsplit('/', 1)[0] + "/"
            if self.base_url.endswith("master.mpd/"):
                self.base_url = self.base_url.split("master.mpd/")[0]

        try:
            self.mpd_dict = xmltodict.parse(self.xml_text, process_namespaces=False)
        except Exception as e:
            logger.error(f"Failed to parse XML: {e}")
            raise MediaResolutionException(f"Invalid DASH manifest XML: {e}")

    def get_kid(self) -> Optional[str]:
        pattern = r'default_KID="([0-9a-fA-F-]+)"'
        match = re.search(pattern, self.xml_text)
        return match.group(1) if match else None

    def _build_url(self, media_path: str, segment_number: Optional[int] = None) -> str:
        base = self.base_url if self.base_url.endswith('/') else f"{self.base_url}/"
        media = media_path[1:] if media_path.startswith('/') else media_path
        full_url = f"{base}{media}"
        
        if segment_number is not None:
            full_url = full_url.replace("$Number$", str(segment_number))
            
        return f"{full_url}?{self.signature}" if self.signature else full_url

    def _get_adaptation_set(self, content_type: str) -> Dict[str, Any]:
        try:
            period = self.mpd_dict["MPD"]["Period"]
            adaptation_sets = period["AdaptationSet"]
            if not isinstance(adaptation_sets, list):
                adaptation_sets = [adaptation_sets]
            
            for a_set in adaptation_sets:
                if a_set.get("@contentType") == content_type:
                    return a_set
        except KeyError as e:
            raise MediaResolutionException(f"Missing expected XML element in DASH Period: {e}")
        
        raise MediaResolutionException(f"{content_type.capitalize()} adaptation set not found in MPD.")

    def _get_segment_template_info(self, adaptation_set: Dict[str, Any], target_height: str) -> Tuple[Dict, int, str, str]:
        representations = adaptation_set.get("Representation", [])
        if not isinstance(representations, list):
            representations = [representations]

        selected_rep = representations[0]
        if adaptation_set.get("@contentType") == "video":
            for rep in representations:
                if rep.get("@height") == target_height:
                    selected_rep = rep
                    break

        template = selected_rep.get("SegmentTemplate")
        if not template:
            raise MediaResolutionException("SegmentTemplate not found in DASH representation.")

        try:
            start_number = int(template.get("@startNumber", 1))
            init = template.get("@initialization")
            media = template.get("@media")
        except (ValueError, TypeError) as e:
            raise MediaResolutionException(f"Invalid SegmentTemplate attributes: {e}")
        
        return template, start_number, init, media

    def get_segment_urls(self, quality: str = "720") -> Dict[str, Any]:
        urls = {
            'video': {'init': None, 'segments': {}},
            'audio': {'init': None, 'segments': {}}
        }

        v_set = self._get_adaptation_set("video")
        v_template, v_start, v_init, v_media = self._get_segment_template_info(v_set, quality)
        urls['video']['init'] = self._build_url(v_init)
        
        v_timeline = v_template.get("SegmentTimeline", {}).get("S", [])
        if not isinstance(v_timeline, list):
            v_timeline = [v_timeline]
            
        v_end = 0
        for s in v_timeline:
            v_end += int(s.get("@r", 0)) + 1
            
        for i in range(v_start, v_end + v_start):
            urls['video']['segments'][i] = self._build_url(v_media, i)

        a_set = self._get_adaptation_set("audio")
        a_template, a_start, a_init, a_media = self._get_segment_template_info(a_set, target_height="")
        urls['audio']['init'] = self._build_url(a_init)
        
        a_timeline = a_template.get("SegmentTimeline", {}).get("S", [])
        if not isinstance(a_timeline, list):
            a_timeline = [a_timeline]
            
        a_end = 0
        for s in a_timeline:
            a_end += int(s.get("@r", 0)) + 1

        for i in range(a_start, a_end + a_start):
            urls['audio']['segments'][i] = self._build_url(a_media, i)

        return urls


async def download_segment_file(
    client: httpx.AsyncClient,
    url: str,
    path: Path,
    semaphore: asyncio.Semaphore
) -> None:
    async with semaphore:
        for attempt in range(3):
            try:
                async with client.stream("GET", url, timeout=settings.REQUEST_TIMEOUT_SECONDS) as response:
                    if response.status_code != 200:
                        raise httpx.HTTPStatusError(
                            f"Non-200 status code: {response.status_code}",
                            request=response.request,
                            response=response
                        )
                    
                    temp_path = path.with_suffix(".tmp")
                    with open(temp_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=16384):
                            f.write(chunk)
                    
                    temp_path.rename(path)
                    return
            except (httpx.HTTPError, OSError) as exc:
                logger.warning(f"Attempt {attempt + 1} failed to download segment {url}: {exc}")
                if attempt == 2:
                    raise FileSystemException(f"Failed to download segment after 3 attempts: {url}")
                await asyncio.sleep(1.0)


async def execute_subprocess(cmd: List[str], description: str) -> None:
    logger.info(f"Running subprocess command: {' '.join(cmd)}")
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            err_msg = stderr.decode().strip() or stdout.decode().strip()
            logger.error(f"{description} failed with return code {process.returncode}: {err_msg}")
            raise FileSystemException(f"{description} failed: {err_msg}")
    except FileNotFoundError as exc:
        logger.error(f"{cmd[0]} binary not found: {exc}")
        raise FileSystemException(f"Required binary '{cmd[0]}' was not found on the system PATH.")


class DownloaderService:
    def __init__(self, job_service: JobService) -> None:
        self.job_service = job_service

    async def fetch_and_parse_manifest(
        self,
        client: httpx.AsyncClient,
        manifest_url: str
    ) -> MPDParserHelper:
        try:
            logger.info(f"Fetching DASH manifest from {manifest_url}")
            response = await client.get(manifest_url, timeout=settings.REQUEST_TIMEOUT_SECONDS)
            if response.is_error:
                raise MediaResolutionException(
                    f"Failed to fetch manifest (Status: {response.status_code})"
                )
            
            return MPDParserHelper(manifest_url, response.text)
        except httpx.RequestError as exc:
            raise MediaResolutionException(f"Network error fetching manifest: {exc}")

    async def download_pipeline(
        self,
        client: httpx.AsyncClient,
        job_id: str,
        segment_urls: Dict[str, Any],
        threads: int
    ) -> Tuple[Path, Path]:
        tmp_dir = settings.DOWNLOAD_PATH / f"tmp_{job_id}"
        audio_tmp = tmp_dir / "audio"
        video_tmp = tmp_dir / "video"
        audio_tmp.mkdir(parents=True, exist_ok=True)
        video_tmp.mkdir(parents=True, exist_ok=True)

        audio_data = segment_urls.get("audio", {})
        video_data = segment_urls.get("video", {})

        audio_segments = audio_data.get("segments", {})
        video_segments = video_data.get("segments", {})

        total_segments = len(audio_segments) + len(video_segments) + (2 if audio_data.get("init") and video_data.get("init") else 0)
        
        logger.info(f"Starting concurrent download of {total_segments} total segments (using {threads} workers)")
        
        segment_semaphore = asyncio.Semaphore(threads)
        tasks = []
        downloaded_count = 0
        progress_lock = asyncio.Lock()

        async def tracked_download(url: str, path: Path) -> None:
            nonlocal downloaded_count
            await download_segment_file(client, url, path, segment_semaphore)
            async with progress_lock:
                downloaded_count += 1
                pct = (downloaded_count / total_segments) * 70.0
                await self.job_service.update_job(
                    job_id=job_id,
                    progress_percent=pct,
                    stage=f"Downloading media segments ({downloaded_count}/{total_segments})"
                )

        if audio_data.get("init"):
            tasks.append(tracked_download(audio_data["init"], audio_tmp / "0000-audio-init.mp4"))
        if video_data.get("init"):
            tasks.append(tracked_download(video_data["init"], video_tmp / "0000-video-init.mp4"))

        for idx, url in audio_segments.items():
            tasks.append(tracked_download(url, audio_tmp / f"{int(idx):04d}-audio-segment.mp4"))

        for idx, url in video_segments.items():
            tasks.append(tracked_download(url, video_tmp / f"{int(idx):04d}-video-segment.mp4"))

        await asyncio.gather(*tasks)

        logger.info("All segments downloaded successfully. Concatenating files...")
        await self.job_service.update_job(
            job_id=job_id,
            progress_percent=70.0,
            stage="Concatenating downloaded chunks"
        )

        audio_enc_path = tmp_dir / "audio_enc.mp4"
        audio_files = sorted(audio_tmp.glob("*"))
        with open(audio_enc_path, "wb") as outfile:
            for f in audio_files:
                with open(f, "rb") as infile:
                    outfile.write(infile.read())

        video_enc_path = tmp_dir / "video_enc.mp4"
        video_files = sorted(video_tmp.glob("*"))
        with open(video_enc_path, "wb") as outfile:
            for f in video_files:
                with open(f, "rb") as infile:
                    outfile.write(infile.read())

        return audio_enc_path, video_enc_path

    async def decrypt_media(
        self,
        job_id: str,
        kid: str,
        key_string: str,
        audio_enc: Path,
        video_enc: Path
    ) -> Tuple[Path, Path]:
        await self.job_service.update_job(
            job_id=job_id,
            progress_percent=75.0,
            stage="Decrypting audio and video streams"
        )

        tmp_dir = settings.DOWNLOAD_PATH / f"tmp_{job_id}"
        audio_dec = tmp_dir / "audio_dec.mp4"
        video_dec = tmp_dir / "video_dec.mp4"

        cmd_audio = [
            settings.MP4DECRYPT_PATH,
            "--key",
            f"1:{key_string}",
            str(audio_enc),
            str(audio_dec)
        ]
        await execute_subprocess(cmd_audio, "Audio decryption")

        cmd_video = [
            settings.MP4DECRYPT_PATH,
            "--key",
            f"1:{key_string}",
            str(video_enc),
            str(video_dec)
        ]
        await execute_subprocess(cmd_video, "Video decryption")

        return audio_dec, video_dec

    async def merge_media(
        self,
        job_id: str,
        audio_dec: Path,
        video_dec: Path,
        final_file_name: str
    ) -> Path:
        await self.job_service.update_job(
            job_id=job_id,
            progress_percent=85.0,
            stage="Merging decrypted streams (remuxing)"
        )

        settings.DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
        final_output = settings.DOWNLOAD_PATH / f"{final_file_name}.mp4"

        cmd_merge = [
            settings.FFMPEG_PATH,
            "-y",
            "-i", str(video_dec),
            "-i", str(audio_dec),
            "-c", "copy",
            str(final_output)
        ]
        await execute_subprocess(cmd_merge, "Muxing streams")
        
        return final_output

    async def cleanup(self, job_id: str) -> None:
        tmp_dir = settings.DOWNLOAD_PATH / f"tmp_{job_id}"
        if tmp_dir.exists():
            try:
                await asyncio.to_thread(shutil.rmtree, tmp_dir)
                logger.info(f"Cleaned up temporary directory: {tmp_dir}")
            except OSError as e:
                logger.warning(f"Failed to clean up temporary directory {tmp_dir}: {e}")
