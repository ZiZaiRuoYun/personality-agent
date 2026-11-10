from db.database import (
    DATABASE_PATH,
    get_recent_events,
    get_recent_memories,
    initialize_database,
    load_agent_state,
    load_relationship,
    save_agent_state,
    save_event,
    save_memory,
    save_relationship,
    get_claim_evidence,
    get_claims_for_subject,
    get_memory,
    get_unresolved_memories,
    reset_claim_layer,
    mark_memory_claim_resolved,
    get_all_current_beliefs,
)

from belief.categorical_resolver import (
    resolve_categorical_belief,
)

from belief.scalar_resolver import (
    resolve_scalar_belief,
)

from llm.base import LLMClient
from llm.factory import create_llm_client

from memory.analyzer import (
    analyze_event_memory,
)

from memory.engine import (
    create_memory_from_candidate,
)

from models.event import Event
from models.relationship import (
    RelationshipState,
)
from models.state import AgentState

from relationship.engine import (
    apply_event_to_relationship,
)

from state.engine import (
    apply_event_to_state,
)

from claim.engine import (
    process_memory_claim,
)


USER_ID = "user_001"


from models.current_belief import (
    CurrentBelief,
)

from db.database import (
    save_current_belief,
)

def resolve_scalar_beliefs() -> None:
    claims = get_claims_for_subject(
        USER_ID
    )

    scalar_claims = [
        claim
        for claim in claims
        if claim["value_type"] == "scalar"
    ]

    if not scalar_claims:
        print(
            "\nNo scalar claims found."
        )
        return

    print(
        f"\nResolving "
        f"{len(scalar_claims)} "
        f"scalar beliefs..."
    )

    for claim in scalar_claims:
        evidence = get_claim_evidence(
            claim["claim_id"]
        )

        try:
            belief, used = (
                resolve_scalar_belief(
                    claim=claim,
                    evidence_rows=evidence,
                )
            )

            save_current_belief(
                belief
            )

        except Exception as exc:
            print(
                f"\n[Belief Resolver Error] "
                f"{claim['canonical_text']}"
            )

            print(
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            continue

        print(
            f"\n- "
            f"{claim['canonical_text']}"
        )

        print(
            f"    value="
            f"{belief.scalar_value}"
        )

        print(
            f"    confidence="
            f"{belief.confidence:.3f}"
        )

        print(
            f"    status="
            f"{belief.status}"
        )

        print(
            f"    evidence="
            f"{belief.evidence_count}"
        )

        print(
            f"    independent_roots="
            f"{belief.independent_root_count}"
        )

        print(
            "    contributions:"
        )

        for item in used:
            print(
                f"      value="
                f"{item['value']:.1f}, "
                f"weight="
                f"{item['weight']:.3f}, "
                f"temporal="
                f"{item['temporal_weight']:.3f}, "
                f"root="
                f"{item['root_cause_id']}"
            )



def resolve_categorical_beliefs() -> None:
    """计算并保存所有 categorical Claim 的 CurrentBelief。"""

    claims = get_claims_for_subject(USER_ID)

    categorical_claims = [
        claim
        for claim in claims
        if claim["value_type"] == "categorical"
    ]

    if not categorical_claims:
        print("\nNo categorical claims found.")
        return

    print(
        f"\nResolving {len(categorical_claims)} "
        "categorical beliefs..."
    )

    for claim in categorical_claims:
        try:
            evidence = get_claim_evidence(
                claim["claim_id"]
            )

            belief, used = resolve_categorical_belief(
                claim=claim,
                evidence_rows=evidence,
            )

            save_current_belief(belief)

        except Exception as exc:
            print(
                f"\n[Categorical Resolver Error] "
                f"{claim['canonical_text']}"
            )
            print(f"{type(exc).__name__}: {exc}")
            continue

        print(f"\n- {claim['canonical_text']}")
        print(f"    value={belief.categorical_value}")
        print(f"    confidence={belief.confidence:.3f}")
        print(f"    status={belief.status}")
        print(f"    evidence={belief.evidence_count}")
        print(
            f"    independent_roots="
            f"{belief.independent_root_count}"
        )

        print("    contributions:")

        for item in used:
            print(
                f"      label={item['label']}, "
                f"weight={item['weight']:.3f}, "
                f"temporal={item['temporal_weight']:.3f}, "
                f"root={item['root_cause_id']}"
            )



def create_test_belief() -> None:
    claims = get_claims_for_subject(
        USER_ID
    )

    scalar_claim = next(
        (
            claim
            for claim in claims
            if (
                claim["value_type"]
                == "scalar"
            )
        ),
        None,
    )

    if scalar_claim is None:
        print(
            "\nNo scalar claim found."
        )
        return

    belief = CurrentBelief(
        claim_id=(
            scalar_claim["claim_id"]
        ),
        belief_type="scalar",
        scalar_value=82.0,
        confidence=0.90,
        status="resolved",
        evidence_count=3,
        independent_root_count=3,
    )

    save_current_belief(
        belief
    )

    print(
        "\nTest belief saved."
    )


def create_user_message_event(
    message: str,
) -> Event:
    return Event(
        event_type="user_message",
        source="user",
        actor_id=USER_ID,
        content=message,
        epistemic_status="user_claim",
        confidence=1.0,
        scope=f"relationship:{USER_ID}",
    )


def print_recent_events() -> None:
    events = get_recent_events(
        limit=5
    )

    if not events:
        print("\nNo events found.")
        return

    print("\nRecent events:")

    for event in events:
        print(
            f"- [{event['event_type']}] "
            f"{event['content']} "
            f"({event['event_id']})"
        )


def print_memories() -> None:
    memories = get_recent_memories(
        limit=10
    )

    if not memories:
        print("\nNo memories found.")
        return

    print("\nRecent Memories:")

    for memory in memories:
        print(
            f"- [{memory['memory_type']}] "
            f"{memory['content']}"
        )

        print(
            f"    memory_id="
            f"{memory['memory_id']}"
        )

        print(
            f"    confidence="
            f"{memory['confidence']:.2f}, "
            f"strength="
            f"{memory['statement_strength']}"
        )

        print(
            f"    importance="
            f"{memory['importance']:.2f}, "
            f"utility="
            f"{memory['future_utility']:.2f}"
        )

        print(
            f"    temporal_scope="
            f"{memory['temporal_scope']}, "
            f"modality="
            f"{memory['modality']}, "
            f"fact_status="
            f"{memory['fact_status']}"
        )


def print_state(
    state: AgentState,
) -> None:
    print("\nCurrent Agent State:")

    print(
        f"  mood_valence   = "
        f"{state.mood_valence:.2f}"
    )

    print(
        f"  energy          = "
        f"{state.energy:.2f}"
    )

    print(
        f"  social_drive    = "
        f"{state.social_drive:.2f}"
    )

    print(
        f"  stress          = "
        f"{state.stress:.2f}"
    )

    print(
        f"  disappointment  = "
        f"{state.disappointment:.2f}"
    )


def print_relationship(
    relationship: RelationshipState,
) -> None:
    print("\nCurrent Relationship:")

    print(
        f"  subject_id        = "
        f"{relationship.subject_id}"
    )

    print(
        f"  trust             = "
        f"{relationship.trust:.3f}"
    )

    print(
        f"  familiarity       = "
        f"{relationship.familiarity:.3f}"
    )

    print(
        f"  reciprocity       = "
        f"{relationship.reciprocity:.3f}"
    )

    print(
        f"  attachment        = "
        f"{relationship.attachment:.3f}"
    )

    print(
        f"  interaction_count = "
        f"{relationship.interaction_count}"
    )


def process_memory(
    event: Event,
    llm_client: LLMClient,
) -> None:
    try:
        analysis = analyze_event_memory(
            event,
            llm_client,
        )

    except Exception as exc:
        print(
            "\n[Memory Analyzer Error]"
        )

        print(
            f"{type(exc).__name__}: "
            f"{exc}"
        )

        return

    if not analysis.memory_worthy:
        print(
            "\nMemory Analyzer: "
            "nothing worth storing."
        )
        return

    print("\nMemory Analyzer:")

    for candidate in analysis.memories:
        try:
            memory, source = (
                create_memory_from_candidate(
                    event,
                    candidate,
                )
            )

            save_memory(
                memory,
                source,
            )

            print(
                f"  + "
                f"[{memory.memory_type}] "
                f"{memory.content}"
            )

            print(
                f"    strength="
                f"{memory.statement_strength}, "
                f"confidence="
                f"{memory.confidence:.2f}"
            )

            process_claim(
                memory,
                llm_client,
            )

        except Exception as exc:
            print(
                "  [Memory Save Error] "
                f"{type(exc).__name__}: "
                f"{exc}"
            )


def print_claims() -> None:
    claims = get_claims_for_subject(
        USER_ID
    )

    if not claims:
        print(
            "\nNo claims found."
        )
        return

    print(
        "\nClaims:"
    )

    for claim in claims:
        print(
            f"\n- {claim['canonical_text']}"
        )

        print(
            f"    claim_id="
            f"{claim['claim_id']}"
        )

        print(
            f"    type="
            f"{claim['claim_type']}"
        )

        print(
            f"    predicate="
            f"{claim['canonical_predicate']}"
        )

        print(
            f"    object="
            f"{claim['canonical_object']}"
        )

        print(
            f"    temporal_mode="
            f"{claim['temporal_mode']}"
        )

        print(
            f"    value_type="
            f"{claim['value_type']}"
        )

        evidence = get_claim_evidence(
            claim["claim_id"]
        )

        if not evidence:
            print(
                "      No evidence."
            )
            continue

        for item in evidence:
            print(
                f"      [{item['stance']}] "
                f"{item['memory_content']}"
            )

            value = item[
                "evidence_value"
            ]

            value_text = (
                str(value)
                if value is not None
                else "None"
            )

            label = item[
                "evidence_label"
            ]

            label_text = (
                str(label)
                if label is not None
                else "None"
            )

            print(
                f"        strength="
                f"{item['statement_strength']}, "
                f"value="
                f"{value_text}, "
                f"label="
                f"{label_text}, "
                f"memory_conf="
                f"{item['memory_confidence']:.2f}, "
                f"relation_conf="
                f"{item['relation_confidence']:.2f}"
            )

            print(
                f"        root_cause="
                f"{item['root_cause_id']}"
            )


def process_claim(
    memory,
    llm_client: LLMClient,
) -> None:
    """
    将一条正式 Memory 放入 Claim Layer。
    """

    if memory.subject_id is None:
        print(
            "    Claim Resolver: skipped "
            "(no subject_id)"
        )
        return

    try:
        claim, evidences, resolution = (
            process_memory_claim(
                memory,
                llm_client,
            )
        )

    except Exception as exc:
        print(
            "    [Claim Resolver Error] "
            f"{type(exc).__name__}: "
            f"{exc}"
        )

        return

    if resolution.action == "skip":
        print(
            "    Claim Resolver: skipped"
        )

        print(
            f"    reason="
            f"{resolution.reason}"
        )

        return

    print(
        f"    Claim: "
        f"{claim.canonical_text}"
    )

    print(
        f"    action="
        f"{resolution.action}, "
        f"stance="
        f"{resolution.stance}, "
        f"relation_conf="
        f"{resolution.relation_confidence:.2f}"
    )

    if resolution.evidence_value is not None:
        print(
            f"    evidence_value="
            f"{resolution.evidence_value}"
        )

    if resolution.evidence_label is not None:
        print(
            f"    evidence_label="
            f"{resolution.evidence_label}"
        )


def resolve_existing_memories(
    llm_client: LLMClient,
) -> None:
    memories = get_unresolved_memories(
        limit=50
    )

    if not memories:
        print(
            "\nNo unresolved memories."
        )
        return

    print(
        f"\nResolving "
        f"{len(memories)} memories..."
    )

    for row in memories:
        memory = get_memory(
            row["memory_id"]
        )

        if memory is None:
            continue

        if memory.subject_id is None:
            print(
                f"\nDeferred: "
                f"{memory.content}"
            )

            mark_memory_claim_resolved(
                memory.memory_id,
                "deferred",
                (
                    "Memory has no resolvable subject_id. "
                    "Third-party/entity resolution is "
                    "not supported in the current MVP."
                ),
            )

            continue

        print(
            f"\nMemory: "
            f"{memory.content}"
        )

        process_claim(
            memory,
            llm_client,
        )


def print_beliefs() -> None:
    beliefs = get_all_current_beliefs(
        limit=100
    )

    if not beliefs:
        print(
            "\nNo current beliefs found."
        )
        return

    print(
        "\nCurrent Beliefs:"
    )

    for belief in beliefs:
        print(
            f"\n- {belief['canonical_text']}"
        )

        print(
            f"    claim_id="
            f"{belief['claim_id']}"
        )

        print(
            f"    type="
            f"{belief['belief_type']}"
        )

        print(
            f"    scalar_value="
            f"{belief['scalar_value']}"
        )

        print(
            f"    categorical_value="
            f"{belief['categorical_value']}"
        )

        print(
            f"    boolean_value="
            f"{belief['boolean_value']}"
        )

        print(
            f"    confidence="
            f"{belief['confidence']:.3f}"
        )

        print(
            f"    status="
            f"{belief['status']}"
        )

        print(
            f"    evidence_count="
            f"{belief['evidence_count']}"
        )

        print(
            f"    independent_roots="
            f"{belief['independent_root_count']}"
        )

        print(
            f"    resolver_version="
            f"{belief['resolver_version']}"
        )


def main() -> None:
    initialize_database()

    state = load_agent_state()

    relationship = load_relationship(
        USER_ID
    )

    try:
        llm_client = create_llm_client()

    except Exception as exc:
        print(
            "\nLLM configuration error:"
        )

        print(
            f"{type(exc).__name__}: "
            f"{exc}"
        )

        return

    print("=" * 50)

    print(
        "Personality Agent MVP v0.1"
    )

    print("=" * 50)

    print(
        f"\nDatabase: "
        f"{DATABASE_PATH}"
    )

    print(
        "\nCommands:\n"
        "  /history         Show recent events\n"
        "  /state           Show current agent state\n"
        "  /relationship    Show relationship state\n"
        "  /memories        Show recent memories\n"
        "  /claims          Show claims and evidence\n"
        "  /resolve-claims  Resolve old memories\n"
        "  /reset-claims    Reset Claims\n"
        "  /beliefs         Show current beliefs\n"
        # "  /test-belief     \n"
        "  /resolve-beliefs \n"
        "  /exit            Exit program"
    )

    while True:
        try:
            message = input(
                "\nYou > "
            ).strip()

            if not message:
                continue

            if message == "/exit":
                print("\nBye.")
                break

            if message == "/history":
                print_recent_events()
                continue

            if message == "/state":
                print_state(state)
                continue

            if message == "/relationship":
                print_relationship(
                    relationship
                )
                continue

            if message == "/memories":
                print_memories()
                continue

            if message == "/claims":
                print_claims()
                continue

            if message == "/resolve-claims":
                resolve_existing_memories(
                    llm_client
                )
                continue

            if message == "/reset-claims":
                reset_claim_layer()

                print(
                    "\nClaim layer cleared."
                )

                print(
                    "Events and Memories were preserved."
                )

                continue

            if message == "/beliefs":
                print_beliefs()
                continue


            # if message == "/test-belief":
            #     create_test_belief()
            #     continue

            # if message == "/resolve-beliefs":
            #     resolve_scalar_beliefs()
            #     continue

            if message == "/resolve-beliefs":
                resolve_scalar_beliefs()
                resolve_categorical_beliefs()
                continue
                

            event = (
                create_user_message_event(
                    message
                )
            )

            save_event(
                event
            )

            state = (
                apply_event_to_state(
                    state,
                    event,
                )
            )

            save_agent_state(
                state
            )

            relationship = (
                apply_event_to_relationship(
                    relationship,
                    event,
                )
            )

            save_relationship(
                relationship
            )

            print("\nEvent saved:")

            print(
                f"  event_id      = "
                f"{event.event_id}"
            )

            print(
                f"  root_cause_id = "
                f"{event.root_cause_id}"
            )

            process_memory(
                event,
                llm_client,
            )

        except KeyboardInterrupt:
            print("\n\nBye.")
            break


if __name__ == "__main__":
    main()