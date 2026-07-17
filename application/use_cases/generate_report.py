import asyncio
import calendar
import logging
import os
import re
from collections import defaultdict
from typing import Any

from application.interfaces.exporter import ReportExporter
from application.interfaces.repository import ReportRepository
from application.services.auditoria_contatos_service import AuditoriaContatosService
from application.services.auditoria_os_service import AuditoriaOSService
from application.services.report_aggregator import ReportAggregator
from domain import constants, logic
from domain.entities.report_data import RawConversationData
from domain.metrics.art import ARTCalculator
from domain.metrics.duration import DurationCalculator
from domain.metrics.frt import FRTCalculator
from infrastructure.exporters.metrics_cache import (
    get_all_years_from_cache,
    get_annual_monthly_breakdown,
    get_year_accumulated,
    load_cache,
    save_cache,
)

logger = logging.getLogger("standalone.generate_report")

def _sanitize_path_segment(name: str) -> str:
    """Replace characters invalid on Windows filesystems with underscores."""
    name = name.strip()
    # Keep only characters valid in Windows filenames:
    # \w = Unicode letters, digits, underscore
    # \s = whitespace
    # plus safe punctuation
    safe = re.compile(r"[^\w\s\-.()\[\]{}!@#$%^&+=,;'~]")
    name = safe.sub("_", name)
    return name.rstrip(".")

