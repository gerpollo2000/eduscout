"""
EduScout Orchestrator Agent (Day 7 — Anthropic Sonnet + Comparison)
LangGraph StateGraph deployed via Gradient ADK.

Day 7 changes:
- Switched to anthropic-claude-4.6-sonnet (max_tokens explicitly set — required by Anthropic via DO)
- Added school comparison tool
- End-of-week integration: all agents wired together
- Model: anthropic-claude-4.6-sonnet on inference.do-ai.run
- Fallback: set MODEL_NAME env var to switch models without redeploying
"""

import os
import sys
import logging
import json
import httpx
from langchain_openai import ChatOpenAI

from typing import TypedDict, Annotated

from gradient_adk import entrypoint, RequestContext

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.school_finder import school_finder_tools
from agents.session_manager import session_tools
from agents.document_analyst import document_analyst_tools
from agents.school_comparison import comparison_tools
from agents.logistics import logistics_tools
from agents.mystery_shopper import mystery_shopper_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eduscout.orchestrator")

logging.getLogger("httpcore").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("openai").setLevel(logging.DEBUG)

class AgentState(TypedDict):
    messages: Annotated[list, lambda a, b: a + b]

def _inject_max_tokens(request: httpx.Request) -> None:
    """Force-inject max_tokens into every request body sent to the inference endpoint."""
    if request.content:
        try:
            body = json.loads(request.content)
            if "max_tokens" not in body or not body.get("max_tokens"):
                body["max_tokens"] = 4096
                new_content = json.dumps(body).encode()
                # Must update Content-Length to match new body size
                request.headers["content-length"] = str(len(new_content))
                request.stream = httpx.ByteStream(new_content)
                logger.info(f"[inject] max_tokens injected, new content-length={len(new_content)}")
            else:
                logger.info(f"[inject] max_tokens already present: {body.get('max_tokens')}")
        except Exception as e:
            logger.warning(f"[inject] Failed to patch request body: {e}")


def get_llm():
    """
    Get LLM instance. Model is configurable via MODEL_NAME env var.
    Default: anthropic-claude-4.6-sonnet

    IMPORTANT: Anthropic models on DO Gradient require max_tokens explicitly.
    openai-gpt-oss-120b does NOT require it.
    """
    model_name = os.environ.get("MODEL_NAME", "anthropic-claude-4.6-sonnet")
    max_tokens = int(os.environ.get("MAX_TOKENS", "4096"))

    logger.info(f"[LLM] model={model_name}, max_tokens={max_tokens}")

    http_client = httpx.Client(
        event_hooks={"request": [_inject_max_tokens]},
        timeout=httpx.Timeout(60.0, connect=10.0),  # 60s read timeout, 10s connect
    )

    return ChatOpenAI(
        model=model_name,
        api_key=os.environ.get("GRADIENT_MODEL_ACCESS_KEY", ""),
        base_url="https://inference.do-ai.run/v1",
        temperature=0.3,
        max_tokens=max_tokens,
        http_client=http_client,
        timeout=60,  # also set on ChatOpenAI level
    )


