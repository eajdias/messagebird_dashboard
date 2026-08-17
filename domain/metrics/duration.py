from domain import logic
from domain.entities.report_data import RawConversationData
from domain.strategies.metrics_strategy import MetricStrategy


class DurationCalculator(MetricStrategy):
    def calculate(self, data: RawConversationData) -> float:
        # We use the canonical ticket duration logic from domain.logic
        # This ensures consistency between dashboard and OS reports.
        return logic.calculate_ticket_duration(data.raw_created, data.raw_updated)
