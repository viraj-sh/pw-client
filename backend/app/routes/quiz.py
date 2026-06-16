from fastapi import APIRouter, Depends, HTTPException, status
import httpx
from typing import Annotated
from fastapi.security import HTTPAuthorizationCredentials

from app.services.quiz import quiz_details, quiz_result, parse_quiz_result
from app.core.http import security, HTTPClientDep
from app.schemas.quiz import QuizDetailResponse

router = APIRouter()


@router.post("/details", status_code=status.HTTP_201_CREATED)
async def fetch_quiz_details(
    test_id: list[str],
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
):
    try:
        response = await quiz_details(token, client, test_id)
        if response.status_code == 201:
            return [
                QuizDetailResponse(
                    id=test.get("exerciseId").get("_id"),
                    name=test.get("exerciseId").get("name"),
                    total_attempts=test.get("exerciseId").get("totalAttempts"),
                    difficulty_level=test.get("exerciseId").get("difficultyLevel"),
                    slug=test.get("exerciseId").get("slug"),
                    status=test.get("exerciseId").get("visibleStatus"),
                    student_count=test.get("exerciseId").get("studentCount"),
                    student_mapping_id=test.get("testStudentMapping").get("_id"),
                    student_mapping_status=test.get("testStudentMapping").get(
                        "testActivityStatus"
                    ),
                    student_mapping_source=test.get("testStudentMapping").get(
                        "testSource"
                    ),
                    tag1=test.get("tag1"),
                    tag2=test.get("tag2"),
                )
                for test in response.json().get("data")
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


@router.get("/{test_mapping_id}/result", status_code=status.HTTP_200_OK)
async def fetch_quiz_result(
    test_mapping_id: str,
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
):
    try:
        response = await quiz_result(token, client, test_mapping_id)
        if response.status_code == 200:
            return parse_quiz_result(response.json(), test_mapping_id)

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
