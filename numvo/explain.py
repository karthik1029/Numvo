from __future__ import annotations

from numvo.models import ProviderResult


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
            total = int(metadata.get("complaint_count", 0))
            recent_30 = int(metadata.get("recent_30d", 0))
            if total >= 10 or recent_30 >= 3:
                strong_sources += 1
                score += 15
            elif total > 0:
                score += 5

        elif result.provider == "ipqs":
            fraud_score = int(metadata.get("fraud_score", 0))
            if fraud_score >= 85 or metadata.get("recent_abuse") or metadata.get("spammer"):
                strong_sources += 1
                score += 15
            elif fraud_score >= 70:
                score += 5

    if strong_sources >= 2:
        score += 20

    return min(score, 100)


def confidence_label(score: int) -> str:
    if score >= 80:
        return "HIGH"
    if score >= 50:
        return "MEDIUM"
    if score >= 20:
        return "LOW"
    return "VERY_LOW"


def evidence_reasons(results: list[ProviderResult]) -> list[str]:
    reasons: list[str] = []
    strong_reputation_sources = 0

    for result in results:
        metadata = result.metadata or {}

        if "error" in metadata:
            reasons.append(f"{result.provider} lookup unavailable: {metadata['error']}")
            continue

        if result.provider == "ftc_dnc":
            total = int(metadata.get("complaint_count", 0))
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

    if strong_reputation_sources >= 2:
        reasons.append("Two independent reputation sources show strong risk signals")

    if not reasons:
        reasons.append("No strong spam evidence was found in the available reputation sources")

    return reasons
