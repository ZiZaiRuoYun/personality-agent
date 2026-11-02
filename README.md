# Personality Agent

Personality Agent is an experimental stateful AI agent system.

The goal is to build an AI agent whose identity, memory, relationship state,
and personality development persist outside of the language model itself.

Rather than relying on a large system prompt to simulate continuity, the project
treats continuity as explicit application state stored and updated by the agent
runtime.

---

## MVP v0.1 Goals

The first MVP focuses on four core capabilities:

1. Persistent internal state
2. Long-term memory with selective recall
3. Relationship-aware behavior
4. Evidence-controlled personality evolution without self-reinforcing drift

The language model is treated as a reasoning and language-generation component,
not as the sole storage location for identity or memory.

---

## Current Progress

### Milestone 0.1.1 — Persistent Event Foundation ✅

Implemented:

- Unified `Event` model
- Unique `event_id`
- `root_cause_id` for provenance tracking
- `causal_parent_id`
- `epistemic_status`
- `confidence`
- `scope`
- Arbitrary metadata
- SQLite event persistence
- Event history survives application restart
- `/history` CLI command

Current event flow:

```text
User Input
    ↓
Event
    ↓
SQLite
    ↓
Persistent History
```

---

### Milestone 0.1.2 — Persistent Agent State ✅

Implemented:

- `AgentState`
- Persistent short-term internal state
- Deterministic state updates from events
- State survives application restart
- `/state` CLI command

Current state dimensions:

```text
mood_valence     -1.0 ~ 1.0
energy            0.0 ~ 1.0
social_drive      0.0 ~ 1.0
stress            0.0 ~ 1.0
disappointment    0.0 ~ 1.0
```

Important design rule:

```text
State != Personality
```

State represents relatively fast-changing internal conditions such as mood,
energy, stress, and disappointment.

---

### Milestone 0.1.3 — Relationship Engine ✅

Implemented:

- `RelationshipState`
- One relationship state per `subject_id`
- Deterministic relationship updates from user interaction
- Relationship persistence across application restart
- `/relationship` CLI command

Current relationship dimensions:

```text
trust
familiarity
reciprocity
attachment
interaction_count
last_interaction_at
```

Important design rule:

```text
Agent State != Relationship State
```

For example:

```text
Agent may currently feel disappointed
without permanently reducing trust.
```

This separation allows temporary emotional reactions and long-term relationship
judgments to evolve independently.

---

## Current Database

SQLite is currently used directly through Python's built-in `sqlite3` module.

Current tables:

```text
events
agent_state
relationships
```

Database file:

```text
data/personality_agent.db
```

The database is intentionally excluded from Git because it may eventually
contain private conversation history, memories, relationship state, and
personality information.

---

## Current Project Structure

```text
personality-agent/
├─ app/
│  ├─ __init__.py
│  └─ main.py
│
├─ data/
│  └─ personality_agent.db
│
├─ db/
│  ├─ __init__.py
│  ├─ database.py
│  └─ schema.sql
│
├─ models/
│  ├─ __init__.py
│  ├─ event.py
│  ├─ state.py
│  └─ relationship.py
│
├─ relationship/
│  ├─ __init__.py
│  └─ engine.py
│
├─ state/
│  ├─ __init__.py
│  └─ engine.py
│
├─ tests/
│
├─ .gitignore
├─ .python-version
├─ pyproject.toml
├─ README.md
└─ uv.lock
```

---

## Environment

Current development environment:

```text
Python 3.13.13
uv
SQLite 3.53.1
Git
VS Code
Windows
```

The project uses a local virtual environment:

```text
.venv/
```

Activate it in PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Run the project:

```powershell
python -m app.main
```

Or without activating the environment:

```powershell
uv run python -m app.main
```

---

## Current CLI Commands

```text
/history
/state
/relationship
/exit
```

---

## Architecture So Far

```text
                 Incoming User Message
                         │
                         ▼
                       Event
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
     Event Store     Agent State   Relationship
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                       SQLite
```

At this stage, no external LLM is required.

This is intentional: the current milestones validate continuity independently
of any specific model provider.

Later, the runtime can connect to:

```text
DeepSeek
OpenAI
Qwen
Ollama
other LLM providers
```

without moving identity, memory, or relationship state into the model itself.

---

## Core Design Principle

The project follows this idea:

> Presence comes from state continuity, not computation continuity.

The agent does not need to continuously run in order to remain the same agent.

Its continuity comes from persistent state, memories, relationships, evidence,
and versioned personality data.

---

## Provenance Principle

Any information that may influence long-term behavior should eventually be
traceable back to its evidence.

Important fields already present in `Event` include:

```text
event_id
root_cause_id
causal_parent_id
source
epistemic_status
confidence
scope
timestamp
```

This is intended to prevent self-generated thoughts from recursively becoming
their own independent evidence.

Example:

```text
User Event A
    ↓
Agent Response B
    ↓
Reflection C
    ↓
Daily Reflection D
```

If B, C, and D all originate from A, they should share:

```text
root_cause_id = A
```

Therefore they still count as one independent root cause rather than four
independent pieces of evidence.

---

## Next Milestone

### Milestone 0.1.4 — Memory Engine

The next milestone will introduce a real distinction between:

```text
Raw Event History
```

and:

```text
Long-Term Memory
```

The initial Memory Engine is expected to support at least:

```text
Episodic Memory
Semantic Memory
Relationship Memory
```

Each memory should preserve provenance and should not simply duplicate every
conversation turn.

Expected first-stage responsibilities:

- Decide whether an event is worth remembering
- Convert selected events into memory records
- Store memory importance and confidence
- Preserve source event / root cause links
- Retrieve relevant memories for a new event
- Avoid treating every raw event as long-term memory

A later stage may add:

- Memory consolidation
- Decay
- Contradiction handling
- Semantic merging
- Embedding-based retrieval
- Reflection-generated memory
- Memory revision with provenance

---

## Planned Later Components

After the Memory Engine:

```text
Context Builder
Drive System
Behavior Policy
LLM Adapter
Inner Mind
Reflection
Evidence Gate
Adaptive Persona
Persona Versioning
Heartbeat
```

The MVP will continue to add these incrementally instead of implementing the
entire final architecture at once.
