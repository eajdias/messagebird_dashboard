from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class DashboardDTO:
    title: str
    start_date: str
    end_date: str
    general_metrics: dict[str, Any]
    nps_distribution: dict[str, int]
    rating_distribution: dict[str, int]
    heatmap_data: list[dict[str, Any]]
    topic_data: list[dict[str, Any]]
    occurrence_data: list[dict[str, Any]] = None
    bsc_header: list[str] = None
    bsc_data_t1: list[list[Any]] = None
    bsc_data_t2: list[list[Any]] = None
    bsc_kpi_config: dict[str, Any] = None
    tabular_header: list[str] = None
    tabular_data: list[list[Any]] = None
    department_data: list[list[Any]] = None
    department_header: list[str] = None
    dow_data: list[dict[str, Any]] = None
    agent_rating_detail: list[list[Any]] = None
    agent_nps_detail: list[list[Any]] = None
    prev_month_metrics: dict[str, Any] = None
    monthly_evolution: list[dict[str, Any]] = None
    report_type: str = "monthly"
    period_label: str = ""


class ReportExporter(ABC):
    @abstractmethod
    def export_excel(
        self,
        filename: str,
        header: list[str],
        data: list[list[Any]],
        sheet_name: str = "Relatório",
        highlight_frt: bool = False,
    ):
        pass

    @abstractmethod
    def export_executive_dashboard(self, filename: str, dto: DashboardDTO):
        pass

    @abstractmethod
    def export_agent_detailed(
        self,
        filename: str,
        agent_name: str,
        header: list[str],
        data: list[list[Any]],
    ):
        pass

    @abstractmethod
    def export_summary(
        self,
        filename: str,
        title: str,
        start_date: str,
        end_date: str,
        summary_data: dict[str, Any],
        report_type: str = "monthly",
    ):
        pass

    @abstractmethod
    def export_annual_dashboard(self, filename: str, dto: DashboardDTO):
        pass
