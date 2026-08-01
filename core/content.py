from concurrent.futures import ThreadPoolExecutor, as_completed

from core.utils import safe_get, get_auth_headers, get_session, BASE_URL


def fetch_batches(token, page=1):
    """Fetch user-purchased batches. Returns list of dicts."""
    url = f"{BASE_URL}/batch-service/v1/batches/purchased-batches?amount=paid&page={page}&type=ALL"
    data = safe_get(url, token=token)
    if data.get("success") and isinstance(data.get("data"), list):
        return [
            {
                "name": b.get("name"),
                "_id": b.get("_id"),
                "slug": b.get("slug"),
                "startDate": b.get("startDate"),
                "endDate": b.get("endDate"),
                "expiryDate": b.get("expiryDate", ""),
            }
            for b in data["data"]
        ]
    return []


def fetch_subjects(token, batch_slug):
    """Fetch subjects for a batch. Returns list of dicts."""
    url = f"{BASE_URL}/v3/batches/{batch_slug}/details"
    data = safe_get(url, token=token)
    subjects = data.get("data", {}).get("subjects", [])
    return [
        {
            "_id": s.get("_id"),
            "subject": s.get("subject"),
            "slug": s.get("slug"),
            "tagCount": s.get("tagCount"),
            "displayOrder": s.get("displayOrder"),
            "lectureCount": s.get("lectureCount"),
        }
        for s in subjects
    ]


def fetch_topics(token, batch_slug, subject_slug, page=1):
    """Fetch topics for a subject in a batch. Returns list of dicts."""
    url = f"{BASE_URL}/v2/batches/{batch_slug}/subject/{subject_slug}/topics?page={page}"
    data = safe_get(url, token=token)
    return [
        {
            "_id": t.get("_id"),
            "name": t.get("name"),
            "displayOrder": t.get("displayOrder"),
            "notes": t.get("notes"),
            "exercises": t.get("exercises"),
            "videos": t.get("videos"),
            "lectureVideos": t.get("lectureVideos"),
            "slug": t.get("slug"),
        }
        for t in data.get("data", [])
    ]


def _fetch_contents(token, batch_slug, subject_slug, topic_slug, content_type, page=1):
    url = (
        f"{BASE_URL}/v2/batches/{batch_slug}/subject/{subject_slug}"
        f"/contents?page={page}&contentType={content_type}&tag={topic_slug}"
    )
    data = safe_get(url, token=token)
    return data.get("data", [])


def _attachments_from(entries):
    out = []
    for entry in entries:
        for hw in entry.get("homeworkIds", []):
            out.append(
                {
                    "topic": hw.get("topic"),
                    "attachments": [
                        {
                            "_id": a.get("_id"),
                            "baseUrl": a.get("baseUrl"),
                            "key": a.get("key"),
                            "name": a.get("name"),
                        }
                        for a in hw.get("attachmentIds", [])
                    ],
                }
            )
    return out


def fetch_notes(token, batch_slug, subject_slug, topic_slug, page=1):
    """Fetch note attachments for a topic."""
    return _attachments_from(
        _fetch_contents(token, batch_slug, subject_slug, topic_slug, "notes", page)
    )


def fetch_dpp(token, batch_slug, subject_slug, topic_slug, page=1):
    """Fetch DPP attachments for a topic."""
    return _attachments_from(
        _fetch_contents(token, batch_slug, subject_slug, topic_slug, "DppNotes", page)
    )


def fetch_lectures(token, batch_slug, subject_slug, topic_slug, page=1):
    """Fetch video lecture info for a topic (streams are DRM-protected)."""
    entries = _fetch_contents(token, batch_slug, subject_slug, topic_slug, "VIDEO", page)
    lectures = []
    for entry in entries:
        if not entry.get("isVideoLecture"):
            continue
        vd = entry.get("videoDetails") or {}
        video_url = vd.get("videoUrl") or entry.get("url")
        if not video_url:
            continue
        lectures.append(
            {
                "_id": entry.get("_id"),
                "topic": vd.get("name") or entry.get("topic"),
                "videoUrl": video_url,
                "duration": vd.get("duration"),
                "drmProtected": vd.get("drmProtected", False),
                "lectureType": entry.get("lectureType"),
            }
        )
    return lectures


