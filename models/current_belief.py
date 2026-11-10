from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


BeliefType = Literal[
    "scalar",
    "categorical",
    "boolean",
    "unstructured",
]


BeliefStatus = Literal[
    "resolved",
    "mixed",
    "uncertain",
    "insufficient",
]


class CurrentBelief(BaseModel):
    """
    当前 Belief 是派生状态，不是原始事实。

    它可以随时从 ClaimEvidence 重算。
    """

    belief_id: str = Field(
        default_factory=lambda: f"blf_{uuid4().hex}"
    )

    claim_id: str

    belief_type: BeliefType

    scalar_value: float | None = None

    categorical_value: str | None = None

    boolean_value: bool | None = None

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    status: BeliefStatus

    evidence_count: int = Field(
        ge=0,
    )

    independent_root_count: int = Field(
        ge=0,
    )

    computed_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    resolver_version: str = "belief_v0.1"