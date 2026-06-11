from typing import Annotated, Literal
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import Depends

from app.core.http import HTTPClientDep, security
from app.core.constants import auth_headers
from app.core.urls import BatchURLs, API_BASE_URL


async def batches(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    page: int = 1,
):
    return await client.get(
        url=BatchURLs.GET_BATCHES,
        params={"page": page},
        headers=auth_headers(token.credentials),
    )


async def subjects(
    batch_id: str,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
):
    return await client.get(
        url=f"{API_BASE_URL}/v3/batches/{batch_id}/details",
        headers=auth_headers(token.credentials),
    )


async def chapters(
    batch_id: str,
    sub_id: str,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    page: int = 1,
):
    return await client.get(
        url=f"{API_BASE_URL}/v2/batches/{batch_id}/subject/{sub_id}/topics",
        params={"page": page},
        headers=auth_headers(token.credentials),
    )


async def content(
    batch_id: str,
    sub_id: str,
    chapter_id: str,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    skip: int = 0,
    limit: int = 20,
    page: int = 1,
    type: Literal["all", "notes", "lectures", "dpp_pdf", "dpp"] = "all",
):
    if type == "dpp":
        url = f"{API_BASE_URL}/v3/test-service/tests/new-dpp-list"
        params = {
            "page": page,
            "limit": limit,
            "batchId": batch_id,
            "batchSubjectId": sub_id,
            "chapterId": chapter_id,
            "dppType": "ALL",
        }
        return await client.get(
            url=url, params=params, headers=auth_headers(token.credentials)
        )
    else:
        url = f"{API_BASE_URL}/batch-service/v3/batch-subject-schedules/{batch_id}/subject/{sub_id}/contents"
        params = {
            "skip": skip,
            "limit": limit,
            "contentType": type.upper(),
            "tagId": chapter_id,
            "contentFilter": "ALL",
        }
        return await client.get(
            url=url, params=params, headers=auth_headers(token.credentials)
        )
