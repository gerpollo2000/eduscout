"""
EduScout Mystery Shopper Agent (Day 11)
LangChain tool for triggering phone calls to schools when info isn't
available in the database or documents.

Async flow:
1. Parent asks something we can't answer from DB/docs
2. Agent calls `call_school_for_info` tool
3. Tool creates an agent_task, triggers Vapi call, returns immediately
4. Parent gets "I'm calling them now, I'll message you back"
5. When call completes → webhook processes → WhatsApp update sent

Tool:
- call_school_for_info: Fire-and-forget call to a school
"""

import logging
from typing import Optional

from langchain_core.tools import tool

from tools.database import (
    query,
    get_school_by_slug,
    create_agent_task,
    update_task_status,
)
from tools.vapi_caller import trigger_outbound_call

logger = logging.getLogger("eduscout.mystery_shopper")


def _find_school_with_phone(school_name: str) -> Optional[dict]:
    """Find a school by name and verify it has a phone number."""
    # Try slug first
    school = get_school_by_slug(school_name.lower().replace(" ", "-"))
    if school and school.get("phone"):
        return school

    # Fuzzy name search
    results = query(
        "SELECT id, name, slug, phone, address FROM schools WHERE LOWER(name) LIKE LOWER(%s) AND phone IS NOT NULL LIMIT 3",
        (f"%{school_name}%",),
    )
    if results:
        return results[0]

    # Try without phone filter to give a better error message
    results_no_phone = query(
        "SELECT id, name, slug, phone FROM schools WHERE LOWER(name) LIKE LOWER(%s) LIMIT 1",
        (f"%{school_name}%",),
    )
    if results_no_phone and not results_no_phone[0].get("phone"):
        return {"_no_phone": True, "name": results_no_phone[0]["name"]}

    return None


@tool
def call_school_for_info(
    school_name: str,
    question: str,
    parent_id: int = 0,
    session_id: int = 0,
) -> str:
    """Call a school by phone to ask a question that isn't in our database or documents.

    Use this tool ONLY when:
    - The parent asks about something NOT in the database or school documents
    - You've already tried search_schools, get_school_details, and search_school_documents
    - The question requires direct verification from the school (e.g., specific availability,
      current policies, registration deadlines, specific accommodations)

    This is an ASYNC operation — the call happens in the background.
    Tell the parent you're calling and will message them back with the answer.

    Args:
        school_name: Name of the school to call (e.g., "Trinity School")
        question: The specific question to ask the school.
                  Be clear and specific, e.g.: "Do you have wheelchair ramps in all buildings?"
        parent_id: Parent's ID from session context.
        session_id: Active session ID from session context.
    """
    # 1. Find the school
    school = _find_school_with_phone(school_name)

    if not school:
        return (
            f"I couldn't find '{school_name}' in our database. "
            "Could you check the school name? You can ask me to search for schools first."
        )

    if school.get("_no_phone"):
        return (
            f"I found {school['name']} but I don't have their phone number on file. "
            "I can try looking up their contact information, or you could provide it."
        )

    # 2. Create a task record for tracking
    try:
        task = create_agent_task(
            task_type="phone_call",
            question=question,
            school_id=school.get("id"),
            session_id=session_id if session_id else None,
            parent_id=parent_id if parent_id else None,
        )
        task_id = task["id"]
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        task_id = None

    # 3. Trigger the Vapi call
    # Clean up phone number — ensure E.164 format
    phone = school["phone"].strip()
    # Handle various phone formats: (212) 873-1650, 212-873-1650, etc.
    phone_digits = "".join(c for c in phone if c.isdigit() or c == "+")
    if not phone_digits.startswith("+"):
        if phone_digits.startswith("1") and len(phone_digits) == 11:
            phone_digits = f"+{phone_digits}"
        elif len(phone_digits) == 10:
            phone_digits = f"+1{phone_digits}"
        else:
            phone_digits = f"+{phone_digits}"

    result = trigger_outbound_call(
        school_phone=phone_digits,
        question=question,
        school_name=school["name"],
        task_id=task_id,
    )

    if result["success"]:
        # Update task with call ID
        if task_id:
            try:
                from tools.database import execute
                execute(
                    "UPDATE agent_tasks SET status = 'in_progress', vapi_call_id = %s WHERE id = %s",
                    (result["call_id"], task_id),
                )
            except Exception as e:
                logger.error(f"Failed to update task with call ID: {e}")

        return (
            f"📞 I'm calling {school['name']} now to ask: \"{question}\"\n\n"
            "I'll message you back in a few minutes with their answer. "
            "Feel free to keep chatting or ask me anything else in the meantime!"
        )
    else:
        # Mark task as failed
        if task_id:
            try:
                update_task_status(task_id, "failed", error=result["message"])
            except Exception:
                pass

        return (
            f"I wasn't able to reach {school['name']} by phone right now. "
            f"Reason: {result['message']}\n\n"
            "I can try again later, or I can send them an email with your question instead. "
            "What would you prefer?"
        )


# Export
mystery_shopper_tools = [call_school_for_info]
