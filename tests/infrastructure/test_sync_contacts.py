"""Unit tests for sync_contacts."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from infrastructure.sync.sync_core import PgSyncManager
from infrastructure.sync.sync_contacts import sync_contacts


@pytest.fixture
def manager():
    m = PgSyncManager()
    m._contact_cache = {}
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


def _contact(id_str: str, name: str = "Test", phone: str = "+5511999999999"):
    return {
        "id": id_str,
        "displayName": name,
        "phone": phone,
        "msisdn": phone,
        "createdAt": "2026-07-21T10:00:00Z",
        "updatedAt": "2026-07-21T12:00:00Z",
    }


@pytest.mark.asyncio
async def test_sync_contacts_basic(manager, mock_conn):
    manager.client = AsyncMock()
    manager.client.list_contacts = AsyncMock(
        return_value={
            "items": [_contact("cnt_1"), _contact("cnt_2")],
            "pagination": {"totalCount": 2},
        }
    )
    mock_conn.fetch_all = AsyncMock(
        return_value=[
            MagicMock(**{"__getitem__": lambda self, k: {"cnts_id": 1, "cnts_bird": "cnt_1"}[k]}),
            MagicMock(**{"__getitem__": lambda self, k: {"cnts_id": 2, "cnts_bird": "cnt_2"}[k]}),
        ]
    )

    await sync_contacts(manager, mock_conn)

    assert mock_conn.execute_many.call_count == 1
    batch = mock_conn.execute_many.call_args[0][1]
    assert len(batch) == 2


@pytest.mark.asyncio
async def test_sync_contacts_empty(manager, mock_conn):
    manager.client = AsyncMock()
    manager.client.list_contacts = AsyncMock(return_value={"items": [], "pagination": {"totalCount": 0}})

    await sync_contacts(manager, mock_conn)

    assert mock_conn.execute_many.call_count == 0


@pytest.mark.asyncio
async def test_sync_contacts_pagination(manager, mock_conn):
    manager.client = AsyncMock()
    page1 = {"items": [_contact(f"cnt_{i}") for i in range(20)], "pagination": {"totalCount": 25}}
    page2 = {"items": [_contact(f"cnt_{i}") for i in range(20, 25)], "pagination": {"totalCount": 25}}
    page3 = {"items": [], "pagination": {"totalCount": 25}}
    manager.client.list_contacts = AsyncMock(side_effect=[page1, page2, page3])

    await sync_contacts(manager, mock_conn)
    assert manager.client.list_contacts.call_count >= 2


@pytest.mark.asyncio
async def test_sync_contacts_updates_cache(manager, mock_conn):
    manager.client = AsyncMock()
    manager.client.list_contacts = AsyncMock(
        return_value={
            "items": [_contact("cnt_new", name="New Contact")],
            "pagination": {"totalCount": 1},
        }
    )
    mock_conn.fetch_all = AsyncMock(
        return_value=[
            MagicMock(**{"__getitem__": lambda self, k: {"cnts_id": 99, "cnts_bird": "cnt_new"}[k]}),
        ]
    )

    await sync_contacts(manager, mock_conn)
    assert manager._contact_cache.get("cnt_new") == 99


@pytest.mark.asyncio
async def test_sync_contacts_api_error(manager, mock_conn):
    manager.client = AsyncMock()
    manager.client.list_contacts = AsyncMock(return_value={"error": "timeout"})

    await sync_contacts(manager, mock_conn)
    assert mock_conn.execute_many.call_count == 0


@pytest.mark.asyncio
async def test_sync_contacts_logs_error(manager, mock_conn):
    manager.client = AsyncMock()
    manager.client.list_contacts = AsyncMock(return_value={"error": "timeout"})

    await sync_contacts(manager, mock_conn)
    assert mock_conn.execute_query.call_count >= 1


@pytest.mark.asyncio
async def test_sync_contacts_empty_phone_fallback(manager, mock_conn):
    contact = _contact("cnt_1", name="No Phone")
    contact["phone"] = None
    contact["msisdn"] = None

    manager.client = AsyncMock()
    page = {"items": [contact], "pagination": {"totalCount": 1}}
    empty = {"items": [], "pagination": {"totalCount": 1}}
    manager.client.list_contacts = AsyncMock(side_effect=[page, empty])

    await sync_contacts(manager, mock_conn)
    assert mock_conn.execute_many.call_count == 1
    batch = mock_conn.execute_many.call_args[0][1]
    assert batch[0][1] is None
