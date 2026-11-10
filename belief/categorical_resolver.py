
from collections import defaultdict
from datetime import datetime

from belief.scalar_resolver import (
    RESOLVER_VERSION,
    calculate_evidence_weight,
    calculate_evidence_confidence,
    deduplicate_by_root,
    apply_recency_boost,
    parse_datetime,
)
from models.current_belief import CurrentBelief


CATEGORY_RESOLVED_SHARE = 0.70
CATEGORY_TIE_TOLERANCE = 0.05
MIN_EVIDENCE_CONFIDENCE = 0.35


def normalize_evidence_label(
    label: str | None,
) -> str | None:
    """基础类别标签规范化。"""

    if not isinstance(label, str):
        return None

    normalized = (
        label.strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    return normalized or None


def resolve_categorical_belief(
    *,
    claim: dict,
    evidence_rows: list[dict],
    now: datetime | None = None,
) -> tuple[CurrentBelief, list[dict]]:

    if claim["value_type"] != "categorical":
        raise ValueError(
            "Categorical Resolver only accepts "
            "categorical claims."
        )

    contributions = []

    # 1. 提取有效的类别证据
    for evidence in evidence_rows:
        label = normalize_evidence_label(
            evidence.get("evidence_label")
        )

        if label is None:
            continue

        weight, temporal_weight = (
            calculate_evidence_weight(
                claim=claim,
                evidence=evidence,
                now=now,
            )
        )

        # 没有独立 root 时，退化为独立 Memory。
        # 避免把所有缺失 root 的证据错误合并。
        root_id = evidence.get("root_cause_id")

        if not root_id:
            root_id = f"memory:{evidence['memory_id']}"

        contributions.append({
            "memory_id": evidence["memory_id"],
            "root_cause_id": root_id,
            "label": label,
            "weight": weight,
            "temporal_weight": temporal_weight,
            "observed_at": parse_datetime(
                evidence.get("observed_at")
            ),
        })

    evidence_count = len(contributions)

    # 2. 同一个 root 只算一份独立证据
    independent = deduplicate_by_root(
        contributions
    )

    # 3. 最新独立证据给予 15% 温和加权
    independent = apply_recency_boost(
        [dict(item) for item in independent]
    )

    independent = [
        item
        for item in independent
        if item["weight"] > 0
    ]

    independent_root_count = len(independent)

    # 4. 没有有效证据
    if not independent:
        return CurrentBelief(
            claim_id=claim["claim_id"],
            belief_type="categorical",
            categorical_value=None,
            confidence=0.0,
            status="insufficient",
            evidence_count=evidence_count,
            independent_root_count=0,
            resolver_version=RESOLVER_VERSION,
        ), []

    # 5. 按 label 统计证据权重
    label_scores = defaultdict(float)

    for item in independent:
        label_scores[item["label"]] += item["weight"]

    ranked = sorted(
        label_scores.items(),
        key=lambda item: (-item[1], item[0]),
    )

    winner_label, winner_score = ranked[0]

    second_score = (
        ranked[1][1]
        if len(ranked) > 1
        else 0.0
    )

    total_weight = sum(label_scores.values())

    winner_share = winner_score / total_weight
    second_share = second_score / total_weight

    # 6. 计算 confidence
    evidence_confidence = (
        calculate_evidence_confidence(independent)
    )

    confidence = (
        evidence_confidence * winner_share
    )

    confidence = max(0.0, min(confidence, 1.0))

    # 7. 处理类别接近的情况
    near_tie = (
        len(ranked) > 1
        and winner_share - second_share
        <= CATEGORY_TIE_TOLERANCE
    )

    categorical_value = (
        None if near_tie else winner_label
    )

    # 8. 计算 status
    if independent_root_count == 1:
        status = (
            "insufficient"
            if confidence < MIN_EVIDENCE_CONFIDENCE
            else "uncertain"
        )

    elif (
        len(ranked) > 1
        and winner_share < CATEGORY_RESOLVED_SHARE
    ):
        status = "mixed"

    elif near_tie:
        status = "mixed"

    elif confidence >= 0.60:
        status = "resolved"

    else:
        status = "uncertain"

    belief = CurrentBelief(
        claim_id=claim["claim_id"],
        belief_type="categorical",
        categorical_value=categorical_value,
        confidence=round(confidence, 4),
        status=status,
        evidence_count=evidence_count,
        independent_root_count=independent_root_count,
        resolver_version=RESOLVER_VERSION,
    )

    return belief, independent
