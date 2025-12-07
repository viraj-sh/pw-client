from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse
from typing import Any, Dict
from core.utils import standard_response
from core.logging import setup_logging
from core.exceptions import handle_exception
from services.auth import send_otp, verify_otp, verify_token, logout_user, get_countries
from schema.pydantic_auth import (
    SendOTPRequest,
    StandardResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
    VerifyTokenResponse,
    LogoutResponseModel,
    StandardResponseModel,
)


router = APIRouter(tags=["Auth"], prefix="/auth")
logger = setup_logging(name="Auth", level="INFO")


@router.get(
    "/countries",
    response_model=StandardResponseModel,
    operation_id="list_countries",
)
def list_countries(
    refetch: bool = Query(False, description="Bypass cache and refetch country data"),
) -> JSONResponse:
    logger = setup_logging(name="api.list_countries", level="INFO")

    try:
        result: Dict[str, Any] = get_countries(refetch=refetch)
        return JSONResponse(content=result, status_code=result.get("status_code", 200))

    except Exception as exc:
        handled = handle_exception(logger, exc, context="list_countries")
        return JSONResponse(
            content=handled, status_code=handled.get("status_code", 500)
        )


@router.post(
    "/send-otp",
    response_model=StandardResponse,
    operation_id="send_otp_v1",
)
def send_otp_endpoint(payload: SendOTPRequest = Body(...)) -> JSONResponse:
    logger = setup_logging(name="auth.send-otp", level="INFO")
    try:
        result: Dict[str, Any] = send_otp(
            phone=payload.phone, country_code=payload.country_code
        )
        return JSONResponse(content=result, status_code=result.get("status_code", 200))
    except Exception as exc:
        return handle_exception(logger, exc, context="send_otp_endpoint")


@router.post(
    "/verify-otp", response_model=VerifyOtpResponse, operation_id="verify_user_otp"
)
def verify_otp_endpoint(request: VerifyOtpRequest = Body(...)) -> JSONResponse:
    logger = setup_logging(name="auth.verify-otp", level="INFO")
    try:
        result: Dict[str, Any] = verify_otp(
            mobile_no=request.mobile_no,
            otp=request.otp,
        )

        return JSONResponse(
            content=result,
            status_code=result.get("status_code", 200),
        )

    except Exception as exc:
        error_result = handle_exception(logger, exc, context="verify_otp_endpoint")
        return JSONResponse(
            content=error_result,
            status_code=error_result.get("status_code", 500),
        )


@router.get(
    "/verify-token",
    response_model=VerifyTokenResponse,
    operation_id="verifyTokenAuthCheck",
)
async def verify_token_endpoint() -> JSONResponse:
    logger = setup_logging(name="auth.verify_token", level="INFO")

    try:
        logger.info("Received request for token verification.")
        result = verify_token()
        logger.info("Token verification process completed.")
        return JSONResponse(content=result, status_code=result.get("status_code", 200))

    except Exception as exc:
        return handle_exception(logger, exc, context="verify_token_endpoint")


@router.post(
    "/logout",
    response_model=LogoutResponseModel,
    operation_id="logout_user_operation",
)
async def logout_endpoint() -> JSONResponse:
    logger = setup_logging(name="api.logout_user", level="INFO")

    try:
        result: Dict[str, Any] = logout_user()

        if not isinstance(result, dict):
            logger.warning("Invalid response format from logout_user.")
            result = standard_response(
                success=False,
                error="Unexpected response from core logic",
                status_code=500,
            )

        return JSONResponse(content=result, status_code=result.get("status_code", 200))

    except Exception as exc:
        return handle_exception(logger, exc, context="logout_endpoint")
