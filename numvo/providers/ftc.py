from __future__ import annotations

import csv
import re
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from numvo.models import ProviderResult
from numvo.providers.base import PhoneIntelligenceProvider


_PHONE_KEYS = {
    "companyphonenumber",
    "company_phone_number",
    "phonenumber",
    "phone_number",
    "number",
}
_CREATED_KEYS = {"createddate", "created_date"}
_VIOLATION_KEYS = {"violationdate", "violation_date"}
_SUBJECT_KEYS = {"subject"}
_ROBOCALL_KEYS = {
    "recordedmessageorrobocall",
    "recorded_message_or_robocall",
    "isrobocall",
    "is_robocall",
}


def _canonical_key(value: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", value.strip().lower().replace("-", "_"))


def _pick(row: dict[str, str], candidates: set[str]) -> str:
    normalized = {_canonical_key(key): value for key, value in row.items() if key}
    compact_candidates = {candidate.replace("_", "") for candidate in candidates}
    for key, value in normalized.items():
        if key in candidates or key.replace("_", "") in compact_candidates:
            return (value or "").strip()
    return ""


def _us_national_number(phone_number: str) -> str:
    digits = re.sub(r"\D", "", phone_number)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("FTC complaint data currently supports US 10-digit phone numbers")
    return digits


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    cleaned = value.strip().replace("Z", "+00:00")
    for parser in (
        lambda text: datetime.fromisoformat(text),
        lambda text: datetime.strptime(text, "%Y-%m-%d %H:%M:%S"),
        lambda text: datetime.strptime(text, "%m/%d/%Y"),
    ):
        try:
            parsed = parser(cleaned)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


class FTCComplaintIndex:
    """Local SQLite index for public FTC Do Not Call complaint CSV data."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS complaints (
                    phone TEXT NOT NULL,
                    created_date TEXT,
                    violation_date TEXT,
                    subject TEXT,
                    is_robocall INTEGER NOT NULL DEFAULT 0,
                    source_file TEXT NOT NULL,
                    UNIQUE(phone, created_date, violation_date, subject, is_robocall)
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_complaints_phone ON complaints(phone)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_complaints_created ON complaints(created_date)"
            )

    def ingest_csv(self, csv_path: str | Path) -> int:
        csv_path = Path(csv_path)
        inserted = 0

        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle, self._connect() as connection:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError(f"FTC CSV has no header: {csv_path}")

            for row in reader:
                raw_phone = _pick(row, _PHONE_KEYS)
                if not raw_phone:
                    continue
                try:
                    phone = _us_national_number(raw_phone)
                except ValueError:
                    continue

                created = _pick(row, _CREATED_KEYS)
                violation = _pick(row, _VIOLATION_KEYS)
                subject = _pick(row, _SUBJECT_KEYS)
                robocall_raw = _pick(row, _ROBOCALL_KEYS).lower()
                is_robocall = 1 if robocall_raw in {"y", "yes", "true", "1"} else 0

                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO complaints
                    (phone, created_date, violation_date, subject, is_robocall, source_file)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (phone, created, violation, subject, is_robocall, csv_path.name),
                )
                inserted += cursor.rowcount

        return inserted

    def summary(self, phone_number: str, now: datetime | None = None) -> dict:
        phone = _us_national_number(phone_number)
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        cutoff_30 = now - timedelta(days=30)
        cutoff_90 = now - timedelta(days=90)

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT created_date, violation_date, subject, is_robocall
                FROM complaints
                WHERE phone = ?
                ORDER BY created_date DESC
                """,
                (phone,),
            ).fetchall()

        recent_30 = 0
        recent_90 = 0
        robocalls = 0
        dates: list[datetime] = []
        subjects: Counter[str] = Counter()

        for created, violation, subject, is_robocall in rows:
            event_date = _parse_date(created) or _parse_date(violation)
            if event_date:
                dates.append(event_date)
                if event_date >= cutoff_30:
                    recent_30 += 1
                if event_date >= cutoff_90:
                    recent_90 += 1
            if is_robocall:
                robocalls += 1
            if subject:
                subjects[subject] += 1

        total = len(rows)
        robocall_ratio = (robocalls / total) if total else 0.0
        span_days = 0
        if len(dates) >= 2:
            span_days = max(0, (max(dates) - min(dates)).days)

        return {
            "complaint_count": total,
            "recent_30d": recent_30,
            "recent_90d": recent_90,
            "robocall_count": robocalls,
            "robocall_ratio": round(robocall_ratio, 3),
            "report_span_days": span_days,
            "latest_report": max(dates).isoformat() if dates else None,
            "top_subjects": [
                {"subject": subject, "count": count}
                for subject, count in subjects.most_common(3)
            ],
        }


class FTCComplaintProvider(PhoneIntelligenceProvider):
    """Exact-number reputation signal from locally indexed FTC complaints."""

    name = "ftc_dnc"

    def __init__(self, db_path: str | Path):
        self.index = FTCComplaintIndex(db_path)

    def lookup(self, phone_number: str) -> ProviderResult:
        summary = self.index.summary(phone_number)
        total = summary["complaint_count"]
        recent = summary["recent_90d"]

        if total == 0:
            confidence = 0.0
        elif total == 1:
            confidence = 0.35
        elif recent >= 10 or total >= 25:
            confidence = 0.95
        elif recent >= 3 or total >= 10:
            confidence = 0.8
        else:
            confidence = 0.6

        return ProviderResult(
            provider=self.name,
            spam_reports=total,
            confidence=confidence,
            category="spam_reputation",
            metadata=summary,
        )
