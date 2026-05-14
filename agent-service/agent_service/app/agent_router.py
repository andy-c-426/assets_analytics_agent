import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agent_service.app.state import AgentState
from agent_service.app.graph import build_graph, _extract_fields, _make_tool_result


# Compile once at module load — reused across all requests
_compiled_graph = build_graph().compile()
from agent_service.app import events
from agent_service.app.tools.market_data import fetch_market_data
from agent_service.app.tools.macro_research import fetch_macro_research
from agent_service.app.tools.sentiment_news import fetch_sentiment_news
from agent_service.app.tools.cn_market_tools import fetch_capital_flow, fetch_cn_market_sentiment


router = APIRouter()


class AnalyzeRequest(BaseModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    base_url: str | None = None
    finnhub_api_key: str | None = None
    language: str | None = None
    prefetched_data: dict[str, str] | None = None


def _extract_text(result) -> str:
    """Extract display text from a tool result (handles both str and ToolOutput)."""
    if isinstance(result, dict) and "text" in result:
        return result["text"]
    return str(result)


@router.get("/market-data/{symbol}")
async def market_data(symbol: str):
    """Fetch structured market data for a symbol."""
    result = fetch_market_data.invoke({"symbol": symbol})
    return {"symbol": symbol, "data": _extract_text(result)}


@router.get("/macro-research/{symbol}")
async def macro_research(symbol: str):
    """Fetch macro research and sector analysis for a symbol."""
    result = fetch_macro_research.invoke({"symbol": symbol})
    return {"symbol": symbol, "data": result}


@router.get("/sentiment-news/{symbol}")
async def sentiment_news(symbol: str, finnhub_api_key: str | None = None):
    """Fetch sentiment news for a symbol."""
    result = fetch_sentiment_news.invoke({"symbol": symbol, "finnhub_api_key": finnhub_api_key})
    return {"symbol": symbol, "data": result}


@router.get("/capital-flow/{symbol}")
async def capital_flow(symbol: str):
    """Fetch Stock Connect capital flow for CN/HK markets."""
    result = fetch_capital_flow.invoke({"symbol": symbol})
    return {"symbol": symbol, "data": result}


@router.get("/cn-sentiment/{symbol}")
async def cn_sentiment(symbol: str):
    """Fetch CN/HK market sentiment and Dragon Tiger Board data."""
    result = fetch_cn_market_sentiment.invoke({"symbol": symbol})
    return {"symbol": symbol, "data": result}


@router.get("/us-fundamentals/{symbol}")
async def us_fundamentals(symbol: str):
    """Fetch US fundamentals: analyst consensus, insider, institutional, earnings, filings."""
    from agent_service.app.tools.us_market_tools import fetch_us_fundamentals
    result = fetch_us_fundamentals.invoke({"symbol": symbol})
    return {"symbol": symbol, "data": result}


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
        # Build pre-populated tool_results from pre-fetched data
        prefetched = body.prefetched_data or {}
        pre_tool_results = []
        if prefetched:
            for tool_name, data in prefetched.items():
                pre_tool_results.append(_make_tool_result(
                    tool_name, {"symbol": symbol}, data, True,
                    call_id=f"{tool_name}_cached", cached=True,
                ))
        if prefetched:
            yield events.step_started("planning", f"Using cached data for {symbol}...")
        else:
            yield events.step_started("planning", f"Gathering core data for {symbol}...")

        initial_state: AgentState = {
            "symbol": symbol,
            "language": body.language or "en",
            "llm_config": {
                "provider": body.provider,
                "model": body.model,
                "api_key": body.api_key,
                "base_url": body.base_url,
            },
            "finnhub_api_key": body.finnhub_api_key,
            "plan": [],
            "tool_results": pre_tool_results,
            "messages": [],
            "steps": [],
            "final_report": None,
            "next_action": "plan",
            "iteration_count": 0,
            "error": None,
        }

        emitted_results = len(pre_tool_results)

        async for chunk in _compiled_graph.astream(initial_state, stream_mode="updates"):
            for node_name, updates in chunk.items():
                steps = updates.get("steps", [])
                tool_results = updates.get("tool_results", [])

                if node_name == "collect_core_data":
                    new_results = tool_results[emitted_results:]
                    for r in new_results:
                        yield events.tool_called(r["tool"], r.get("args", {}))
                        await asyncio.sleep(0.2)
                        yield events.tool_result(r["tool"], r["summary"])
                        await asyncio.sleep(0.2)
                    emitted_results = len(tool_results)

                elif node_name == "plan":
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
