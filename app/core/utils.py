import os
from pathlib import Path
from dotenv import load_dotenv, set_key
from typing import Any, Optional
import sys

ENV_PATH = ".env"
# ASCII COLORS
RESET = "\033[0m"
BOLD = "\033[1m"
FG_RED = "\033[31m"
FG_WHITE = "\033[97m"
FG_GREEN = "\033[32m"
FG_YELLOW = "\033[33m"


class EnvManager:
    path: Path = Path(ENV_PATH).resolve()
    _loaded = False

    @classmethod
    def _ensure_loaded(cls, force: bool = True):
        if not cls._loaded or force:
            if cls.path.exists():
                load_dotenv(cls.path, override=True)
            cls._loaded = True

    @classmethod
    def get(
        cls, key: str, default: str | None = None, *, force_reload: bool = True
    ) -> str | None:
        cls._ensure_loaded(force=force_reload)
        return os.getenv(key, default)

    @classmethod
    def set(cls, key: str, value: str) -> None:
        try:
            if not cls.path.exists():
                cls.path.touch()
            set_key(str(cls.path), key, value)
            cls._loaded = False  # force reload next time
        except Exception as e:
            raise RuntimeError(f"Failed to set environment variable '{key}': {e}")

    @classmethod
    def unset(cls, key: str) -> None:
        if cls.path.exists():
            lines = cls.path.read_text().splitlines()
            new_lines = [l for l in lines if not l.startswith(f"{key}=")]
            cls.path.write_text("\n".join(new_lines))
        os.environ.pop(key, None)
        cls._loaded = False


def standard_response(
    success: bool,
    error: Optional[str] = None,
    data: Optional[Any] = None,
    status_code: int | None = None,
) -> dict[str, Any]:
    return {
        "success": bool(success),
        "error": error if not success else None,
        "data": data if success else None,
        "status_code": status_code,
    }


def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def frontend_path() -> str:
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "static")
