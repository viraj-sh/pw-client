from core.utils import (
    BASE_URL, ORGANIZATION_ID, CLIENT_ID, CLIENT_SECRET, GRANT_TYPE,
    LATITUDE, LONGITUDE, safe_post,
)


def send_otp(phone: str, country_code: str, random_id=None):
    """Send OTP to the given phone number and country code."""
    url = f"{BASE_URL}/v1/users/get-otp?smsType=0"
    payload = {
        "username": phone,
        "countryCode": country_code,
        "organizationId": ORGANIZATION_ID,
    }
    data = safe_post(url, json=payload)
    if data.get("success"):
        return {"success": True}
    error = data.get("error", {})
    return {
        "success": False,
        "error_message": error.get("message", data.get("message", "Unknown error")),
        "error_status": error.get("status", None),
    }


def get_token(phone: str, otp: str, random_id=None):
    """Exchange phone and OTP for an access token."""
    url = f"{BASE_URL}/v3/oauth/token"
    payload = {
        "username": phone,
        "otp": otp,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": GRANT_TYPE,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "organizationId": ORGANIZATION_ID,
    }
    data = safe_post(url, json=payload)
    if data.get("success") and isinstance(data.get("data"), dict):
        return {
            "success": True,
            "access_token": data["data"].get("access_token"),
            "expires_in": data["data"].get("expires_in"),
        }
    error = data.get("error", {})
    return {
        "success": False,
        "error_message": error.get("message", data.get("message", "Unknown error")),
        "error_status": error.get("status", None),
    }
