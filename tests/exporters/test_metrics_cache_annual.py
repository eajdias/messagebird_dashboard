import unittest

from infrastructure.exporters.metrics_cache import (
    get_all_years_from_cache,
    get_annual_monthly_breakdown,
)


class TestAnnualMetricsCache(unittest.TestCase):
    def setUp(self):
        self.cache = {
            "2024-01": {"total_chats": 100, "real_nps": 70, "avg_art": 15.0},
            "2024-02": {"total_chats": 120, "real_nps": 72, "avg_art": 14.5},
            "2024-03": {"total_chats": 90, "real_nps": 68, "avg_art": 16.0},
            "2023-01": {"total_chats": 80, "real_nps": 65, "avg_art": 18.0},
            "2023-02": {"total_chats": 95, "real_nps": 67, "avg_art": 17.0},
            "some_other_key": "not_a_month",
        }

    def test_get_annual_monthly_breakdown_full_year(self):
        result = get_annual_monthly_breakdown(self.cache, 2024)
        self.assertEqual(len(result), 12)
        self.assertEqual(result[0]["month"], "2024-01")
        self.assertEqual(result[0]["total_chats"], 100)
        self.assertEqual(result[0]["real_nps"], 70)
        self.assertEqual(result[1]["month"], "2024-02")
        self.assertEqual(result[1]["total_chats"], 120)
        self.assertEqual(result[2]["month"], "2024-03")
        self.assertEqual(result[2]["total_chats"], 90)

    def test_get_annual_monthly_breakdown_missing_months(self):
        result = get_annual_monthly_breakdown(self.cache, 2024)
        for i in range(3, 12):
            entry = result[i]
            self.assertEqual(entry["month"], f"2024-{i+1:02d}")
            self.assertNotIn("total_chats", entry)

    def test_get_annual_monthly_breakdown_no_data_year(self):
        result = get_annual_monthly_breakdown(self.cache, 2025)
        self.assertEqual(len(result), 12)
        for entry in result:
            self.assertNotIn("total_chats", entry)

    def test_get_annual_monthly_breakdown_empty_cache(self):
        result = get_annual_monthly_breakdown({}, 2024)
        self.assertEqual(len(result), 12)
        for entry in result:
            self.assertNotIn("total_chats", entry)

    def test_get_all_years_from_cache(self):
        result = get_all_years_from_cache(self.cache)
        self.assertEqual(result, ["2023", "2024"])

    def test_get_all_years_from_cache_empty(self):
        result = get_all_years_from_cache({})
        self.assertEqual(result, [])

    def test_get_all_years_from_cache_no_month_keys(self):
        cache = {"annual": 123, "total": 456}
        result = get_all_years_from_cache(cache)
        self.assertEqual(result, [])

    def test_breakdown_includes_all_kpis_when_present(self):
        cache = {
            "2024-06": {
                "total_chats": 150, "total_msgs": 3000, "avg_art": 12.5,
                "avg_duration": 25.0, "real_nps": 75, "sla_compliance": 92.0,
                "avg_rating": 4.2, "compliments": 120, "negatives": 10,
                "unique_clients": 80, "returners": 70,
            }
        }
        result = get_annual_monthly_breakdown(cache, 2024)
        june = result[5]
        self.assertEqual(june["total_chats"], 150)
        self.assertEqual(june["total_msgs"], 3000)
        self.assertEqual(june["avg_art"], 12.5)
        self.assertEqual(june["avg_duration"], 25.0)
        self.assertEqual(june["real_nps"], 75)
        self.assertEqual(june["sla_compliance"], 92.0)
        self.assertEqual(june["avg_rating"], 4.2)
        self.assertEqual(june["compliments"], 120)
        self.assertEqual(june["negatives"], 10)
        self.assertEqual(june["unique_clients"], 80)
        self.assertEqual(june["returners"], 70)


if __name__ == "__main__":
    unittest.main()
