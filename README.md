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
 │ IPQSProvider         │  fraud / abuse reputation
 └──────────────────────┘
       ↓
Normalize → aggregate → cross-validate → score → explain
```

## What Numvo uses today

### Phone metadata

`phonenumbers` provides number validity, region, carrier information when available, and number type. Metadata alone never makes a number spam.

### FTC complaint reputation

Numvo can ingest the FTC Do Not Call complaint CSV data into a local SQLite index. Lookups are then performed by exact phone number without downloading complaint data during every request.

The FTC data is consumer-submitted complaint evidence. Numvo treats it as a signal, not absolute proof that a number is malicious.

### IPQS reputation

If `IPQS_API_KEY` is configured, Numvo queries IPQualityScore for an independent reputation signal including fraud score, recent abuse, risky/spammer flags, and selected phone attributes.

Set the key before starting the MCP server:

```bash
export IPQS_API_KEY="your-key"
# Windows PowerShell:
# $env:IPQS_API_KEY="your-key"
```

The key is read from the environment and should not be committed to the repository.

## Spam scoring

FTC complaint scoring considers:

- total complaint count
- complaints in the last 30 and 90 days
- robocall ratio
- whether complaints span multiple dates

IPQS contributes its fraud score plus risky, spammer, and recent-abuse signals.

When two independent reputation providers both produce strong evidence, Numvo applies an agreement boost. This makes multi-source confirmation stronger than a single provider result.

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

`check_phone_number()` combines phone metadata, locally indexed FTC complaint evidence, and IPQS reputation when configured.

## Status

Early development. Numvo now supports multi-source spam-risk cross-validation. The next major step is adding an explicit overall evidence-confidence value and clearer human-readable reasons for each score.
