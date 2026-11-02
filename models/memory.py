from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


MemoryType = Literal[
    "episodic",
    "semantic",
    "relationship",
]

EpistemicStatus = Literal[
    "observation",
    "user_claim",
    "inference",
    "hypothesis",
    "self_generated",
]

TemporalScope = Literal[
    "point",
    "current",
    "ongoing",
    "historical",
    "timeless",
    "unknown",
]

Modality = Literal[
    "asserted",
    "possible",
    "conditional",
    "counterfactual",
    "desired",
    "planned",
]

FactStatus = Literal[
    "observed",
    "reported",
    "planned",
    "expected",
    "hypothetical",
]

TemporalScope = Literal[
    "point",
    "current",
    "ongoing",
    "historical",
    "future",
    "timeless",
    "unknown",
]


class Memory(BaseModel):
    """
    长期记忆记录。

    Memory 是 append-only 的历史证据。
    一旦创建，不应该因为后续信息而原地修改其语义内容。
    """

    memory_id: str = Field(
        default_factory=lambda: f"mem_{uuid4().hex}"
    )

    memory_type: MemoryType

    subject_id: str | None = None

    content: str

    epistemic_status: EpistemicStatus = "observation"

    # 这条 Memory 是否准确反映其来源证据。
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )

    # 这些分数不直接决定“真假”。
    importance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    future_utility: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    relationship_relevance: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    # LLM 后续会输出 0~100。
    # 表示一句话针对某命题表达得有多明确、坚定。
    statement_strength: int = Field(
        default=50,
        ge=0,
        le=100,
    )

    observed_at: datetime | None = None

    temporal_scope: TemporalScope = "unknown"

    valid_from: datetime | None = None
    valid_until: datetime | None = None

    modality: Modality = "asserted"
    fact_status: FactStatus = "reported"

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    access_count: int = Field(
        default=0,
        ge=0,
    )

    last_accessed_at: datetime | None = None