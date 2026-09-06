from numvo.models import ProviderResult
from numvo.scoring import calculate_spam_score


def test_two_strong_reputation_sources_get_agreement_boost():
    ftc = ProviderResult(
        provider="ftc_dnc",
        confidence=0.95,
        category="spam_reputation",
        metadata={
            "complaint_count": 30,
            "recent_30d": 12,
            "recent_90d": 20,
            "robocall_ratio": 0.8,
            "report_span_days": 60,
        },
    )
    ipqs = ProviderResult(
        provider="ipqs",
        confidence=0.95,
        category="spam_reputation",
        metadata={
            "fraud_score": 92,
            "spammer": True,
            "recent_abuse": True,
            "risky": True,
        },
    )

    score = calculate_spam_score([ftc, ipqs])

    assert score >= 90


def test_metadata_only_does_not_create_spam_score():
    metadata = ProviderResult(
        provider="phonenumbers",
        confidence=1.0,
        category="phone_metadata",
        spam_reports=0,
        metadata={"valid": True, "number_type": "VOIP"},
    )

    assert calculate_spam_score([metadata]) == 0
