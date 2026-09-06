from datetime import date
from pathlib import Path

from numvo.ftc_refresh import FTCRefresher


def test_refresh_recent_validates_days(tmp_path: Path):
    refresher = FTCRefresher(tmp_path / "ftc.sqlite3", download_dir=tmp_path / "downloads")

    try:
        refresher.refresh_recent(0, end_date=date(2026, 9, 6))
    except ValueError as exc:
        assert "days must be at least 1" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_existing_download_is_reingested_without_duplicate_rows(tmp_path: Path):
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    day = date(2026, 9, 5)
    csv_path = download_dir / f"DNC_Complaint_Numbers_{day.isoformat()}.csv"
    csv_path.write_text(
        "CompanyPhoneNumber,CreatedDate,ViolationDate,Subject,RecordedMessageOrRobocall\n"
        "2025550123,2026-09-05,2026-09-05,Robocall,Yes\n",
        encoding="utf-8",
    )

    refresher = FTCRefresher(tmp_path / "ftc.sqlite3", download_dir=download_dir)

    first = refresher.refresh_day(day)
    second = refresher.refresh_day(day)

    assert first.inserted == 1
    assert second.inserted == 0
    assert first.status == "ok"
    assert second.status == "ok"
