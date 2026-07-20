from collections import defaultdict
from datetime import datetime
from typing import Any

from application.interfaces.repository import ReportRepository
from domain import constants, logic
from domain.entities.report_data import RawConversationData, RawMessageData
from infrastructure.database import queries_pg
from infrastructure.database.postgres_connection import PostgresPool


def _parse_dt(value: str | datetime | None) -> datetime | None:
    """Convert a date/time string to a naive datetime for asyncpg parameters."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    value = str(value).strip()
    if not value:
        return None
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(value).replace(tzinfo=None)


def _utc_range(start_date: str, end_date: str) -> tuple[datetime, datetime]:
    """Get UTC datetime range from date strings (parsed for asyncpg)."""
    s, e = logic.get_utc_range(start_date, end_date)
    return _parse_dt(s), _parse_dt(e)  # type: ignore[return-value]


class PostgresReportRepository(ReportRepository):
    def __init__(self, pool: PostgresPool):
        self._pool = pool

    async def fetch_raw_data_range(
        self, start_date: str, end_date: str, agent_group: str = None
    ) -> list[RawConversationData]:
        s, e = _utc_range(start_date, end_date)
        rows = await self._pool.fetch_all(
            queries_pg.SURVEY_DATA_METADATA_QUERY,
            s,
            e,
            s,
            e,
        )

        conversations: dict[str, RawConversationData] = {}

        for r in rows:
            cid = str(r["cnvs_id"])
            conv_agnt_name = r["conversation_agent_name"] or "Desconhecido"
            msg_agnt_name = r["message_agent_name"] or ""

            if agent_group:
                conv_dept_label = constants.resolve_dept(r["cnvs_dept"])
                if constants.resolve_conversation_group(conv_agnt_name, conv_dept_label) != agent_group:
                    continue

            if cid not in conversations:
                raw_msgs = [
                    RawMessageData(
                        str(r["msgs_created"] or ""), r["msgs_direction"] or "", r["msgs_agnt"], msg_agnt_name
                    )
                ]
                conversations[cid] = RawConversationData(
                    id=cid,
                    contact=r["cnts_name"] or "Unknown",
                    phone=r["cnts_phone"] or "",
                    contact_id=r["cnts_id"] or 0,
                    start_time=logic.format_local_dt(str(r["cnvs_created"])),
                    end_time=logic.format_local_dt(str(r["cnvs_updated"])),
                    queue_time=logic.get_effective_start_time(raw_msgs, str(r["cnvs_created"])),
                    raw_created=str(r["cnvs_created"] or ""),
                    raw_updated=str(r["cnvs_updated"] or ""),
                    msgs=raw_msgs,
                    rating=float(r["cnvs_rating_agent"]) if r["cnvs_rating_agent"] is not None else None,
                    nps=float(r["cnvs_rating_nps"]) if r["cnvs_rating_nps"] is not None else None,
                    dept_label=constants.resolve_dept(r["cnvs_dept"]),
                    contact_reason=constants.resolve_reason(r["cnvs_dept"], r["cnvs_contact_reason"]),
                    occurrence=constants.resolve_occurrence(
                        r["cnvs_dept"], r["cnvs_contact_reason"], r["cnvs_occurrence"]
                    ),
                    metadata={
                        "agent_name": conv_agnt_name,
                        "software": r["cnvs_software"],
                        "channel": r["cnvs_channel"],
                        "channel_name": constants.resolve_channel(r["cnvs_channel"]),
                        "description": r["cnvs_description"],
                    },
                )
            else:
                conversations[cid].msgs.append(
                    RawMessageData(
                        str(r["msgs_created"] or ""), r["msgs_direction"] or "", r["msgs_agnt"], msg_agnt_name
                    )
                )
                conversations[cid].queue_time = logic.get_effective_start_time(
                    conversations[cid].msgs, conversations[cid].raw_created
                )

        return list(conversations.values())

    async def fetch_raw_data_all(self, agent_group: str = None) -> list[RawConversationData]:
        rows = await self._pool.fetch_all(queries_pg.SURVEY_DATA_METADATA_QUERY_ALL)

        conversations: dict[str, RawConversationData] = {}

        for r in rows:
            cid = str(r["cnvs_id"])
            conv_agnt_name = r["conversation_agent_name"] or "Desconhecido"
            msg_agnt_name = r["message_agent_name"] or ""

            if agent_group:
                conv_dept_label = constants.resolve_dept(r["cnvs_dept"])
                if constants.resolve_conversation_group(conv_agnt_name, conv_dept_label) != agent_group:
                    continue

            if cid not in conversations:
                raw_msgs = [
                    RawMessageData(
                        str(r["msgs_created"] or ""), r["msgs_direction"] or "", r["msgs_agnt"], msg_agnt_name
                    )
                ]
                conversations[cid] = RawConversationData(
                    id=cid,
                    contact=r["cnts_name"] or "Unknown",
                    phone=r["cnts_phone"] or "",
                    start_time=logic.format_local_dt(str(r["cnvs_created"])),
                    end_time=logic.format_local_dt(str(r["cnvs_updated"])),
                    queue_time=logic.get_effective_start_time(raw_msgs, str(r["cnvs_created"])),
                    raw_created=str(r["cnvs_created"] or ""),
                    raw_updated=str(r["cnvs_updated"] or ""),
                    msgs=raw_msgs,
                    rating=float(r["cnvs_rating_agent"]) if r["cnvs_rating_agent"] is not None else None,
                    nps=float(r["cnvs_rating_nps"]) if r["cnvs_rating_nps"] is not None else None,
                    dept_label=constants.resolve_dept(r["cnvs_dept"]),
                    contact_reason=constants.resolve_reason(r["cnvs_dept"], r["cnvs_contact_reason"]),
                    occurrence=constants.resolve_occurrence(
                        r["cnvs_dept"], r["cnvs_contact_reason"], r["cnvs_occurrence"]
                    ),
                    metadata={
                        "agent_name": conv_agnt_name,
                        "software": r["cnvs_software"],
                        "channel": r["cnvs_channel"],
                        "channel_name": constants.resolve_channel(r["cnvs_channel"]),
                        "description": r["cnvs_description"],
                    },
                )
            else:
                conversations[cid].msgs.append(
                    RawMessageData(
                        str(r["msgs_created"] or ""), r["msgs_direction"] or "", r["msgs_agnt"], msg_agnt_name
                    )
                )
                conversations[cid].queue_time = logic.get_effective_start_time(
                    conversations[cid].msgs, conversations[cid].raw_created
                )

        return list(conversations.values())

    async def fetch_auditoria_contatos_raw(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        s, e = _utc_range(start_date, end_date)
        return await self._pool.fetch_all(queries_pg.AUDITORIA_CONTATOS_QUERY, s, e)

    async def fetch_auditoria_contatos_raw_all(self) -> list[dict[str, Any]]:
        return await self._pool.fetch_all(queries_pg.AUDITORIA_CONTATOS_QUERY_ALL)

    async def fetch_auditoria_contatos_data(
        self, start_date: str, end_date: str, agent_group: str = None
    ) -> tuple[list[str], list[Any]]:
        from application.services.auditoria_contatos_service import AuditoriaContatosService

        service = AuditoriaContatosService(self)
        return await service.build_report(start_date, end_date, agent_group)

    async def fetch_auditoria_demanda_raw(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        s, e = _utc_range(start_date, end_date)
        return await self._pool.fetch_all(queries_pg.AGENT_MSG_CNVS_QUERY, s, e, s, e)

    async def fetch_auditoria_demanda_data(
        self, start_date: str, end_date: str, agent_group: str = None
    ) -> tuple[list[str], list[Any]]:
        from application.services.auditoria_demanda_service import AuditoriaDemandaService

        service = AuditoriaDemandaService(self)
        return await service.build_report(start_date, end_date, agent_group)

    async def fetch_auditoria_os_raw(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        s, e = _utc_range(start_date, end_date)
        return await self._pool.fetch_all(queries_pg.OS_DATA_QUERY, s, e, s, e)

    async def fetch_auditoria_os_raw_all(self) -> list[dict[str, Any]]:
        return await self._pool.fetch_all(queries_pg.OS_DATA_QUERY_ALL)

    async def fetch_auditoria_os_data(
        self, start_date: str, end_date: str, agent_group: str = None
    ) -> tuple[list[str], list[Any]]:
        from application.services.auditoria_os_service import AuditoriaOSService

        service = AuditoriaOSService(self)
        return await service.build_report(start_date, end_date, agent_group)

    async def fetch_auditoria_chats_data(
        self, start_date: str, end_date: str, agent_group: str = None
    ) -> tuple[list[str], list[Any]]:
        return constants.CHATS_HEADER, []

    async def fetch_unmapped_counts(self) -> tuple[int, int]:
        unmapped_agents = await self._pool.fetch_val(queries_pg.UNMAPPED_AGENTS_QUERY)
        unmapped_depts = await self._pool.fetch_val(queries_pg.UNMAPPED_DEPTS_QUERY)
        return unmapped_agents or 0, unmapped_depts or 0

    async def fetch_all_groups(self, start_date: str, end_date: str) -> list[str]:
        s, e = _utc_range(start_date, end_date)
        rows = await self._pool.fetch_all(queries_pg.FETCH_GROUPS_QUERY, s, e, s, e)
        agents = [r["agnt_name"] for r in rows]
        groups = set()
        for a in agents:
            g = constants.get_agent_group(a)
            if g != "OUTROS" and g != "N/A":
                groups.add(g)

        dept_rows = await self._pool.fetch_all(queries_pg.DEPT_LIST_QUERY, s, e, s, e)
        for row in dept_rows:
            dept_id = row["cnvs_dept"]
            if dept_id is not None:
                dept_label = constants.resolve_dept(dept_id)
                if dept_label in constants.DEPT_ROUTING:
                    groups.add(constants.DEPT_ROUTING[dept_label])
            elif constants.DEPT_ROUTING:
                groups.add("Sem Departamento")

        return sorted(list(groups))

    async def fetch_all_groups_all(self) -> list[str]:
        rows = await self._pool.fetch_all(queries_pg.FETCH_GROUPS_QUERY_ALL)
        agents = [r["agnt_name"] for r in rows]
        groups = set()
        for a in agents:
            g = constants.get_agent_group(a)
            if g != "OUTROS" and g != "N/A":
                groups.add(g)

        dept_rows = await self._pool.fetch_all(queries_pg.DEPT_LIST_QUERY_ALL)
        for row in dept_rows:
            dept_id = row["cnvs_dept"]
            if dept_id is not None:
                dept_label = constants.resolve_dept(dept_id)
                if dept_label in constants.DEPT_ROUTING:
                    groups.add(constants.DEPT_ROUTING[dept_label])
            elif constants.DEPT_ROUTING:
                groups.add("Sem Departamento")

        return sorted(list(groups))

    async def fetch_messages_by_conversation(self, conversation_id: int) -> list[dict[str, Any]]:
        rows = await self._pool.fetch_all(queries_pg.MESSAGES_BY_CONVERSATION_QUERY, conversation_id)
        return [dict(r) for r in rows]

    async def fetch_messages_for_conversations(self, conversation_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
        if not conversation_ids:
            return {}
        rows = await self._pool.fetch_all(queries_pg.MESSAGES_FOR_CONVERSATIONS_QUERY, conversation_ids)
        result: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for r in rows:
            result[r["msgs_cnvs"]].append(dict(r))
        return dict(result)
