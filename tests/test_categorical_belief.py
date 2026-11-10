
from datetime import datetime, timedelta, timezone

import pytest

from belief.categorical_resolver import (
    resolve_categorical_belief,
)


NOW = datetime(
    2026, 11, 4, 0, 0,
    tzinfo=timezone.utc,
)


def make_claim():
    return {
        "claim_id": "test_categorical_claim",
        "claim_type": "goal",
        "temporal_mode": "current",
        "value_type": "categorical",
    }


def make_evidence(
    memory_id,
    root_id,
    label,
    strength=100,
    observed_at=NOW,
):
    return {
        "memory_id": memory_id,
        "root_cause_id": root_id,
        "evidence_label": label,
        "statement_strength": strength,
        "memory_confidence": 1.0,
        "relation_confidence": 1.0,
        "observed_at": observed_at.isoformat(),
    }


def test_single_label():
    belief, used = resolve_categorical_belief(
        claim=make_claim(),
        evidence_rows=[
            make_evidence(
                "m1", "r1", "game_client"
            )
        ],
        now=NOW,
    )

    assert belief.categorical_value == "game_client"
    assert belief.status == "uncertain"
    assert belief.independent_root_count == 1


def test_two_agreeing_roots():
    belief, used = resolve_categorical_belief(
        claim=make_claim(),
        evidence_rows=[
            make_evidence(
                "m1", "r1", "game_client", 80
            ),
            make_evidence(
                "m2", "r2", "game_client", 80
            ),
        ],
        now=NOW,
    )

    assert belief.categorical_value == "game_client"
    assert belief.status == "resolved"
    assert belief.confidence == pytest.approx(0.96)


def test_equal_conflict():
    belief, used = resolve_categorical_belief(
        claim=make_claim(),
        evidence_rows=[
            make_evidence(
                "m1", "r1", "game_client"
            ),
            make_evidence(
                "m2", "r2", "game_engine"
            ),
        ],
        now=NOW,
    )

    assert belief.categorical_value is None
    assert belief.status == "mixed"
    assert belief.confidence == pytest.approx(0.5)


def test_latest_slight_advantage():
    belief, used = resolve_categorical_belief(
        claim=make_claim(),
        evidence_rows=[
            make_evidence(
                "m1",
                "r1",
                "game_client",
                observed_at=NOW - timedelta(minutes=1),
            ),
            make_evidence(
                "m2",
                "r2",
                "game_engine",
                observed_at=NOW,
            ),
        ],
        now=NOW,
    )

    assert belief.categorical_value == "game_engine"
    assert belief.status == "mixed"
    assert 0.50 < belief.confidence < 0.60


def test_duplicate_root():
    belief, used = resolve_categorical_belief(
        claim=make_claim(),
        evidence_rows=[
            make_evidence(
                "m1", "same_root", "game_client", 40
            ),
            make_evidence(
                "m2", "same_root", "game_engine", 90
            ),
        ],
        now=NOW,
    )

    assert len(used) == 1
    assert belief.evidence_count == 2
    assert belief.independent_root_count == 1
    assert belief.categorical_value == "game_engine"


def test_missing_label():
    belief, used = resolve_categorical_belief(
        claim=make_claim(),
        evidence_rows=[
            make_evidence(
                "m1", "r1", None
            )
        ],
        now=NOW,
    )

    assert belief.categorical_value is None
    assert belief.status == "insufficient"
    assert belief.confidence == 0.0
    assert len(used) == 0


def test_label_normalization():
    belief, used = resolve_categorical_belief(
        claim=make_claim(),
        evidence_rows=[
            make_evidence(
                "m1", "r1", "Game Client"
            ),
            make_evidence(
                "m2", "r2", "game-client"
            ),
        ],
        now=NOW,
    )

    assert belief.categorical_value == "game_client"
    assert belief.status == "resolved"
