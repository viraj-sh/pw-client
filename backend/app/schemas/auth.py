from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class CountriesResponse(BaseModel):
    country_code: str
    flag_emoji: str
    country_name: str
    dial_code: str


class OTPInput(BaseModel):
    phone_no: str = Field(min_length=10)
    country_code: str


class OTPResponse(BaseModel):
    success: bool


class VerifyResponse(BaseModel):
    success: bool
    is_verified: bool
    message: str | None = None


class LogoutResponse(BaseModel):
    success: bool


class LoginInput(BaseModel):
    username: str = Field(min_length=10)
    otp: str = Field(min_length=6)


class UserResponse(BaseModel):
    firstName: str
    lastName: str
    username: str | None = None
    email: EmailStr


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: datetime
    user: UserResponse
