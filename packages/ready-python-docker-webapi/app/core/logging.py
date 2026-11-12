"""日誌設定：以標準庫 logging 的 dictConfig 統一格式。"""

import logging
from logging.config import dictConfig

_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s [%(process)d] %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def configure_logging(level: str = "INFO") -> None:
    """套用一次性日誌設定；重複呼叫是安全的。"""
    log_level = level.upper()
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": _LOG_FORMAT, "datefmt": _DATE_FORMAT},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stderr",
                },
            },
            "root": {"handlers": ["console"], "level": log_level},
            "loggers": {
                "uvicorn": {"handlers": ["console"], "level": log_level, "propagate": False},
                "uvicorn.error": {
                    "handlers": ["console"],
                    "level": log_level,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["console"],
                    "level": log_level,
                    "propagate": False,
                },
                "sqlalchemy.engine": {
                    "handlers": ["console"],
                    "level": "WARNING",
                    "propagate": False,
                },
                "aiosqlite": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    """取得具名 logger（薄封裝，方便日後統一替換）。"""
    return logging.getLogger(name)
