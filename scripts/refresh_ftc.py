from __future__ import annotations

import argparse
from pathlib import Path

from numvo.ftc_refresh import FTCRefresher


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh Numvo's local FTC complaint index")
    parser.add_argument("--days", type=int, default=7, help="Number of recent calendar days to check")
    parser.add_argument(
        "--db",
        default="data/ftc_complaints.sqlite3",
        help="SQLite database path",
    )
    parser.add_argument(
        "--download-dir",
        default="data/ftc_daily",
        help="Directory for downloaded FTC CSV files",
    )
    args = parser.parse_args()

    refresher = FTCRefresher(Path(args.db), download_dir=Path(args.download_dir))
    results = refresher.refresh_recent(args.days)

    inserted_total = 0
    for result in results:
        inserted_total += result.inserted
        print(
            f"{result.date}: status={result.status} "
            f"downloaded={result.downloaded} inserted={result.inserted}"
        )

    print(f"Inserted {inserted_total} new FTC complaint rows")


if __name__ == "__main__":
    main()
