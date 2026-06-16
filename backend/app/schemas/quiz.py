from pydantic import BaseModel, Field
from typing import Optional, List


class QuizDetailResponse(BaseModel):
    id: str
    name: Optional[str] = Field(None)
    total_attempts: Optional[int] = Field(None)
    difficulty_level: str
    slug: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    student_count: Optional[int] = Field(None)
    student_mapping_id: Optional[str] = Field(None)
    student_mapping_status: Optional[str] = Field(None)
    student_mapping_source: Optional[str] = Field(None)
    tag1: Optional[str] = Field(None)
    tag2: Optional[str] = Field(None)


class SubTopicModel(BaseModel):
    id: str
    total_questions: Optional[str] = Field(None)
    un_attempted_questions: Optional[str] = Field(None)
    correct_questions: Optional[str] = Field(None)
    incorrect_questions: Optional[str] = Field(None)
    questions_review: Optional[str] = Field(None)
    subtopic_name: Optional[str] = Field(None)


class TopicModel(BaseModel):
    id: str
    total_questions: Optional[str] = Field(None)
    un_attempted_questions: Optional[str] = Field(None)
    correct_questions: Optional[str] = Field(None)
    incorrect_questions: Optional[str] = Field(None)
    questions_review: Optional[str] = Field(None)
    topic_name: Optional[str] = Field(None)
    sub_topics: List[SubTopicModel] = Field(default_factory=list)


class ChapterModel(BaseModel):
    id: str
    total_questions: Optional[str] = Field(None)
    un_attempted_questions: Optional[str] = Field(None)
    correct_questions: Optional[str] = Field(None)
    incorrect_questions: Optional[str] = Field(None)
    questions_review: Optional[str] = Field(None)
    chapter_name: Optional[str] = Field(None)
    chapter_id: Optional[str] = Field(None)  # flattened _id
    topics: List[TopicModel] = Field(default_factory=list)


class SubjectModel(BaseModel):
    id: str
    total_questions: Optional[str] = Field(None)
    un_attempted_questions: Optional[str] = Field(None)
    correct_questions: Optional[str] = Field(None)
    incorrect_questions: Optional[str] = Field(None)
    questions_review: Optional[str] = Field(None)
    subject_name: Optional[str] = Field(None)
    chapters: List[ChapterModel] = Field(default_factory=list)


class SectionModel(BaseModel):
    id: str
    total_questions: Optional[str] = Field(None)
    un_attempted_questions: Optional[str] = Field(None)
    correct_questions: Optional[str] = Field(None)
    incorrect_questions: Optional[str] = Field(None)
    questions_review: Optional[str] = Field(None)
    subjects: List[SubjectModel] = Field(default_factory=list)


class SolutionDescriptionModel(BaseModel):
    sol_image_name: Optional[str] = Field(None)
    sol_image_url: Optional[str] = Field(None)


class YourResultModel(BaseModel):
    is_under_review: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    marked_solutions: List[str] = Field(default_factory=list)
    marked_solution_text: Optional[str] = Field(None)
    score: Optional[str] = Field(None)
    score_str: Optional[str] = Field(None)
    time_taken: Optional[str] = Field(None)


class QuestionModel(BaseModel):
    id: str
    q_type: Optional[str] = Field(None)
    q_number: Optional[str] = Field(None)
    pos_marks: Optional[str] = Field(None)
    neg_marks: Optional[str] = Field(None)
    image_name: Optional[str] = Field(None)
    image_url: Optional[str] = Field(None)
    options: List[str] = Field(default_factory=list)
    diff_level: Optional[str] = Field(None)
    topic_name: Optional[str] = Field(None)
    section_id: Optional[str] = Field(None)
    subject_id: Optional[str] = Field(None)
    chapter_id: Optional[str] = Field(None)
    subtopic_id: Optional[str] = Field(None)
    solutions: List[str] = Field(default_factory=list)
    solution_description: List[SolutionDescriptionModel] = Field(default_factory=list)
    your_result: Optional[YourResultModel] = Field(None)


class ResponseModel(BaseModel):
    id: str
    sections: List[SectionModel] = Field(default_factory=list)
    questions: List[QuestionModel] = Field(default_factory=list)
