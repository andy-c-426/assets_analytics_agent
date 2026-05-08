# Phase 1 — Core Flow: Search → Detail → Analyze

**Status:** completed
**Branch:** `phase-1-core-flow`
**Date:** 2026-05-08

## What Was Built

### Backend (Python FastAPI)
- Health check endpoint
- Search autocomplete via yfinance — `GET /api/search?q=`
- Asset detail (profile, price, metrics, news) — `GET /api/assets/{symbol}`
- Price history OHLCV series — `GET /api/assets/{symbol}/price-history?period=`
- LLM analysis with user-provided keys — `POST /api/analyze/{symbol}`
- yfinance proxy adapter for multi-market data
- LLM proxy adapter supporting Claude (Anthropic SDK), GPT (OpenAI SDK), DeepSeek (OpenAI-compatible)

### Frontend (React + Vite + TypeScript)
- SearchBar with debounced autocomplete dropdown
- SearchPage landing page
- AssetDetail component (profile, price, 8 key metrics)
- PriceChart with period selector (1M/6M/1Y/5Y/Max) using recharts
- NewsList with linked article cards
- SettingsDialog for LLM config (provider, model, API key, base URL), persisted to localStorage
- AnalyzePanel with loading/error/result states, markdown rendering via react-markdown
- AssetPage assembling all components
- App routing: `/` → SearchPage, `/asset/:symbol` → AssetPage
- Vite proxy config for `/api` → backend

### Tooling
- `start.sh` — single command to launch both servers
- 14 pytest backend tests
- TypeScript strict type-checking

## Files Changed

### Created
```
backend/
  app/__init__.py
  app/main.py
  app/models/__init__.py, schemas.py
  app/proxy/__init__.py, yfinance.py, llm.py
  app/activities/__init__.py, search.py, asset_detail.py, price_history.py, analyze.py
  requirements.txt

frontend/
  (scaffolded via Vite, then customized)
  src/api/types.ts, client.ts
  src/components/SearchBar.tsx, AssetDetail.tsx, PriceChart.tsx,
    NewsList.tsx, SettingsDialog.tsx, AnalyzePanel.tsx
  src/pages/SearchPage.tsx, AssetPage.tsx
  src/App.tsx (rewritten with routing)
  vite.config.ts (proxy added)

tests/
  __init__.py, conftest.py
  test_health.py, test_search.py, test_asset_detail.py,
  test_price_history.py, test_analyze.py
  test_yfinance_proxy.py, test_llm_proxy.py

.gitignore
start.sh
README.md
```

### Modified from scaffold
- `backend/app/main.py` — router registration for all 4 endpoints
- `frontend/src/App.tsx` — replaced with BrowserRouter
- `frontend/vite.config.ts` — API proxy added

## Commits

```
cfd1045 docs: add detailed README and start.sh convenience script
94d88ff chore: mark all Phase 1 tasks complete
e5f64c4 feat: wire up routing for search and asset pages
6fdde88 feat: add AssetPage combining detail, chart, news, and analyze
2ea5eac feat: add AnalyzePanel with LLM analysis call and markdown rendering
6a464a5 feat: add SettingsDialog for LLM configuration
fbe4a3c feat: add NewsList component
d9444e0 feat: add PriceChart component with period selector
4883ff7 feat: add AssetDetail component with profile, price, and metrics
3711e15 feat: add SearchBar with autocomplete and SearchPage
9789385 feat: add typed API client for all endpoints
826042d feat: scaffold React + Vite frontend with proxy config
6e4c818 feat: add LLM analyze endpoint
cd3a743 feat: add LLM proxy with Claude, GPT, and DeepSeek support
b8a83ca feat: add price history endpoint
708ef76 feat: add asset detail endpoint
6e41e43 feat: add search autocomplete endpoint
c7f5fd7 feat: add yfinance proxy with search, asset data, and price history
6c6b63f feat: add Pydantic schemas for all API models
dbc8ce1 feat: scaffold FastAPI backend with health check
```
