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
