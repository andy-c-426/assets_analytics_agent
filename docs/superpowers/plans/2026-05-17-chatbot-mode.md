# Chatbot Mode Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add a conversational chat interface (web + CLI) that guides users through asset discovery, proposes research plans, and streams analysis results using the existing LangGraph agent pipeline.

**Architecture:** New `POST /api/chat` endpoint in the backend that classifies user intent (discovery / proposal / execute), converses via a cheap classifier LLM, and proxies execution to the existing `POST /api/analyze/{symbol}` agent service. Frontend adds a `/chat` page with SSE-based streaming messages. CLI adds a terminal client calling the same API.

**Tech Stack:** Python stdlib (CLI), existing FastAPI + httpx (backend), React + TypeScript (frontend), no new dependencies.

---

### Task 1: Chat Prompts — System prompts for discovery, proposal, and classification

**Files:**
- Create: `backend/app/chat/__init__.py`
- Create: `backend/app/chat/prompts.py`

- [x] **Step 1: Create empty `__init__.py`**

```bash
touch backend/app/chat/__init__.py
```

- [x] **Step 2: Write the prompts module**

```python
"""System prompts for the chatbot intent classifier and response generator."""

CLASSIFIER_SYSTEM_PROMPT = """You are a financial chat router. Classify the user's message into one phase:
- "discovery": user needs to be asked questions to clarify their goal, scope, criteria, time horizon, risk tolerance, or report type
- "proposal": enough information exists to propose a research plan — summarize and ask for confirmation
- "execute": user confirmed the proposal, or explicitly asked to analyze specific tickers now
- "follow_up": user is asking about a previous analysis already in context

Also extract a direction object that accumulates across the conversation:
{
  "goal": null | "comparison" | "screening" | "deep_dive" | "monitoring",
  "tickers": ["AAPL"],
  "criteria": [],
  "report_type": null | "comparison" | "snapshot" | "full_report"
}

Return ONLY valid JSON:
{
  "phase": "discovery",
  "next_question": "Are you researching specific stocks, or would you like me to help find candidates?",
  "direction": {...},
  "ready_to_analyze": false
}

Rules:
- In discovery phase, ask only ONE question at a time. Pick the most important unanswered aspect.
- Never ask a question that the user already answered.
- If the user names ticker symbols, add them to direction.tickers.
- Set ready_to_analyze: true only when the user confirmed a proposal (phase "execute").
- If the user corrects or adjusts, update direction accordingly.
"""

DISCOVERY_PROMPT = """You are a professional financial analyst assistant. Your goal is to understand the user's investment research needs through a brief, natural conversation.

Ask only ONE question at a time. Pick from the most relevant unanswered area:
- Goal: purchase research, portfolio review, or learning?
- Scope: specific tickers, or need help finding candidates?
- Criteria: growth, value, dividends, sector exposure?
- Time horizon: short-term or long-term?
- Risk tolerance: comfortable with volatility, or prefer stable?
- Report type: quick snapshot, deep fundamentals, or comparison?

Be warm and concise. Never ask something the user already told you.
Today's date: {current_date}."""

PROPOSAL_PROMPT = """You are a professional financial analyst. Based on the conversation, summarize the research plan and ask for confirmation.

Current direction: {direction}

Write a concise proposal paragraph that restates:
1. Which assets to analyze
2. What angle/criteria to focus on
3. What type of report

End with "Ready to run this?" so the user can confirm or adjust.

Keep it under 3 sentences. Don't start the analysis yet."""

CHAT_RESPONSE_PROMPT = """You are a professional financial analyst assistant. Answer the user's question conversationally using the available context.

Context from previous analysis:
{analysis_context}

Market context note:
{market_framing}

Be concise and helpful. If you don't have data to answer, suggest what analysis to run.
Today's date: {current_date}."""
```

- [x] **Step 3: Commit**

```bash
git add backend/app/chat/__init__.py backend/app/chat/prompts.py
git commit -m "feat: add chatbot prompts for discovery, proposal, and classification"
```

---

### Task 2: Intent Classifier — Lightweight LLM routing

**Files:**
- Create: `backend/app/chat/intent.py`

- [x] **Step 1: Write the test file**

Create `backend/tests/test_chat_intent.py`:

```python
import json
import os
from unittest.mock import patch, MagicMock
from backend.app.chat.intent import classify_intent, ChatDirection


class FakeResponse:
    def __init__(self, content):
        self.content = content

def test_classify_intent_discovery():
    result = classify_intent(
        message="Hi, I want to invest in tech stocks",
        history=[],
        current_direction=None,
    )
    assert result["phase"] == "discovery"
    assert isinstance(result["next_question"], str)
    assert len(result["next_question"]) > 5
    assert result["ready_to_analyze"] is False

def test_classify_intent_proposal():
    direction = {
        "goal": "comparison",
        "tickers": ["AAPL", "MSFT"],
        "criteria": ["fundamentals"],
        "report_type": "comparison",
    }
    result = classify_intent(
        message="Long-term growth, moderate risk",
        history=[{"role": "user", "content": "compare AAPL and MSFT"}],
        current_direction=direction,
    )
    assert result["phase"] in ("proposal", "execute")

def test_classify_intent_execute():
    direction = {
        "goal": "deep_dive",
        "tickers": ["AAPL"],
        "criteria": ["fundamentals"],
        "report_type": "full_report",
    }
    result = classify_intent(
        message="Yes, go ahead and run the analysis",
        history=[
            {"role": "user", "content": "analyze Apple"},
            {"role": "assistant", "content": "I'll run a full fundamentals report on AAPL. Ready to run this?"},
        ],
        current_direction=direction,
    )
    assert result["phase"] == "execute"
    assert result["ready_to_analyze"] is True

def test_direction_merges_tickers():
    direction = {
        "goal": "deep_dive",
        "tickers": ["AAPL"],
        "criteria": [],
        "report_type": "snapshot",
    }
    result = classify_intent(
        message="Also add MSFT to the list",
        history=[],
        current_direction=direction,
    )
    assert "MSFT" in result["direction"]["tickers"]

def test_classify_intent_invalid_json_fallback():
    """If LLM returns garbage, fallback to discovery."""
    with patch("backend.app.chat.intent._call_classifier_llm") as mock_llm:
        mock_llm.return_value = "not valid json {{{"
        result = classify_intent(
            message="Hello",
            history=[],
            current_direction=None,
        )
        assert result["phase"] == "discovery"
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_chat_intent.py -v`
Expected: FAIL (module not found)

