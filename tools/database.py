"""
EduScout Database Tool (Day 8 fix — dynamic create_search_session)
PostgreSQL connection pool and query functions for the agent.
"""

import os
import json
import logging
from typing import Optional
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool, extras

logger = logging.getLogger(__name__)

_pool: Optional[pool.ThreadedConnectionPool] = None


def get_pool() -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL environment variable is not set")
        _pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=database_url,
        )
        logger.info("Database connection pool created")
    return _pool


@contextmanager
def get_connection():
    p = get_pool()
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def get_db_connection():
    """Get a raw connection (caller must close). Used by diagnostic scripts."""
    p = get_pool()
    return p.getconn()


def query(sql: str, params: tuple = ()) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


def execute(sql: str, params: tuple = ()) -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount


def execute_returning(sql: str, params: tuple = ()) -> dict:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return dict(cur.fetchone())


# ============================================================
# SCHOOL QUERIES
# ============================================================

def search_schools(
    level: Optional[str] = None,
    budget_max: Optional[float] = None,
    neighborhood: Optional[str] = None,
    borough: Optional[str] = None,
    school_type: Optional[str] = None,
    religious_orientation: Optional[str] = None,
    has_wheelchair_access: Optional[bool] = None,
    has_special_needs_support: Optional[bool] = None,
    has_scholarships: Optional[bool] = None,
    has_transportation: Optional[bool] = None,
    has_lunch_program: Optional[bool] = None,
    methodology: Optional[str] = None,
    limit: int = 10,
) -> list[dict]:
    conditions = []
    params = []

    if level:
        conditions.append("(s.level = %s OR s.level = 'k12')")
        params.append(level)

    if budget_max is not None:
        conditions.append("(s.annual_tuition_max <= %s OR s.annual_tuition_max = 0)")
        params.append(budget_max)

    if neighborhood:
        conditions.append("LOWER(s.neighborhood) LIKE LOWER(%s)")
        params.append(f"%{neighborhood}%")

    if borough:
        conditions.append("LOWER(s.borough) LIKE LOWER(%s)")
        params.append(f"%{borough}%")

    if school_type:
        conditions.append("s.school_type = %s")
        params.append(school_type)

    if religious_orientation:
        conditions.append("s.religious_orientation = %s")
        params.append(religious_orientation)

    if has_wheelchair_access:
        conditions.append("s.has_wheelchair_access = TRUE")

    if has_special_needs_support:
        conditions.append("s.has_special_needs_support = TRUE")

    if has_scholarships:
        conditions.append("(s.has_scholarships = TRUE OR s.has_financial_aid = TRUE)")

    if has_transportation:
        conditions.append("s.has_transportation = TRUE")

    if has_lunch_program:
        conditions.append("s.has_lunch_program = TRUE")

    if methodology:
        conditions.append("LOWER(s.methodology) LIKE LOWER(%s)")
        params.append(f"%{methodology}%")

    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    params.append(limit)

    sql = f"""
        SELECT
            s.*,
            COALESCE(
                (SELECT json_agg(json_build_object('name', e.name, 'category', e.category))
                 FROM school_extracurriculars e WHERE e.school_id = s.id),
                '[]'::json
            ) AS extracurriculars,
            COALESCE(
                (SELECT json_agg(json_build_object('sport', sp.sport_name, 'tournaments', sp.competes_in_tournaments))
                 FROM school_sports sp WHERE sp.school_id = s.id),
                '[]'::json
            ) AS sports,
            COALESCE(
                (SELECT json_agg(json_build_object('condition', sn.condition_supported, 'type', sn.support_type, 'details', sn.details))
                 FROM school_special_needs sn WHERE sn.school_id = s.id),
                '[]'::json
            ) AS special_needs_programs
        FROM schools s
        WHERE {where_clause}
        ORDER BY s.annual_tuition_max ASC NULLS LAST
        LIMIT %s
    """

    return query(sql, tuple(params))


def get_school_by_slug(slug: str) -> Optional[dict]:
    results = query("""
        SELECT s.*,
            COALESCE(
                (SELECT json_agg(json_build_object('name', e.name, 'category', e.category, 'description', e.description, 'cost', e.additional_cost))
                 FROM school_extracurriculars e WHERE e.school_id = s.id),
                '[]'::json
            ) AS extracurriculars,
            COALESCE(
                (SELECT json_agg(json_build_object('sport', sp.sport_name, 'tournaments', sp.competes_in_tournaments, 'details', sp.tournament_details))
                 FROM school_sports sp WHERE sp.school_id = s.id),
                '[]'::json
            ) AS sports,
            COALESCE(
                (SELECT json_agg(json_build_object('condition', sn.condition_supported, 'type', sn.support_type, 'details', sn.details))
                 FROM school_special_needs sn WHERE sn.school_id = s.id),
                '[]'::json
            ) AS special_needs_programs,
            COALESCE(
                (SELECT json_agg(json_build_object('cert', tc.certification_name, 'pct', tc.percentage_certified))
                 FROM school_teacher_certifications tc WHERE tc.school_id = s.id),
                '[]'::json
            ) AS teacher_certifications
        FROM schools s WHERE s.slug = %s
    """, (slug,))
    return results[0] if results else None


def get_school_by_id(school_id: int) -> Optional[dict]:
    results = query("SELECT * FROM schools WHERE id = %s", (school_id,))
    return results[0] if results else None


# ============================================================
# PARENT / SESSION QUERIES
# ============================================================

