from fastapi import APIRouter
from fastapi.responses import FileResponse
from schema.pydantic_system import (
    MessageResponse,
    MessageData,
    HealthResponse,
    HealthData,
)
from pathlib import Path


router = APIRouter(tags=["System"])


@router.get(
    "/",
    summary="Root endpoint",
    response_model=MessageResponse,
    operation_id="get_system_info",
)
def home():
    return MessageResponse(
        success=True,
        data=MessageData(message="Unofficial PW API"),
        error=None,
        status_code=200,
    )


@router.get(
    "/health",
    summary="Health check",
    response_model=HealthResponse,
    operation_id="check_system_health",
)
def health_check():
    return HealthResponse(
        success=True,
        data=HealthData(status="OK"),
        error=None,
        status_code=200,
    )
