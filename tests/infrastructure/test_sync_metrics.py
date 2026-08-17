"""Unit tests for sync_metrics (idempotent FRT/ART backfill)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from domain import constants
from infrastructure.sync.sync_metrics import METRICS_BACKFILL_SQL, backfill_conversation_metrics


@pytest.fixture
def mock_conn():
    conn = AsyncMock()
    conn.fetch_one = AsyncMock(return_value=MagicMock(**{"__getitem__": lambda s, k: 42 if k == "n" else 0}))
    conn.fetch_all = AsyncMock(return_value=[])
    conn.execute_query = AsyncMock()
    return conn


@pytest.mark.asyncio
async def test_backfill_metrics_updates_both_columns(mock_conn):
    count = await backfill_conversation_metrics(MagicMock(), mock_conn)

    assert mock_conn.execute_query.call_count == 1
    sql = mock_conn.execute_query.call_args.args[0]
    assert "cnvs_frt_minutes" in sql
    assert "cnvs_art_minutes" in sql
    assert "UPDATE conversations" in sql
    assert count == 42


@pytest.mark.asyncio
async def test_backfill_metrics_caps_at_max_art(mock_conn):
    assert f"{constants.MAX_ART_MINUTES}.0" in METRICS_BACKFILL_SQL
    assert "INTERVAL '24 hours'" in METRICS_BACKFILL_SQL


@pytest.mark.asyncio
async def test_backfill_metrics_zero_when_no_rows(mock_conn):
    mock_conn.fetch_one = AsyncMock(return_value=None)
    count = await backfill_conversation_metrics(MagicMock(), mock_conn)
    assert count == 0


@pytest.mark.asyncio
async def test_backfill_metrics_is_idempotent(mock_conn):
    """Re-running issues the exact same statement and yields the same count."""
    first = await backfill_conversation_metrics(MagicMock(), mock_conn)
    second = await backfill_conversation_metrics(MagicMock(), mock_conn)

    sql_first = mock_conn.execute_query.call_args_list[0].args[0]
    sql_second = mock_conn.execute_query.call_args_list[1].args[0]
    assert sql_first == sql_second
    assert first == second
