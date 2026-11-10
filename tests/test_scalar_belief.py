from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from belief.scalar_resolver import (
    resolve_scalar_belief,
)


NOW = datetime(
    2026,
    11,
    4,
    0,
    0,
    tzinfo=timezone.utc,
)


def make_claim(
    claim_type="preference",
    temporal_mode="current",
):
    return {
        "claim_id": "claim_test",
        "claim_type": claim_type,
        "temporal_mode": temporal_mode,
        "value_type": "scalar",
    }


def make_evidence(
    *,
    memory_id,
    root_cause_id,
    value,
    strength=100,
    memory_confidence=1.0,
    relation_confidence=1.0,
    observed_at=NOW,
):
    return {
        "memory_id": memory_id,
        "root_cause_id": (
            root_cause_id
        ),
        "evidence_value": value,
        "statement_strength": strength,
        "memory_confidence": (
            memory_confidence
        ),
        "relation_confidence": (
            relation_confidence
        ),
        "observed_at": (
            observed_at.isoformat()
        ),
    }


def test_single_scalar_evidence():
    claim = make_claim()

    evidence = [
        make_evidence(
            memory_id="m1",
            root_cause_id="r1",
            value=80,
        )
    ]

    belief, used = (
        resolve_scalar_belief(
            claim=claim,
            evidence_rows=evidence,
            now=NOW,
        )
    )

    assert belief.scalar_value == pytest.approx(
        80.0
    )

    assert belief.independent_root_count == 1

    assert belief.status == "uncertain"


def test_two_equal_opposite_values():
    claim = make_claim()

    evidence = [
        make_evidence(
            memory_id="m1",
            root_cause_id="r1",
            value=100,
        ),
        make_evidence(
            memory_id="m2",
            root_cause_id="r2",
            value=-100,
        ),
    ]

    belief, used = (
        resolve_scalar_belief(
            claim=claim,
            evidence_rows=evidence,
            now=NOW,
        )
    )

    assert belief.scalar_value == pytest.approx(
        0.0
    )

    assert belief.status == "mixed"

    assert belief.confidence == pytest.approx(
        0.0
    )


def test_root_cause_deduplication():
    claim = make_claim()

    evidence = [
        make_evidence(
            memory_id="m1",
            root_cause_id="r1",
            value=0,
            strength=40,
        ),
        make_evidence(
            memory_id="m2",
            root_cause_id="r1",
            value=100,
            strength=90,
        ),
    ]

    belief, used = (
        resolve_scalar_belief(
            claim=claim,
            evidence_rows=evidence,
            now=NOW,
        )
    )

    assert len(used) == 1

    assert belief.evidence_count == 2

    assert (
        belief.independent_root_count
        == 1
    )

    assert belief.scalar_value == pytest.approx(
        100.0
    )


def test_newer_preference_has_more_weight():
    claim = make_claim()

    old_time = (
        NOW
        - timedelta(days=90)
    )

    evidence = [
        make_evidence(
            memory_id="old",
            root_cause_id="r1",
            value=100,
            observed_at=old_time,
        ),
        make_evidence(
            memory_id="new",
            root_cause_id="r2",
            value=0,
            observed_at=NOW,
        ),
    ]

    belief, used = (
        resolve_scalar_belief(
            claim=claim,
            evidence_rows=evidence,
            now=NOW,
        )
    )

    # old weight = 0.5
    # new weight = 1.0
    #
    # (100 * .5 + 0 * 1) / 1.5
    # = 33.333...

    assert belief.scalar_value == pytest.approx(
        30.303,
        abs=0.01,
    )


def test_non_decaying_skill():
    claim = make_claim(
        claim_type="skill",
        temporal_mode="persistent",
    )

    old_time = (
        NOW
        - timedelta(days=3650)
    )

    evidence = [
        make_evidence(
            memory_id="m1",
            root_cause_id="r1",
            value=80,
            observed_at=old_time,
        )
    ]

    belief, used = (
        resolve_scalar_belief(
            claim=claim,
            evidence_rows=evidence,
            now=NOW,
        )
    )

    assert belief.scalar_value == pytest.approx(
        80.0
    )

    assert used[0][
        "temporal_weight"
    ] == pytest.approx(
        1.0
    )


def test_missing_scalar_evidence():
    claim = make_claim()

    evidence = [
        {
            "memory_id": "m1",
            "root_cause_id": "r1",
            "evidence_value": None,
            "statement_strength": 100,
            "memory_confidence": 1.0,
            "relation_confidence": 1.0,
            "observed_at": NOW.isoformat(),
        }
    ]

    belief, used = (
        resolve_scalar_belief(
            claim=claim,
            evidence_rows=evidence,
            now=NOW,
        )
    )

    assert belief.scalar_value is None

    assert belief.status == "insufficient"

    assert belief.evidence_count == 0

    assert (
        belief.independent_root_count
        == 0
    )


def test_latest_evidence_small_boost():
    claim = make_claim()

    evidence = [
        make_evidence(
            memory_id="old",
            root_cause_id="r1",
            value=0,
            observed_at=NOW - timedelta(minutes=1),
        ),
        make_evidence(
            memory_id="new",
            root_cause_id="r2",
            value=100,
            observed_at=NOW,
        ),
    ]

    belief, used = resolve_scalar_belief(
        claim=claim,
        evidence_rows=evidence,
        now=NOW,
    )

    assert 50 < belief.scalar_value < 60
    assert belief.status == "mixed"