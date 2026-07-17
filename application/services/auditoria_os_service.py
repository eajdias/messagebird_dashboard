from typing import Any

from application.interfaces.repository import ReportRepository
from domain import constants, logic


def _detect_reopen_by_gap(messages: list[dict[str, Any]], gap_hours: float = None) -> bool:
    if gap_hours is None:
        gap_hours = constants.REOPEN_GAP_HOURS
    if len(messages) < 2:
        return False
    gap_threshold = gap_hours * 3600
    for i in range(1, len(messages)):
        prev = logic.parse_datetime(messages[i - 1]["msgs_created"])
        curr = logic.parse_datetime(messages[i]["msgs_created"])
        if prev and curr and (curr - prev).total_seconds() >= gap_threshold:
            return True
    return False


class AuditoriaOSService:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def _build_report_rows(self, rows: list[dict[str, Any]], agent_group: str = None) -> tuple[list[str], list[Any]]:
        conv_ids = [r["cnvs_id"] for r in rows]
        msgs_map = await self.repository.fetch_messages_for_conversations(conv_ids)

        data_list = []
        for r in rows:
            agnt_name = r["agnt_name"] or "Não Mapeado"
            if agent_group:
                conv_dept_label = constants.resolve_dept(r["cnvs_dept"])
                if constants.resolve_conversation_group(agnt_name, conv_dept_label) != agent_group:
                    continue

            msgs = msgs_map.get(r["cnvs_id"], [])
            effective_start = logic.get_effective_start_time(msgs, r["cnvs_created"])
            created = logic.format_local_dt(effective_start)
            duration = logic.calculate_ticket_duration(effective_start, r["cnvs_updated"])

            has_reopening = (r["cnvs_reopened_count"] or 0) > 0
            if not has_reopening and msgs:
                has_reopening = _detect_reopen_by_gap(msgs)

            dept = constants.resolve_dept(r["cnvs_dept"])
            contact_reason = constants.resolve_reason(r["cnvs_dept"], r["cnvs_contact_reason"])
            occurrence = constants.resolve_occurrence(r["cnvs_dept"], r["cnvs_contact_reason"], r["cnvs_occurrence"])

            data_list.append([
                r["cnvs_bird"],
                created,
                agnt_name,
                r["cnts_name"] or "Desconhecido",
                r["cnts_phone"] or "",
                r["cnvs_tax_id"] or "",
                r["cnvs_software"] or "",
                dept,
                contact_reason,
                occurrence,
                r["cnvs_rating_agent"] if r["cnvs_rating_agent"] is not None else "",
                r["cnvs_rating_nps"] if r["cnvs_rating_nps"] is not None else "",
                "Sim" if has_reopening else "Não",
                r["cnvs_description"] or "",
                duration if duration > 0 else "N/D",
                r["cnvs_id"],
                f"./OS/OS_{r['cnvs_bird']}.pdf" if r["cnvs_bird"] else ""
            ])

        return constants.OS_HEADER, data_list

    async def build_report(self, start_date: str, end_date: str, agent_group: str = None) -> tuple[list[str], list[Any]]:
        rows = await self.repository.fetch_auditoria_os_raw(start_date, end_date)
        return await self._build_report_rows(rows, agent_group)

    async def build_report_all(self, agent_group: str = None) -> tuple[list[str], list[Any]]:
        rows = await self.repository.fetch_auditoria_os_raw_all()
        return await self._build_report_rows(rows, agent_group)
