"""Intent classifier — lightweight LLM call to route chat messages."""

import json
import os
from typing import TypedDict

from langchain_core.messages import SystemMessage, HumanMessage

from backend.app.chat.prompts import CLASSIFIER_SYSTEM_PROMPT


class ChatDirection(TypedDict, total=False):
    goal: str | None
    tickers: list[str]
    criteria: list[str]
    report_type: str | None


def _build_classifier_llm():
    """Create a lightweight LLM for intent classification. Uses server-side API key."""
    from backend.app.llm import create_llm

    provider = os.environ.get("CHAT_CLASSIFIER_PROVIDER", "claude")
    model = os.environ.get("CHAT_CLASSIFIER_MODEL", "claude-haiku-4-5-20251001")
    api_key = os.environ.get("CHAT_CLASSIFIER_API_KEY", "")
    base_url = os.environ.get("CHAT_CLASSIFIER_BASE_URL", None)

    if not api_key:
        raise RuntimeError(
            "CHAT_CLASSIFIER_API_KEY env var is required for the chatbot. "
            "Set it to a valid API key for the classifier model."
        )

    return create_llm(provider=provider, model=model, api_key=api_key, base_url=base_url)


def _call_classifier_llm(system_prompt: str, user_message: str) -> str:
    """Call the classifier LLM and return raw text."""
    llm = _build_classifier_llm()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]
    response = llm.invoke(messages)
    return response.content if hasattr(response, "content") else str(response)


def classify_intent(
    message: str,
    history: list[dict],
    current_direction: dict | None,
) -> dict:
    """Classify the user's message and return {phase, next_question, direction, ready_to_analyze}.

    Args:
        message: latest user message
        history: last few exchanges as [{"role": "user"|"assistant", "content": "..."}]
        current_direction: accumulated direction from previous turns, or None
    """
    # Build context from recent history (last 3 exchanges)
    history_text = ""
    for h in history[-6:]:
        role = h.get("role", "user")
        content = h.get("content", "")
        if content:
            history_text += f"{role.capitalize()}: {content}\n"

    direction_json = json.dumps(current_direction) if current_direction else "null"

    user_message = f"""Conversation history:
{history_text}
Current direction: {direction_json}

Latest user message: {message}"""

    try:
        raw = _call_classifier_llm(CLASSIFIER_SYSTEM_PROMPT, user_message)
        # Strip code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1] if "\n" in raw else raw
        if raw.endswith("```"):
            raw = raw[:-3].strip()
        result = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        # Fallback: discovery mode
        return {
            "phase": "discovery",
            "next_question": "Could you tell me more about what you're looking for?",
            "direction": current_direction or {"goal": None, "tickers": [], "criteria": [], "report_type": None},
            "ready_to_analyze": False,
        }

    # Merge direction: preserve existing, overlay new
    merged = dict(current_direction or {"goal": None, "tickers": [], "criteria": [], "report_type": None})
    new_dir = result.get("direction", {})
    if new_dir:
        if new_dir.get("goal"):
            merged["goal"] = new_dir["goal"]
        if new_dir.get("report_type"):
            merged["report_type"] = new_dir["report_type"]
        # Merge tickers
        existing_tickers = set(merged.get("tickers", []))
        for t in new_dir.get("tickers", []):
            existing_tickers.add(t.upper().strip())
        merged["tickers"] = list(existing_tickers)
        # Merge criteria
        existing_criteria = set(merged.get("criteria", []))
        for c in new_dir.get("criteria", []):
            existing_criteria.add(c.lower().strip())
        merged["criteria"] = list(existing_criteria)

    return {
        "phase": result.get("phase", "discovery"),
        "next_question": result.get("next_question", ""),
        "direction": merged,
        "ready_to_analyze": result.get("ready_to_analyze", False),
    }
