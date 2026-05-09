# Agent Service — Multi-Step Reasoning with LangGraph

**Status:** design-approved
**Date:** 2026-05-09

## Goal

Replace the current single-prompt LLM analysis with a multi-step reasoning agent. The agent plans its analysis, calls tools to fetch data, evaluates results, loops if needed, and synthesizes a structured report. The frontend renders the full reasoning chain live via SSE.

## Architecture

```
frontend (React)              backend (FastAPI)           agent-service (LangGraph)
AssetPage                       main.py                    agent_router.py
  AnalyzePanel ──SSE────────→ analyze.py ──HTTP──────────→ /analyze/{symbol}
    renders reasoning chain    (thin proxy)                  LangGraph StateGraph:
    + final report                                            plan → execute_tools →
                                                                 observe → synthesize
                                                              tools/
                                                                yfinance.py
                                                                technicals.py
```

- **Backend** becomes a thin proxy for the analyze path — it forwards SSE events from the agent service
- **Agent service** is a standalone FastAPI app with the LangGraph runtime, tool registry, and MCP client
- **Knowledge base is deferred** to a later phase (no RAG/embeddings in this spec)
- **Frontend** AnalyzePanel reads SSE events via `fetch()` + `ReadableStream`, renders reasoning chain

## LangGraph State Machine

### State Shape

```python
class AgentState(TypedDict):
    symbol: str
    llm_config: dict           # provider, model, api_key, base_url
    chat_model: str            # which provider to use
    plan: list[dict]           # list of planned tool calls
    tool_results: list[dict]   # accumulated tool execution results
    messages: list             # full message history
    steps: list[ReasoningStep] # structured step log for SSE streaming
    final_report: str | None
    next_action: str           # plan | execute_tools | observe | synthesize | done
    error: str | None
```

### Nodes & Edges

```
plan → execute_tools → observe → synthesize → END
         ↑                          │
         └──────────────────────────┘ (loop if more data needed)
```

1. **plan** — LLM receives symbol + available tools, decides which to call, emits plan. SSE event: `step_started: planning`
2. **execute_tools** — Runs each planned tool sequentially, collects results. SSE events: `tool_called`, `tool_result`
3. **observe** — LLM reviews results, decides: enough data or loop back. SSE event: `step_started: evaluating`
4. **synthesize** — LLM writes final structured analysis. SSE events: `reasoning_chunk`, `report_ready`
5. **END** — final state persisted

### Tool Catalog (Phase 2)

| Tool | Description |
|------|-------------|
| `fetch_asset_data(symbol)` | Full yfinance fetch — profile, price, metrics, news |
| `fetch_price_history(symbol, period)` | OHLCV series (1mo/6mo/1y/5y/max) |
| `calculate_technicals(symbol, period)` | SMA, EMA, RSI, volatility from price data |

Future tools (not in this spec): web search via MCP, sector comparison, correlation analysis.

## Service API Contract

### Endpoint: `POST /analyze/{symbol}`

Request body:
```json
{
  "provider": "claude",
  "model": "claude-sonnet-4-6",
  "api_key": "sk-...",
  "base_url": null
}
```

Response: `text/event-stream` (SSE)

### SSE Events

```
event: step_started
data: {"step": "planning", "message": "Planning analysis for AAPL..."}

event: tool_called
data: {"tool": "fetch_asset_data", "args": {"symbol": "AAPL"}}

event: tool_result
data: {"tool": "fetch_asset_data", "summary": "Retrieved: AAPL ($187.32), sector: Technology"}

event: tool_called
data: {"tool": "calculate_technicals", "args": {"symbol": "AAPL", "period": "1y"}}

event: reasoning_chunk
data: {"text": "Looking at the metrics..."}

event: report_ready
data: {"report": "# AAPL Analysis\n\n..."}

event: error
data: {"message": "API key invalid", "retryable": false}

event: done
data: {}
```

## Backend Changes

**`backend/app/activities/analyze.py`** — becomes a thin proxy:

- Before: call yfinance → build context → call LLM → return JSON
- After: forward request to agent service → stream SSE response back to frontend

The backend no longer calls yfinance or LLM APIs directly in the analyze path.

## Frontend Changes

### New UI: Reasoning Chain

```
┌──────────────────────────────────────────────────┐
│ [Analyze with AI]  [LLM Settings]                 │
├──────────────────────────────────────────────────┤
│                                                    │
│  ◆ Planning — Analyzing AAPL...           [done]  │
│  ◆ Fetching asset data...                 [done]  │
│  ◆ Calculating technical indicators...    [done]  │
│  ◇ Synthesizing report...               [active] │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │ # AAPL Analysis                               │ │
│  │ ...report content...                          │ │
│  └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

### Files to Modify

- **`frontend/src/components/AnalyzePanel.tsx`** — SSE reader, reasoning chain state, StepList + final report rendering
- **`frontend/src/components/AnalyzePanel.module.css`** — step list classes (`.stepList`, `.stepItem`, `.stepDone`, `.stepActive`, `.stepPending`, `.stepIcon`)
- **`frontend/src/api/client.ts`** — new `analyzeAssetStream(symbol, settings)` returning a `ReadableStream`

Zero new npm dependencies — SSE from native `fetch()` + `ReadableStream`.

## File Structure (New)

```
agent-service/
  pyproject.toml
  app/
    __init__.py
    main.py              # FastAPI app, CORS, startup
    agent_router.py      # POST /analyze/{symbol}, SSE streaming
    state.py             # AgentState TypedDict, ReasoningStep
    graph.py             # LangGraph StateGraph definition
    tools/
      __init__.py
      yfinance_tools.py  # fetch_asset_data, fetch_price_history
      technicals.py      # calculate_technicals (SMA, EMA, RSI, volatility)
    llm/
      __init__.py
      client_factory.py  # Create Anthropic/OpenAI client from config
    events.py            # SSE event formatting helpers
```

## Implementation Notes

- No knowledge base / RAG in this phase — deferred
- MCP tool integration scaffolded but not connected to live MCP servers (web search tool will use direct API initially)
- LangGraph dependency: `langgraph`, `langchain-core`, `anthropic`, `openai`
- Backend needs `httpx` (or `aiohttp`) for async proxy to agent service
- Frontend SSE parsing: no EventSource (only supports GET), use `fetch()` with `response.body.getReader()`
- The old non-streaming `analyzeAsset()` function stays in `api/client.ts` for backward compatibility — the streaming version is additive
