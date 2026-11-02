from datetime import datetime, timezone

from models.event import Event
from models.relationship import RelationshipState


def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    return max(
        minimum,
        min(maximum, value),
    )


def apply_event_to_relationship(
    relationship: RelationshipState,
    event: Event,
) -> RelationshipState:
    """
    根据事件更新关系状态。

    MVP 暂时只做确定性规则。
    """

    new_relationship = relationship.model_copy(
        deep=True
    )

    if (
        event.event_type == "user_message"
        and event.actor_id == relationship.subject_id
    ):
        new_relationship.interaction_count += 1

        # 每次正常互动都会略微增加熟悉度
        new_relationship.familiarity += 0.02

        # 有持续互动时，关系依附非常轻微增加
        new_relationship.attachment += 0.005

        # 目前默认用户主动发送消息属于正常互惠互动
        new_relationship.reciprocity += 0.005

        new_relationship.last_interaction_at = (
            event.timestamp
        )

    new_relationship.trust = clamp(
        new_relationship.trust,
        0.0,
        1.0,
    )

    new_relationship.familiarity = clamp(
        new_relationship.familiarity,
        0.0,
        1.0,
    )

    new_relationship.reciprocity = clamp(
        new_relationship.reciprocity,
        0.0,
        1.0,
    )

    new_relationship.attachment = clamp(
        new_relationship.attachment,
        0.0,
        1.0,
    )

    new_relationship.updated_at = datetime.now(
        timezone.utc
    )

    return new_relationship