class GenerateReportUseCase:
    def __init__(self, repository: ReportRepository, exporter: ReportExporter):
        self.repository = repository
        self.exporter = exporter
        # Initialize aggregator with domain strategies
        self.aggregator = ReportAggregator(strategies=[
            FRTCalculator(),
            DurationCalculator(),
            ARTCalculator()
        ])
        self.auditoria_contatos_service = AuditoriaContatosService(repository)
        self.auditoria_os_service = AuditoriaOSService(repository)

    async def _fetch_os_messages(self, os_data: list[list[Any]]) -> dict[int, list[dict[str, Any]]]:
        """Fetch messages for all conversations in OS data."""
        messages_dict = {}
        for row in os_data:
            cnvs_id = row[15]  # ID BD
            if cnvs_id and cnvs_id not in messages_dict:
                try:
                    messages = await self.repository.fetch_messages_by_conversation(cnvs_id)
                    # Convert sqlite3.Row objects to dictionaries
                    messages_dict[cnvs_id] = [dict(msg) for msg in messages]
                except Exception as e:
                    logger.error(f"Error fetching messages for conversation {cnvs_id}: {e}")
                    messages_dict[cnvs_id] = []
        return messages_dict

    async def execute(self, year: int, month: int | None, output_dir: str, skip_os: bool = False, sector: str | None = None, report_type: str = "monthly", start_date: str | None = None, end_date: str | None = None):
        if report_type == "total":
            return await self._generate_system_total(output_dir, skip_os, sector)
        if report_type == "custom_range" and start_date and end_date:
            return await self._generate_custom_range(start_date, end_date, output_dir, skip_os, sector)
        if month:
            return await self._generate_monthly(year, month, output_dir, skip_os, sector)
        else:
            return await self._generate_annual(year, output_dir, skip_os, sector)

    async def _generate_monthly(self, year: int, month: int, output_dir: str, skip_os: bool, sector: str | None):
        _, last_day = calendar.monthrange(year, month)
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{last_day}"
        return await self._generate_custom_range(start_date, end_date, output_dir, skip_os, sector)

    async def _generate_custom_range(self, start_date: str, end_date: str, output_dir: str, skip_os: bool, sector: str | None):

        # 0. Validation & Metadata
        unmapped_agents, unmapped_depts = await self.repository.fetch_unmapped_counts()
        safe_start = start_date.replace("-", "").replace("/", "")
        safe_end = end_date.replace("-", "").replace("/", "")
        report_subdir = os.path.join(output_dir, f"{safe_start}_{safe_end}")
        os.makedirs(report_subdir, exist_ok=True)

        # 1. Fetch Raw Data
        raw_data = await self.repository.fetch_raw_data_range(start_date, end_date)

        # 2. Process Domain Entities
        processed_data = self.aggregator.process_all(raw_data)

        # 3. Global Executive Report
        if not sector:
            dashboard_dto = self.aggregator.aggregate_dashboard(
                processed_data,
                title="DASHBOARD EXECUTIVO - OMNICHANNEL",
                start_date=start_date,
                end_date=end_date,
            )
            dash_path = os.path.join(report_subdir, f"Dashboard_Executivo_GLOBAL_{safe_start}_{safe_end}.xlsx")
            self.exporter.export_executive_dashboard(dash_path, dashboard_dto)

        # 4. Sector-specific processing
        all_groups = await self.repository.fetch_all_groups(start_date, end_date)
        groups = [g for g in all_groups if g == sector] if sector else all_groups

        if not groups and sector:
            print(f"Warning: Sector '{sector}' not found or has no data in this period.")
            return None

        async def process_group(group):
            safe_group = _sanitize_path_segment(group)
            group_path = os.path.join(report_subdir, safe_group)
            os.makedirs(group_path, exist_ok=True)

            # Filter data for this group
            [r for r in raw_data if constants.resolve_conversation_group(r.metadata.get("agent_name"), r.dept_label) == group]
            group_processed = [p for p in processed_data if constants.resolve_conversation_group(p.agent, p.dept_label) == group]

            # Group Dashboard
            g_dash_dto = self.aggregator.aggregate_dashboard(
                group_processed,
                title=f"DASHBOARD EXECUTIVO - {group.upper()}",
                start_date=start_date,
                end_date=end_date
            )
            g_dash_path = os.path.join(group_path, f"Dashboard_Executivo_{safe_group}_{safe_start}_{safe_end}.xlsx")
            self.exporter.export_executive_dashboard(g_dash_path, g_dash_dto)

            # Audit Reports
            auditoria_dir = os.path.join(group_path, "auditoria")
            os.makedirs(auditoria_dir, exist_ok=True)

            c_header, c_data = await self.auditoria_contatos_service.build_report(start_date, end_date, agent_group=group)
            if c_header: self.exporter.export_excel(os.path.join(auditoria_dir, "auditoria_contatos.xlsx"), c_header, c_data, "Contatos")

            if not skip_os:
                os_header, os_data = await self.auditoria_os_service.build_report(start_date, end_date, agent_group=group)
                if os_header:
                    self.exporter.export_excel(os.path.join(auditoria_dir, "auditoria_os.xlsx"), os_header, os_data, "Ordens de Serviço")
                    from infrastructure.exporters.pdf_exporter import PDFExporter
                    messages_dict = await self._fetch_os_messages(os_data)
                    PDFExporter().export_os_pdfs(os.path.join(auditoria_dir, "OS"), os_header, os_data, messages_dict)

        await asyncio.gather(*(process_group(g) for g in groups))

        # 5. Terminal Summary & README
        group_rows = self.aggregator.build_excel_rows(processed_data, report_type="groups")
        agent_rows = self.aggregator.build_excel_rows(processed_data, report_type="agents")

        # Filter by sector if specified
        if sector:
            group_rows = [r for r in group_rows if r[0] == sector or r[0] == "TOTAIS"]
            agent_rows = [r for r in agent_rows if r[1] == sector or r[2] == "TOTAIS"]

        summary_data = {
            "start_date": start_date,
            "end_date": end_date,
            "agent_data": agent_rows,
            "group_data": group_rows,
            "unmapped": (unmapped_agents, unmapped_depts)
        }

        self.exporter.export_summary(os.path.join(report_subdir, "README.md"), "Relatório Período Personalizado Omnichannel", start_date, end_date, summary_data)

        return summary_data

    async def _generate_annual(self, year: int, output_dir: str, skip_os: bool, sector: str | None):
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        unmapped_agents, unmapped_depts = await self.repository.fetch_unmapped_counts()
        report_subdir = os.path.join(output_dir, str(year))
        os.makedirs(report_subdir, exist_ok=True)

        raw_data = await self.repository.fetch_raw_data_range(start_date, end_date)
        if not raw_data:
            print(f"Warning: Nenhum dado encontrado para {year}.")
            return None

        processed_data = self.aggregator.process_all(raw_data)

        cache = load_cache()
        str(year - 1)
        prev_year_accumulated = get_year_accumulated(cache, year - 1, 12) if cache.get(f"{year-1}-01") else None

        annual_dto = self.aggregator.aggregate_dashboard(
            processed_data,
            title=f"DASHBOARD EXECUTIVO ANUAL — {year}",
            start_date=start_date,
            end_date=end_date,
            prev_month_metrics=prev_year_accumulated or {},
        )

        monthly_evolution = get_annual_monthly_breakdown(cache, year)
        if not all(m.get("total_chats") for m in monthly_evolution if m.get("total_chats") is not None):
            monthly_raw = self._fetch_monthly_breakdown(year, raw_data)
            for i, entry in enumerate(monthly_evolution):
                month_num = i + 1
                if not entry.get("total_chats") and month_num in monthly_raw:
                    entry.update(monthly_raw[month_num])

        annual_dto.monthly_evolution = monthly_evolution
        annual_dto.report_type = "annual"
        annual_dto.period_label = str(year)

        gm = annual_dto.general_metrics
        annual_key = f"{year}-annual"
        cache[annual_key] = {
            "total_chats": gm.get("total_chats", 0),
            "total_msgs": gm.get("total_msgs", 0),
            "avg_art": gm.get("avg_art"),
            "avg_duration": gm.get("avg_duration"),
            "real_nps": gm.get("real_nps"),
            "sla_compliance": gm.get("sla_compliance"),
            "avg_rating": gm.get("avg_rating"),
            "compliments": gm.get("compliments", 0),
            "negatives": gm.get("negatives", 0),
            "unique_clients": gm.get("unique_clients", 0),
            "returners": gm.get("returners", 0),
        }
        save_cache(cache)

        dash_path = os.path.join(report_subdir, f"Dashboard_Executivo_ANUAL_{year}.xlsx")
        self.exporter.export_annual_dashboard(dash_path, annual_dto)

        all_groups = await self.repository.fetch_all_groups(start_date, end_date)
        groups = [g for g in all_groups if g == sector] if sector else all_groups

        async def process_group(group):
            safe_group = _sanitize_path_segment(group)
            group_path = os.path.join(report_subdir, safe_group)
            os.makedirs(group_path, exist_ok=True)

            [r for r in raw_data
                         if constants.resolve_conversation_group(r.metadata.get("agent_name"), r.dept_label) == group]
            group_processed = [p for p in processed_data
                               if constants.resolve_conversation_group(p.agent, p.dept_label) == group]

            g_dash_dto = self.aggregator.aggregate_dashboard(
                group_processed,
                title=f"DASHBOARD ANUAL — {group.upper()} ({year})",
                start_date=start_date,
                end_date=end_date,
            )
            g_dash_dto.monthly_evolution = monthly_evolution
            g_dash_dto.report_type = "annual"
            g_dash_dto.period_label = str(year)

            g_dash_path = os.path.join(group_path, f"Dashboard_Anual_{safe_group}_{year}.xlsx")
            self.exporter.export_annual_dashboard(g_dash_path, g_dash_dto)

            auditoria_dir = os.path.join(group_path, "auditoria")
            os.makedirs(auditoria_dir, exist_ok=True)

            c_header, c_data = await self.auditoria_contatos_service.build_report(
                start_date, end_date, agent_group=group)
            if c_header:
                self.exporter.export_excel(os.path.join(auditoria_dir, "auditoria_contatos.xlsx"),
                                           c_header, c_data, "Contatos")

            if not skip_os:
                os_header, os_data = await self.auditoria_os_service.build_report(
                    start_date, end_date, agent_group=group)
                if os_header:
                    self.exporter.export_excel(os.path.join(auditoria_dir, "auditoria_os.xlsx"),
                                               os_header, os_data, "Ordens de Serviço")
                    from infrastructure.exporters.pdf_exporter import PDFExporter
                    messages_dict = await self._fetch_os_messages(os_data)
                    PDFExporter().export_os_pdfs(os.path.join(auditoria_dir, "OS"),
                                                  os_header, os_data, messages_dict)

        await asyncio.gather(*(process_group(g) for g in groups))

        group_rows = self.aggregator.build_excel_rows(processed_data, report_type="groups")
        agent_rows = self.aggregator.build_excel_rows(processed_data, report_type="agents")

        summary_data = {
            "start_date": start_date,
            "end_date": end_date,
            "agent_data": agent_rows,
            "group_data": group_rows,
            "unmapped": (unmapped_agents, unmapped_depts),
            "monthly_evolution": monthly_evolution,
        }
        self.exporter.export_summary(
            os.path.join(report_subdir, "README.md"),
            f"Relatório Anual Omnichannel — {year}",
            start_date, end_date, summary_data,
            report_type="annual",
        )

        return summary_data

    async def _generate_system_total(self, output_dir: str, skip_os: bool, sector: str | None):
        raw_data = await self.repository.fetch_raw_data_all()
        if not raw_data:
            print("Warning: Nenhum dado encontrado no banco.")
            return None

        processed_data = self.aggregator.process_all(raw_data)

        dates = [p.raw_created for p in processed_data if p.raw_created]
        first_date = min(dates) if dates else "N/A"
        last_date = max(dates) if dates else "N/A"

        cache = load_cache()

        total_dto = self.aggregator.aggregate_dashboard(
            processed_data,
            title="DASHBOARD EXECUTIVO — TOTAL DO SISTEMA",
            start_date=first_date,
            end_date=last_date,
        )

        all_years = get_all_years_from_cache(cache)
        full_evolution = []
        for y in all_years:
            full_evolution.extend(get_annual_monthly_breakdown(cache, int(y)))

        total_dto.monthly_evolution = full_evolution
        total_dto.report_type = "total"
        total_dto.period_label = f"Todo o histórico ({first_date} a {last_date})"

        report_subdir = os.path.join(output_dir, "total")
        os.makedirs(report_subdir, exist_ok=True)

        dash_path = os.path.join(report_subdir, "Dashboard_Executivo_TOTAL_SISTEMA.xlsx")
        self.exporter.export_annual_dashboard(dash_path, total_dto)

        all_groups = await self.repository.fetch_all_groups_all()
        groups = [g for g in all_groups if g == sector] if sector else all_groups

        unmapped_agents, unmapped_depts = await self.repository.fetch_unmapped_counts()

        async def process_group(group):
            safe_group = _sanitize_path_segment(group)
            group_path = os.path.join(report_subdir, safe_group)
            os.makedirs(group_path, exist_ok=True)

            [r for r in raw_data
                         if constants.resolve_conversation_group(r.metadata.get("agent_name"), r.dept_label) == group]
            group_processed = [p for p in processed_data
                               if constants.resolve_conversation_group(p.agent, p.dept_label) == group]

            g_dash_dto = self.aggregator.aggregate_dashboard(
                group_processed,
                title=f"DASHBOARD TOTAL — {group.upper()}",
                start_date=first_date,
                end_date=last_date,
            )
            g_dash_dto.monthly_evolution = full_evolution
            g_dash_dto.report_type = "total"
            g_dash_dto.period_label = total_dto.period_label

            g_dash_path = os.path.join(group_path, f"Dashboard_Total_{safe_group}.xlsx")
            self.exporter.export_annual_dashboard(g_dash_path, g_dash_dto)

            auditoria_dir = os.path.join(group_path, "auditoria")
            os.makedirs(auditoria_dir, exist_ok=True)

            c_header, c_data = await self.auditoria_contatos_service.build_report_all(agent_group=group)
            if c_header:
                self.exporter.export_excel(os.path.join(auditoria_dir, "auditoria_contatos.xlsx"),
                                           c_header, c_data, "Contatos")

            if not skip_os:
                os_header, os_data = await self.auditoria_os_service.build_report_all(agent_group=group)
                if os_header:
                    self.exporter.export_excel(os.path.join(auditoria_dir, "auditoria_os.xlsx"),
                                               os_header, os_data, "Ordens de Serviço")
                    from infrastructure.exporters.pdf_exporter import PDFExporter
                    messages_dict = await self._fetch_os_messages(os_data)
                    PDFExporter().export_os_pdfs(os.path.join(auditoria_dir, "OS"),
                                                  os_header, os_data, messages_dict)

        await asyncio.gather(*(process_group(g) for g in groups))

        group_rows = self.aggregator.build_excel_rows(processed_data, report_type="groups")
        agent_rows = self.aggregator.build_excel_rows(processed_data, report_type="agents")

        summary_data = {
            "start_date": first_date,
            "end_date": last_date,
            "agent_data": agent_rows,
            "group_data": group_rows,
            "unmapped": (unmapped_agents, unmapped_depts),
            "monthly_evolution": full_evolution,
        }
        self.exporter.export_summary(
            os.path.join(report_subdir, "README.md"),
            "Relatório Total do Sistema Omnichannel",
            first_date, last_date, summary_data,
            report_type="total",
        )

        return summary_data

    def _fetch_monthly_breakdown(self, year: int, raw_data: list[RawConversationData]) -> dict[int, dict]:
        by_month: dict[int, list[RawConversationData]] = defaultdict(list)
        for conv in raw_data:
            if conv.raw_created:
                dt = logic.parse_datetime(conv.raw_created)
                if dt and dt.year == year:
                    by_month[dt.month].append(conv)

        monthly_stats = {}
        for month_num, month_data in by_month.items():
            processed = self.aggregator.process_all(month_data)
            stats = self.aggregator.aggregate_statistics(processed)
            monthly_stats[month_num] = stats
        return monthly_stats
