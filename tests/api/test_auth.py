"""Tests for Auth API endpoints."""

from __future__ import annotations

from fastapi import status
from fastapi.testclient import TestClient


class TestAuthLogin:
    def test_login_success(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@empresa.com", "password": "admin123"},
        )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@empresa.com", "password": "wrong"},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_empty_email(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "", "password": "admin123"},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthRegister:
    def test_register_success(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "novo@empresa.com", "password": "nova123", "name": "Novo"},
        )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_register_invalid_email(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "invalido", "password": "senha123", "name": "Test"},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthRefresh:
    def test_refresh_success(self, authed_client: TestClient):
        resp = authed_client.post("/api/v1/auth/refresh")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_refresh_unauthorized(self, client: TestClient):
        resp = client.post("/api/v1/auth/refresh")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_invalid_token(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthMe:
    def test_get_me_success(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/auth/me")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["email"] == "admin@test.com"
        assert body["role"] == "admin"

    def test_get_me_unauthorized(self, client: TestClient):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_me_invalid_token(self, client: TestClient):
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
