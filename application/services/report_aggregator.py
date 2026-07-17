from collections import Counter
from typing import Any

from application.interfaces.exporter import DashboardDTO
from application.services.sub_aggregators import RatingAggregator, TemporalAggregator, TopicAggregator
from domain import constants
from domain.entities.report_data import ProcessedReportData, RawConversationData
from domain.services.metrics_calculator import MetricsCalculator


class ReportAggregator:
    def __init__(self, strategies: list[Any] = None,
                 temporal_aggregator: TemporalAggregator = None,
                 topic_aggregator: TopicAggregator = None,
                 rating_aggregator: RatingAggregator = None):
        self._strategies = strategies or []
        self._temporal = temporal_aggregator or TemporalAggregator()
        self._topic = topic_aggregator or TopicAggregator()
        self._rating = rating_aggregator or RatingAggregator()

    def process_conversation(self, raw_data: RawConversationData) -> ProcessedReportData:
        """Processes a single conversation to extract granular metrics."""
        results = {}
        for strategy in self._strategies:
            # We use the class name as key for simplicity
            results[type(strategy).__name__] = strategy.calculate(raw_data)

        # Calculate derived fields
        rating = raw_data.rating
        is_compliment = rating in (4, 5)
        is_negative = rating in (1, 2)
        nps = raw_data.nps
        if nps is not None and not (1 <= nps <= 10):
            nps = None

        return ProcessedReportData(
            conversation_id=raw_data.id,
            agent=raw_data.metadata.get("agent_name", "Unknown"),
            contact_id=raw_data.contact_id,
            frt_min=results.get("FRTCalculator"),
            duration_min=results.get("DurationCalculator"),
            art_min=results.get("ARTCalculator"),
            rating=rating,
            nps=nps,
            dept_label=raw_data.dept_label,
            contact_reason=raw_data.contact_reason,
            occurrence=raw_data.occurrence,
            is_compliment=is_compliment,
            is_negative=is_negative,
            msg_count=len(raw_data.msgs),
            phone=raw_data.phone,
            start_time=raw_data.start_time,
            end_time=raw_data.end_time,
            raw_created=raw_data.raw_created
        )

    def process_all(self, raw_data_list: list[RawConversationData]) -> list[ProcessedReportData]:
        """Processes a list of raw conversations into processed data."""
        return [self.process_conversation(r) for r in raw_data_list]

    def aggregate_statistics(self, processed_data: list[ProcessedReportData]) -> dict[str, Any]:
        """
        Orchestrates the aggregation of statistics for a set of conversations.
        Delegates all math to MetricsCalculator.
        """
        ratings = [p.rating for p in processed_data if p.rating is not None]
        nps_scores = [p.nps for p in processed_data if p.nps is not None]
        arts = [p.art_min for p in processed_data if isinstance(p.art_min, (int, float)) and 0 < p.art_min <= constants.MAX_ART_MINUTES]
        durations = [p.duration_min for p in processed_data if isinstance(p.duration_min, (int, float)) and 0 < p.duration_min <= constants.MAX_DURATION_MINUTES]

        compliments = sum(1 for p in processed_data if p.is_compliment)
        negatives = sum(1 for p in processed_data if p.is_negative)
        total_ratings = len(ratings)

        # Count unique contacts and returners (contacts with >1 chat)
        contacts = Counter(p.contact_id for p in processed_data if p.contact_id)
        unique_clients = len(contacts)
        returners = sum(1 for count in contacts.values() if count > 1)

        return {
            "avg_rating": MetricsCalculator.calculate_rating_average(ratings),
            "avg_nps": MetricsCalculator.calculate_average(nps_scores),
            "real_nps": MetricsCalculator.calculate_nps(nps_scores),
            "avg_art": MetricsCalculator.calculate_average(arts),
            "avg_duration": MetricsCalculator.calculate_average(durations),
            "sla_compliance": MetricsCalculator.calculate_sla_rate(arts, threshold=constants.SLA_FRT_THRESHOLD_MINUTES),
            "total_chats": len(processed_data),
            "total_msgs": sum(p.msg_count for p in processed_data),
            "compliments": compliments,
            "negatives": negatives,
            "pct_compliments": round(compliments / total_ratings * 100, 2) if total_ratings > 0 else "N/A",
            "pct_negatives": round(negatives / total_ratings * 100, 2) if total_ratings > 0 else "N/A",
            "unique_clients": unique_clients,
            "returners": returners,
            "rating_coverage": round(total_ratings / len(processed_data) * 100, 2) if len(processed_data) > 0 else 0
        }

    def aggregate_dashboard(self, data: list[ProcessedReportData], title: str, start_date: str, end_date: str, prev_month_metrics: dict[str, Any] = None) -> DashboardDTO:
        general = self.aggregate_statistics(data)
        dist_data = self._rating.aggregate_distributions(data)
        topic_reasons = self._topic.aggregate_reasons(data)
        topic_occurrences = self._topic.aggregate_occurrences(data)
        tabular_rows = self.build_excel_rows(data, report_type="agents")
        dept_rows = self._build_departments_rows(data)
        dow_data = self._temporal.aggregate_dow(data)
        agent_detail = self._rating.aggregate_agent_ratings(data)

        agent_map: dict[str, list[ProcessedReportData]] = {}
        for p in data:
            agent_map.setdefault(p.agent, []).append(p)

        agents = sorted(agent_map.keys())
        bsc_header = ["Métrica"] + agents

        rows_t1 = []

        def _pct_compliments(agent):
            p_list = agent_map[agent]
            ratings = [p.rating for p in p_list if p.rating is not None]
            elogios = sum(1 for r in ratings if r >= 4)
            if not ratings:
                return None
            return round(elogios / len(ratings) * 100, 1)

        def _pct_negatives(agent):
            p_list = agent_map[agent]
            ratings = [p.rating for p in p_list if p.rating is not None]
            neg = sum(1 for r in ratings if r <= 2)
            if not ratings:
                return None
            return round(neg / len(ratings) * 100, 1)

        def _nps_score(agent):
            nps_scores = [p.nps for p in agent_map[agent] if p.nps is not None]
            return MetricsCalculator.calculate_nps(nps_scores)

        def _avg_rating(agent):
            ratings = [p.rating for p in agent_map[agent] if p.rating is not None]
            return MetricsCalculator.calculate_rating_average(ratings) or 0

        def _total_msgs(agent):
            return sum(p.msg_count for p in agent_map[agent])

        def _count(agent):
            return len(agent_map[agent])

        kpi_cfg = next(iter(constants.KPI_CONFIG.values()), {})
        t1_defs = kpi_cfg.get("t1", [])
        t2_defs = kpi_cfg.get("t2", [])

        # Métricas automáticas: nome (conforme KPI_CONFIG) -> função de cálculo por agente.
        # Demais métricas são manuais/externas e default 0 (podem ser sobrescritas por fonte externa).
        _t1_computers = {
            "Elogios de atendimento / Feedback": _pct_compliments,
            "NPS (Net Promoter Score)": _nps_score,
            "Feedback Negativo (Penalidade)": _pct_negatives,
            "Atendimentos | Ligações Finalizados": _count,
        }
        _t2_computers = {
            "Avaliação Média": _avg_rating,
            "Mensagens Totais": _total_msgs,
        }
        def _zero(a):
            return 0

        rows_t1 = [
            [m["name"]] + [_t1_computers.get(m["name"], _zero)(a) for a in agents]
            for m in t1_defs
        ]

        rows_t2 = [
            [m["name"]] + [_t2_computers.get(m["name"], _zero)(a) for a in agents]
            for m in t2_defs
        ]

        return DashboardDTO(
            title=title,
            start_date=start_date,
            end_date=end_date,
            general_metrics=general,
            nps_distribution=dist_data["nps_distribution"],
            rating_distribution=dist_data["rating_distribution"],
            heatmap_data=self._temporal.aggregate_heatmap(data),
            topic_data=topic_reasons,
            occurrence_data=topic_occurrences,
            bsc_header=bsc_header,
            bsc_data_t1=rows_t1,
            bsc_data_t2=rows_t2,
            bsc_kpi_config=constants.KPI_CONFIG,
            tabular_header=constants.AGENTS_HEADER,
            tabular_data=tabular_rows,
            department_data=dept_rows,
            department_header=constants.DEPARTMENTS_HEADER,
            dow_data=dow_data,
            agent_rating_detail=agent_detail["rating_rows"],
            agent_nps_detail=agent_detail["nps_rows"],
            prev_month_metrics=prev_month_metrics or {},
        )

    def aggregate_monthly_breakdown(self, processed_data_by_month: dict[str, list[ProcessedReportData]],
                                     prev_metrics: dict[str, Any] = None) -> list[dict[str, Any]]:
        months = []
        for month_key in sorted(processed_data_by_month.keys()):
            data = processed_data_by_month[month_key]
            stats = self.aggregate_statistics(data)
            months.append({
                "month": month_key,
                "total_chats": stats.get("total_chats", 0),
                "total_msgs": stats.get("total_msgs", 0),
                "avg_art": stats.get("avg_art"),
                "avg_duration": stats.get("avg_duration"),
                "real_nps": stats.get("real_nps"),
                "sla_compliance": stats.get("sla_compliance"),
                "avg_rating": stats.get("avg_rating"),
                "compliments": stats.get("compliments", 0),
                "negatives": stats.get("negatives", 0),
                "unique_clients": stats.get("unique_clients", 0),
                "returners": stats.get("returners", 0),
            })
        return months

    def build_excel_rows(self, processed_data: list[ProcessedReportData], report_type: str = "agents") -> list[list[Any]]:
        """
        Transforms processed entities into Excel-ready rows based on report type.
        Supports: 'agents', 'groups', 'departments'.
        """
        if report_type == "agents":
            return self._build_agents_rows(processed_data)
        elif report_type == "groups":
            return self._build_groups_rows(processed_data)
        elif report_type == "departments":
            return self._build_departments_rows(processed_data)
        return []

    def _build_agent_row(self, label: str, group: str, agent: str, stats: dict) -> list:
        return [
            label, group, agent,
            stats["total_chats"], "100%",
            stats["compliments"], stats["pct_compliments"],
            stats["negatives"], stats["pct_negatives"],
            stats["total_msgs"],
            round(stats["total_msgs"] / stats["total_chats"], 2) if stats["total_chats"] > 0 else 0,
            stats["avg_rating"], stats["avg_nps"], stats["real_nps"],
            stats["avg_art"], stats["sla_compliance"], stats["avg_duration"],
            stats["unique_clients"], stats["returners"]
        ]

    def _build_agents_rows(self, data: list[ProcessedReportData]) -> list[list[Any]]:
        # Group by agent
        agent_map: dict[str, list[ProcessedReportData]] = {}
        for p in data:
            if p.agent not in agent_map:
                agent_map[p.agent] = []
            agent_map[p.agent].append(p)

        rows = []
        for agent, p_list in agent_map.items():
            stats = self.aggregate_statistics(p_list)

            # Find main department for this agent
            depts = Counter(p.dept_label for p in p_list)
            main_dept = depts.most_common(1)[0][0] if depts else "N/A"

            rows.append(self._build_agent_row(
                main_dept, constants.resolve_conversation_group(agent, main_dept), agent, stats
            ))

        # Add Global Summary Row at the top
        global_stats = self.aggregate_statistics(data)
        rows.sort(key=lambda x: x[9], reverse=True) # Sort by total messages

        # TOTAIS must be sum of per-agent values (not global deduplication),
        # so that it matches the visible agents in the table.
        global_stats["unique_clients"] = sum(r[17] for r in rows)
        global_stats["returners"] = sum(r[18] for r in rows)

        rows.insert(0, self._build_agent_row(
            "N/A", "GLOBAL", "TOTAIS", global_stats
        ))
        return rows

    def _build_groups_rows(self, data: list[ProcessedReportData]) -> list[list[Any]]:
        group_map: dict[str, list[ProcessedReportData]] = {}
        for p in data:
            grp = constants.resolve_conversation_group(p.agent, p.dept_label)
            if grp not in group_map:
                group_map[grp] = []
            group_map[grp].append(p)

        rows = []
        for grp, p_list in group_map.items():
            stats = self.aggregate_statistics(p_list)
            rows.append([
                grp, stats["total_chats"], stats["total_msgs"], stats["avg_art"],
                stats["sla_compliance"], stats["avg_duration"], stats["avg_nps"],
                stats["real_nps"], stats["avg_rating"], stats["unique_clients"], stats["returners"]
            ])
        return rows

    def _build_departments_rows(self, data: list[ProcessedReportData]) -> list[list[Any]]:
        dept_map: dict[str, list[ProcessedReportData]] = {}
        for p in data:
            if p.dept_label not in dept_map:
                dept_map[p.dept_label] = []
            dept_map[p.dept_label].append(p)

        total_chats = len(data)
        rows = []
        for dept, p_list in dept_map.items():
            stats = self.aggregate_statistics(p_list)
            rows.append([
                dept, stats["total_chats"],
                f"{round(stats['total_chats']/total_chats*100, 2)}%" if total_chats else "0%",
                stats["total_msgs"], stats["avg_art"], stats["sla_compliance"],
                stats["avg_duration"], stats["avg_nps"], stats["real_nps"],
                stats["avg_rating"], stats["unique_clients"], stats["returners"],
                f"{stats['rating_coverage']}%"
            ])
        return rows
