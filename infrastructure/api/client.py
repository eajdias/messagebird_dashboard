import json
import logging

import httpx

from .config import (
    HTTP_TIMEOUT,
    get_api_key,
    get_base_url_bird,
    get_base_url_contacts,
    get_base_url_conversations,
    get_workspace_id,
)

logger = logging.getLogger("standalone.client")


class MessageBirdClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or get_api_key()
        self.workspace_id = get_workspace_id()
        self.base_url_conv = get_base_url_conversations()
        self.base_url_contacts = get_base_url_contacts()
        self.base_url_bird = get_base_url_bird()
        self.client = httpx.AsyncClient(headers=self._get_headers(), timeout=HTTP_TIMEOUT)

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
        self, method: str, url: str, params: dict[str, object] | None = None, json_data: dict[str, object] | None = None
    ) -> dict[str, object]:
        try:
            logger.debug(f"Making {method} request to {url}")
            response = await self.client.request(method, url, params=params, json=json_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error: {e}")
            logger.error(f"Response: {e.response.text}")
            return {"error": str(e), "details": e.response.text}
        except json.JSONDecodeError:
            logger.error("Response is not JSON")
            return {"error": "Invalid JSON response"}
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"error": str(e)}

    async def list_conversations(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str = "active",
        page_token: str | None = None,
        createdDatetimeAfter: str | None = None,
        createdDatetimeBefore: str | None = None,
        updatedDatetimeAfter: str | None = None,
    ):
        url = f"{self.base_url_conv}/conversations"
        params: dict[str, object] = {"limit": limit, "offset": offset, "status": status}
        if page_token:
            params["pageToken"] = page_token
        if createdDatetimeAfter:
            params["createdDatetimeAfter"] = createdDatetimeAfter
        if createdDatetimeBefore:
            params["createdDatetimeBefore"] = createdDatetimeBefore
        if updatedDatetimeAfter:
            params["updatedDatetimeAfter"] = updatedDatetimeAfter
        return await self._make_request("GET", url, params)

    async def get_messages(self, conversation_id: str, limit: int = 20, offset: int = 0, date_from: str | None = None):
        url = f"{self.base_url_conv}/conversations/{conversation_id}/messages"
        params: dict[str, object] = {"limit": limit, "offset": offset}
        if date_from:
            params["dateFrom"] = date_from
        return await self._make_request("GET", url, params)

    async def list_contacts(self, limit: int = 20, offset: int = 0):
        url = f"{self.base_url_contacts}/contacts"
        params: dict[str, object] = {"limit": limit, "offset": offset}
        return await self._make_request("GET", url, params)
