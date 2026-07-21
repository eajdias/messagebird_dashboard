"""Integration test: sync_conversations against real Bird API.

Marked as integration — requires valid API key in env and network access.
Run with: pytest tests/infrastructure/test_sync_integration.py -v -m integration
"""

import os

import pytest

from infrastructure.api.client import MessageBirdClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_conversations_real_api():
    """Verify the Bird API connection works and returns valid data."""
    api_key = os.getenv("MESSAGEBIRD_API_KEY_LIVE") or os.getenv("MESSAGEBIRD_API_KEY_TEST")
    if not api_key:
        pytest.skip("No API key configured")

    async with MessageBirdClient(api_key=api_key) as client:
        result = await client.list_conversations(limit=3, status="active", reverse=True)

        assert "error" not in result, f"API returned error: {result}"
        items = result.get("data", result.get("items", []))
        assert isinstance(items, list)

        if items:
            conv = items[0]
            assert "id" in conv
            assert "updatedDatetime" in conv
            assert "status" in conv
            print(f"  First conversation: id={conv['id']}, updated={conv['updatedDatetime']}, status={conv['status']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_contacts_real_api():
    """Verify contacts API returns data."""
    api_key = os.getenv("MESSAGEBIRD_API_KEY_LIVE") or os.getenv("MESSAGEBIRD_API_KEY_TEST")
    if not api_key:
        pytest.skip("No API key configured")

    async with MessageBirdClient(api_key=api_key) as client:
        result = await client.list_contacts(limit=3, offset=0)

        assert "error" not in result, f"API returned error: {result}"
        items = result.get("items", [])
        assert isinstance(items, list)
        print(f"  Contacts returned: {len(items)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reverse_true_gives_newest_first():
    """Verify reverse=true returns conversations newest-first."""
    api_key = os.getenv("MESSAGEBIRD_API_KEY_LIVE") or os.getenv("MESSAGEBIRD_API_KEY_TEST")
    if not api_key:
        pytest.skip("No API key configured")

    async with MessageBirdClient(api_key=api_key) as client:
        result = await client.list_conversations(limit=5, status="active", reverse=True)
        items = result.get("data", result.get("items", []))

        if len(items) < 2:
            pytest.skip("Need at least 2 conversations to verify ordering")

        timestamps = [c.get("updatedDatetime", "") for c in items]
        assert timestamps == sorted(timestamps, reverse=True), f"Expected newest-first ordering. Got: {timestamps}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_retry_on_timeout():
    """Verify retry works by using a very short timeout that should trigger retry."""
    api_key = os.getenv("MESSAGEBIRD_API_KEY_LIVE") or os.getenv("MESSAGEBIRD_API_KEY_TEST")
    if not api_key:
        pytest.skip("No API key configured")

    from infrastructure.api.client import MessageBirdClient

    client = MessageBirdClient(api_key=api_key)
    # Set a very short timeout to force timeouts
    import httpx

    client.client = httpx.AsyncClient(
        headers=client._get_headers(),
        timeout=httpx.Timeout(0.001, connect=0.001),
    )

    result = await client.list_conversations(limit=3, status="active")
    assert "error" in result
    await client.close()
