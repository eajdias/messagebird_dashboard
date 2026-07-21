"""Sync profile definitions for APScheduler.

Each profile configures incremental and full sync intervals, lookback windows,
and message collection parameters. Select via SYNC_PROFILE env var.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SyncProfile:
    name: str
    incremental_minutes: int | None
    incremental_lookback: int | None
    full_sync_hour: int | None
    full_sync_minute: int
    sync_messages: bool
    messages_days: int | None
    backfill_surveys: bool

    @property
    def has_incremental(self) -> bool:
        return self.incremental_minutes is not None

    @property
    def has_full_sync(self) -> bool:
        return self.full_sync_hour is not None


PROFILES: dict[str, SyncProfile] = {
    "debug": SyncProfile(
        name="debug",
        incremental_minutes=15,
        incremental_lookback=60,
        full_sync_hour=None,
        full_sync_minute=0,
        sync_messages=True,
        messages_days=1,
        backfill_surveys=True,
    ),
    "short": SyncProfile(
        name="short",
        incremental_minutes=30,
        incremental_lookback=120,
        full_sync_hour=None,
        full_sync_minute=0,
        sync_messages=True,
        messages_days=2,
        backfill_surveys=True,
    ),
    "hourly": SyncProfile(
        name="hourly",
        incremental_minutes=60,
        incremental_lookback=180,
        full_sync_hour=None,
        full_sync_minute=0,
        sync_messages=True,
        messages_days=3,
        backfill_surveys=True,
    ),
    "daily": SyncProfile(
        name="daily",
        incremental_minutes=60,
        incremental_lookback=120,
        full_sync_hour=3,
        full_sync_minute=0,
        sync_messages=True,
        messages_days=None,
        backfill_surveys=True,
    ),
    "weekly": SyncProfile(
        name="weekly",
        incremental_minutes=60,
        incremental_lookback=120,
        full_sync_hour=4,
        full_sync_minute=0,
        sync_messages=True,
        messages_days=90,
        backfill_surveys=True,
    ),
    "monthly": SyncProfile(
        name="monthly",
        incremental_minutes=None,
        incremental_lookback=None,
        full_sync_hour=5,
        full_sync_minute=0,
        sync_messages=True,
        messages_days=365,
        backfill_surveys=True,
    ),
}

DEFAULT_PROFILE = "daily"


def get_active_profile() -> SyncProfile:
    """Read SYNC_PROFILE env var and return the matching profile."""
    name = os.getenv("SYNC_PROFILE", DEFAULT_PROFILE).lower()
    if name not in PROFILES:
        import logging

        logging.getLogger("m_bird.sync_profiles").warning(
            "Unknown sync profile %r, falling back to %r", name, DEFAULT_PROFILE
        )
        name = DEFAULT_PROFILE
    return PROFILES[name]


def list_profiles() -> list[dict[str, object]]:
    """Return all available profiles as serializable dicts."""
    return [
        {
            "name": p.name,
            "incremental_minutes": p.incremental_minutes,
            "incremental_lookback": p.incremental_lookback,
            "full_sync_hour": p.full_sync_hour,
            "full_sync_minute": p.full_sync_minute,
            "sync_messages": p.sync_messages,
            "messages_days": p.messages_days,
            "backfill_surveys": p.backfill_surveys,
        }
        for p in PROFILES.values()
    ]
