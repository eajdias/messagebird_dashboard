"""Tests for Dashboard API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock

from fastapi import status
from fastapi.testclient import TestClient

from domain.entities.report_data import RawConversationData


def _make_raw(contact_id: int = 1, nps: int = 9, rating: int = 5, channel: str = "WhatsApp") -> RawConversationData:
    return RawConversationData(
        id=f"conv_{contact_id}",
        contact=f"Contact {contact_id}",
        phone=f"+55119{contact_id:08d}",
        contact_id=contact_id,
        nps=nps,
        rating=rating,
        start_time="2026-07-01T10:00:00",
        end_time="2026-07-01T10:30:00",
        metadata={"channel": channel, "channel_name": channel, "agent_name": "Ana Santos"},
    )


class TestDashboardSummary:
    def test_summary_success(self, authed_client: TestClient, mock_repo: AsyncMock):
        mock_repo.fetch_raw_data_range.return_value = [_make_raw()]
        resp = authed_client.get("/api/v1/dashboard/summary")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["total_conversations"] == 1
        assert body["nps_score"] == 100.0

    def test_summary_empty(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/dashboard/summary")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["total_conversations"] == 0

    def test_summary_unauthorized(self, client: TestClient):
        resp = client.get("/api/v1/dashboard/summary")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_summary_with_date_range(self, authed_client: TestClient, mock_repo: AsyncMock):
        mock_repo.fetch_raw_data_range.return_value = [_make_raw(contact_id=2, nps=7)]
        resp = authed_client.get("/api/v1/dashboard/summary?start_date=2026-07-01&end_date=2026-07-31")
        assert resp.status_code == 200
        assert resp.json()["nps_score"] == 0.0


class TestDashboardBSC:
    def test_bsc_success(self, authed_client: TestClient, mock_repo: AsyncMock):
        mock_repo.fetch_raw_data_range.return_value = [_make_raw()]
        resp = authed_client.get("/api/v1/dashboard/bsc")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "header" in body

    def test_bsc_empty(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/dashboard/bsc")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["header"] == ["Métrica"]


class TestDashboardKPIs:
    def test_kpis_success(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/dashboard/kpis")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "kpis" in body

    def test_kpis_with_department(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/dashboard/kpis?department=Suporte")
        assert resp.status_code == status.HTTP_200_OK

    def test_kpis_no_auth(self, client: TestClient):
        resp = client.get("/api/v1/dashboard/kpis")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestDashboardEvolution:
    def test_evolution_success(self, authed_client: TestClient, mock_repo: AsyncMock):
        mock_repo.fetch_raw_data_range.return_value = [_make_raw()]
        resp = authed_client.get("/api/v1/dashboard/evolution?months=3")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "evolution" in body
        assert len(body["evolution"]) == 3

    def test_evolution_invalid_months(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/dashboard/evolution?months=0")
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_evolution_too_many_months(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/dashboard/evolution?months=25")
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDashboardAgents:
    def test_agents_ranking_success(self, authed_client: TestClient, mock_repo: AsyncMock):
        mock_repo.fetch_raw_data_range.return_value = [_make_raw()]
        resp = authed_client.get("/api/v1/dashboard/agents")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "agents" in body
        assert len(body["agents"]) == 1

    def test_agents_ranking_multiple(self, authed_client: TestClient, mock_repo: AsyncMock):
        mock_repo.fetch_raw_data_range.return_value = [
            _make_raw(),
            RawConversationData(
                id="conv_2",
                contact="Contact 2",
                phone="+5511987654321",
                contact_id=2,
                nps=8,
                rating=4,
                start_time="2026-07-02T10:00:00",
                end_time="2026-07-02T10:15:00",
                metadata={
                    "channel": "Messenger",
                    "channel_name": "Messenger",
                    "agent_name": "Carlos Lima",
                },
            ),
        ]
        resp = authed_client.get("/api/v1/dashboard/agents")
        assert resp.status_code == 200
        assert len(resp.json()["agents"]) == 2


class TestDashboardChannels:
    def test_channels_success(self, authed_client: TestClient, mock_repo: AsyncMock):
        mock_repo.fetch_raw_data_range.return_value = [_make_raw()]
        resp = authed_client.get("/api/v1/dashboard/channels")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "channels" in body

    def test_channels_multiple(self, authed_client: TestClient, mock_repo: AsyncMock):
        mock_repo.fetch_raw_data_range.return_value = [
            _make_raw(contact_id=1, channel="WhatsApp"),
            _make_raw(contact_id=2, channel="Messenger"),
        ]
        resp = authed_client.get("/api/v1/dashboard/channels")
        assert resp.status_code == 200
        assert len(resp.json()["channels"]) == 2
