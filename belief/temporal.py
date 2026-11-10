from datetime import datetime, timezone


DEFAULT_CURRENT_HALF_LIFE_DAYS = 90.0


def ensure_utc(
    value: datetime,
) -> datetime:
    """
    保证 datetime 是 UTC-aware。

    SQLite / Pydantic 读出来的时间理论上应该带 timezone，
    这里额外做容错。
    """

    if value.tzinfo is None:
        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


def calculate_age_days(
    observed_at: datetime,
    now: datetime | None = None,
) -> float:
    """
    计算 Evidence 距离当前时间多少天。

    如果因为时钟误差等原因 observed_at 在未来，
    按 0 天处理，不产生 > 1 的权重。
    """

    observed_at = ensure_utc(
        observed_at
    )

    if now is None:
        now = datetime.now(
            timezone.utc
        )
    else:
        now = ensure_utc(
            now
        )

    age_seconds = (
        now - observed_at
    ).total_seconds()

    age_days = (
        age_seconds / 86400.0
    )

    return max(
        age_days,
        0.0,
    )


def exponential_decay(
    age_days: float,
    half_life_days: float,
) -> float:
    """
    半衰期指数衰减。

    age = 0
    -> 1.0

    age = half_life
    -> 0.5

    age = 2 * half_life
    -> 0.25
    """

    if half_life_days <= 0:
        raise ValueError(
            "half_life_days must be > 0."
        )

    weight = 0.5 ** (
        age_days
        / half_life_days
    )

    return max(
        0.0,
        min(
            weight,
            1.0,
        ),
    )


def should_decay(
    claim_type: str,
    temporal_mode: str,
) -> bool:
    """
    MVP v0.1 时间衰减策略。

    当前确定：

    preference
        -> 衰减

    current goal
        -> 衰减

    skill / identity / fact / other
        -> 暂不衰减

    relationship_pattern / behavior_pattern
        -> MVP 暂不衰减，后续单独设计

    future
        -> 暂不在这里做过期判断
    """

    if claim_type == "preference":
        return True

    if (
        claim_type == "goal"
        and temporal_mode == "current"
    ):
        return True

    return False


def calculate_temporal_weight(
    *,
    claim_type: str,
    temporal_mode: str,
    observed_at: datetime | None,
    now: datetime | None = None,
    half_life_days: float = (
        DEFAULT_CURRENT_HALF_LIFE_DAYS
    ),
) -> float:
    """
    计算 ClaimEvidence 的 temporal_weight。

    返回范围：
        0.0 ~ 1.0

    当前 MVP 策略：

    preference / current goal
        -> 90 天半衰期

    其他
        -> 1.0

    如果 observed_at 缺失：
        -> 暂时返回 1.0
           不因为系统缺失时间信息而惩罚 Evidence。
    """

    if not should_decay(
        claim_type,
        temporal_mode,
    ):
        return 1.0

    if observed_at is None:
        return 1.0

    age_days = calculate_age_days(
        observed_at,
        now,
    )

    return exponential_decay(
        age_days,
        half_life_days,
    )