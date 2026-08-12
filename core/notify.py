import os

from dotenv import load_dotenv

from core.announcer import fetch_batch_announcements
from core.content import fetch_batches
from core.tracker import load_known_ids, get_new_announcements, update_known_ids, save_known_ids
from notification.discord_noti import send_discord_announcements
from notification.telegram_noti import send_telegram_announcements
from notification.email_noti import send_email_announcements

TRACKER_FILE = os.path.join("data", "known_announcements.json")


def _send_all(announcements):
    sent = {}
    discord_url = os.getenv("DISCORD_WEBHOOK_URL")
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat = os.getenv("TELEGRAM_CHAT_ID")
    smtp_host = os.getenv("SMTP_HOST")

    if discord_url:
        sent["discord"] = send_discord_announcements(discord_url, announcements)
    if tg_token and tg_chat:
        sent["telegram"] = send_telegram_announcements(tg_token, tg_chat, announcements)
    if smtp_host:
        to = os.getenv("EMAIL_TO")
        if to:
            to = [a.strip() for a in to.split(",") if a.strip()]
            sent["email"] = send_email_announcements(
                smtp_host,
                int(os.getenv("SMTP_PORT", "587")),
                os.getenv("SMTP_USERNAME", ""),
                os.getenv("SMTP_PASSWORD", ""),
                os.getenv("EMAIL_FROM", os.getenv("SMTP_USERNAME", "")),
                to,
                announcements,
            )
    return sent


def run_notifier(batch_names=None):
    """Fetch new announcements for all (or matching) batches and push them."""
    load_dotenv()
    token_file = os.getenv("TOKEN_FILE", os.path.join("data", "token.txt"))
    if not os.path.exists(token_file):
        return {"error": "no token file"}
    token = open(token_file).read().strip()
    if not token:
        return {"error": "empty token"}

    known = load_known_ids(TRACKER_FILE)
    os.makedirs(os.path.dirname(TRACKER_FILE) or ".", exist_ok=True)
    total_new = []

    for batch in fetch_batches(token):
        name = batch.get("name", "")
        if batch_names and not any(k.lower() in name.lower() for k in batch_names):
            continue
        announcements = fetch_batch_announcements(token, batch.get("_id"))
        new = get_new_announcements(announcements, known)
        for ann in new:
            ann["batchName"] = name
        total_new.extend(new)
        known = update_known_ids(announcements, known)

    save_known_ids(known, TRACKER_FILE)

    if not total_new:
        return {"new": 0, "sent": {}}

    sent = _send_all(total_new)
    return {"new": len(total_new), "sent": sent}


if __name__ == "__main__":
    import json

    result = run_notifier()
    print(json.dumps(result, indent=2, default=str))
