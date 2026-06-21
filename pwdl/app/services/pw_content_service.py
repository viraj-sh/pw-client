import httpx
from typing import Dict, Any, List, Optional
from app.core.config import get_settings
from app.core.exceptions import UpstreamAPIException
from app.core.logging import get_logger

logger = get_logger("pw_content_service")
settings = get_settings()

async def get_lecture_details(
    client: httpx.AsyncClient,
    token: str,
    random_id: str,
    video_id: str,
    batch_id: str,
    video_url: str,
    secondary_parent_id: str,
    lecture_type: str
) -> Dict[str, Any]:
    url = f"{settings.PW_API_BASE_URL}/v1/videos/video-url-details"
    params = {
        "type": lecture_type,
        "childId": video_id,
        "parentId": batch_id,
        "reqType": "query",
        "videoContainerType": "DASH"
    }
    if video_url:
        params["videoUrl"] = video_url
    if secondary_parent_id:
        params["secondaryParentId"] = secondary_parent_id

    headers = {
        "client-id": "5eb393ee95fab7468a79d189",
        "client-type": "WEB",
        "Authorization": f"Bearer {token}",
        "randomid": random_id
    }

    logger.info(f"Fetching lecture URL details for video_id={video_id}, batch_id={batch_id}, type={lecture_type}")
    try:
        response = await client.get(
            url,
            params=params,
            headers=headers,
            timeout=settings.REQUEST_TIMEOUT_SECONDS
        )
        if response.is_error:
            logger.error(f"Penpencil API error for video details. Status: {response.status_code}")
            raise UpstreamAPIException(
                message="Failed to fetch lecture details from upstream Penpencil API",
                status_code=response.status_code,
                detail=response.text
            )
        
        data = response.json()
        result = data.get("data", {})
        if not result:
            logger.error("Penpencil API returned empty data field for video details")
            raise UpstreamAPIException(
                message="Upstream API returned an empty or invalid payload",
                status_code=response.status_code,
                detail=str(data)
            )
        return result

    except httpx.RequestError as exc:
        logger.error(f"HTTP request to Penpencil API failed: {exc}")
        raise UpstreamAPIException(
            message=f"Network error communicating with upstream Penpencil API: {exc}",
            status_code=500
        )

async def get_batch_subjects(
    client: httpx.AsyncClient,
    token: str,
    random_id: str,
    batch_id: str
) -> List[Dict[str, Any]]:
    url = f"{settings.PW_API_BASE_URL}/v3/batches/{batch_id}/details"
    headers = {
        "client-id": "5eb393ee95fab7468a79d189",
        "client-type": "WEB",
        "Authorization": f"Bearer {token}",
        "randomid": random_id
    }

    logger.info(f"Fetching batch details for batch_id={batch_id}")
    try:
        response = await client.get(
            url,
            headers=headers,
            timeout=settings.REQUEST_TIMEOUT_SECONDS
        )
        if response.is_error:
            logger.error(f"Penpencil API error for batch details. Status: {response.status_code}")
            raise UpstreamAPIException(
                message="Failed to fetch batch subjects from upstream Penpencil API",
                status_code=response.status_code,
                detail=response.text
            )
        
        data = response.json()
        subjects = data.get("data", {}).get("subjects", [])
        return subjects

    except httpx.RequestError as exc:
        logger.error(f"HTTP request to Penpencil API failed: {exc}")
        raise UpstreamAPIException(
            message=f"Network error communicating with upstream Penpencil API: {exc}",
            status_code=500
        )
