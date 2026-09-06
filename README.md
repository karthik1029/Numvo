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

## Confidence and explanations

Every Numvo result separates **risk** from **confidence**.

- `spam_score` answers: how suspicious does the available evidence look?
- `confidence_score` answers: how much independent reputation evidence supports that conclusion?

Confidence labels are:

```text
0-19   VERY_LOW
20-49  LOW
50-79  MEDIUM
80-100 HIGH
```

The result also includes human-readable `reasons`, for example:

```text
FTC complaint history: 31 reports
12 FTC complaints in the last 30 days
84% of FTC reports were robocall-related
IPQS fraud score: 94/100
IPQS identifies the number as a spammer
IPQS reports recent abuse activity
Two independent reputation sources show strong risk signals
```

This is intentionally explainable: a high risk score with very low confidence should be treated differently from a high risk score confirmed by multiple independent sources.

## Development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
pytest
```

## Automatic FTC refresh

Numvo can now check recent FTC daily complaint files automatically and ingest any published rows into the local SQLite index.

Refresh the most recent 7 calendar days:

```bash
python scripts/refresh_ftc.py
```

Or choose a wider window:

```bash
python scripts/refresh_ftc.py --days 30
```

Numvo checks each date in the requested window. If the FTC has no file for a date, such as a weekend or non-published day, it records `not_published` and continues.

Downloaded files are cached under:

```text
data/ftc_daily/
```

The SQLite index is stored at:

```text
data/ftc_complaints.sqlite3
```

The refresh is safe to rerun: downloaded CSVs are reused and `INSERT OR IGNORE` prevents identical complaint rows from being duplicated.

You can still ingest a local FTC CSV manually:

```bash
python scripts/ingest_ftc_csv.py path/to/complaints.csv
```

## MCP tools

The server exposes:

```text
check_phone_number(phone_number)
normalize_number(phone_number)
```

`check_phone_number()` combines phone metadata, locally indexed FTC complaint evidence, and IPQS reputation when configured, then returns risk, confidence, reasons, and raw provider signals.

## Status

Early development. Numvo now supports multi-source spam-risk cross-validation, explicit evidence confidence, human-readable explanations, and automatic FTC complaint-data refresh.
