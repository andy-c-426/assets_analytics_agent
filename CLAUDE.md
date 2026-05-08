# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A web application for searching and analyzing financial assets (stocks, ETFs) across all major global markets. Users search by ticker, view detailed asset information, and get LLM-powered analysis using their own API keys.

## Architecture

- **Backend:** Python FastAPI — stateless API server, fetches data from yfinance, proxies LLM calls
- **Frontend:** React + Vite TypeScript SPA — search, asset detail, analysis panel, settings
- **Data:** yfinance for multi-market price data, fundamentals, news, and search autocomplete
- **LLM:** User-configurable Claude / GPT / DeepSeek with user-provided API keys per request

## Project Structure

```
backend/                    # Python FastAPI
  app/main.py               # entry point
  app/models/               # pydantic schemas
  app/activities/           # one file per endpoint (search, asset_detail, price_history, analyze)
  app/proxy/                # external adapters (yfinance.py, llm.py)
frontend/                   # React + Vite
  src/components/           # SearchBar, AssetDetail, PriceChart, NewsList, AnalyzePanel, SettingsDialog
  src/pages/                # SearchPage, AssetPage
  src/api/client.ts         # API client
tests/
```

**Conventions:** `activities/` = one file per API endpoint. `proxy/` = all external dependency adapters. No local search index — yfinance provides autocomplete. No server-side API key storage.

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/search?q=` | Autocomplete search across all markets |
| GET | `/api/assets/{symbol}` | Asset detail: profile, price, metrics, news |
| GET | `/api/assets/{symbol}/price-history?period=` | OHLCV series |
| POST | `/api/analyze/{symbol}` | LLM analysis (body: provider, model, api_key, base_url) |

## Docs

- `docs/superpowers/specs/` — design specifications for features
- `docs/superpowers/plans/` — implementation plans
- `docs/superpowers/tasks/` — task breakdowns with status
- `features/` — completed feature records with changed files and commits