def get_or_create_parent(whatsapp_number: str, name: Optional[str] = None) -> dict:
    existing = query("SELECT * FROM parents WHERE whatsapp_number = %s", (whatsapp_number,))
    if existing:
        return existing[0]
    return execute_returning(
        "INSERT INTO parents (whatsapp_number, name) VALUES (%s, %s) RETURNING *",
        (whatsapp_number, name),
    )


# ALLOWED columns for search_sessions — keeps us safe from SQL injection
# while being flexible enough to handle all fields
ALLOWED_SESSION_COLUMNS = {
    "target_level", "student_name", "budget_max", "interests",
    "special_needs", "religious_preference", "preferred_neighborhood",
    "needs_wheelchair_access", "preferred_methodology", "needs_transportation",
    "needs_lunch_program", "additional_requirements", "intake_complete",
    "status",
}


def create_search_session(parent_id: int, **kwargs) -> dict:
    """Create a new search session. Accepts ANY valid session column dynamically."""
    # Filter to only allowed columns
    filtered = {k: v for k, v in kwargs.items() if k in ALLOWED_SESSION_COLUMNS and v is not None}

    if not filtered:
        # Create minimal session
        return execute_returning(
            "INSERT INTO search_sessions (parent_id) VALUES (%s) RETURNING *",
            (parent_id,),
        )

    columns = ["parent_id"] + list(filtered.keys())
    placeholders = ["%s"] * len(columns)
    values = [parent_id] + list(filtered.values())

    sql = f"""INSERT INTO search_sessions ({', '.join(columns)})
              VALUES ({', '.join(placeholders)}) RETURNING *"""

    logger.info(f"[db] create_search_session: columns={columns}, values={values}")
    return execute_returning(sql, tuple(values))


def get_active_session(parent_id: int) -> Optional[dict]:
    results = query(
        "SELECT * FROM search_sessions WHERE parent_id = %s AND status = 'active' ORDER BY created_at DESC LIMIT 1",
        (parent_id,),
    )
    return results[0] if results else None


def update_session(session_id: int, **kwargs) -> int:
    """Update search session fields. Only allowed columns are accepted."""
    # Filter to allowed columns for safety
    filtered = {k: v for k, v in kwargs.items() if k in ALLOWED_SESSION_COLUMNS}

    if not filtered:
        logger.warning(f"[db] update_session called with no valid fields: {kwargs}")
        return 0

    set_clauses = []
    params = []
    for key, value in filtered.items():
        set_clauses.append(f"{key} = %s")
        params.append(value)
    set_clauses.append("updated_at = NOW()")
    params.append(session_id)

    sql = f"UPDATE search_sessions SET {', '.join(set_clauses)} WHERE id = %s"
    logger.info(f"[db] update_session id={session_id}: {filtered}")
    return execute(sql, tuple(params))


# ============================================================
# CONVERSATION MEMORY
# ============================================================

def save_message(parent_id: int, role: str, content: str, session_id: Optional[int] = None, metadata: Optional[dict] = None):
    execute(
        """INSERT INTO conversation_messages (parent_id, session_id, role, content, metadata)
           VALUES (%s, %s, %s, %s, %s)""",
        (parent_id, session_id, role, content, json.dumps(metadata or {})),
    )


def get_recent_messages(parent_id: int, limit: int = 20) -> list[dict]:
    return query(
        """SELECT role, content, created_at FROM conversation_messages
           WHERE parent_id = %s ORDER BY created_at DESC LIMIT %s""",
        (parent_id, limit),
    )


# ============================================================
# ASYNC TASKS
# ============================================================

def create_agent_task(
    task_type: str,
    question: str,
    school_id: Optional[int] = None,
    session_id: Optional[int] = None,
    parent_id: Optional[int] = None,
) -> dict:
    return execute_returning(
        """INSERT INTO agent_tasks (task_type, question, school_id, session_id, parent_id)
           VALUES (%s, %s, %s, %s, %s) RETURNING *""",
        (task_type, question, school_id, session_id, parent_id),
    )


def update_task_status(task_id: int, status: str, result: Optional[str] = None, error: Optional[str] = None):
    execute(
        """UPDATE agent_tasks SET status = %s, result = %s, error_message = %s,
           completed_at = CASE WHEN %s IN ('completed','failed') THEN NOW() ELSE NULL END
           WHERE id = %s""",
        (status, result, error, status, task_id),
    )


def get_pending_tasks(parent_id: int) -> list[dict]:
    return query(
        "SELECT * FROM agent_tasks WHERE parent_id = %s AND status IN ('pending', 'in_progress')",
        (parent_id,),
    )


# ============================================================
# RECOMMENDATIONS
# ============================================================

def save_recommendation(session_id: int, school_id: int, match_score: float, reasoning: str, **kwargs) -> dict:
    return execute_returning(
        """INSERT INTO recommendations (session_id, school_id, match_score, reasoning,
            commute_from_home_minutes, commute_from_work_minutes,
            traffic_adjusted_home_minutes, traffic_adjusted_work_minutes)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *""",
        (
            session_id, school_id, match_score, reasoning,
            kwargs.get("commute_from_home_minutes"),
            kwargs.get("commute_from_work_minutes"),
            kwargs.get("traffic_adjusted_home_minutes"),
            kwargs.get("traffic_adjusted_work_minutes"),
        ),
    )


def get_session_recommendations(session_id: int) -> list[dict]:
    return query(
        """SELECT r.*, s.name AS school_name, s.neighborhood, s.annual_tuition_max,
                  s.has_wheelchair_access, s.has_special_needs_support
           FROM recommendations r
           JOIN schools s ON s.id = r.school_id
           WHERE r.session_id = %s
           ORDER BY r.match_score DESC""",
        (session_id,),
    )