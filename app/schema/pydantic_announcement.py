from typing import Optional, List
from pydantic import BaseModel, Field


class AnnouncementModel(BaseModel):
    announcement: Optional[str] = Field(None, description="Announcement text")
    my_id: Optional[str] = Field(None, description="Announcement ID")
    scheduleTime: Optional[str] = Field(None, description="Schedule timestamp")
    endlink: Optional[str] = Field(None, description="Attachment final URL")


class AnnouncementsDataModel(BaseModel):
    announcements: List[AnnouncementModel] = Field(
        default_factory=list, description="List of announcements"
    )


class StandardResponseModel(BaseModel):
    success: bool = Field(..., description="Indicates whether the request succeeded")
    error: Optional[str] = Field(None, description="Error message if any")
    data: Optional[AnnouncementsDataModel] = Field(
        None, description="Payload containing announcements list"
    )
    status_code: int = Field(..., description="HTTP status code")
