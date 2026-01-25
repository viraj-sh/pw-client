from datetime import timedelta
from core.utils import EnvManager, standard_response
from core.logging import setup_logging
from core.cache import cached_request, invalidate_cache
from core.exceptions import handle_exception
from typing import Any, Dict, List
from .data_model.model_announcement import (
    Announcement,
)


def fetch_announcements(
    batch_id: str, page: int = 1, refetch: bool = False
) -> Dict[str, Any]:
    logger = setup_logging(name="core.fetch_announcements", level="INFO")
    log_prefix = "[AnnouncementsAPI] "

    try:
        token = EnvManager.get("TOKEN", default=None)
        logger.info(f"{log_prefix}Loaded TOKEN from EnvManager")

        if not token:
            return standard_response(
                success=False,
                error="Authentication token missing from environment.",
                status_code=400,
            )

        url = f"https://api.penpencil.co/v1/batches/{batch_id}/announcement"
        params = {"page": page}
        headers = {
            "accept": "application/json",
            "authorization": token,
        }

        response = cached_request(
            method="GET",
            url=url,
            headers=headers,
            params=params,
            expire_after=timedelta(minutes=10),
            refetch=refetch,
            log_prefix=log_prefix,
        )

        if response is None:
            return standard_response(
                success=False,
                error="No response received from server.",
                status_code=500,
            )

        if not response.ok:
            invalidate_cache(response)
            return standard_response(
                success=False,
                error=f"HTTP error {response.status_code}",
                status_code=response.status_code,
            )

        try:
            json_data = response.json()
        except Exception:
            invalidate_cache(response)
            return standard_response(
                success=False,
                error="Invalid JSON received from server.",
                status_code=500,
            )

        raw_items = json_data.get("data", [])
        if not isinstance(raw_items, list):
            return standard_response(
                success=False,
                error="Malformed API response.",
                status_code=500,
            )

        parsed_announcements: List[Dict[str, Any]] = []

        for item in raw_items:
            obj = Announcement.from_json(item)
            if obj:
                parsed_announcements.append(
                    {
                        "announcement": obj.announcement,
                        "_id": obj.id,
                        "scheduleTime": obj.schedule_time,
                        "endlink": obj.endlink,
                    }
                )

        return standard_response(
            success=True,
            data={"announcements": parsed_announcements},
            status_code=200,
        )

    except Exception as exc:
        return handle_exception(logger, exc, context="fetch_announcements")
