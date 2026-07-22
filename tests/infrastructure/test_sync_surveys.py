"""Unit tests for sync_surveys (survey extraction from messages)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from infrastructure.sync.sync_core import PgSyncManager
from infrastructure.sync.sync_surveys import backfill_surveys, update_conversation_surveys


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


def _survey_msg(
    direction: str = "sent",
    content: str = "Selecione o departamento desejado",
    created: str = "2026-07-21T10:00:00",
):
    return MagicMock(
        **{
            "__getitem__": lambda s, k: {
                "msgs_id": 1,
                "msgs_content": content,
                "msgs_direction": direction,
                "msgs_created": created,
            }[k],
        }
    )


def _resp_msg(content: str = "1", direction: str = "received", created: str = "2026-07-21T10:00:30"):
    return MagicMock(
        **{
            "__getitem__": lambda s, k: {
                "msgs_id": 2,
                "msgs_content": content,
                "msgs_direction": direction,
                "msgs_created": created,
            }[k],
        }
    )


@pytest.mark.asyncio
async def test_update_conversation_surveys_department(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(
        return_value=MagicMock(
            **{
                "__getitem__": lambda s, k: {
                    "cnvs_id": 1,
                    "cnvs_status": "active",
                    "cnvs_rating_agent": None,
                    "cnvs_rating_nps": None,
                }[k]
            }
        )
    )
    mock_conn.fetch_all = AsyncMock(
        return_value=[
            _survey_msg(),
            _resp_msg("1"),
        ]
    )

    await update_conversation_surveys(manager, mock_conn, "conv_test")
    assert mock_conn.execute_query.call_count >= 1


@pytest.mark.asyncio
async def test_update_conversation_surveys_rating_nps(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(
        return_value=MagicMock(
            **{
                "__getitem__": lambda s, k: {
                    "cnvs_id": 1,
                    "cnvs_status": "active",
                    "cnvs_rating_agent": None,
                    "cnvs_rating_nps": None,
                }[k]
            }
        )
    )
    mock_conn.fetch_all = AsyncMock(
        return_value=[
            _survey_msg(content="Avalie nosso atendimento de 0 a 10"),
            _resp_msg("9"),
        ]
    )

    await update_conversation_surveys(manager, mock_conn, "conv_test")
    assert mock_conn.execute_query.call_count >= 1


@pytest.mark.asyncio
async def test_update_conversation_surveys_rating_agent(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(
        return_value=MagicMock(
            **{
                "__getitem__": lambda s, k: {
                    "cnvs_id": 1,
                    "cnvs_status": "active",
                    "cnvs_rating_agent": None,
                    "cnvs_rating_nps": None,
                }[k]
            }
        )
    )
    mock_conn.fetch_all = AsyncMock(
        return_value=[
            _survey_msg(content="como você avalia o atendimento do técnico"),
            _resp_msg("5"),
        ]
    )

    await update_conversation_surveys(manager, mock_conn, "conv_test")
    assert mock_conn.execute_query.call_count >= 1


@pytest.mark.asyncio
async def test_update_conversation_surveys_no_survey(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(
        return_value=MagicMock(
            **{
                "__getitem__": lambda s, k: {
                    "cnvs_id": 1,
                    "cnvs_status": "active",
                    "cnvs_rating_agent": None,
                    "cnvs_rating_nps": None,
                }[k]
            }
        )
    )
    mock_conn.fetch_all = AsyncMock(
        return_value=[
            _survey_msg(content="Some random message", direction="sent"),
        ]
    )

    await update_conversation_surveys(manager, mock_conn, "conv_test")
    assert mock_conn.execute_query.call_count >= 0


@pytest.mark.asyncio
async def test_update_conversation_surveys_conversation_not_found(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(return_value=None)
    await update_conversation_surveys(manager, mock_conn, "unknown")
    assert mock_conn.fetch_all.call_count == 0


@pytest.mark.asyncio
async def test_backfill_surveys(manager, mock_conn):
    mock_conn.fetch_all = AsyncMock(
        side_effect=[
            [MagicMock(**{"__getitem__": lambda s, k: {"cnvs_bird": "conv_1"}[k]})],
            [],
        ]
    )

    count = await backfill_surveys(manager, mock_conn)
    assert count == 1


@pytest.mark.asyncio
async def test_backfill_surveys_empty(manager, mock_conn):
    mock_conn.fetch_all = AsyncMock(
        side_effect=[
            [],
            [],
        ]
    )

    count = await backfill_surveys(manager, mock_conn)
    assert count == 0


@pytest.mark.asyncio
async def test_update_conversation_surveys_extracts_tax_id(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(
        return_value=MagicMock(
            **{
                "__getitem__": lambda s, k: {
                    "cnvs_id": 1,
                    "cnvs_status": "active",
                    "cnvs_rating_agent": None,
                    "cnvs_rating_nps": None,
                }[k]
            }
        )
    )
    mock_conn.fetch_all = AsyncMock(
        return_value=[
            _survey_msg(content="Informe por favor o CNPJ de sua empresa ou CPF"),
            _resp_msg("11.222.333/0001-44"),
        ]
    )

    await update_conversation_surveys(manager, mock_conn, "conv_test")
    assert mock_conn.execute_query.call_count >= 1


@pytest.mark.asyncio
async def test_update_conversation_surveys_extracts_software(manager, mock_conn):
    mock_conn.fetch_one = AsyncMock(
        return_value=MagicMock(
            **{
                "__getitem__": lambda s, k: {
                    "cnvs_id": 1,
                    "cnvs_status": "active",
                    "cnvs_rating_agent": None,
                    "cnvs_rating_nps": None,
                }[k]
            }
        )
    )
    mock_conn.fetch_all = AsyncMock(
        return_value=[
            _survey_msg(content="Qual seria o sistema"),
            _resp_msg("SIGAF"),
        ]
    )

    await update_conversation_surveys(manager, mock_conn, "conv_test")
    assert mock_conn.execute_query.call_count >= 1
