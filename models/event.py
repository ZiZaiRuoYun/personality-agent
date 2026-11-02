from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class Event(BaseModel):
    """
    Personality Agent 中所有输入事件的统一数据结构。

    未来无论是：
    - 用户消息
    - Heartbeat
    - Tool Result
    - Agent Action
    - Reflection
    - 外部事件

    都会尽量转换成 Event。
    """

    event_id: str = Field(default_factory=lambda: f"evt_{uuid4().hex}")

    root_cause_id: str | None = None

    event_type: str
    source: str

    actor_id: str | None = None
    content: str | None = None

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    causal_parent_id: str | None = None

    epistemic_status: str = "observation"
    confidence: float = 1.0

    scope: str = "global"

    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def set_root_cause(self):
        """
        如果这是一个新的根事件，那么 root_cause_id
        默认就是自己的 event_id。
        """
        if self.root_cause_id is None:
            self.root_cause_id = self.event_id

        return self