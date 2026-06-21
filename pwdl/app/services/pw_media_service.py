import base64
import httpx
from typing import Optional
from app.core.config import get_settings
from app.core.exceptions import UpstreamAPIException, MediaResolutionException
from app.core.logging import get_logger

logger = get_logger("pw_media_service")
settings = get_settings()

def _xor_encrypt(data: str, token: str) -> list[int]:
    return [ord(c) ^ ord(token[i % len(token)]) for i, c in enumerate(data)]

def _insert_zeros(hex_string: str) -> str:
    result = "00"
    for i in range(0, len(hex_string), 2):
        result += hex_string[i:i+2]
        if i + 2 < len(hex_string):
            result += "00"
    return result

def _decrypt_otp(otp_b64: str, token: str) -> str:
    decoded_bytes = base64.b64decode(otp_b64)
    decoded_ints = [int(byte) for byte in decoded_bytes]
    result = "".join(
        chr(decoded_ints[i] ^ ord(token[i % len(token)]))
        for i in range(len(decoded_ints))
    )
    return result

async def fetch_decryption_key(
    client: httpx.AsyncClient,
    token: str,
    random_id: str,
    kid: str
) -> str:
    logger.info(f"Initiating decryption key exchange for KID={kid}")
    try:
        clean_kid = kid.replace("-", "")
        xor_ints = _xor_encrypt(clean_kid, token)
        otp_key = base64.b64encode(bytes(xor_ints)).decode("utf-8")
        encoded_otp_key_step1 = otp_key.encode("utf-8").hex()
        encoded_otp_key = _insert_zeros(encoded_otp_key_step1)

        url = f"{settings.PW_API_BASE_URL}/v1/videos/get-otp"
        params = {
            "key": encoded_otp_key,
            "isEncoded": "true"
        }
        headers = {
            "accept": "*/*",
            "authorization": f"Bearer {token}",
            "client-id": "5eb393ee95fab7468a79d189",
            "client-type": "WEB",
            "content-type": "application/json",
            "randomid": random_id
        }

        response = await client.get(
            url,
            params=params,
            headers=headers,
            timeout=settings.REQUEST_TIMEOUT_SECONDS
        )
        if response.is_error:
            logger.error(f"Failed to fetch OTP from get-otp endpoint. Status: {response.status_code}")
            raise UpstreamAPIException(
                message="Failed to fetch OTP from get-otp endpoint during key exchange",
                status_code=response.status_code,
                detail=response.text
            )

        data = response.json()
        otp_payload = data.get("data", {}).get("otp")
        if not otp_payload:
            logger.error("Response from get-otp did not contain otp field in data payload")
            raise MediaResolutionException(
                "Upstream key exchange response did not contain OTP field"
            )

        decryption_key = _decrypt_otp(otp_payload, token)
        logger.info("Successfully completed key exchange and retrieved decryption key")
        return decryption_key

    except httpx.RequestError as exc:
        logger.error(f"HTTP request to key exchange API failed: {exc}")
        raise UpstreamAPIException(
            message=f"Network error communicating with upstream key exchange API: {exc}",
            status_code=500
        )
    except Exception as exc:
        if isinstance(exc, (UpstreamAPIException, MediaResolutionException)):
            raise exc
        logger.error(f"Unexpected error in key exchange pipeline: {exc}")
        raise MediaResolutionException(f"Failed to resolve decryption key: {exc}")
