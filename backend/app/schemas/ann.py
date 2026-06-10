from typing import Optional

from pydantic import BaseModel, Field


class AnnResponse(BaseModel):
    id: str
    heading: Optional[str] = Field(default=None)
    announcement: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)
    schedule_time: Optional[str] = Field(default=None)
    use_case: Optional[str] = Field(default=None)
    url: Optional[str] = Field(default=None)
