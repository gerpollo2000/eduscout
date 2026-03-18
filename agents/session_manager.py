"""
EduScout Session Manager (Day 8 — Added methodology)
LangChain tools for creating and updating parent search sessions.
"""

import logging
from typing import Optional

from langchain_core.tools import tool

from tools.database import (
    create_search_session,
    update_session,
    get_active_session,
)

logger = logging.getLogger("eduscout.session_manager")


@tool
def create_search_session_tool(
    parent_id: int,
    target_level: Optional[str] = None,
    budget_max: Optional[float] = None,
    preferred_neighborhood: Optional[str] = None,
    special_needs: Optional[str] = None,
    interests: Optional[str] = None,
    religious_preference: Optional[str] = None,
    needs_wheelchair_access: Optional[bool] = None,
    preferred_methodology: Optional[str] = None,
) -> str:
    """Create a new search session to save the parent's school preferences.

    Call this ONCE when you first learn what the parent is looking for.

    Args:
        parent_id: The parent's ID from the system context.
        target_level: 'elementary', 'middle', 'high', 'k12', or 'university'.
        budget_max: Max annual tuition in USD. 0 for free/public only.
        preferred_neighborhood: Manhattan neighborhood like 'Chelsea', 'Upper East Side'.
        special_needs: Comma-separated: 'autism', 'adhd', 'dyslexia', 'wheelchair'.
        interests: Comma-separated: 'theater', 'robotics', 'basketball', 'music', 'art'.
        religious_preference: 'secular', 'catholic', 'jewish', 'episcopal'.
        needs_wheelchair_access: True if wheelchair accessibility required.
        preferred_methodology: 'traditional', 'progressive', 'montessori', 'waldorf', 'IB', 'stem_focus'.
    """
    try:
        existing = get_active_session(parent_id)
        if existing:
            return f"Session already exists (id={existing['id']}). Use update_search_session to modify."

        kwargs = {}
        for key, val in [
            ("target_level", target_level), ("budget_max", budget_max),
            ("preferred_neighborhood", preferred_neighborhood),
            ("religious_preference", religious_preference),
            ("needs_wheelchair_access", needs_wheelchair_access),
            ("preferred_methodology", preferred_methodology),
        ]:
            if val is not None:
                kwargs[key] = val

        # Convert comma-separated strings to arrays
        if special_needs is not None:
            updates["special_needs"] = [s.strip() for s in special_needs.split(',')]
        if interests is not None:
            updates["interests"] = [i.strip() for i in interests.split(',')]

        session = create_search_session(parent_id, **kwargs)
        saved = [f"{k}={v}" for k, v in kwargs.items()]
        return f"Session created (id={session['id']}). Saved: {', '.join(saved)}."

    except Exception as e:
        logger.exception(f"create_search_session error: {e}")
        return f"Error creating session: {str(e)}"


@tool
def update_search_session_tool(
    parent_id: int,
    target_level: Optional[str] = None,
    budget_max: Optional[float] = None,
    preferred_neighborhood: Optional[str] = None,
    special_needs: Optional[str] = None,
    interests: Optional[str] = None,
    religious_preference: Optional[str] = None,
    needs_wheelchair_access: Optional[bool] = None,
    preferred_methodology: Optional[str] = None,
) -> str:
    """Update the parent's search session with new or changed preferences.

    Call when the parent mentions new preferences. Only pass changed fields.

    Args:
        parent_id: The parent's ID from system context.
        target_level: Updated school level.
        budget_max: Updated max annual tuition.
        preferred_neighborhood: Updated neighborhood.
        special_needs: Updated special needs (comma-separated, replaces previous).
        interests: Updated interests (comma-separated, replaces previous).
        religious_preference: Updated religious preference.
        needs_wheelchair_access: Updated wheelchair requirement.
        preferred_methodology: Updated methodology preference.
    """
    try:
        session = get_active_session(parent_id)
        if not session:
            return "No active session. Use create_search_session first."

        updates = {}
        for key, val in [
            ("target_level", target_level), ("budget_max", budget_max),
            ("preferred_neighborhood", preferred_neighborhood),
            ("special_needs", special_needs), ("interests", interests),
            ("religious_preference", religious_preference),
            ("needs_wheelchair_access", needs_wheelchair_access),
            ("preferred_methodology", preferred_methodology),
        ]:
            if val is not None:
                updates[key] = val

        if not updates:
            return "No fields to update."

        update_session(session["id"], **updates)
        updated = [f"{k}={v}" for k, v in updates.items()]
        return f"Session {session['id']} updated: {', '.join(updated)}."

    except Exception as e:
        logger.exception(f"update_search_session error: {e}")
        return f"Error updating session: {str(e)}"


session_tools = [create_search_session_tool, update_search_session_tool]
