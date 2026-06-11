from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from typing import Annotated, Literal
import httpx

from app.core.http import HTTPClientDep, security
from app.services.batch import batches, subjects, chapters, content
from app.schemas.batch import (
    BatchResponse,
    BatchDetailResponse,
    Fee,
    Subject,
    TeacherBrief,
    TopicResponse,
    NotesResponse,
    LectureResponse,
)

router = APIRouter()


@router.get("", response_model=list[BatchResponse], status_code=status.HTTP_200_OK)
async def fetch_batches(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    page: int = Query(default=1, ge=1),
):
    try:
        response = await batches(token, client, page)
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
    "/{batch_id}",
    response_model=BatchDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def fetch_subjects(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    batch_id: str,
):
    try:
        response = await subjects(batch_id, token, client)
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


@router.get(
    "/{batch_id}/{subject_id}",
    response_model=list[TopicResponse],
    status_code=status.HTTP_200_OK,
)
async def fetch_topics(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    batch_id: str,
    subject_id: str,
    page: int = Query(default=1, ge=1),
):
    try:
        response = await chapters(batch_id, subject_id, token, client, page)
        if response.status_code == 200:
            return [
                TopicResponse(
                    id=topic.get("_id"),
                    name=topic.get("name"),
                    slug=topic.get("slug"),
                    order=topic.get("displayOrder"),
                    notes=topic.get("notes"),
                    exercises=topic.get("exercises"),
                    videos=topic.get("videos"),
                    lecture_videos=topic.get("lectureVideos"),
                )
                for topic in response.json().get("data")
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


@router.get(
    "/{batch_id}/{subject_id}/{chapter_id}",
    status_code=status.HTTP_200_OK,
)
async def fetch_content(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    batch_id: str,
    subject_id: str,
    chapter_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1),
    type: Literal["all", "notes", "lectures", "dpp_pdf"] = Query(default="all"),
):
    try:
        response = await content(
            batch_id, subject_id, chapter_id, token, client, skip, limit, type
        )
        if response.status_code == 200:
            if type == "notes" or type == "dpp_pdf":
                data_list = response.json().get("data", [])
                return [
                    NotesResponse(
                        type=note.get("type"),
                        id=note.get("data", {}).get("_id"),
                        status=note.get("data", {}).get("status"),
                        is_dpp_notes=note.get("data", {}).get("isDPPNotes"),
                        topic=note["data"]["homeworkIds"][0].get("topic")
                        if note.get("data", {}).get("homeworkIds")
                        else None,
                        note=note["data"]["homeworkIds"][0].get("note")
                        if note.get("data", {}).get("homeworkIds")
                        else None,
                        url=f"{note['data']['homeworkIds'][0]['attachmentIds'][-1]['baseUrl']}{note['data']['homeworkIds'][0]['attachmentIds'][-1]['key']}",
                        file_name=(
                            note["data"]["homeworkIds"][0]["attachmentIds"][-1].get(
                                "name"
                            )
                            if note.get("data", {}).get("homeworkIds")
                            and note["data"]["homeworkIds"][0].get("attachmentIds")
                            else None
                        ),
                        created_at=(
                            note["data"]["homeworkIds"][0]["attachmentIds"][-1].get(
                                "createdAt"
                            )
                            if note.get("data", {}).get("homeworkIds")
                            and note["data"]["homeworkIds"][0].get("attachmentIds")
                            else None
                        ),
                    )
                    for note in data_list
                    if note.get("data", {}).get("homeworkIds")
                ]
            elif type == "lectures":
                data_list = response.json().get("data", [])
                return [
                    LectureResponse(
                        type=item.get("type"),  # "LECTURE"
                        id=item.get("data", {}).get("_id"),
                        dpp_count=item.get("data", {}).get("dppCount"),
                        date=item.get("data", {}).get("date"),
                        topic=item.get("data", {}).get("topic"),
                        slug=item.get("data", {}).get("slug"),
                        status=item.get("data", {}).get("status"),
                        video_id=item.get("data", {})
                        .get("videoDetails", {})
                        .get("_id"),
                        video_name=item.get("data", {})
                        .get("videoDetails", {})
                        .get("name"),
                        video_url=item.get("data", {})
                        .get("videoDetails", {})
                        .get("videoUrl"),
                        duration=item.get("data", {})
                        .get("videoDetails", {})
                        .get("duration"),
                        is_drm_protectured=item.get("data", {})
                        .get("videoDetails", {})
                        .get("drmProtected"),
                        find_key=item.get("data", {})
                        .get("videoDetails", {})
                        .get("findKey"),
                    )
                    for item in data_list
                ]
            elif type == "all":
                data_list = response.json().get("data", [])
                results = []
                for item in data_list:
                    item_type = item.get("type")
                    if item_type in ("NOTES", "DPP_PDF"):
                        note = item
                        results.append(
                            NotesResponse(
                                type=note.get("type"),
                                id=note.get("data", {}).get("_id"),
                                status=note.get("data", {}).get("status"),
                                is_dpp_notes=note.get("data", {}).get("isDPPNotes"),
                                topic=note["data"]["homeworkIds"][0].get("topic")
                                if note.get("data", {}).get("homeworkIds")
                                else None,
                                note=note["data"]["homeworkIds"][0].get("note")
                                if note.get("data", {}).get("homeworkIds")
                                else None,
                                url=f"{note['data']['homeworkIds'][0]['attachmentIds'][-1]['baseUrl']}{note['data']['homeworkIds'][0]['attachmentIds'][-1]['key']}",
                                file_name=(
                                    note["data"]["homeworkIds"][0]["attachmentIds"][
                                        -1
                                    ].get("name")
                                    if note.get("data", {}).get("homeworkIds")
                                    and note["data"]["homeworkIds"][0].get(
                                        "attachmentIds"
                                    )
                                    else None
                                ),
                                created_at=(
                                    note["data"]["homeworkIds"][0]["attachmentIds"][
                                        -1
                                    ].get("createdAt")
                                    if note.get("data", {}).get("homeworkIds")
                                    and note["data"]["homeworkIds"][0].get(
                                        "attachmentIds"
                                    )
                                    else None
                                ),
                            )
                        )
                    elif item_type == "LECTURE":
                        results.append(
                            LectureResponse(
                                type=item.get("type"),
                                id=item.get("data", {}).get("_id"),
                                dpp_count=item.get("data", {}).get("dppCount"),
                                date=item.get("data", {}).get("date"),
                                topic=item.get("data", {}).get("topic"),
                                slug=item.get("data", {}).get("slug"),
                                status=item.get("data", {}).get("status"),
                                video_id=item.get("data", {})
                                .get("videoDetails", {})
                                .get("_id"),
                                video_name=item.get("data", {})
                                .get("videoDetails", {})
                                .get("name"),
                                video_url=item.get("data", {})
                                .get("videoDetails", {})
                                .get("videoUrl"),
                                duration=item.get("data", {})
                                .get("videoDetails", {})
                                .get("duration"),
                                is_drm_protectured=item.get("data", {})
                                .get("videoDetails", {})
                                .get("drmProtected"),
                                find_key=item.get("data", {})
                                .get("videoDetails", {})
                                .get("findKey"),
                            )
                        )
                return results
        return response.json()
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "External API timed out")
    except httpx.NetworkError:
        raise HTTPException(502, "Could not reach external API")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected error: {exc}")
