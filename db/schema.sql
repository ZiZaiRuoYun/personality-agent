CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,

    root_cause_id TEXT NOT NULL,

    event_type TEXT NOT NULL,
    source TEXT NOT NULL,

    actor_id TEXT,
    content TEXT,

    timestamp TEXT NOT NULL,

    causal_parent_id TEXT,

    epistemic_status TEXT NOT NULL,
    confidence REAL NOT NULL,

    scope TEXT NOT NULL,

    metadata_json TEXT NOT NULL DEFAULT '{}',

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX IF NOT EXISTS idx_events_root_cause
ON events(root_cause_id);


CREATE INDEX IF NOT EXISTS idx_events_timestamp
ON events(timestamp);


CREATE INDEX IF NOT EXISTS idx_events_actor
ON events(actor_id);


CREATE INDEX IF NOT EXISTS idx_events_type
ON events(event_type);

CREATE TABLE IF NOT EXISTS agent_state (
    state_id INTEGER PRIMARY KEY CHECK (state_id = 1),

    mood_valence REAL NOT NULL,
    energy REAL NOT NULL,
    social_drive REAL NOT NULL,
    stress REAL NOT NULL,
    disappointment REAL NOT NULL,

    updated_at TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS relationships (
    subject_id TEXT PRIMARY KEY,

    trust REAL NOT NULL,
    familiarity REAL NOT NULL,
    reciprocity REAL NOT NULL,
    attachment REAL NOT NULL,

    interaction_count INTEGER NOT NULL,

    last_interaction_at TEXT,

    updated_at TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS memories (
    memory_id TEXT PRIMARY KEY,

    memory_type TEXT NOT NULL,

    subject_id TEXT,

    content TEXT NOT NULL,

    epistemic_status TEXT NOT NULL,

    confidence REAL NOT NULL,

    importance REAL NOT NULL,
    future_utility REAL NOT NULL,
    relationship_relevance REAL NOT NULL,

    statement_strength INTEGER NOT NULL,

    observed_at TEXT,

    temporal_scope TEXT NOT NULL,

    valid_from TEXT,
    valid_until TEXT,

    modality TEXT NOT NULL,
    fact_status TEXT NOT NULL,

    created_at TEXT NOT NULL,

    access_count INTEGER NOT NULL DEFAULT 0,

    last_accessed_at TEXT
);


CREATE TABLE IF NOT EXISTS memory_sources (
    memory_id TEXT NOT NULL,

    event_id TEXT NOT NULL,
    root_cause_id TEXT NOT NULL,

    source_role TEXT NOT NULL,
    contribution_weight REAL NOT NULL,

    created_at TEXT NOT NULL,

    PRIMARY KEY (memory_id, event_id),

    FOREIGN KEY (memory_id)
        REFERENCES memories(memory_id),

    FOREIGN KEY (event_id)
        REFERENCES events(event_id)
);


CREATE INDEX IF NOT EXISTS idx_memories_type
ON memories(memory_type);


CREATE INDEX IF NOT EXISTS idx_memories_subject
ON memories(subject_id);


CREATE INDEX IF NOT EXISTS idx_memories_created_at
ON memories(created_at);


CREATE INDEX IF NOT EXISTS idx_memory_sources_root
ON memory_sources(root_cause_id);


CREATE INDEX IF NOT EXISTS idx_memory_sources_event
ON memory_sources(event_id);