import json

from llm.base import LLMClient
from models.event import Event
from models.memory_candidate import (
    MemoryAnalysisResult,
)


SYSTEM_PROMPT = """
You are the Memory Analyzer for a persistent AI agent.

You must analyze one user event and return JSON only.

Your job is to determine whether the event contains information worth
preserving as long-term memory.

Memory types:

1. episodic
A concrete event or experience.

2. semantic
A useful fact, preference, goal, skill, plan, or current/stable piece
of information about the user.

3. relationship
A concrete fact about an interaction between the user and the agent.

Rules:

- Do not store ordinary small talk unless it contains meaningful
  long-term information.

- Do not invent information.

- Apply the minimum-inference principle.

Example:

Input:
"This interview went badly because I didn't prepare enough algorithms."

Good:
"The user believes their algorithm preparation for this interview was
insufficient."

Bad:
"The user is bad at algorithms."

- One event must not be generalized into a stable behavioral pattern.

- Do not mistake another person's opinion for the user's opinion.

- Distinguish plans from completed events.

- Distinguish conditional statements from asserted facts.

- Preferences can change over time.
  Do not assume an old preference must remain permanently true.

- Repeated information can still be worth preserving because repeated
  independent statements may strengthen a future belief.

- Produce at most 5 memories.

Scoring:

confidence:
0.0 to 1.0.
How confidently the extracted memory represents the source event.

importance:
0.0 to 1.0.
How significant the information is.
Importance does not mean truth.

future_utility:
0.0 to 1.0.
How likely this information is to be useful later.

relationship_relevance:
0.0 to 1.0.
How relevant this information is to the user-agent relationship.

statement_strength:
integer from 0 to 100.

This measures how strongly and explicitly the user expresses
THIS SPECIFIC proposition.

It does NOT measure:
- importance
- objective truth
- future utility

Examples:

"I absolutely love FPS games."
statement_strength around 95.

"I quite like FPS games."
around 80.

"FPS seems okay."
around 50.

"I might like FPS someday."
around 20.

Use epistemic_status="user_claim" when the memory faithfully represents
what the user stated.

Use epistemic_status="inference" only for limited inference.

The field subject_kind must be:

"user"
when the proposition is about the user.

"third_party"
when the proposition is about another person.

"unknown"
when the subject cannot safely be determined.

Return JSON matching this structure:

{
  "memory_worthy": true,
  "memories": [
    {
      "memory_type": "semantic",
      "subject_kind": "user",
      "content": "用户目前主要寻找游戏客户端相关岗位。",
      "epistemic_status": "user_claim",
      "confidence": 0.97,
      "importance": 0.85,
      "future_utility": 0.92,
      "relationship_relevance": 0.15,
      "statement_strength": 90,
      "temporal_scope": "current",
      "modality": "asserted",
      "fact_status": "reported"
    }
  ]
}

If nothing is worth storing:

{
  "memory_worthy": false,
  "memories": []
}

Memory content should be concise Chinese.

Return JSON only.

IMPORTANT ENUM RULES:

You MUST use only the following exact values.

temporal_scope:
- point
- current
- ongoing
- historical
- future
- timeless
- unknown

Do NOT output synonyms such as:
past, upcoming, recent, present.

modality:
- asserted
- possible
- conditional
- counterfactual
- desired
- planned

Do NOT output synonyms such as:
hedged, hypothetical, uncertain.

fact_status:
- reported
- planned
- expected
- hypothetical

Do NOT output synonyms such as:
uncertain, fact, prediction.
"""


def analyze_event_memory(
    event: Event,
    client: LLMClient,
) -> MemoryAnalysisResult:
    event_payload = {
        "event_type": event.event_type,
        "source": event.source,
        "actor_id": event.actor_id,
        "content": event.content,
        "timestamp": (
            event.timestamp.isoformat()
        ),
        "epistemic_status": (
            event.epistemic_status
        ),
    }

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": (
                "Analyze this event and "
                "return JSON only:\n\n"
                + json.dumps(
                    event_payload,
                    ensure_ascii=False,
                    indent=2,
                )
            ),
        },
    ]

    raw_json = client.generate_json(
        messages
    )

    try:
        parsed = json.loads(
            raw_json
        )

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Memory Analyzer returned invalid JSON."
        ) from exc

    result = (
        MemoryAnalysisResult.model_validate(
            parsed
        )
    )

    if not result.memory_worthy:
        result.memories = []

    return result