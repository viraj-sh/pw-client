from fastapi import Depends
from typing import Annotated, Literal
from fastapi.security import HTTPAuthorizationCredentials

from app.core.urls import API_BASE_URL
from app.core.http import HTTPClientDep, security
from app.core.constants import auth_headers


async def batch_stats(
    batch_id: str,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
):

    return await client.get(
        url=f"{API_BASE_URL}/v3/performance/lecture",
        params={"batchId": batch_id},
        headers=auth_headers(token.credentials),
    )


async def sub_stats(
    batch_id: str,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
):

    return await client.get(
        url=f"{API_BASE_URL}/v3/performance/lecture/subjects",
        params={"batchId": batch_id},
        headers=auth_headers(token.credentials),
    )


async def quiz_stats(
    batch_id: str,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    type: Literal["objective", "subjective"] = "objective",
):

    return await client.get(
        url=f"{API_BASE_URL}/v3/performance/quiz/subjects",
        params={"batchId": batch_id, "type": type.upper()},
        headers=auth_headers(token.credentials),
    )
