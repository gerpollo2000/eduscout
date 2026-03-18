"""
VAPI WEBHOOK HANDLER — Replace the existing stub in server.py

This code goes in server.py. It handles:
1. end-of-call-report: processes transcript, updates DB, sends WhatsApp to parent
2. status-update (ended): fallback if end-of-call-report doesn't arrive

Add these imports at the top of server.py:
    from tools.vapi_caller import get_call_details, extract_call_findings

Then replace the existing /webhook/vapi endpoint with the code below.
"""


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

        # Check for analysis summary
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
                findings = extract_call_findings(full_call)
                summary = findings.get("school_answers", "")

        if not transcript:
            logger.warning(f"No transcript found for call {call_id}")
            return

        # Find the agent_task linked to this call
        task = _find_task_by_call_id(call_id)
        if not task:
            # Try metadata
            metadata = call_data.get("assistantOverrides", {}).get("metadata", {})
            task_id = metadata.get("task_id", "")
            if task_id:
                tasks = query("SELECT * FROM agent_tasks WHERE id = %s", (int(task_id),))
                task = tasks[0] if tasks else None

        if not task:
            logger.warning(f"No matching agent_task for call {call_id}")
            return

        # Update the task with results
        update_task_status(
            task["id"],
            "completed",
            result=summary or transcript[:2000],
        )

        # Also save the full transcript
        try:
            execute(
                "UPDATE agent_tasks SET call_transcript = %s WHERE id = %s",
                (transcript, task["id"]),
            )
        except Exception as e:
            logger.error(f"Failed to save transcript: {e}")

        # Send WhatsApp update to the parent
        if task.get("parent_id"):
            await _send_call_results_to_parent(task, transcript, summary)

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

        findings = extract_call_findings(call_data)

        if task:
            update_task_status(
                task["id"],
                "completed",
                result=findings.get("school_answers", "") or findings.get("transcript", "")[:2000],
            )
            try:
                execute(
                    "UPDATE agent_tasks SET call_transcript = %s WHERE id = %s",
                    (findings.get("transcript", ""), task["id"]),
                )
            except Exception:
                pass

            if task.get("parent_id"):
                await _send_call_results_to_parent(
                    task,
                    findings.get("transcript", ""),
                    findings.get("school_answers", ""),
                )

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


async def _send_call_results_to_parent(task: dict, transcript: str, summary: str):
    """
    Send the call results back to the parent via WhatsApp.
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

    # Build the message
    question = task.get("question", "your question")

    message_parts = [
        f"📞 *Update: I just spoke with {school_name}!*\n",
        f"Your question: \"{question}\"\n",
    ]

    if summary:
        message_parts.append(f"Here's what they said:\n{summary}\n")
    elif transcript:
        # Extract just the key answer parts from transcript
        # The transcript format is: "User: ...\nAI: ...\n"
        message_parts.append(f"Here's the conversation summary:\n{transcript[:1500]}\n")

    message_parts.append(
        "Want me to update your school comparison with this new info, "
        "or do you have follow-up questions?"
    )

    full_message = "\n".join(message_parts)

    # Save and send
    try:
        save_message(parent_id, "assistant", full_message)
        await send_text_message(phone, full_message)
        logger.info(f"Call results sent to {phone} for task {task['id']}")
    except Exception as e:
        logger.exception(f"Failed to send call results to {phone}: {e}")
