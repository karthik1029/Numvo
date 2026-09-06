from collections.abc import Iterable

from numvo.explain import confidence_label, confidence_score, evidence_reasons
from numvo.models import PhoneCheckResult, ProviderResult
from numvo.normalize import normalize_phone_number
from numvo.providers.base import PhoneIntelligenceProvider
from numvo.scoring import calculate_spam_score, risk_label


class Numvo:
    def __init__(self, providers: Iterable[PhoneIntelligenceProvider] | None = None):
        self.providers = list(providers or [])

    def check(self, phone_number: str) -> PhoneCheckResult:
        normalized = normalize_phone_number(phone_number)
        results: list[ProviderResult] = []

        for provider in self.providers:
            try:
                results.append(provider.lookup(normalized))
            except Exception as exc:
                results.append(
                    ProviderResult(
                        provider=getattr(provider, "name", provider.__class__.__name__),
                        confidence=0.0,
                        metadata={"error": str(exc)},
                    )
                )

        spam_score = calculate_spam_score(results)
        confidence_value = confidence_score(results)

        return PhoneCheckResult(
            phone_number=normalized,
            spam_score=spam_score,
            risk=risk_label(spam_score),
            confidence_score=confidence_value,
            confidence=confidence_label(confidence_value),
            reasons=evidence_reasons(results),
            provider_results=results,
        )