- [x] **Step 3: Write the intent classifier module**

```python
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
    from backend.app.llm import create_llm  # reuses existing factory
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
```

- [x] **Step 4: Verify the test passes** (mocked — real LLM calls excluded)

Run: `python3 -m pytest backend/tests/test_chat_intent.py -v`
Expected: all tests PASS (the mock test passes; classification tests may need `CHAT_CLASSIFIER_API_KEY` set)

- [x] **Step 5: Commit**

```bash
git add backend/app/chat/intent.py backend/tests/test_chat_intent.py
git commit -m "feat: add intent classifier for chat routing"
```

---

### Task 3: Chat API Endpoint — POST /api/chat with SSE streaming

**Files:**
- Create: `backend/app/activities/chat.py`
- Modify: `backend/app/main.py`

- [x] **Step 1: Write the test file**

Create `backend/tests/test_chat_endpoint.py`:

```python
import json
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


def make_test_app():
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    from backend.app.activities.chat import router as chat_router
    app.include_router(chat_router)

    return app


client = TestClient(make_test_app())


def test_chat_endpoint_requires_message():
    body = {
        "message": "",
        "history": [],
        "direction": None,
        "user_preferences": {
            "language": "en",
            "llm_config": {"provider": "claude", "model": "c", "api_key": "k"},
        },
    }
    resp = client.post("/api/chat", json=body)
    assert resp.status_code == 422  # validation error for empty message


def test_chat_endpoint_returns_sse():
    """Chat endpoint returns text/event-stream."""
    body = {
        "message": "I want to analyze AAPL",
        "history": [],
        "direction": None,
        "user_preferences": {
            "language": "en",
            "llm_config": {"provider": "claude", "model": "claude-sonnet-4-6", "api_key": "sk-test"},
        },
    }
    resp = client.post("/api/chat", json=body, stream=True)
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")


def test_chat_endpoint_stream_contains_done_event():
    """SSE stream ends with done event."""
    body = {
        "message": "Hi",
        "history": [],
        "direction": None,
        "user_preferences": {
            "language": "en",
            "llm_config": {"provider": "openai", "model": "gpt-4o-mini", "api_key": "sk-test"},
        },
    }
    with patch("backend.app.activities.chat._handle_chat") as mock_handle:
        async def fake_stream():
            yield b"event: clarification\ndata: {\"phase\": \"discovery\"}\n\n"
            yield b"event: done\ndata: {}\n\n"
        mock_handle.return_value = fake_stream()

        resp = client.post("/api/chat", json=body, stream=True)
        content = b""
        for chunk in resp.iter_bytes():
            content += chunk
        assert b"event: done" in content
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_chat_endpoint.py -v`
Expected: FAIL (module not found)

- [x] **Step 3: Write the chat endpoint**

