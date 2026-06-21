import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas.download import JobStatus, JobProgressResponse
from app.core.logging import get_logger

logger = get_logger("job_service")

class JobService:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobProgressResponse] = {}
        self._lock = asyncio.Lock()

    async def create_job(self, job_id: str, video_id: str, video_url: str, batch_id: str, file_name: str) -> JobProgressResponse:
        now = datetime.now(timezone.utc).isoformat()
        job = JobProgressResponse(
            job_id=job_id,
            video_id=video_id,
            video_url=video_url,
            batch_id=batch_id,
            file_name=file_name,
            status=JobStatus.QUEUED,
            progress_percent=0.0,
            stage="Queued in line",
            error_message=None,
            created_at=now,
            updated_at=now
        )
        async with self._lock:
            self._jobs[job_id] = job
            logger.info(f"Job {job_id} created for video {video_id} (status: QUEUED)")
        return job

    async def get_job(self, job_id: str) -> Optional[JobProgressResponse]:
        async with self._lock:
            return self._jobs.get(job_id)

    async def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress_percent: Optional[float] = None,
        stage: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[JobProgressResponse]:
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Attempted to update non-existent job: {job_id}")
                return None

            now = datetime.now(timezone.utc).isoformat()
            
            updated_data = job.model_dump()
            if status is not None:
                updated_data["status"] = status
            if progress_percent is not None:
                updated_data["progress_percent"] = max(0.0, min(100.0, progress_percent))
            if stage is not None:
                updated_data["stage"] = stage
            if error_message is not None:
                updated_data["error_message"] = error_message
            
            updated_data["updated_at"] = now

            updated_job = JobProgressResponse(**updated_data)
            self._jobs[job_id] = updated_job
            return updated_job

    async def list_jobs(self) -> List[JobProgressResponse]:
        async with self._lock:
            return list(self._jobs.values())

job_service_instance = JobService()

def get_job_service() -> JobService:
    return job_service_instance
