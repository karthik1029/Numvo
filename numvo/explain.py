from __future__ import annotations

from numvo.models import ProviderResult


def _freshness_penalty(metadata: dict) -> int:
    freshness = str(metadata.get("data_freshness", "UNKNOWN")).upper()
    if freshness == "STALE":
        return 10
    if freshness == "VERY_STALE":
        return 25
    return 0


def confidence_score(results: list[ProviderResult]) -> int:
    reputation = [
        result
        for result in results
        if result.category == "spam_reputation" and "error" not in (result.metadata or {})
    ]
    if not reputation:
        return 0

    score = min(len(reputation) * 25, 50)
    strong_sources = 0

    for result in reputation:
        metadata = result.metadata or {}

        if result.provider == "ftc_dnc":
            total = int(metadata.get("complaint_count", result.spam_reports or 0))
            recent_30 = int(metadata.get("recent_30d", 0))
            if total >= 10 or recent_30 >= 3:
                strong_sources += 1
                score += 15
            elif total > 0:
                score += 5
            score -= _freshness_penalty(metadata)

        elif result.provider == "ipqs":
            fraud_score = int(metadata.get("fraud_score", 0))
            if fraud_score >= 85 or metadata.get("recent_abuse") or metadata.get("spammer"):
                strong_sources += 1
                score += 15
            elif fraud_score >= 70:
                score += 5

        else:
            if result.spam_reports >= 10 or result.confidence >= 0.85:
                strong_sources += 1
                score += 15
            elif result.spam_reports > 0 or result.confidence >= 0.5:
                score += 5
            score -= _freshness_penalty(metadata)

    if strong_sources >= 2:
        score += 20

    return max(0, min(score, 100))


def confidence_label(score: int) -> str:
    if score >= 80:
        return "HIGH"
    if score >= 50:
        return "MEDIUM"
    if score >= 20:
        return "LOW"
    return "VERY_LOW"


def _append_freshness_reason(reasons: list[str], provider_name: str, metadata: dict) -> None:
    age = metadata.get("data_age_days")
    refreshed = metadata.get("last_successful_refresh")
    freshness = metadata.get("data_freshness")

    if age is not None:
        day_word = "day" if age == 1 else "days"
        reasons.append(f"{provider_name} data freshness: {age} {day_word} old ({freshness})")
    if refreshed:
        reasons.append(f"{provider_name} last successful refresh: {str(refreshed)[:10]}")


def evidence_reasons(results: list[ProviderResult]) -> list[str]:
    reasons: list[str] = []
    strong_reputation_sources = 0

    for result in results:
        metadata = result.metadata or {}

        if "error" in metadata:
            reasons.append(f"{result.provider} lookup unavailable: {metadata['error']}")
            continue

        if result.provider == "ftc_dnc":
            total = int(metadata.get("complaint_count", result.spam_reports or 0))
            recent_30 = int(metadata.get("recent_30d", 0))
            recent_90 = int(metadata.get("recent_90d", 0))
            robocall_count = int(metadata.get("robocall_count", 0))
            robocall_ratio = float(metadata.get("robocall_ratio", 0.0))

            if total > 0:
                suffix = "s" if total != 1 else ""
                reasons.append(f"FTC complaint history: {total} report{suffix}")
            if recent_30 > 0:
                suffix = "s" if recent_30 != 1 else ""
                reasons.append(f"{recent_30} FTC complaint{suffix} in the last 30 days")
            elif recent_90 > 0:
                suffix = "s" if recent_90 != 1 else ""
                reasons.append(f"{recent_90} FTC complaint{suffix} in the last 90 days")
            if robocall_count > 0 and total > 0:
                reasons.append(f"{round(robocall_ratio * 100)}% of FTC reports were robocall-related")
            if total >= 10 or recent_30 >= 3:
                strong_reputation_sources += 1

            _append_freshness_reason(reasons, "FTC", metadata)

        elif result.provider == "ipqs":
            fraud_score = int(metadata.get("fraud_score", 0))
            if fraud_score:
                reasons.append(f"IPQS fraud score: {fraud_score}/100")
            if metadata.get("spammer"):
                reasons.append("IPQS identifies the number as a spammer")
            if metadata.get("recent_abuse"):
                reasons.append("IPQS reports recent abuse activity")
            if metadata.get("risky"):
                reasons.append("IPQS marks the number as risky")
            if fraud_score >= 85 or metadata.get("recent_abuse") or metadata.get("spammer"):
                strong_reputation_sources += 1

        elif result.category == "spam_reputation":
            if result.spam_reports > 0:
                suffix = "s" if result.spam_reports != 1 else ""
                reasons.append(
                    f"{result.provider} reports {result.spam_reports} spam report{suffix}"
                )
            elif result.confidence > 0:
                reasons.append(
                    f"{result.provider} returned a spam-reputation signal with confidence {result.confidence:.2f}"
                )

            if result.spam_reports >= 10 or result.confidence >= 0.85:
                strong_reputation_sources += 1

            _append_freshness_reason(reasons, result.provider, metadata)

    if strong_reputation_sources >= 2:
        reasons.append("Two independent reputation sources show strong risk signals")

    if not reasons:
        reasons.append("No strong spam evidence was found in the available reputation sources")

    return reasons
