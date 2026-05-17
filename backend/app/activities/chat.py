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
    return "\n".join(lines) + "\n"


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
                await asyncio.sleep(0.5)

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
