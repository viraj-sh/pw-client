import logging
import time
import uuid

import requests

BASE_URL = "https://api.penpencil.co"
ORGANIZATION_ID = "5eb393ee95fab7468a79d189"
REFERER = "https://www.pw.live/"
CONTENT_TYPE = "application/json"
ACCEPT = "application/json"
CLIENT_ID = "system-admin"
CLIENT_SECRET = "KjPXuAVfC5xbmgreETNMaL7z"
GRANT_TYPE = "password"
LATITUDE = 0
LONGITUDE = 0

DEFAULT_TIMEOUT = 20
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5
RETRY_STATUS = (429, 500, 502, 503, 504)

logger = logging.getLogger("pw")

_session = None


def get_session():
    global _session
    if _session is None:
        retries = requests.adapters.Retry(
            total=MAX_RETRIES,
            backoff_factor=BACKOFF_FACTOR,
            status_forcelist=RETRY_STATUS,
            allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE"]),
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retries)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        _session = session
    return _session


def get_default_headers(random_id=None):
    if not random_id:
        random_id = str(uuid.uuid4())
    return {
        "Content-Type": CONTENT_TYPE,
        "Accept": ACCEPT,
        "Referer": REFERER,
        "Randomid": random_id,
    }


def get_auth_headers(token, random_id=None):
    headers = get_default_headers(random_id)
    headers["Authorization"] = f"Bearer {token}"
    return headers


def verify_token(token):
    url = f"{BASE_URL}/v3/oauth/verify-token"
    data = _request("POST", url, token=token)
    if data.get("success") and data.get("data", {}).get("isVerified"):
        return {"success": True}
    error = data.get("error", {})
    return {
        "success": False,
        "error_message": error.get("message", data.get("message", "Unknown error")),
        "error_status": error.get("status", None),
    }


def get_token_expiry_info(expires_in):
    current_time_ms = int(time.time() * 1000)
    ms_remaining = expires_in - current_time_ms
    days_remaining = ms_remaining // (1000 * 60 * 60 * 24)
    return {
        "is_expired": ms_remaining <= 0,
        "days_remaining": days_remaining if ms_remaining > 0 else 0,
    }


def _request(method, url, token=None, params=None, json=None, timeout=DEFAULT_TIMEOUT):
    """Return parsed JSON dict (or {} on failure) for a penpencil API call."""
    headers = get_auth_headers(token) if token else get_default_headers()
    session = get_session()
    try:
        resp = session.request(
            method, url, headers=headers, params=params, json=json, timeout=timeout
        )
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, dict) else {"data": data}
    except Exception as e:
        logger.debug("API error %s %s: %s", method, url, e)
        return {}


def safe_get(url, token=None, params=None, timeout=DEFAULT_TIMEOUT):
    return _request("GET", url, token=token, params=params, timeout=timeout)


def safe_post(url, token=None, json=None, timeout=DEFAULT_TIMEOUT):
    return _request("POST", url, token=token, json=json, timeout=timeout)
