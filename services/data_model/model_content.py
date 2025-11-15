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
