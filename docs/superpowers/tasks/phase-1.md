# Phase 1 — Core Flow: Search → Detail → Analyze

**Goal:** Full end-to-end flow working. A user can search for any global asset, view its detail, and get LLM-powered analysis.

**Status:** completed (14 tests passing, 18 commits on `phase-1-core-flow`)

---

## Backend — Python FastAPI

### 1.1 Project scaffold
- [x] Create `backend/` directory with `app/main.py`, `requirements.txt`
- [x] Install FastAPI, uvicorn, yfinance, httpx, pydantic
- [x] Health check endpoint `GET /api/health`
- **Depends on:** nothing

### 1.2 Pydantic models
- [x] `app/models/schemas.py` — AssetSearchResult, AssetDetail, AssetProfile, PriceData, KeyMetrics, NewsArticle, OHLCV, AnalysisRequest, AnalysisResponse
- **Depends on:** 1.1

### 1.3 yfinance proxy
- [x] `app/proxy/yfinance.py` — search(), fetch_asset(symbol), fetch_price_history(symbol, period), fetch_news(symbol)
- [x] Return data in shapes matching the Pydantic models
- **Depends on:** 1.2

### 1.4 Search activity
- [x] `app/activities/search.py` — `GET /api/search?q=`
- [x] Calls yfinance proxy search, returns AssetSearchResult[]
- **Depends on:** 1.3

### 1.5 Asset detail activity
- [x] `app/activities/asset_detail.py` — `GET /api/assets/{symbol}`
- [x] Calls yfinance proxy for profile, price, metrics, news
- [x] Returns AssetDetail
- **Depends on:** 1.3

### 1.6 Price history activity
- [x] `app/activities/price_history.py` — `GET /api/assets/{symbol}/price-history?period=1mo|6mo|1y|5y|max`
- [x] Calls yfinance proxy, returns OHLCV[]
- **Depends on:** 1.3

### 1.7 LLM proxy
- [x] `app/proxy/llm.py` — analyze(provider, model, api_key, base_url, context)
- [x] Support Claude (Anthropic SDK), GPT (OpenAI SDK), DeepSeek (OpenAI-compatible endpoint)
- [x] Context assembly: format asset data + news into a prompt
- **Depends on:** 1.2

### 1.8 Analyze activity
- [x] `app/activities/analyze.py` — `POST /api/analyze/{symbol}`
- [x] Accepts AnalysisRequest, fetches asset data + news, calls LLM proxy, returns AnalysisResponse
- **Depends on:** 1.3, 1.7

---

## Frontend — React + Vite + TypeScript

### 2.1 Project scaffold
- [x] Create `frontend/` with Vite + React + TypeScript
- [x] Install dependencies: react-router-dom, recharts (or lightweight chart lib)
- [x] Basic App shell with routing
- **Depends on:** nothing

### 2.2 API client
- [x] `src/api/client.ts` — typed fetch wrappers for all 4 endpoints
- [x] searchAssets(q), getAssetDetail(symbol), getPriceHistory(symbol, period), analyzeAsset(symbol, config)
- **Depends on:** 2.1

### 2.3 SearchBar component + SearchPage
- [x] `SearchBar.tsx` — input with debounced autocomplete dropdown
- [x] `SearchPage.tsx` — full search experience, navigates to asset on select
- **Depends on:** 2.2

### 2.4 AssetDetail component
- [x] `AssetDetail.tsx` — company name, market, sector, market cap, description
- **Depends on:** 2.2

### 2.5 PriceChart component
- [x] `PriceChart.tsx` — interactive line/area chart, period selector (1mo, 6mo, 1y, 5y, max)
- **Depends on:** 2.2

### 2.6 NewsList component
- [x] `NewsList.tsx` — list of recent news with title, source, date, link
- **Depends on:** 2.2

### 2.7 SettingsDialog component
- [x] `SettingsDialog.tsx` — modal for LLM config (provider selector, model name, API key input, base URL)
- [x] Store config in localStorage
- **Depends on:** 2.2

### 2.8 AnalyzePanel component
- [x] `AnalyzePanel.tsx` — "Analyze" button, loading state, streaming or progressive display, result rendering (markdown)
- [x] Reads LLM config from settings, calls analyzeAsset
- **Depends on:** 2.2, 2.7

### 2.9 AssetPage
- [x] `AssetPage.tsx` — combines AssetDetail + PriceChart + NewsList + AnalyzePanel
- [x] Reads symbol from URL params
- **Depends on:** 2.4, 2.5, 2.6, 2.8

### 2.10 App routing
- [x] Wire up routes: `/` → SearchPage, `/asset/:symbol` → AssetPage
- **Depends on:** 2.3, 2.9

---

## Integration

### 3.1 End-to-end test pass
- [x] Search for an asset → see results
- [x] Click result → see detail page with chart, metrics, news
- [x] Configure LLM settings → click analyze → see analysis
- [x] Test with different ticker formats (US, HK, CN, JP)
- **Depends on:** all above
