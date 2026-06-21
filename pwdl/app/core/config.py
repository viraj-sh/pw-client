from functools import lru_cache
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DOWNLOAD_PATH: Path = Field(default=Path("./downloads"))
    MAX_CONCURRENT_DOWNLOADS: int = Field(default=3, ge=1, le=10)
    DEFAULT_QUALITY: int = Field(default=720)
    DEFAULT_THREADS: int = Field(default=16, ge=1, le=32)
    PW_API_BASE_URL: str = Field(default="https://api.penpencil.co")
    REQUEST_TIMEOUT_SECONDS: float = Field(default=30.0, gt=0.0)
    ALLOWED_ORIGINS: List[str] = Field(default=["*"])
    FFMPEG_PATH: str = Field(default="ffmpeg")
    MP4DECRYPT_PATH: str = Field(default="mp4decrypt")
    LOG_LEVEL: str = Field(default="INFO")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
