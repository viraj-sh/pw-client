from core.content import fetch_announcements, fetch_batches
from core.utils import verify_token


def fetch_batch_announcements(token, batch_id, page=1):
    """Fetch announcements for a batch after verifying the token."""
    if not verify_token(token).get("success"):
        return []
    return fetch_announcements(token, batch_id, page)
