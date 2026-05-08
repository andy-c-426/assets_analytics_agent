# Asset Analytics Agent — Design Spec

## Overview

A web application for searching and analyzing financial assets (stocks, ETFs) across all major global markets. Users search by ticker, view detailed asset information, and get LLM-powered analysis using their own API keys.

## User Flow

1. **Search** — Autocomplete search bar accepts any ticker format (AMZN, 300502.SZ, 0700.HK, 7203.T). Returns matching assets from all global markets.
2. **Asset Detail** — Click a result to see: interactive price chart, key metrics (market cap, P/E, dividend yield), company profile, recent news headlines.
3. **LLM Analysis** — Click "Analyze" button. Backend packages asset data + news into context, sends to user's chosen LLM, returns analysis.
4. **Settings** — User configures LLM provider (model name, model ID, API key, base URL).

## Architecture

```
Browser → React Frontend → FastAPI Backend → yfinance (market data + search)
                                    └─────────→ Claude / GPT / DeepSeek (LLM analysis)
```

**Backend (Python FastAPI):** Stateless API server. Fetches data from yfinance, assembles LLM context, proxies LLM calls. Does not store API keys — user passes them per request.

**Frontend (React + Vite):** Single-page app. Search bar, asset detail page with chart, news list, analyze panel, settings dialog. Never calls external data providers directly.

## Data Sources

- **yfinance** — Multi-market price data, fundamentals, company profile, news, and search/autocomplete. Covers US, HK, CN, JP, UK, KR, TW, EU, and more.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/search?q={query}` | Autocomplete search, returns `AssetSearchResult[]` |
| GET | `/api/assets/{symbol}` | Asset detail: profile, current price, metrics, news |
| GET | `/api/assets/{symbol}/price-history?period=1mo` | OHLCV price series |
| POST | `/api/analyze/{symbol}` | LLM analysis with user API config |

### POST /api/analyze/{symbol} request body

```json
{
  "provider": "claude",
  "model": "claude-sonnet-4-6",
  "api_key": "sk-...",
  "base_url": null
}
```

Response includes: symbol, analysis text, model used, and context metadata (data points, news count).

## Data Models

**AssetSearchResult:** symbol, name, exchange, type (stock/etf), market, currency

**AssetDetail:** profile (name, sector, market_cap, description), price (current, change, change_pct, high, low), metrics (pe_ratio, pb_ratio, eps, dividend_yield), news (NewsArticle[])

**OHLCV:** date, open, high, low, close, volume

**AnalysisResponse:** symbol, analysis (full LLM output), model_used, context_sent (data_points, news_count)

## Project Structure

```
assets_analytics_agent/
├── backend/                    # Python FastAPI
│   ├── app/
│   │   ├── main.py             # entry point
│   │   ├── models/             # pydantic schemas
│   │   ├── activities/         # one file per endpoint
│   │   │   ├── search.py       # GET /api/search
│   │   │   ├── asset_detail.py # GET /api/assets/{symbol}
│   │   │   ├── price_history.py# GET /api/assets/{symbol}/price-history
│   │   │   └── analyze.py      # POST /api/analyze/{symbol}
│   │   └── proxy/              # external dependency adapters
│   │       ├── yfinance.py     # market data + search
│   │       └── llm.py          # Claude / GPT / DeepSeek
│   └── requirements.txt
├── frontend/                   # React + Vite
│   ├── src/
│   │   ├── components/         # SearchBar, AssetDetail, PriceChart,
│   │   │                       # NewsList, AnalyzePanel, SettingsDialog
│   │   ├── pages/              # SearchPage, AssetPage
│   │   ├── api/client.ts       # API client
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
└── tests/
```

**Directory conventions:**
- `activities/` — one file per API endpoint, handles request/response
- `proxy/` — adapters for all external dependencies (yfinance, LLM providers)
- `models/` — shared Pydantic schemas used across activities and proxy

## Phases

**Phase 1:** Search autocomplete + asset detail page + LLM analysis + settings dialog. Full working flow end-to-end.

**Phase 2+:** Chart interactivity improvements, news sentiment, analysis history, additional data providers, portfolio page.

## Key Design Decisions

- No local search index — yfinance provides autocomplete via its search API
- No server-side API key storage — user passes LLM config in each analyze request
- No CLI — web-only for initial delivery
- yfinance as sole data provider for Phase 1; proxy abstraction allows adding more later
