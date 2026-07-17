import unittest

from application.services.report_aggregator import ReportAggregator
from domain.entities.report_data import RawConversationData, RawMessageData
from domain.metrics.art import ARTCalculator
from domain.metrics.duration import DurationCalculator
from domain.metrics.frt import FRTCalculator


class TestReportFlow(unittest.TestCase):
    def setUp(self):
        self.aggregator = ReportAggregator(strategies=[
            FRTCalculator(),
            DurationCalculator(),
            ARTCalculator()
        ])

    def _make_conversation(self, cid: str, agent: str, rating: int = None, nps: int = None,
                           phone: str = "5511999999999", msg_count: int = 3,
                           created: str = "2024-03-01 10:00:00",
                           updated: str = "2024-03-01 10:30:00",
                           dept_label: str = "Suporte Técnico",
                           contact_reason: str = "Problemas técnicos",
                           occurrence: str = "Pedal") -> RawConversationData:
        msgs = [RawMessageData(created, "received", None, agent)]
        for i in range(msg_count):
            msgs.append(RawMessageData(
                f"2024-03-01 10:{i+1:02d}:00", "sent", "1", agent
            ))
        return RawConversationData(
            id=cid,
            contact="Test Client",
            phone=phone,
            start_time=created,
            end_time=updated,
            queue_time=None,
            raw_created=created,
            raw_updated=updated,
            msgs=msgs,
            metadata={"agent_name": agent},
            rating=rating,
            nps=nps,
            dept_label=dept_label,
            contact_reason=contact_reason,
            occurrence=occurrence
        )

    def test_full_pipeline_single_agent(self):
        conversations = [
            self._make_conversation("1", "Agent A", rating=5, nps=9, msg_count=3),
            self._make_conversation("2", "Agent A", rating=4, nps=8, msg_count=5),
            self._make_conversation("3", "Agent A", rating=2, nps=6, msg_count=2),
        ]

        # process_all -> agregacao -> linhas Excel
        processed = self.aggregator.process_all(conversations)
        self.assertEqual(len(processed), 3)

        stats = self.aggregator.aggregate_statistics(processed)
        self.assertEqual(stats["total_chats"], 3)
        # total_msgs = sum of all messages (received + sent) across conversations
        self.assertEqual(stats["total_msgs"], 13)
        self.assertEqual(stats["compliments"], 2)
        self.assertEqual(stats["negatives"], 1)

        rows = self.aggregator.build_excel_rows(processed, report_type="agents")
        # First row = global summary, second = agent row
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][2], "TOTAIS")
        self.assertEqual(rows[1][2], "Agent A")

    def test_full_pipeline_multiple_agents(self):
        conversations = [
            self._make_conversation("1", "Agent A", rating=5, msg_count=3),
            self._make_conversation("2", "Agent B", rating=3, msg_count=1),
            self._make_conversation("3", "Agent A", rating=4, msg_count=6),
        ]

        processed = self.aggregator.process_all(conversations)
        rows = self.aggregator.build_excel_rows(processed, report_type="agents")

        # Global + 2 agents
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0][2], "TOTAIS")

    def test_groups_report(self):
        conversations = [
            self._make_conversation("1", "Agent A", rating=5),
            self._make_conversation("2", "Agent B", rating=3),
        ]
        processed = self.aggregator.process_all(conversations)
        rows = self.aggregator.build_excel_rows(processed, report_type="groups")
        self.assertGreater(len(rows), 0)

    def test_empty_data(self):
        processed = self.aggregator.process_all([])
        self.assertEqual(len(processed), 0)
        stats = self.aggregator.aggregate_statistics(processed)
        self.assertEqual(stats["total_chats"], 0)
        self.assertIsNone(stats["avg_rating"])

    def test_departments_report(self):
        conversations = [
            self._make_conversation("1", "Agent A", rating=5, dept_label="Suporte Técnico"),
            self._make_conversation("2", "Agent B", rating=3, dept_label="Financeiro"),
        ]
        processed = self.aggregator.process_all(conversations)
        rows = self.aggregator.build_excel_rows(processed, report_type="departments")
        self.assertEqual(len(rows), 2)

    def test_aggregate_dashboard(self):
        conversations = [
            self._make_conversation("1", "Agent A", rating=5, nps=10, created="2024-03-01 10:00:00"),
            self._make_conversation("2", "Agent B", rating=3, nps=7, created="2024-03-02 14:00:00"),
        ]
        processed = self.aggregator.process_all(conversations)
        dto = self.aggregator.aggregate_dashboard(processed, "Title", "2024-03-01", "2024-03-31")

        self.assertEqual(dto.title, "Title")
        self.assertEqual(dto.general_metrics["total_chats"], 2)
        self.assertEqual(dto.nps_distribution["promoters"], 1)
        self.assertEqual(dto.nps_distribution["passives"], 1)
        self.assertEqual(dto.rating_distribution["5"], 1)
        self.assertEqual(dto.rating_distribution["3"], 1)
        self.assertEqual(len(dto.heatmap_data), 2)
        self.assertGreater(len(dto.topic_data), 0)

if __name__ == "__main__":
    unittest.main()
