from datetime import datetime

from models.claim import Claim
from models.claim_evidence import (
    ClaimEvidence,
)
from models.claim_resolution import (
    ClaimResolutionResult,
)
from models.memory import Memory

from db.database import (
    get_claim,
    get_claims_for_subject,
    get_memory_sources,
    mark_memory_claim_resolved,
    save_claim_evidences,
    save_claim_with_evidence,
)

from llm.base import LLMClient
from claim.resolver import (
    resolve_memory_claim,
)


def create_claim_from_resolution(
    memory: Memory,
    resolution: ClaimResolutionResult,
) -> Claim:
    """
    根据 LLM Resolution 创建系统 Claim。

    claim_id 由 Python 创建，
    LLM 无权提供。
    """

    if memory.subject_id is None:
        raise ValueError(
            "Cannot create user claim "
            "without subject_id."
        )

    return Claim(
        subject_id=memory.subject_id,
        claim_type=resolution.claim_type,
        canonical_subject=(
            resolution.canonical_subject
        ),
        canonical_predicate=(
            resolution.canonical_predicate
        ),
        canonical_object=(
            resolution.canonical_object
        ),
        canonical_text=(
            resolution.canonical_text
        ),
        temporal_mode=(
            resolution.temporal_mode
        ),
        value_type=(
            resolution.value_type
        ),
        status="active",
    )


def create_claim_evidences(
    claim_id: str,
    memory: Memory,
    memory_sources: list[dict],
    resolution: ClaimResolutionResult,
) -> list[ClaimEvidence]:
    """
    一个 Memory 未来可能对应多个 root causes。

    因此按照 unique root_cause_id
    创建 ClaimEvidence。
    """

    root_causes = {
        source["root_cause_id"]
        for source in memory_sources
    }

    evidences = []

    for root_cause_id in root_causes:
        evidence = ClaimEvidence(
            claim_id=claim_id,
            memory_id=memory.memory_id,
            root_cause_id=root_cause_id,
            stance=resolution.stance,
            statement_strength=(
                memory.statement_strength
            ),
            memory_confidence=(
                memory.confidence
            ),
            relation_confidence=(
                resolution.relation_confidence
            ),
            evidence_value=(
                resolution.evidence_value
            ),
            evidence_label=(
                resolution.evidence_label
            ),
            observed_at=memory.observed_at,
        )

        evidences.append(
            evidence
        )

    return evidences


def process_memory_claim(
    memory: Memory,
    llm_client: LLMClient,
) -> tuple[
    Claim | None,
    list[ClaimEvidence],
    ClaimResolutionResult,
]:
    """
    Memory
    ↓
    Claim Resolver
    ↓
    Claim / ClaimEvidence
    """

    if memory.subject_id is None:
        raise ValueError(
            "MVP currently skips Claim resolution "
            "for memories without subject_id."
        )

    existing_claims = (
        get_claims_for_subject(
            memory.subject_id
        )
    )

    resolution = resolve_memory_claim(
        memory,
        existing_claims,
        llm_client,
    )

    if resolution.action == "skip":
        mark_memory_claim_resolved(
            memory.memory_id,
            resolution.action,
            resolution.reason,
        )

        
        return (
            None,
            [],
            resolution,
        )

    sources = get_memory_sources(
        memory.memory_id
    )

    if not sources:
        raise RuntimeError(
            "Memory has no provenance sources."
        )

    if resolution.action == "create":
        claim = create_claim_from_resolution(
            memory,
            resolution,
        )

        evidences = (
            create_claim_evidences(
                claim.claim_id,
                memory,
                sources,
                resolution,
            )
        )

        save_claim_with_evidence(
            claim,
            evidences,
        )

        mark_memory_claim_resolved(
            memory.memory_id,
            resolution.action,
            resolution.reason,
        )

        return (
            claim,
            evidences,
            resolution,
        )

    claim_data = get_claim(
        resolution.existing_claim_id
    )

    if claim_data is None:
        raise RuntimeError(
            "Claim Resolver referenced "
            "a claim that does not exist."
        )

    # 防止模型链接到其他主体的 Claim。
    if (
        claim_data["subject_id"]
        != memory.subject_id
    ):
        raise RuntimeError(
            "Claim subject mismatch."
        )

    claim = Claim(
        **claim_data
    )

    evidences = (
        create_claim_evidences(
            claim.claim_id,
            memory,
            sources,
            resolution,
        )
    )

    save_claim_evidences(
        evidences
    )

    mark_memory_claim_resolved(
        memory.memory_id,
        resolution.action,
        resolution.reason,
    )

    return (
        claim,
        evidences,
        resolution,
    )