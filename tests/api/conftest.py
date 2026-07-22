"""Shared fixtures for API integration tests."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.auth import create_access_token
from api.dependencies import get_pool, get_repository
from api.main import create_app
from application.interfaces.repository import ReportRepository


@pytest.fixture(autouse=True)
def _patch_db(monkeypatch: pytest.MonkeyPatch):
    """Prevent the app from connecting to PostgreSQL during tests."""

    async def _fake_pool():
        return AsyncMock()

    monkeypatch.setattr("api.dependencies.get_pool", _fake_pool)
    monkeypatch.setattr("api.dependencies._pool", None, raising=False)
    monkeypatch.setenv("SYNC_ENABLED", "false")
    monkeypatch.setenv("JWT_SECRET", "test-secret")

    # Prevent APScheduler shutdown errors during lifespan teardown
    monkeypatch.setattr("api.main.scheduler.shutdown", lambda wait=False: None)


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
def mock_repo() -> AsyncMock:
    repo = AsyncMock(spec=ReportRepository)
    repo.fetch_raw_data_range = AsyncMock(return_value=[])
    repo.list_conversations = AsyncMock(return_value=([], 0))
    repo.get_conversation_detail = AsyncMock(return_value=None)
    repo.fetch_messages_by_conversation = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def client(app: FastAPI, mock_repo: AsyncMock) -> TestClient:
    app.dependency_overrides[get_repository] = lambda: mock_repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    token = create_access_token({"sub": "admin@test.com", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def authed_client(app: FastAPI, mock_repo: AsyncMock, auth_headers: dict[str, str]) -> TestClient:
    app.dependency_overrides[get_repository] = lambda: mock_repo
    with TestClient(app) as c:
        c.headers.update(auth_headers)
        yield c
    app.dependency_overrides.clear()
