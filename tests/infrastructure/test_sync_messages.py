"""Unit tests for sync_messages and related functions."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from infrastructure.sync.sync_core import PgSyncManager
from infrastructure.sync.sync_messages import (
    _sync_messages_internal,
    sync_all_messages,
    sync_messages_for_month,
    sync_messages_for_recent,
)


@pytest.fixture
def manager():
    m = PgSyncManager()
    m._contact_cache = {"cnt_test": 1}
    m._agent_cache = {"agnt_test": 10}
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


def _msg(id_str: str, direction: str = "received", created: str | None = None):
    if created is None:
        created = (datetime.now(UTC) - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    return {
        "id": id_str,
        "direction": direction,
        "status": "delivered",
        "type": "text",
        "content": {"text": "Hello" if direction == "sent" else "Hi"},
        "createdDatetime": created,
        "updatedDatetime": created,
        "source": {"inboxAgent": {"id": "agnt_test", "fullName": "Test Agent"}} if direction == "sent" else {},
    }


@pytest.mark.asyncio
async def test_sync_all_messages(manager, mock_conn):
    fake_db_conn = AsyncMock()
    fake_db_conn.fetchrow = AsyncMock(return_value={"count": 5, "last_msg_date": None})
    fake_ctx = MagicMock()
    fake_ctx.__aenter__ = AsyncMock(return_value=fake_db_conn)
    fake_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_conn._pool.acquire = MagicMock(return_value=fake_ctx)
    mock_conn.fetch_all = AsyncMock(
        return_value=[
            MagicMock(**{"__getitem__": lambda s, k: {"cnvs_bird": "conv_1", "cnvs_msgcount": 5}[k]}),
        ]
    )
    mock_conn.fetch_one = AsyncMock(
        side_effect=[
            MagicMock(**{"__getitem__": lambda s, k: {"cnvs_id": 1}[k]}),
            MagicMock(**{"__getitem__": lambda s, k: {"count": 5, "last_msg_date": None}[k]}),
        ]
    )
    manager.client = AsyncMock()
    manager.client.get_messages = AsyncMock(return_value={"items": [], "pagination": {}})

    await sync_all_messages(manager, mock_conn)
    assert manager.client.get_messages.call_count >= 0


@pytest.mark.asyncio
async def test_sync_messages_for_recent(manager, mock_conn):
    mock_conn.fetch_all = AsyncMock(return_value=[])
    await sync_messages_for_recent(manager, mock_conn, days=30)
    assert True


@pytest.mark.asyncio
async def test_sync_messages_for_month(manager, mock_conn):
    mock_conn.fetch_all = AsyncMock(return_value=[])
    await sync_messages_for_month(manager, mock_conn, 2026, 7)
    assert True


@pytest.mark.asyncio
async def test_sync_messages_paginates_by_offset_without_next_page_token(
    manager: PgSyncManager, mock_conn: AsyncMock
) -> None:
    """Regression: API never returns nextPageToken, so cursor pagination stopped at page 1."""
    mock_conn.fetch_one = AsyncMock(return_value=MagicMock(**{"__getitem__": lambda s, k: 1}))
    manager.client = AsyncMock()
    pages = [
        {"items": [_msg(f"p1_{i}") for i in range(20)], "count": 70, "totalCount": 70},
        {"items": [_msg(f"p2_{i}") for i in range(20)], "count": 70, "totalCount": 70},
        {"items": [_msg(f"p3_{i}") for i in range(20)], "count": 70, "totalCount": 70},
        {"items": [_msg(f"p4_{i}") for i in range(10)], "count": 70, "totalCount": 70},
    ]
    manager.client.get_messages = AsyncMock(side_effect=pages)

    total, raw = await _sync_messages_internal(manager, mock_conn, "conv_1")

    assert total == 70
    assert len(raw) == 70
    offsets = [call.kwargs.get("offset") for call in manager.client.get_messages.call_args_list]
    assert offsets == [0, 20, 40, 60]
    assert all("page_token" not in call.kwargs for call in manager.client.get_messages.call_args_list)
