# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A web application for searching and analyzing financial assets (stocks, ETFs) across all major global markets. Users search by ticker, view detailed asset information, and get LLM-powered analysis using their own API keys.

## Architecture

- **Backend:** Python FastAPI — stateless API proxy, forwards analyze requests to agent service
- **Agent Service:** Python FastAPI + LangGraph — multi-step reasoning agent (collect_core_data → plan → execute_tools → observe → synthesize) with deterministic coverage check, parallel tool execution, streaming SSE, and analytics computation
- **Frontend:** React + Vite TypeScript SPA — search, asset detail, analysis panel with live streaming, settings
- **Data:** yfinance for multi-market price data, fundamentals, and search autocomplete; Futu OpenD for real-time market snapshots; DuckDuckGo / Finnhub for news
- **LLM:** User-configurable Claude / GPT / DeepSeek with user-provided API keys per request

## Project Structure

```
backend/                    # Python FastAPI (proxy layer)
  app/main.py               # entry point
  app/models/               # pydantic schemas
  app/activities/           # one file per endpoint (search, asset_detail, price_history, analyze)
  app/proxy/                # external adapters (yfinance.py, llm.py)
agent-service/              # Python FastAPI (LangGraph agent)
  agent_service/app/
    main.py                 # entry point (port 8001)
    agent_router.py         # SSE streaming endpoint
    graph.py                # LangGraph StateGraph (collect_core_data→plan→execute_tools→observe→synthesize)
    prompts.py              # LLM system prompts + tool registry
    events.py               # SSE event formatters
    state.py                # AgentState TypedDict
    cache.py                # TTL in-memory cache for analytics
    analytics/              # Bloomberg-style derived metrics
    tools/                  # LangChain tools (market_data, macro_research, sentiment_news, price_history, technicals)
    llm/                    # LLM client factory (Claude/GPT/DeepSeek)
frontend/                   # React + Vite
  src/components/           # SearchBar, AssetDetail, PriceChart, NewsList, AnalyzePanel, SettingsDialog, LanguageToggle
  src/pages/                # SearchPage, AssetPage
  src/i18n/                 # translations.ts, LocaleContext.tsx (en / zh-CN)
  src/api/client.ts         # API client
tests/
```

**Conventions:** `activities/` = one file per API endpoint. `proxy/` = all external dependency adapters. `tools/` = one file per LangChain tool. No local search index — yfinance provides autocomplete. No server-side API key storage.

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/search?q=` | Autocomplete search across all markets |
| GET | `/api/assets/{symbol}` | Asset detail: profile, price, metrics, news |
| GET | `/api/assets/{symbol}/price-history?period=` | OHLCV series |
| POST | `/api/analyze/{symbol}` | LLM agent analysis with SSE streaming (body: provider, model, api_key, base_url, finnhub_api_key, language, prefetched_data) |

Agent service also exposes direct-access endpoints: `GET /market-data/{symbol}`, `GET /macro-research/{symbol}`, `GET /sentiment-news/{symbol}`.

## Docs

- `docs/superpowers/specs/` — design specifications for features
- `docs/superpowers/plans/` — implementation plans
- `docs/superpowers/tasks/` — task breakdowns with status
- `features/` — completed feature records with changed files and commits
