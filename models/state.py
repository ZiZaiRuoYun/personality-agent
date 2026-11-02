from datetime import datetime, timezone

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """
    Agent 的短期动态状态。

    这些状态会随着互动快速变化，
    但它们不等于 Personality。
    """

    mood_valence: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
    )

    energy: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
    )

    social_drive: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
    )

    stress: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
    )

    disappointment: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )