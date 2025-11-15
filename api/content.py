from fastapi import APIRouter, Query, Body, Path
from fastapi.responses import JSONResponse
from typing import Optional
from core.utils import standard_response
from core.logging import setup_logging
from core.exceptions import handle_exception
from typing import Optional, Any, Dict
from schema.pydantic_content import GetBatchesResponse, StandardResponseModel, ChapterRequestModel, ChapterContentRequest, StandardResponse
from services.content import get_batches, get_sub, get_ch, get_ch_content


router = APIRouter(tags=["Content"], prefix="/content")
logger = setup_logging(name="Content", level="INFO")


@router.get(
    "/batches",
    response_model=GetBatchesResponse,
    operation_id="getUserBatches"
)
async def fetch_user_batches(
    amount: str = Query("", description="Filter for batch type: '', 'free', or 'paid'"),
    refetch: bool = Query(False, description="Bypass cache and refetch from API"),
):
    try:
        result = get_batches(amount=amount, refetch=refetch)
        return JSONResponse(content=result, status_code=result.get("status_code", 200))

    except Exception as exc:
        err_resp = handle_exception(logger, exc, context="fetch_user_batches")
        return JSONResponse(
            content=err_resp, status_code=err_resp.get("status_code", 500)
        )


@router.get(
    "/{batch_id}/subjects",
    response_model=StandardResponseModel,
    operation_id="get_batch_subjects",
)
def get_batch_subjects(
    batch_id: str,
    refetch: bool = Query(False, description="Bypass cache and force refetch"),
) -> Any:
    logger = setup_logging(name="api.get_batch_subjects")

    try:
        result = get_sub(batch_id=batch_id, refetch=refetch)

        if not isinstance(result, dict):
            result = standard_response(
                success=False,
                error="Invalid internal response structure",
                status_code=500,
            )

        return JSONResponse(content=result, status_code=result.get("status_code", 200))

    except Exception as exc:
        handled = handle_exception(logger, exc, context="get_batch_subjects")
        return JSONResponse(
            content=handled, status_code=handled.get("status_code", 500)
        )


@router.post(
    "/content/{batch_id}/chapters",
    response_model=StandardResponseModel,
    operation_id="getChaptersForBatch",
)
async def fetch_chapters_for_batch(
    batch_id: str,
    payload: ChapterRequestModel = Body(...),
):
    logger = setup_logging("api.get_chapters")

    try:
        result = get_ch(
            batch_id=batch_id,
            subject_ids=payload.subject_ids,
            refetch=payload.refetch,
        )

        return JSONResponse(content=result, status_code=result.get("status_code", 200))

    except Exception as exc:
        handled = handle_exception(logger, exc, context="fetch_chapters_for_batch")
        return JSONResponse(
            content=handled, status_code=handled.get("status_code", 500)
        )


@router.post(
    "/{batch_id}/chapters/{subject_id}/contents",
    response_model=StandardResponse,
    operation_id="fetch_chapter_content"
)
async def fetch_chapter_content(
    batch_id: str = Path(..., description="Batch identifier"),
    subject_id: str = Path(..., description="Subject identifier"),
    body: ChapterContentRequest = Body(...),
):
    logger = setup_logging(name="endpoint.fetch_chapter_content")

    try:
        result: Dict[str, Any] = get_ch_content(
            batch_id=batch_id,
            subject_id=subject_id,
            chapter_ids=body.chapter_ids,
            content_type=body.content_type,
            refetch=body.refetch,
        )

        return JSONResponse(
            content=result,
            status_code=result.get("status_code", 200),
        )

    except Exception as exc:
        error_response = handle_exception(logger, exc, context="fetch_chapter_content")
        return JSONResponse(
            content=error_response,
            status_code=error_response.get("status_code", 500),
        )
