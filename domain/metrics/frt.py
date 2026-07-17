from domain import logic
from domain.entities.report_data import RawConversationData
from domain.services.metrics_calculator import MetricsCalculator
from domain.strategies.metrics_strategy import MetricStrategy


class FRTCalculator(MetricStrategy):
    def calculate(self, data: RawConversationData) -> float:
        first_resp_dt = None
        for m in data.msgs:
            if m.direction == "sent" and m.agent_id is not None:
                first_resp_dt = logic.parse_datetime(m.created, apply_offset=True)
                break

        q_time = data.queue_time
        start_dt_obj = logic.parse_datetime(q_time, apply_offset=True) if q_time else logic.parse_datetime(data.raw_created, apply_offset=True)

        if not first_resp_dt or not start_dt_obj:
            return None

        return MetricsCalculator.calculate_frt(start_dt_obj, first_resp_dt)
