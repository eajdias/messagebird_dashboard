import asyncio
import json
import logging
from typing import Any

import httpx

from .config import (
    HTTP_TIMEOUT,
    get_api_key,
    get_base_url_bird,
    get_base_url_contacts,
    get_base_url_conversations,
    get_workspace_id,
)

logger = logging.getLogger("m_bird.api_client")

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0


class MessageBirdClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or get_api_key()
        self.workspace_id = get_workspace_id()
        self.base_url_conv = get_base_url_conversations()
        self.base_url_contacts = get_base_url_contacts()
        self.base_url_bird = get_base_url_bird()
        self.client = httpx.AsyncClient(
            headers=self._get_headers(),
            timeout=HTTP_TIMEOUT,
        )

    def _get_headers(self):
        return {
            "Authorization": f"AccessKey {self.api_key}",
            "Content-Type": "application/json",
        }

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _make_request(
        self, method: str, url: str, params: dict[str, Any] | None = None, json_data: dict[str, Any] | None = None
    ) -> Any:
        last_exc: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await self.client.request(method, url, params=params, json=json_data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES:
                    delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(f"HTTP {status} on attempt {attempt}/{MAX_RETRIES}, retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    continue
                logger.error(f"HTTP Error {status}: {e.response.text[:500]}")
                return {"error": f"HTTP {status}", "details": e.response.text[:500]}
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exc = e
                if attempt < MAX_RETRIES:
                    delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        "Network error on attempt %d/%d: %s, retrying in %.1fs...",
                        attempt,
                        MAX_RETRIES,
                        type(e).__name__,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                msg = str(e) or f"{type(e).__name__}: {e!r}"
                logger.error(f"Request failed after {MAX_RETRIES} attempts: {msg}")
                return {"error": msg}
            except json.JSONDecodeError:
                logger.error("Response is not JSON")
                return {"error": "Invalid JSON response"}
            except Exception as e:
                msg = str(e) or f"{type(e).__name__}: {e!r}"
                logger.error(f"Request failed: {msg}")
                return {"error": msg}
        return {"error": f"Request failed after {MAX_RETRIES} attempts: {last_exc}"}

    async def list_conversations(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str = "active",
        page_token: str | None = None,
        reverse: bool = False,
        created_datetime_after: str | None = None,
        created_datetime_before: str | None = None,
    ):
        url = f"{self.base_url_conv}/conversations"
        params: dict[str, Any] = {"limit": limit, "offset": offset, "status": status}
        if reverse:
            params["reverse"] = "true"
        if page_token:
            params["pageToken"] = page_token
        if created_datetime_after:
            params["createdDatetimeAfter"] = created_datetime_after
        if created_datetime_before:
            params["createdDatetimeBefore"] = created_datetime_before
        return await self._make_request("GET", url, params)

    async def get_messages(self, conversation_id: str, limit: int = 20, offset: int = 0, date_from: str | None = None):
        url = f"{self.base_url_conv}/conversations/{conversation_id}/messages"
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if date_from:
            params["dateFrom"] = date_from
        return await self._make_request("GET", url, params)

    async def list_contacts(self, limit: int = 20, offset: int = 0):
        url = f"{self.base_url_contacts}/contacts"
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        return await self._make_request("GET", url, params)
