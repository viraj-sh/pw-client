from typing import Annotated
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


async def batch_details(
    batch_id: str,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
):
    return await client.get(
        url=f"{API_BASE_URL}/v3/batches/{batch_id}/details",
        headers=auth_headers(token.credentials),
    )
