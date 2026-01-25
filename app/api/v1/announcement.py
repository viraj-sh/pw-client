from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from core.logging import setup_logging
from core.exceptions import handle_exception
from schema.pydantic_announcement import (
    StandardResponseModel,
)
from services.announcement import fetch_announcements

router = APIRouter(tags=["Announcement"], prefix="/announcement")
logger = setup_logging(name="Announcement", level="INFO")


@router.get(
    "/{batch_id}",
    response_model=StandardResponseModel,
    operation_id="fetchAnnouncements",
)
async def get_announcements(
    batch_id: str,
    page: int = Query(1, ge=1, description="Page number for pagination"),
    refetch: bool = Query(False, description="Bypass cache and refetch results"),
):
    logger = setup_logging(name="api.get_announcements")

    try:
        result = fetch_announcements(
            batch_id=batch_id,
            page=page,
            refetch=refetch,
        )
        return JSONResponse(
            content=result,
            status_code=result.get("status_code", 200),
        )

    except Exception as exc:
        error_resp = handle_exception(logger, exc, context="get_announcements")

        return JSONResponse(
            content=error_resp,
            status_code=error_resp.get("status_code", 500),
        )