def fetch_announcements(token, batch_id, page=1):
    """Fetch announcements for a batch. Returns list of dicts."""
    url = f"{BASE_URL}/v1/batches/{batch_id}/announcement?page={page}"
    data = safe_get(url, token=token)
    result = []
    for ann in data.get("data", []):
        info = {
            "announcement": ann.get("announcement"),
            "_id": ann.get("_id"),
            "scheduleTime": ann.get("scheduleTime"),
            "attachment": None,
        }
        att = ann.get("attachment")
        if att:
            info["attachment"] = {
                "name": att.get("name"),
                "baseUrl": att.get("baseUrl"),
                "key": att.get("key"),
            }
        result.append(info)
    return result


# ---------------- DPP-Quiz ----------------

def get_dpp_quiz_attempt_id(token, batch_id, subject_id, topic_id, page=1, limit=50):
    """Return the attempt ID for a topic's DPP quiz, or None."""
    url = (
        f"{BASE_URL}/v3/test-service/tests/dpp?"
        f"page={page}&limit={limit}&batchId={batch_id}&batchSubjectId={subject_id}"
        f"&isSubjective=false&chapterId={topic_id}"
    )
    data = safe_get(url, token=token)
    for entry in data.get("data", []):
        attempt_id = (entry.get("testStudentMapping") or {}).get("_id")
        if attempt_id:
            return attempt_id
    return None


def fetch_dpp_quiz_questions(token, attempt_id):
    """Fetch questions + solutions for an attempted quiz."""
    url = f"{BASE_URL}/v3/test-service/tests/mapping/{attempt_id}/preview-test"
    data = safe_get(url, token=token)
    out = []
    for qwrap in data.get("data", {}).get("questions", []):
        q = qwrap.get("question", {})
        options = [
            {"_id": opt.get("_id"), "en": (opt.get("texts") or {}).get("en")}
            for opt in q.get("options", [])
        ]
        images = []
        image_en = (q.get("imageIds") or {}).get("en")
        if image_en:
            images.append(
                {
                    "_id": image_en.get("_id"),
                    "name": image_en.get("name"),
                    "baseUrl": image_en.get("baseUrl"),
                    "key": image_en.get("key"),
                }
            )
        solution_desc = []
        for sd in q.get("solutionDescription", []):
            sd_img = (sd.get("imageIds") or {}).get("en")
            if sd_img:
                solution_desc.append(
                    {
                        "_id": sd_img.get("_id"),
                        "name": sd_img.get("name"),
                        "baseUrl": sd_img.get("baseUrl"),
                        "key": sd_img.get("key"),
                    }
                )
        out.append(
            {
                "_id": q.get("_id"),
                "questionNumber": q.get("questionNumber"),
                "images": images,
                "options": options,
                "solution_option_ids": q.get("solutions", []),
                "difficultyLevel": q.get("difficultyLevel"),
                "topicName": (q.get("topicId") or {}).get("name"),
                "solutionDescriptions": solution_desc,
            }
        )
    return out


def fetch_topic_quiz(token, batch_id, subject_id, topic_id):
    """Return quiz questions for a topic, or None if unattempted."""
    attempt_id = get_dpp_quiz_attempt_id(token, batch_id, subject_id, topic_id)
    if not attempt_id:
        return None
    return fetch_dpp_quiz_questions(token, attempt_id)


# ---------------- Content tree ----------------

def _load_subject(token, batch_slug, subject):
    topics = fetch_topics(token, batch_slug, subject["slug"])
    return {
        "subject": subject,
        "topics": {t["_id"] or t["slug"]: t for t in topics},
    }


def _load_batch(token, batch, workers=8):
    subjects = fetch_subjects(token, batch["slug"])
    if not subjects:
        return {"batch": batch, "subjects": {}}
    loaded = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {
            ex.submit(_load_subject, token, batch["slug"], s): s for s in subjects
        }
        for fut in as_completed(futures):
            s = futures[fut]
            try:
                res = fut.result()
            except Exception:
                continue
            if res:
                loaded[s["_id"] or s["slug"]] = res
    return {"batch": batch, "subjects": loaded}


def build_content_tree(token, workers=8):
    """Fetch batches -> subjects -> topics in parallel.

    Returns {batch_id: {"batch": {...}, "subjects": {subject_id: {...}}}}
    """
    batches = fetch_batches(token)
    tree = {}
    if not batches:
        return tree
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_load_batch, token, b, workers): b for b in batches}
        for fut in as_completed(futures):
            b = futures[fut]
            try:
                res = fut.result()
            except Exception:
                continue
            if res:
                tree[b["_id"] or b["slug"]] = res
    return tree
