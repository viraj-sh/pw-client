from typing import Literal
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated

from app.core.http import HTTPClientDep
from app.core.utils import API_BASE_URL, STATIC_BASE_URL, ORG_ID
from app.schemas.auth import OTPInput, LoginInput

security = HTTPBearer()


async def fetch_countires(client: HTTPClientDep):
    url = f"{STATIC_BASE_URL}/auth-fe/assets/json/app-constants.json"
    headers = {
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
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    }
    response = await client.get(url=url, headers=headers)
    return response


async def otp(
    smsType: Literal["whatsapp", "sms"],
    input_data: OTPInput,
    client: HTTPClientDep,
    resend: bool = False,
):
    if smsType == "whatsapp":
        type = 1
    else:
        type = 0

    params = {"smsType": type}
    if resend:
        url = f"{API_BASE_URL}/v1/users/resend-otp"
    else:
        url = f"{API_BASE_URL}/v1/users/get-otp"
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "client-id": "5eb393ee95fab7468a79d189",
        "client-type": "WEB",
        "content-type": "application/json",
        "origin": "https://www.pw.live",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "randomid": "52d3b33f-ad69-4022-85a5-7d195e1dd2ee",
        "referer": "https://www.pw.live/",
        "sec-ch-ua": "'Not/A)Brand';v='99', 'Chromium';v='148'",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Linux",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "x-sdk-version": "0.0.25",
    }
    payload = {
        "username": input_data.phone_no,
        "countryCode": input_data.country_code,
        "organizationId": ORG_ID,
    }
    response = await client.post(url=url, params=params, headers=headers, json=payload)

    return response


async def verify(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
):
    url = f"{API_BASE_URL}/v3/oauth/verify-token"
    headers = {
        "authorization": token.credentials,
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "client-id": "5eb393ee95fab7468a79d189",
        "client-type": "WEB",
        "content-type": "application/json",
        "origin": "https://www.pw.live",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "randomid": "52d3b33f-ad69-4022-85a5-7d195e1dd2ee",
        "referer": "https://www.pw.live/",
        "sec-ch-ua": "'Not/A)Brand';v='99', 'Chromium';v='148'",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Linux",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "x-sdk-version": "0.0.25",
    }
    response = await client.post(url=url, headers=headers)

    return response


async def logout(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
):
    url = f"{API_BASE_URL}/v1/oauth/logout"
    headers = {
        "authorization": token.credentials,
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "client-id": "5eb393ee95fab7468a79d189",
        "client-type": "WEB",
        "content-type": "application/json",
        "origin": "https://www.pw.live",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "randomid": "52d3b33f-ad69-4022-85a5-7d195e1dd2ee",
        "referer": "https://www.pw.live/",
        "sec-ch-ua": "'Not/A)Brand';v='99', 'Chromium';v='148'",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Linux",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "x-sdk-version": "0.0.25",
    }
    response = await client.post(url=url, headers=headers)
    return response


async def token(
    input: LoginInput,
    client: HTTPClientDep,
):
    url = f"{API_BASE_URL}/v3/oauth/token"
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "client-id": "5eb393ee95fab7468a79d189",
        "client-type": "WEB",
        "content-type": "application/json",
        "origin": "https://www.pw.live",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "randomid": "52d3b33f-ad69-4022-85a5-7d195e1dd2ee",
        "referer": "https://www.pw.live/",
        "sec-ch-ua": "'Not/A)Brand';v='99', 'Chromium';v='148'",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Linux",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "x-sdk-version": "0.0.25",
    }
    payload = {
        "username": input.username,
        "otp": input.otp,
        "client_id": "system-admin",
        "client_secret": "KjPXuAVfC5xbmgreETNMaL7z",
        "grant_type": "password",
        "organizationId": ORG_ID,
        "latitude": 0,
        "longitude": 0,
    }
    response = await client.post(url=url, headers=headers, json=payload)
    return response
