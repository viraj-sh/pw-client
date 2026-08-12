import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.utils import get_session


def _img_url(base_url, key):
    if not base_url or not key:
        return None
    return base_url.rstrip("/") + "/" + key.lstrip("/")


def _download(session, url, dest):
    try:
        with session.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception:
        return False


def _html_escape(text):
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _img_tag(relative):
    return f'<img src="{relative}" style="max-width:100%;max-height:400px;">'


def build_quiz_html(questions, out_html, image_dir, workers=8):
    """Download quiz images and render a self-contained HTML file.

    Returns (out_html, failed_downloads_count).
    """
    os.makedirs(image_dir, exist_ok=True)
    session = get_session()

    jobs = []  # (url, dest, ref)
    for q in questions:
        qid = q["_id"]
        for i, img in enumerate(q.get("images", [])):
            url = _img_url(img.get("baseUrl"), img.get("key"))
            if url:
                jobs.append((url, os.path.join(image_dir, f"q_{qid}_img{i}.png"), qid, f"q{i}"))
        for i, sd in enumerate(q.get("solutionDescriptions", [])):
            url = _img_url(sd.get("baseUrl"), sd.get("key"))
            if url:
                jobs.append((url, os.path.join(image_dir, f"q_{qid}_sol{i}.png"), qid, f"sol{i}"))

    failed = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_download, session, url, dest) for url, dest, _, _ in jobs]
        for fut, (url, dest, qid, kind) in zip(as_completed(futures), jobs):
            if not fut.result():
                failed += 1
                if os.path.exists(dest):
                    os.remove(dest)

    def img_rel(question_id, kind, i):
        rel = os.path.join(os.path.basename(image_dir), f"q_{question_id}_{kind}{i}.png")
        return rel if os.path.exists(os.path.join(image_dir, f"q_{question_id}_{kind}{i}.png")) else None

    parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        "<title>DPP Quiz</title></head><body style='font-family:sans-serif;max-width:900px;margin:auto;'>",
        "<h1>DPP Quiz</h1>",
    ]
    for q in questions:
        parts.append("<hr><h3>Q" + str(q.get("questionNumber", "?")) + "</h3>")
        if q.get("topicName"):
            parts.append(f"<p><i>{_html_escape(q['topicName'])}</i></p>")
        for i in range(len(q.get("images", []))):
            rel = img_rel(q["_id"], "img", i)
            if rel:
                parts.append(_img_tag(rel))
        options = q.get("options", [])
        correct = set(q.get("solution_option_ids") or [])
        for j, opt in enumerate(options):
            label = chr(ord("A") + j)
            mark = "&#10004;" if opt["_id"] in correct else ""
            color = "#0a7d32" if opt["_id"] in correct else "#222"
            parts.append(
                f"<p style='color:{color}'>[{label}] {_html_escape(opt.get('en'))} {mark}</p>"
            )
        sols = q.get("solutionDescriptions", [])
        if sols:
            parts.append("<h4>Solution</h4>")
            for i in range(len(sols)):
                rel = img_rel(q["_id"], "sol", i)
                if rel:
                    parts.append(_img_tag(rel))
        elif correct:
            parts.append("<p><i>No solution image.</i></p>")

    parts.append("</body></html>")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    return out_html, failed
