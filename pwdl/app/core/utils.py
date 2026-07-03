import base64
import json
from typing import Tuple

from app.core.exceptions import ValidationException


def extract_org_and_role_from_token(token: str) -> Tuple[str, str]:
    default_org = "5eb393ee95fab7468a79d189"
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            payload = parts[1]
            payload += "=" * ((4 - len(payload) % 4) % 4)
            data = json.loads(base64.b64decode(payload).decode("utf-8")).get("data", {})

            # Extract organization ID
            org_id = data.get("organization", {}).get("_id")
            if org_id == "5eb393ee95fab7468a79t189":
                org_id = "5eb393ee95fab7468a79d189"
            elif not org_id:
                org_id = default_org

            # Extract roles
            roles = data.get("roles", [])
            if not roles:
                raise ValidationException(
                    "No roles found in the authorization token payload."
                )
            role = roles[0]
            return org_id, role
    except ValidationException as e:
        raise e
    except Exception as e:
        raise ValidationException(f"Failed to parse authorization token: {str(e)}")

    raise ValidationException("Invalid authorization token format.")
