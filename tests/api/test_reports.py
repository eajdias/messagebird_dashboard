"""Tests for Reports API endpoints."""

from __future__ import annotations

from fastapi import status
from fastapi.testclient import TestClient


class TestGenerateReport:
    def test_generate_success(self, authed_client: TestClient):
        resp = authed_client.post(
            "/api/v1/reports/generate",
            json={"type": "monthly", "year": 2026, "month": 7},
        )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["status"] == "processing"
        assert body["report_id"] == "pending"

    def test_generate_annual(self, authed_client: TestClient):
        resp = authed_client.post(
            "/api/v1/reports/generate",
            json={"type": "annual", "year": 2026},
        )
        assert resp.status_code == status.HTTP_200_OK

    def test_generate_invalid_type(self, authed_client: TestClient):
        resp = authed_client.post(
            "/api/v1/reports/generate",
            json={"type": "invalid", "year": 2026},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_missing_year(self, authed_client: TestClient):
        resp = authed_client.post(
            "/api/v1/reports/generate",
            json={"type": "monthly", "month": 7},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_unauthorized(self, client: TestClient):
        resp = client.post(
            "/api/v1/reports/generate",
            json={"type": "monthly", "year": 2026, "month": 7},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestDownloadReport:
    def test_download_success(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/reports/abc123/download")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "download_url" in body
        assert "abc123" in body["download_url"]

    def test_download_unauthorized(self, client: TestClient):
        resp = client.get("/api/v1/reports/abc123/download")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestAvailableReports:
    def test_available_success(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/reports/available")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "reports" in body

    def test_available_unauthorized(self, client: TestClient):
        resp = client.get("/api/v1/reports/available")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
