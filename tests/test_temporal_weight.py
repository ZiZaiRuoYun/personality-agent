from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from belief.temporal import (
    calculate_temporal_weight,
)


NOW = datetime(
    2026,
    11,
    3,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


def test_current_preference_now():
    weight = calculate_temporal_weight(
        claim_type="preference",
        temporal_mode="current",
        observed_at=NOW,
        now=NOW,
    )

    assert weight == pytest.approx(
        1.0
    )


def test_current_preference_90_days():
    observed_at = (
        NOW
        - timedelta(days=90)
    )

    weight = calculate_temporal_weight(
        claim_type="preference",
        temporal_mode="current",
        observed_at=observed_at,
        now=NOW,
    )

    assert weight == pytest.approx(
        0.5
    )


def test_current_preference_180_days():
    observed_at = (
        NOW
        - timedelta(days=180)
    )

    weight = calculate_temporal_weight(
        claim_type="preference",
        temporal_mode="current",
        observed_at=observed_at,
        now=NOW,
    )

    assert weight == pytest.approx(
        0.25
    )


def test_current_goal_decays():
    observed_at = (
        NOW
        - timedelta(days=90)
    )

    weight = calculate_temporal_weight(
        claim_type="goal",
        temporal_mode="current",
        observed_at=observed_at,
        now=NOW,
    )

    assert weight == pytest.approx(
        0.5
    )


def test_future_goal_does_not_decay_yet():
    observed_at = (
        NOW
        - timedelta(days=90)
    )

    weight = calculate_temporal_weight(
        claim_type="goal",
        temporal_mode="future",
        observed_at=observed_at,
        now=NOW,
    )

    assert weight == pytest.approx(
        1.0
    )


def test_skill_does_not_decay():
    observed_at = (
        NOW
        - timedelta(days=3650)
    )

    weight = calculate_temporal_weight(
        claim_type="skill",
        temporal_mode="persistent",
        observed_at=observed_at,
        now=NOW,
    )

    assert weight == pytest.approx(
        1.0
    )


def test_identity_does_not_decay():
    observed_at = (
        NOW
        - timedelta(days=3650)
    )

    weight = calculate_temporal_weight(
        claim_type="identity",
        temporal_mode="persistent",
        observed_at=observed_at,
        now=NOW,
    )

    assert weight == pytest.approx(
        1.0
    )


def test_fact_does_not_decay():
    observed_at = (
        NOW
        - timedelta(days=3650)
    )

    weight = calculate_temporal_weight(
        claim_type="fact",
        temporal_mode="persistent",
        observed_at=observed_at,
        now=NOW,
    )

    assert weight == pytest.approx(
        1.0
    )


def test_missing_observed_at():
    weight = calculate_temporal_weight(
        claim_type="preference",
        temporal_mode="current",
        observed_at=None,
        now=NOW,
    )

    assert weight == pytest.approx(
        1.0
    )


def test_future_timestamp_is_clamped():
    observed_at = (
        NOW
        + timedelta(days=30)
    )

    weight = calculate_temporal_weight(
        claim_type="preference",
        temporal_mode="current",
        observed_at=observed_at,
        now=NOW,
    )

    assert weight == pytest.approx(
        1.0
    )