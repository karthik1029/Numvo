from datetime import datetime, timezone
from pathlib import Path

from numvo.models import ProviderResult
from numvo.providers.ftc import FTCComplaintIndex, FTCComplaintProvider
from numvo.scoring import calculate_spam_score


def test_ftc_index_and_provider(tmp_path: Path):
    csv_path = tmp_path / "ftc.csv"
    csv_path.write_text(
        "CompanyPhoneNumber,CreatedDate,ViolationDate,Subject,RecordedMessageOrRobocall\n"
        "2025550123,2026-09-05T12:00:00Z,2026-09-05,Imposter,Yes\n"
        "2025550123,2026-09-04T12:00:00Z,2026-09-04,Imposter,Yes\n"
        "2025550123,2026-09-03T12:00:00Z,2026-09-03,Telemarketing,No\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "ftc.sqlite3"
    index = FTCComplaintIndex(db_path)
    assert index.ingest_csv(csv_path) == 3

    provider = FTCComplaintProvider(db_path)
    result = provider.lookup("+12025550123")

    assert result.provider == "ftc_dnc"
    assert result.spam_reports == 3
    assert result.metadata["robocall_count"] == 2
    assert result.metadata["top_subjects"][0]["subject"] == "Imposter"


def test_recent_ftc_reports_score_higher_than_old_reports():
    recent = ProviderResult(
        provider="ftc_dnc",
        spam_reports=10,
        confidence=0.9,
        metadata={
            "complaint_count": 10,
            "recent_30d": 10,
            "recent_90d": 10,
            "robocall_ratio": 0.8,
            "report_span_days": 10,
        },
    )
    old = ProviderResult(
        provider="ftc_dnc",
        spam_reports=10,
        confidence=0.9,
        metadata={
            "complaint_count": 10,
            "recent_30d": 0,
            "recent_90d": 0,
            "robocall_ratio": 0.8,
            "report_span_days": 10,
        },
    )

    assert calculate_spam_score([recent]) > calculate_spam_score([old])
