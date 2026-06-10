from pydantic import BaseModel, Field
from typing import List, Optional


class BatchResponse(BaseModel):
    id: str
    cohort_id: str | None = Field(default=None)
    batch_category_id: str | None = Field(default=None)
    batch_category_ids: list[str] = []
    exam: list[str] = []
    name: str
    slug: str | None = Field(default=None)
    is_purchased: bool | None = Field(default=None)
    is_free: bool | None = Field(default=None)
    is_batch_plus: bool | None = Field(default=None)
    board: str | None = Field(default=None)
    academic_level: str | None = Field(default=None)
    start_date: str | None = Field(default=None)
    end_date: str | None = Field(default=None)
    expiry_date: str | None = Field(default=None)


class Fee(BaseModel):
    amount: Optional[float] = None
    discount: Optional[float] = None
    total: Optional[float] = None


class TeacherBrief(BaseModel):
    id: str
    firstName: str
    lastName: Optional[str] = None
    email: Optional[str] = None

    class Config:
        populate_by_name = True


class Subject(BaseModel):
    id: str
    subject: Optional[str] = None
    subject_id: str
    slug: Optional[str] = None
    teachers: List[TeacherBrief] = Field(default_factory=list)
    tag_count: Optional[int] = Field(None)
    batch_id: Optional[str] = Field(None)
    order: Optional[int] = Field(None)
    lecture_count: Optional[int] = Field(None)

    class Config:
        populate_by_name = True


class BatchDetailResponse(BaseModel):
    is_security_enabled: Optional[bool] = Field(None)
    exam_year: Optional[str] = Field(None)
    expiry_days: Optional[int] = Field(None)
    fee: Optional[Fee] = None
    subjects: List[Subject] = Field(default_factory=list)

    class Config:
        populate_by_name = True
