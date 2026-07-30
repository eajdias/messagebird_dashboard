import os
from datetime import datetime, timedelta
from typing import Any

# Business logic for time handling (Canonical)
# Lido do .env (MESSAGEBIRD_TIMEZONE_OFFSET); default -3 (Brasília) para compatibilidade.
TIMEZONE_OFFSET = float(os.getenv("MESSAGEBIRD_TIMEZONE_OFFSET", "-3"))


def parse_datetime(dt_string: str | None, apply_offset: bool = False) -> datetime | None:
    """Parse datetime string without try/except loops for better performance.

    Detects format by string inspection instead of exception handling.
    """
    if not dt_string:
        return None

    dt = None
    s = str(dt_string)

    if "T" in s:
        clean = s.replace("Z", "").split(".")[0]
        dt = datetime.strptime(clean, "%Y-%m-%dT%H:%M:%S")
    elif len(s) >= 19 and s[4] == "-" and s[10] == " " and s[13] == ":" and s[16] == ":":
        dt = datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
    elif len(s) >= 10 and s[4] == "-" and s[7] == "-":
        dt = datetime.strptime(s[:10], "%Y-%m-%d")
        dt = dt.replace(hour=23, minute=59, second=59)
    else:
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    if dt is None:
        return None

    if apply_offset:
        dt += timedelta(hours=TIMEZONE_OFFSET)
    return dt.replace(tzinfo=None)


def local_date_bounds(start_date_str: str, end_date_str: str) -> tuple[datetime, datetime]:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            start_dt = datetime.strptime(start_date_str, fmt)
            end_dt = datetime.strptime(end_date_str, fmt).replace(hour=23, minute=59, second=59)
            return start_dt, end_dt
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {start_date_str} or {end_date_str}. Use YYYY-MM-DD or DD/MM/YYYY")


def to_utc_string(dt: datetime) -> str:
    utc_dt = dt - timedelta(hours=TIMEZONE_OFFSET)
    return utc_dt.strftime("%Y-%m-%d %H:%M:%S")


def get_utc_range(start_date: str, end_date: str) -> tuple[str, str]:
    start_dt, end_dt = local_date_bounds(start_date, end_date)
    return to_utc_string(start_dt), to_utc_string(end_dt)


def format_local_dt(dt_string: str | None) -> str | None:
    dt = parse_datetime(dt_string, apply_offset=True)
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None


def _get_val(obj, keys, default=None):
    if hasattr(obj, "keys"):
        for key in keys:
            try:
                return obj[key]
            except KeyError, IndexError:
                pass
    else:
        for key in keys:
            val = getattr(obj, key, None)
            if val is not None:
                return val
    return default


def _get_datetime(obj, keys, apply_offset=True):
    val = _get_val(obj, keys)
    return parse_datetime(val, apply_offset=apply_offset)


def calculate_ticket_duration(created_at: str, updated_at: str) -> float:
    """Calculates minutes from ticket open to ticket close."""
    c_dt = parse_datetime(created_at, apply_offset=True)
    u_dt = parse_datetime(updated_at, apply_offset=True)
    if c_dt and u_dt:
        if c_dt >= u_dt:
            return 0.0
        delta = (u_dt - c_dt).total_seconds() / 60.0
        from domain.constants import MAX_DURATION_MINUTES

        if delta > MAX_DURATION_MINUTES:
            return 0.0
        return delta
    return 0.0


def get_effective_start_time(messages: list[Any], default_start: str) -> str:
    """
    Finds the start of the current activity episode:
    - Detects reopen gaps (inactivity >= REOPEN_GAP_HOURS) and focuses on the latest episode.
    - Within that episode, finds the last customer message before the first agent response.
    """
    if not messages:
        return default_start

    from domain.constants import REOPEN_GAP_HOURS

    gap_threshold = REOPEN_GAP_HOURS * 3600
    last_gap_idx = -1

    for i in range(1, len(messages)):
        prev = _get_val(messages[i - 1], ("msgs_created", "created"))
        curr = _get_val(messages[i], ("msgs_created", "created"))
        prev_dt = parse_datetime(prev)
        curr_dt = parse_datetime(curr)
        if prev_dt and curr_dt and (curr_dt - prev_dt).total_seconds() >= gap_threshold:
            last_gap_idx = i

    active_msgs = messages[last_gap_idx:] if last_gap_idx >= 0 else messages

    first_agent_msg_time = None
    for m in active_msgs:
        direction = _get_val(m, ("msgs_direction", "direction"))
        agent_id = _get_val(m, ("msgs_agnt", "agent_id"))
        created = _get_val(m, ("msgs_created", "created"))

        if direction == "sent" and agent_id is not None:
            first_agent_msg_time = created
            break

    if not first_agent_msg_time:
        return default_start

    last_customer_msg_time = None
    for m in active_msgs:
        direction = _get_val(m, ("msgs_direction", "direction"))
        created = _get_val(m, ("msgs_created", "created"))

        if direction == "received" and created <= first_agent_msg_time:
            if not last_customer_msg_time or created > last_customer_msg_time:
                last_customer_msg_time = created
        elif created > first_agent_msg_time:
            break

    return last_customer_msg_time or default_start
