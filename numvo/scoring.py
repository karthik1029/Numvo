from numvo.models import ProviderResult


def calculate_spam_score(results: list[ProviderResult]) -> int:
    if not results:
        return 0

    weighted = 0.0
    total_confidence = 0.0

    for result in results:
        confidence = max(0.0, min(1.0, result.confidence))
        signal = min(result.spam_reports * 10, 100)
        weighted += signal * confidence
        total_confidence += confidence

    if total_confidence == 0:
        return 0

    return round(weighted / total_confidence)


def risk_label(score: int) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 35:
        return "MEDIUM"
    return "LOW"
