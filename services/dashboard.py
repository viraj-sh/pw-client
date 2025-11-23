from datetime import timedelta
from core.utils import EnvManager, standard_response
from core.logging import setup_logging
from core.cache import cached_request, invalidate_cache
from core.exceptions import handle_exception
from typing import Optional, Any, Dict, List
from .data_model.model_dashboard import (
    LectureOverview,
    LectureSubjectStat,
    QuizOverviewItem,
    QuizSubject,
)

def fetch_lecture_overview(batch_id: str, refetch: bool = False) -> Dict[str, Any]:

    logger = setup_logging(name="core.fetch_lecture_overview", level="INFO")

    try:
        token = EnvManager.get("TOKEN", default=None)

        if not token:
            logger.warning("TOKEN is missing in environment variables.")
            return standard_response(
                success=False,
                error="Missing authentication token.",
                status_code=400,
            )

        url = "https://api.penpencil.co/v3/performance/lecture"
        params = {"batchId": batch_id}
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        response = cached_request(
            method="GET",
            url=url,
            headers=headers,
            params=params,
            expire_after=timedelta(minutes=5),
            log_prefix="[PenPencilAPI] ",
            refetch=refetch,
        )

        if response is None or not hasattr(response, "status_code"):
            logger.warning("Invalid or no response received from API.")
            return standard_response(
                False,
                error="Invalid or empty response from server.",
                status_code=502,
            )

        if response.status_code >= 400:
            invalidate_cache(response)
            logger.warning(f"API returned error: {response.status_code}")
            return standard_response(
                False,
                error=f"API error: {response.status_code}",
                status_code=response.status_code,
            )

        try:
            json_body = response.json()
        except Exception:
            invalidate_cache(response)
            logger.warning("Response JSON parsing failed.")
            return standard_response(
                False,
                error="Failed to parse API response JSON.",
                status_code=500,
            )

        raw_data = json_body.get("data", {})
        overview_obj = LectureOverview.from_json(raw_data)

        if overview_obj is None:
            logger.warning("Failed to parse lecture overview data.")
            return standard_response(
                False,
                error="Invalid lecture overview data.",
                status_code=500,
            )

        result_data = overview_obj.__dict__

        logger.info("Lecture overview fetched successfully.")
        return standard_response(
            True,
            data=result_data,
            status_code=200,
        )

    except Exception as exc:
        return handle_exception(logger, exc, context="fetch_lecture_overview")


def fetch_lecture_subjects(batch_id: str, refetch: bool = False) -> Dict[str, Any]:


    logger = setup_logging(name="core.fetch_lecture_subjects", level="INFO")

    try:
        token = EnvManager.get("TOKEN", default=None)
        if not token:
            logger.warning("Missing TOKEN in EnvManager.")
            return standard_response(
                success=False,
                error="Authorization token missing.",
                status_code=400,
            )

        url = "https://api.penpencil.co/v3/performance/lecture/subjects"
        params = {"batchId": batch_id}
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        response = cached_request(
            method="GET",
            url=url,
            headers=headers,
            params=params,
            log_prefix="[LectureSubjects] ",
            expire_after=timedelta(minutes=10),
            refetch=refetch,
        )

        if response is None:
            return standard_response(
                success=False,
                error="No response from lecture subjects API.",
                status_code=400,
            )

        try:
            json_data = response.json()
        except ValueError:
            invalidate_cache(response)
            logger.warning("Invalid JSON response received — cache invalidated.")
            return standard_response(
                success=False,
                error="Invalid JSON in API response.",
                status_code=400,
            )

        if not isinstance(json_data, dict) or "data" not in json_data:
            invalidate_cache(response)
            logger.warning(
                "API response missing expected 'data' field — cache invalidated."
            )
            return standard_response(
                success=False,
                error="Invalid response from lecture subjects API.",
                status_code=400,
            )

        raw_items = json_data.get("data", [])
        parsed_items: List[LectureSubjectStat] = []

        for item in raw_items:
            subject = item.get("subjectId", {}) or {}

            payload = {
                "subjectName": subject.get("name"),
                "completedChapter": item.get("completedChapter"),
                "completedLectures": item.get("completedLectures"),
                "totalWatchTime": item.get("totalWatchTime"),
                "totalLectures": item.get("totalLectures"),
                "totalChapters": item.get("totalChapters"),
            }

            parsed = LectureSubjectStat.from_json(payload)
            if parsed:
                parsed_items.append(parsed)
            else:
                logger.warning(f"Skipping invalid subject entry: {item!r}")

        result_data = [vars(obj) for obj in parsed_items]

        return standard_response(
            success=True,
            data=result_data,
            status_code=200,
        )

    except Exception as exc:
        return handle_exception(logger, exc, context="fetch_lecture_subjects")

