from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderResult:
    provider: str
    spam_reports: int = 0
    confidence: float = 0.0
    category: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PhoneCheckResult:
    phone_number: str
    spam_score: int
    risk: str
    provider_results: list[ProviderResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "phone_number": self.phone_number,
            "spam_score": self.spam_score,
            "risk": self.risk,
            "provider_results": [result.__dict__ for result in self.provider_results],
        }
