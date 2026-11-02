from db.database import (
    DATABASE_PATH,
    get_recent_events,
    initialize_database,
    load_agent_state,
    load_relationship,
    save_agent_state,
    save_event,
    save_relationship,
)

from models.event import Event
from models.relationship import RelationshipState
from models.state import AgentState

from relationship.engine import (
    apply_event_to_relationship,
)

from state.engine import apply_event_to_state


USER_ID = "user_001"


def create_user_message_event(
    message: str,
) -> Event:
    """
    将用户输入转换成统一 Event。
    """

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
    events = get_recent_events(limit=5)

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

    print(
        f"  updated_at      = "
        f"{state.updated_at}"
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

    print(
        f"  last_interaction  = "
        f"{relationship.last_interaction_at}"
    )


def main() -> None:
    initialize_database()

    state = load_agent_state()

    relationship = load_relationship(
        USER_ID
    )

    print("=" * 50)
    print("Personality Agent MVP v0.1")
    print("=" * 50)

    print(
        f"\nDatabase: {DATABASE_PATH}"
    )

    print(
        "\nCommands:\n"
        "  /history       Show recent events\n"
        "  /state         Show current agent state\n"
        "  /relationship  Show relationship state\n"
        "  /exit          Exit program"
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

            event = create_user_message_event(
                message
            )

            save_event(event)

            state = apply_event_to_state(
                state,
                event,
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

            print_state(state)

            print_relationship(
                relationship
            )

        except KeyboardInterrupt:
            print("\n\nBye.")
            break


if __name__ == "__main__":
    main()