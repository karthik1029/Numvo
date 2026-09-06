from __future__ import annotations

import argparse

from numvo.providers.ftc import FTCComplaintIndex


def main() -> None:
    parser = argparse.ArgumentParser(description="Index an FTC Do Not Call complaint CSV for Numvo.")
    parser.add_argument("csv_path", help="Path to an FTC complaint CSV file")
    parser.add_argument(
        "--db",
        default="data/ftc_complaints.sqlite3",
        help="SQLite database path (default: data/ftc_complaints.sqlite3)",
    )
    args = parser.parse_args()

    index = FTCComplaintIndex(args.db)
    inserted = index.ingest_csv(args.csv_path)
    print(f"Indexed {inserted} new FTC complaint rows into {args.db}")


if __name__ == "__main__":
    main()
