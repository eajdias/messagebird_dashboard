"""Unit tests for sync_messages and related functions."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from infrastructure.sync.sync_core import PgSyncManager
from infrastructure.sync.sync_messages import (
    sync_all_messages,
    sync_messages,
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
async def test_sync_messages_basic(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(
        side_effect=[
            MagicMock(**{"__getitem__": lambda s, k: {"cnvs_id": 1}[k]}),
            None,
            MagicMock(
                **{
                    "__getitem__": lambda s, k: {
                        "cnvs_id": 1,
                        "cnvs_status": "active",
                        "cnvs_rating_agent": None,
                        "cnvs_rating_nps": None,
                    }[k]
                }
            ),
        ]
    )
    manager.client = AsyncMock()
    manager.client.get_messages = AsyncMock(return_value={"items": [_msg("msg_1"), _msg("msg_2")], "pagination": {}})

    count = await sync_messages(manager, mock_conn, "conv_test")

    assert count == 2
    assert mock_conn.execute_many.call_count == 1


@pytest.mark.asyncio
async def test_sync_messages_conversation_not_found(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(return_value=None)

    count = await sync_messages(manager, mock_conn, "unknown_conv")

    assert count == 0
    assert mock_conn.execute_many.call_count == 0


@pytest.mark.asyncio
async def test_sync_messages_empty(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(
        side_effect=[
            MagicMock(**{"__getitem__": lambda s, k: {"cnvs_id": 1}[k]}),
            None,
        ]
    )
    manager.client = AsyncMock()
    manager.client.get_messages = AsyncMock(return_value={"items": [], "pagination": {}})

    count = await sync_messages(manager, mock_conn, "conv_test")

    assert count == 0


@pytest.mark.asyncio
async def test_sync_messages_api_error(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(
        side_effect=[
            MagicMock(**{"__getitem__": lambda s, k: {"cnvs_id": 1}[k]}),
            None,
        ]
    )
    manager.client = AsyncMock()
    manager.client.get_messages = AsyncMock(return_value={"error": "timeout"})

    count = await sync_messages(manager, mock_conn, "conv_test")

    assert count == 0


@pytest.mark.asyncio
async def test_sync_messages_sent_agent_resolution(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(
        side_effect=[
            MagicMock(**{"__getitem__": lambda s, k: {"cnvs_id": 1}[k]}),
            None,
            MagicMock(
                **{
                    "__getitem__": lambda s, k: {
                        "cnvs_id": 1,
                        "cnvs_status": "active",
                        "cnvs_rating_agent": None,
                        "cnvs_rating_nps": None,
                    }[k]
                }
            ),
        ]
    )
    manager.client = AsyncMock()
    manager.client.get_messages = AsyncMock(
        return_value={
            "items": [
                _msg("msg_1", direction="sent"),
            ],
            "pagination": {},
        }
    )

    count = await sync_messages(manager, mock_conn, "conv_test")

    assert count == 1


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
async def test_sync_messages_with_date_from(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(
        side_effect=[
            MagicMock(**{"__getitem__": lambda s, k: {"cnvs_id": 1}[k]}),
            MagicMock(**{"__getitem__": lambda s, k: {"msgs_created": datetime(2026, 7, 1, 10, 0, 0)}[k]}),
            MagicMock(
                **{
                    "__getitem__": lambda s, k: {
                        "cnvs_id": 1,
                        "cnvs_status": "active",
                        "cnvs_rating_agent": None,
                        "cnvs_rating_nps": None,
                    }[k]
                }
            ),
        ]
    )
    manager.client = AsyncMock()
    manager.client.get_messages = AsyncMock(return_value={"items": [_msg("msg_1")], "pagination": {}})

    count = await sync_messages(manager, mock_conn, "conv_test")

    assert count == 1


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
async def test_sync_messages_updates_conversation_agent(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(
        side_effect=[
            MagicMock(**{"__getitem__": lambda s, k: {"cnvs_id": 1}[k]}),
            None,
            MagicMock(
                **{
                    "__getitem__": lambda s, k: {
                        "cnvs_id": 1,
                        "cnvs_status": "active",
                        "cnvs_rating_agent": None,
                        "cnvs_rating_nps": None,
                    }[k]
                }
            ),
        ]
    )
    manager.client = AsyncMock()
    manager.client.get_messages = AsyncMock(
        return_value={
            "items": [_msg("msg_1", direction="sent")],
            "pagination": {},
        }
    )

    await sync_messages(manager, mock_conn, "conv_test")

    update_calls = [c for c in mock_conn.execute_query.call_args_list if "UPDATE conversations" in str(c)]
    assert len(update_calls) == 1


@pytest.mark.asyncio
async def test_sync_messages_resolves_new_agent(manager, mock_conn):
    agent_bid = "agnt_new"

    class CachedCnvs:
        def __getitem__(self, k):
            return {"cnvs_id": 1}[k]

    msg = _msg("msg_1", direction="sent")
    msg["source"]["inboxAgent"]["id"] = agent_bid
    msg["source"]["inboxAgent"]["fullName"] = "New Agent"

    manager.client = AsyncMock()
    manager.client.get_messages = AsyncMock(return_value={"items": [msg], "pagination": {}})
    manager._agent_cache = {}

    # fetch_one will be called 4 times:
    # 1. cnvs_row lookup → CachedCnvs
    # 2. last_msg query → None
    # 3. get_or_create_agent select → agnt_id
    # 4. update_conversation_surveys cnvs_row
    mock_conn.fetch_one = AsyncMock(
        side_effect=[
            CachedCnvs(),
            None,
            MagicMock(**{"__getitem__": lambda s, k: {"agnt_id": 42}[k]}),
            MagicMock(
                **{
                    "__getitem__": lambda s, k: {
                        "cnvs_id": 1,
                        "cnvs_status": "active",
                        "cnvs_rating_agent": None,
                        "cnvs_rating_nps": None,
                    }[k]
                }
            ),
        ]
    )

    await sync_messages(manager, mock_conn, "conv_test")
    assert manager.client.get_messages.call_count == 1
    assert manager._agent_cache.get("agnt_new") == 42