```python
"""POST /api/chat — conversational chat with SSE streaming."""

import asyncio
import json
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.app.chat.intent import classify_intent
from backend.app.chat.prompts import DISCOVERY_PROMPT, PROPOSAL_PROMPT, CHAT_RESPONSE_PROMPT
from backend.app.logger import logger

router = APIRouter()

AGENT_SERVICE_URL = "http://localhost:8001"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[dict] = []
    direction: dict | None = None
    user_preferences: dict = Field(...)


def _format_sse(event: str, data: dict | None = None) -> str:
    lines = [f"event: {event}"]
    if data is not None:
        lines.append(f"data: {json.dumps(data)}")
    lines.append("")
    return "\n".join(lines)


async def _call_chat_llm(system_prompt: str, user_message: str, llm_config: dict) -> str:
    """Call the user's LLM for discovery/proposal/chat text generation."""
    from backend.app.llm import create_llm
    from langchain_core.messages import SystemMessage, HumanMessage

    llm = create_llm(
        provider=llm_config["provider"],
        model=llm_config["model"],
        api_key=llm_config["api_key"],
        base_url=llm_config.get("base_url"),
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]
    response = await llm.ainvoke(messages)
    return response.content if hasattr(response, "content") else str(response)


async def _stream_agent_analysis(symbol: str, prefetched_data: dict, llm_config: dict, finnhub_key: str | None, language: str) -> AsyncGenerator[str, None]:
    """Proxy the existing agent service SSE stream, remapping events to chat format."""
    client = httpx.AsyncClient(timeout=120.0)
    try:
        async with client.stream(
            "POST",
            f"{AGENT_SERVICE_URL}/analyze/{symbol}",
            json={
                "provider": llm_config["provider"],
                "model": llm_config["model"],
                "api_key": llm_config["api_key"],
                "base_url": llm_config.get("base_url"),
                "finnhub_api_key": finnhub_key,
                "language": language,
                "prefetched_data": prefetched_data,
            },
        ) as response:
            buffer = ""
            async for chunk in response.aiter_bytes():
                text = chunk.decode()
                buffer += text
                lines = buffer.split("\n")
                buffer = lines.pop() or ""

                event_type = ""
                for line in lines:
                    if line.startswith("event: "):
                        event_type = line[7:].strip()
                    elif line.startswith("data: ") and event_type:
                        try:
                            data = json.loads(line[6:])
                        except json.JSONDecodeError:
                            event_type = ""
                            continue

                        if event_type == "step_started":
                            yield _format_sse("tool_start", {"tool": data.get("step", ""), "message": data.get("message", "")})
                        elif event_type == "tool_called":
                            yield _format_sse("tool_start", {"tool": data.get("tool", ""), "args": data.get("args", {})})
                        elif event_type == "tool_result":
                            yield _format_sse("tool_result", {"tool": data.get("tool", ""), "summary": data.get("summary", "")})
                        elif event_type == "plan_reasoning":
                            yield _format_sse("reasoning_chunk", {"text": data.get("text", "")})
                        elif event_type == "report_ready":
                            yield _format_sse("report_ready", {"report": data.get("report", "")})
                        elif event_type == "error":
                            yield _format_sse("error", {"message": data.get("message", ""), "retryable": data.get("retryable", False)})

                        event_type = ""
    except httpx.ConnectError:
        yield _format_sse("error", {"message": "Agent service is not running", "retryable": True})
    except Exception as e:
        logger.error("Agent proxy failed for %s: %s", symbol, str(e))
        yield _format_sse("error", {"message": f"Analysis failed: {e}", "retryable": False})
    finally:
        await client.aclose()


async def _handle_chat(body: ChatRequest) -> AsyncGenerator[str, None]:
    """Core chat logic: classify → route → stream."""
    language = body.user_preferences.get("language", "en")
    llm_config = body.user_preferences.get("llm_config", {})
    finnhub_key = body.user_preferences.get("finnhub_api_key")

    # 1. Classify intent
    classification = classify_intent(
        message=body.message,
        history=body.history,
        current_direction=body.direction,
    )
    phase = classification["phase"]
    direction = classification["direction"]

    logger.info("Chat phase=%s tickers=%s", phase, direction.get("tickers", []))

    # 2. Route by phase
    if phase == "discovery":
        from datetime import datetime
        prompt = DISCOVERY_PROMPT.format(current_date=datetime.now().strftime("%Y-%m-%d"))
        history_text = "\n".join(
            f"{h['role'].capitalize()}: {h['content']}" for h in body.history[-6:]
        )
        user_msg = f"Conversation:\n{history_text}\n\nLatest user message: {body.message}"
        try:
            response_text = await _call_chat_llm(prompt, user_msg, llm_config)
        except Exception as e:
            logger.error("Discovery LLM call failed: %s", e)
            response_text = classification["next_question"] or "What would you like to know about?"
        yield _format_sse("clarification", {
            "phase": "discovery",
            "message": response_text,
            "direction": direction,
        })

    elif phase == "proposal":
        prompt = PROPOSAL_PROMPT.format(direction=json.dumps(direction))
        try:
            response_text = await _call_chat_llm(prompt, body.message, llm_config)
        except Exception as e:
            logger.error("Proposal LLM call failed: %s", e)
            tickers = direction.get("tickers", [])
            response_text = f"I'll analyze {', '.join(tickers)}. Ready to run this?"
        yield _format_sse("proposal", {
            "phase": "proposal",
            "message": response_text,
            "direction": direction,
            "ready_to_analyze": True,
        })

    elif phase == "execute":
        tickers = direction.get("tickers", [])
        if not tickers:
            yield _format_sse("clarification", {
                "phase": "discovery",
                "message": "Which stocks would you like me to analyze?",
                "direction": direction,
            })
            yield _format_sse("done", {})
            return

        # Run analysis for each ticker
        for i, symbol in enumerate(tickers):
            if i > 0:
                await asyncio.sleep(0.5)  # brief pause between analyses

            # Emit asset card placeholder
            yield _format_sse("asset_card", {
                "symbol": symbol,
                "status": "loading",
            })

            prefetched = {}
            async for sse in _stream_agent_analysis(
                symbol=symbol,
                prefetched_data=prefetched,
                llm_config=llm_config,
                finnhub_key=finnhub_key,
                language=language,
            ):
                yield sse

        # If comparing, emit comparison event
        if len(tickers) > 1:
            yield _format_sse("comparison", {
                "tickers": tickers,
                "message": f"Comparison complete for {', '.join(tickers)}.",
            })

    elif phase == "follow_up":
        from datetime import datetime
        prompt = CHAT_RESPONSE_PROMPT.format(
            current_date=datetime.now().strftime("%Y-%m-%d"),
            analysis_context="(previous analysis context from conversation)",
            market_framing="",
        )
        try:
            response_text = await _call_chat_llm(prompt, body.message, llm_config)
        except Exception as e:
            logger.error("Follow-up LLM call failed: %s", e)
            response_text = "I'm not sure about that. Could you rephrase?"
        yield _format_sse("text", {"message": response_text})

    yield _format_sse("done", {})


@router.post("/api/chat")
async def chat_endpoint(body: ChatRequest):
    """Conversational chat endpoint with SSE streaming.

    Routes messages through intent classification, guides discovery conversation,
    and dispatches analysis to the existing agent service.
    """
    return StreamingResponse(
        _handle_chat(body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

- [x] **Step 4: Register the router in main.py**

In `backend/app/main.py`, add after the last `app.include_router(...)`:

```python
from backend.app.activities.chat import router as chat_router
app.include_router(chat_router)
```

- [x] **Step 5: Run tests**

Run: `python3 -m pytest backend/tests/test_chat_endpoint.py -v`
Expected: PASS

- [x] **Step 6: Verify all tests still pass**

Run: `python3 -m pytest agent-service/tests/ -v`
Expected: 50 passed

- [x] **Step 7: Commit**

```bash
git add backend/app/activities/chat.py backend/app/main.py backend/tests/test_chat_endpoint.py
git commit -m "feat: add POST /api/chat endpoint with intent routing and SSE streaming"
```

---

### Task 4: Backend LLM Factory — Shared LLM creation for classifier and chat

**Files:**
- Create: `backend/app/llm.py`

The intent classifier and chat endpoint both need to create LLM instances. We need a shared factory instead of duplicating the code in `agent_service/app/llm/client_factory.py`.

- [x] **Step 1: Write the LLM factory**

```python
"""Shared LLM client factory for backend services."""

