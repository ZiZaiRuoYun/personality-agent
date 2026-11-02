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