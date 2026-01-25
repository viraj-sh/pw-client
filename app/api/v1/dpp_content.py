from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from core.logging import setup_logging
from core.exceptions import handle_exception
from schema.pydantic_content import (
    StandardResponseModel,
    DPPTestSolutionResponse,
)
from services.content import fetch_dpp_tests, fetch_dpp_test_sol


router = APIRouter(tags=["DPP (QUIZ) Content"], prefix="/content")
logger = setup_logging(name="DPP Content", level="INFO")


@router.get(
    "/dpp/{batch_id}/{subject_id}/{chapter_id}/tests",
    response_model=StandardResponseModel,
    operation_id="get_dpp_tests",
)
async def get_dpp_tests_endpoint(
    batch_id: str,
    subject_id: str,
    chapter_id: str,
    page: int = Query(1, description="Page number"),
    limit: int = Query(20, description="Items per page"),
    dpp_type: str = Query("ALL", description="DPP type filter"),
    refetch: bool = Query(False, description="Force refresh, bypass cache"),
):
    try:
        result = fetch_dpp_tests(
            batch_id=batch_id,
            subject_id=subject_id,
            chapter_id=chapter_id,
            page=page,
            limit=limit,
            dpp_type=dpp_type,
            refetch=refetch,
        )

        status = result.get("status_code", 200)
        return JSONResponse(content=result, status_code=status)

    except Exception as exc:
        error_resp = handle_exception(
            logger=logger, exc=exc, context="get_dpp_tests_endpoint"
        )
        return JSONResponse(
            content=error_resp, status_code=error_resp.get("status_code", 500)
        )


@router.get(
    "/dpp/{attempt_id}/solution",
    response_model=DPPTestSolutionResponse,
    operation_id="fetchDPPTestSolution",
)
async def get_dpp_test_solution(
    attempt_id: str,
    refetch: bool = Query(
        False, description="If true, bypass cache and force refetch from API"
    ),
):
    logger = setup_logging(name="api.get_dpp_test_solution")

    try:
        result = fetch_dpp_test_sol(
            attempt_id=attempt_id,
            refetch=refetch,
        )
        return JSONResponse(
            content=result,
            status_code=result.get("status_code", 200),
        )

    except Exception as exc:
        handled = handle_exception(
            logger,
            exc,
            context="get_dpp_test_solution",
        )
        return JSONResponse(
            content=handled,
            status_code=handled.get("status_code", 500),
        )
