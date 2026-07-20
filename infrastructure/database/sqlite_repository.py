from typing import Any

from application.interfaces.repository import ReportRepository
from domain import constants, logic
from domain.entities.report_data import RawConversationData, RawMessageData
from infrastructure.database import queries
from infrastructure.database.connection import DatabaseConnection


class SqliteReportRepository(ReportRepository):
    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def fetch_raw_data_range(
        self, start_date: str, end_date: str, agent_group: str | None = None
    ) -> list[RawConversationData]:
        """
        Returns pure raw data for the given date range.
        This method is a pure data provider - no aggregation logic.
        """
        start_dt_utc, end_dt_utc = logic.get_utc_range(start_date, end_date)
        # Pass the date range twice to satisfy the (created OR updated) logic in the query
        rows = await self.db.fetch_all(
            queries.SURVEY_DATA_METADATA_QUERY, (start_dt_utc, end_dt_utc, start_dt_utc, end_dt_utc)
        )

        conversations: dict[str, RawConversationData] = {}

        for r in rows:
            cid = r["cnvs_id"]
            conv_agnt_name = r["conversation_agent_name"] or "Desconhecido"
            msg_agnt_name = r["message_agent_name"]

            # Apply agent group filter if provided
            if agent_group:
                conv_dept_label = constants.resolve_dept(r["cnvs_dept"])
                if constants.resolve_conversation_group(conv_agnt_name, conv_dept_label) != agent_group:
                    continue

            if cid not in conversations:
                raw_msgs = [RawMessageData(r["msgs_created"], r["msgs_direction"], r["msgs_agnt"], msg_agnt_name)]
                conversations[cid] = RawConversationData(
                    id=cid,
                    contact=r["cnts_name"] or "Unknown",
                    phone=r["cnts_phone"] or "",
                    contact_id=r["cnts_id"] or 0,
                    start_time=logic.format_local_dt(r["cnvs_created"]) or "",
                    end_time=logic.format_local_dt(r["cnvs_updated"]) or "",
                    queue_time=logic.get_effective_start_time(raw_msgs, r["cnvs_created"]),
                    raw_created=r["cnvs_created"],
                    raw_updated=r["cnvs_updated"],
                    msgs=raw_msgs,
                    rating=r["cnvs_rating_agent"],
                    nps=r["cnvs_rating_nps"],
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
                    RawMessageData(r["msgs_created"], r["msgs_direction"], r["msgs_agnt"], msg_agnt_name)
                )
                # Update queue_time as more messages are added
                conversations[cid].queue_time = logic.get_effective_start_time(
                    conversations[cid].msgs, conversations[cid].raw_created
                )

        return list(conversations.values())

    async def fetch_auditoria_contatos_raw(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        start_dt, end_dt = logic.get_utc_range(start_date, end_date)
        query = """
        SELECT c.cnts_id, c.cnts_name, c.cnts_phone, cv.cnvs_id, cv.cnvs_dept, cv.cnvs_rating_agent, cv.cnvs_rating_nps, m.msgs_created, a.agnt_name
        FROM contacts c
        JOIN conversations cv ON c.cnts_id = cv.cnvs_cnts
        JOIN messages m ON cv.cnvs_id = m.msgs_cnvs
        LEFT JOIN agents a ON m.msgs_agnt = a.agnt_id
        WHERE datetime(m.msgs_created) BETWEEN ? AND ?
        ORDER BY c.cnts_id, m.msgs_created ASC
        """
        return await self.db.fetch_all(query, (start_dt, end_dt))

    async def fetch_auditoria_contatos_data(
        self, start_date: str, end_date: str, agent_group: str | None = None
    ) -> tuple[list[str], list[Any]]:
        from application.services.auditoria_contatos_service import AuditoriaContatosService

        service = AuditoriaContatosService(self)
        return await service.build_report(start_date, end_date, agent_group)

    async def fetch_auditoria_chats_data(
        self, start_date: str, end_date: str, agent_group: str | None = None
    ) -> tuple[list[str], list[Any]]:
        # This is a complex one, for now we will implement a simplified version or just return empty
        # to focus on the main executive reports which are already working.
        return constants.CHATS_HEADER, []

    async def fetch_auditoria_demanda_raw(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        start_dt_utc, end_dt_utc = logic.get_utc_range(start_date, end_date)
        return await self.db.fetch_all(
            queries.AGENT_MSG_CNVS_QUERY, (start_dt_utc, end_dt_utc, start_dt_utc, end_dt_utc)
        )

    async def fetch_auditoria_demanda_data(
        self, start_date: str, end_date: str, agent_group: str | None = None
    ) -> tuple[list[str], list[Any]]:
        from application.services.auditoria_demanda_service import AuditoriaDemandaService

        service = AuditoriaDemandaService(self)
        return await service.build_report(start_date, end_date, agent_group)

    async def fetch_auditoria_os_raw(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        start_dt_utc, end_dt_utc = logic.get_utc_range(start_date, end_date)
        return await self.db.fetch_all(queries.OS_DATA_QUERY, (start_dt_utc, end_dt_utc, start_dt_utc, end_dt_utc))

    async def fetch_auditoria_os_data(
        self, start_date: str, end_date: str, agent_group: str | None = None
    ) -> tuple[list[str], list[Any]]:
        from application.services.auditoria_os_service import AuditoriaOSService

        service = AuditoriaOSService(self)
        return await service.build_report(start_date, end_date, agent_group)

    async def fetch_unmapped_counts(self) -> tuple[int, int]:
        unmapped_agents = await self.db.fetch_val(queries.UNMAPPED_AGENTS_QUERY)
        unmapped_depts = await self.db.fetch_val(queries.UNMAPPED_DEPTS_QUERY)
        return unmapped_agents or 0, unmapped_depts or 0

    async def fetch_all_groups(self, start_date: str, end_date: str) -> list[str]:
        start_dt, end_dt = logic.get_utc_range(start_date, end_date)
        rows = await self.db.fetch_all(queries.FETCH_GROUPS_QUERY, (start_dt, end_dt, start_dt, end_dt))
        agents = [r[0] for r in rows]
        groups = set()
        for a in agents:
            g = constants.get_agent_group(a)
            if g != "OUTROS" and g != "N/A":
                groups.add(g)

        # Add groups from DEPT_ROUTING based on departments present in the period
        dept_rows = await self.db.fetch_all(
            "SELECT DISTINCT c.cnvs_dept FROM conversations c "
            "WHERE (datetime(c.cnvs_created) BETWEEN ? AND ?) "
            "   OR (datetime(c.cnvs_updated) BETWEEN ? AND ?)",
            (start_dt, end_dt, start_dt, end_dt),
        )
        for row in dept_rows:
            dept_id = row[0]
            if dept_id is not None:
                dept_label = constants.resolve_dept(dept_id)
                if dept_label in constants.DEPT_ROUTING:
                    groups.add(constants.DEPT_ROUTING[dept_label])
            elif constants.DEPT_ROUTING:
                groups.add("Sem Departamento")

        return sorted(list(groups))

    async def fetch_raw_data_all(self, agent_group: str | None = None) -> list[RawConversationData]:
        rows = await self.db.fetch_all(queries.SURVEY_DATA_METADATA_QUERY_ALL)

        conversations: dict[str, RawConversationData] = {}

        for r in rows:
            cid = r["cnvs_id"]
            conv_agnt_name = r["conversation_agent_name"] or "Desconhecido"
            msg_agnt_name = r["message_agent_name"]

            if agent_group:
                conv_dept_label = constants.resolve_dept(r["cnvs_dept"])
                if constants.resolve_conversation_group(conv_agnt_name, conv_dept_label) != agent_group:
                    continue

            if cid not in conversations:
                raw_msgs = [RawMessageData(r["msgs_created"], r["msgs_direction"], r["msgs_agnt"], msg_agnt_name)]
                conversations[cid] = RawConversationData(
                    id=cid,
                    contact=r["cnts_name"] or "Unknown",
                    phone=r["cnts_phone"] or "",
                    start_time=logic.format_local_dt(r["cnvs_created"]) or "",
                    end_time=logic.format_local_dt(r["cnvs_updated"]) or "",
                    queue_time=logic.get_effective_start_time(raw_msgs, r["cnvs_created"]),
                    raw_created=r["cnvs_created"],
                    raw_updated=r["cnvs_updated"],
                    msgs=raw_msgs,
                    rating=r["cnvs_rating_agent"],
                    nps=r["cnvs_rating_nps"],
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
                    RawMessageData(r["msgs_created"], r["msgs_direction"], r["msgs_agnt"], msg_agnt_name)
                )
                # Update queue_time as more messages are added
                conversations[cid].queue_time = logic.get_effective_start_time(
                    conversations[cid].msgs, conversations[cid].raw_created
                )

        return list(conversations.values())

    async def fetch_all_groups_all(self) -> list[str]:
        rows = await self.db.fetch_all(queries.FETCH_GROUPS_QUERY_ALL)
        agents = [r[0] for r in rows]
        groups = set()
        for a in agents:
            g = constants.get_agent_group(a)
            if g != "OUTROS" and g != "N/A":
                groups.add(g)

        # Add groups from DEPT_ROUTING
        dept_rows = await self.db.fetch_all("SELECT DISTINCT c.cnvs_dept FROM conversations c")
        for row in dept_rows:
            dept_id = row[0]
            if dept_id is not None:
                dept_label = constants.resolve_dept(dept_id)
                if dept_label in constants.DEPT_ROUTING:
                    groups.add(constants.DEPT_ROUTING[dept_label])
            elif constants.DEPT_ROUTING:
                groups.add("Sem Departamento")

        return sorted(list(groups))

    async def fetch_auditoria_contatos_raw_all(self) -> list[dict[str, Any]]:
        query = """
        SELECT c.cnts_id, c.cnts_name, c.cnts_phone, cv.cnvs_id, cv.cnvs_dept, cv.cnvs_rating_agent, cv.cnvs_rating_nps, m.msgs_created, a.agnt_name
        FROM contacts c
        JOIN conversations cv ON c.cnts_id = cv.cnvs_cnts
        JOIN messages m ON cv.cnvs_id = m.msgs_cnvs
        LEFT JOIN agents a ON m.msgs_agnt = a.agnt_id
        ORDER BY c.cnts_id, m.msgs_created ASC
        """
        return await self.db.fetch_all(query)

    async def fetch_auditoria_os_raw_all(self) -> list[dict[str, Any]]:
        return await self.db.fetch_all(queries.OS_DATA_QUERY_ALL)

    async def fetch_messages_by_conversation(self, conversation_id: int) -> list[dict[str, Any]]:
        return await self.db.fetch_all(queries.MESSAGES_BY_CONVERSATION_QUERY, (conversation_id,))

    async def fetch_messages_for_conversations(self, conversation_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
        if not conversation_ids:
            return {}
        placeholders = ",".join("?" * len(conversation_ids))
        sql = queries.MESSAGES_FOR_CONVERSATIONS_QUERY.format(placeholders=placeholders)
        rows = await self.db.fetch_all(sql, tuple(conversation_ids))
        result: dict[int, list[dict[str, Any]]] = {}
        for r in rows:
            cid = r["msgs_cnvs"]
            if cid not in result:
                result[cid] = []
            result[cid].append(r)
        return result

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
        return [], 0

    async def get_conversation_detail(self, conversation_id: int) -> dict[str, Any] | None:
        return None
