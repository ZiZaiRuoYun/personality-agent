from typing import Any, Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


CandidateMemoryType = Literal[
    "episodic",
    "semantic",
    "relationship",
]

CandidateEpistemicStatus = Literal[
    "user_claim",
    "inference",
]

CandidateTemporalScope = Literal[
    "point",
    "current",
    "ongoing",
    "historical",
    "future",
    "timeless",
    "unknown",
]

CandidateModality = Literal[
    "asserted",
    "possible",
    "conditional",
    "counterfactual",
    "desired",
    "planned",
]

CandidateFactStatus = Literal[
    "reported",
    "planned",
    "expected",
    "hypothetical",
]

CandidateSubjectKind = Literal[
    "user",
    "third_party",
    "unknown",
]


TEMPORAL_SCOPE_ALIASES = {
    "present": "current",
    "now": "current",
    "recent": "current",

    "past": "historical",
    "previous": "historical",

    "upcoming": "future",
    "future": "future",

    "specific": "point",
    "event": "point",

    "continuous": "ongoing",
    "long_term": "ongoing",

    "permanent": "timeless",
    "general": "timeless",
}


MODALITY_ALIASES = {
    "certain": "asserted",
    "direct": "asserted",

    "hedged": "possible",
    "uncertain": "possible",
    "hypothetical": "possible",
    "maybe": "possible",

    "conditioned": "conditional",

    "wish": "desired",
    "preference": "desired",

    "intend": "planned",
    "intended": "planned",
}


FACT_STATUS_ALIASES = {
    "fact": "reported",
    "asserted": "reported",
    "stated": "reported",

    "plan": "planned",
    "future_plan": "planned",

    "likely": "expected",
    "prediction": "expected",

    "uncertain": "hypothetical",
    "possible": "hypothetical",
    "hypothesis": "hypothetical",
}


def normalize_enum_value(
    value: Any,
    aliases: dict[str, str],
) -> Any:
    if not isinstance(value, str):
        return value

    normalized = (
        value
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    return aliases.get(
        normalized,
        normalized,
    )


class MemoryCandidate(BaseModel):
    memory_type: CandidateMemoryType

    subject_kind: CandidateSubjectKind = "user"

    content: str = Field(
        min_length=1,
        max_length=500,
    )

    epistemic_status: CandidateEpistemicStatus

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    importance: float = Field(
        ge=0.0,
        le=1.0,
    )

    future_utility: float = Field(
        ge=0.0,
        le=1.0,
    )

    relationship_relevance: float = Field(
        ge=0.0,
        le=1.0,
    )

    statement_strength: int = Field(
        ge=0,
        le=100,
    )

    temporal_scope: CandidateTemporalScope

    modality: CandidateModality

    fact_status: CandidateFactStatus

    @field_validator(
        "temporal_scope",
        mode="before",
    )
    @classmethod
    def normalize_temporal_scope(
        cls,
        value: Any,
    ) -> Any:
        return normalize_enum_value(
            value,
            TEMPORAL_SCOPE_ALIASES,
        )

    @field_validator(
        "modality",
        mode="before",
    )
    @classmethod
    def normalize_modality(
        cls,
        value: Any,
    ) -> Any:
        return normalize_enum_value(
            value,
            MODALITY_ALIASES,
        )

    @field_validator(
        "fact_status",
        mode="before",
    )
    @classmethod
    def normalize_fact_status(
        cls,
        value: Any,
    ) -> Any:
        return normalize_enum_value(
            value,
            FACT_STATUS_ALIASES,
        )


class MemoryAnalysisResult(BaseModel):
    memory_worthy: bool

    memories: list[MemoryCandidate] = Field(
        default_factory=list,
        max_length=5,
    )