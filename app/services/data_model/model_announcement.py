from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass
class Announcement:
    announcement: Optional[str]
    id: Optional[str]
    schedule_time: Optional[str]
    endlink: Optional[str]

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> Optional["Announcement"]:
        if not isinstance(payload, dict):
            return None

        ann_text = payload.get("announcement")
        ann_id = payload.get("_id")
        schedule_time = payload.get("scheduleTime")

        attachment = payload.get("attachment") or {}
        endlink = None
        if isinstance(attachment, dict):
            base = attachment.get("baseUrl")
            key = attachment.get("key")
            if base and key:
                endlink = f"{base}{key}"

        return cls(
            announcement=ann_text,
            id=ann_id,
            schedule_time=schedule_time,
            endlink=endlink,
        )