def fetch_quiz_overview(batch_id: str, refetch: bool = False) -> Dict[str, Any]:
    logger = setup_logging(name="core.fetch_quiz_overview", level="INFO")
    log_prefix = "[QuizOverviewAPI] "

    try:
        token = EnvManager.get("TOKEN")
        if not token:
            logger.warning(f"{log_prefix}Missing TOKEN in environment.")
            return standard_response(
                success=False, error="Authentication token not found.", status_code=400
            )

        url = "https://api.penpencil.co/v3/performance/quiz"
        params = {"batchId": batch_id}
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        response = cached_request(
            method="GET",
            url=url,
            headers=headers,
            params=params,
            log_prefix=log_prefix,
            expire_after=timedelta(minutes=10),
            refetch=refetch,
        )

        if response is None:
            logger.warning(f"{log_prefix}No response returned.")
            return standard_response(
                False, error="No response received", status_code=400
            )

        if response.status_code != 200:
            logger.warning(f"{log_prefix}Non-200 status: {response.status_code}")
            invalidate_cache(response)
            return standard_response(
                False,
                error=f"Failed to fetch quiz overview (status {response.status_code})",
                status_code=response.status_code,
            )

        json_body = response.json()
        if not json_body or "data" not in json_body:
            logger.warning(f"{log_prefix}Invalid or empty JSON response.")
            invalidate_cache(response)
            return standard_response(
                False, error="Invalid response format", status_code=400
            )

        raw_items: List[Dict[str, Any]] = json_body.get("data", [])
        parsed_items: List[Dict[str, Any]] = []

        for item in raw_items:
            value = item.get("value", {})
            merged = {
                "key": item.get("key"),
                "accuracy": value.get("accuracy"),
                "marksObtained": value.get("marksObtained"),
                "correctQuestions": value.get("correctQuestions"),
                "completedQuiz": value.get("completedQuiz"),
                "totalQuiz": value.get("totalQuiz"),
            }

            dataclass_obj = QuizOverviewItem.from_json(merged)
            if dataclass_obj:
                parsed_items.append(dataclass_obj.__dict__)

        return standard_response(
            success=True, data={"quiz_overview": parsed_items}, status_code=200
        )

    except Exception as exc:
        return handle_exception(logger, exc, context="fetch_quiz_overview")


def fetch_quiz_subjects(
    batch_id: str, quiz_type: str = "OBJECTIVE", refetch: bool = False
) -> Dict[str, Any]:
    """
    Fetch quiz subject performance overview for a given batch.
    Uses cached_request, EnvManager for token, full logging, typed dataclass parsing.
    """

    logger = setup_logging(name="core.fetch_quiz_subjects", level="INFO")
    log_prefix = "[QuizSubjectsAPI] "

    try:
        token = EnvManager.get("TOKEN", default=None)
        if not token:
            logger.warning(f"{log_prefix}TOKEN missing in environment.")
            return standard_response(
                success=False,
                error="Missing TOKEN environment variable.",
                status_code=400,
            )

        url = "https://api.penpencil.co/v3/performance/quiz/subjects"
        params = {"batchId": batch_id, "type": quiz_type}
        headers = {
            "Authorization": token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        logger.info(
            f"{log_prefix}Requesting quiz subjects for batch={batch_id}, type={quiz_type}"
        )

        response = cached_request(
            method="GET",
            url=url,
            headers=headers,
            params=params,
            expire_after=timedelta(minutes=10),
            refetch=refetch,
            log_prefix=log_prefix,
        )

        if response is None:
            return standard_response(
                success=False,
                error="Failed to execute request.",
                status_code=400,
            )

        try:
            json_data = response.json()
        except Exception:
            logger.warning(f"{log_prefix}Invalid JSON received.")
            invalidate_cache(response)
            return standard_response(
                success=False,
                error="Invalid JSON response from upstream API.",
                status_code=400,
            )

        items = json_data.get("data", [])
        if not isinstance(items, list):
            logger.warning(f"{log_prefix}Unexpected data format.")
            invalidate_cache(response)
            return standard_response(
                success=False,
                error="Unexpected API response structure.",
                status_code=400,
            )

        subjects: List[Dict[str, Any]] = []

        for item in items:
            parsed = QuizSubject.from_json(item)
            if parsed:
                subjects.append(parsed.__dict__)
            else:
                logger.warning(f"{log_prefix}Skipping invalid subject entry: {item}")

        return standard_response(
            success=True,
            data={"subjects": subjects},
            status_code=200,
        )

    except Exception as exc:
        return handle_exception(logger, exc, context="fetch_quiz_subjects")
