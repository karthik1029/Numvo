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


def calculate_spam_score(results: list[ProviderResult]) -> int:
    if not results:
        return 0

    weighted = 0.0
    total_confidence = 0.0

    for result in results:
        confidence = max(0.0, min(1.0, result.confidence))
        if confidence == 0:
            continue

        if result.provider == "ftc_dnc":
            signal = _ftc_signal(result)
        else:
            signal = min(result.spam_reports * 10, 100)

        weighted += signal * confidence
        total_confidence += confidence

    if total_confidence == 0:
        return 0

    return round(weighted / total_confidence)


def risk_label(score: int) -> str:
    if score >= 75:
        return "VERY_HIGH"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "SUSPICIOUS"
    return "LOW"
