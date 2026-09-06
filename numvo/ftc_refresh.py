from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from numvo.providers.ftc import FTCComplaintIndex


FTC_DAILY_URL = "https://www.ftc.gov/sites/default/files/DNC_Complaint_Numbers_{date}.csv"


@dataclass
class RefreshResult:
    date: str
    downloaded: bool
    inserted: int
    status: str


class FTCRefresher:
    """Download public FTC daily complaint CSVs and ingest them into SQLite."""

    def __init__(
        self,
        db_path: str | Path,
        *,
        download_dir: str | Path = "data/ftc_daily",
        timeout: float = 15.0,
    ):
        self.index = FTCComplaintIndex(db_path)
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout

    def _url_for(self, day: date) -> str:
        return FTC_DAILY_URL.format(date=day.isoformat())

    def _path_for(self, day: date) -> Path:
        return self.download_dir / f"DNC_Complaint_Numbers_{day.isoformat()}.csv"

    def refresh_day(self, day: date) -> RefreshResult:
        target = self._path_for(day)

        if not target.exists():
            request = urllib.request.Request(
                self._url_for(day),
                headers={"User-Agent": "Numvo/0.2"},
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    target.write_bytes(response.read())
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    return RefreshResult(day.isoformat(), False, 0, "not_published")
                raise RuntimeError(f"FTC download failed with HTTP {exc.code}") from exc
            except urllib.error.URLError as exc:
                raise RuntimeError(f"FTC download failed: {exc.reason}") from exc

        inserted = self.index.ingest_csv(target)
        refreshed_at = datetime.now(timezone.utc).isoformat()
        self.index.set_metadata("last_successful_refresh", refreshed_at)

        current_latest = self.index.get_metadata("latest_source_date")
        if current_latest is None or day.isoformat() > current_latest:
            self.index.set_metadata("latest_source_date", day.isoformat())

        return RefreshResult(day.isoformat(), True, inserted, "ok")

    def refresh_recent(self, days: int = 7, *, end_date: date | None = None) -> list[RefreshResult]:
        if days < 1:
            raise ValueError("days must be at least 1")

        end = end_date or date.today()
        start = end - timedelta(days=days - 1)

        results: list[RefreshResult] = []
        current = start
        while current <= end:
            results.append(self.refresh_day(current))
            current += timedelta(days=1)
        return results
