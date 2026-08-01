import os
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.content import (
    fetch_notes, fetch_dpp, fetch_lectures, fetch_announcements, fetch_topic_quiz,
)
from core.quiz import build_quiz_html
from core.utils import get_session


def _safe_filename(name):
    name = (name or "").strip().replace("/", "-").replace("\\", "-")
    name = "".join(c for c in name if c.isalnum() or c in " ._-()[]")
    name = name.strip(" .")
    return name[:120] or "untitled"


def _att_url(att):
    base_url = att.get("baseUrl") or ""
    key = att.get("key") or ""
    if not key:
        return None
    return base_url.rstrip("/") + "/" + key.lstrip("/")


def build_download_jobs(token, batch, subject_ids, types, out_dir):
    """Build a list of download jobs from a content-tree batch + selection.

    `batch` is a tree entry: {"batch": {...}, "subjects": {...}}.

    Returns jobs: list of dicts with kinds 'file', 'quiz', 'lectures'.
    """
    types = {t.lower() for t in types}
    jobs = []
    batch_info = batch["batch"]
    subjects = batch["subjects"]
    batch_name = _safe_filename(batch_info.get("name"))
    base = os.path.join(out_dir, batch_name)

    for sid in subject_ids:
        subj_entry = subjects.get(sid)
        if not subj_entry:
            continue
        subject = subj_entry["subject"]
        subj_base = os.path.join(base, _safe_filename(subject.get("subject")))
        for topic in subj_entry["topics"].values():
            topic_base = os.path.join(subj_base, _safe_filename(topic.get("name")))
            slug = batch_info.get("slug")
            subj_slug = subject.get("slug")
            topic_slug = topic.get("slug")

            if "notes" in types:
                for entry in fetch_notes(token, slug, subj_slug, topic_slug):
                    for att in entry.get("attachments", []):
                        url = _att_url(att)
                        if not url:
                            continue
                        fname = _safe_filename(att.get("name") or f"{entry.get('topic', 'note')}.pdf")
                        jobs.append({
                            "kind": "file",
                            "label": f"Notes/{topic.get('name')}/{fname}",
                            "url": url,
                            "dest": os.path.join(topic_base, "Notes", fname),
                        })

            if "dpp" in types:
                for entry in fetch_dpp(token, slug, subj_slug, topic_slug):
                    for att in entry.get("attachments", []):
                        url = _att_url(att)
                        if not url:
                            continue
                        fname = _safe_filename(att.get("name") or f"{entry.get('topic', 'dpp')}.pdf")
                        jobs.append({
                            "kind": "file",
                            "label": f"DPP/{topic.get('name')}/{fname}",
                            "url": url,
                            "dest": os.path.join(topic_base, "DPP", fname),
                        })

            if "quiz" in types:
                questions = fetch_topic_quiz(
                    token, batch_info.get("_id"), subject.get("_id"), topic.get("_id")
                )
                if questions:
                    jobs.append({
                        "kind": "quiz",
                        "label": f"Quiz/{topic.get('name')}",
                        "questions": questions,
                        "out_html": os.path.join(topic_base, "Quiz", "quiz.html"),
                        "image_dir": os.path.join(topic_base, "Quiz", "images"),
                    })

            if "lectures" in types:
                lectures = fetch_lectures(token, slug, subj_slug, topic_slug)
                if lectures:
                    jobs.append({
                        "kind": "lectures",
                        "label": f"Lectures/{topic.get('name')}",
                        "lectures": lectures,
                        "path": os.path.join(topic_base, "lectures.txt"),
                    })

    if "announcements" in types and batch_info.get("_id"):
        ann_base = os.path.join(base, "Announcements")
        for ann in fetch_announcements(token, batch_info.get("_id")):
            att = ann.get("attachment")
            if not att:
                continue
            url = _att_url(att)
            if not url:
                continue
            fname = _safe_filename(att.get("name") or f"announcement_{ann.get('_id')}.pdf")
            jobs.append({
                "kind": "file",
                "label": f"Announcements/{fname}",
                "url": url,
                "dest": os.path.join(ann_base, fname),
            })

    return jobs


def _handle_job(job):
    if job["kind"] == "file":
        ok = _download_file(job["url"], job["dest"])
        return ok, job["dest"] if ok else "download failed"
    if job["kind"] == "quiz":
        try:
            path, failed = build_quiz_html(
                job["questions"], job["out_html"], job["image_dir"]
            )
            return True, f"{path} ({failed} images failed)"
        except Exception as e:
            return False, f"quiz build error: {e}"
    if job["kind"] == "lectures":
        try:
            os.makedirs(os.path.dirname(job["path"]), exist_ok=True)
            with open(job["path"], "w", encoding="utf-8") as f:
                f.write(f"Topic: {os.path.basename(os.path.dirname(job['path']))}\n")
                f.write("Note: lectures are DRM-protected; use the PW app for offline viewing.\n\n")
                for L in job["lectures"]:
                    f.write(f"- {L.get('topic')} [{L.get('duration')}] {L.get('videoUrl')}\n")
            return True, job["path"]
        except Exception as e:
            return False, f"lecture manifest error: {e}"
    return False, "unknown job kind"


def _download_file(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    session = get_session()
    try:
        with session.get(url, stream=True, timeout=90) as r:
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    if chunk:
                        f.write(chunk)
        os.replace(tmp, dest)
        return True
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        return False


def run_downloads(jobs, workers=8, progress=None):
    """Execute jobs in parallel. progress(done, total) is called after each."""
    results = []
    total = len(jobs)
    done = 0
    if not jobs:
        if progress:
            progress(0, 0)
        return results
    with ThreadPoolExecutor(max_workers=workers) as ex:
        future_to_job = {ex.submit(_handle_job, job): job for job in jobs}
        for fut in as_completed(future_to_job):
            job = future_to_job[fut]
            try:
                ok, detail = fut.result()
            except Exception as e:
                ok, detail = False, str(e)
            done += 1
            results.append((job.get("label", ""), ok, detail))
            if progress:
                progress(done, total)
    return results


def zip_dir(root_dir, zip_path):
    """Zip a folder tree. Returns zip_path."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, _, filenames in os.walk(root_dir):
            for name in filenames:
                full = os.path.join(dirpath, name)
                zf.write(full, os.path.relpath(full, root_dir))
    return zip_path
