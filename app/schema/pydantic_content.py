from pydantic import BaseModel, Field, RootModel
from typing import Optional, Any, Dict, List


class BatchItem(BaseModel):
    batch_id: Optional[str] = Field(None)
    batch_name: Optional[str] = Field(None)
    batch_slug: Optional[str] = Field(None)
    batch_start: Optional[str] = Field(None)
    batch_end: Optional[str] = Field(None)


class GetBatchesResponse(BaseModel):
    success: bool = Field(...)
    error: Optional[str] = Field(None)
    data: Optional[List[BatchItem]] = None
    status_code: int = Field(...)


class TeacherModel(BaseModel):
    t_id: Optional[str] = None
    t_name: Optional[str] = None
    t_exp: Optional[Any] = None
    t_qual: Optional[str] = None
    t_email: Optional[str] = None


class SubjectModel(BaseModel):
    subject_id: Optional[str] = None
    subject_name: Optional[str] = None
    subject_slug: Optional[str] = None
    tag: Optional[Any] = None
    order: Optional[Any] = None
    lecture: Optional[Any] = None
    teachers: List[TeacherModel] = Field(default_factory=list)


class BatchDataModel(BaseModel):
    batch_id: Optional[str] = None
    batch_name: Optional[str] = None
    order: Optional[Any] = None
    expiry: Optional[Any] = None
    subjects: List[SubjectModel] = Field(default_factory=list)


class StandardResponseModel(BaseModel):
    success: bool
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    status_code: int


class ChapterModel(BaseModel):
    chapter_id: Optional[str] = Field(None)
    chapter_name: Optional[str] = Field(None)
    type: Optional[str] = Field(None)
    order: Optional[int] = Field(None)
    notes: Optional[Any] = Field(None)
    exercises: Optional[Any] = Field(None)
    videos: Optional[Any] = Field(None)
    lecture_videos: Optional[Any] = Field(None)
    chapter_slug: Optional[str] = Field(None)


class ChaptersBySubjectModel(RootModel[Dict[Any, List[ChapterModel]]]):
    pass


class ChapterRequestModel(BaseModel):
    subject_ids: List[Any] = Field(
        ..., description="List of subject IDs to fetch chapters for"
    )
    refetch: Optional[bool] = Field(
        False, description="Bypass cache and fetch fresh data"
    )


class ChapterContentDocModel(BaseModel):
    doc_id: str = Field(..., description="Document ID")
    doc_type: Optional[str] = Field(None, description="Document type (note, dpp, etc.)")
    doc_url: str = Field(..., description="Full URL to the document file")
    doc_name: Optional[str] = Field(None, description="Original document name")
    date: str = Field(..., description="Date associated with the content")


class ChapterContentRequest(BaseModel):
    chapter_ids: List[str] = Field(..., description="List of chapter IDs")
    content_type: Optional[str] = Field("ALL", description="Type of content to filter")
    refetch: Optional[bool] = Field(False, description="Bypass cache and force refetch")


class StandardResponse(BaseModel):
    success: bool
    error: Optional[str]
    data: Optional[Any]
    status_code: int


class TestPerformanceModel(BaseModel):
    total_marks: Optional[float] = None
    user_marks: Optional[float] = None
    time_taken: Optional[int] = None
    total_questions: Optional[int] = None
    attempted_questions: Optional[int] = None
    unattempted_questions: Optional[int] = None
    correct_questions: Optional[int] = None
    incorrect_questions: Optional[int] = None
    accuracy: Optional[float] = None
    completed: Optional[bool] = None
    incorrect_score: Optional[float] = None
    unattempted_score: Optional[float] = None


class TestEntryModel(BaseModel):
    order: Optional[str]
    type: Optional[str]
    attempted: bool = False
    attempt_id: Optional[str]
    test_id: Optional[str]
    test_name: Optional[str]
    total_marks: Optional[float]
    total_questions: Optional[int]
    date: Optional[str]
    performance: Optional[TestPerformanceModel]


class DPPTestsData(BaseModel):
    tests: List[TestEntryModel] = Field(default_factory=list)


from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class SolutionDescriptionModel(BaseModel):
    sol_id: Optional[str] = Field(None)
    sol_name: Optional[str] = Field(None)
    endlink: Optional[str] = Field(None)


class DPPQuestionModel(BaseModel):
    question_id: Optional[str] = Field(None)
    question_name: Optional[str] = Field(None)
    endlink: Optional[str] = Field(None)
    order: Optional[int] = Field(None)
    positive_marks: Optional[float] = Field(None)
    negative_marks: Optional[float] = Field(None)
    difficulty: Optional[str] = Field(None)
    solutions: Optional[List[str]] = Field(default=None)
    solution_descriptions: Optional[List[SolutionDescriptionModel]] = Field(
        default=None
    )


class DPPTestSolutionResponse(BaseModel):
    success: bool = Field(..., description="Whether the request succeeded")
    error: Optional[str] = Field(None, description="Error message if any")
    data: Optional[Dict[str, Any]] = Field(
        None, description="Response payload such as questions"
    )
    status_code: int = Field(..., description="HTTP status code returned by API")
