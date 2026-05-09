import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent_service.app.state import AgentState
from agent_service.app.graph import build_graph
from agent_service.app import events


router = APIRouter()


class AnalyzeRequest(BaseModel):
    provider: str
    model: str
    api_key: str
    base_url: str | None = None


@router.post("/analyze/{symbol}")
async def analyze(symbol: str, body: AnalyzeRequest):
    return StreamingResponse(
        _stream_analysis(symbol, body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _stream_analysis(symbol: str, body: AnalyzeRequest) -> AsyncGenerator[str, None]:
    try:
        graph = build_graph()
        compiled = graph.compile()

        initial_state: AgentState = {
            "symbol": symbol,
            "llm_config": {
                "provider": body.provider,
                "model": body.model,
                "api_key": body.api_key,
                "base_url": body.base_url,
            },
            "plan": [],
            "tool_results": [],
            "messages": [],
            "steps": [],
            "final_report": None,
            "next_action": "plan",
            "error": None,
        }

        yield events.step_started("planning", f"Starting analysis for {symbol}...")

        # Run the graph in a thread pool to avoid blocking the event loop
        final_state = await asyncio.to_thread(compiled.invoke, initial_state)

        # Emit all steps from the state
        for step in final_state.get("steps", []):
            if step["step_type"] == "planning":
                yield events.step_started("planning", step["message"])
            elif step["step_type"] == "tool_call":
                if step["status"] == "active":
                    pass  # tool_called already emitted during execution
                elif step["status"] == "done":
                    for r in final_state.get("tool_results", []):
                        if r["tool"] in step.get("message", ""):
                            yield events.tool_result(r["tool"], r["summary"])
            elif step["step_type"] == "evaluating":
                yield events.step_started("evaluating", step["message"])
            elif step["step_type"] == "synthesizing":
                yield events.step_started("synthesizing", step["message"])

        if final_state.get("error"):
            yield events.error_event(final_state["error"])
        elif final_state.get("final_report"):
            yield events.report_ready(final_state["final_report"])
        else:
            yield events.error_event("Analysis produced no report")

    except Exception as e:
        yield events.error_event(str(e), retryable=False)
    finally:
        yield events.done()
