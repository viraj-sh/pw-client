from typing import Optional

from pydantic import BaseModel, Field


class BatchResponse(BaseModel):
    completed_chapter: Optional[int] = Field(None)
    completed_lectures: Optional[int] = Field(None)
    total_watch_time: Optional[int] = Field(None)
    total_chapters: Optional[int] = Field(None)
    total_lectures: Optional[int] = Field(None)


class SubjectResponse(BaseModel):
    completed_chapter: Optional[int] = Field(None)
    completed_lectures: Optional[int] = Field(None)
    sub_id: Optional[str] = Field(None)
    sub_name: Optional[str] = Field(None)
    total_watch_time: Optional[int] = Field(None)
    total_chapters: Optional[int] = Field(None)
    total_lectures: Optional[int] = Field(None)


class QuizObjectiveResponse(BaseModel):
    sub_id: Optional[str] = Field(None)
    sub_name: Optional[str] = Field(None)
    sub_type: Optional[str] = Field(None)
    accuracy: Optional[int] = Field(None)
    avg_time: Optional[float] = Field(None)
    avg_score: Optional[int] = Field(None)
    total_marks: Optional[int] = Field(None)
    marks_obtained: Optional[int] = Field(None)
    total_questions: Optional[int] = Field(None)
    correct_questions: Optional[int] = Field(None)
    attempt_questions: Optional[int] = Field(None)
    attempted: Optional[int] = Field(None)
    total_quiz: Optional[int] = Field(None)
