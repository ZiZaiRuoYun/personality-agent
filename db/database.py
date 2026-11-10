import json
import sqlite3
from pathlib import Path

from models.event import Event

from models.state import AgentState

from models.relationship import RelationshipState

from models.memory import Memory
from models.memory_source import MemorySource

from models.claim import Claim
from models.claim_evidence import ClaimEvidence

from models.current_belief import (
    CurrentBelief,
)


# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# data/personality_agent.db
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "personality_agent.db"

# db/schema.sql
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """
    创建 SQLite 数据库连接。
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    # SQLite 默认不会强制执行 Foreign Key。
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection

def initialize_database() -> None:
    """
    根据 schema.sql 初始化数据库，
    并执行 MVP 所需的轻量 schema migration。
    """

    with open(
        SCHEMA_PATH,
        "r",
        encoding="utf-8",
    ) as schema_file:
        schema_sql = schema_file.read()

    with get_connection() as connection:
        connection.executescript(
            schema_sql
        )

        ensure_schema_migrations(
            connection
        )

        connection.commit()


def get_table_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> set[str]:
    """
    获取 SQLite 表已有字段。
    """

    rows = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return {
        row["name"]
        for row in rows
    }


def ensure_schema_migrations(
    connection: sqlite3.Connection,
) -> None:
    """
    MVP 阶段的轻量数据库 Migration。
    """

    # -------------------------
    # claim_evidence migrations
    # -------------------------

    claim_evidence_columns = (
        get_table_columns(
            connection,
            "claim_evidence",
        )
    )

    if (
        "evidence_value"
        not in claim_evidence_columns
    ):
        connection.execute(
            """
            ALTER TABLE claim_evidence
            ADD COLUMN evidence_value INTEGER
            """
        )

    if (
        "evidence_label"
        not in claim_evidence_columns
    ):
        connection.execute(
            """
            ALTER TABLE claim_evidence
            ADD COLUMN evidence_label TEXT
            """
        )

    # -------------------------
    # claims migrations
    # -------------------------

    claims_columns = get_table_columns(
        connection,
        "claims",
    )

    if "value_type" not in claims_columns:
        connection.execute(
            """
            ALTER TABLE claims
            ADD COLUMN value_type TEXT
            NOT NULL
            DEFAULT 'unstructured'
            """
        )


def save_event(event: Event) -> None:
    """
    将 Event 写入 SQLite。
    """

    sql = """
    INSERT INTO events (
        event_id,
        root_cause_id,
        event_type,
        source,
        actor_id,
        content,
        timestamp,
        causal_parent_id,
        epistemic_status,
        confidence,
        scope,
        metadata_json
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    values = (
        event.event_id,
        event.root_cause_id,
        event.event_type,
        event.source,
        event.actor_id,
        event.content,
        event.timestamp.isoformat(),
        event.causal_parent_id,
        event.epistemic_status,
        event.confidence,
        event.scope,
        json.dumps(event.metadata, ensure_ascii=False),
    )

    with get_connection() as connection:
        connection.execute(sql, values)
        connection.commit()


def get_recent_events(limit: int = 10) -> list[dict]:
    """
    获取最近的 Event。

    暂时主要用于调试。
    """

    sql = """
    SELECT *
    FROM events
    ORDER BY timestamp DESC
    LIMIT ?
    """

    with get_connection() as connection:
        rows = connection.execute(sql, (limit,)).fetchall()

    return [dict(row) for row in rows]


# State
def load_agent_state() -> AgentState:
    """
    从数据库读取当前 Agent 状态。

    如果数据库还没有状态，则创建默认状态。
    """

    sql = """
    SELECT *
    FROM agent_state
    WHERE state_id = 1
    """

    with get_connection() as connection:
        row = connection.execute(sql).fetchone()

    if row is None:
        state = AgentState()
        save_agent_state(state)
        return state

    return AgentState(
        mood_valence=row["mood_valence"],
        energy=row["energy"],
        social_drive=row["social_drive"],
        stress=row["stress"],
        disappointment=row["disappointment"],
        updated_at=row["updated_at"],
    )


def save_agent_state(state: AgentState) -> None:
    """
    保存当前 Agent 状态。

    SQLite UPSERT：
    如果 state_id=1 已存在，就更新；
    如果不存在，就插入。
    """

    sql = """
    INSERT INTO agent_state (
        state_id,
        mood_valence,
        energy,
        social_drive,
        stress,
        disappointment,
        updated_at
    )
    VALUES (1, ?, ?, ?, ?, ?, ?)

    ON CONFLICT(state_id)
    DO UPDATE SET
        mood_valence = excluded.mood_valence,
        energy = excluded.energy,
        social_drive = excluded.social_drive,
        stress = excluded.stress,
        disappointment = excluded.disappointment,
        updated_at = excluded.updated_at
    """

    values = (
        state.mood_valence,
        state.energy,
        state.social_drive,
        state.stress,
        state.disappointment,
        state.updated_at.isoformat(),
    )

    with get_connection() as connection:
        connection.execute(sql, values)
        connection.commit()



def load_relationship(subject_id: str) -> RelationshipState:
    """
    从数据库加载某个用户对应的 RelationshipState。

    如果不存在，则创建默认关系。
    """

    sql = """
    SELECT *
    FROM relationships
    WHERE subject_id = ?
    """

    with get_connection() as connection:
        row = connection.execute(
            sql,
            (subject_id,),
        ).fetchone()

    if row is None:
        relationship = RelationshipState(
            subject_id=subject_id
        )

        save_relationship(relationship)

        return relationship

    return RelationshipState(
        subject_id=row["subject_id"],
        trust=row["trust"],
        familiarity=row["familiarity"],
        reciprocity=row["reciprocity"],
        attachment=row["attachment"],
        interaction_count=row["interaction_count"],
        last_interaction_at=row["last_interaction_at"],
        updated_at=row["updated_at"],
    )


def save_relationship(
    relationship: RelationshipState,
) -> None:
    """
    保存 RelationshipState。
    """

    sql = """
    INSERT INTO relationships (
        subject_id,
        trust,
        familiarity,
        reciprocity,
        attachment,
        interaction_count,
        last_interaction_at,
        updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)

    ON CONFLICT(subject_id)
    DO UPDATE SET
        trust = excluded.trust,
        familiarity = excluded.familiarity,
        reciprocity = excluded.reciprocity,
        attachment = excluded.attachment,
        interaction_count = excluded.interaction_count,
        last_interaction_at = excluded.last_interaction_at,
        updated_at = excluded.updated_at
    """

    values = (
        relationship.subject_id,
        relationship.trust,
        relationship.familiarity,
        relationship.reciprocity,
        relationship.attachment,
        relationship.interaction_count,
        (
            relationship.last_interaction_at.isoformat()
            if relationship.last_interaction_at
            else None
        ),
        relationship.updated_at.isoformat(),
    )

    with get_connection() as connection:
        connection.execute(sql, values)
        connection.commit()


def save_memory(
    memory: Memory,
    source: MemorySource,
) -> None:
    """
    保存 Memory 及其来源。

    两条记录必须放在同一个 transaction 中，
    避免出现 Memory 写成功但 MemorySource 写失败的情况。
    """

    memory_sql = """
    INSERT INTO memories (
        memory_id,
        memory_type,
        subject_id,
        content,
        epistemic_status,
        confidence,
        importance,
        future_utility,
        relationship_relevance,
        statement_strength,
        observed_at,
        temporal_scope,
        valid_from,
        valid_until,
        modality,
        fact_status,
        created_at,
        access_count,
        last_accessed_at
    )
    VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """

    memory_values = (
        memory.memory_id,
        memory.memory_type,
        memory.subject_id,
        memory.content,
        memory.epistemic_status,
        memory.confidence,
        memory.importance,
        memory.future_utility,
        memory.relationship_relevance,
        memory.statement_strength,
        (
            memory.observed_at.isoformat()
            if memory.observed_at
            else None
        ),
        memory.temporal_scope,
        (
            memory.valid_from.isoformat()
            if memory.valid_from
            else None
        ),
        (
            memory.valid_until.isoformat()
            if memory.valid_until
            else None
        ),
        memory.modality,
        memory.fact_status,
        memory.created_at.isoformat(),
        memory.access_count,
        (
            memory.last_accessed_at.isoformat()
            if memory.last_accessed_at
            else None
        ),
    )

    source_sql = """
    INSERT INTO memory_sources (
        memory_id,
        event_id,
        root_cause_id,
        source_role,
        contribution_weight,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """

    source_values = (
        source.memory_id,
        source.event_id,
        source.root_cause_id,
        source.source_role,
        source.contribution_weight,
        source.created_at.isoformat(),
    )

    with get_connection() as connection:
        try:
            connection.execute(
                memory_sql,
                memory_values,
            )

            connection.execute(
                source_sql,
                source_values,
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise


def get_recent_memories(
    limit: int = 10,
) -> list[dict]:
    """
    获取最近的长期记忆。
    """

    sql = """
    SELECT *
    FROM memories
    ORDER BY created_at DESC
    LIMIT ?
    """

    with get_connection() as connection:
        rows = connection.execute(
            sql,
            (limit,),
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def get_memory_sources(
    memory_id: str,
) -> list[dict]:
    """
    获取某个 Memory 的所有来源。
    """

    sql = """
    SELECT *
    FROM memory_sources
    WHERE memory_id = ?
    ORDER BY created_at ASC
    """

    with get_connection() as connection:
        rows = connection.execute(
            sql,
            (memory_id,),
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def get_claims_for_subject(
    subject_id: str,
    limit: int = 50,
) -> list[dict]:
    """
    获取某个主体当前已有的 Claim。
    """

    sql = """
    SELECT *
    FROM claims
    WHERE subject_id = ?
    ORDER BY created_at DESC
    LIMIT ?
    """

    with get_connection() as connection:
        rows = connection.execute(
            sql,
            (
                subject_id,
                limit,
            ),
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]

def get_claim(
    claim_id: str,
) -> dict | None:
    sql = """
    SELECT *
    FROM claims
    WHERE claim_id = ?
    """

    with get_connection() as connection:
        row = connection.execute(
            sql,
            (claim_id,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def save_claim_with_evidence(
    claim: Claim,
    evidences: list[ClaimEvidence],
) -> None:
    """
    创建新 Claim 时，
    Claim 与 Evidence 必须处于同一个 transaction。
    """

    claim_sql = """
    INSERT INTO claims (
        claim_id,
        subject_id,
        claim_type,
        canonical_subject,
        canonical_predicate,
        canonical_object,
        canonical_text,
        temporal_mode,
        value_type,
        status,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    claim_values = (
        claim.claim_id,
        claim.subject_id,
        claim.claim_type,
        claim.canonical_subject,
        claim.canonical_predicate,
        claim.canonical_object,
        claim.canonical_text,
        claim.temporal_mode,
        claim.value_type,
        claim.status,
        claim.created_at.isoformat(),
    )

    evidence_sql = """
    INSERT INTO claim_evidence (
        claim_evidence_id,
        claim_id,
        memory_id,
        root_cause_id,
        stance,
        statement_strength,
        memory_confidence,
        relation_confidence,
        evidence_value,
        evidence_label,
        observed_at,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    with get_connection() as connection:
        try:
            connection.execute(
                claim_sql,
                claim_values,
            )

            for evidence in evidences:
                evidence_values = (
                    evidence.claim_evidence_id,
                    evidence.claim_id,
                    evidence.memory_id,
                    evidence.root_cause_id,
                    evidence.stance,
                    evidence.statement_strength,
                    evidence.memory_confidence,
                    evidence.relation_confidence,
                    evidence.evidence_value,
                    evidence.evidence_label,
                    (
                        evidence.observed_at.isoformat()
                        if evidence.observed_at
                        else None
                    ),
                    evidence.created_at.isoformat(),
                )

                connection.execute(
                    evidence_sql,
                    evidence_values,
                )

            connection.commit()

        except Exception:
            connection.rollback()
            raise


def save_claim_evidences(
    evidences: list[ClaimEvidence],
) -> None:
    """
    给已有 Claim 追加证据。
    """

    sql = """
    INSERT INTO claim_evidence (
        claim_evidence_id,
        claim_id,
        memory_id,
        root_cause_id,
        stance,
        statement_strength,
        memory_confidence,
        relation_confidence,
        evidence_value,
        evidence_label,
        observed_at,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    with get_connection() as connection:
        try:
            for evidence in evidences:
                values = (
                    evidence.claim_evidence_id,
                    evidence.claim_id,
                    evidence.memory_id,
                    evidence.root_cause_id,
                    evidence.stance,
                    evidence.statement_strength,
                    evidence.memory_confidence,
                    evidence.relation_confidence,
                    evidence.evidence_value,
                    evidence.evidence_label,
                    (
                        evidence.observed_at.isoformat()
                        if evidence.observed_at
                        else None
                    ),
                    evidence.created_at.isoformat(),
                )

                connection.execute(
                    sql,
                    values,
                )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

    
def get_claim_evidence(
    claim_id: str,
) -> list[dict]:
    sql = """
    SELECT
        ce.*,
        m.content AS memory_content,
        m.temporal_scope,
        m.modality,
        m.fact_status
    FROM claim_evidence ce

    JOIN memories m
        ON m.memory_id = ce.memory_id

    WHERE ce.claim_id = ?

    ORDER BY ce.created_at ASC
    """

    with get_connection() as connection:
        rows = connection.execute(
            sql,
            (claim_id,),
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def get_unresolved_memories(
    limit: int = 50,
) -> list[dict]:
    """
    获取尚未经过 Claim Resolver 的 Memory。
    """

    sql = """
    SELECT m.*
    FROM memories m

    WHERE NOT EXISTS (
        SELECT 1
        FROM claim_resolution_log crl
        WHERE crl.memory_id = m.memory_id
    )

    ORDER BY m.created_at ASC

    LIMIT ?
    """

    with get_connection() as connection:
        rows = connection.execute(
            sql,
            (limit,),
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def get_memory(
    memory_id: str,
) -> Memory | None:
    sql = """
    SELECT *
    FROM memories
    WHERE memory_id = ?
    """

    with get_connection() as connection:
        row = connection.execute(
            sql,
            (memory_id,),
        ).fetchone()

    if row is None:
        return None

    return Memory(
        memory_id=row["memory_id"],
        memory_type=row["memory_type"],
        subject_id=row["subject_id"],
        content=row["content"],
        epistemic_status=(
            row["epistemic_status"]
        ),
        confidence=row["confidence"],
        importance=row["importance"],
        future_utility=(
            row["future_utility"]
        ),
        relationship_relevance=(
            row["relationship_relevance"]
        ),
        statement_strength=(
            row["statement_strength"]
        ),
        observed_at=row["observed_at"],
        temporal_scope=(
            row["temporal_scope"]
        ),
        valid_from=row["valid_from"],
        valid_until=row["valid_until"],
        modality=row["modality"],
        fact_status=row["fact_status"],
        created_at=row["created_at"],
        access_count=row["access_count"],
        last_accessed_at=(
            row["last_accessed_at"]
        ),
    )


def reset_claim_layer() -> None:
    """
    清空 Claim Layer。

    Event 和 Memory 保留。
    """

    with get_connection() as connection:
        try:
            connection.execute(
                "DELETE FROM current_beliefs"
            )

            connection.execute(
                "DELETE FROM claim_evidence"
            )

            connection.execute(
                "DELETE FROM claims"
            )

            connection.execute(
                "DELETE FROM claim_resolution_log"
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise


def mark_memory_claim_resolved(
    memory_id: str,
    action: str,
    reason: str | None,
) -> None:
    """
    标记某条 Memory 已经过 Claim Resolver。
    """

    sql = """
    INSERT INTO claim_resolution_log (
        memory_id,
        action,
        reason,
        resolved_at
    )
    VALUES (
        ?, ?, ?, CURRENT_TIMESTAMP
    )

    ON CONFLICT(memory_id)
    DO UPDATE SET
        action = excluded.action,
        reason = excluded.reason,
        resolved_at = CURRENT_TIMESTAMP
    """

    with get_connection() as connection:
        connection.execute(
            sql,
            (
                memory_id,
                action,
                reason,
            ),
        )

        connection.commit()


def save_current_belief(
    belief: CurrentBelief,
) -> None:
    """
    保存 / 更新一个 Claim 的 Current Belief。

    CurrentBelief 是派生缓存，
    所以按 claim_id UPSERT。
    """

    sql = """
    INSERT INTO current_beliefs (
        belief_id,
        claim_id,
        belief_type,
        scalar_value,
        categorical_value,
        boolean_value,
        confidence,
        status,
        evidence_count,
        independent_root_count,
        computed_at,
        resolver_version
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    ON CONFLICT(claim_id)
    DO UPDATE SET
        belief_id = excluded.belief_id,
        belief_type = excluded.belief_type,
        scalar_value = excluded.scalar_value,
        categorical_value = excluded.categorical_value,
        boolean_value = excluded.boolean_value,
        confidence = excluded.confidence,
        status = excluded.status,
        evidence_count = excluded.evidence_count,
        independent_root_count = excluded.independent_root_count,
        computed_at = excluded.computed_at,
        resolver_version = excluded.resolver_version
    """

    values = (
        belief.belief_id,
        belief.claim_id,
        belief.belief_type,
        belief.scalar_value,
        belief.categorical_value,
        (
            int(belief.boolean_value)
            if belief.boolean_value is not None
            else None
        ),
        belief.confidence,
        belief.status,
        belief.evidence_count,
        belief.independent_root_count,
        belief.computed_at.isoformat(),
        belief.resolver_version,
    )

    with get_connection() as connection:
        connection.execute(
            sql,
            values,
        )

        connection.commit()


def get_current_belief(
    claim_id: str,
) -> dict | None:
    sql = """
    SELECT *
    FROM current_beliefs
    WHERE claim_id = ?
    """

    with get_connection() as connection:
        row = connection.execute(
            sql,
            (claim_id,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def get_all_current_beliefs(
    limit: int = 100,
) -> list[dict]:
    sql = """
    SELECT
        cb.*,
        c.canonical_text,
        c.canonical_predicate,
        c.value_type
    FROM current_beliefs cb

    JOIN claims c
        ON c.claim_id = cb.claim_id

    ORDER BY cb.computed_at DESC

    LIMIT ?
    """

    with get_connection() as connection:
        rows = connection.execute(
            sql,
            (limit,),
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]

def clear_current_beliefs() -> None:
    """
    清空所有 Current Belief。

    不影响 Claim / Evidence。
    """

    with get_connection() as connection:
        connection.execute(
            "DELETE FROM current_beliefs"
        )

        connection.commit()