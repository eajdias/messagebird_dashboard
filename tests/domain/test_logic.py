import unittest

from domain import logic


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
        # 8 months later
        start = "2025-05-06 18:58:28"
        end = "2026-01-28 14:10:57"
        # Should be 0.0 because it exceeds MAX_DURATION_MINUTES (630)
        self.assertEqual(logic.calculate_ticket_duration(start, end), 0.0)

    def test_calculate_business_duration_multi_day(self):
        from datetime import datetime

        start = datetime(2024, 1, 1, 23, 50, 0)
        end = datetime(2024, 1, 2, 0, 10, 0)
        self.assertEqual(logic.calculate_business_duration(start, end), 20.0)


if __name__ == "__main__":
    unittest.main()
