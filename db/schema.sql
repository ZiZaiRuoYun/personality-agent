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


CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,

    subject_id TEXT NOT NULL,

    claim_type TEXT NOT NULL,

    canonical_subject TEXT NOT NULL,
    canonical_predicate TEXT NOT NULL,
    canonical_object TEXT,

    canonical_text TEXT NOT NULL,

    temporal_mode TEXT NOT NULL,

    value_type TEXT NOT NULL,

    status TEXT NOT NULL,

    created_at TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS claim_evidence (
    claim_evidence_id TEXT PRIMARY KEY,

    claim_id TEXT NOT NULL,
    memory_id TEXT NOT NULL,

    root_cause_id TEXT NOT NULL,

    stance TEXT NOT NULL,

    statement_strength INTEGER NOT NULL,

    memory_confidence REAL NOT NULL,
    relation_confidence REAL NOT NULL,

    evidence_value INTEGER,

    evidence_label TEXT,

    observed_at TEXT,

    created_at TEXT NOT NULL,

    FOREIGN KEY (claim_id)
        REFERENCES claims(claim_id),

    FOREIGN KEY (memory_id)
        REFERENCES memories(memory_id),

    UNIQUE (
        claim_id,
        memory_id,
        root_cause_id
    )
);


CREATE INDEX IF NOT EXISTS idx_claims_subject
ON claims(subject_id);


CREATE INDEX IF NOT EXISTS idx_claims_predicate
ON claims(canonical_predicate);


CREATE INDEX IF NOT EXISTS idx_claims_status
ON claims(status);


CREATE INDEX IF NOT EXISTS idx_claim_evidence_claim
ON claim_evidence(claim_id);


CREATE INDEX IF NOT EXISTS idx_claim_evidence_memory
ON claim_evidence(memory_id);


CREATE INDEX IF NOT EXISTS idx_claim_evidence_root
ON claim_evidence(root_cause_id);


CREATE TABLE IF NOT EXISTS claim_resolution_log (
    memory_id TEXT PRIMARY KEY,

    action TEXT NOT NULL,

    reason TEXT,

    resolved_at TEXT NOT NULL,

    FOREIGN KEY (memory_id)
        REFERENCES memories(memory_id)
);



CREATE TABLE IF NOT EXISTS current_beliefs (
    belief_id TEXT PRIMARY KEY,

    claim_id TEXT NOT NULL UNIQUE,

    belief_type TEXT NOT NULL,

    scalar_value REAL,
    categorical_value TEXT,
    boolean_value INTEGER,

    confidence REAL NOT NULL,

    status TEXT NOT NULL,

    evidence_count INTEGER NOT NULL,
    independent_root_count INTEGER NOT NULL,

    computed_at TEXT NOT NULL,

    resolver_version TEXT NOT NULL,

    FOREIGN KEY (claim_id)
        REFERENCES claims(claim_id)
        ON DELETE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_current_beliefs_claim
ON current_beliefs(claim_id);


CREATE INDEX IF NOT EXISTS idx_current_beliefs_status
ON current_beliefs(status);