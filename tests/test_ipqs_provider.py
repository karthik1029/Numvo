import io
import json

from numvo.providers.ipqs import IPQSPhoneReputationProvider


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_ipqs_provider_maps_reputation_fields(monkeypatch):
    payload = {
        "success": True,
        "fraud_score": 93,
        "spammer": True,
        "recent_abuse": True,
        "risky": True,
        "valid": True,
        "active": True,
        "VOIP": True,
        "carrier": "Example Carrier",
        "line_type": "VOIP",
        "country": "US",
        "region": "Virginia",
        "do_not_call": False,
        "tcpa_blacklist": True,
    }

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout: FakeResponse(payload),
    )

    provider = IPQSPhoneReputationProvider("test-key")
    result = provider.lookup("+12025550123")

    assert result.provider == "ipqs"
    assert result.category == "spam_reputation"
    assert result.confidence == 0.95
    assert result.spam_reports == 1
    assert result.metadata["fraud_score"] == 93
    assert result.metadata["spammer"] is True
    assert result.metadata["recent_abuse"] is True