from langchain_core.language_models import BaseChatModel


def create_llm(
    provider: str,
    model: str,
    api_key: str,
    base_url: str | None = None,
) -> BaseChatModel:
    """Create a LangChain chat model for the given provider.

    Supported providers: claude, openai, deepseek
    """
    if provider == "claude":
        from langchain_anthropic import ChatAnthropic
        kwargs: dict = {
            "model": model,
            "api_key": api_key,
            "max_tokens": 4096,
        }
        if base_url:
            kwargs["base_url"] = base_url
        return ChatAnthropic(**kwargs)

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        kwargs = {
            "model": model,
            "api_key": api_key,
        }
        if base_url:
            kwargs["base_url"] = base_url
        return ChatOpenAI(**kwargs)

    elif provider == "deepseek":
        from langchain_openai import ChatOpenAI
        kwargs = {
            "model": model,
            "api_key": api_key,
            "base_url": base_url or "https://api.deepseek.com/v1",
        }
        return ChatOpenAI(**kwargs)

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
```

- [x] **Step 2: Run existing tests to verify nothing is broken**

Run: `python3 -m pytest agent-service/tests/ -v`
Expected: 50 passed

- [x] **Step 3: Commit**

```bash
git add backend/app/llm.py
git commit -m "feat: add shared LLM client factory for backend"
```

---

### Task 5: CLI Chat Client

**Files:**
- Create: `backend/app/chat/cli.py`
- Create: `chat.sh`

- [x] **Step 1: Write the CLI module**

```python
"""Terminal chat client for Asset Analytics Agent.

Usage: python3 -m backend.app.chat.cli
"""

import json
import os
import sys
import urllib.request
import urllib.error


# ── ANSI helpers ──
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def _print_header():
    print()
    print(f"{BOLD}{'═' * 46}{RESET}")
    print(f"{BOLD}  Asset Analytics Agent — Chat Mode{RESET}")
    print(f"{DIM}  Type /help for commands, Ctrl+C to exit{RESET}")
    print(f"{BOLD}{'═' * 46}{RESET}")
    print()


def _print_help():
    print(f"""
{CYAN}Commands:{RESET}
  /help          Show this help
  /settings      Show current LLM config
  /settings set <key> <value>  Change config (provider, model, api_key, base_url, finnhub_key, language)
  /export <file> Save last report to markdown file
  /history       Show recent conversation
  /clear         Reset conversation
  /quit          Exit

{CYAN}Tips:{RESET}
  Type naturally — the agent will guide you through research.
  Mention ticker symbols (AAPL, 0700.HK) to analyze specific stocks.
""")


SETTINGS_FILE = os.path.expanduser("~/.asset_analytics_chat.json")


def _load_settings() -> dict:
    try:
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_settings(s: dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f, indent=2)


def _print_settings(settings: dict):
    print(f"\n{CYAN}Current settings:{RESET}")
    for k, v in settings.items():
        if "key" in k.lower() and v:
            v = v[:8] + "..." if len(str(v)) > 8 else v
        print(f"  {k}: {v}")
    if not settings:
        print(f"  {DIM}(not configured — run /settings set to configure){RESET}")
    print()


def _handle_sse_line(line: str, report_parts: list[str]) -> str | None:
    """Parse one SSE event and print it. Returns the report text if report_ready."""
    if line.startswith("event: "):
        return None  # event type consumed by the main loop
    if not line.startswith("data: "):
        return None

    try:
        data = json.loads(line[6:])
    except json.JSONDecodeError:
        return None

    event_type = data.get("type", "")

    # Handle different SSE event shapes (the stream loop passes event_type explicitly)
    return None  # actual rendering happens in _stream_chat


