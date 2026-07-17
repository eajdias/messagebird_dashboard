import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from infrastructure.exporters.metrics_cache import (
    get_previous_month_key,
    get_year_accumulated,
    load_cache,
    save_cache,
)

CACHE_DATA = {
    "2026-01": {"total_chats": 800, "real_nps": 45.0, "avg_art": 10.5},
    "2026-02": {"total_chats": 850, "real_nps": 48.0, "avg_art": 9.8},
    "2026-03": {"total_chats": 900, "real_nps": 50.0, "avg_art": 9.5},
}


import infrastructure.exporters.metrics_cache as mc  # noqa: E402


class TestMetricsCache(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cache_file = mc.CACHE_FILE
        self.cache_path = os.path.join(self.tmpdir, "_metrics_cache.json")
        mc.CACHE_FILE = self.cache_path

    def tearDown(self):
        mc.CACHE_FILE = self.orig_cache_file

    def _write_cache(self, data):
        with open(self.cache_path, "w") as f:
            json.dump(data, f)

    def test_get_previous_month_key_january(self):
        self.assertEqual(get_previous_month_key(2026, 1), "2025-12")

    def test_get_previous_month_key_march(self):
        self.assertEqual(get_previous_month_key(2026, 3), "2026-02")

    def test_get_previous_month_key_december(self):
        self.assertEqual(get_previous_month_key(2026, 12), "2026-11")

    def test_get_previous_month_key_january_2027(self):
        self.assertEqual(get_previous_month_key(2027, 1), "2026-12")

    def test_load_cache_file_not_found(self):
        result = load_cache()
        self.assertEqual(result, {})

    def test_save_and_load(self):
        save_cache(CACHE_DATA)
        loaded = load_cache()
        self.assertEqual(loaded["2026-01"]["total_chats"], 800)
        self.assertEqual(loaded["2026-03"]["real_nps"], 50.0)

    def test_get_year_accumulated_all_months(self):
        save_cache(CACHE_DATA)
        cache = load_cache()
        acc = get_year_accumulated(cache, 2026, 3)
        self.assertIsNotNone(acc)
        self.assertEqual(acc["total_chats"], 800 + 850 + 900)

    def test_get_year_accumulated_no_data(self):
        save_cache({})
        cache = load_cache()
        acc = get_year_accumulated(cache, 2026, 3)
        self.assertIsNone(acc)

    def test_get_year_accumulated_partial(self):
        save_cache(CACHE_DATA)
        cache = load_cache()
        acc = get_year_accumulated(cache, 2026, 2)
        self.assertIsNotNone(acc)
        self.assertEqual(acc["total_chats"], 800 + 850)


if __name__ == "__main__":
    unittest.main()
