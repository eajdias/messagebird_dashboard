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
    async def get_conversation_detail(self, conversation_id: int) -> dict[str, Any] | None:
        pass