SYSTEM_PROMPT = """You are EduScout, an AI school advisor helping parents in Manhattan, New York find the perfect school. You communicate via WhatsApp.

## Personality
- Warm, professional, empathetic
- Concise — keep WhatsApp messages brief and scannable
- Proactive — suggest things the parent hasn't thought of
- Honest — if you don't have data, say so

## Your Tools

### Session Management
1. **create_search_session** — Save parent's preferences. Call ONCE when you first learn their needs.
2. **update_search_session** — Update preferences as parent shares more info.

### School Search
3. **search_schools** — Find schools matching criteria from database.
4. **get_school_details** — Get full details for a specific school.

### Document Analysis (RAG)
5. **search_school_documents** — Search school handbooks, policies, regulations.

### Comparison
6. **compare_schools** — Side-by-side comparison of 2-3 schools.

### Logistics
7. **calculate_commute_to_school** — Calculate travel time (transit + driving) from an address to a school.
8. **save_parent_address** — Save parent's home or work address for future commute lookups.

### Mystery Shopper (Phone Calls)
9. **call_school_for_info** — Call a school by phone to ask a question.
   ASYNC: The call happens in the background. Tell the parent you'll message back.
   ONLY use when info is NOT in the database or documents.
   
## CRITICAL RULES

### Session Updates
When the parent shares NEW info (special needs, interests, budget, wheelchair, neighborhood):
→ FIRST call update_search_session with the new info
→ THEN call search_schools if needed

### Data Integrity
- NEVER invent school data — only state facts from tool results
- If data is missing: "I don't have confirmed information about that"
- Cite sources: "According to our records..." or "According to [School]'s handbook..."

### When to Use Each Tool
- Parent asks "find me a school" → search_schools
- Parent asks "tell me about Trinity" → get_school_details
- Parent asks "what's the dress code at IDEAL" → search_school_documents
- Parent asks "compare Beacon vs Stuyvesant" → compare_schools
- Parent gives new preference info → update_search_session first
- Parent asks "how far is [school]?" or "commute to [school]" → calculate_commute_to_school
- Parent shares home/work address ("I live at...", "my office is...") → save_parent_address
- Parent asks "how far from home to [school]?" → calculate_commute_to_school with address_type="home"
- Parent asks something not in DB/docs and wants verified info → call_school_for_info
- IMPORTANT: Try search_schools, get_school_details, and search_school_documents FIRST.
  Only call_school_for_info as a last resort when data is missing.
  
## Conversation Flow
1. GREETING: Brief intro, ask what they need
2. INTAKE: Gather level, budget, location, needs (1-2 questions at a time)
3. SEARCH: Use tools once you have enough info
4. RECOMMEND: Top 3 with brief reasons
5. DEEP DIVE: Answer follow-ups with details/docs/comparison

## WhatsApp Formatting
- Under 500 words per message
- Line breaks for readability
- Emojis sparingly: 🏫 📚 ✅ ⭐
"""


# ============================================================
# TOOLS
# ============================================================

all_tools = school_finder_tools + session_tools + document_analyst_tools + comparison_tools + logistics_tools + mystery_shopper_tools
tool_node = ToolNode(all_tools)

def agent_node(state: AgentState) -> dict:
    llm = get_llm()
    llm_with_tools = llm.bind_tools(all_tools)

    # Log what max_tokens the bound model actually has
    logger.info(f"[agent_node] LLM max_tokens={llm_with_tools.max_tokens}, model_kwargs={llm_with_tools.model_kwargs}")
    logger.info(f"[agent_node] bound max_tokens={llm_with_tools.max_tokens}")

    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "end": END},
    )
    workflow.add_edge("tools", "agent")
    return workflow.compile()


graph = build_graph()


@entrypoint
async def main(input: dict, context: RequestContext):
    prompt = input.get("prompt", "")
    history = input.get("history", [])
    parent_name = input.get("parent_name", "")
    parent_id = input.get("parent_id", 0)
    session = input.get("session")

    if not prompt:
        return {"response": "I didn't receive a message. Could you try again?"}

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    # Inject parent + session context
    ctx_parts = [f"[System: parent_id={parent_id}, name={parent_name}]"]

    if session and session.get("id"):
        s = session
        sd = f"[Active session id={s['id']}"
        for key, label in [
            ("target_level", "level"), ("budget_max", "budget"),
            ("special_needs", "special_needs"), ("preferred_neighborhood", "area"),
            ("interests", "interests"), ("religious_preference", "religion"),
        ]:
            val = s.get(key)
            if val:
                sd += f", {label}={'${val:,.0f}/yr' if key == 'budget_max' and isinstance(val, (int, float)) else val}"
        if s.get("needs_wheelchair_access"):
            sd += ", wheelchair=required"
        sd += " — use update_search_session for changes]"
        ctx_parts.append(sd)
    else:
        ctx_parts.append("[No session yet — create one when you learn the parent's needs]")

    messages.append(SystemMessage(content="\n".join(ctx_parts)))

    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    if not history and parent_name:
        messages.append(HumanMessage(content=f"[Parent: {parent_name}] {prompt}"))
    else:
        messages.append(HumanMessage(content=prompt))

    try:
        result = await graph.ainvoke({"messages": messages})

        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                return {"response": msg.content}

        last_msg = result["messages"][-1]
        if hasattr(last_msg, "content") and last_msg.content:
            return {"response": last_msg.content}

        return {"response": "I had trouble processing that. Could you rephrase?"}

    except Exception as e:
        logger.exception(f"Agent error: {e}")
        return {"response": "I encountered an issue. Please try again in a moment."}