def _stream_chat(message: str, history: list[dict], direction: dict | None, settings: dict, last_report: list[str]):
    """Send POST /api/chat and render SSE events in the terminal."""
    body = json.dumps({
        "message": message,
        "history": history,
        "direction": direction,
        "user_preferences": {
            "language": settings.get("language", "en"),
            "llm_config": {
                "provider": settings.get("provider", "claude"),
                "model": settings.get("model", "claude-sonnet-4-6"),
                "api_key": settings.get("api_key", ""),
                "base_url": settings.get("base_url", ""),
            },
            "finnhub_api_key": settings.get("finnhub_key", ""),
        },
    }).encode()

    req = urllib.request.Request(
        "http://localhost:8000/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )

    new_direction = direction
    report_text = ""

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            buffer = ""
            event_type = ""

            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break

                buffer += chunk.decode()
                lines = buffer.split("\n")
                buffer = lines.pop() or ""

                for line in lines:
                    if line.startswith("event: "):
                        event_type = line[7:].strip()
                    elif line.startswith("data: ") and event_type:
                        try:
                            data = json.loads(line[6:])
                        except json.JSONDecodeError:
                            event_type = ""
                            continue

                        if event_type == "clarification":
                            new_direction = data.get("direction", new_direction)
                            print(f"\n{GREEN}Agent:{RESET} {data['message']}")

                        elif event_type == "proposal":
                            new_direction = data.get("direction", new_direction)
                            print(f"\n{GREEN}Agent:{RESET}")
                            print(f"  {data['message']}")

                        elif event_type == "tool_start":
                            tool = data.get("tool", "")
                            print(f"  {YELLOW}⏳{RESET} {tool}...", end="\r")

                        elif event_type == "tool_result":
                            tool = data.get("tool", "")
                            summary = data.get("summary", "")[:100]
                            print(f"  {GREEN}✓{RESET} {tool}: {summary}")

                        elif event_type == "reasoning_chunk":
                            print(data.get("text", ""), end="", flush=True)

                        elif event_type == "report_ready":
                            report_text = data.get("report", "")
                            print(f"\n{BOLD}{'─' * 50}{RESET}")
                            print(report_text)
                            print(f"{BOLD}{'─' * 50}{RESET}")
                            last_report.clear()
                            last_report.append(report_text)

                        elif event_type == "asset_card":
                            symbol = data.get("symbol", "")
                            print(f"\n{CYAN}┌── {symbol} ──────────{RESET}")

                        elif event_type == "comparison":
                            print(f"\n{BOLD}Comparison: {data.get('message', '')}{RESET}")

                        elif event_type == "text":
                            print(f"\n{GREEN}Agent:{RESET} {data.get('message', '')}")

                        elif event_type == "error":
                            print(f"\n{RED}Error: {data.get('message', '')}{RESET}")

                        elif event_type == "done":
                            pass  # stream end

                        event_type = ""

    except urllib.error.HTTPError as e:
        print(f"\n{RED}Server error: {e.code} — {e.reason}{RESET}")
    except urllib.error.URLError:
        print(f"\n{RED}Cannot reach backend at http://localhost:8000{RESET}")
        print(f"{DIM}Make sure the backend is running: ./start_backend.sh{RESET}")
    except KeyboardInterrupt:
        print(f"\n{DIM}Stopped.{RESET}")

    return new_direction


def main():
    settings = _load_settings()
    history: list[dict] = []
    direction = None
    last_report: list[str] = []

    _print_header()

    # Check if settings are configured
    if not settings.get("api_key"):
        print(f"{YELLOW}First-time setup: configure your LLM settings.{RESET}")
        print(f"  Use {CYAN}/settings set provider claude{RESET}")
        print(f"  Use {CYAN}/settings set model claude-sonnet-4-6{RESET}")
        print(f"  Use {CYAN}/settings set api_key sk-ant-...{RESET}")
        print()

    # Welcome message
    print(f"{GREEN}Agent:{RESET} Welcome! I can help you research and analyze stocks globally.")
    print(f"  What are you interested in today?")
    print()

    while True:
        try:
            user_input = input(f"{CYAN}You:{RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{DIM}Goodbye!{RESET}")
            break

        if not user_input:
            continue

        # ── Handle slash commands ──
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=2)
            cmd = parts[0].lower()

            if cmd == "/quit" or cmd == "/exit":
                print(f"{DIM}Goodbye!{RESET}")
                break

            elif cmd == "/help":
                _print_help()

            elif cmd == "/settings":
                if len(parts) >= 3 and parts[1] == "set":
                    key = parts[2].lower()
                    value = input(f"  {key}: ").strip()
                    if key == "api_key":
                        settings["api_key"] = value
                    elif key == "base_url":
                        settings["base_url"] = value
                    elif key == "finnhub_key":
                        settings["finnhub_key"] = value
                    elif key == "language":
                        settings["language"] = value
                    else:
                        settings[key] = value
                    _save_settings(settings)
                    print(f"  {GREEN}✓ Saved{RESET}")
                else:
                    _print_settings(settings)

            elif cmd == "/export":
                if len(parts) >= 2 and last_report:
                    filename = parts[1]
                    with open(filename, "w") as f:
                        f.write(last_report[0])
                    print(f"  {GREEN}✓ Saved to {filename}{RESET}")
                elif not last_report:
                    print(f"  {DIM}No report to export yet.{RESET}")

            elif cmd == "/history":
                print(f"\n{DIM}── Conversation ──{RESET}")
                for h in history:
                    role = h["role"].capitalize()
                    content = h["content"][:200]
                    print(f"  {BOLD if role == 'User' else ''}{role}:{RESET} {content}")
                print()

            elif cmd == "/clear":
                history = []
                direction = None
                last_report = []
                print(f"  {GREEN}✓ Conversation cleared.{RESET}")

            else:
                print(f"  {RED}Unknown command: {cmd}{RESET}  (use /help)")

            continue

        # ── Send message to chat API ──
        history.append({"role": "user", "content": user_input})
        direction = _stream_chat(user_input, history, direction, settings, last_report)
        # Add a placeholder assistant entry for history tracking
        history.append({"role": "assistant", "content": "[response rendered above]"})


if __name__ == "__main__":
    main()
```

- [x] **Step 2: Write the chat.sh wrapper**

```bash
#!/bin/bash
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
python3 -m backend.app.chat.cli
```

- [x] **Step 3: Make it executable**

```bash
chmod +x chat.sh
```

- [x] **Step 4: Commit**

```bash
git add backend/app/chat/cli.py chat.sh
git commit -m "feat: add CLI chat client with ANSI rendering and slash commands"
```

---

### Task 6: Frontend API Client — postChat function

**Files:**
- Modify: `frontend/src/api/client.ts`

- [x] **Step 1: Add ChatRequest type and postChat function**

In `frontend/src/api/client.ts`, add after the existing exports:

```typescript
// ── Chat Types ────────────────────────────────────────────────────

export interface ChatDirection {
  goal: string | null;
  tickers: string[];
  criteria: string[];
  report_type: string | null;
}

export interface ChatRequest {
  message: string;
  history: { role: 'user' | 'assistant'; content: string }[];
  direction: ChatDirection | null;
  user_preferences: {
    language: string;
    llm_config: {
      provider: string;
      model: string;
      api_key: string;
      base_url?: string;
    };
    finnhub_api_key?: string;
  };
}

