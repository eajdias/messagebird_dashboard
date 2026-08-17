from datetime import timedelta
from typing import Any

from application.interfaces.repository import ReportRepository
from domain import constants, logic


class AuditoriaDemandaService:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def build_report(
        self, start_date: str, end_date: str, agent_group: str | None = None
    ) -> tuple[list[str], list[Any]]:
        hours = {h: {"sent": 0, "received": 0, "cnvs": 0} for h in range(24)}

        dt_start, dt_end = logic.local_date_bounds(start_date, end_date)
        business_days = 0
        curr = dt_start
        while curr <= dt_end:
            if curr.weekday() < 5:
                business_days += 1
            curr += timedelta(days=1)
        if business_days < 1:
            business_days = 1

        msg_rows = await self.repository.fetch_auditoria_demanda_raw(start_date, end_date)
        if agent_group:
            valid_cids = {
                r["cnvs_id"]
                for r in msg_rows
                if r["agnt_name"]
                and r["agnt_name"].lower() != "sistema"
                and constants.resolve_conversation_group(r["agnt_name"], constants.resolve_dept(r["cnvs_dept"]))
                == agent_group
            }
            msg_rows = [r for r in msg_rows if r["cnvs_id"] in valid_cids]

        for r in msg_rows:
            local_dt = logic.parse_datetime(r["msgs_created"], apply_offset=True)
            if not local_dt:
                continue
            h = local_dt.hour
            if r["msgs_direction"] == "sent":
                hours[h]["sent"] += 1
            elif r["msgs_direction"] == "received":
                hours[h]["received"] += 1

        seen_cids = set()
        for r in msg_rows:
            if r["cnvs_id"] not in seen_cids:
                seen_cids.add(r["cnvs_id"])
                local_dt = logic.parse_datetime(r["cnvs_created"], apply_offset=True)
                if local_dt:
                    hours[local_dt.hour]["cnvs"] += 1

        data_list = []
        for h in range(24):
            total_new = hours[h]["cnvs"]
            data_list.append(
                [f"{h:02d}", total_new, hours[h]["received"], hours[h]["sent"], round(total_new / business_days, 2)]
            )
        return constants.DEMAND_HEADER, data_list
