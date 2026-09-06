from numvo import Numvo
from numvo.models import ProviderResult
from numvo.providers.base import PhoneIntelligenceProvider


class FakeProvider(PhoneIntelligenceProvider):
    name = "fake"

    def lookup(self, phone_number: str) -> ProviderResult:
        return ProviderResult(
            provider=self.name,
            spam_reports=8,
            confidence=1.0,
            category="telemarketing",
        )


def test_numvo_normalizes_and_scores():
    result = Numvo([FakeProvider()]).check("202-555-0123")

    assert result.phone_number == "+12025550123"
    assert result.spam_score == 80
    assert result.risk == "HIGH"
    assert result.provider_results[0].provider == "fake"


def test_numvo_handles_no_providers():
    result = Numvo().check("202-555-0123")

    assert result.spam_score == 0
    assert result.risk == "LOW"
