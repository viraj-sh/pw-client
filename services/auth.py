from typing import Optional, Any, Dict
import uuid
import requests
import json
from datetime import timedelta
from core.utils import EnvManager, standard_response
from core.logging import setup_logging
from core.exceptions import handle_exception
from core.cache import cached_request, invalidate_cache
from .data_model.model_auth import Country

def send_otp(phone: str, country_code: str) -> Dict[str, Any]:
    logger = setup_logging(name="services.send_otp", level="INFO")
    url = "https://api.penpencil.co/v1/users/get-otp?smsType=0"

    try:
        organization_id = "5eb393ee95fab7468a79d189"
        if not organization_id:
            logger.warning("Organization ID missing in environment variables.")
            return standard_response(
                False, error="Missing organization ID", status_code=400
            )

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": "https://www.pw.live/",
            "Randomid": str(uuid.uuid4()),
        }

        payload = {
            "username": phone,
            "countryCode": country_code,
            "organizationId": organization_id,
        }

        logger.info(f"Sending OTP to {phone} with country code {country_code}.")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        data = response.json()

        if data.get("success"):
            logger.info("OTP sent successfully.")
            result = {"message": "OTP sent successfully"}
            return standard_response(True, data=result, status_code=200)

        error_info = data.get("error", {})
        error_message = error_info.get("message", "Unknown error")
        status = error_info.get("status", response.status_code)

        logger.warning(f"OTP sending failed: {error_message}")
        return standard_response(False, error=error_message, status_code=status)

    except Exception as exc:
        return handle_exception(logger, exc, context="send_otp")


def verify_otp(mobile_no: str, otp: str) -> Dict[str, Any]:
    logger = setup_logging(name="services.verify_otp", level="INFO")

    try:
        url = "https://api.penpencil.co/v3/oauth/token"
        querystring = {"smsType": "0", "fallback": "true"}

        # Fetch secure configuration from environment
        client_id = "system-admin"
        organization_id = "5eb393ee95fab7468a79d189"

        payload = {
            "username": str(mobile_no),
            "otp": str(otp),
            "client_id": client_id,
            "grant_type": "password",
            "organizationId": organization_id,
        }

        headers = {
            "content-type": "application/json",
            "origin": "https://www.pw.live",
            "referer": "https://www.pw.live/",
            "user-agent": "Mozilla/5.0",
        }

        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=headers,
            params=querystring,
            timeout=10,
        )

        result = response.json()

        if not result.get("success"):
            error_info = result.get("error", {})
            error_message = error_info.get("message", "Unknown error")
            error_status = error_info.get("status", "No status")

            logger.warning(f"OTP verification failed: {error_status} - {error_message}")

            return standard_response(
                success=False,
                error=f"Error {error_status}: {error_message}",
                status_code=400,
            )

        data = result.get("data", {})
        user = data.get("user", {})

        token = f"Bearer {data.get('access_token', '')}"
        expires_in = data.get("expires_in", 0)
        EnvManager.set("TOKEN", token)
        logger.info("TOKEN saved via EnvManager")

        user_dict = {
            "user_id": user.get("id"),
            "f_name": user.get("firstName"),
            "l_name": user.get("lastName"),
            "mob_no": user.get("primaryNumber"),
            "country_code": user.get("countryCode"),
            "country_group": user.get("countryGroup"),
            "email_id": user.get("email"),
            "user_name": user.get("username"),
            "DOB": user.get("dateOfBirth"),
            "address": user.get("address"),
        }

        result_dict = {
            "token": token,
            "expires_in": expires_in,
            "user": user_dict,
        }

        logger.info(f"OTP verification successful for mobile: {mobile_no}")

        return standard_response(
            success=True,
            data=result_dict,
            status_code=200,
        )

    except Exception as exc:
        return handle_exception(logger, exc, context="verify_otp")