// ── Chat SSE ──────────────────────────────────────────────────────

export async function postChat(
  request: ChatRequest,
  signal?: AbortSignal
): Promise<ReadableStream<Uint8Array>> {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  });
  if (!res.ok) throw new Error(`POST /chat failed: ${res.status}`);
  if (!res.body) throw new Error('No response body');
  return res.body;
}
```

- [x] **Step 2: Verify TypeScript compiles**

Run: `npx tsc --noEmit`
Expected: clean

- [x] **Step 3: Commit**

```bash
git add frontend/src/api/client.ts
git commit -m "feat: add postChat API function with SSE stream support"
```

---

### Task 7: Chat UI Components — ChatMessage and ChatInput

**Files:**
- Create: `frontend/src/components/ChatMessage.tsx`
- Create: `frontend/src/components/ChatMessage.module.css`
- Create: `frontend/src/components/ChatInput.tsx`
- Create: `frontend/src/components/ChatInput.module.css`

- [x] **Step 1: Write ChatMessage component**

```typescript
import ReactMarkdown from 'react-markdown';
import { Link } from 'react-router-dom';
import styles from './ChatMessage.module.css';

interface ChatMessageData {
  type: 'text' | 'asset_card' | 'analysis_stream' | 'clarification' | 'error' | 'loading';
  role: 'user' | 'assistant' | 'system';
  content?: string;
  symbol?: string;
  report?: string;
  choices?: string[];
  onChoice?: (choice: string) => void;
}

export default function ChatMessage({ msg }: { msg: ChatMessageData }) {
  const className =
    msg.role === 'user' ? styles.userMsg :
    msg.role === 'system' ? styles.systemMsg :
    styles.assistantMsg;

  const renderContent = () => {
    switch (msg.type) {
      case 'text':
        return <ReactMarkdown>{msg.content || ''}</ReactMarkdown>;

      case 'asset_card':
        return (
          <div className={styles.assetCard}>
            <span className={styles.assetSymbol}>{msg.symbol}</span>
            {msg.report && (
              <Link to={`/asset/${msg.symbol}`} className={styles.assetLink}>
                View Full Analysis →
              </Link>
            )}
          </div>
        );

      case 'analysis_stream':
        return (
          <div className={styles.analysisBlock}>
            <ReactMarkdown>{msg.report || msg.content || ''}</ReactMarkdown>
          </div>
        );

      case 'clarification':
        return (
          <div>
            <p>{msg.content}</p>
            {msg.choices && msg.choices.length > 0 && (
              <div className={styles.choiceRow}>
                {msg.choices.map((c, i) => (
                  <button
                    key={i}
                    className={styles.choiceBtn}
                    onClick={() => msg.onChoice?.(c)}
                  >
                    {c}
                  </button>
                ))}
              </div>
            )}
          </div>
        );

      case 'error':
        return <div className={styles.errorBanner}>{msg.content}</div>;

      case 'loading':
        return <span className={styles.loadingDots}>...</span>;

      default:
        return <p>{msg.content}</p>;
    }
  };

  return (
    <div className={`${styles.message} ${className}`}>
      {msg.role === 'assistant' && <span className={styles.label}>Agent</span>}
      {renderContent()}
    </div>
  );
}
```

- [x] **Step 2: Write ChatMessage CSS**

`frontend/src/components/ChatMessage.module.css`:

```css
.message {
  padding: 12px 16px;
  border-radius: var(--radius-md);
  max-width: 85%;
  line-height: 1.6;
  font-size: 14px;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.userMsg {
  align-self: flex-end;
  background: var(--accent);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.assistantMsg {
  align-self: flex-start;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
}

.systemMsg {
  align-self: center;
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  text-align: center;
}

.label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--accent);
  margin-bottom: 6px;
}

.assetCard {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  margin: 4px 0;
}

.assetSymbol {
  font-weight: 600;
  font-size: 15px;
  font-family: monospace;
}

.assetLink {
  font-size: 13px;
  color: var(--accent);
  text-decoration: none;
}

.assetLink:hover {
  text-decoration: underline;
}

.analysisBlock {
  font-size: 14px;
  line-height: 1.7;
}

.choiceRow {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.choiceBtn {
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
  cursor: pointer;
  font-size: 13px;
  transition: background 0.15s;
}

.choiceBtn:hover {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.errorBanner {
  padding: 10px 14px;
  background: var(--red-subtle);
  color: var(--red);
  border-radius: var(--radius-sm);
  font-size: 13px;
}

.loadingDots {
  animation: blink 1.4s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 0.2; }
  50% { opacity: 1; }
}
```

- [x] **Step 3: Write ChatInput component**

```typescript
import { useState, useRef, useEffect } from 'react';
import styles from './ChatInput.module.css';

interface Props {
  onSend: (message: string) => void;
  onStop?: () => void;
  loading?: boolean;
  placeholder?: string;
}

export default function ChatInput({ onSend, onStop, loading, placeholder }: Props) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 120) + 'px';
    }
  }, [value]);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || loading) return;
    onSend(trimmed);
    setValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={styles.inputBar}>
      <textarea
        ref={inputRef}
        className={styles.textarea}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || 'Ask about any stock... (Shift+Enter for newline)'}
        rows={1}
        disabled={loading}
      />
      <div className={styles.buttons}>
        {loading ? (
          <button className={styles.stopBtn} onClick={onStop}>
            Stop
          </button>
        ) : (
          <button
            className={styles.sendBtn}
            onClick={handleSend}
            disabled={!value.trim()}
          >
            Send
          </button>
        )}
      </div>
    </div>
  );
}
```

- [x] **Step 4: Write ChatInput CSS**

`frontend/src/components/ChatInput.module.css`:

```css
.inputBar {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 14px 16px;
  border-top: 1px solid var(--border);
  background: var(--bg-card);
}

