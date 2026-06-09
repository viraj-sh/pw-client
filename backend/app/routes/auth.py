from typing import Annotated, Literal
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import httpx

from app.core.http import HTTPClientDep
from app.services.auth import fetch_countires, otp, verify, security, logout, token
from app.schemas.auth import (
    CountriesResponse,
    OTPInput,
    OTPResponse,
    VerifyResponse,
    LogoutResponse,
    LoginInput,
    LoginResponse,
    UserResponse,
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
        elif response.status_code == 403:
            raise HTTPException(status_code=403, detail="invalid endpoint url")
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
    smsType: Literal["sms", "whatsapp"],
    input_data: OTPInput,
    client: HTTPClientDep,
    resend: bool = False,
):

    try:
        response = await otp(smsType, input_data, client, resend)
        if response.status_code == 201:
            data = response.json()
            return OTPResponse(success=data.get("success"))
        elif response.status_code == 400:
            raise HTTPException(status_code=400, detail="invalid user")
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "External API timed out")
    except httpx.NetworkError:
        raise HTTPException(502, "Could not reach external API")
    except Exception as exc:
        raise HTTPException(500, f"Unexpected error: {exc}")


@router.post("/token", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_user(input: LoginInput, client: HTTPClientDep):
    try:
        response = await token(input, client)
        data = response.json()
        if response.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail="user not found",
            )
        elif response.status_code == 412:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail="invalid username or otp",
            )
        elif response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED, detail="user not found"
            )
        elif response.status_code == 200:
            if data.get("success"):
                return LoginResponse(
                    access_token=data.get("access_token"),
                    refresh_token=data.get("refresh_token"),
                    expires_in=data.get("expires_in"),
                    user=UserResponse(
                        firstName=data.get("user").get("firstName"),
                        lastName=data.get("user").get("lastName"),
                        email=data.get("user").get("email"),
                    ),
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="unknown error"
                )

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
            raise HTTPException(status_code=401, detail="invalid or expired token")
        elif response.status_code == 200:
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
