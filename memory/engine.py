from models.event import Event
from models.memory import Memory
from models.memory_candidate import (
    MemoryCandidate,
)
from models.memory_source import (
    MemorySource,
)


def create_memory_from_event(
    event: Event,
    *,
    memory_type: str,
    content: str,
    subject_id: str | None = None,
    epistemic_status: str | None = None,
    confidence: float = 1.0,
    importance: float = 0.5,
    future_utility: float = 0.5,
    relationship_relevance: float = 0.0,
    statement_strength: int = 50,
    temporal_scope: str = "unknown",
    modality: str = "asserted",
    fact_status: str = "reported",
) -> tuple[
    Memory,
    MemorySource,
]:
    memory = Memory(
        memory_type=memory_type,
        subject_id=subject_id,
        content=content,
        epistemic_status=(
            epistemic_status
            or event.epistemic_status
        ),
        confidence=confidence,
        importance=importance,
        future_utility=future_utility,
        relationship_relevance=(
            relationship_relevance
        ),
        statement_strength=(
            statement_strength
        ),
        observed_at=event.timestamp,
        temporal_scope=temporal_scope,
        modality=modality,
        fact_status=fact_status,
    )

    source = MemorySource(
        memory_id=memory.memory_id,
        event_id=event.event_id,
        root_cause_id=(
            event.root_cause_id
        ),
        source_role="direct",
        contribution_weight=1.0,
    )

    return memory, source


def create_memory_from_candidate(
    event: Event,
    candidate: MemoryCandidate,
) -> tuple[
    Memory,
    MemorySource,
]:
    """
    将 LLM Candidate 转换成正式 Memory。

    provenance 由 Python 注入。
    """

    if candidate.subject_kind == "user":
        subject_id = event.actor_id
    else:
        subject_id = None

    return create_memory_from_event(
        event,
        memory_type=(
            candidate.memory_type
        ),
        subject_id=subject_id,
        content=candidate.content,
        epistemic_status=(
            candidate.epistemic_status
        ),
        confidence=(
            candidate.confidence
        ),
        importance=(
            candidate.importance
        ),
        future_utility=(
            candidate.future_utility
        ),
        relationship_relevance=(
            candidate.relationship_relevance
        ),
        statement_strength=(
            candidate.statement_strength
        ),
        temporal_scope=(
            candidate.temporal_scope
        ),
        modality=(
            candidate.modality
        ),
        fact_status=(
            candidate.fact_status
        ),
    )