from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.core.http import security, HTTPClientDep
from app.core.urls import API_BASE_URL
from app.core.constants import auth_headers


async def fetch_annoucements(
    batch_id: str,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    page: int = 1,
):
    return await client.get(
        url=f"{API_BASE_URL}/v1/batches/{batch_id}/announcement/v2",
        params={"page": page},
        headers=auth_headers(token.credentials),
    )
