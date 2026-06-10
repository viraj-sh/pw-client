from typing import Annotated, Literal
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import Depends

from app.core.http import HTTPClientDep, security
from app.core.constants import auth_headers
from app.core.urls import BatchURLs


async def batches(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    amount: Literal["paid", "free"],
    type: Literal["all"],
    page: int = 1,
):
    params = {page: page, type: type, amount: amount.capitalize()}
    return await client.get(
        url=BatchURLs.GET_BATCHES,
        params=params,
        headers=auth_headers(token.credentials),
    )


async def batch_details(
    batch_id: str,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
):
    return await client.get(
        url=f"{BatchURLs.BATCH_BASE}/{batch_id}/details",
        headers=auth_headers(token.credentials),
    )
