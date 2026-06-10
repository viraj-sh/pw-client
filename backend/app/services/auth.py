from typing import Literal
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated

from app.core.http import HTTPClientDep
from app.core.urls import AuthURLs
from app.core.constants import (
    API_HEADERS,
    STATIC_HEADERS,
    auth_headers,
    BASE_PAYLOAD,
    TOKEN_PAYLOAD_BASE,
)
from app.schemas.auth import OTPInput, LoginInput, ResendInput

security = HTTPBearer()


async def fetch_countires(client: HTTPClientDep):
    return await client.get(url=AuthURLs.APP_CONSTANTS, headers=STATIC_HEADERS)


async def otp(
    smsType: Literal["whatsapp", "sms", "call"],
    input_data: OTPInput,
    client: HTTPClientDep,
):
    if smsType == "whatsapp":
        sms_type_value = 1
    elif smsType == "call":
        sms_type_value = 2
    else:
        sms_type_value = 0
    params = {"smsType": sms_type_value}

    payload = {
        **BASE_PAYLOAD,
        "username": input_data.phone_no,
        "countryCode": input_data.country_code,
    }
    return await client.post(
        url=AuthURLs.GET_OTP, params=params, headers=API_HEADERS, json=payload
    )


async def resend_otp(
    smsType: Literal["whatsapp", "sms", "call"],
    input_data: ResendInput,
    client: HTTPClientDep,
):
    if smsType == "whatsapp":
        sms_type_value = 1
    elif smsType == "call":
        sms_type_value = 2
    else:
        sms_type_value = 0
    params = {"smsType": sms_type_value}
    payload = {**BASE_PAYLOAD, "mobile": input_data.mobile}
    return await client.post(
        url=AuthURLs.RESEND_OTP, params=params, headers=API_HEADERS, json=payload
    )


async def token(
    input: LoginInput,
    client: HTTPClientDep,
    method: Literal["otp", "password"] = "otp",
):
    payload = {**TOKEN_PAYLOAD_BASE, "username": input.username}
    if method == "otp":
        if input.otp is None:
            raise ValueError("OTP required for method='otp'")
        payload["otp"] = str(input.otp)
    if method == "password":
        if input.password is None:
            raise ValueError("PASSWORD required for method='password'")
        payload["password"] = input.password
    return await client.post(url=AuthURLs.TOKEN, headers=API_HEADERS, json=payload)


async def reset(
    input: LoginInput,
    client: HTTPClientDep,
):
    payload = {**TOKEN_PAYLOAD_BASE, "username": input.username}
    if input.otp is None:
        raise ValueError("OTP required for reset password")
    elif input.password is None:
        raise ValueError("PASSWORD required for reset password")
    payload["otp"] = input.otp
    payload["password"] = input.password
    return await client.post(
        url=AuthURLs.RESET_PASSWORD, headers=API_HEADERS, json=payload
    )


async def refresh(
    refresh_token: str,
    client: HTTPClientDep,
):
    payload = {**TOKEN_PAYLOAD_BASE, "refresh_token": refresh_token}
    return await client.post(
        url=AuthURLs.REFRESH_TOKEN,
        headers=API_HEADERS,
        json=payload,
    )


async def exchange(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
):
    return await client.get(
        url=AuthURLs.EXCHANGE_TOKEN, headers=auth_headers(token.credentials)
    )


async def verify(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
):
    return await client.post(
        url=AuthURLs.VERIFY_TOKEN, headers=auth_headers(token.credentials)
    )


async def logout(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
):
    return await client.post(
        url=AuthURLs.LOGOUT, headers=auth_headers(token.credentials)
    )
