"""Download PW lecture videos.

PW lecture videos are DASH (MPD) streams. Most are protected with Widevine
DRM. For protected videos this module:

  1. Resolves the signed DASH manifest for a lecture
     (``/v1/videos/video-url-details``).
  2. Reads the encryption KID from the manifest and exchanges it for a
     decryption key using PW's OTP endpoint.
  3. Downloads the (encrypted) audio/video segments from the manifest.
  4. Concatenates segments and decrypts them with ``mp4decrypt``.
  5. Merges audio + video with ``ffmpeg``.

DRM-free lectures are downloaded directly (plain MP4) or via ``ffmpeg``.

External dependencies (binaries looked up on ``PATH``):
  - ``ffmpeg``      - required for merging (and direct HLS/DASH grabs)
  - ``mp4decrypt``  - Bento4 tool, required for DRM-protected lectures
"""

import base64
import math
import os
import re
import shutil
import subprocess
import threading
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

from core.utils import BASE_URL, get_auth_headers, get_session

# ---------------------------------------------------------------------------
# Manifest / stream resolution
# ---------------------------------------------------------------------------


def get_stream_headers(token):
    """Headers required by the video / OTP endpoints."""
    headers = get_auth_headers(token)
    headers.update(
        {
            "client-id": "5eb393ee95fab7468a79d189",
            "client-type": "WEB",
            "client-version": "200",
            "origin": "https://www.pw.live",
        }
    )
    return headers