.textarea {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-size: 14px;
  font-family: inherit;
  line-height: 1.5;
  resize: none;
  outline: none;
  background: var(--bg);
  color: var(--text);
  max-height: 120px;
}

.textarea:focus {
  border-color: var(--accent);
}

.buttons {
  display: flex;
  gap: 8px;
}

.sendBtn, .stopBtn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s;
}

.sendBtn {
  background: var(--accent);
  color: #fff;
}

.sendBtn:disabled {
  opacity: 0.4;
  cursor: default;
}

.stopBtn {
  background: var(--red);
  color: #fff;
}
```

- [x] **Step 5: Verify TypeScript compiles**

Run: `npx tsc --noEmit`
Expected: clean

- [x] **Step 6: Commit**

```bash
git add frontend/src/components/ChatMessage.tsx frontend/src/components/ChatMessage.module.css frontend/src/components/ChatInput.tsx frontend/src/components/ChatInput.module.css
git commit -m "feat: add ChatMessage and ChatInput components"
```

---

### Task 8: ChatPage — Wire everything together

**Files:**
- Create: `frontend/src/pages/ChatPage.tsx`
- Create: `frontend/src/pages/ChatPage.module.css`

- [x] **Step 1: Write the ChatPage component**

```typescript
import { useState, useRef, useCallback, useEffect } from 'react';
import { postChat, type ChatDirection } from '../api/client';
import { loadSettings } from '../components/SettingsDialog';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import SettingsDialog from '../components/SettingsDialog';
import { useLocale } from '../i18n/LocaleContext';
import type { AnalysisRequest } from '../api/types';
import styles from './ChatPage.module.css';

interface Message {
  id: number;
  type: 'text' | 'asset_card' | 'analysis_stream' | 'clarification' | 'error' | 'loading';
  role: 'user' | 'assistant' | 'system';
  content?: string;
  symbol?: string;
  report?: string;
  choices?: string[];
}

let msgId = 0;

export default function ChatPage() {
  const { t, locale } = useLocale();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settings, setSettings] = useState<AnalysisRequest | null>(loadSettings);
  const directionRef = useRef<ChatDirection | null>(null);
  const historyRef = useRef<{ role: 'user' | 'assistant'; content: string }[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = useCallback((msg: Omit<Message, 'id'>) => {
    const id = ++msgId;
    setMessages((prev) => [...prev, { ...msg, id }]);
    return id;
  }, []);

  const updateMessage = useCallback((id: number, updates: Partial<Message>) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, ...updates } : m)));
  }, []);

  const handleSend = useCallback(async (message: string) => {
    const currentSettings = settings || loadSettings();
    if (!currentSettings) {
      setSettingsOpen(true);
      return;
    }

    // Add user message
    addMessage({ type: 'text', role: 'user', content: message });
    historyRef.current.push({ role: 'user', content: message });

    setLoading(true);
    const loadingId = addMessage({ type: 'loading', role: 'assistant' });

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const body = await postChat({
        message,
        history: historyRef.current.slice(0, -1), // exclude the just-added user message
        direction: directionRef.current,
        user_preferences: {
          language: locale,
          llm_config: {
            provider: currentSettings.provider,
            model: currentSettings.model,
            api_key: currentSettings.api_key,
            base_url: currentSettings.base_url,
          },
          finnhub_api_key: currentSettings.finnhub_api_key,
        },
      }, controller.signal);

      removeMessage(loadingId);

      const reader = body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentStreamId: number | null = null;
      let streamBuffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let eventType = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith('data: ') && eventType) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (eventType) {
                case 'clarification':
                  directionRef.current = data.direction;
                  addMessage({
                    type: 'clarification',
                    role: 'assistant',
                    content: data.message,
                    choices: extractChoices(data.message),
                  });
                  historyRef.current.push({ role: 'assistant', content: data.message });
                  break;

                case 'proposal':
                  directionRef.current = data.direction;
                  addMessage({ type: 'text', role: 'assistant', content: data.message });
                  historyRef.current.push({ role: 'assistant', content: data.message });
                  break;

                case 'asset_card':
                  addMessage({
                    type: 'asset_card',
                    role: 'assistant',
                    symbol: data.symbol,
                  });
                  break;

                case 'tool_start':
                  // Show brief tool status via loading message update
                  break;

                case 'tool_result':
                  // Tool results shown via streaming text
                  break;

                case 'reasoning_chunk':
                  streamBuffer += data.text || '';
                  if (!currentStreamId) {
                    currentStreamId = addMessage({
                      type: 'analysis_stream',
                      role: 'assistant',
                      report: streamBuffer,
                    });
                  } else {
                    updateMessage(currentStreamId, { report: streamBuffer });
                  }
                  break;

                case 'report_ready':
                  streamBuffer = data.report || '';
                  if (currentStreamId) {
                    updateMessage(currentStreamId, {
                      type: 'analysis_stream',
                      report: streamBuffer,
                    });
                  } else {
                    addMessage({
                      type: 'analysis_stream',
                      role: 'assistant',
                      report: streamBuffer,
                    });
                  }
                  historyRef.current.push({ role: 'assistant', content: streamBuffer.slice(0, 200) });
                  streamBuffer = '';
                  currentStreamId = null;
                  break;

                case 'comparison':
                  addMessage({
                    type: 'text',
                    role: 'assistant',
                    content: data.message,
                  });
                  break;

                case 'text':
                  addMessage({ type: 'text', role: 'assistant', content: data.message });
                  historyRef.current.push({ role: 'assistant', content: data.message });
                  break;

                case 'error':
                  addMessage({ type: 'error', role: 'assistant', content: data.message });
                  break;

                case 'done':
                  // Stream complete
                  break;
              }
            } catch { /* skip malformed */ }
            eventType = '';
          }
        }
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      removeMessage(loadingId);
      addMessage({
        type: 'error',
        role: 'assistant',
        content: err instanceof Error ? err.message : 'Chat failed',
      });
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }, [settings, locale, addMessage, updateMessage]);

  const removeMessage = useCallback((id: number) => {
    setMessages((prev) => prev.filter((m) => m.id !== id));
  }, []);

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const handleSettingsSaved = useCallback((s: AnalysisRequest) => {
    setSettings(s);
  }, []);

  return (
    <div className={styles.page}>
      <div className={styles.chatArea}>
        {messages.length === 0 && (
          <div className={styles.welcome}>
            <h2>{t('chat.welcome') || 'Asset Analytics Chat'}</h2>
            <p>{t('chat.welcomeSub') || 'Describe your investment goals and I\'ll guide you through research and analysis.'}</p>
          </div>
        )}
        {messages.map((msg) => (
          <ChatMessage key={msg.id} msg={msg} />
        ))}
        <div ref={chatEndRef} />
      </div>
      <ChatInput
        onSend={handleSend}
        onStop={handleStop}
        loading={loading}
        placeholder={t('chat.placeholder') || 'Ask about any stock...'}
      />
      <SettingsDialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onSaved={handleSettingsSaved}
      />
    </div>
  );
}

