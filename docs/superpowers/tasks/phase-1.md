# Phase 1 — Core Flow: Search → Detail → Analyze

**Goal:** Full end-to-end flow working. A user can search for any global asset, view its detail, and get LLM-powered analysis.

**Status:** not started

---

## Backend — Python FastAPI

### 1.1 Project scaffold
- [ ] Create `backend/` directory with `app/main.py`, `requirements.txt`
- [ ] Install FastAPI, uvicorn, yfinance, httpx, pydantic
- [ ] Health check endpoint `GET /api/health`
- **Depends on:** nothing

### 1.2 Pydantic models
- [ ] `app/models/schemas.py` — AssetSearchResult, AssetDetail, AssetProfile, PriceData, KeyMetrics, NewsArticle, OHLCV, AnalysisRequest, AnalysisResponse
- **Depends on:** 1.1

### 1.3 yfinance proxy
- [ ] `app/proxy/yfinance.py` — search(), fetch_asset(symbol), fetch_price_history(symbol, period), fetch_news(symbol)
- [ ] Return data in shapes matching the Pydantic models
- **Depends on:** 1.2

### 1.4 Search activity
- [ ] `app/activities/search.py` — `GET /api/search?q=`
- [ ] Calls yfinance proxy search, returns AssetSearchResult[]
- **Depends on:** 1.3

### 1.5 Asset detail activity
- [ ] `app/activities/asset_detail.py` — `GET /api/assets/{symbol}`
- [ ] Calls yfinance proxy for profile, price, metrics, news
- [ ] Returns AssetDetail
- **Depends on:** 1.3

### 1.6 Price history activity
- [ ] `app/activities/price_history.py` — `GET /api/assets/{symbol}/price-history?period=1mo|6mo|1y|5y|max`
- [ ] Calls yfinance proxy, returns OHLCV[]
- **Depends on:** 1.3

### 1.7 LLM proxy
- [ ] `app/proxy/llm.py` — analyze(provider, model, api_key, base_url, context)
- [ ] Support Claude (Anthropic SDK), GPT (OpenAI SDK), DeepSeek (OpenAI-compatible endpoint)
- [ ] Context assembly: format asset data + news into a prompt
- **Depends on:** 1.2

### 1.8 Analyze activity
- [ ] `app/activities/analyze.py` — `POST /api/analyze/{symbol}`
- [ ] Accepts AnalysisRequest, fetches asset data + news, calls LLM proxy, returns AnalysisResponse
- **Depends on:** 1.3, 1.7

---

## Frontend — React + Vite + TypeScript

### 2.1 Project scaffold
- [ ] Create `frontend/` with Vite + React + TypeScript
- [ ] Install dependencies: react-router-dom, recharts (or lightweight chart lib)
- [ ] Basic App shell with routing
- **Depends on:** nothing

### 2.2 API client
- [ ] `src/api/client.ts` — typed fetch wrappers for all 4 endpoints
- [ ] searchAssets(q), getAssetDetail(symbol), getPriceHistory(symbol, period), analyzeAsset(symbol, config)
- **Depends on:** 2.1

### 2.3 SearchBar component + SearchPage
- [ ] `SearchBar.tsx` — input with debounced autocomplete dropdown
- [ ] `SearchPage.tsx` — full search experience, navigates to asset on select
- **Depends on:** 2.2

### 2.4 AssetDetail component
- [ ] `AssetDetail.tsx` — company name, market, sector, market cap, description
- **Depends on:** 2.2

### 2.5 PriceChart component
- [ ] `PriceChart.tsx` — interactive line/area chart, period selector (1mo, 6mo, 1y, 5y, max)
- **Depends on:** 2.2

### 2.6 NewsList component
- [ ] `NewsList.tsx` — list of recent news with title, source, date, link
- **Depends on:** 2.2

### 2.7 SettingsDialog component
- [ ] `SettingsDialog.tsx` — modal for LLM config (provider selector, model name, API key input, base URL)
- [ ] Store config in localStorage
- **Depends on:** 2.2

### 2.8 AnalyzePanel component
- [ ] `AnalyzePanel.tsx` — "Analyze" button, loading state, streaming or progressive display, result rendering (markdown)
- [ ] Reads LLM config from settings, calls analyzeAsset
- **Depends on:** 2.2, 2.7

### 2.9 AssetPage
- [ ] `AssetPage.tsx` — combines AssetDetail + PriceChart + NewsList + AnalyzePanel
- [ ] Reads symbol from URL params
- **Depends on:** 2.4, 2.5, 2.6, 2.8

### 2.10 App routing
- [ ] Wire up routes: `/` → SearchPage, `/asset/:symbol` → AssetPage
- **Depends on:** 2.3, 2.9

---

## Integration

### 3.1 End-to-end test pass
- [ ] Search for an asset → see results
- [ ] Click result → see detail page with chart, metrics, news
- [ ] Configure LLM settings → click analyze → see analysis
- [ ] Test with different ticker formats (US, HK, CN, JP)
- **Depends on:** all above