def fetch_stream_details(token, parent_id, child_id, video_type="BATCHES"):
    """Resolve the DASH manifest details for a lecture.

    Returns the ``data`` dict from ``video-url-details`` or ``None``.
    The dict usually contains ``url`` (the MPD location) and ``signedUrl``
    (a CloudFront signature query string).
    """
    url = (
        f"{BASE_URL}/v1/videos/video-url-details?"
        f"type={video_type}&childId={child_id}&parentId={parent_id}"
        f"&reqType=query&videoContainerType=DASH"
    )
    try:
        resp = get_session().get(url, headers=get_stream_headers(token), timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None
    if not (data or {}).get("success"):
        return None
    return data.get("data") or {}


def build_mpd_url(details):
    """Combine the MPD url and its CloudFront signature."""
    url = (details or {}).get("url") or ""
    if not url:
        return None
    if "?" in url:
        return url
    signed = (details or {}).get("signedUrl") or ""
    if signed:
        if not signed.startswith("?"):
            signed = "?" + signed
        return url + signed
    return url


def fetch_mpd(mpd_url, token):
    """Download the raw MPD XML text."""
    try:
        resp = get_session().get(mpd_url, headers=get_stream_headers(token), timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def extract_kid(mpd_text):
    """Extract the Widevine default_KID from MPD text."""
    if not mpd_text:
        return None
    match = re.search(r'default_KID\s*=\s*"?([0-9a-fA-F-]{32,36})', mpd_text)
    if not match:
        match = re.search(r'\buuid\s*=\s*"?([0-9a-fA-F-]{32,36})', mpd_text)
    if not match:
        return None
    return match.group(1).replace("-", "").lower()


# ---------------------------------------------------------------------------
# License key (OTP) exchange
# ---------------------------------------------------------------------------


def _otp_encrypt(token, kid_hex):
    """Encode a KID into the form the get-otp endpoint expects."""
    xor_bytes = [ord(c) ^ ord(token[i % len(token)]) for i, c in enumerate(kid_hex)]
    otp_key = base64.b64encode(bytes(xor_bytes)).decode("utf-8")
    hex_step = otp_key.encode("utf-8").hex()
    return "".join(
        "00" + hex_step[i : i + 2] + ("" if i + 2 >= len(hex_step) else "00")
        for i in range(0, len(hex_step), 2)
    )


def _otp_decrypt(token, otp_b64):
    """Turn the OTP response back into a decryption key."""
    raw = base64.b64decode(otp_b64)
    return "".join(chr(b ^ ord(token[i % len(token)])) for i, b in enumerate(raw))


def get_license_key(token, kid_hex):
    """Fetch the Widevine content key via PW's OTP endpoint."""
    if not kid_hex:
        return None
    key_hex = _otp_encrypt(token, kid_hex)
    url = f"{BASE_URL}/v1/videos/get-otp?key={key_hex}&isEncoded=true"
    try:
        resp = get_session().get(url, headers=get_stream_headers(token), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        payload = data.get("data") or {}
        otp = payload.get("otp") or data.get("otp")
        if not otp:
            return None
        return _otp_decrypt(token, otp)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# MPD parsing (namespace-agnostic)
# ---------------------------------------------------------------------------


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _children(elem, name):
    return [c for c in list(elem) if _local(c.tag) == name]


def _find(elem, name):
    for c in list(elem):
        if _local(c.tag) == name:
            return c
    return None


def _iso8601_seconds(value):
    """Parse a simple ISO8601 duration (PT..H..M..S) to seconds."""
    if not value:
        return None
    match = re.match(r"P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:([\d.]+)S)?", value)
    if not match:
        return None
    d = int(match.group(1) or 0)
    h = int(match.group(2) or 0)
    m = int(match.group(3) or 0)
    s = float(match.group(4) or 0)
    return d * 86400 + h * 3600 + m * 60 + s


def parse_mpd(mpd_text, base_url, signature):
    """Parse an MPD and return a download plan.

    Returns dict::

        {
          "drm": bool,
          "kid": "32hex" or None,
          "duration": seconds or None,
          "video": {"init": url|None, "segments": [url, ...]}|None,
          "audio": {"init": url|None, "segments": [url, ...]}|None,
        }
    """
    plan = {
        "drm": "ContentProtection" in (mpd_text or ""),
        "kid": extract_kid(mpd_text),
        "duration": None,
        "video": None,
        "audio": None,
    }
    try:
        root = ET.fromstring(mpd_text or "")
    except ET.ParseError:
        return plan

    plan["duration"] = _iso8601_seconds(root.get("mediaPresentationDuration"))

    period = None
    for elem in root.iter():
        if _local(elem.tag) == "Period":
            period = elem
            break
    if period is None:
        return plan

    for aset in _children(period, "AdaptationSet"):
        kind = _adaptation_kind(aset)
        if kind and not plan[kind]:
            plan[kind] = _adaptation_plan(aset, base_url, signature, plan["duration"])

    return plan


def _adaptation_kind(aset):
    ct = (aset.get("contentType") or "").lower()
    mime = (aset.get("mimeType") or "").lower()
    if ct.startswith("audio") or mime.startswith("audio"):
        return "audio"
    if ct.startswith("video") or mime.startswith("video"):
        return "video"
    for rep in _children(aset, "Representation"):
        m = (rep.get("mimeType") or "").lower()
        if m.startswith("audio"):
            return "audio"
        if m.startswith("video"):
            return "video"
    return None


def _adaptation_plan(aset, base_url, signature, total_duration=None):
    reps = _children(aset, "Representation")
    rep = _pick_representation(aset, reps) if reps else None

    template = _find(rep, "SegmentTemplate") if rep is not None else None
    if template is None:
        template = _find(aset, "SegmentTemplate")
    if template is not None:
        return _template_plan(template, base_url, signature, total_duration)

    seg_list = _find(rep, "SegmentList") if rep is not None else None
    if seg_list is None:
        seg_list = _find(aset, "SegmentList")
    if seg_list is not None:
        return _segment_list_plan(seg_list, base_url, signature)

    seg_base = _find(rep, "SegmentBase") if rep is not None else None
    if seg_base is None:
        seg_base = _find(aset, "SegmentBase")
    if seg_base is not None:
        base = _find(seg_base, "BaseURL")
        if base is None:
            base = _find(rep, "BaseURL") if rep is not None else _find(aset, "BaseURL")
        if base is not None:
            return {"init": None, "segments": [_resolve(base.text, base_url, signature)]}

    base = _find(rep, "BaseURL") if rep is not None else None
    if base is None:
        base = _find(aset, "BaseURL")
    if base is not None:
        return {"init": None, "segments": [_resolve(base.text, base_url, signature)]}
    return None


def _pick_representation(aset, reps):
    for rep in reps:
        if rep.get("height") == "720":
            return rep
    return reps[0]


def _template_plan(template, base_url, signature, total_duration=None):
    media = template.get("media")
    if not media:
        return None
    start = int(template.get("startNumber") or 1)
    count = _template_segment_count(template, total_duration)
    if not count or count <= 0:
        return None

    def _media_url(number):
        url = re.sub(
            r"\$Number%0(\d+)d\$",
            lambda m: str(number).zfill(int(m.group(1))),
            media,
        )
        url = url.replace("$Number$", str(number))
        return _resolve(url, base_url, signature)

    return {
        "init": _resolve(template.get("initialization"), base_url, signature)
        if template.get("initialization")
        else None,
        "segments": [_media_url(start + i) for i in range(count)],
    }


def _template_segment_count(template, total_duration=None):
    timeline = _find(template, "SegmentTimeline")
    if timeline is not None:
        total = 0
        for s in _children(timeline, "S"):
            total += 1
            r = s.get("r")
            if r:
                total += int(r)
        return total
    duration = template.get("duration")
    timescale = int(template.get("timescale") or 1)
    if duration and total_duration:
        seg_seconds = int(duration) / timescale
        return max(1, int(math.ceil(total_duration / seg_seconds)))
    return None


def _segment_list_plan(seg_list, base_url, signature):
    init = None
    init_elem = _find(seg_list, "Initialization")
    if init_elem is not None and init_elem.get("sourceURL"):
        init = _resolve(init_elem.get("sourceURL"), base_url, signature)
    segments = []
    for s in _children(seg_list, "SegmentURL"):
        media = s.get("media")
        if media:
            segments.append(_resolve(media, base_url, signature))
    return {"init": init, "segments": segments}


def _resolve(url, base_url, signature):
    if not url:
        return None
    if not url.startswith("http"):
        url = urljoin(base_url, url)
    if signature and "?" not in url:
        url = url + ("?" + signature if not signature.startswith("?") else signature)
    return url


# ---------------------------------------------------------------------------
# Segment download
# ---------------------------------------------------------------------------


def _download_url(url, dest, headers=None, retries=3):
    session = get_session()
    for attempt in range(retries):
        try:
            with session.get(url, headers=headers, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        if chunk:
                            f.write(chunk)
                return True
        except Exception:
            if attempt < retries - 1:
                continue
    return False


def _download_plan(plan, work_dir, headers=None, max_workers=16, progress=None):
    """Download init + segments for one adaptation set into work_dir.

    Returns (init_path, [segment_paths]) or (None, []) on failure.
    """
    if not plan or not plan.get("segments"):
        return None, []
    os.makedirs(work_dir, exist_ok=True)
    init_path = None
    if plan.get("init"):
        init_path = os.path.join(work_dir, "init.mp4")
        if not _download_url(plan["init"], init_path, headers=headers):
            init_path = None

    paths = [None] * len(plan["segments"])
    done = 0
    lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {}
        for i, url in enumerate(plan["segments"]):
            if url is None:
                continue
            dest = os.path.join(work_dir, f"{i:05d}.m4s")
            futures[ex.submit(_download_url, url, dest, headers=headers)] = (i, dest)
        for fut in as_completed(futures):
            i, dest = futures[fut]
            ok = fut.result()
            if ok:
                paths[i] = dest
            with lock:
                done += 1
                if progress:
                    progress(done, len(plan["segments"]))
    return init_path, [p for p in paths if p is not None]


def _concat(init_path, segment_paths, out_path):
    """Concatenate init + segments (in order) into a single file."""
    with open(out_path, "wb") as out:
        if init_path and os.path.exists(init_path):
            with open(init_path, "rb") as f:
                shutil.copyfileobj(f, out)
        for path in segment_paths:
            with open(path, "rb") as f:
                shutil.copyfileobj(f, out)
    return out_path


# ---------------------------------------------------------------------------
# External binaries
# ---------------------------------------------------------------------------


def find_ffmpeg():
    return shutil.which("ffmpeg")


def find_mp4decrypt():
    return shutil.which("mp4decrypt")


def check_dependencies():
    """Return (ffmpeg_path, mp4decrypt_path). Missing entries are None."""
    return find_ffmpeg(), find_mp4decrypt()


def _run(cmd):
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode
    except Exception:
        return -1


def _merge(ffmpeg, video_path, audio_path, out_path):
    if audio_path and os.path.exists(audio_path):
        return _run(
            [ffmpeg, "-y", "-i", video_path, "-i", audio_path, "-c", "copy", out_path]
        )
    return _run([ffmpeg, "-y", "-i", video_path, "-c", "copy", out_path])


# ---------------------------------------------------------------------------
# High-level downloader
# ---------------------------------------------------------------------------


def download_video(
    token,
    lecture,
    batch_slug,
    dest,
    tmp_dir=None,
    ffmpeg=None,
    mp4decrypt=None,
    progress=None,
    keep_tmp=False,
):
    """Download a single lecture video to ``dest``.

    ``lecture`` is a dict as returned by ``core.content.fetch_lectures``
    (requires ``_id`` and optionally ``drmProtected`` / ``videoUrl``).

    ``progress`` is an optional callable ``progress(done, total, message)``.
    Returns ``(ok, detail)``.
    """
    if not token or not lecture:
        return False, "missing token/lecture"
    lecture_id = lecture.get("_id")
    if not lecture_id:
        return False, "lecture has no id"

    # Direct MP4 (DRM-free lectures often expose one)
    plain_url = _plain_mp4_url(lecture)
    if plain_url:
        if progress:
            progress(0, 1, "Downloading direct MP4…")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        ok = _download_url(plain_url, dest, headers=None)
        return (ok, dest if ok else "download failed")

    if progress:
        progress(0, 1, "Resolving stream…")
    details = fetch_stream_details(token, batch_slug, lecture_id)
    mpd_url = build_mpd_url(details) if details else None
    if not mpd_url:
        return False, "could not resolve stream url"

    mpd_text = fetch_mpd(mpd_url, token)
    if mpd_text is None:
        return False, "could not fetch manifest"

    tmp_root = tmp_dir or os.path.join(os.path.dirname(dest), ".video_tmp")
    work = os.path.join(tmp_root, lecture_id)
    os.makedirs(work, exist_ok=True)

    base_url, signature = _split_mpd(mpd_url)
    plan = parse_mpd(mpd_text, base_url, signature)
    if not plan["video"] and not plan["audio"]:
        shutil.rmtree(work, ignore_errors=True)
        return False, "unsupported manifest"

    is_drm = plan["drm"] or bool(lecture.get("drmProtected"))

    key = None
    if is_drm:
        if progress:
            progress(0, 1, "Fetching decryption key…")
        if not mp4decrypt:
            shutil.rmtree(work, ignore_errors=True)
            return False, "DRM lecture requires mp4decrypt (Bento4)"
        kid = plan.get("kid") or extract_kid(mpd_text)
        key = get_license_key(token, kid) if kid else None
        if not key:
            shutil.rmtree(work, ignore_errors=True)
            return False, "could not obtain decryption key"

    headers = get_stream_headers(token) if is_drm else None
    results = {}
    for kind in ("video", "audio"):
        if not plan[kind]:
            continue
        if progress:
            progress(0, len(plan[kind]["segments"]), f"Downloading {kind}…")
        results[kind] = _download_plan(
            plan[kind], os.path.join(work, kind), headers=headers, progress=progress
        )
        if not results[kind][1]:
            shutil.rmtree(work, ignore_errors=True)
            return False, f"no {kind} segments downloaded"

    os.makedirs(os.path.dirname(dest), exist_ok=True)

    try:
        if ffmpeg and len(results) == 2:
            video_enc = _concat_all(results["video"], work, "video-enc.mp4")
            audio_enc = _concat_all(results["audio"], work, "audio-enc.mp4")
            video_dec, audio_dec = video_enc, audio_enc
            if is_drm:
                video_dec = os.path.join(work, "video.mp4")
                audio_dec = os.path.join(work, "audio.mp4")
                if _run([mp4decrypt, "--key", f"1:{key}", video_enc, video_dec]) != 0:
                    raise RuntimeError("video decryption failed")
                if _run([mp4decrypt, "--key", f"1:{key}", audio_enc, audio_dec]) != 0:
                    raise RuntimeError("audio decryption failed")
            if _merge(ffmpeg, video_dec, audio_dec, dest) != 0:
                raise RuntimeError("ffmpeg merge failed")
        else:
            kind = "video" if "video" in results else "audio"
            enc = _concat_all(results[kind], work, "stream-enc.mp4")
            if is_drm:
                dec = os.path.join(work, "stream.mp4")
                if _run([mp4decrypt, "--key", f"1:{key}", enc, dec]) != 0:
                    raise RuntimeError("decryption failed")
            else:
                dec = enc
            if ffmpeg:
                if _run([ffmpeg, "-y", "-i", dec, "-c", "copy", dest]) != 0:
                    raise RuntimeError("ffmpeg remux failed")
            else:
                shutil.move(dec, dest)
    except Exception as e:
        shutil.rmtree(work, ignore_errors=True)
        return False, str(e)

    if not keep_tmp:
        shutil.rmtree(work, ignore_errors=True)
    return True, dest


def _concat_all(result, work, name):
    init_path, segment_paths = result
    return _concat(init_path, segment_paths, os.path.join(work, name))


def _split_mpd(mpd_url):
    if "?" in mpd_url:
        base, signature = mpd_url.split("?", 1)
    else:
        base, signature = mpd_url, None
    return base.rsplit("/", 1)[0] + "/", signature


def _plain_mp4_url(lecture):
    """Return a direct .mp4 url when the lecture exposes one, else None."""
    video_url = (lecture or {}).get("videoUrl")
    if video_url and video_url.lower().endswith(".mp4"):
        return video_url
    return None