function extractChoices(text: string): string[] {
  // Extract numbered or bulleted options from the message
  const choices: string[] = [];
  const lines = text.split('\n');
  for (const line of lines) {
    const match = line.match(/^[\d]+[.)]\s*(.+)/);
    if (match) {
      choices.push(match[1].trim());
    }
  }
  return choices;
}
```

- [x] **Step 2: Write ChatPage CSS**

`frontend/src/pages/ChatPage.module.css`:

```css
.page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px); /* minus nav height */
  max-width: 780px;
  margin: 0 auto;
}

.chatArea {
  flex: 1;
  overflow-y: auto;
  padding: 20px 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.welcome {
  text-align: center;
  margin-top: 80px;
  color: var(--text-muted);
}

.welcome h2 {
  font-size: 20px;
  color: var(--text);
  margin-bottom: 8px;
}

.welcome p {
  font-size: 14px;
}
```

- [x] **Step 3: Verify TypeScript compiles**

Run: `npx tsc --noEmit`
Expected: clean

- [x] **Step 4: Commit**

```bash
git add frontend/src/pages/ChatPage.tsx frontend/src/pages/ChatPage.module.css
git commit -m "feat: add ChatPage component with SSE streaming and settings integration"
```

---

### Task 9: Route + Nav + i18n — Wire chat into the app

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/i18n/translations.ts`

- [x] **Step 1: Add /chat route to App.tsx**

```typescript
// Add import at top:
import ChatPage from './pages/ChatPage';

// Add route inside <Routes>:
<Route path="/chat" element={<PageWrapper><ChatPage /></PageWrapper>} />
```

- [x] **Step 2: Add Chat nav link to the NavBar**

In `frontend/src/App.tsx`, add inside the `navRight` div:

```tsx
<Link to="/chat" className={styles.navLink}>{t('nav.chat')}</Link>
```

- [x] **Step 3: Add i18n labels**

In `frontend/src/i18n/translations.ts`, add:

```typescript
'nav.chat': { en: 'Chat', 'zh-CN': '对话' },
'chat.welcome': { en: 'Asset Analytics Chat', 'zh-CN': '资产分析助手' },
'chat.welcomeSub': { en: 'Describe your investment goals and I\'ll guide you through research and analysis.', 'zh-CN': '描述您的投资目标，我将引导您完成研究和分析。' },
'chat.placeholder': { en: 'Ask about any stock... (Shift+Enter for newline)', 'zh-CN': '询问任意股票...（Shift+Enter 换行）' },
```

- [x] **Step 4: Verify TypeScript compiles**

Run: `npx tsc --noEmit`
Expected: clean

- [x] **Step 5: Run all backend tests**

Run: `python3 -m pytest agent-service/tests/ -v`
Expected: 50 passed

- [x] **Step 6: Commit**

```bash
git add frontend/src/App.tsx frontend/src/i18n/translations.ts
git commit -m "feat: wire chat page into routing, nav, and i18n"
```

---

### Task 10: Integration verification

**Files:**
- None (verification only)

- [x] **Step 1: Start backend**

```bash
./start_backend.sh --reload --log
```

- [x] **Step 2: Start agent service** (separate terminal)

```bash
./start_agent.sh --reload --log
```

- [x] **Step 3: Start frontend** (separate terminal)

```bash
./start_frontend.sh --log
```

- [x] **Step 4: Verify health**

```bash
curl http://localhost:8000/api/health
```

Expected: `{"status":"ok"}`

- [x] **Step 5: Test chat API endpoint**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hi",
    "history": [],
    "direction": null,
    "user_preferences": {
      "language": "en",
      "llm_config": {"provider": "claude", "model": "claude-sonnet-4-6", "api_key": "sk-test"}
    }
  }'
```

Expected: SSE stream that gracefully handles the invalid API key (classifier fails → discovery fallback)

- [x] **Step 6: Test CLI**

```bash
echo "/quit" | python3 -m backend.app.chat.cli
```

Expected: clean startup and exit with header printed

- [x] **Step 7: Browse to http://localhost:5173/chat**

Expected: Chat page renders with welcome message and input bar. Nav shows "Chat" link.

- [x] **Step 8: Run all tests one final time**

```bash
python3 -m pytest agent-service/tests/ -v
npx tsc --noEmit
```

Expected: 50 passed, TypeScript clean
```

---

