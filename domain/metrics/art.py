from domain.entities.report_data import RawConversationData
from domain.metrics.frt import _calculate_response_time
from domain.strategies.metrics_strategy import MetricStrategy


class ARTCalculator(MetricStrategy):
    def calculate(self, data: RawConversationData) -> float:
        return _calculate_response_time(data)
