"""Unit tests for sync_conversations (full structural sync)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from infrastructure.sync.sync_conversations import sync_conversations
from infrastructure.sync.sync_core import PgSyncManager, parse_dt

# ── Helpers ─────────────────────────────────────────────────────


def _make_conversation(bird_id: str, updated: str, status: str = "active"):
    """Build a minimal Bird API conversation object."""
    return {
        "id": bird_id,
        "status": status,
        "updatedDatetime": updated,
        "createdDatetime": updated,
        "lastReceivedDatetime": updated,
        "contactId": "cnt_test",
        "contact": {"displayName": "Test", "msisdn": "+5511999999999"},
        "messages": {"totalCount": 3},
        "lastUsedChannelId": "chan_1",
        "assignedTo": {},
    }


def _make_page(conversations: list[dict], next_page_token: str | None = None):
    """Build a Bird API list response."""
    result = {"items": conversations, "pagination": {"totalCount": len(conversations)}}
    if next_page_token:
        result["pagination"]["nextPageToken"] = next_page_token
    return result


# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def manager():
    m = PgSyncManager()
    m._contact_cache = {"cnt_test": 1}
    m._agent_cache = {}
    return m


@pytest.fixture
def mock_conn():
    conn = AsyncMock()
    conn.fetch_all = AsyncMock(return_value=[])
    conn.fetch_one = AsyncMock(return_value=None)
    conn.execute_query = AsyncMock()
    conn.execute_many = AsyncMock()
    mock_tx = MagicMock()
    mock_tx.__aenter__ = AsyncMock(return_value=None)
    mock_tx.__aexit__ = AsyncMock(return_value=False)
    conn.transaction = MagicMock(return_value=mock_tx)
    return conn


# ── Tests: parse_dt ────────────────────────────────────────────


def test_parse_dt_none():
    assert parse_dt(None) is None


def test_parse_dt_empty_string():
    assert parse_dt("") is None


def test_parse_dt_z_suffix():
    dt = parse_dt("2026-07-21T12:00:00Z")
    assert dt.year == 2026
    assert dt.month == 7
    assert dt.hour == 12
    assert dt.tzinfo is None


def test_parse_dt_datetime_passthrough():
    now = datetime.now(UTC)
    result = parse_dt(now)
    assert result.tzinfo is None
    assert result.year == now.year


# ── Tests: sync_conversations client-side filtering ──────────────


@pytest.mark.asyncio
async def test_incremental_stops_at_cutoff(manager, mock_conn):
    """When reverse=true, should stop early when hitting conversations older than cutoff."""
    now = datetime.now(UTC)
    recent = (now - timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
    old = (now - timedelta(hours=2)).isoformat().replace("+00:00", "Z")

    page1 = _make_page(
        [
            _make_conversation("c1", recent),
            _make_conversation("c2", recent),
        ],
        next_page_token="page2",
    )
    page2 = _make_page(
        [
            _make_conversation("c3", recent),
            _make_conversation("c4", old),
        ]
    )

    mock_conn.fetch_all = AsyncMock(return_value=[])
    empty_page = _make_page([])
    manager.client = AsyncMock()
    manager.client.list_conversations = AsyncMock(side_effect=[page1, page2, empty_page])

    await sync_conversations(manager, mock_conn)

    assert manager.client.list_conversations.call_count == 3
    first_call_kwargs = manager.client.list_conversations.call_args_list[0]
    assert first_call_kwargs.kwargs.get("reverse") is False
    assert mock_conn.execute_many.call_count == 2


@pytest.mark.asyncio
async def test_incremental_no_reverse_in_full_sync(manager, mock_conn):
    """Sync always uses reverse=false now."""
    manager.client = AsyncMock()
    manager.client.list_conversations = AsyncMock(return_value=_make_page([]))

    await sync_conversations(manager, mock_conn)

    call_kwargs = manager.client.list_conversations.call_args_list[0]
    assert "reverse" in call_kwargs.kwargs and not call_kwargs.kwargs.get("reverse")


@pytest.mark.asyncio
async def test_incremental_processes_all_recent(manager, mock_conn):
    """All conversations are synced (no cutoff)."""
    now = datetime.now(UTC)
    recent = (now - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")

    page = _make_page(
        [
            _make_conversation("c1", recent),
            _make_conversation("c2", recent),
            _make_conversation("c3", recent),
        ]
    )

    mock_conn.fetch_all = AsyncMock(return_value=[])
    empty_page = _make_page([])
    manager.client = AsyncMock()
    manager.client.list_conversations = AsyncMock(side_effect=[page, empty_page])

    await sync_conversations(manager, mock_conn)
    assert mock_conn.execute_many.call_count == 1
    batch = mock_conn.execute_many.call_args_list[0][0][1]
    assert len(batch) == 3


@pytest.mark.asyncio
async def test_empty_response(manager, mock_conn):
    """Empty API response should not crash and should not insert anything."""
    mock_conn.fetch_all = AsyncMock(return_value=[])
    manager.client = AsyncMock()
    manager.client.list_conversations = AsyncMock(return_value=_make_page([]))

    await sync_conversations(manager, mock_conn)
    assert mock_conn.execute_many.call_count == 0


@pytest.mark.asyncio
async def test_api_error_returns_zero(manager, mock_conn):
    """API error should not crash."""
    mock_conn.fetch_all = AsyncMock(return_value=[])
    manager.client = AsyncMock()
    manager.client.list_conversations = AsyncMock(return_value={"error": "timeout"})

    await sync_conversations(manager, mock_conn)
    assert mock_conn.execute_many.call_count == 0


@pytest.mark.asyncio
async def test_reopen_detection(manager, mock_conn):
    """Detects archived->active transition as reopen."""
    now = datetime.now(UTC)
    recent = (now - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")

    existing = MagicMock()
    existing.__getitem__ = lambda self, key: {
        "cnvs_id": 1,
        "cnvs_bird": "c1",
        "cnvs_status": "archived",
        "cnvs_agnt": None,
        "cnvs_reopened_count": 0,
    }[key]

    mock_conn.fetch_all = AsyncMock(return_value=[existing])

    page = _make_page([_make_conversation("c1", recent, status="active")])
    manager.client = AsyncMock()
    manager.client.list_conversations = AsyncMock(return_value=page)

    await sync_conversations(manager, mock_conn)

    execute_many_call = mock_conn.execute_many.call_args_list[-1]
    batch_data = execute_many_call[0][1]
    assert batch_data[0][-1] == 1


# ── Tests: PgSyncManager core methods ───────────────────────────


@pytest.mark.asyncio
async def test_load_caches(manager, mock_conn):
    mock_conn.fetch_all = AsyncMock(
        side_effect=[
            [MagicMock(**{"__getitem__": lambda s, k: {"agnt_id": 1, "agnt_bird": "agnt_1"}[k]})],
            [MagicMock(**{"__getitem__": lambda s, k: {"cnts_id": 1, "cnts_bird": "cnt_1"}[k]})],
        ]
    )

    await manager.load_caches(mock_conn)

    assert manager._agent_cache == {"agnt_1": 1}
    assert manager._contact_cache == {"cnt_1": 1}


@pytest.mark.asyncio
async def test_load_caches_empty(manager, mock_conn):
    await manager.load_caches(mock_conn)
    assert manager._agent_cache == {}
    assert manager._contact_cache == {}


@pytest.mark.asyncio
async def test_seed_known_agents(manager, mock_conn):
    import infrastructure.api.config as api_config

    known_agents_backup = api_config.get_known_agents
    try:
        api_config.get_known_agents = lambda: {
            "bird_1": {"name": "Agent One", "group": "Suporte"},
        }

        await manager.seed_known_agents(mock_conn)

        assert mock_conn.execute_many.call_count == 1
        batch = mock_conn.execute_many.call_args[0][1]
        assert len(batch) == 1
        assert batch[0][0] == "Agent One"
    finally:
        api_config.get_known_agents = known_agents_backup


@pytest.mark.asyncio
async def test_seed_known_agents_empty(manager, mock_conn):
    import infrastructure.api.config as api_config

    backup = api_config.get_known_agents
    try:
        api_config.get_known_agents = lambda: {}
        await manager.seed_known_agents(mock_conn)
        assert mock_conn.execute_many.call_count == 0
    finally:
        api_config.get_known_agents = backup


@pytest.mark.asyncio
async def test_get_or_create_contact_cached(manager, mock_conn):
    manager._contact_cache = {"cnt_existing": 42}
    result = await manager.get_or_create_contact(mock_conn, "cnt_existing", "Test", "+5511999999999")
    assert result == 42
    assert mock_conn.execute_query.call_count == 0


@pytest.mark.asyncio
async def test_get_or_create_contact_new(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(return_value=MagicMock(**{"__getitem__": lambda s, k: {"cnts_id": 99}[k]}))
    result = await manager.get_or_create_contact(mock_conn, "cnt_new", "New Contact", "+5511888888888")
    assert result == 99
    assert manager._contact_cache["cnt_new"] == 99
    assert mock_conn.execute_query.call_count == 1


@pytest.mark.asyncio
async def test_get_or_create_contact_not_found(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(return_value=None)
    result = await manager.get_or_create_contact(mock_conn, "cnt_ghost", "Ghost", "+5511777777777")
    assert result is None


@pytest.mark.asyncio
async def test_get_or_create_agent_cached(manager, mock_conn):
    manager._agent_cache = {"agnt_existing": 7}
    result = await manager.get_or_create_agent(mock_conn, "agnt_existing", "Existing Agent")
    assert result == 7
    assert mock_conn.execute_query.call_count == 0


@pytest.mark.asyncio
async def test_get_or_create_agent_new(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(return_value=MagicMock(**{"__getitem__": lambda s, k: {"agnt_id": 33}[k]}))
    result = await manager.get_or_create_agent(mock_conn, "agnt_new", "New Agent")
    assert result == 33
    assert manager._agent_cache["agnt_new"] == 33


@pytest.mark.asyncio
async def test_get_last_sync_time_none(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(return_value=None)
    created, cursor, offset = await manager.get_last_sync_time(mock_conn, "conversations")
    assert created is None
    assert cursor is None
    assert offset == 0


@pytest.mark.asyncio
async def test_get_last_sync_time_exists(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(
        return_value=MagicMock(
            **{
                "__getitem__": lambda s, k: {
                    "sync_created": datetime(2026, 7, 20, 10, 0, 0),
                    "sync_cursor": "tok_abc",
                    "sync_offset": 5,
                }[k],
            }
        )
    )
    created, cursor, offset = await manager.get_last_sync_time(mock_conn, "conversations")
    assert created == datetime(2026, 7, 20, 10, 0, 0)
    assert cursor == "tok_abc"
    assert offset == 5


@pytest.mark.asyncio
async def test_should_skip_recently_synced(manager, mock_conn):
    now = datetime.now(UTC)
    mock_conn.fetch_one = AsyncMock(
        return_value=MagicMock(
            **{
                "__getitem__": lambda s, k: {
                    "sync_created": now,
                    "sync_cursor": None,
                    "sync_offset": 0,
                }[k],
            }
        )
    )
    assert await manager.should_skip(mock_conn, "conversations", minutes=60)


@pytest.mark.asyncio
async def test_should_skip_not_recently_synced(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(
        return_value=MagicMock(
            **{
                "__getitem__": lambda s, k: {
                    "sync_created": datetime(2020, 1, 1, 0, 0, 0),
                    "sync_cursor": None,
                    "sync_offset": 0,
                }[k],
            }
        )
    )
    assert not await manager.should_skip(mock_conn, "conversations", minutes=60)


@pytest.mark.asyncio
async def test_should_skip_no_sync(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(return_value=None)
    assert not await manager.should_skip(mock_conn, "conversations", minutes=60)


@pytest.mark.asyncio
async def test_save_sync_progress(manager, mock_conn):
    await manager.save_sync_progress(mock_conn, "conversations", cursor="tok_xyz", offset=10)
    assert mock_conn.execute_query.call_count == 1


@pytest.mark.asyncio
async def test_update_sync_state(manager, mock_conn):
    await manager.update_sync_state(mock_conn, "conversations", duration=30.5, records_count=100)
    assert mock_conn.execute_query.call_count == 1


@pytest.mark.asyncio
async def test_log_sync_error(manager, mock_conn):
    await manager.log_sync_error(mock_conn, "conversations", "Something went wrong", code=500, context={"page": 1})
    assert mock_conn.execute_query.call_count == 1


# ── Tests: month_bounds_utc ─────────────────────────────────────


def test_month_bounds_utc():
    from infrastructure.sync.sync_core import month_bounds_utc

    start, end = month_bounds_utc(2026, 7)
    assert start.year == 2026
    assert start.month == 7
    assert start.day == 1
    assert end.month == 8

    start, end = month_bounds_utc(2026, 12)
    assert start.month == 12
    assert end.month == 1
    assert end.year == 2027


def test_month_bounds_utc_invalid():
    from infrastructure.sync.sync_core import month_bounds_utc

    with pytest.raises(ValueError):
        month_bounds_utc(2026, 13)


# ── Tests: to_bird_iso ──────────────────────────────────────────


def test_to_bird_iso():
    from infrastructure.sync.sync_core import to_bird_iso

    dt = datetime(2026, 7, 21, 10, 30, 0, tzinfo=UTC)
    result = to_bird_iso(dt)
    assert result == "2026-07-21T10:30:00Z"
    assert result.endswith("Z")
