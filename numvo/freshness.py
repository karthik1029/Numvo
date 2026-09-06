from __future__ import annotations

from datetime import date, datetime, timezone


def freshness_label(age_days: int | None) -> str:
    if age_days is None:
        return "UNKNOWN"
    if age_days <= 2:
        return "FRESH"
    if age_days <= 7:
        return "RECENT"
    if age_days <= 30:
        return "STALE"
    return "VERY_STALE"


def source_age_days(source_date: str | None, *, now: datetime | None = None) -> int | None:
    if not source_date:
        return None

    try:
        parsed = date.fromisoformat(source_date)
    except ValueError:
        return None

    today = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).date()
    return max(0, (today - parsed).days)
