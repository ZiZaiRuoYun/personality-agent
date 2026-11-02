from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


MemorySourceRole = Literal[
    "direct",
    "supporting",
    "derived",
]


class MemorySource(BaseModel):
    """
    Memory 与原始 Event 之间的证据连接。

    root_cause_id 非常重要：
    后续 Claim / Belief 系统会依靠它避免重复计算同一个根事件。
    """

    memory_id: str

    event_id: str
    root_cause_id: str

    source_role: MemorySourceRole = "direct"

    contribution_weight: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )