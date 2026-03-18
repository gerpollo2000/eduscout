"""
EduScout Webhook Server (Day 8 — Preference Extraction + Session Auto-Update)
FastAPI application that receives:
  - YCloud WhatsApp inbound messages
  - Vapi.ai call completion callbacks (future)

Day 8 changes:
- Preference extractor runs on EVERY message before calling agent
- Session auto-created/updated from extracted preferences
- Guaranteed data capture regardless of LLM tool-calling behavior
- Timeout 90s to match agent timeout chain
"""

import os
import sys
import json
import logging
import boto3
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from typing import Optional

from fastapi import FastAPI, Request, Response, BackgroundTasks
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from tools.whatsapp import parse_inbound_message, send_text_message, mark_as_read
from tools.database import (
    get_or_create_parent,
    save_message,
    get_active_session,
    get_recent_messages,
    create_search_session,
    update_session,
    query,
    execute,
    update_task_status,
)
from tools.preference_extractor import extract_preferences, merge_preferences
from tools.vapi_caller import get_call_details, extract_call_findings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("eduscout.webhook")

AGENT_ENDPOINT = os.environ.get("AGENT_ENDPOINT", "")
DIGITALOCEAN_API_TOKEN = os.environ.get("DIGITALOCEAN_API_TOKEN", "")

app = FastAPI(title="EduScout Webhook Server", version="0.3.0")


