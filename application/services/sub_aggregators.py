from collections import Counter
from typing import Any

from domain.entities.report_data import ProcessedReportData
from domain.logic import parse_datetime
from domain.services.metrics_calculator import MetricsCalculator

DOW_NAMES = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

class TemporalAggregator:
    def aggregate_heatmap(self, data: list[ProcessedReportData]) -> list[dict[str, Any]]:
        """Calcula a distribuição horária por dia da semana (Heatmap)."""
        heatmap = {}
        for p in data:
            dt = parse_datetime(p.raw_created, apply_offset=True)
            if dt:
                # weekday(): 0 (Segunda) a 6 (Domingo)
                key = (dt.weekday(), dt.hour)
                heatmap[key] = heatmap.get(key, 0) + 1

        return [{"day": day, "hour": hour, "value": count} for (day, hour), count in heatmap.items()]

    def aggregate_dow(self, data: list[ProcessedReportData]) -> list[dict[str, Any]]:
        """Calcula a distribuição de chats por dia da semana."""
        dow_counts = Counter()
        for p in data:
            dt = parse_datetime(p.raw_created, apply_offset=True)
            if dt:
                dow_counts[dt.weekday()] += 1
        return [{"day": DOW_NAMES[day], "value": count} for day, count in sorted(dow_counts.items())]

class TopicAggregator:
    def aggregate_reasons(self, data: list[ProcessedReportData]) -> list[dict[str, Any]]:
        """Calcula os motivos de contato mais frequentes."""
        reasons = Counter(p.contact_reason for p in data if p.contact_reason and p.contact_reason != "N/A")
        return [{"label": reason, "value": count} for reason, count in reasons.most_common(15)]

    def aggregate_occurrences(self, data: list[ProcessedReportData]) -> list[dict[str, Any]]:
        """Calcula as ocorrências mais frequentes."""
        occurrences = Counter(p.occurrence for p in data if p.occurrence and p.occurrence != "N/A")
        return [{"label": occ, "value": count} for occ, count in occurrences.most_common(15)]

class RatingAggregator:
    def aggregate_distributions(self, data: list[ProcessedReportData]) -> dict[str, Any]:
        """Calcula as distribuições de NPS e Notas."""
        ratings = [p.rating for p in data if p.rating is not None]
        nps_scores = [p.nps for p in data if p.nps is not None]

        return {
            "nps_distribution": MetricsCalculator.calculate_nps_distribution(nps_scores),
            "rating_distribution": MetricsCalculator.calculate_rating_distribution(ratings)
        }

    def aggregate_agent_ratings(self, data: list[ProcessedReportData]) -> dict[str, Any]:
        """Calcula distribuição de notas técnicas (1-5) por agente."""
        agent_map: dict[str, list[ProcessedReportData]] = {}
        for p in data:
            if p.agent not in agent_map:
                agent_map[p.agent] = []
            agent_map[p.agent].append(p)

        agents = sorted(agent_map.keys())
        rating_rows = []
        nps_rows = []

        for agent in agents:
            ratings = [p.rating for p in agent_map[agent] if p.rating is not None]
            nps_scores = [p.nps for p in agent_map[agent] if p.nps is not None]

            rating_dist = {str(i): 0 for i in range(1, 6)}
            for r in ratings:
                if 1 <= r <= 5:
                    rating_dist[str(int(r))] += 1

            nps_dist = {str(i): 0 for i in range(1, 11)}
            for n in nps_scores:
                if 1 <= n <= 10:
                    nps_dist[str(int(n))] += 1

            rating_row = [agent]
            for i in range(1, 6):
                rating_row.append(rating_dist[str(i)])
            rating_row.append(len(ratings))
            rating_rows.append(rating_row)

            nps_row = [agent]
            for i in range(1, 11):
                nps_row.append(nps_dist[str(i)])
            nps_row.append(len(nps_scores))
            nps_rows.append(nps_row)

        # Totals
        rating_header = ["Agente"] + [f"Nota {i}" for i in range(1, 6)] + ["TOTAL"]
        nps_header = ["Agente"] + [f"NPS {i}" for i in range(1, 11)] + ["TOTAL"]

        rating_total = ["TOTAL"]
        for i in range(1, 6):
            rating_total.append(sum(r[i] for r in rating_rows))
        rating_total.append(sum(r[-1] for r in rating_rows))

        nps_total = ["TOTAL"]
        for i in range(1, 11):
            nps_total.append(sum(r[i] for r in nps_rows))
        nps_total.append(sum(r[-1] for r in nps_rows))

        rating_rows.append(rating_total)
        nps_rows.append(nps_total)

        return {
            "rating_header": rating_header,
            "rating_rows": rating_rows,
            "nps_header": nps_header,
            "nps_rows": nps_rows
        }
