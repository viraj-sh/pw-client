BASE_HEADERS: dict = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "origin": "https://www.pw.live",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://www.pw.live/",
    "sec-ch-ua": "Not/A)Brand';v='99', 'Chromium';v='148'",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Linux",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "user-agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/148.0.0.0 Safari/537.36"
    ),
}

API_HEADERS: dict = {
    **BASE_HEADERS,
    "client-id": "5eb393ee95fab7468a79d189",
    "client-type": "WEB",
    "content-type": "application/json",
    "randomid": "606c4ee7-f122-4445-b517-ce26330db6b0",
    "sec-fetch-site": "cross-site",
    "x-sdk-version": "0.0.25",
}

STATIC_HEADERS: dict = {
    **BASE_HEADERS,
    "sec-fetch-site": "same-site",
}


def auth_headers(token: str) -> dict:
    return {**API_HEADERS, "authorization": f"Bearer {token}"}


BASE_PAYLOAD: dict = {
    "organizationId": "5eb393ee95fab7468a79d189",
}

TOKEN_PAYLOAD_BASE: dict = {
    **BASE_PAYLOAD,
    "client_id": "system-admin",
    "client_secret": "KjPXuAVfC5xbmgreETNMaL7z",
    "grant_type": "password",
    "latitude": 0,
    "longitude": 0,
}
