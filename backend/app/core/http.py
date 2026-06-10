import httpx

from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()


class HTTPClientState:
    client: httpx.AsyncClient | None = None


http_state = HTTPClientState()


def get_http_client() -> httpx.AsyncClient:
    if http_state.client is None:
        raise RuntimeError("HTTP client not initialized")

    return http_state.client


HTTPClientDep = Annotated[
    httpx.AsyncClient,
    Depends(get_http_client),
]
