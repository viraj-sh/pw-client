import logging
import logging.config
import os
from pathlib import Path


def setup_logging(
    name: str = "app",
    level: str = "INFO",
    log_dir: str | Path = "logs",
    json_logs: bool = False,
):
    os.makedirs(log_dir, exist_ok=True)
    log_file = Path(log_dir) / f"{name}.log"

    plain_format = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    json_format = (
        "%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)d"
    )

    if json_logs:
        formatter_class = "pythonjsonlogger.jsonlogger.JsonFormatter"
        formatter_args = {"format": json_format}
    else:
        formatter_class = "logging.Formatter"
        formatter_args = {"format": plain_format}

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"()": formatter_class, **formatter_args},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": level,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "filename": str(log_file),
                "maxBytes": 10 * 1024 * 1024,  # 10MB per file
                "backupCount": 5,
                "encoding": "utf-8",
                "level": level,
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": level,
        },
    }

    logging.config.dictConfig(logging_config)
    return logging.getLogger(name)
