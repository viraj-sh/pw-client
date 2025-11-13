from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List


class SendOTPRequest(BaseModel):
    phone: str = Field(..., example="9876543210", description="User's phone number")
    country_code: str = Field(..., example="+91", description="User's country code")


class StandardResponse(BaseModel):
    success: bool = Field(..., description="Indicates if the request was successful")
    error: Optional[str] = Field(None, description="Error message, if any")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data on success")
    status_code: int = Field(..., description="HTTP status code for this response")

class VerifyOtpRequest(BaseModel):
    mobile_no: str = Field(..., description="Registered mobile number to verify")
    otp: str = Field(
        ..., description="One-time password sent to the provided mobile number"
    )


class UserInfo(BaseModel):
    user_id: Optional[str] = Field(None, description="Unique identifier for the user")
    f_name: Optional[str] = Field(None, description="First name of the user")
    l_name: Optional[str] = Field(None, description="Last name of the user")
    mob_no: Optional[str] = Field(None, description="User's mobile number")
    country_code: Optional[str] = Field(None, description="Country calling code")
    country_group: Optional[str] = Field(
        None, description="User's region or country group"
    )
    email_id: Optional[str] = Field(None, description="User's email address")
    user_name: Optional[str] = Field(None, description="Username used for login")
    DOB: Optional[str] = Field(None, description="Date of birth of the user")
    address: Optional[str] = Field(None, description="User's registered address")


class VerifyOtpData(BaseModel):
    token: Optional[str] = Field(
        None, description="Bearer access token issued upon successful verification"
    )
    expires_in: Optional[int] = Field(
        None, description="Time in seconds before token expiry"
    )
    user: Optional[UserInfo] = Field(
        None, description="Details of the authenticated user"
    )


class VerifyOtpResponse(BaseModel):
    success: bool = Field(
        ..., description="Indicates whether the OTP verification was successful"
    )
    error: Optional[str] = Field(
        None, description="Error message if OTP verification failed"
    )
    data: Optional[VerifyOtpData] = Field(
        None, description="Response payload containing token and user info"
    )
    status_code: int = Field(
        ..., description="HTTP status code representing the result"
    )

class VerifyTokenData(BaseModel):
    isVerified: Optional[bool] = Field(
        None, description="Indicates whether the token is verified"
    )


class VerifyTokenResponse(BaseModel):
    success: bool = Field(
        ..., description="Indicates success or failure of the operation"
    )
    error: Optional[str] = Field(None, description="Error message if any")
    data: Optional[VerifyTokenData] = Field(
        None, description="Response payload containing verification status"
    )
    status_code: int = Field(
        ..., description="HTTP status code corresponding to the result"
    )
class LogoutResponseModel(BaseModel):
    success: bool = Field(..., description="Indicates if the operation was successful.")
    error: Optional[str] = Field(
        None, description="Error message if the operation failed."
    )
    data: Optional[Dict[str, Any]] = Field(
        None, description="Response data on success."
    )
    status_code: int = Field(
        ..., description="HTTP status code corresponding to the result."
    )

class CountryModel(BaseModel):
    country_abbr: str = Field(
        ..., description="Two-letter country abbreviation, e.g., 'IN'"
    )
    country_flag: Optional[str] = Field(
        None, description="Country flag emoji or icon URL"
    )
    country_name: str = Field(..., description="Full country name, e.g., 'India'")
    country_code: Optional[str] = Field(None, description="Country dialing or ISO code")


class StandardResponseModel(BaseModel):
    success: bool = Field(..., description="Indicates if the request was successful")
    error: Optional[str] = Field(None, description="Error message, if any")
    data: Optional[List[CountryModel]] = Field(
        None, description="List of available countries"
    )
    status_code: int = Field(..., description="HTTP status code for the response")
