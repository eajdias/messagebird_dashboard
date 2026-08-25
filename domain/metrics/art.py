from domain import logic
from domain.entities.report_data import RawConversationData
from domain.strategies.metrics_strategy import MetricStrategy


def _calculate_art(data: RawConversationData) -> float | None:
    """Average Response Time: mean of deltas between each client message and
    the next agent reply. Messages come sorted chronologically (ASC)."""
    deltas: list[float] = []
    pending_client: str | None = None

    for m in data.msgs:
        if m.direction == "received":
            pending_client = m.created
            continue
        if m.direction == "sent" and pending_client is not None:
            client_dt = logic.parse_datetime(pending_client, apply_offset=True)
            agent_dt = logic.parse_datetime(m.created, apply_offset=True)
            if client_dt and agent_dt and agent_dt > client_dt:
                deltas.append((agent_dt - client_dt).total_seconds() / 60)
            pending_client = None

    if not deltas:
        return None
    return round(sum(deltas) / len(deltas), 2)


class ARTCalculator(MetricStrategy):
    def calculate(self, data: RawConversationData) -> float | None:
        return _calculate_art(data)
