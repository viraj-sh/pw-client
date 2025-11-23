from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List


class LectureOverviewData(BaseModel):
    completedChapter: Optional[int] = Field(None)
    completedLectures: Optional[int] = Field(None)
    totalWatchTime: Optional[int] = Field(None)
    totalChapters: Optional[int] = Field(None)
    totalLectures: Optional[int] = Field(None)


class LectureOverviewResponse(BaseModel):
    success: bool = Field(...)
    error: Optional[str] = Field(None)
    data: Optional[LectureOverviewData] = Field(None)
    status_code: int = Field(...)


class LectureSubjectItem(BaseModel):
    subjectName: Optional[str] = Field(None, description="Name of the subject")
    completedChapter: Optional[int] = Field(
        None, description="Number of completed chapters"
    )
    completedLectures: Optional[int] = Field(
        None, description="Number of completed lectures"
    )
    totalWatchTime: Optional[int] = Field(
        None, description="Total watch time in minutes/seconds"
    )
    totalLectures: Optional[int] = Field(None, description="Total number of lectures")
    totalChapters: Optional[int] = Field(None, description="Total number of chapters")


class LectureSubjectsResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation succeeded")
    error: Optional[str] = Field(None, description="Error message, if any")
    data: Optional[List[LectureSubjectItem]] = Field(
        None, description="List of lecture subject statistics"
    )
    status_code: int = Field(..., description="HTTP status code")


class QuizOverviewItemModel(BaseModel):
    key: str
    accuracy: Optional[float] = None
    marksObtained: Optional[int] = None
    correctQuestions: Optional[int] = None
    completedQuiz: Optional[int] = None
    totalQuiz: Optional[int] = None


class QuizOverviewDataModel(BaseModel):
    quiz_overview: List[QuizOverviewItemModel] = Field(default_factory=list)


class StandardResponseModel(BaseModel):
    success: bool
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    status_code: int


class QuizSubjectModel(BaseModel):
    subjectName: Optional[str] = Field(None)
    accuracy: Optional[float] = Field(None)
    marksObtained: Optional[float] = Field(None)
    totalQuestions: Optional[int] = Field(None)
    correctQuestions: Optional[int] = Field(None)
    attemptedQuestions: Optional[int] = Field(None)
    attempted: Optional[int] = Field(None)
    totalQuiz: Optional[int] = Field(None)


class QuizSubjectsData(BaseModel):
    subjects: List[QuizSubjectModel] = Field(default_factory=list)


class QuizSubjectsResponse(BaseModel):
    success: bool = Field(...)
    error: Optional[str] = Field(None)
    data: Optional[QuizSubjectsData] = Field(None)
    status_code: int = Field(...)
