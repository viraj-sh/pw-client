from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class DownloadRequest(BaseModel):
    video_id: str = Field(..., description="The unique video ID / child ID to download.")
    video_url: str = Field(..., description="The direct video manifest URL (.mpd).")
    batch_id: str = Field(..., description="The batch ID / parent ID.")
    file_name: str = Field(..., description="The target output filename (without extension).")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "video_id": "65d75d320531c20018ade9bb",
                "video_url": "https://d1d34p8vz63oiq.cloudfront.net/1c585057-6886-4e4f-a955-e88bdcd82629/master.mpd",
                "batch_id": "65d75d320531c20018ade9b2",
                "file_name": "lecture_01"
            }
        }
    )

class DownloadResponse(BaseModel):
    job_id: str = Field(..., description="The unique UUID for the created download job.")

class JobProgressResponse(BaseModel):
    job_id: str
    video_id: str
    video_url: str
    batch_id: str
    file_name: str
    status: JobStatus
    progress_percent: float = Field(0.0, ge=0.0, le=100.0)
    stage: str = Field("Initializing")
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)
