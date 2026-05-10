# Phase 2 — Agent Service with LangGraph, Futu, and Finnhub

**Status:** completed
**Branch:** `main`
**Date:** 2026-05-09 – 2026-05-10

## What Was Built

### Agent Service (LangGraph)

- StateGraph with 4 nodes: plan → execute_tools → observe → synthesize
- Multi-step reasoning agent that decides which tools to call and re-plans if data is insufficient
- Parallel tool execution via `ThreadPoolExecutor` (max 5 concurrent)
- Live SSE streaming via `astream(stream_mode="updates")` — each stage emitted as it completes
- Structured observe decision: `{"decision": "enough"|"more", "missing": [...], "reasoning": "..."}`
- Timestamp injection into all 3 LLM prompts for date-aware decisions
- Plan reasoning display — LLM explains why it chose each tool

### Tools

| Tool | Source | Purpose |
|------|--------|---------|
| `fetch_asset_data` | yfinance | Asset profile, price, metrics, news |
| `fetch_price_history` | yfinance | OHLCV historical prices |
| `calculate_technicals` | computed | SMA, EMA, RSI, volatility |
| `search_latest_news` | DuckDuckGo | Web news search |
| `fetch_futu_data` | Futu OpenD | Real-time market snapshots (142 fields) |
| `fetch_finnhub_news` | Finnhub | Ticker-specific financial news |

### Bloomberg-Style Analytics

- Valuation zones (severe discount → extreme premium)
- Momentum returns (1W, 1M, 3M, YTD)
- RSI, max drawdown, daily volatility
- Beta context classification
- TTL in-memory cache (300s) with `threading.Lock()`

### Futu OpenD Integration

- Market snapshot API: price, volume, turnover, valuation (P/E, P/B, EPS), fundamentals (net profit, net asset, book value), 52W range, extended hours
- Stock basic info: type, exchange, listing date
- Multi-market: US (NASDAQ/NYSE), HK (HKEX), CN (SH/SZ), JP, SG, AU, MY, CA
- Auto code resolution (AAPL → US.AAPL, 00700 → HK.00700)
- Graceful fallback to yfinance when OpenD is unavailable

### Finnhub News Integration

- Company news by ticker with headlines, summaries, sources, dates
- API key passed through SettingsDialog → localStorage → backend → agent service
- DuckDuckGo fallback when no key is configured

### Frontend Improvements

- **AnalyzePanel** — live streaming of all agent stages, plan reasoning display with step detail
- **AssetDetail** — description collapse/expand toggle with "Show more"/"Show less"
- **SettingsDialog** — Finnhub API key field
- SSE event types: `step_started`, `plan_reasoning`, `tool_called`, `tool_result`, `report_ready`, `error`, `done`

### Prompt Improvements

- Compressed tool results for observe (8 lines per tool) to reduce token cost
- Description compression (first 2 sentences, ~200 chars) in yfinance output
- Structured JSON observe decisions instead of brittle string matching

## Files Changed

### Created

```
agent-service/
  agent_service/app/
    main.py
    agent_router.py
    graph.py
    prompts.py
    events.py
    state.py
    cache.py
    __init__.py
    analytics/
      __init__.py
      metrics.py
    tools/
      __init__.py
      yfinance_tools.py
      futu_data.py
      finnhub_news.py
      news_search.py
      technicals.py
    llm/
      __init__.py
      client_factory.py
  requirements.txt
```

### Modified from Phase 1

```
backend/
  app/models/schemas.py              # added finnhub_api_key
  app/activities/analyze.py          # SSE proxy to agent service, pass finnhub key
  app/proxy/llm.py                   # no changes needed

frontend/
  src/api/types.ts                   # added finnhub_api_key, SSEEvent, ReasoningStep
  src/api/client.ts                  # added analyzeAssetStream
  src/components/AnalyzePanel.tsx     # rewritten for live streaming + plan reasoning
  src/components/AnalyzePanel.module.css  # stepDetail styles
  src/components/AssetDetail.tsx      # description toggle
  src/components/AssetDetail.module.css  # moreBtn, description styles
  src/components/SettingsDialog.tsx   # Finnhub key input
```

## Commits

```
6bcf1a8 feat: add Finnhub news tool with API key settings flow
6e68581 feat: add Futu OpenD data tool with real-time market snapshots
533ac2b feat: add plan reasoning display and description toggle to frontend
58392af feat: add analytics engine, news search, parallel execution, and live streaming
2572414 feat: add SSE streaming client and reasoning chain UI to AnalyzePanel
0067165 feat: refactor analyze endpoint to proxy SSE from agent service
ca83953 fix: add min_length validation to AnalyzeRequest and improve SSE event replay
3b4080c feat: add agent SSE streaming endpoint with LangGraph execution
41419a2 fix: improve markdown stripping and remove overly broad error detection in observe_node
1fd0286 feat: add LangGraph state machine with plan/execute/observe/synthesize nodes
5355b58 feat: add technical analysis tools (SMA, EMA, RSI, volatility)
3047d19 fix: use is-not-None checks and add exception handling to yfinance tools
d9e0b84 feat: add yfinance tools for asset data and price history
3ad808d feat: add LLM client factory for Claude, OpenAI, and DeepSeek
```
