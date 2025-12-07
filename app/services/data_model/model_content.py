from dataclasses import dataclass
from typing import Optional, Any, Dict, List


@dataclass
class BatchRecord:
    batch_id: Optional[str]
    batch_name: Optional[str]
    batch_slug: Optional[str]
    batch_start: Optional[str]
    batch_end: Optional[str]

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Optional["BatchRecord"]:
        if not isinstance(data, dict):
            return None
        return cls(
            batch_id=data.get("_id"),
            batch_name=data.get("name"),
            batch_slug=data.get("slug"),
            batch_start=data.get("startDate"),
            batch_end=data.get("endDate"),
        )


@dataclass
class TeacherInfo:
    t_id: Optional[str]
    t_name: Optional[str]
    t_exp: Optional[Any]
    t_qual: Optional[str]
    t_email: Optional[str]

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Optional["TeacherInfo"]:
        if data is None:
            return None
        return cls(
            t_id=data.get("_id"),
            t_name=data.get("t_name") or data.get("name") or None,
            t_exp=data.get("experience"),
            t_qual=data.get("qualification"),
            t_email=data.get("email"),
        )


@dataclass
class SubjectInfo:
    subject_id: Optional[str]
    subject_name: Optional[str]
    subject_slug: Optional[str]
    tag: Optional[Any]
    order: Optional[Any]
    lecture: Optional[Any]
    teachers: List[TeacherInfo]

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Optional["SubjectInfo"]:
        if data is None:
            return None
        if "_id" not in data:
            return None
        teachers_raw = data.get("teacherIds", []) or []
        teachers = []
        for t in teachers_raw:
            full_name = f"{t.get('firstName', '')} {t.get('lastName', '')}".strip()
            t_parsed = TeacherInfo.from_json(
                {
                    "_id": t.get("_id"),
                    "t_name": full_name,
                    "experience": t.get("experience"),
                    "qualification": t.get("qualification"),
                    "email": t.get("email"),
                }
            )
            if t_parsed:
                teachers.append(t_parsed)
        return cls(
            subject_id=data.get("_id"),
            subject_name=data.get("subject"),
            subject_slug=data.get("slug"),
            tag=data.get("tagCount"),
            order=data.get("displayOrder"),
            lecture=data.get("lectureCount"),
            teachers=teachers,
        )


@dataclass
class BatchInfo:
    batch_id: Optional[str]
    batch_name: Optional[str]
    order: Optional[Any]
    expiry: Optional[Any]
    subjects: List[SubjectInfo]

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Optional["BatchInfo"]:
        if data is None:
            return None
        if "_id" not in data:
            return None
        subjects_raw = data.get("subjects", []) or []
        subjects = []
        for s in subjects_raw:
            parsed = SubjectInfo.from_json(s)
            if parsed:
                subjects.append(parsed)
        return cls(
            batch_id=data.get("_id"),
            batch_name=data.get("batchName"),
            order=data.get("displayOrder"),
            expiry=data.get("expiryDays"),
            subjects=subjects,
        )


@dataclass
class ChapterItem:
    chapter_id: Optional[str]
    chapter_name: Optional[str]
    type: Optional[str]
    order: Optional[int]
    notes: Optional[Any]
    exercises: Optional[Any]
    videos: Optional[Any]
    lecture_videos: Optional[Any]
    chapter_slug: Optional[str]

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Optional["ChapterItem"]:
        required = ["_id", "name"]
        if any(key not in data or data[key] is None for key in required):
            return None
        return cls(
            chapter_id=data.get("_id"),
            chapter_name=data.get("name"),
            type=data.get("type"),
            order=data.get("displayOrder"),
            notes=data.get("notes"),
            exercises=data.get("exercises"),
            videos=data.get("videos"),
            lecture_videos=data.get("lectureVideos"),
            chapter_slug=data.get("slug"),
        )


