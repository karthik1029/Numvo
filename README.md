# Numvo

Phone number intelligence and spam-risk detection built with a reusable Python orchestration layer and MCP.

## Architecture

```text
Client / MCP Host
       ↓
    MCP adapter
       ↓
 Numvo service
       ↓
 ┌──────────────────────┐
 │ PhoneNumbersProvider │  metadata / validity
 │ FTCComplaintProvider │  complaint reputation
 └──────────────────────┘
       ↓
Normalize → aggregate → score → explain
```

## What Numvo uses today

### Phone metadata

`phonenumbers` provides number validity, region, carrier information when available, and number type.

### FTC complaint reputation

Numvo can ingest the FTC Do Not Call complaint CSV data into a local SQLite index. Lookups are then performed by exact phone number without downloading complaint data during every request.

The FTC data is consumer-submitted complaint evidence. Numvo treats it as a signal, not absolute proof that a number is malicious.

## Spam scoring

FTC complaint scoring considers:

- total complaint count
- complaints in the last 30 and 90 days
- robocall ratio
- whether complaints span multiple dates

Recent repeated complaints carry more weight than isolated old complaints.

Risk labels are:

```text
0-24   LOW
25-49  SUSPICIOUS
50-74  HIGH
75-100 VERY_HIGH
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
pytest
```

## Index FTC complaint data

Download an FTC Do Not Call complaint CSV, then run:

```bash
python scripts/ingest_ftc_csv.py path/to/complaints.csv
```

By default Numvo stores the index at:

```text
data/ftc_complaints.sqlite3
```

You can choose another database path:

```bash
python scripts/ingest_ftc_csv.py complaints.csv --db data/my_ftc.sqlite3
```

The ingest process uses `INSERT OR IGNORE`, so re-ingesting overlapping FTC files does not duplicate identical complaint rows.

## MCP tools

The server exposes:

```text
check_phone_number(phone_number)
normalize_number(phone_number)
```

`check_phone_number()` combines real phone metadata and locally indexed FTC complaint signals.

## Status

Early development. The next major step is adding another independent reputation source so Numvo can cross-check FTC complaints instead of relying on a single complaint dataset.
