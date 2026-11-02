import json
import sqlite3
from pathlib import Path

from models.event import Event
from models.state import AgentState
from models.relationship import RelationshipState


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

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    # 让查询结果可以使用 row["column"] 形式读取
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database() -> None:
    """
    根据 schema.sql 初始化数据库。
    """

    with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
        schema_sql = schema_file.read()

    with get_connection() as connection:
        connection.executescript(schema_sql)
        connection.commit()


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