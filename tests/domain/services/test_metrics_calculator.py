import unittest
from datetime import datetime

from domain.services.metrics_calculator import MetricsCalculator


class TestMetricsCalculator(unittest.TestCase):
    def test_nps_calculation(self):
        scores = [10, 9, 8, 7, 6, 5]
        # Promotores (10, 9): 2, Detratores (6, 5): 2, Total: 6
        # NPS: (2 - 2) / 6 = 0.0
        self.assertEqual(MetricsCalculator.calculate_nps(scores), 0.0)

    def test_nps_empty(self):
        self.assertIsNone(MetricsCalculator.calculate_nps([]))

    def test_sla_rate(self):
        arts = [10, 30, 60, 90]  # 3 hits (<=60), 1 miss
        self.assertEqual(MetricsCalculator.calculate_sla_rate(arts), 75.0)

    def test_sla_empty(self):
        self.assertIsNone(MetricsCalculator.calculate_sla_rate([]))

    def test_rating_average(self):
        ratings = [5, 4, 3]
        self.assertEqual(MetricsCalculator.calculate_rating_average(ratings), 4.0)

    def test_frt_calculation(self):
        start = datetime(2024, 1, 1, 10, 0, 0)
        resp = datetime(2024, 1, 1, 10, 30, 0)
        self.assertEqual(MetricsCalculator.calculate_frt(start, resp), 30.0)

    def test_frt_different_days(self):
        start = datetime(2024, 1, 1, 23, 0, 0)
        resp = datetime(2024, 1, 2, 0, 30, 0)
        # Should now be 90 minutes instead of None
        self.assertEqual(MetricsCalculator.calculate_frt(start, resp), 90.0)

    def test_nps_distribution(self):
        scores = [10, 8, 5]
        expected = {"promoters": 1, "passives": 1, "detractors": 1}
        self.assertEqual(MetricsCalculator.calculate_nps_distribution(scores), expected)

    def test_rating_distribution(self):
        values = [5, 5, 4, 3, 2, 1]
        expected = {"5": 2, "4": 1, "3": 1, "2": 1, "1": 1}
        self.assertEqual(MetricsCalculator.calculate_rating_distribution(values), expected)


if __name__ == "__main__":
    unittest.main()
