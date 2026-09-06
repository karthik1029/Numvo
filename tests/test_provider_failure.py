from numvo import Numvo
from numvo.providers.base import PhoneIntelligenceProvider


class BrokenProvider(PhoneIntelligenceProvider):
    name = "broken"

    def lookup(self, phone_number: str):
        raise RuntimeError("provider unavailable")


def test_provider_failure_does_not_crash_check():
    result = Numvo([BrokenProvider()]).check("202-555-0123")

    assert result.spam_score == 0
    assert result.risk == "LOW"
    assert result.provider_results[0].provider == "broken"
    assert result.provider_results[0].metadata["error"] == "provider unavailable"
