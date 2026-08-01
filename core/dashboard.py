from core.utils import safe_get, BASE_URL


def fetch_batch_lecture_stats(token, batch_id):
    """Lecture statistics for a complete batch."""
    url = f"{BASE_URL}/v3/performance/lecture?batchId={batch_id}"
    d = safe_get(url, token=token).get("data", {})
    return {
        "completedChapter": d.get("completedChapter"),
        "completedLectures": d.get("completedLectures"),
        "totalWatchTime": d.get("totalWatchTime"),
        "totalChapters": d.get("totalChapters"),
        "totalLectures": d.get("totalLectures"),
    }


def fetch_subject_lecture_stats(token, batch_id):
    """Lecture statistics per subject."""
    url = f"{BASE_URL}/v3/performance/lecture/subjects?batchId={batch_id}"
    data = safe_get(url, token=token)
    stats = []
    for item in data.get("data", []):
        subject = item.get("subjectId", {})
        stats.append(
            {
                "subjectName": subject.get("name"),
                "completedChapter": item.get("completedChapter"),
                "completedLectures": item.get("completedLectures"),
                "totalWatchTime": item.get("totalWatchTime"),
                "totalLectures": item.get("totalLectures"),
                "totalChapters": item.get("totalChapters"),
            }
        )
    return stats


def fetch_batch_quiz_stats(token, batch_id):
    """Combined DPP-Quiz stats for a batch."""
    url = f"{BASE_URL}/v3/performance/quiz?batchId={batch_id}"
    data = safe_get(url, token=token)
    result = []
    for item in data.get("data", []):
        val = item.get("value", {})
        result.append(
            {
                "key": item.get("key"),
                "accuracy": val.get("accuracy"),
                "marksObtained": val.get("marksObtained"),
                "correctQuestions": val.get("correctQuestions"),
                "completedQuiz": val.get("completedQuiz"),
                "totalQuiz": val.get("totalQuiz"),
            }
        )
    return result


def fetch_subject_quiz_stats(token, batch_id, quiz_type="OBJECTIVE"):
    """DPP-Quiz stats per subject."""
    url = f"{BASE_URL}/v3/performance/quiz/subjects?batchId={batch_id}&type={quiz_type}"
    data = safe_get(url, token=token)
    result = []
    for item in data.get("data", []):
        subject = item.get("subjectId", {})
        result.append(
            {
                "subjectName": subject.get("name"),
                "accuracy": item.get("accuracy"),
                "marksObtained": item.get("marksObtained"),
                "totalQuestions": item.get("totalQuestions"),
                "correctQuestions": item.get("correctQuestions"),
                "attemptedQuestions": item.get("attemptedQuestions"),
                "attempted": item.get("attempted"),
                "totalQuiz": item.get("totalQuiz"),
            }
        )
    return result
