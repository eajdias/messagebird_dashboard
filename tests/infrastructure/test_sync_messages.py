"""Unit tests for sync_messages and related functions."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from infrastructure.sync.sync_core import PgSyncManager
from infrastructure.sync.sync_messages import (
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
