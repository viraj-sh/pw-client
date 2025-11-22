from datetime import timedelta
from core.utils import EnvManager, standard_response
from core.logging import setup_logging
from core.cache import cached_request, invalidate_cache
from core.exceptions import handle_exception
from .data_model.model_content import (
    BatchRecord,
    BatchInfo,
    ChapterItem,
    ChapterContentDoc,
    TestEntry,
    TestPerformance,
    DPPTestSolutionItem,
)
from typing import Optional, Any, Dict, List


def get_batches(amount: str = "", refetch: bool = False) -> Dict[str, Any]:
    logger = setup_logging(name="core.get_batches", level="INFO")

    try:
        token = EnvManager.get("TOKEN", default=None)
        if not token:
            return standard_response(
                False, error="Missing TOKEN in environment", status_code=400
            )

        if amount not in ("", "free", "paid"):
            return standard_response(
                False, error="Invalid amount value", status_code=400
            )

        url = "https://api.penpencil.co/batch-service/v1/batches/purchased-batches"
        params = {"type": "ALL", "amount": amount}

        headers = {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0",
            "authorization": token,
            "origin": "https://www.pw.live",
            "referer": "https://www.pw.live/",
            "client-type": "WEB",
        }

        response = cached_request(
            method="GET",
            url=url,
            headers=headers,
            params=params,
            log_prefix="[PenPencilAPI] ",
            expire_after=timedelta(minutes=10),
            refetch=refetch,
        )

        if response is None:
            return standard_response(
                False, error="No response received", status_code=400
            )

        try:
            result = response.json()
        except Exception:
            invalidate_cache(response)
            return standard_response(
                False, error="Invalid JSON response", status_code=400
            )

        if not result.get("success"):
            invalidate_cache(response)
            err = result.get("error", {})
            msg = err.get("message", "Unknown error")
            status = err.get("status", "Unknown")
            return standard_response(
                False, error=f"Error {status}: {msg}", status_code=400
            )

        raw_items = result.get("data", [])
        batches: List[Dict[str, Any]] = []

        for item in raw_items:
            parsed = BatchRecord.from_json(item)
            if parsed:
                batches.append(
                    {
                        "batch_id": parsed.batch_id,
                        "batch_name": parsed.batch_name,
                        "batch_slug": parsed.batch_slug,
                        "batch_start": parsed.batch_start,
                        "batch_end": parsed.batch_end,
                    }
                )

        return standard_response(True, data=batches, status_code=200)

    except Exception as exc:
        return handle_exception(logger, exc, context="get_batches")


def get_sub(batch_id: str, refetch: bool = False) -> Dict[str, Any]:
    logger = setup_logging(name="core.get_sub", level="INFO")

    try:
        token = EnvManager.get("TOKEN", default=None)
        if not token:
            return standard_response(False, error="Missing TOKEN", status_code=400)

        url = f"https://api.penpencil.co/v3/batches/{batch_id}/details"
        headers = {"Authorization": token, "client-type": "WEB"}

        response = cached_request(
            method="GET",
            url=url,
            headers=headers,
            log_prefix="[BatchAPI] ",
            expire_after=timedelta(minutes=10),
            refetch=refetch,
        )

        if not response or response.status_code != 200:
            invalidate_cache(response)
            return standard_response(
                False, error="Invalid response from upstream", status_code=400
            )

        result = result = response.json()

        if not isinstance(result, dict):
            invalidate_cache(response)
            return standard_response(
                False, error="Malformed upstream response", status_code=400
            )

        data = result.get("data")
        parsed = BatchInfo.from_json(data)
        if not parsed:
            invalidate_cache(response)
            return standard_response(
                False, error="Failed to parse batch data", status_code=400
            )

        result_dict = {
            "batch_id": parsed.batch_id,
            "batch_name": parsed.batch_name,
            "order": parsed.order,
            "expiry": parsed.expiry,
            "subjects": [
                {
                    "subject_id": s.subject_id,
                    "subject_name": s.subject_name,
                    "subject_slug": s.subject_slug,
                    "tag": s.tag,
                    "order": s.order,
                    "lecture": s.lecture,
                    "teachers": [
                        {
                            "t_id": t.t_id,
                            "t_name": t.t_name,
                            "t_exp": t.t_exp,
                            "t_qual": t.t_qual,
                            "t_email": t.t_email,
                        }
                        for t in s.teachers
                    ],
                }
                for s in parsed.subjects
            ],
        }

        return standard_response(True, data=result_dict, status_code=200)

    except Exception as exc:
        return handle_exception(logger, exc, context="get_sub")


