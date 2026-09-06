from numvo.models import ProviderResult
from numvo.providers.base import PhoneIntelligenceProvider


class MockReputationProvider(PhoneIntelligenceProvider):
    name = "mock-reputation"

    def lookup(self, phone_number: str) -> ProviderResult:
        last_digit = int(phone_number[-1])
        reports = last_digit
        confidence = 0.8 if reports else 0.5
        category = "spam" if reports >= 5 else None

        return ProviderResult(
            provider=self.name,
            spam_reports=reports,
            confidence=confidence,
            category=category,
        )