@app.get("/")
async def root():
    return {"status": "ok", "service": "eduscout-webhook", "version": "0.3.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


# ============================================================
# PREFERENCE EXTRACTION + SESSION UPDATE (SAFETY NET)
# ============================================================

def ensure_session_updated(parent_id: int, message_text: str) -> Optional[dict]:
    """
    Extract preferences from the message and update/create session.
    Runs on EVERY message. Guarantees data capture.
    """
    extracted = extract_preferences(message_text)

    if not extracted:
        return get_active_session(parent_id)

    session = get_active_session(parent_id)

    if session:
        current = {}
        for key in ["target_level", "special_needs", "interests",
                     "preferred_neighborhood", "preferred_methodology",
                     "religious_preference"]:
            if session.get(key):
                current[key] = session[key]
        if session.get("budget_max"):
            current["budget_max"] = float(session["budget_max"])
        if session.get("needs_wheelchair_access"):
            current["needs_wheelchair_access"] = session["needs_wheelchair_access"]

        merged = merge_preferences(current, extracted)

        updates = {}
        for key, value in merged.items():
            if current.get(key) != value:
                updates[key] = value

        if updates:
            logger.info(f"[session] Auto-updating session {session['id']}: {updates}")
            try:
                update_session(session["id"], **updates)
            except Exception as e:
                logger.error(f"[session] Failed to auto-update: {e}")

        return get_active_session(parent_id)

    else:
        if extracted:
            logger.info(f"[session] Auto-creating session for parent {parent_id}: {extracted}")
            try:
                return create_search_session(parent_id, **extracted)
            except Exception as e:
                logger.error(f"[session] Failed to auto-create: {e}")
                return None

    return session


# ============================================================
# WHATSAPP WEBHOOK
# ============================================================

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        return Response(status_code=400)

    logger.info(f"Webhook received: type={payload.get('type', 'unknown')}")

    message = parse_inbound_message(payload)
    if message is None:
        return Response(status_code=200)

    sender = message["sender"]
    text = message["text"]
    name = message["name"]

    logger.info(f"Message from {name} ({sender}): {text}")
    background_tasks.add_task(process_message, sender, text, name, message["message_id"])
    return Response(status_code=200)


async def process_message(sender: str, text: str, name: str, message_id: str):
    try:
        await mark_as_read(message_id)

        parent = get_or_create_parent(sender, name)
        parent_id = parent["id"]

        save_message(parent_id, "user", text)

        # === DAY 8: EXTRACT & SAVE PREFERENCES BEFORE CALLING AGENT ===
        session = ensure_session_updated(parent_id, text)
        logger.info(f"[session] After extraction: id={session.get('id') if session else 'none'}")

        recent = get_recent_messages(parent_id, limit=10)
        history = list(reversed(recent))

        conversation_context = []
        for msg in history:
            conversation_context.append({
                "role": msg["role"],
                "content": msg["content"],
            })

        agent_response = await call_agent(
            prompt=text,
            parent_id=parent_id,
            parent_name=name,
            parent_phone=sender,
            session=session,
            history=conversation_context,
        )

        if agent_response:
            save_message(parent_id, "assistant", agent_response)

            if len(agent_response) > 4000:
                chunks = split_message(agent_response, 4000)
                for chunk in chunks:
                    await send_text_message(sender, chunk)
            else:
                await send_text_message(sender, agent_response)

            logger.info(f"Reply sent to {sender}: {agent_response[:100]}...")
        else:
            fallback = (
                "I apologize, I'm experiencing a temporary issue. "
                "Please try again in a moment."
            )
            save_message(parent_id, "assistant", fallback)
            await send_text_message(sender, fallback)
            logger.error(f"Agent returned empty response for {sender}")

    except Exception as e:
        logger.exception(f"Error processing message from {sender}: {e}")
        try:
            await send_text_message(
                sender,
                "I'm sorry, something went wrong. Please try again shortly."
            )
        except Exception:
            pass


def split_message(text: str, max_len: int = 4000) -> list:
    if len(text) <= max_len:
        return [text]

    chunks = []
    current = ""

    paragraphs = text.split("\n\n")
    for para in paragraphs:
        if len(current) + len(para) + 2 > max_len:
            if current:
                chunks.append(current.strip())
                current = ""
            if len(para) > max_len:
                sentences = para.split(". ")
                for sent in sentences:
                    if len(current) + len(sent) + 2 > max_len:
                        if current:
                            chunks.append(current.strip())
                        current = sent + ". "
                    else:
                        current += sent + ". "
            else:
                current = para
        else:
            current += ("\n\n" if current else "") + para

    if current.strip():
        chunks.append(current.strip())

    return chunks if chunks else [text[:max_len]]


async def call_agent(
    prompt: str,
    parent_id: int,
    parent_name: str,
    parent_phone: str,
    session: Optional[dict] = None,
    history: Optional[list] = None,
) -> Optional[str]:
    import httpx

    if not AGENT_ENDPOINT:
        logger.error("AGENT_ENDPOINT not configured")
        return None

    payload = {
        "prompt": prompt,
        "parent_id": parent_id,
        "parent_name": parent_name,
        "parent_phone": parent_phone,
        "history": history or [],
    }

    if session:
        payload["session"] = {
            "id": session["id"],
            "target_level": session.get("target_level"),
            "budget_max": float(session["budget_max"]) if session.get("budget_max") else None,
            "interests": session.get("interests"),
            "special_needs": session.get("special_needs"),
            "religious_preference": session.get("religious_preference"),
            "preferred_neighborhood": session.get("preferred_neighborhood"),
            "preferred_methodology": session.get("preferred_methodology"),
            "needs_wheelchair_access": session.get("needs_wheelchair_access"),
            "intake_complete": session.get("intake_complete"),
        }

    headers = {"Content-Type": "application/json"}

    if "agents.do-ai.run" in AGENT_ENDPOINT:
        headers["Authorization"] = f"Bearer {DIGITALOCEAN_API_TOKEN}"

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                AGENT_ENDPOINT,
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                logger.error(f"Agent error: {response.status_code} {response.text}")
                return None

            result = response.json()

            if isinstance(result, str):
                return result
            elif isinstance(result, dict):
                return (
                    result.get("response")
                    or result.get("output")
                    or result.get("message")
                    or result.get("content")
                    or json.dumps(result)
                )
            else:
                return str(result)

    except httpx.TimeoutException:
        logger.error("Agent request timed out (90s)")
        return None
    except Exception as e:
        logger.exception(f"Agent call failed: {e}")
        return None


# ============================================================
# VAPI.AI WEBHOOK (Day 11 — Mystery Shopper)
# ============================================================

@app.post("/webhook/vapi")
async def vapi_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
    except Exception:
        return Response(status_code=400)

    message = payload.get("message", {})
    event_type = message.get("type", "")

    logger.info(f"Vapi webhook: type={event_type}")

    if event_type == "end-of-call-report":
        background_tasks.add_task(process_call_report, message)
    elif event_type == "status-update" and message.get("status") == "ended":
        # Fallback — if end-of-call-report doesn't come, process from status-update
        call = message.get("call", {})
        call_id = call.get("id", "")
        if call_id:
            background_tasks.add_task(process_call_ended_fallback, call_id)

    return Response(status_code=200)


async def process_call_report(message: dict):
    """
    Process Vapi end-of-call-report webhook.
    Extract transcript, update agent_task, send WhatsApp to parent.
    """
    try:
        # Extract data from the report
        call_data = message.get("call", {})
        call_id = call_data.get("id", "")
        transcript = message.get("transcript", "") or call_data.get("transcript", "")
        summary = ""

        # Capture endedReason for bad-outcome detection
        ended_reason = (
            message.get("endedReason")
            or call_data.get("endedReason")
            or ""
        )
        logger.info(f"Call {call_id} endedReason={ended_reason!r}")

        analysis = message.get("analysis", {})
        if analysis:
            summary = analysis.get("summary", "")

        # Extract the artifact messages for structured transcript
        artifact = message.get("artifact", {})
        messages = artifact.get("messages", [])

        # If we don't have a transcript from the report, try the call object
        if not transcript and call_id:
            from tools.vapi_caller import get_call_details, extract_call_findings
            full_call = get_call_details(call_id)
            if full_call:
                transcript = full_call.get("transcript", "")
                ended_reason = ended_reason or full_call.get("endedReason", "")
                findings = extract_call_findings(full_call)
                summary = findings.get("school_answers", "")

        # For bad outcomes we still want to notify the parent even without a transcript
        task = _find_task_by_call_id(call_id)
        if not task:
            metadata = call_data.get("assistantOverrides", {}).get("metadata", {})
            task_id = metadata.get("task_id", "")
            if task_id:
                tasks = query("SELECT * FROM agent_tasks WHERE id = %s", (int(task_id),))
                task = tasks[0] if tasks else None

        if not task:
            logger.warning(f"No matching agent_task for call {call_id}")
            return

        # Mark task failed for known bad outcomes, otherwise completed
        bad_ended_reasons = {"customer-did-not-answer", "customer-busy", "voicemail"}
        task_status = "failed" if ended_reason in bad_ended_reasons else "completed"

        update_task_status(
            task["id"],
            task_status,
            result=summary or (transcript[:2000] if transcript else f"Call ended: {ended_reason}"),
        )

        if transcript:
            try:
                execute(
                    "UPDATE agent_tasks SET call_transcript = %s WHERE id = %s",
                    (transcript, task["id"]),
                )
            except Exception as e:
                logger.error(f"Failed to save transcript: {e}")

        # Send WhatsApp update to the parent
        if task.get("parent_id"):
            await _send_call_results_to_parent(task, transcript, summary, ended_reason)

    except Exception as e:
        logger.exception(f"Error processing call report: {e}")

async def process_call_ended_fallback(call_id: str):
    """
    Fallback: If we didn't get a clean end-of-call-report,
    fetch the call details from Vapi API and process.
    """
    import asyncio
    # Wait a few seconds for Vapi to finalize the call data
    await asyncio.sleep(5)

    try:
        from tools.vapi_caller import get_call_details, extract_call_findings

        call_data = get_call_details(call_id)
        if not call_data:
            logger.warning(f"Could not fetch call {call_id} from Vapi API")
            return

        # Check if we already processed this via end-of-call-report
        task = _find_task_by_call_id(call_id)
        if task and task.get("status") == "completed":
            logger.info(f"Call {call_id} already processed, skipping fallback")
            return

        ended_reason = call_data.get("endedReason", "")
        findings = extract_call_findings(call_data)
        transcript = findings.get("transcript", "")
        school_answers = findings.get("school_answers", "")

        if task:
            bad_ended_reasons = {"customer-did-not-answer", "customer-busy", "voicemail"}
            task_status = "failed" if ended_reason in bad_ended_reasons else "completed"

            update_task_status(
                task["id"],
                task_status,
                result=school_answers or transcript[:2000] or f"Call ended: {ended_reason}",
            )
            try:
                execute(
                    "UPDATE agent_tasks SET call_transcript = %s WHERE id = %s",
                    (transcript, task["id"]),
                )
            except Exception:
                pass

            if task.get("parent_id"):
                await _send_call_results_to_parent(task, transcript, school_answers, ended_reason)

    except Exception as e:
        logger.exception(f"Fallback processing error for call {call_id}: {e}")

def _find_task_by_call_id(call_id: str):
    """Find an agent_task by its vapi_call_id."""
    if not call_id:
        return None
    tasks = query(
        "SELECT * FROM agent_tasks WHERE vapi_call_id = %s",
        (call_id,),
    )
    return tasks[0] if tasks else None



async def _send_call_results_to_parent(task: dict, transcript: str, summary: str, ended_reason: str = ""):
    """
    Send the call results back to the parent via WhatsApp.
    Handles bad outcomes: no answer, busy, voicemail, too-short calls.
    """
    parent_id = task.get("parent_id")
    if not parent_id:
        return

    # Get parent's WhatsApp number
    parents = query("SELECT whatsapp_number, name FROM parents WHERE id = %s", (parent_id,))
    if not parents:
        return

    parent = parents[0]
    phone = parent["whatsapp_number"]

    # Get school name from task
    school_name = "the school"
    if task.get("school_id"):
        schools = query("SELECT name FROM schools WHERE id = %s", (task["school_id"],))
        if schools:
            school_name = schools[0]["name"]

    question = task.get("question", "your question")

    # ------------------------------------------------------------------
    # Check if the call actually succeeded before building a success msg
    # ------------------------------------------------------------------
    BAD_OUTCOMES = {
        "customer-did-not-answer": (
            f"📞 *Update on {school_name}*\n\n"
            f"I tried calling about: \"{question}\"\n\n"
            "Unfortunately, no one picked up. 📵\n\n"
            "Would you like me to try again later, or is there another way I can help?"
        ),
        "customer-busy": (
            f"📞 *Update on {school_name}*\n\n"
            f"I tried calling about: \"{question}\"\n\n"
            "The line was busy when I called. 🔁\n\n"
            "Should I try again in a bit?"
        ),
        "voicemail": (
            f"📞 *Update on {school_name}*\n\n"
            f"I tried calling about: \"{question}\"\n\n"
            "The call went to voicemail, so I wasn't able to speak with anyone directly. 📬\n\n"
            "Would you like me to try again at a different time?"
        ),
    }

    if ended_reason in BAD_OUTCOMES:
        full_message = BAD_OUTCOMES[ended_reason]
        try:
            save_message(parent_id, "assistant", full_message)
            await send_text_message(phone, full_message)
            logger.info(f"Bad-outcome message ({ended_reason}) sent to {phone} for task {task['id']}")
        except Exception as e:
            logger.exception(f"Failed to send bad-outcome message to {phone}: {e}")
        return

    # If transcript is very short or empty, the call probably failed silently
    transcript_too_short = len((transcript or "").strip()) < 20

    if transcript_too_short and ended_reason not in ("assistant-ended-call", "customer-ended-call"):
        full_message = (
            f"📞 *Update on {school_name}*\n\n"
            f"I tried calling about: \"{question}\"\n\n"
            "Unfortunately, I couldn't get through — the call wasn't answered "
            "or was too brief to get useful information.\n\n"
            "Would you like me to try again later, or is there another way I can help?"
        )
        try:
            save_message(parent_id, "assistant", full_message)
            await send_text_message(phone, full_message)
            logger.info(f"Short-transcript fallback sent to {phone} for task {task['id']}")
        except Exception as e:
            logger.exception(f"Failed to send short-transcript message to {phone}: {e}")
        return

    # ------------------------------------------------------------------
    # Normal success path
    # ------------------------------------------------------------------
    message_parts = [
        f"📞 *Update: I just spoke with {school_name}!*\n",
        f"Your question: \"{question}\"\n",
    ]

    if summary:
        message_parts.append(f"Here's what they said:\n{summary}\n")
    elif transcript:
        message_parts.append(f"Here's the conversation summary:\n{transcript[:1500]}\n")

    message_parts.append(
        "Want me to update your school comparison with this new info, "
        "or do you have follow-up questions?"
    )

    full_message = "\n".join(message_parts)

    try:
        save_message(parent_id, "assistant", full_message)
        await send_text_message(phone, full_message)
        logger.info(f"Call results sent to {phone} for task {task['id']}")
    except Exception as e:
        logger.exception(f"Failed to send call results to {phone}: {e}")
# ============================================================
# TEST ENDPOINTS
# ============================================================

@app.post("/test/send")
async def test_send(request: Request):
    data = await request.json()
    to = data.get("to")
    text = data.get("text")
    if not to or not text:
        return {"error": "Missing 'to' or 'text' field"}
    result = await send_text_message(to, text)
    return result


@app.post("/test/agent")
async def test_agent(request: Request):
    data = await request.json()
    result = await call_agent(
        prompt=data.get("prompt", "hello"),
        parent_id=data.get("parent_id", 0),
        parent_name=data.get("parent_name", "Test User"),
        parent_phone="+10000000000",
    )
    return {"agent_response": result}


@app.post("/test/extract")
async def test_extract(request: Request):
    """Test the preference extractor directly."""
    data = await request.json()
    text = data.get("text", "")
    extracted = extract_preferences(text)
    return {"text": text, "extracted": extracted}


# ============================================================
# SCHOOL PORTAL (Day 17 — Two-Sided Marketplace)
# ============================================================

# --- Serve the portal HTML ---

@app.get("/portal")
async def school_portal():
    """Serve the school upload portal."""
    portal_path = "/opt/eduscout/school_portal/index.html"
    if os.path.exists(portal_path):
        return FileResponse(portal_path, media_type="text/html")
    return {"error": "Portal page not found"}


# --- List schools for the dropdown ---

@app.get("/api/schools")
async def list_schools():
    """Return all schools for the portal dropdown."""
    from tools.database import query
    schools = query("SELECT id, name FROM schools ORDER BY name ASC")
    return schools


# --- Upload file to DO Spaces ---

def get_spaces_client():
    """Get a boto3 client for DigitalOcean Spaces."""
    return boto3.client(
        "s3",
        region_name=os.environ.get("DO_SPACES_REGION", "nyc3"),
        endpoint_url=f"https://{os.environ.get('DO_SPACES_REGION', 'nyc3')}.digitaloceanspaces.com",
        aws_access_key_id=os.environ.get("DO_SPACES_KEY", ""),
        aws_secret_access_key=os.environ.get("DO_SPACES_SECRET", ""),
    )


@app.post("/api/upload")
async def upload_document(request: Request):
    """
    Upload a PDF to DO Spaces and record it in the database.
    The Knowledge Base will auto-index new files in the bucket.
    """
    from fastapi import UploadFile, File, Form

    form = await request.form()
    file = form.get("file")
    school_id = form.get("school_id")
    document_type = form.get("document_type", "other")
    uploader_email = form.get("uploader_email", "")

    if not file or not school_id:
        return Response(
            content=json.dumps({"error": "Missing file or school_id"}),
            status_code=400,
            media_type="application/json",
        )

    # Validate file
    filename = file.filename
    allowed_extensions = ('.pdf', '.doc', '.docx', '.txt', '.csv', '.xlsx', '.xls',
                          '.html', '.md', '.rtf', '.odt', '.xml', '.json', '.jsonl',
                          '.epub', '.rst', '.tsv', '.eml')
    if not filename.lower().endswith(allowed_extensions):
        return Response(
            content=json.dumps({"error": "This filetype is not accepted"}),
            status_code=400,
            media_type="application/json",
        )

    # Read file content
    content = await file.read()
    if len(content) > 25 * 1024 * 1024:
        return Response(
            content=json.dumps({"error": "File too large (max 25 MB)"}),
            status_code=400,
            media_type="application/json",
        )

    # Get school info for the path
    from tools.database import query as db_query, execute_returning
    schools = db_query("SELECT slug, name FROM schools WHERE id = %s", (int(school_id),))
    if not schools:
        return Response(
            content=json.dumps({"error": "School not found"}),
            status_code=404,
            media_type="application/json",
        )

    school_slug = schools[0]["slug"]
    school_name = schools[0]["name"]

    # Upload to DO Spaces
    # Path: school-slug/document-type/filename.pdf
    import time
    timestamp = int(time.time())
    safe_filename = filename.replace(" ", "_").lower()
    spaces_key = f"{school_slug}/{document_type}/{timestamp}_{safe_filename}"

    bucket = os.environ.get("DO_SPACES_BUCKET", "eduscout-docs")

    try:
        s3 = get_spaces_client()
        s3.put_object(
            Bucket=bucket,
            Key=spaces_key,
            Body=content,
            ContentType=file.content_type or "application/octet-stream",
            ACL="private",
        )
        logger.info(f"Uploaded to Spaces: {bucket}/{spaces_key}")
    except Exception as e:
        logger.exception(f"Spaces upload error: {e}")
        return Response(
            content=json.dumps({"error": f"Upload failed: {str(e)}"}),
            status_code=500,
            media_type="application/json",
        )

    # Record in database
    spaces_full_url = f"https://{bucket}.{os.environ.get('DO_SPACES_REGION', 'nyc3')}.digitaloceanspaces.com/{spaces_key}"
    try:
        doc = execute_returning(
            """INSERT INTO school_documents
               (school_id, document_type, title, file_name, spaces_url)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING id, file_name, document_type""",
            (
                int(school_id),
                document_type,
                filename.replace(".pdf", "").replace("_", " ").title(),
                filename,
                spaces_full_url,
            ),
        )
        logger.info(f"Document recorded: id={doc['id']}, school={school_name}")
    except Exception as e:
        logger.exception(f"DB insert error: {e}")
        # File is already in Spaces, so just log the DB error
        doc = {"id": None, "file_name": filename}

    return {
        "success": True,
        "document_id": doc.get("id"),
        "file_name": filename,
        "school": school_name,
        "message": f"'{filename}' uploaded for {school_name}. It will be indexed by the AI shortly.",
    }
