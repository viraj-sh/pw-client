from typing import Annotated, Literal
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import httpx

from app.core.http import HTTPClientDep
from app.services.auth import (
    fetch_countires,
    otp,
    resend_otp,
    verify,
    security,
    logout,
    token,
    refresh,
    reset,
    exchange,
)
from app.schemas.auth import (
    CountriesResponse,
    OTPInput,
    OTPResponse,
    VerifyResponse,
    LogoutResponse,
    LoginInput,
    LoginResponse,
    UserResponse,
    ResendInput,
    RefreshResponse,
)

router = APIRouter()


@router.get(
    "/countries", status_code=status.HTTP_200_OK, response_model=list[CountriesResponse]
)
async def get_countries(client: HTTPClientDep):
    try:
        response = await fetch_countires(client)
        if response.status_code == 200:
            data = response.json()
            country_list = []
            for country in data:
                country_list.append(
                    CountriesResponse(
                        country_code=country["c"],
                        flag_emoji=country["e"],
                        country_name=country["n"],
                        dial_code=country["d"],
                    )
                )
            return country_list
        return response.json()
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "External API timed out")
    except httpx.NetworkError:
        raise HTTPException(502, "Could not reach external API")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected error: {exc}")


@router.post("/send-otp", status_code=status.HTTP_201_CREATED)
async def send_otp(
    smsType: Literal["sms", "whatsapp", "call"],
    input_data: OTPInput,
    client: HTTPClientDep,
):

    try:
        response = await otp(smsType, input_data, client)
        if response.status_code == 201:
            return OTPResponse(success=response.json().get("success"))
        elif response.status_code == 400:
            raise HTTPException(
                status_code=400,
                detail=f"{response.json().get('error').get('status')} -> {response.json().get('error').get('message')}",
            )
        return response.json()
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "External API timed out")
    except httpx.NetworkError:
        raise HTTPException(502, "Could not reach external API")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected error: {exc}")


@router.post("/resend-otp", status_code=status.HTTP_200_OK)
async def resend_phone_otp(
    smsType: Literal["sms", "whatsapp", "call"],
    input_data: ResendInput,
    client: HTTPClientDep,
):
    try:
        response = await resend_otp(smsType, input_data, client)
        data = response.json()
        if response.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{data.get('error').get('status')} -> {data.get('error').get('message')}",
            )
        elif response.status_code == 200:
            return OTPResponse(success=response.json().get("success"))
        return response.json()
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "External API timed out")
    except httpx.NetworkError:
        raise HTTPException(502, "Could not reach external API")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected error: {exc}")


@router.post("/token", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_user(
    input: LoginInput, client: HTTPClientDep, method: Literal["otp", "password"] = "otp"
):
    try:
        response = await token(input, client, method)
        data = response.json()
        if response.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail=f"{response.json().get('error').get('status')} -> {response.json().get('error').get('message')}",
            )
        elif response.status_code == 412:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail=f"{data.get('error').get('status')} -> {data.get('error').get('message')}",
            )
        elif response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail=f"{data.get('error').get('status')} -> {data.get('error').get('message')}",
            )
        elif response.status_code == 200:
            if data.get("success"):
                return LoginResponse(
                    access_token=data.get("data").get("access_token"),
                    refresh_token=data.get("data").get("refresh_token"),
                    expires_in=str(data.get("data").get("expires_in")),
                    user=UserResponse(
                        firstName=data.get("data").get("user").get("firstName"),
                        lastName=data.get("data").get("user").get("lastName"),
                        email=data.get("data").get("user").get("email"),
                    ),
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="unknown error"
                )
        return data

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "External API timed out")
    except httpx.NetworkError:
        raise HTTPException(502, "Could not reach external API")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected error: {exc}")


@router.post("/reset-password", status_code=status.HTTP_200_OK, deprecated=True)
async def reset_password(input: LoginInput, client: HTTPClientDep):
    try:
        response = await reset(input, client)
        if response.status_code == 500:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{response.json().get('error').get('status')} -> {response.json().get('error').get('message')}",
            )
        if response.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail=f"{response.json().get('error').get('status')} -> {response.json().get('error').get('message')}",
            )
        return response.json()
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "External API timed out")
    except httpx.NetworkError:
        raise HTTPException(502, "Could not reach external API")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected error: {exc}")


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_access_token(
    refresh_token: str,
    client: HTTPClientDep,
):
    try:
        response = await refresh(refresh_token, client)
        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail=f"{response.json().get('error').get('status')} -> {response.json().get('error').get('message')}",
            )
        elif response.status_code == 200:
            return RefreshResponse(
                access_token=response.json().get("data").get("access_token"),
                refresh_token=response.json().get("data").get("refresh_token"),
                expires_in=response.json().get("data").get("expires_in"),
            )
        return response.json()
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "External API timed out")
    except httpx.NetworkError:
        raise HTTPException(502, "Could not reach external API")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected error: {exc}")


@router.post("/exchange", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def exchange_token(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
):
    try:
        response = await exchange(token, client)
        data = response.json()
        if response.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail=f"{response.json().get('error').get('status')} -> {response.json().get('error').get('message')}",
            )
        elif response.status_code == 412:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail=f"{data.get('error').get('status')} -> {data.get('error').get('message')}",
            )
        elif response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail=f"{data.get('error').get('status')} -> {data.get('error').get('message')}",
            )
        elif response.status_code == 200:
            if data.get("success"):
                return LoginResponse(
                    access_token=data.get("data").get("access_token"),
                    refresh_token=data.get("data").get("refresh_token"),
                    expires_in=data.get("data").get("expires_in"),
                    user=UserResponse(
                        firstName=data.get("data").get("user").get("firstName"),
                        lastName=data.get("data").get("user").get("lastName"),
                        email=data.get("data").get("user").get("email"),
                    ),
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="unknown error"
                )
        return data

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "External API timed out")
    except httpx.NetworkError:
        raise HTTPException(502, "Could not reach external API")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected error: {exc}")


@router.post("/verify", response_model=VerifyResponse, status_code=status.HTTP_200_OK)
async def verify_token(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
):
    try:
        response = await verify(token, client)
        data = response.json()
        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail=f"{data.get('error').get('status')} -> {data.get('error').get('message')}",
            )
        if response.status_code == 200:
            return VerifyResponse(
                success=data.get("success"),
                is_verified=data.get("data").get("isVerified"),
            )
        return response.json()
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "External API timed out")
    except httpx.NetworkError:
        raise HTTPException(502, "Could not reach external API")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected error: {exc}")


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    client: HTTPClientDep,
):
    try:
        response = await logout(token, client)
        data = response.json()
        return LogoutResponse(success=data.get("success"))
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "External API timed out")
    except httpx.NetworkError:
        raise HTTPException(502, "Could not reach external API")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected error: {exc}")
