from collections import Counter
from typing import Any

from application.interfaces.repository import ReportRepository
from domain import constants, logic


class AuditoriaContatosService:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def build_report(
        self, start_date: str, end_date: str, agent_group: str | None = None
    ) -> tuple[list[str], list[Any]]:
        raw_data = await self.repository.fetch_auditoria_contatos_raw(start_date, end_date)
        if agent_group:
            valid_cids = {
                r["cnvs_id"]
                for r in raw_data
                if r["agnt_name"]
                and r["agnt_name"].lower() != "sistema"
                and constants.resolve_conversation_group(r["agnt_name"], constants.resolve_dept(r["cnvs_dept"]))
                == agent_group
            }
            raw_data = [r for r in raw_data if r["cnvs_id"] in valid_cids]
        contact_data = {}
        for row in raw_data:
            cid = row["cnts_id"]
            if cid not in contact_data:
                contact_data[cid] = {
                    "name": row["cnts_name"] or "Unknown",
                    "phone": row["cnts_phone"] or "",
                    "msg_count": 0,
                    "convs": set(),
                    "conv_dates": {},
                    "conv_agents": {},
                    "conv_ratings": {},
                    "conv_nps": {},
                }
            d = contact_data[cid]
            cv_id = row["cnvs_id"]
            msg_dt = logic.parse_datetime(row["msgs_created"], apply_offset=True)
            if not msg_dt:
                continue
            msg_date = msg_dt.strftime("%Y-%m-%d")
            if cv_id not in d["convs"]:
                d["convs"].add(cv_id)
                if cv_id not in d["conv_dates"]:
                    d["conv_dates"][cv_id] = msg_date
                if cv_id not in d["conv_agents"]:
                    d["conv_agents"][cv_id] = None
                if row["cnvs_rating_agent"] is not None:
                    d["conv_ratings"][cv_id] = row["cnvs_rating_agent"]
                if row["cnvs_rating_nps"] is not None:
                    d["conv_nps"][cv_id] = row["cnvs_rating_nps"]
            d["msg_count"] += 1
            if row["agnt_name"] and row["agnt_name"].lower() != "sistema":
                if d["conv_agents"][cv_id] is None:
                    d["conv_agents"][cv_id] = row["agnt_name"]
        data_list = []
        for d in sorted(contact_data.values(), key=lambda x: len(x["convs"]), reverse=True):
            human_cvs = [cid for cid, ag in d["conv_agents"].items() if ag is not None]
            if not human_cvs:
                continue
            agents_list = [d["conv_agents"][cid] for cid in human_cvs]
            ratings = [d["conv_ratings"][cid] for cid in human_cvs if cid in d["conv_ratings"]]
            nps_values = [d["conv_nps"][cid] for cid in human_cvs if cid in d["conv_nps"]]
            counts = Counter(agents_list)
            data_list.append(
                [
                    counts.most_common(1)[0][0] if counts else "",
                    d["name"],
                    d["phone"],
                    len(human_cvs),
                    d["msg_count"],
                    round(sum(ratings) / len(ratings), 1) if ratings else "",
                    round(sum(nps_values) / len(nps_values), 1) if nps_values else "",
                    "; ".join([d["conv_dates"].get(cid, "") for cid in human_cvs]),
                    "; ".join(agents_list),
                ]
            )
        return constants.CONTACTS_HEADER, data_list

    async def build_report_all(self, agent_group: str | None = None) -> tuple[list[str], list[Any]]:
        raw_data = await self.repository.fetch_auditoria_contatos_raw_all()
        if agent_group:
            valid_cids = {
                r["cnvs_id"]
                for r in raw_data
                if r["agnt_name"]
                and r["agnt_name"].lower() != "sistema"
                and constants.resolve_conversation_group(r["agnt_name"], constants.resolve_dept(r["cnvs_dept"]))
                == agent_group
            }
            raw_data = [r for r in raw_data if r["cnvs_id"] in valid_cids]
        contact_data = {}
        for row in raw_data:
            cid = row["cnts_id"]
            if cid not in contact_data:
                contact_data[cid] = {
                    "name": row["cnts_name"] or "Unknown",
                    "phone": row["cnts_phone"] or "",
                    "msg_count": 0,
                    "convs": set(),
                    "conv_dates": {},
                    "conv_agents": {},
                    "conv_ratings": {},
                    "conv_nps": {},
                }
            d = contact_data[cid]
            cv_id = row["cnvs_id"]
            msg_dt = logic.parse_datetime(row["msgs_created"], apply_offset=True)
            if not msg_dt:
                continue
            msg_date = msg_dt.strftime("%Y-%m-%d")
            if cv_id not in d["convs"]:
                d["convs"].add(cv_id)
                if cv_id not in d["conv_dates"]:
                    d["conv_dates"][cv_id] = msg_date
                if cv_id not in d["conv_agents"]:
                    d["conv_agents"][cv_id] = None
                if row["cnvs_rating_agent"] is not None:
                    d["conv_ratings"][cv_id] = row["cnvs_rating_agent"]
                if row["cnvs_rating_nps"] is not None:
                    d["conv_nps"][cv_id] = row["cnvs_rating_nps"]
            d["msg_count"] += 1
            if row["agnt_name"] and row["agnt_name"].lower() != "sistema":
                if d["conv_agents"][cv_id] is None:
                    d["conv_agents"][cv_id] = row["agnt_name"]
        data_list = []
        for d in sorted(contact_data.values(), key=lambda x: len(x["convs"]), reverse=True):
            human_cvs = [cid for cid, ag in d["conv_agents"].items() if ag is not None]
            if not human_cvs:
                continue
            agents_list = [d["conv_agents"][cid] for cid in human_cvs]
            ratings = [d["conv_ratings"][cid] for cid in human_cvs if cid in d["conv_ratings"]]
            nps_values = [d["conv_nps"][cid] for cid in human_cvs if cid in d["conv_nps"]]
            counts = Counter(agents_list)
            data_list.append(
                [
                    counts.most_common(1)[0][0] if counts else "",
                    d["name"],
                    d["phone"],
                    len(human_cvs),
                    d["msg_count"],
                    round(sum(ratings) / len(ratings), 1) if ratings else "",
                    round(sum(nps_values) / len(nps_values), 1) if nps_values else "",
                    "; ".join([d["conv_dates"].get(cid, "") for cid in human_cvs]),
                    "; ".join(agents_list),
                ]
            )
        return constants.CONTACTS_HEADER, data_list