@dataclass
class ChapterContentDoc:
    doc_id: str
    doc_type: Optional[str]
    doc_url: str
    doc_name: Optional[str]
    date: str

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Optional["ChapterContentDoc"]:
        required = ["doc_id", "doc_url", "date"]
        if not all(key in data and data[key] is not None for key in required):
            return None

        return cls(
            doc_id=str(data.get("doc_id")),
            doc_type=data.get("doc_type"),
            doc_url=str(data.get("doc_url")),
            doc_name=data.get("doc_name"),
            date=str(data.get("date")),
        )


@dataclass
class TestPerformance:
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

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Optional["TestPerformance"]:
        if not isinstance(data, dict):
            return None
        return cls(
            total_marks=data.get("total_marks"),
            user_marks=data.get("user_marks"),
            time_taken=data.get("time_taken"),
            total_questions=data.get("total_questions"),
            attempted_questions=data.get("attempted_questions"),
            unattempted_questions=data.get("unattempted_questions"),
            correct_questions=data.get("correct_questions"),
            incorrect_questions=data.get("incorrect_questions"),
            accuracy=data.get("accuracy"),
            completed=data.get("completed"),
            incorrect_score=data.get("incorrect_score"),
            unattempted_score=data.get("unattempted_score"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_marks": self.total_marks,
            "user_marks": self.user_marks,
            "time_taken": self.time_taken,
            "total_questions": self.total_questions,
            "attempted_questions": self.attempted_questions,
            "unattempted_questions": self.unattempted_questions,
            "correct_questions": self.correct_questions,
            "incorrect_questions": self.incorrect_questions,
            "accuracy": self.accuracy,
            "completed": self.completed,
            "incorrect_score": self.incorrect_score,
            "unattempted_score": self.unattempted_score,
        }


@dataclass
class TestEntry:
    order: Optional[str]
    type: Optional[str]
    attempted: bool
    attempt_id: Optional[str]
    test_id: Optional[str]
    test_name: Optional[str]
    total_marks: Optional[float]
    total_questions: Optional[int]
    date: Optional[str]
    performance: Optional[TestPerformance]

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Optional["TestEntry"]:
        required = ["order", "type", "attempted", "test_id", "test_name"]
        for key in required:
            if key not in data:
                return None

        perf = (
            TestPerformance.from_json(data.get("performance"))
            if isinstance(data.get("performance"), dict)
            else None
        )

        return cls(
            order=data.get("order"),
            type=data.get("type"),
            attempted=data.get("attempted", False),
            attempt_id=data.get("attempt_id"),
            test_id=data.get("test_id"),
            test_name=data.get("test_name"),
            total_marks=data.get("total_marks"),
            total_questions=data.get("total_questions"),
            date=data.get("date"),
            performance=perf,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order": self.order,
            "type": self.type,
            "attempted": self.attempted,
            "attempt_id": self.attempt_id,
            "test_id": self.test_id,
            "test_name": self.test_name,
            "total_marks": self.total_marks,
            "total_questions": self.total_questions,
            "date": self.date,
            "performance": (self.performance.to_dict() if self.performance else None),
        }


@dataclass
class DPPTestSolutionItem:
    question_id: Optional[str]
    question_name: Optional[str]
    endlink: Optional[str]
    order: Optional[int]
    positive_marks: Optional[float]
    negative_marks: Optional[float]
    difficulty: Optional[str]
    solutions: Optional[List[str]]
    solution_descriptions: Optional[List[Dict[str, Optional[str]]]]

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Optional["DPPTestSolutionItem"]:
        if "order" not in data:
            return None  # required

        return cls(
            question_id=data.get("question_id"),
            question_name=data.get("question_name"),
            endlink=data.get("endlink"),
            order=data.get("order"),
            positive_marks=data.get("positive_marks"),
            negative_marks=data.get("negative_marks"),
            difficulty=data.get("difficulty"),
            solutions=data.get("solutions"),
            solution_descriptions=data.get("solution_descriptions"),
        )
