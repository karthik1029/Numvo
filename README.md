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
 ┌──────────────┐
 │ Providers    │
 │ Reputation   │
 │ Metadata     │
 │ Web signals  │
 └──────────────┘
       ↓
Normalize → aggregate → score → explain
```

## V1 goals

- Normalize phone numbers
- Query pluggable providers
- Combine provider results
- Calculate a spam-risk score
- Return a structured explanation
- Expose the service through MCP

## Development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
pytest
```

## Status

Early development.
