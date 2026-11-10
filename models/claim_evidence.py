from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


EvidenceStance = Literal[
    "support",
    "contradict",
    "temporal_update",
    "context",
]


class ClaimEvidence(BaseModel):
    """
    一条 Memory 与 Claim semantic slot 之间的关系。

    evidence_value:
    对可以表示“方向/程度”的 Claim，
    使用 -100 ~ +100 保存该证据表达的值。

    例如 preference：
        -100 = 极度不喜欢
           0 = 中性
        +100 = 极度喜欢 / 最喜欢

    对没有自然标量含义的 Claim，使用 None。
    """

    claim_evidence_id: str = Field(
        default_factory=lambda: f"cev_{uuid4().hex}"
    )

    claim_id: str
    memory_id: str

    root_cause_id: str

    stance: EvidenceStance

    # 用户表达该命题有多明确/坚定。
    statement_strength: int = Field(
        ge=0,
        le=100,
    )

    # Memory Analyzer 对自身理解的置信度。
    memory_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    # Claim Resolver 对“这条 Memory
    # 属于这个 Claim”的置信度。
    relation_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    # 可选的语义值。
    evidence_value: int | None = Field(
        default=None,
        ge=-100,
        le=100,
    )

    evidence_label: str | None = Field(
        default=None,
        max_length=200,
    )

    observed_at: datetime | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )