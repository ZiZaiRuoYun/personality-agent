from datetime import datetime, timezone

from models.event import Event
from models.state import AgentState


def clamp(value: float, minimum: float, maximum: float) -> float:
    """
    保证数值不会超出允许范围。
    """

    return max(minimum, min(maximum, value))


def apply_event_to_state(
    state: AgentState,
    event: Event,
) -> AgentState:
    """
    根据 Event 更新 AgentState。

    MVP 当前只做非常简单的确定性规则。
    以后这里会逐渐被更复杂的情绪评估系统替代。
    """

    new_state = state.model_copy(deep=True)

    if event.event_type == "user_message":
        # 用户进行了互动：
        # 社交需求得到一定满足。
        new_state.social_drive -= 0.03

        # 正常聊天会轻微消耗精力。
        new_state.energy -= 0.01

    new_state.mood_valence = clamp(
        new_state.mood_valence,
        -1.0,
        1.0,
    )

    new_state.energy = clamp(
        new_state.energy,
        0.0,
        1.0,
    )

    new_state.social_drive = clamp(
        new_state.social_drive,
        0.0,
        1.0,
    )

    new_state.stress = clamp(
        new_state.stress,
        0.0,
        1.0,
    )

    new_state.disappointment = clamp(
        new_state.disappointment,
        0.0,
        1.0,
    )

    new_state.updated_at = datetime.now(timezone.utc)

    return new_state