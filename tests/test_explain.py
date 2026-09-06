from numvo.explain import confidence_label, confidence_score, evidence_reasons
from numvo.models import ProviderResult


def test_two_strong_sources_produce_high_confidence():
    results = [
        ProviderResult(
            provider="ftc_dnc",
            confidence=0.95,
            category="spam_reputation",
            metadata={
                "complaint_count": 31,
                "recent_30d": 12,
                "recent_90d": 23,
                "robocall_count": 26,
                "robocall_ratio": 0.839,
            },
        ),
        ProviderResult(
            provider="ipqs",
            confidence=0.95,
            category="spam_reputation",
            metadata={
                "fraud_score": 94,
                "recent_abuse": True,
                "risky": True,
                "spammer": True,
            },
        ),
    ]

    score = confidence_score(results)
    reasons = evidence_reasons(results)

    assert score == 100
    assert confidence_label(score) == "HIGH"
    assert "FTC complaint history: 31 reports" in reasons
    assert "12 FTC complaints in the last 30 days" in reasons
    assert "IPQS fraud score: 94/100" in reasons
    assert "Two independent reputation sources show strong risk signals" in reasons


def test_no_reputation_evidence_is_very_low_confidence():
    results = [
        ProviderResult(
            provider="phonenumbers",
            confidence=1.0,
            category="phone_metadata",
            metadata={"valid": True, "number_type": "MOBILE"},
        )
    ]

    score = confidence_score(results)
    reasons = evidence_reasons(results)

    assert score == 0
    assert confidence_label(score) == "VERY_LOW"
    assert reasons == ["No strong spam evidence was found in the available reputation sources"]
