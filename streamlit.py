import os
import time
from collections import Counter

import requests
import streamlit as st
from dotenv import load_dotenv

from core.content import (
    build_content_tree, fetch_notes, fetch_dpp, fetch_lectures,
    fetch_announcements, fetch_topic_quiz,
)
from core.downloader import build_download_jobs, run_downloads, zip_dir, _safe_filename
from core.generate_token import send_otp, get_token
from core.utils import verify_token

load_dotenv()

DATA_DIR = "data"
OUT_DIR = "downloads"
TOKEN_FILE = os.path.join(DATA_DIR, "token.txt")
ALL_TYPES = ["Notes", "DPP", "Quiz", "Announcements", "Lectures"]
TYPE_HELP = {
    "Notes": "Class notes · PDFs",
    "DPP": "Daily practice problems · PDFs",
    "Quiz": "Attempted DPP quizzes with solutions · HTML",
    "Announcements": "Batch announcements & attachments",
    "Lectures": "Lecture listing only (DRM-protected videos)",
}

CSS = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}
.block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1100px;}
div[data-testid="stMetric"] {
    background: #f6f7f9;
    border-radius: 12px;
    padding: 12px 16px;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap: 0.5rem;}
.stTabs [data-baseweb="tab-list"] {gap: 6px;}
.stTabs [data-baseweb="tab"] {border-radius: 8px; padding: 6px 14px;}
</style>
"""


def save_token(token):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        f.write(token)


def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return f.read().strip()
    return None


def delete_token():
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)


def check_token(token):
    if not token:
        return False
    return verify_token(token).get("success", False)


def _att_url(att):
    base_url = att.get("baseUrl") or ""
    key = att.get("key") or ""
    if not key:
        return None
    return base_url.rstrip("/") + "/" + key.lstrip("/")


# ---------------- Login ----------------

def _render_login():
    st.markdown(CSS, unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("## PW Study Material")
        st.markdown("#### Login to continue")
        method = st.radio("Login method", ["Paste access token", "Phone + OTP"], horizontal=True)

        if method == "Paste access token":
            token = st.text_area("Access token", height=110, placeholder="eyJhbGciOi...")
            if st.button("Login", type="primary", use_container_width=True):
                if token.strip() and check_token(token.strip()):
                    save_token(token.strip())
                    st.session_state.clear()
                    st.rerun()
                elif token.strip():
                    st.error("Invalid token. Please check and try again.")
                else:
                    st.warning("Paste your access token first.")
        else:
            cc = st.text_input("Country code", value="+91", max_chars=5)
            phone = st.text_input("Phone number")
            if st.button("Send OTP", use_container_width=True):
                if phone and cc:
                    resp = send_otp(phone, cc)
                    if resp.get("success"):
                        st.session_state["otp_sent"] = True
                        st.toast("OTP sent to your phone.")
                    else:
                        st.session_state["otp_sent"] = False
                        st.error(resp.get("error_message", "Failed to send OTP."))
                else:
                    st.warning("Enter your phone number and country code.")
            if st.session_state.get("otp_sent"):
                otp = st.text_input("Enter OTP", max_chars=6)
                if st.button("Verify & Login", type="primary", use_container_width=True):
                    if otp:
                        tkres = get_token(phone, otp)
                        if tkres.get("success"):
                            save_token(tkres["access_token"])
                            st.session_state.clear()
                            st.rerun()
                        else:
                            st.error(tkres.get("error_message", "Invalid OTP."))
                    else:
                        st.warning("Enter the OTP.")


# ---------------- Download ----------------

def _jobs_key(bid, subject_ids, types):
    return f"jobs_{bid}_{'-'.join(sorted(subject_ids))}_{'-'.join(sorted(types))}"


def _jobs_summary(jobs):
    kinds = Counter(j.get("kind") for j in jobs)
    return kinds


def _render_downloader(token, batch):
    batch_info = batch["batch"]
    subjects_dict = batch["subjects"]
    subj_names = {
        sid: (subjects_dict[sid]["subject"].get("subject") or sid)
        for sid in subjects_dict
    }
    subject_ids = list(subj_names.keys())

    st.subheader("What do you want to download?")
    subj_key = f"subj_sel_{batch_info.get('_id')}"
    st.session_state.setdefault(subj_key, subject_ids)
    col_sel, col_clear = st.columns([6, 1])
    with col_sel:
        sel_subject_ids = st.multiselect(
            "Subjects",
            subject_ids,
            key=subj_key,
            format_func=lambda sid: subj_names[sid],
            placeholder="Choose one or more subjects",
        )
    with col_clear:
        st.write("")
        st.write("")
        b1, b2 = st.columns(2)
        if b1.button("All", use_container_width=True):
            st.session_state[subj_key] = subject_ids
            st.rerun()
        if b2.button("None", use_container_width=True):
            st.session_state[subj_key] = []
            st.rerun()

    sel_types = st.multiselect(
        "Content",
        ALL_TYPES,
        default=ALL_TYPES,
        help="Lectures are DRM-protected; only a listing is saved.",
    )
    if sel_types:
        for t in ALL_TYPES:
            if t in sel_types:
                st.caption(f"• **{t}** — {TYPE_HELP[t]}")

    col_w, col_sp = st.columns([2, 3])
    workers = col_w.slider("Parallel downloads", min_value=1, max_value=32, value=8)

    if not sel_subject_ids:
        st.info("Pick at least one subject.")
        return
    if not sel_types:
        st.info("Pick at least one content type.")
        return

    types = list(sel_types)
    key = _jobs_key(batch_info.get("_id"), sel_subject_ids, types)
    jobs = st.session_state.get(key)

    col_preview, col_dl = st.columns([1, 1])
    if col_preview.button("Scan & preview", use_container_width=True):
        with st.spinner("Scanning your subjects..."):
            jobs = build_download_jobs(token, batch, sel_subject_ids, types, OUT_DIR)
        st.session_state[key] = jobs

    if jobs is not None:
        kinds = _jobs_summary(jobs)
        total = len(jobs)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Files", kinds.get("file", 0))
        m2.metric("Quizzes", kinds.get("quiz", 0))
        m3.metric("Lecture lists", kinds.get("lectures", 0))
        m4.metric("Total items", total)
        st.caption(f"Will be saved under `downloads/{_safe_filename(batch_info.get('name'))}`")

    if col_dl.button(
        f"Download{' ' + str(len(jobs)) if jobs else ''}",
        type="primary",
        use_container_width=True,
        disabled=not jobs,
    ):
        if jobs is None:
            with st.spinner("Scanning your subjects..."):
                jobs = build_download_jobs(token, batch, sel_subject_ids, types, OUT_DIR)
            st.session_state[key] = jobs
        if not jobs:
            st.info("Nothing to download for this selection.")
            return

        prog = st.progress(0.0, text="Starting...")
        start = time.time()

        def on_progress(done, total):
            prog.progress(done / total if total else 1.0, text=f"{done}/{total}")

        results = run_downloads(jobs, workers=workers, progress=on_progress)
        elapsed = time.time() - start
        ok = sum(1 for _, s, _ in results if s)
        fail = len(results) - ok

        st.toast(f"Finished — {ok} succeeded, {fail} failed")
        col_ok, col_fail = st.columns(2)
        col_ok.metric("Succeeded", ok)
        col_fail.metric("Failed", fail)
        st.caption(f"Done in {elapsed:.1f}s")

        failed = [r for r in results if not r[1]]
        if failed:
            with st.expander(f"Show {len(failed)} failures"):
                st.dataframe(
                    [{"item": l, "detail": d} for l, _, d in failed],
                    use_container_width=True,
                    hide_index=True,
                )

        base = os.path.join(OUT_DIR, _safe_filename(batch_info.get("name")))
        if os.path.isdir(base):
            zip_path = base + ".zip"
            zip_dir(base, zip_path)
            with open(zip_path, "rb") as f:
                st.download_button(
                    "Download everything as ZIP",
                    f.read(),
                    file_name=os.path.basename(zip_path),
                    mime="application/zip",
                    use_container_width=True,
                )
            st.caption(f"Saved to `{os.path.abspath(base)}`")


# ---------------- Browse ----------------

def _render_attachments(entries, prefix):
    if not entries:
        st.info("Nothing here yet.")
        return
    for entry in entries:
        st.markdown(f"**{entry.get('topic') or 'Untitled'}**")
        for att in entry.get("attachments", []):
            url = _att_url(att)
            name = att.get("name") or "file"
            if not url:
                continue
            c1, c2, c3 = st.columns([6, 2, 2])
            c1.write(name)
            c2.markdown(f"[Open]({url})")
            try:
                resp = requests.get(url, timeout=30)
                if resp.ok:
                    c3.download_button(
                        "Download", resp.content,
                        file_name=name, key=f"{prefix}{name}{url}",
                    )
                else:
                    c3.write("Unavailable")
            except Exception:
                c3.write("Unavailable")
        st.divider()


def _render_browser(token, batch):
    batch_info = batch["batch"]
    subjects_dict = batch["subjects"]
    subject_ids = list(subjects_dict.keys())
    if not subject_ids:
        st.info("No subjects in this batch.")
        return

    c1, c2 = st.columns(2)
    subj_id = c1.selectbox(
        "Subject",
        subject_ids,
        format_func=lambda s: subjects_dict[s]["subject"].get("subject", s),
    )
    subj_entry = subjects_dict[subj_id]
    subject = subj_entry["subject"]
    topics_dict = subj_entry["topics"]
    if not topics_dict:
        st.info("No topics for this subject.")
        return
    topic_id = c2.selectbox(
        "Topic",
        list(topics_dict.keys()),
        format_func=lambda t: topics_dict[t].get("name", t),
    )
    topic = topics_dict[topic_id]
    slug, subj_slug, topic_slug = batch_info.get("slug"), subject.get("slug"), topic.get("slug")

    tab_notes, tab_dpp, tab_quiz, tab_ann, tab_lec = st.tabs(
        ["Notes", "DPP", "Quiz", "Announcements", "Lectures"]
    )

    with tab_notes:
        _render_attachments(fetch_notes(token, slug, subj_slug, topic_slug), "n")

    with tab_dpp:
        _render_attachments(fetch_dpp(token, slug, subj_slug, topic_slug), "d")

    with tab_quiz:
        questions = fetch_topic_quiz(token, batch_info.get("_id"), subject.get("_id"), topic.get("_id"))
        if not questions:
            st.info("No attempted quiz for this topic (only attempted quizzes can be opened).")
        else:
            st.caption(f"**{len(questions)} questions** with solutions")
            for q in questions:
                st.markdown(f"**Q{q.get('questionNumber')}** · {q.get('topicName') or ''}")
                for img in q.get("images", []):
                    url = _att_url(img)
                    if url:
                        st.image(url)
                for j, opt in enumerate(q.get("options", [])):
                    mark = " ✓" if opt["_id"] in (q.get("solution_option_ids") or []) else ""
                    st.markdown(f"`{chr(65 + j)}` {opt.get('en') or ''}{mark}")
                for sd in q.get("solutionDescriptions", []):
                    url = _att_url(sd)
                    if url:
                        st.image(url)

    with tab_ann:
        announcements = fetch_announcements(token, batch_info.get("_id"))
        if not announcements:
            st.info("No announcements.")
        else:
            for ann in announcements:
                st.markdown(f"**{ann.get('scheduleTime', '')}**")
                st.write(ann.get("announcement", ""))
                att = ann.get("attachment")
                if att:
                    url = _att_url(att)
                    if url:
                        st.markdown(f"[Attachment]({url})")

    with tab_lec:
        lectures = fetch_lectures(token, slug, subj_slug, topic_slug)
        if not lectures:
            st.info("No lectures for this topic.")
        else:
            for L in lectures:
                st.markdown(f"**{L.get('topic')}** · {L.get('duration')}")
            st.caption("Lectures are DRM-protected; use the PW app for offline viewing.")


# ---------------- App ----------------

def main():
    st.set_page_config("PW Study Material", layout="wide")
    if "otp_sent" not in st.session_state:
        st.session_state["otp_sent"] = False

    token = load_token()
    if not token or not check_token(token):
        _render_login()
        return

    if "tree" not in st.session_state:
        with st.spinner("Loading your batches, subjects and chapters..."):
            st.session_state["tree"] = build_content_tree(token)

    tree = st.session_state["tree"]
    if not tree:
        st.warning("No batches found for your account.")
        if st.button("Logout"):
            delete_token()
            st.session_state.clear()
            st.rerun()
        return

    batch_ids = list(tree.keys())
    with st.sidebar:
        st.markdown("#### PW Study Material")
        batch_id = st.selectbox(
            "Batch",
            batch_ids,
            format_func=lambda b: tree[b]["batch"].get("name", b),
        )
        st.caption(f"{len(tree[batch_id]['subjects'])} subjects in this batch")
        if st.button("Logout", use_container_width=True):
            delete_token()
            st.session_state.clear()
            st.rerun()

    batch = tree[batch_id]
    st.markdown(CSS, unsafe_allow_html=True)

    tab_dl, tab_br = st.tabs(["⬇  Download", "◈  Browse"])
    with tab_dl:
        _render_downloader(token, batch)
    with tab_br:
        _render_browser(token, batch)


if __name__ == "__main__":
    main()
