from typing import Dict, Any, Optional
import requests
from core.utils import standard_response
import logging


def handle_exception(
    logger: logging.Logger,
    exc: Exception,
    context: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    log_prefix = f"[{context}] " if context else ""

    if extra:
        logger = logger.bind(**extra) if hasattr(logger, "bind") else logger

    if isinstance(exc, requests.Timeout):
        logger.error(f"{log_prefix}Request timed out: {exc}")
        return standard_response(False, error_msg="Request timed out", status_code=504)

    if isinstance(exc, requests.RequestException):
        logger.error(f"{log_prefix}Network error: {exc}")
        return standard_response(
            False, error_msg="Network error occurred", status_code=503
        )

    if isinstance(exc, ValueError):
        logger.error(f"{log_prefix}Failed to parse JSON response: {exc}")
        return standard_response(
            False, error_msg="Invalid response from server", status_code=400
        )

    logger.exception(f"{log_prefix}Unexpected error occurred: {exc}")
    return standard_response(
        False, error_msg="An unexpected error occurred", status_code=500
    )
