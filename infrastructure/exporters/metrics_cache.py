import json
import os
import re
from typing import Any

CACHE_FILE = "reports/_metrics_cache.json"


def load_cache() -> dict[str, Any]:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError, OSError:
        return {}


def save_cache(cache: dict[str, Any]):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def get_previous_month_key(year: int, month: int) -> str:
    if month == 1:
        return f"{year - 1}-{12:02d}"
    return f"{year}-{month - 1:02d}"


def get_year_accumulated(cache: dict[str, Any], year: int, upto_month: int) -> dict[str, Any] | None:
    accumulated = {}
    count = 0
    for m in range(1, upto_month + 1):
        key = f"{year}-{m:02d}"
        if key in cache:
            mdata = cache[key]
            for k, v in mdata.items():
                if isinstance(v, (int, float)):
                    accumulated[k] = accumulated.get(k, 0) + v
            count += 1
    if count == 0:
        return None
    for k in list(accumulated.keys()):
        if (k.startswith("avg_") or k.startswith("pct_")) and count > 0:
            accumulated[k] = round(accumulated[k] / count, 2)
    return accumulated


def get_annual_monthly_breakdown(cache: dict[str, Any], year: int) -> list[dict[str, Any]]:
    months = []
    for m in range(1, 13):
        key = f"{year}-{m:02d}"
        if key in cache:
            entry = {"month": key}
            entry.update(cache[key])
            months.append(entry)
        else:
            months.append({"month": key})
    return months


def get_all_years_from_cache(cache: dict[str, Any]) -> list[str]:
    years = set()
    for key in cache:
        if re.match(r"^\d{4}-\d{2}$", key):
            years.add(key[:4])
    return sorted(years)
