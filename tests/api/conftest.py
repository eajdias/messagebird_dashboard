"""Shared fixtures for API integration tests."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.auth import create_access_token, get_password_hash
from api.dependencies import get_repository
from api.main import create_app
from application.interfaces.repository import ReportRepository

_TEST_USER = {
    "id": 1,
    "email": "admin@empresa.com",
    "password_hash": get_password_hash("admin123"),
    "role": "admin",
    "name": "Admin",
    "active": True,
}


@pytest.fixture(autouse=True)
def _patch_db(monkeypatch: pytest.MonkeyPatch):
    """Prevent the app from connecting to PostgreSQL during tests."""

    async def _fake_pool():
        pool = AsyncMock()

        async def _fetch_one(query: str, *args):
            if "FROM users WHERE email" in query:
                for arg in args:
                    if arg == _TEST_USER["email"]:
                        return dict(_TEST_USER)
                return None
            return None

        async def _fetch_all(query: str, *args):
            return []

        async def _execute(query: str, *args):
            return None

        pool.fetch_one = AsyncMock(side_effect=_fetch_one)
        pool.fetch_all = AsyncMock(side_effect=_fetch_all)
        pool.execute = AsyncMock(side_effect=_execute)
        return pool

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
