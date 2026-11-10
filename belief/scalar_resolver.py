from datetime import datetime
from math import prod

from belief.temporal import (
    calculate_temporal_weight,
)
from models.current_belief import (
    CurrentBelief,
)


RESOLVER_VERSION = "belief_v0.1"

LATEST_EVIDENCE_BOOST = 1.15


def parse_datetime(
    value,
) -> datetime | None:
    """
    SQLite 中 datetime 可能以 ISO string 存储。

    Resolver 统一转换成 datetime。
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

    raise TypeError(
        f"Unsupported datetime value: "
        f"{type(value)}"
    )


def calculate_evidence_weight(
    *,
    claim: dict,
    evidence: dict,
    now: datetime | None = None,
) -> tuple[float, float]:
    """
    单条 Evidence 最终参与 Belief 的权重。

    weight =
        statement_strength
        × memory_confidence
        × relation_confidence
        × temporal_weight

    返回：
        (effective_weight, temporal_weight)
    """

    observed_at = parse_datetime(
        evidence.get(
            "observed_at"
        )
    )

    temporal_weight = (
        calculate_temporal_weight(
            claim_type=(
                claim["claim_type"]
            ),
            temporal_mode=(
                claim["temporal_mode"]
            ),
            observed_at=observed_at,
            now=now,
        )
    )

    statement_weight = (
        evidence["statement_strength"]
        / 100.0
    )

    effective_weight = (
        statement_weight
        * evidence["memory_confidence"]
        * evidence["relation_confidence"]
        * temporal_weight
    )

    return (
        effective_weight,
        temporal_weight,
    )


def deduplicate_by_root(
    contributions: list[dict],
) -> list[dict]:
    """
    同一个 Claim 内：

    同一个 root_cause_id
    只能作为一份独立证据。

    如果同一个 root 产生多条 Evidence，
    只取 effective_weight 最大的一条。
    """

    best_by_root: dict[
        str,
        dict,
    ] = {}

    for contribution in contributions:
        root_cause_id = (
            contribution[
                "root_cause_id"
            ]
        )

        existing = best_by_root.get(
            root_cause_id
        )

        if (
            existing is None
            or contribution["weight"]
            > existing["weight"]
        ):
            best_by_root[
                root_cause_id
            ] = contribution

    return list(
        best_by_root.values()
    )


def apply_recency_boost(
    contributions: list[dict],
) -> list[dict]:
    """
    对最新的独立 Evidence 给予轻微权重奖励。

    规则：
    1. 只有一条证据时，不加权。
    2. 时间完全相同，不加权。
    3. 时间未知，不加权。
    4. 最新时间戳对应的证据获得 15% 加权。
    """

    if len(contributions) < 2:
        return contributions

    timestamps = [
        item["observed_at"]
        for item in contributions
        if item["observed_at"] is not None
    ]

    if len(timestamps) != len(contributions):
        return contributions

    latest_time = max(timestamps)

    if all(
        timestamp == latest_time
        for timestamp in timestamps
    ):
        return contributions

    for item in contributions:
        if item["observed_at"] == latest_time:
            item["weight"] *= LATEST_EVIDENCE_BOOST

    return contributions


def calculate_consistency(
    contributions: list[dict],
    scalar_value: float,
) -> float:
    """
    衡量 Evidence 是否彼此一致。

    使用加权平均绝对偏差。

    scalar 范围为：
        -100 ~ +100

    差异越大，consistency 越低。
    """

    if not contributions:
        return 0.0

    total_weight = sum(
        item["weight"]
        for item in contributions
    )

    if total_weight <= 0:
        return 0.0

    weighted_deviation = sum(
        abs(
            item["value"]
            - scalar_value
        )
        * item["weight"]
        for item in contributions
    ) / total_weight

    consistency = (
        1.0
        - min(
            weighted_deviation
            / 100.0,
            1.0,
        )
    )

    return max(
        0.0,
        min(
            consistency,
            1.0,
        ),
    )


def calculate_evidence_confidence(
    contributions: list[dict],
) -> float:
    """
    多个独立 root 的 Evidence
    使用 diminishing returns 聚合。

    confidence =
        1 - Π(1 - weight_i)

    例如：

    0.8
    + 0.8

    不会得到 1.6，

    而是：

    1 - 0.2 * 0.2
    = 0.96
    """

    if not contributions:
        return 0.0

    remaining_uncertainty = prod(
        1.0
        - max(
            0.0,
            min(
                item["weight"],
                1.0,
            ),
        )
        for item in contributions
    )

    confidence = (
        1.0
        - remaining_uncertainty
    )

    return max(
        0.0,
        min(
            confidence,
            1.0,
        ),
    )


def determine_status(
    *,
    independent_root_count: int,
    confidence: float,
    consistency: float,
) -> str:
    """
    MVP v0.1 status 规则。

    这是第一版启发式规则，
    后面可以根据测试数据调整。
    """

    if independent_root_count == 0:
        return "insufficient"

    if independent_root_count == 1:
        if confidence < 0.35:
            return "insufficient"

        return "uncertain"

    if consistency < 0.60:
        return "mixed"

    if confidence >= 0.60:
        return "resolved"

    return "uncertain"


def resolve_scalar_belief(
    *,
    claim: dict,
    evidence_rows: list[dict],
    now: datetime | None = None,
) -> tuple[
    CurrentBelief,
    list[dict],
]:
    """
    从一个 scalar Claim 的 Evidence
    计算 CurrentBelief。

    返回：

    CurrentBelief
    +
    实际参与计算的 Evidence contributions
    """

    if (
        claim["value_type"]
        != "scalar"
    ):
        raise ValueError(
            "resolve_scalar_belief() "
            "only accepts scalar claims."
        )

    contributions = []

    for evidence in evidence_rows:
        value = evidence.get(
            "evidence_value"
        )

        if value is None:
            continue

        weight, temporal_weight = (
            calculate_evidence_weight(
                claim=claim,
                evidence=evidence,
                now=now,
            )
        )

        contributions.append(
            {
                "memory_id": (
                    evidence[
                        "memory_id"
                    ]
                ),
                "root_cause_id": (
                    evidence[
                        "root_cause_id"
                    ]
                ),
                "value": float(
                    value
                ),
                "weight": weight,
                "temporal_weight": (
                    temporal_weight
                ),
                "observed_at": parse_datetime(
                    evidence.get("observed_at")
                ),
            }
        )

    evidence_count = len(
        contributions
    )

    independent = (
        deduplicate_by_root(
            contributions
        )
    )

    independent = apply_recency_boost(
        independent
    )

    independent_root_count = len(
        independent
    )

    if not independent:
        belief = CurrentBelief(
            claim_id=(
                claim["claim_id"]
            ),
            belief_type="scalar",
            scalar_value=None,
            confidence=0.0,
            status="insufficient",
            evidence_count=0,
            independent_root_count=0,
            resolver_version=(
                RESOLVER_VERSION
            ),
        )

        return (
            belief,
            [],
        )

    total_weight = sum(
        item["weight"]
        for item in independent
    )

    if total_weight <= 0:
        scalar_value = 0.0
    else:
        scalar_value = sum(
            item["value"]
            * item["weight"]
            for item in independent
        ) / total_weight

    scalar_value = max(
        -100.0,
        min(
            scalar_value,
            100.0,
        ),
    )

    evidence_confidence = (
        calculate_evidence_confidence(
            independent
        )
    )

    consistency = (
        calculate_consistency(
            independent,
            scalar_value,
        )
    )

    confidence = (
        evidence_confidence
        * consistency
    )

    confidence = max(
        0.0,
        min(
            confidence,
            1.0,
        ),
    )

    status = determine_status(
        independent_root_count=(
            independent_root_count
        ),
        confidence=confidence,
        consistency=consistency,
    )

    belief = CurrentBelief(
        claim_id=(
            claim["claim_id"]
        ),
        belief_type="scalar",
        scalar_value=round(
            scalar_value,
            3,
        ),
        confidence=round(
            confidence,
            4,
        ),
        status=status,
        evidence_count=(
            evidence_count
        ),
        independent_root_count=(
            independent_root_count
        ),
        resolver_version=(
            RESOLVER_VERSION
        ),
    )

    return (
        belief,
        independent,
    )