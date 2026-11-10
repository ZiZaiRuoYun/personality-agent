from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


ResolutionAction = Literal[
    "create",
    "link",
    "skip",
]

ResolutionStance = Literal[
    "support",
    "contradict",
    "temporal_update",
    "context",
]

ResolutionClaimType = Literal[
    "preference",
    "goal",
    "fact",
    "skill",
    "relationship_pattern",
    "behavior_pattern",
    "identity",
    "other",
]

ResolutionTemporalMode = Literal[
    "current",
    "historical",
    "persistent",
    "episodic",
    "future",
    "unknown",
]

ResolutionValueType = Literal[
    "scalar",
    "categorical",
    "boolean",
    "unstructured",
]


class ClaimResolutionResult(BaseModel):
    """
    LLM 对一条 Memory 如何进入 Claim Layer
    的判断结果。
    """

    action: ResolutionAction

    # link 时使用
    existing_claim_id: str | None = None

    # create 时使用
    claim_type: ResolutionClaimType | None = None

    canonical_subject: str | None = None
    canonical_predicate: str | None = None
    canonical_object: str | None = None

    # 注意：
    # canonical_text 应描述 semantic slot，
    # 而不是直接复制某次 Memory。
    canonical_text: str | None = None

    temporal_mode: (
        ResolutionTemporalMode | None
    ) = None


    value_type: ResolutionValueType | None = None

    # create / link 时需要。
    # skip 时可以为空。
    stance: ResolutionStance | None = None

    relation_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    # 对 preference / willingness / degree 等
    # 可标量化属性使用 -100 ~ +100。
    #
    # 非标量 Claim 使用 None。
    evidence_value: int | None = Field(
        default=None,
        ge=-100,
        le=100,
    )

    evidence_label: str | None = Field(
        default=None,
        max_length=200,
    )

    reason: str = Field(
        min_length=1,
        max_length=500,
    )

    @model_validator(mode="after")
    def validate_resolution(self):
        if self.action == "skip":
            return self

        if self.stance is None:
            raise ValueError(
                "stance is required when "
                "action is create or link."
            )

        if self.relation_confidence is None:
            raise ValueError(
                "relation_confidence is required "
                "when action is create or link."
            )

        if self.action == "link":
            if not self.existing_claim_id:
                raise ValueError(
                    "existing_claim_id is required "
                    "when action='link'."
                )

        if self.action == "create":
            required = [
                self.claim_type,
                self.canonical_subject,
                self.canonical_predicate,
                self.canonical_text,
                self.temporal_mode,
                self.value_type,
            ]

            if any(
                value is None
                for value in required
            ):
                raise ValueError(
                    "Claim fields are required "
                    "when action='create'."
                )

        return self