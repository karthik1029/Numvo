from datetime import datetime, timezone

from numvo.explain import confidence_label, confidence_score, evidence_reasons
from numvo.freshness import freshness_label, source_age_days
from numvo.models import ProviderResult


def test_freshness_labels():
    assert freshness_label(1) == "FRESH"
    assert freshness_label(5) == "RECENT"
    assert freshness_label(15) == "STALE"
    assert freshness_label(45) == "VERY_STALE"
    assert freshness_label(None) == "UNKNOWN"


def test_source_age_days():
    now = datetime(2026, 9, 6, tzinfo=timezone.utc)
    assert source_age_days("2026-09-05", now=now) == 1


def test_stale_ftc_data_lowers_confidence():
    fresh = ProviderResult(
        provider="ftc_dnc",
        spam_reports=25,
        confidence=0.95,
        category="spam_reputation",
        metadata={
            "complaint_count": 25,
            "recent_30d": 5,
            "data_freshness": "FRESH",
        },
    )
    stale = ProviderResult(
        provider="ftc_dnc",
        spam_reports=25,
        confidence=0.95,
        category="spam_reputation",
        metadata={
            "complaint_count": 25,
            "recent_30d": 5,
            "data_freshness": "VERY_STALE",
        },
    )

    assert confidence_score([stale]) < confidence_score([fresh])


def test_ftc_freshness_is_explained():
    result = ProviderResult(
        provider="ftc_dnc",
        spam_reports=10,
        confidence=0.8,
        category="spam_reputation",
        metadata={
            "complaint_count": 10,
            "recent_30d": 3,
            "data_age_days": 1,
            "data_freshness": "FRESH",
            "last_successful_refresh": "2026-09-05T12:00:00+00:00",
        },
    )

    reasons = evidence_reasons([result])
    assert "FTC data freshness: 1 day old (FRESH)" in reasons
    assert "FTC last successful refresh: 2026-09-05" in reasons


def test_zero_ftc_evidence_has_zero_confidence():
    result = ProviderResult(
        provider="ftc_dnc",
        spam_reports=0,
        confidence=0.0,
        category="spam_reputation",
        metadata={
            "complaint_count": 0,
            "recent_30d": 0,
            "data_age_days": 2,
            "data_freshness": "FRESH",
        },
    )

    assert confidence_score([result]) == 0
    assert confidence_label(confidence_score([result])) == "VERY_LOW"


def test_generic_spam_reputation_contributes_to_confidence_and_reasons():
    result = ProviderResult(
        provider="community_feed",
        spam_reports=25,
        confidence=0.95,
        category="spam_reputation",
        metadata={},
    )

    score = confidence_score([result])
    reasons = evidence_reasons([result])

    assert score == 40
    assert confidence_label(score) == "LOW"
    assert "community_feed reports 25 spam reports" in reasons
