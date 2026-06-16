from fastapi import APIRouter, Query, status, HTTPException, Depends
from typing import Annotated, Literal, Optional
from fastapi.security import HTTPAuthorizationCredentials
import httpx

from app.core.http import HTTPClientDep, security
from app.services.dashboard import batch_stats, sub_stats, quiz_stats
from app.schemas.dashboard import BatchResponse, SubjectResponse, QuizObjectiveResponse

router = APIRouter()


@router.get("/{batch_id}", status_code=status.HTTP_200_OK)
async def fetch_stats(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
    batch_id: str,
    type: Literal["subject", "batch", "quiz"] = Query(default="batch"),
    quiz_type: Optional[Literal["objective", "subjective"]] = Query(default=None),
):
    try:
        if type == "batch":
            response = await batch_stats(batch_id, token, client)
            if response.status_code == 200:
                return BatchResponse(
                    completed_chapter=response.json()
                    .get("data")
                    .get("completedChapter"),
                    completed_lectures=response.json()
                    .get("data")
                    .get("completedChapter"),
                    total_watch_time=response.json().get("data").get("totalWatchTime"),
                    total_chapters=response.json().get("data").get("completedChapter"),
                    total_lectures=response.json().get("data").get("completedChapter"),
                )
        elif type == "subject":
            response = await sub_stats(batch_id, token, client)
            if response.status_code == 200:
                return [
                    SubjectResponse(
                        completed_chapter=sub.get("completedChapter"),
                        completed_lectures=sub.get("completedLectures"),
                        sub_id=sub.get("subjectId").get("_id"),
                        sub_name=sub.get("subjectId").get("name"),
                        total_watch_time=sub.get("totalWatchTime"),
                        total_chapters=sub.get("totalChapters"),
                        total_lectures=sub.get("totalLectures"),
                    )
                    for sub in response.json().get("data")
                ]
        elif type == "quiz":
            if quiz_type is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="quiz type cannot be none",
                )
            response = await quiz_stats(
                batch_id,
                token,
                client,
                type=quiz_type,
            )
            if quiz_type == "objective":
                if response.status_code == 200:
                    return [
                        QuizObjectiveResponse(
                            sub_id=quiz.get("subjectId").get("_id"),
                            sub_name=quiz.get("subjectId").get("name"),
                            sub_type=quiz.get("subjectType"),
                            accuracy=quiz.get("accuracy"),
                            avg_time=quiz.get("averageTime"),
                            avg_score=quiz.get("averageScore"),
                            total_marks=quiz.get("totalMarks"),
                            marks_obtained=quiz.get("marksObtained"),
                            total_questions=quiz.get("totalQuestions"),
                            correct_questions=quiz.get("correctQuestions"),
                            attempt_questions=quiz.get("attemptedQuestions"),
                            attempted=quiz.get("attempted"),
                            total_quiz=quiz.get("totalQuiz"),
                        )
                        for quiz in response.json().get("data")
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
