from fastapi import APIRouter, Query, Body, Path
from fastapi.responses import JSONResponse
from typing import Optional
from core.utils import standard_response
from core.logging import setup_logging
from core.exceptions import handle_exception
from typing import Optional, Any, Dict
from schema.pydantic_dashboard import (
    LectureOverviewResponse,
    LectureSubjectsResponse,
    QuizOverviewDataModel,
    StandardResponseModel,
    QuizSubjectsResponse,
)
from services.dashboard import (
    fetch_lecture_overview,
    fetch_lecture_subjects,
    fetch_quiz_overview,
    fetch_quiz_subjects,
)

router = APIRouter(tags=["Dashboard"], prefix="/dashboard")
logger = setup_logging(name="Dashboard", level="INFO")


@router.get(
    "/{batch_id}/lectures/overview",
    response_model=LectureOverviewResponse,
    operation_id="get_lecture_overview",
)
async def get_lecture_overview(
    batch_id: str,
    refetch: bool = Query(
        default=False,
        description="Set True to bypass cache and refetch from upstream API.",
    ),
):
    logger = setup_logging(name="api.get_lecture_overview")

    try:
        result: Dict[str, Any] = fetch_lecture_overview(
            batch_id=batch_id, refetch=refetch
        )
        return JSONResponse(content=result, status_code=result.get("status_code", 200))

    except Exception as exc:
        return handle_exception(logger=logger, exc=exc, context="get_lecture_overview")


@router.get(
    "/{batch_id}/lectures/subjects",
    response_model=LectureSubjectsResponse,
    operation_id="getLectureSubjectStats",
)
async def get_lecture_subject_stats(
    batch_id: str,
    refetch: bool = Query(False, description="Bypass cache and fetch fresh data"),
) -> JSONResponse:
    logger = setup_logging(name="api.get_lecture_subject_stats")

    try:
        result: Dict[str, Any] = fetch_lecture_subjects(
            batch_id=batch_id,
            refetch=refetch,
        )

        status = result.get("status_code", 200)

        return JSONResponse(
            content=result,
            status_code=status,
        )

    except Exception as exc:
        return handle_exception(logger, exc, context="get_lecture_subject_stats")


@router.get(
    "/{batch_id}/quiz/overview",
    response_model=StandardResponseModel,
    operation_id="get_quiz_overview",
)
def get_quiz_overview(
    batch_id: str,
    refetch: bool = Query(
        default=False, description="Force refresh by bypassing cache if true."
    ),
):
    logger = setup_logging(name="api.get_quiz_overview")

    try:
        result: Dict[str, Any] = fetch_quiz_overview(batch_id=batch_id, refetch=refetch)

        status = result.get("status_code", 200)

        return JSONResponse(content=result, status_code=status)

    except Exception as exc:
        handled = handle_exception(logger, exc, context="get_quiz_overview")
        status = handled.get("status_code", 500)
        return JSONResponse(content=handled, status_code=status)


@router.get(
    "/{batch_id}/quiz/subjects",
    response_model=QuizSubjectsResponse,
    operation_id="getQuizSubjectsForBatch",
)
async def get_quiz_subjects(
    batch_id: str,
    quiz_type: str = Query("OBJECTIVE", description="Filter by quiz type"),
    refetch: bool = Query(False, description="Bypass cache and refetch from source"),
):
    logger = setup_logging(name="api.get_quiz_subjects")

    try:
        result = fetch_quiz_subjects(
            batch_id=batch_id,
            quiz_type=quiz_type,
            refetch=refetch,
        )
        status_code = result.get("status_code", 200)

        return JSONResponse(content=result, status_code=status_code)

    except Exception as exc:
        error_resp = handle_exception(logger, exc, context="get_quiz_subjects")
        return JSONResponse(
            content=error_resp,
            status_code=error_resp.get("status_code", 500),
        )