def get_ch(batch_id: str, subject_ids: Any, refetch: bool = False) -> Dict[str, Any]:
    logger = setup_logging(name="core.get_ch", level="INFO")

    try:
        token = EnvManager.get("TOKEN", default=None)
        if not token:
            return standard_response(
                False, error="Missing TOKEN in environment", status_code=400
            )

        if isinstance(subject_ids, list):
            subject_ids_str = ",".join(str(s) for s in subject_ids)
        else:
            subject_ids_str = str(subject_ids)

        url = f"https://api.penpencil.co/batch-service/v1/batch-tags/{batch_id}/topics"
        query = {"batchSubjectIds": subject_ids_str}

        headers = {"Authorization": token, "client-type": "WEB"}

        response = cached_request(
            method="GET",
            url=url,
            headers=headers,
            params=query,
            refetch=refetch,
            log_prefix="[PenPencilAPI] ",
            expire_after=timedelta(minutes=15),
        )

        if response is None or not response.ok:
            invalidate_cache(response)
            return standard_response(False, error="Request failed", status_code=400)

        payload = response.json() or {}
        items = payload.get("data", {}).get("data", [])

        chapters_by_subject: Dict[Any, List[Dict[str, Any]]] = {}

        for raw in items:
            type_id = raw.get("typeId")
            parsed = ChapterItem.from_json(raw)
            if not parsed:
                continue
            if type_id not in chapters_by_subject:
                chapters_by_subject[type_id] = []
            chapters_by_subject[type_id].append(
                {
                    "chapter_id": parsed.chapter_id,
                    "chapter_name": parsed.chapter_name,
                    "type": parsed.type,
                    "order": parsed.order,
                    "notes": parsed.notes,
                    "exercises": parsed.exercises,
                    "videos": parsed.videos,
                    "lecture_videos": parsed.lecture_videos,
                    "chapter_slug": parsed.chapter_slug,
                }
            )

        return standard_response(True, data=chapters_by_subject, status_code=200)

    except Exception as exc:
        return handle_exception(logger, exc, context="get_ch")


def get_ch_content(
    batch_id: str,
    subject_id: str,
    chapter_ids: List[str],
    content_type: str = "ALL",
    refetch: bool = False,
) -> Dict[str, Any]:
    logger = setup_logging(name="core.get_ch_content", level="INFO")

    try:
        token = EnvManager.get("TOKEN")
        if not token:
            return standard_response(
                success=False,
                error="Missing TOKEN in environment",
                status_code=400,
            )

        if isinstance(chapter_ids, str):
            chapter_ids = [chapter_ids]

        if content_type not in ["ALL", "DPP_PDF", "NOTES"]:
            return standard_response(
                success=False,
                error="content_type must be ALL, DPP_PDF, or NOTES",
                status_code=400,
            )

        content_types = (
            ["NOTES", "DPP_PDF"] if content_type == "ALL" else [content_type]
        )

        collected: List[ChapterContentDoc] = []

        for chapter_id in chapter_ids:
            for ctype in content_types:
                url = (
                    f"https://api.penpencil.co/batch-service/v3/"
                    f"batch-subject-schedules/{batch_id}/subject/{subject_id}/contents"
                )

                params = {
                    "skip": "0",
                    "limit": "20",
                    "contentType": ctype,
                    "contentFilter": "ALL",
                    "tagId": chapter_id,
                }

                headers = {"Authorization": f"{token}"}

                resp = cached_request(
                    method="GET",
                    url=url,
                    params=params,
                    headers=headers,
                    log_prefix="[ChContentAPI] ",
                    expire_after=timedelta(minutes=10),
                    refetch=refetch,
                )

                if not resp or "data" not in resp:
                    logger.warning("Invalid response; cache invalidated")
                    invalidate_cache(resp)
                    continue

                items = resp.get("data", [])

                for item in items:
                    date = item.get("data", {}).get("date", "")
                    homework_list = item.get("data", {}).get("homeworkIds", [])

                    for hw in homework_list:
                        doc_type = hw.get("note")
                        for att in hw.get("attachmentIds", []):
                            raw = {
                                "doc_id": att.get("_id"),
                                "doc_type": doc_type,
                                "doc_url": str(att.get("baseUrl", ""))
                                + str(att.get("key", "")),
                                "doc_name": att.get("name"),
                                "date": date,
                            }

                            parsed = ChapterContentDoc.from_json(raw)
                            if parsed:
                                collected.append(parsed)

        result = [
            {
                "doc_id": d.doc_id,
                "doc_type": d.doc_type,
                "doc_url": d.doc_url,
                "doc_name": d.doc_name,
                "date": d.date,
            }
            for d in collected
        ]

        return standard_response(
            success=True,
            data=result,
            status_code=200,
        )

    except Exception as exc:
        return handle_exception(logger, exc, context="get_ch_content")


