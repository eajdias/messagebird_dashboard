"""Tests for Admin API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock

from fastapi import status
from fastapi.testclient import TestClient


class TestHealthCheck:
    def test_health_success(self, client: TestClient):
        resp = client.get("/api/v1/admin/health")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["status"] == "healthy"
        assert body["version"] == "2.0.0"


class TestSyncStatus:
    def test_sync_status_success(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/admin/sync/status")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "last_sync" in body

    def test_sync_status_unauthorized(self, client: TestClient):
        resp = client.get("/api/v1/admin/sync/status")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestSyncTrigger:
    def test_trigger_full_sync(self, authed_client: TestClient, monkeypatch):
        mock_use_case = AsyncMock()
        monkeypatch.setattr(
            "application.use_cases.sync_database.SyncDatabaseUseCase",
            lambda: mock_use_case,
        )
        monkeypatch.setattr("api.sync_utils.refresh_materialized_view", AsyncMock())

        resp = authed_client.post(
            "/api/v1/admin/sync/trigger",
            json={"full_sync": True, "sync_messages": True},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["status"] == "completed"

    def test_trigger_incremental(self, authed_client: TestClient, monkeypatch):
        mock_use_case = AsyncMock()
        monkeypatch.setattr(
            "application.use_cases.sync_database.SyncDatabaseUseCase",
            lambda: mock_use_case,
        )
        monkeypatch.setattr("api.sync_utils.refresh_materialized_view", AsyncMock())

        resp = authed_client.post(
            "/api/v1/admin/sync/trigger",
            json={"full_sync": False},
        )
        assert resp.status_code == status.HTTP_200_OK

    def test_trigger_unauthorized(self, client: TestClient):
        resp = client.post(
            "/api/v1/admin/sync/trigger",
            json={"full_sync": True},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestListAgents:
    def test_list_agents_has_items(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/admin/agents")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "agents" in body

    def test_list_agents_structure(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/admin/agents")
        assert resp.status_code == 200
        agents = resp.json()["agents"]
        if agents:
            assert "bird_id" in agents[0]
            assert "name" in agents[0]


class TestListDepartments:
    def test_list_departments_success(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/admin/departments")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "departments" in body

    def test_list_departments_unauthorized(self, client: TestClient):
        resp = client.get("/api/v1/admin/departments")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestSyncProfile:
    def test_sync_profile_success(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/admin/sync/profile")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "active_profile" in body
        assert "available_profiles" in body
