from numvo.models import ProviderResult


def _ftc_signal(result: ProviderResult) -> int:
    metadata = result.metadata or {}
    total = int(metadata.get("complaint_count", result.spam_reports or 0))
    recent_30 = int(metadata.get("recent_30d", 0))
    recent_90 = int(metadata.get("recent_90d", 0))
    robocall_ratio = float(metadata.get("robocall_ratio", 0.0))
    span_days = int(metadata.get("report_span_days", 0))

    score = 0

    if total >= 25:
        score += 45
    elif total >= 10:
        score += 35
    elif total >= 3:
        score += 22
    elif total >= 1:
        score += 10

    if recent_30 >= 10:
        score += 25
    elif recent_30 >= 3:
        score += 18
    elif recent_30 >= 1:
        score += 8
    elif recent_90 >= 3:
        score += 10

    if total >= 3 and robocall_ratio >= 0.70:
        score += 15
    elif total >= 3 and robocall_ratio >= 0.40:
        score += 8

    if total >= 3 and span_days >= 30:
        score += 10

    return min(score, 100)


def _ipqs_signal(result: ProviderResult) -> int:
    metadata = result.metadata or {}
    score = int(metadata.get("fraud_score", 0) or 0)

    if metadata.get("spammer"):
        score = max(score, 90)
    if metadata.get("recent_abuse"):
        score = max(score, 90)
    if metadata.get("risky"):
        score = max(score, 85)

    return max(0, min(score, 100))


def calculate_spam_score(results: list[ProviderResult]) -> int:
    if not results:
        return 0

    weighted = 0.0
    total_confidence = 0.0
    reputation_signals: list[int] = []

    for result in results:
        confidence = max(0.0, min(1.0, result.confidence))
        if confidence == 0:
            continue

        if result.provider == "ftc_dnc":
            signal = _ftc_signal(result)
        elif result.provider == "ipqs":
            signal = _ipqs_signal(result)
        else:
            signal = min(result.spam_reports * 10, 100)

        weighted += signal * confidence
        total_confidence += confidence

        if result.category == "spam_reputation" and signal > 0:
            reputation_signals.append(signal)

    if total_confidence == 0:
        return 0

    score = round(weighted / total_confidence)

    # Independent-source agreement is stronger than either source alone.
    if len(reputation_signals) >= 2:
        strong_sources = sum(signal >= 70 for signal in reputation_signals)
        moderate_sources = sum(signal >= 40 for signal in reputation_signals)
        if strong_sources >= 2:
            score += 15
        elif moderate_sources >= 2:
            score += 8

    return min(score, 100)


def risk_label(score: int) -> str:
    if score >= 75:
        return "VERY_HIGH"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "SUSPICIOUS"
    return "LOW"