def fetch_dpp_tests(
    batch_id: str,
    subject_id: str,
    chapter_id: str,
    page: int = 1,
    limit: int = 20,
    dpp_type: str = "ALL",
    refetch: bool = False,
) -> Dict[str, Any]:

    logger = setup_logging(name="core.fetch_dpp_tests", level="INFO")

    try:
        logger.info("Fetching API token using EnvManager...")
        token = EnvManager.get("TOKEN", default=None)

        if not token:
            return standard_response(
                success=False,
                error="Missing TOKEN in environment",
                status_code=400,
            )

        base_url = "https://api.penpencil.co/v3/test-service/tests/new-dpp-list"
        params = {
            "page": page,
            "batchId": batch_id,
            "batchSubjectId": subject_id,
            "chapterId": chapter_id,
            "dppType": dpp_type,
            "limit": limit,
        }

        headers = {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (compatible; PenPencilFetcher/1.0)",
            "origin": "https://www.pw.live",
            "referer": "https://www.pw.live/",
            "authorization": token,
        }

        response = cached_request(
            method="GET",
            url=base_url,
            params=params,
            headers=headers,
            expire_after=timedelta(minutes=10),
            log_prefix="[DPPList] ",
            refetch=refetch,
        )

        try:
            payload = response.json()
        except Exception:
            invalidate_cache(response)
            return standard_response(
                False, error="Invalid JSON from DPP API", status_code=400
            )

        if (
            not isinstance(payload, dict)
            or "data" not in payload
            or not isinstance(payload["data"], list)
        ):
            invalidate_cache(response)
            return standard_response(
                False,
                error="Unexpected or malformed DPP response",
                status_code=400,
            )

        data_list = payload.get("data", [])
        results: List[TestEntry] = []

        for item in data_list:
            quiz_details = item.get("dppQuizDetails", {})
            test_data = quiz_details.get("test", {})

            tag = (quiz_details.get("tag") or "").lower()
            attempted = tag == "reattempt"
            attempt_id = (
                quiz_details.get("testStudentMapping", {}).get("_id")
                if attempted
                else None
            )

            performance_obj = None

            if attempted and attempt_id:
                result_url = (
                    f"https://api.penpencil.co/v3/test-service/tests/"
                    f"{test_data.get('_id')}/my-result"
                )

                result_response = cached_request(
                    method="GET",
                    url=result_url,
                    headers=headers,
                    expire_after=timedelta(minutes=10),
                    log_prefix="[DPPResult] ",
                    refetch=refetch,
                )

                try:
                    result_json = result_response.json()
                except Exception:
                    invalidate_cache(result_response)
                    result_json = {}

                perf = (
                    result_json.get("data", {}).get("yourPerformance", {})
                    if isinstance(result_json, dict)
                    else {}
                )

                performance_obj = TestPerformance.from_json(
                    {
                        "total_marks": perf.get("totalScore"),
                        "user_marks": perf.get("userScore"),
                        "time_taken": perf.get("timeTaken"),
                        "total_questions": perf.get("totalQuestions"),
                        "attempted_questions": perf.get("attemptedQuestions"),
                        "unattempted_questions": perf.get("unAttemptedQuestions"),
                        "correct_questions": perf.get("correctQuestions"),
                        "incorrect_questions": perf.get("inCorrectQuestions"),
                        "accuracy": perf.get("accuracy"),
                        "completed": perf.get("completed"),
                        "incorrect_score": perf.get("inCorrectScore"),
                        "unattempted_score": perf.get("unAttemptedScore"),
                    }
                )

            entry_dict = {
                "order": item.get("_id"),
                "type": item.get("type"),
                "attempted": attempted,
                "attempt_id": attempt_id,
                "test_id": test_data.get("_id"),
                "test_name": test_data.get("name"),
                "total_marks": test_data.get("totalMarks"),
                "total_questions": test_data.get("totalQuestions"),
                "date": test_data.get("createdAt"),
                "performance": (performance_obj.__dict__ if performance_obj else None),
            }

            entry_obj = TestEntry.from_json(entry_dict)
            if entry_obj:
                results.append(entry_obj)

        return standard_response(
            True, data={"tests": [i.to_dict() for i in results]}, status_code=200
        )

    except Exception as exc:
        return handle_exception(logger, exc, context="fetch_dpp_tests")