def verify_token() -> Dict[str, Any]:
    logger = setup_logging(name="services.verify_token", level="INFO")

    try:
        url = "https://api.penpencil.co/v3/oauth/verify-token"

        organization_id = "5eb393ee95fab7468a79d189"
        token = EnvManager.get("TOKEN")

        if not organization_id:
            logger.warning("Missing PENPENCIL_ORG_ID in environment.")
            return standard_response(
                False, error="Organization ID not configured", status_code=500
            )

        if not token:
            logger.warning("Missing TOKEN in environment.")
            return standard_response(
                False, error="Token not configured", status_code=401
            )

        headers = {
            "organizationid": organization_id,
            "referer": "https://www.pw.live/",
            "user-agent": "Mozilla/5.0",
            "origin": "https://www.pw.live",
            "authorization": token,
            "randomid": str(uuid.uuid4()),
        }

        logger.info("Sending token verification request to Penpencil API.")
        response = requests.post(url, headers=headers, timeout=10)

        if response.status_code != 200:
            logger.warning(f"Unexpected status code from API: {response.status_code}")
            return standard_response(
                False,
                error=f"HTTP {response.status_code}",
                status_code=response.status_code,
            )

        result = response.json()
        success = result.get("success", False)

        if not success:
            error_info = result.get("error", {})
            message = error_info.get("message", "Unknown error")
            status = error_info.get("status", "Unknown")
            logger.warning(f"Token verification failed: {message} (status={status})")
            return standard_response(
                False, error=f"Error {status}: {message}", status_code=400
            )

        data = result.get("data", {})
        is_verified = data.get("isVerified", False)

        logger.info(f"Token verification successful: isVerified={is_verified}")
        return standard_response(
            True, data={"isVerified": is_verified}, status_code=200
        )

    except Exception as exc:
        return handle_exception(logger, exc, context="verify_token")


def logout_user() -> Dict[str, Any]:
    logger = setup_logging(name="core.logout_user", level="INFO")

    try:
        url = "https://api.penpencil.co/v1/oauth/logout"
        token = EnvManager.get("TOKEN")

        if not token:
            logger.warning("Missing TOKEN in environment.")
            return standard_response(
                False, error="Token not configured", status_code=401
            )

        device_id = token.replace("Bearer ", "")
        payload = {"deviceId": device_id}
        headers = {
            "client-type": "WEB",
            "content-type": "application/json",
            "authorization": token,
        }

        logger.info("Initiating logout request to Penpencil API.")
        response = requests.post(
            url, data=json.dumps(payload), headers=headers, timeout=10
        )

        if response.status_code != 200:
            logger.warning(f"Unexpected API response status: {response.status_code}")
            return standard_response(
                False,
                error=f"Unexpected status code: {response.status_code}",
                status_code=response.status_code,
            )

        result = response.json()
        success = result.get("success", False)

        if not success:
            error_info = result.get("error", {})
            message = error_info.get("message", "Logout failed")
            logger.warning(f"Logout unsuccessful: {message}")
            return standard_response(False, error=message, status_code=400)

        logger.info("Logout request successful. Verifying token status.")
        verification = verify_token()

        # If verification fails (e.g., 401, token invalid), that means logout succeeded
        if not verification.get("success"):
            logger.info(
                "Token verification failed after logout — token invalidated successfully."
            )
            EnvManager.unset("TOKEN")
            return standard_response(True, data={"logout": True}, status_code=200)

        verified = verification["data"].get("isVerified", True)
        if verified:
            logger.warning("Token still valid after logout attempt — logout failed.")
            return standard_response(
                False, error="Token still active after logout", status_code=400
            )

        logger.info("Logout completed successfully and token invalidated.")
        EnvManager.unset("TOKEN")
        return standard_response(True, data={"logout": True}, status_code=200)

    except Exception as exc:
        return handle_exception(logger, exc, context="logout_user")


def get_countries(refetch: bool = False) -> Dict[str, Any]:
    logger = setup_logging(name="core.get_countries", level="INFO")
    log_prefix = "[PWLiveAPI] "

    try:
        url = "https://static.pw.live/auth-fe/assets/json/app-constants.json"

        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.6",
            "referer": "https://www.pw.live/",
            "origin": "https://www.pw.live/",
            "user-agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/141.0.0.0 Safari/537.36"
            ),
        }
        # Add no-cache headers only if explicitly refetching
        if refetch:
            headers.update(
                {
                    "cache-control": "no-cache",
                    "pragma": "no-cache",
                }
            )

        response = cached_request(
            method="GET",
            url=url,
            headers=headers,
            log_prefix=log_prefix,
            expire_after=timedelta(hours=24),
            refetch=refetch,
        )

        if not response:
            return standard_response(
                False, error="Empty response from API", status_code=400
            )

        if hasattr(response, "json"):
            try:
                response = response.json()
            except Exception:
                return standard_response(
                    False, error="Failed to parse JSON from API", status_code=400
                )

        if not isinstance(response, list):
            return standard_response(
                False, error="Unexpected response format", status_code=400
            )

        countries: List[Dict[str, Any]] = []
        for item in response:
            if isinstance(item, dict):
                parsed = Country.from_json(item)
                if parsed:
                    countries.append(
                        {
                            "country_abbr": parsed.country_abbr,
                            "country_flag": parsed.country_flag,
                            "country_name": parsed.country_name,
                            "country_code": parsed.country_code,
                        }
                    )

        if not countries:
            return standard_response(
                False, error="No valid country data found", status_code=404
            )

        return standard_response(True, data=countries, status_code=200)

    except Exception as exc:
        return handle_exception(logger, exc, context="get_countries")
