from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass
class LectureOverview:
    completedChapter: Optional[int] = None
    completedLectures: Optional[int] = None
    totalWatchTime: Optional[int] = None
    totalChapters: Optional[int] = None
    totalLectures: Optional[int] = None

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Optional["LectureOverview"]:
        if not isinstance(data, dict):
            return None
        return cls(
            completedChapter=data.get("completedChapter"),
            completedLectures=data.get("completedLectures"),
            totalWatchTime=data.get("totalWatchTime"),
            totalChapters=data.get("totalChapters"),
            totalLectures=data.get("totalLectures"),
        )


@dataclass
class LectureSubjectStat:
    subjectName: Optional[str]
    completedChapter: Optional[int]
    completedLectures: Optional[int]
    totalWatchTime: Optional[int]
    totalLectures: Optional[int]
    totalChapters: Optional[int]

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> Optional["LectureSubjectStat"]:
        if not isinstance(payload, dict):
            return None

        return cls(
            subjectName=payload.get("subjectName"),
            completedChapter=payload.get("completedChapter"),
            completedLectures=payload.get("completedLectures"),
            totalWatchTime=payload.get("totalWatchTime"),
            totalLectures=payload.get("totalLectures"),
            totalChapters=payload.get("totalChapters"),
        )

@dataclass
class QuizOverviewItem:
    key: str
    accuracy: Optional[float]
    marksObtained: Optional[int]
    correctQuestions: Optional[int]
    completedQuiz: Optional[int]
    totalQuiz: Optional[int]

    @classmethod
    def from_json(cls, obj: Dict[str, Any]) -> Optional["QuizOverviewItem"]:
        if "key" not in obj:
            return None  # mandatory field missing

        return cls(
            key=obj.get("key"),
            accuracy=obj.get("accuracy"),
            marksObtained=obj.get("marksObtained"),
            correctQuestions=obj.get("correctQuestions"),
            completedQuiz=obj.get("completedQuiz"),
            totalQuiz=obj.get("totalQuiz"),
        )


@dataclass
class QuizSubject:
    subjectName: Optional[str]
    accuracy: Optional[float]
    marksObtained: Optional[float]
    totalQuestions: Optional[int]
    correctQuestions: Optional[int]
    attemptedQuestions: Optional[int]
    attempted: Optional[int]
    totalQuiz: Optional[int]

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Optional["QuizSubject"]:
        if not isinstance(data, dict):
            return None
        subject_block = data.get("subjectId", {})
        subject_name = (
            subject_block.get("name") if isinstance(subject_block, dict) else None
        )

        try:
            return cls(
                subjectName=subject_name,
                accuracy=data.get("accuracy"),
                marksObtained=data.get("marksObtained"),
                totalQuestions=data.get("totalQuestions"),
                correctQuestions=data.get("correctQuestions"),
                attemptedQuestions=data.get("attemptedQuestions"),
                attempted=data.get("attempted"),
                totalQuiz=data.get("totalQuiz"),
            )
        except Exception:
            return None