def fetch_dpp_test_sol(
    attempt_id: Optional[str] = None, refetch: bool = False
) -> Dict[str, Any]:
    logger = setup_logging(name="core.fetch_dpp_test_sol", level="INFO")

    try:
        if not attempt_id:
            return standard_response(
                success=False,
                error="Missing required parameter: attempt_id",
                status_code=400,
            )

        token = EnvManager.get("TOKEN", default=None)
        logger.info("Loaded TOKEN from environment")

        if not token:
            return standard_response(
                success=False,
                error="TOKEN missing from environment",
                status_code=400,
            )

        url = f"https://api.penpencil.co/v3/test-service/tests/mapping/{attempt_id}/preview-test"
        headers = {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (compatible; PenPencilFetcher/1.0)",
            "origin": "https://www.pw.live",
            "referer": "https://www.pw.live/",
            "authorization": token,
        }

        raw_response = cached_request(
            method="GET",
            url=url,
            headers=headers,
            log_prefix="[DPPTestSol] ",
            expire_after=timedelta(minutes=30),
            refetch=refetch,
        )

        if raw_response is None:
            return standard_response(
                success=False,
                error="Empty response from API",
                status_code=400,
            )


        if hasattr(raw_response, "json"):
            try:
                response = raw_response.json()
            except Exception:
                logger.warning("Failed to parse JSON; using text")
                response = {"raw": raw_response.text}


        elif isinstance(raw_response, dict):
            response = raw_response

        else:
            return standard_response(
                success=False,
                error="Invalid response format returned by cached_request",
                status_code=400,
            )

        if not isinstance(response, dict):
            return standard_response(
                success=False,
                error="Malformed API response",
                status_code=400,
            )

        if not response.get("success", True):
            invalidate_cache(raw_response)
            return standard_response(
                success=False,
                error="API returned an error",
                status_code=400,
            )

        data_root = response.get("data", {})
        difficulty_levels_map = {
            lvl.get("level"): lvl.get("title")
            for lvl in data_root.get("difficultyLevels", [])
        }

        results: List[Dict[str, Any]] = []

        for q in data_root.get("questions", []):
            qinfo = q.get("question", {})

            img_en = qinfo.get("imageIds", {}).get("en", {})
            question_id = img_en.get("_id")
            question_name = img_en.get("name")
            endlink = (img_en.get("baseUrl", "") or "") + (img_en.get("key", "") or "")

            difficulty_level = difficulty_levels_map.get(
                qinfo.get("difficultyLevel"), "Unknown"
            )

            option_map = {
                opt["_id"]: opt.get("texts", {}).get("en")
                for opt in qinfo.get("options", [])
            }

            sols = [
                option_map.get(sid)
                for sid in qinfo.get("solutions", [])
                if sid in option_map
            ]

            sol_desc_list = []
            for sol in qinfo.get("solutionDescription", []):
                img = sol.get("imageIds", {}).get("en", {})
                sol_desc_list.append(
                    {
                        "sol_id": img.get("_id"),
                        "sol_name": img.get("name"),
                        "endlink": (img.get("baseUrl", "") or "")
                        + (img.get("key", "") or ""),
                    }
                )

            record = {
                "question_id": question_id,
                "question_name": question_name,
                "endlink": endlink,
                "order": qinfo.get("questionNumber"),
                "positive_marks": qinfo.get("positiveMarks"),
                "negative_marks": qinfo.get("negativeMarks"),
                "difficulty": difficulty_level,
                "solutions": sols,
                "solution_descriptions": sol_desc_list,
            }

            parsed = DPPTestSolutionItem.from_json(record)
            if parsed is not None:
                results.append(record)

        return standard_response(
            success=True,
            data={"questions": results},
            status_code=200,
        )

    except Exception as exc:
        return handle_exception(
            logger,
            exc,
            context="fetch_dpp_test_sol",
        )
