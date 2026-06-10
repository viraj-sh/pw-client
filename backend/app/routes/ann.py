from fastapi import APIRouter, Query, status, Depends, HTTPException
import httpx
from fastapi.security import HTTPAuthorizationCredentials
from typing import Annotated


from app.core.http import HTTPClientDep, security
from app.services.ann import fetch_annoucements
from app.schemas.ann import AnnResponse

router = APIRouter()


@router.get("/{batch_id}", status_code=status.HTTP_200_OK)
async def fetch_batch_annoucements(
    batch_id: str,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    page: int = Query(default=1),
):
    try:
        response = await fetch_annoucements(batch_id, token, client, page)
        if response.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{response.json().get('error').get('status')} -> {response.json().get('error').get('message')}",
            )
        elif response.status_code == 200:
            return [
                AnnResponse(
                    id=ann.get("_id"),
                    heading=ann.get("heading"),
                    announcement=ann.get("announcement"),
                    type=ann.get("type"),
                    schedule_time=ann.get("scheduleTime"),
                    use_case=ann.get("announcementUseCase"),
                    url=f"{ann.get('attachment').get('baseUrl')}{ann.get('attachment').get('key')}",
                )
                for ann in response.json().get("data")
            ]
        return response.json()
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "External API timed out")
    except httpx.NetworkError:
        raise HTTPException(502, "Could not reach external API")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected error: {exc}")
