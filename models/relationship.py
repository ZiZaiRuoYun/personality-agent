from datetime import datetime, timezone

from pydantic import BaseModel, Field


class RelationshipState(BaseModel):
    """
    Agent 与某一个用户之间的关系状态。

    Relationship 属于长期、缓慢变化的状态，
    与 AgentState 中的短期情绪分开。
    """

    subject_id: str

    trust: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    familiarity: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
    )

    reciprocity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    attachment: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
    )

    interaction_count: int = Field(
        default=0,
        ge=0,
    )

    last_interaction_at: datetime | None = None

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )