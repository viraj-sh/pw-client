import smtplib
from email.message import EmailMessage
from datetime import datetime


def _format_time(schedule_time):
    try:
        dt = datetime.fromisoformat(str(schedule_time)[:-1])
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return str(schedule_time or "")


def send_email_announcements(smtp_host, smtp_port, username, password, from_addr, to_addrs, announcements):
    """Send announcements as plain-text emails. Returns list of (to, ok)."""
    results = []
    if isinstance(to_addrs, str):
        to_addrs = [to_addrs]
    for announcement in sorted(announcements, key=lambda x: str(x.get("scheduleTime", ""))):
        msg = EmailMessage()
        msg["Subject"] = f"[PW] New announcement ({_format_time(announcement.get('scheduleTime'))})"
        msg["From"] = from_addr
        msg["To"] = ", ".join(to_addrs)
        body = announcement.get("announcement", "New announcement")
        attachment = announcement.get("attachment")
        if attachment and attachment.get("baseUrl") and attachment.get("key"):
            body += (
                "\n\nAttachment: "
                + attachment["baseUrl"].rstrip("/")
                + "/"
                + attachment["key"].lstrip("/")
            )
        msg.set_content(body)
        ok = False
        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                if username and password:
                    server.starttls()
                    server.login(username, password)
                server.send_message(msg)
            ok = True
        except Exception:
            ok = False
        results.append((to_addrs, ok))
    return results
