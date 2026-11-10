from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


ClaimType = Literal[
    "preference",
    "goal",
    "fact",
    "skill",
    "relationship_pattern",
    "behavior_pattern",
    "identity",
    "other",
]


ClaimTemporalMode = Literal[
    "current",
    "historical",
    "persistent",
    "episodic",
    "future",
    "unknown",
]


ClaimStatus = Literal[
    "active",
    "historical",
    "dormant",
    "unresolved",
]


ClaimValueType = Literal[
    "scalar",
    "categorical",
    "boolean",
    "unstructured",
]


class Claim(BaseModel):
    """
    Claim 表示一个可被多个 Memory 更新的语义属性槽。

    value_type 决定后续 Belief Resolver
    应该使用哪一种聚合方式。
    """

    claim_id: str = Field(
        default_factory=lambda: f"clm_{uuid4().hex}"
    )

    subject_id: str

    claim_type: ClaimType

    canonical_subject: str

    canonical_predicate: str

    canonical_object: str | None = None

    canonical_text: str

    temporal_mode: ClaimTemporalMode = "unknown"

    value_type: ClaimValueType = "unstructured"

    status: ClaimStatus = "active"

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )