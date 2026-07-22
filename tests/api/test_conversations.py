"""Tests for Conversations API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestListConversations:
    def test_list_success(self, authed_client: TestClient, mock_repo: AsyncMock):
        mock_repo.list_conversations.return_value = (
            [
                {
                    "cnvs_id": 1,
                    "cnts_name": "João Silva",
                    "cnts_phone": "+5511999999999",
                    "cnts_id": 1,
                    "agnt_name": "Ana Santos",
                    "cnvs_dept": 1,
                    "cnvs_channel": "whatsapp",
                    "cnvs_status": "archived",
                    "cnvs_created": "2026-07-01T10:00:00",
                    "cnvs_updated": "2026-07-01T10:30:00",
                    "cnvs_rating_agent": 5,
                    "cnvs_rating_nps": 9,
                    "cnvs_msgcount": 3,
                    "cnvs_reopened_count": 0,
                }
            ],
            1,
        )
        resp = authed_client.get("/api/v1/conversations/")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["total"] == 1
        assert len(body["conversations"]) == 1

    def test_list_empty(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/conversations/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["total"] == 0

    def test_list_unauthorized(self, client: TestClient):
        resp = client.get("/api/v1/conversations/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_with_filters(self, authed_client: TestClient, mock_repo: AsyncMock):
        mock_repo.list_conversations.return_value = ([], 0)
        resp = authed_client.get("/api/v1/conversations/?department=Suporte&status=archived&page=1&per_page=10")
        assert resp.status_code == status.HTTP_200_OK

    def test_list_pagination_out_of_range(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/conversations/?page=0")
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_per_page_too_large(self, authed_client: TestClient):
        resp = authed_client.get("/api/v1/conversations/?per_page=200")
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetConversation:
    def test_get_detail_success(self, authed_client: TestClient, mock_repo: AsyncMock):
        mock_repo.get_conversation_detail.return_value = {
            "cnvs_id": 1,
            "cnts_name": "João Silva",
            "cnts_phone": "+5511999999999",
            "cnts_id": 1,
            "agnt_name": "Ana Santos",
            "cnvs_dept": 1,
            "cnvs_channel": "whatsapp",
            "cnvs_status": "archived",
            "cnvs_created": "2026-07-01T10:00:00",
            "cnvs_updated": "2026-07-01T10:30:00",
            "cnvs_rating_agent": 5,
            "cnvs_rating_nps": 9,
            "cnvs_msgcount": 3,
            "cnvs_reopened_count": 0,
        }
        mock_repo.fetch_messages_by_conversation.return_value = [
            {
                "msgs_direction": "received",
                "msgs_content": "Olá",
                "msgs_created": "2026-07-01T10:00:00",
                "agnt_name": None,
            }
        ]
        resp = authed_client.get("/api/v1/conversations/1")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["id"] == "1"
        assert len(body["messages"]) == 1

    def test_get_detail_not_found(self, authed_client: TestClient, mock_repo: AsyncMock):
        mock_repo.get_conversation_detail.return_value = None
        resp = authed_client.get("/api/v1/conversations/999")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestGetConversationMessages:
    def test_get_messages_success(self, authed_client: TestClient, mock_repo: AsyncMock):
        mock_repo.fetch_messages_by_conversation.return_value = [
            {
                "msgs_direction": "received",
                "msgs_content": "Olá",
                "msgs_created": "2026-07-01T10:00:00",
                "agnt_name": None,
            },
            {
                "msgs_direction": "sent",
                "msgs_content": "Como posso ajudar?",
                "msgs_created": "2026-07-01T10:01:00",
                "agnt_name": "Ana Santos",
            },
        ]
        resp = authed_client.get("/api/v1/conversations/1/messages")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["total"] == 2
        assert len(body["messages"]) == 2

    def test_get_messages_empty(self, authed_client: TestClient, mock_repo: AsyncMock):
        mock_repo.fetch_messages_by_conversation.return_value = []
        resp = authed_client.get("/api/v1/conversations/1/messages")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["total"] == 0

    def test_get_messages_unauthorized(self, client: TestClient):
        resp = client.get("/api/v1/conversations/1/messages")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
