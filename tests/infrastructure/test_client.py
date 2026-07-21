"""Unit tests for MessageBirdClient with mocked HTTP responses."""

import httpx
import pytest
import respx

from infrastructure.api.client import MessageBirdClient, MAX_RETRIES


@pytest.fixture
def client():
    return MessageBirdClient(api_key="test_key_123")


@pytest.fixture
def conv_url():
    return "https://conversations.messagebird.com/v1/conversations"


@pytest.fixture
def contacts_url():
    return "https://contacts.messagebird.com/v2/contacts"


# ── list_conversations ──────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_list_conversations_basic(client, conv_url):
    respx.get(conv_url).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [{"id": "conv_1", "status": "active", "updatedDatetime": "2026-07-21T12:00:00Z"}],
                "pagination": {"totalCount": 1},
            },
        )
    )
    result = await client.list_conversations(limit=10, offset=0, status="active")
    assert "items" in result
    assert len(result["items"]) == 1
    assert result["items"][0]["id"] == "conv_1"


@pytest.mark.asyncio
@respx.mock
async def test_list_conversations_reverse_param(client, conv_url):
    route = respx.get(conv_url).mock(
        return_value=httpx.Response(200, json={"items": [], "pagination": {"totalCount": 0}})
    )
    await client.list_conversations(limit=10, status="active", reverse=True)
    request = route.calls[0].request
    assert request.url.params.get("reverse") == "true"


@pytest.mark.asyncio
@respx.mock
async def test_list_conversations_no_updatedDatetimeAfter(client, conv_url):
    """Verify updatedDatetimeAfter is NOT sent (Bird API ignores it)."""
    route = respx.get(conv_url).mock(
        return_value=httpx.Response(200, json={"items": [], "pagination": {"totalCount": 0}})
    )
    await client.list_conversations(limit=10, status="active")
    request = route.calls[0].request
    assert "updatedDatetimeAfter" not in str(request.url)


@pytest.mark.asyncio
@respx.mock
async def test_list_conversations_createdDatetimeBefore(client, conv_url):
    route = respx.get(conv_url).mock(
        return_value=httpx.Response(200, json={"items": [], "pagination": {"totalCount": 0}})
    )
    await client.list_conversations(limit=10, status="active", createdDatetimeBefore="2026-07-21T12:00:00Z")
    request = route.calls[0].request
    assert request.url.params.get("createdDatetimeBefore") == "2026-07-21T12:00:00Z"


@pytest.mark.asyncio
@respx.mock
async def test_list_conversations_page_token(client, conv_url):
    route = respx.get(conv_url).mock(
        return_value=httpx.Response(200, json={"items": [], "pagination": {"totalCount": 0}})
    )
    await client.list_conversations(limit=10, status="active", page_token="tok_abc123")
    request = route.calls[0].request
    assert request.url.params.get("pageToken") == "tok_abc123"


# ── Retry logic ─────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_retry_on_500(client, conv_url):
    """500 errors should be retried up to MAX_RETRIES."""
    route = respx.get(conv_url).mock(
        side_effect=[
            httpx.Response(500, text="Internal Server Error"),
            httpx.Response(200, json={"items": [{"id": "conv_1"}], "pagination": {}}),
        ]
    )
    result = await client.list_conversations(limit=10, status="active")
    assert route.call_count == 2
    assert result["items"][0]["id"] == "conv_1"


@pytest.mark.asyncio
@respx.mock
async def test_retry_on_timeout(client, conv_url):
    """Timeout errors should be retried."""
    route = respx.get(conv_url).mock(
        side_effect=[
            httpx.TimeoutException("read timeout"),
            httpx.Response(200, json={"items": [{"id": "conv_retry"}], "pagination": {}}),
        ]
    )
    result = await client.list_conversations(limit=10, status="active")
    assert route.call_count == 2
    assert result["items"][0]["id"] == "conv_retry"


@pytest.mark.asyncio
@respx.mock
async def test_no_retry_on_400(client, conv_url):
    """400 errors should NOT be retried (client error)."""
    respx.get(conv_url).mock(return_value=httpx.Response(400, text="Bad Request"))
    result = await client.list_conversations(limit=10, status="active")
    assert "error" in result
    assert "400" in result["error"]


@pytest.mark.asyncio
@respx.mock
async def test_retry_exhaustion(client, conv_url):
    """After MAX_RETRIES failures, return error dict."""
    respx.get(conv_url).mock(side_effect=httpx.TimeoutException("timeout"))
    result = await client.list_conversations(limit=10, status="active")
    assert "error" in result
    assert "timeout" in result["error"].lower() or "TimeoutException" in result["error"]


# ── list_contacts ───────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_list_contacts(client, contacts_url):
    respx.get(contacts_url).mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": "cnt_1", "displayName": "Test"}], "pagination": {"totalCount": 1}}
        )
    )
    result = await client.list_contacts(limit=10, offset=0)
    assert len(result["items"]) == 1
    assert result["items"][0]["displayName"] == "Test"


# ── get_messages ────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_get_messages(client):
    url = "https://conversations.messagebird.com/v1/conversations/conv_1/messages"
    respx.get(url).mock(
        return_value=httpx.Response(200, json={"items": [{"id": "msg_1", "direction": "sent"}], "pagination": {}})
    )
    result = await client.get_messages("conv_1", limit=10, offset=0)
    assert len(result["items"]) == 1
    assert result["items"][0]["direction"] == "sent"
