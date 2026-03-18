"""
EduScout Vapi Caller Tool (Day 11 — Mystery Shopper)
Triggers outbound phone calls via Vapi.ai and processes call results.

Flow:
1. Agent decides it needs to call a school (info not in DB/docs)
2. This tool triggers a Vapi outbound call (fire-and-forget)
3. Vapi calls the school, has a conversation, hangs up
4. Vapi sends end-of-call-report webhook → server.py processes it
5. Server sends WhatsApp update to the parent with the results

Env vars required:
    VAPI_API_KEY
    VAPI_ASSISTANT_ID  (the school inquiry assistant)
    VAPI_PHONE_NUMBER_ID  (Vapi phone number to call FROM)
"""

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger("eduscout.vapi_caller")

VAPI_API_KEY = os.environ.get("VAPI_API_KEY", "")
VAPI_ASSISTANT_ID = os.environ.get("VAPI_ASSISTANT_ID", "")
VAPI_PHONE_NUMBER_ID = os.environ.get("VAPI_PHONE_NUMBER_ID", "")
VAPI_BASE_URL = "https://api.vapi.ai"


def trigger_outbound_call(
    school_phone: str,
    question: str,
    school_name: str,
    task_id: Optional[int] = None,
) -> dict:
    """
    Trigger an outbound Vapi call to a school.

    Args:
        school_phone: The school's phone number (E.164 format: +1XXXXXXXXXX)
        question: What to ask the school (injected into assistant context)
        school_name: Name of the school (for context)
        task_id: Our internal agent_tasks.id for tracking

    Returns:
        {"success": bool, "call_id": str, "message": str}
    """
    if not VAPI_API_KEY:
        logger.error("VAPI_API_KEY not set")
        return {"success": False, "call_id": None, "message": "Vapi API key not configured"}

    if not VAPI_ASSISTANT_ID:
        logger.error("VAPI_ASSISTANT_ID not set")
        return {"success": False, "call_id": None, "message": "Vapi assistant not configured"}

    if not VAPI_PHONE_NUMBER_ID:
        logger.error("VAPI_PHONE_NUMBER_ID not set")
        return {"success": False, "call_id": None, "message": "Vapi phone number not configured"}

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json",
    }

    # Override the assistant's first message and system prompt to include
    # the specific question and school context
    payload = {
        "assistantId": VAPI_ASSISTANT_ID,
        "phoneNumberId": VAPI_PHONE_NUMBER_ID,
        "customer": {
            "number": school_phone,
        },
        "assistantOverrides": {
            "firstMessage": (
                f"Hello, I'm calling from EduScout, a school advisory service. "
                f"I'm helping a parent who is interested in {school_name}. "
                f"I have a quick question: {question}"
            ),
            # Pass metadata so we can link the call back to our task
            "metadata": {
                "task_id": str(task_id) if task_id else "",
                "school_name": school_name,
                "question": question,
            },
        },
    }

    try:
        resp = requests.post(
            f"{VAPI_BASE_URL}/call/phone",
            headers=headers,
            json=payload,
            timeout=15,
        )

        if resp.status_code in (200, 201):
            data = resp.json()
            call_id = data.get("id", "")
            logger.info(f"Vapi call triggered: call_id={call_id}, school={school_name}, task={task_id}")
            return {
                "success": True,
                "call_id": call_id,
                "message": f"Call initiated to {school_name}",
            }
        else:
            error_msg = resp.text[:500]
            logger.error(f"Vapi call failed: {resp.status_code} - {error_msg}")
            return {
                "success": False,
                "call_id": None,
                "message": f"Failed to initiate call: {error_msg}",
            }

    except Exception as e:
        logger.exception(f"Vapi call error: {e}")
        return {
            "success": False,
            "call_id": None,
            "message": f"Error initiating call: {str(e)}",
        }


def get_call_details(call_id: str) -> Optional[dict]:
    """
    Fetch call details from Vapi API (transcript, status, etc).
    Use this as a fallback if the webhook didn't capture the full data.

    Returns the full call object or None.
    """
    if not VAPI_API_KEY or not call_id:
        return None

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.get(
            f"{VAPI_BASE_URL}/call/{call_id}",
            headers=headers,
            timeout=15,
        )

        if resp.status_code == 200:
            return resp.json()
        else:
            logger.error(f"Failed to get call {call_id}: {resp.status_code}")
            return None

    except Exception as e:
        logger.exception(f"Error fetching call {call_id}: {e}")
        return None


def extract_call_findings(call_data: dict) -> dict:
    """
    Extract the useful information from a completed Vapi call.

    Args:
        call_data: The full call object from Vapi API

    Returns:
        {
            "transcript": str,  # Full conversation text
            "summary": str,     # AI-generated summary (if available)
            "status": str,      # "ended", "failed", etc.
            "ended_reason": str,
            "duration_seconds": int,
            "cost": float,
            "school_answers": str,  # Extracted answers from the bot messages
        }
    """
    transcript = call_data.get("transcript", "")
    summary = call_data.get("summary", "")
    status = call_data.get("status", "unknown")
    ended_reason = call_data.get("endedReason", "")
    cost = call_data.get("cost", 0)

    # Calculate duration
    started = call_data.get("startedAt", "")
    ended = call_data.get("endedAt", "")
    duration = 0
    if started and ended:
        try:
            from datetime import datetime
            start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(ended.replace("Z", "+00:00"))
            duration = int((end_dt - start_dt).total_seconds())
        except Exception:
            pass

    # Extract what the school (bot/AI on the other end) actually said
    # In messages, the school's responses come from "bot" role
    messages = call_data.get("messages", [])
    school_responses = []
    for msg in messages:
        role = msg.get("role", "")
        text = msg.get("message", "")
        # The "bot" messages in an outbound call are from OUR assistant
        # The "user" messages are from the school receptionist
        # But wait — in the test call, "user" = the person who picked up (school)
        # and "bot" = our Vapi assistant
        # So the useful info is in what the "user" (school) said back
        if role == "user" and text:
            school_responses.append(text)

    school_answers = "\n".join(school_responses) if school_responses else ""

    return {
        "transcript": transcript,
        "summary": summary,
        "status": status,
        "ended_reason": ended_reason,
        "duration_seconds": duration,
        "cost": cost,
        "school_answers": school_answers,
    }
