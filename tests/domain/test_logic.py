import unittest
from datetime import datetime

from domain import logic


def calculate_business_duration(start_dt: datetime, end_dt: datetime) -> float:
    if not start_dt or not end_dt or start_dt >= end_dt:
        return 0.0

    delta = (end_dt - start_dt).total_seconds() / 60.0

    from domain.constants import MAX_ART_MINUTES

    if delta > MAX_ART_MINUTES:
        return 0.0

    return delta


class TestLogic(unittest.TestCase):
    def test_calculate_ticket_duration_same_day(self):
        start = "2024-01-01 10:00:00"
        end = "2024-01-01 10:30:00"
        self.assertEqual(logic.calculate_ticket_duration(start, end), 30.0)

    def test_calculate_ticket_duration_multi_day(self):
        start = "2024-01-01 23:50:00"
        end = "2024-01-02 00:10:00"
        self.assertEqual(logic.calculate_ticket_duration(start, end), 20.0)

    def test_calculate_ticket_duration_too_long(self):
        start = "2025-05-06 18:58:28"
        end = "2026-01-28 14:10:57"
        self.assertEqual(logic.calculate_ticket_duration(start, end), 0.0)

    def test_calculate_business_duration_multi_day(self):
        start = datetime(2024, 1, 1, 23, 50, 0)
        end = datetime(2024, 1, 2, 0, 10, 0)
        self.assertEqual(calculate_business_duration(start, end), 20.0)


if __name__ == "__main__":
    unittest.main()
