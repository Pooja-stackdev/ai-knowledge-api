"""Application logging configuration."""

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import ClassVar

from app.core.config import settings

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE = LOG_DIR / "application.log"

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

logger = logging.getLogger("app")

class ContextFormatter(logging.Formatter):
    """Formatter that prints values supplied through logging extra."""

    STANDARD_FIELDS = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "asctime",
        "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)

        extra = {
            key: value
            for key, value in record.__dict__.items()
            if key not in self.STANDARD_FIELDS
        }

        if extra:
            message += f" | {extra}"

        return message
    
# def setup_logging() -> None:
#     """Configure application-wide console and rotating file logging.

#     Logging configuration is applied only once to prevent duplicate
#     log messages when the application is reloaded or imported multiple times.
#     """
#     if logger.handlers:
#         return

#     LOG_DIR.mkdir(parents=True, exist_ok=True)

#     log_level = getattr(
#         logging,
#         settings.log_level.upper(),
#         logging.INFO,
#     )

#     logger.setLevel(log_level)
#     logger.propagate = False

#     formatter = logging.Formatter(LOG_FORMAT)

#     console_handler = logging.StreamHandler()
#     console_handler.setLevel(log_level)
#     console_handler.setFormatter(formatter)

#     file_handler = TimedRotatingFileHandler(
#         filename=LOG_FILE,
#         when="midnight",
#         interval=1,
#         backupCount=30,
#         encoding="utf-8",
#     )
#     file_handler.setLevel(log_level)
#     file_handler.setFormatter(formatter)

#     logger.addHandler(console_handler)
#     logger.addHandler(file_handler)

def setup_logging() -> None:
    """Configure application-wide console and rotating file logging."""

    if logger.handlers:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_level = getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO,
    )

    logger.setLevel(log_level)
    logger.propagate = False

    formatter = ContextFormatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    file_handler = TimedRotatingFileHandler(
        filename=LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)