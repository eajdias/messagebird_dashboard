from abc import ABC, abstractmethod
from typing import Any

from domain.entities.report_data import RawConversationData


class ReportRepository(ABC):
    @abstractmethod
    async def fetch_raw_data_range(
        self, start_date: str, end_date: str, agent_group: str | None = None
    ) -> list[RawConversationData]:
        pass

    @abstractmethod
    async def fetch_auditoria_contatos_raw(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def fetch_auditoria_demanda_raw(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def fetch_auditoria_os_raw(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def fetch_auditoria_contatos_data(
        self, start_date: str, end_date: str, agent_group: str | None = None
    ) -> tuple[list[str], list[Any]]:
        pass

    @abstractmethod
    async def fetch_auditoria_os_data(
        self, start_date: str, end_date: str, agent_group: str | None = None
    ) -> tuple[list[str], list[Any]]:
        pass

    @abstractmethod
    async def fetch_auditoria_chats_data(
        self, start_date: str, end_date: str, agent_group: str | None = None
    ) -> tuple[list[str], list[Any]]:
        pass

    @abstractmethod
    async def fetch_auditoria_demanda_data(
        self, start_date: str, end_date: str, agent_group: str | None = None
    ) -> tuple[list[str], list[Any]]:
        pass

    @abstractmethod
    async def fetch_unmapped_counts(self) -> tuple[int, int]:
        pass

    @abstractmethod
    async def fetch_all_groups(self, start_date: str, end_date: str) -> list[str]:
        pass

    @abstractmethod
    async def fetch_raw_data_all(self, agent_group: str | None = None) -> list[RawConversationData]:
        pass

    @abstractmethod
    async def fetch_all_groups_all(self) -> list[str]:
        pass

    @abstractmethod
    async def fetch_auditoria_contatos_raw_all(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def fetch_auditoria_os_raw_all(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def fetch_messages_by_conversation(self, conversation_id: int) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def fetch_messages_for_conversations(self, conversation_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
        pass

    @abstractmethod
    async def list_conversations(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        department: str | None = None,
        agent: str | None = None,
        channel: str | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[dict[str, Any]], int]:
        pass

    @abstractmethod
    async def export_conversations(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        department: str | None = None,
        agent: str | None = None,
        channel: str | None = None,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        art_min_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """Export all conversations matching filters (no pagination)."""
        pass

    @abstractmethod
    async def export_conversations_by_contacts(
        self,
        contact_ids: list[int],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        """Export all conversations for a list of contact IDs in a date range."""
        pass

    @abstractmethod
    async def export_conversation_ids(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        agent: str | None = None,
        channel: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[int]:
        """Export matching conversation IDs (lightweight, no pagination)."""
        pass

    @abstractmethod
    async def fetch_conversation_details(self, conversation_ids: list[int]) -> dict[int, dict[str, Any]]:
        """Batch-fetch conversation details for multiple IDs."""
        pass

    @abstractmethod
    async def get_conversation_detail(self, conversation_id: int) -> dict[str, Any] | None:
        pass

    @abstractmethod
    async def get_bsc_manual_values(
        self, department: str, period_start: str, period_end: str
    ) -> dict[str, dict[str, float]]:
        pass

    @abstractmethod
    async def upsert_bsc_manual_value(
        self,
        department: str,
        agent_name: str,
        metric_name: str,
        period_start: str,
        period_end: str,
        value: float,
    ) -> None:
        pass
