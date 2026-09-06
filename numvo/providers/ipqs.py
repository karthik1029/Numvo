from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from numvo.models import ProviderResult
from numvo.providers.base import PhoneIntelligenceProvider


class IPQSPhoneReputationProvider(PhoneIntelligenceProvider):
    """Phone reputation provider backed by the IPQualityScore Phone API."""

    name = "ipqs"
    base_url = "https://www.ipqualityscore.com/api/json/phone"

    def __init__(self, api_key: str, *, strictness: int = 1, timeout: float = 5.0):
        if not api_key:
            raise ValueError("IPQS api_key is required")
        if strictness not in {0, 1, 2}:
            raise ValueError("IPQS strictness must be 0, 1, or 2")

        self.api_key = api_key
        self.strictness = strictness
        self.timeout = timeout

    def _build_url(self, phone_number: str) -> str:
        encoded_number = urllib.parse.quote(phone_number, safe="")
        query = urllib.parse.urlencode({"strictness": self.strictness})
        return f"{self.base_url}/{self.api_key}/{encoded_number}?{query}"

    def lookup(self, phone_number: str) -> ProviderResult:
        request = urllib.request.Request(
            self._build_url(phone_number),
            headers={"Accept": "application/json", "User-Agent": "Numvo/0.1"},
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"IPQS HTTP error: {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"IPQS network error: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("IPQS returned invalid JSON") from exc

        if not payload.get("success", False):
            message = payload.get("message") or "IPQS lookup failed"
            raise RuntimeError(str(message))

        fraud_score = int(payload.get("fraud_score") or 0)
        spammer = bool(payload.get("spammer"))
        recent_abuse = bool(payload.get("recent_abuse"))
        risky = bool(payload.get("risky"))

        if fraud_score >= 90 or recent_abuse or spammer:
            confidence = 0.95
        elif fraud_score >= 85 or risky:
            confidence = 0.85
        elif fraud_score >= 75:
            confidence = 0.70
        else:
            confidence = 0.55

        return ProviderResult(
            provider=self.name,
            spam_reports=1 if spammer else 0,
            confidence=confidence,
            category="spam_reputation",
            metadata={
                "fraud_score": fraud_score,
                "recent_abuse": recent_abuse,
                "risky": risky,
                "spammer": spammer,
                "valid": payload.get("valid"),
                "active": payload.get("active"),
                "voip": payload.get("VOIP"),
                "prepaid": payload.get("prepaid"),
                "carrier": payload.get("carrier"),
                "line_type": payload.get("line_type"),
                "country": payload.get("country"),
                "region": payload.get("region"),
                "do_not_call": payload.get("do_not_call"),
                "tcpa_blacklist": payload.get("tcpa_blacklist"),
            },
        )
