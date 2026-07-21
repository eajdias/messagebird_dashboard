"""Centralized logging configuration for the MBird API.

Call ``setup_logging()`` once during application lifespan startup.
All loggers in the project should use the ``m_bird.*`` namespace hierarchy:

    m_bird.scheduler   — APScheduler jobs
    m_bird.sync        — pg_sync_engine, sync_profiles
    m_bird.cache       — TTL cache
    m_bird.api_client  — MessageBird HTTP client
    m_bird.db          — database pool / repository
    m_bird.auth        — JWT authentication
    m_bird.request     — HTTP request/response middleware
"""

from __future__ import annotations

import logging
import logging.config
import os

_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_APP_ENV = os.getenv("APP_ENV", "development").lower()

_FORMATTER_NAME = "m_bird"


def _json_formatter() -> dict[str, str]:
    """Return a dictConfig formatter entry that outputs single-line structured logs."""
    return {
        "format": "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        "datefmt": "%Y-%m-%dT%H:%M:%S",
    }


def _human_formatter() -> dict[str, str]:
    """Return a dictConfig formatter entry for readable dev output."""
    return {
        "format": "\033[36m%(asctime)s\033[0m %(levelname)-8s \033[33m%(name)s\033[0m %(message)s",
        "datefmt": "%H:%M:%S",
    }


def setup_logging() -> None:
    """Configure the root logger for the entire application.

    - Development (APP_ENV=development): coloured human-readable output to stderr.
    - Production  (APP_ENV=production):  timestamped structured output to stdout.

    The root logger is set to the level defined by the ``LOG_LEVEL`` env var
    (default: INFO).  Third-party libraries (uvicorn, httpx, asyncpg, apscheduler)
    are clamped to WARNING to keep output focused.
    """
    fmt = _human_formatter() if _APP_ENV == "development" else _json_formatter()

    config: dict[str, object] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            _FORMATTER_NAME: fmt,
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": _FORMATTER_NAME,
                "stream": "ext://sys.stdout" if _APP_ENV != "development" else "ext://sys.stderr",
            },
        },
        "root": {
            "level": _LOG_LEVEL,
            "handlers": ["console"],
        },
        "loggers": {
            # ── Application loggers (inherit root level) ──
            "m_bird": {
                "level": _LOG_LEVEL,
                "handlers": ["console"],
                "propagate": False,
            },
            # ── Route-specific loggers ──
            "api": {
                "level": _LOG_LEVEL,
                "handlers": ["console"],
                "propagate": False,
            },
            # ── Third-party: clamp to WARNING ──
            "uvicorn": {"level": "WARNING"},
            "uvicorn.access": {"level": "WARNING"},
            "uvicorn.error": {"level": "INFO"},
            "httpx": {"level": "WARNING"},
            "httpcore": {"level": "WARNING"},
            "asyncpg": {"level": "WARNING"},
            "apscheduler": {"level": "INFO"},
        },
    }

    logging.config.dictConfig(config)

    root = logging.getLogger()
    root.info(
        "Logging configured: level=%s env=%s",
        _LOG_LEVEL,
        _APP_ENV,
    )


def get_request_logger() -> logging.Logger:
    """Return the logger used by the request/response middleware."""
    return logging.getLogger("m_bird.request")
