from pydantic import BaseModel, Field
from typing import Optional


class MessageData(BaseModel):
    message: str = Field(...)


class MessageResponse(BaseModel):
    success: bool = Field(...)
    data: MessageData = Field(...)
    error: Optional[str] = Field(None)
    status_code: int = Field(...)


class HealthData(BaseModel):
    status: str = Field(...)


class HealthResponse(BaseModel):
    success: bool = Field(...)
    data: HealthData = Field(...)
    error: Optional[str] = Field(None)
    status_code: int = Field(...)
