import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agent_service.app.state import AgentState
from agent_service.app.graph import build_graph
from agent_service.app import events
from agent_service.app.tools.finnhub_news import set_api_key as set_finnhub_key


router = APIRouter()


class AnalyzeRequest(BaseModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    base_url: str | None = None
    finnhub_api_key: str | None = None


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
        set_finnhub_key(body.finnhub_api_key or None)

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

        emitted_results = 0

        async for chunk in compiled.astream(initial_state, stream_mode="updates"):
            for node_name, updates in chunk.items():
                steps = updates.get("steps", [])
                tool_results = updates.get("tool_results", [])

                if node_name == "plan":
                    for step in reversed(steps):
                        if step["step_type"] == "planning" and step["status"] == "done":
                            detail = step.get("detail", "")
                            if detail:
                                yield events.plan_reasoning(detail)
                            break

                elif node_name == "execute_tools":
                    for r in tool_results[emitted_results:]:
                        yield events.tool_called(r["tool"], r.get("args", {}))
                        await asyncio.sleep(0.2)
                        yield events.tool_result(r["tool"], r["summary"])
                        await asyncio.sleep(0.2)
                    emitted_results = len(tool_results)

                elif node_name == "observe":
                    for step in reversed(steps):
                        if step["step_type"] == "evaluating" and step["status"] == "done":
                            yield events.step_started("evaluating", step.get("detail", step["message"]))
                            break

                elif node_name == "synthesize":
                    for step in reversed(steps):
                        if step["step_type"] == "synthesizing" and step["status"] == "done":
                            yield events.step_started("synthesizing", step.get("detail", step["message"]))
                            break
                    if updates.get("final_report"):
                        yield events.report_ready(updates["final_report"])

                if updates.get("error"):
                    yield events.error_event(updates["error"])

    except Exception as e:
        yield events.error_event(str(e), retryable=False)
    finally:
        yield events.done()
