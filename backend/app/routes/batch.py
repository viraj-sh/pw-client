from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from typing import Annotated, Literal
import httpx

from app.core.http import HTTPClientDep, security
from app.services.batch import batches, batch_details
from app.schemas.batch import (
    BatchResponse,
    BatchDetailResponse,
    Fee,
    Subject,
    TeacherBrief,
)

router = APIRouter()


@router.get(
    "/batches", response_model=list[BatchResponse], status_code=status.HTTP_200_OK
)
async def fetch_batches(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    amount: Literal["free", "paid"] = Query(default="paid"),
    type: Literal["all"] = Query(default="all"),
    page: int = Query(default=1),
):
    try:
        response = await batches(token, client, amount, type, page)
        if response.status_code == 200:
            return [
                BatchResponse(
                    id=batch.get("_id"),
                    cohort_id=batch.get("cohortId"),
                    batch_category_id=batch.get("batchCategoryId"),
                    batch_category_ids=batch.get("batchCategoryIds"),
                    exam=batch.get("exam"),
                    name=batch.get("name"),
                    slug=batch.get("slug"),
                    is_purchased=batch.get("isPurchased"),
                    is_free=batch.get("isFree"),
                    is_batch_plus=batch.get("isBatchPlusEnabled"),
                    board=batch.get("board"),
                    academic_level=batch.get("board"),
                    start_date=batch.get("startDate"),
                    end_date=batch.get("endDate"),
                    expiry_date=batch.get("expiryDate"),
                )
                for batch in response.json().get("data")
            ]
        elif response.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{response.json().get('error').get('status')} -> {response.json().get('error').get('message')}",
            )
        return response.json()
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "External API timed out")
    except httpx.NetworkError:
        raise HTTPException(502, "Could not reach external API")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected error: {exc}")


@router.get(
    "/batches/{batch_id}",
    response_model=BatchDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def fetch_batche_details(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    batch_id: str,
):
    try:
        response = await batch_details(batch_id, token, client)
        if response.status_code == 200:
            data = response.json().get("data")
            if not data:
                raise HTTPException(404, "Batch data not found")

            subjects_list = []
            for sub in data.get("subjects", []):
                teachers = []
                for teacher in sub.get("teacherIds", []):
                    teachers.append(
                        TeacherBrief(
                            id=teacher.get("_id"),
                            firstName=teacher.get("firstName"),
                            lastName=teacher.get("lastName"),
                            email=teacher.get("email"),
                        )
                    )
                subjects_list.append(
                    Subject(
                        id=sub.get("_id"),
                        subject=sub.get("subject"),
                        subject_id=sub.get("subjectId"),
                        slug=sub.get("slug"),
                        teachers=teachers,
                        tag_count=sub.get("tagCount"),
                        batch_id=sub.get("batchId"),
                        order=sub.get("displayOrder"),
                        lecture_count=sub.get("lectureCount"),
                    )
                )
            fee_data = data.get("fee")
            fee_obj = (
                Fee(
                    amount=fee_data.get("amount") if fee_data else None,
                    discount=fee_data.get("discount") if fee_data else None,
                    total=fee_data.get("total") if fee_data else None,
                )
                if fee_data
                else None
            )

            return BatchDetailResponse(
                is_security_enabled=data.get("isBatchContentSecurityEnabled"),
                exam_year=data.get("examYear"),
                expiry_days=data.get("expiryDays"),
                fee=fee_obj,
                subjects=subjects_list,
            )
        return response.json()
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "External API timed out")
    except httpx.NetworkError:
        raise HTTPException(502, "Could not reach external API")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected error: {exc}")
