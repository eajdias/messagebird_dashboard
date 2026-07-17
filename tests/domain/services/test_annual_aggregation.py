import unittest

from application.services.report_aggregator import ReportAggregator
from domain.entities.report_data import RawConversationData, RawMessageData
from domain.metrics.art import ARTCalculator
from domain.metrics.duration import DurationCalculator
from domain.metrics.frt import FRTCalculator


class TestAnnualAggregation(unittest.TestCase):
    def setUp(self):
        self.aggregator = ReportAggregator(strategies=[
            FRTCalculator(),
            DurationCalculator(),
            ARTCalculator()
        ])

    def _make_conversation(self, cid: str, agent: str, rating: int = None, nps: int = None,
                           phone: str = "5511999999999", msg_count: int = 3,
                           created: str = "2024-03-01 10:00:00",
                           updated: str = "2024-03-01 10:30:00") -> RawConversationData:
        msgs = [RawMessageData(created, "received", None, agent)]
        for i in range(msg_count):
            msgs.append(RawMessageData(
                f"2024-03-01 10:{i+1:02d}:00", "sent", "1", agent
            ))
        raw = RawConversationData(
            id=cid, contact="Test", phone=phone,
            start_time=created, end_time=updated,
            queue_time=None, raw_created=created, raw_updated=updated,
            msgs=msgs, metadata={"agent_name": agent},
            rating=rating, nps=nps,
            dept_label="Suporte Técnico",
            contact_reason="Problemas técnicos",
            occurrence="Pedal"
        )
        return self.aggregator.process_conversation(raw)

    def test_aggregate_monthly_breakdown_empty(self):
        result = self.aggregator.aggregate_monthly_breakdown({})
        self.assertEqual(result, [])

    def test_aggregate_monthly_breakdown_single_month(self):
        data = {
            "2024-01": [
                self._make_conversation("1", "Agent A", rating=5, nps=9),
                self._make_conversation("2", "Agent A", rating=4, nps=8),
            ]
        }
        result = self.aggregator.aggregate_monthly_breakdown(data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["month"], "2024-01")
        self.assertEqual(result[0]["total_chats"], 2)
        self.assertEqual(result[0]["compliments"], 2)
        self.assertEqual(result[0]["negatives"], 0)

    def test_aggregate_monthly_breakdown_multiple_months(self):
        data = {
            "2024-01": [
                self._make_conversation("1", "Agent A", rating=5, nps=9),
            ],
            "2024-02": [
                self._make_conversation("2", "Agent A", rating=2, nps=4),
                self._make_conversation("3", "Agent A", rating=3, nps=6),
            ],
            "2024-03": [],
        }
        result = self.aggregator.aggregate_monthly_breakdown(data)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["month"], "2024-01")
        self.assertEqual(result[0]["total_chats"], 1)
        self.assertEqual(result[1]["month"], "2024-02")
        self.assertEqual(result[1]["total_chats"], 2)
        self.assertEqual(result[1]["negatives"], 1)
        self.assertEqual(result[2]["month"], "2024-03")
        self.assertEqual(result[2]["total_chats"], 0)

    def test_aggregate_monthly_breakdown_sorted_order(self):
        data = {
            "2024-03": [self._make_conversation("1", "A")],
            "2024-01": [self._make_conversation("2", "B")],
            "2024-02": [self._make_conversation("3", "C")],
        }
        result = self.aggregator.aggregate_monthly_breakdown(data)
        months = [entry["month"] for entry in result]
        self.assertEqual(months, ["2024-01", "2024-02", "2024-03"])

    def test_aggregate_monthly_breakdown_all_kpi_fields(self):
        data = {
            "2024-06": [
                self._make_conversation("1", "Agent A", rating=5, nps=9, msg_count=5),
            ]
        }
        result = self.aggregator.aggregate_monthly_breakdown(data)
        entry = result[0]
        expected_keys = {
            "month", "total_chats", "total_msgs", "avg_art", "avg_duration",
            "real_nps", "sla_compliance", "avg_rating", "compliments",
            "negatives", "unique_clients", "returners",
        }
        self.assertSetEqual(set(entry.keys()), expected_keys)


if __name__ == "__main__":
    unittest.main()
