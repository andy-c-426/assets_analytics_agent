# Phase 1 Core Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Full end-to-end flow — search any global asset, view detail page, get LLM-powered analysis.

**Architecture:** Python FastAPI backend serves 4 endpoints. React + Vite frontend consumes them. yfinance provides all market data. User-configured LLM (Claude/GPT/DeepSeek) provides analysis. Backend is stateless — API keys are passed per request, never stored server-side.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, yfinance, httpx, pydantic v2, anthropic SDK, openai SDK, pytest, React 18, TypeScript, Vite, react-router-dom v6, recharts, react-markdown

---

## File Map

| File | Responsibility |
|------|---------------|
| `backend/app/main.py` | FastAPI app creation, CORS, route registration |
| `backend/app/models/schemas.py` | All Pydantic request/response models |
| `backend/app/proxy/yfinance.py` | yfinance adapter: search, asset data, price history, news |
| `backend/app/proxy/llm.py` | LLM adapter: context assembly, provider routing |
| `backend/app/activities/search.py` | `GET /api/search` — autocomplete endpoint |
| `backend/app/activities/asset_detail.py` | `GET /api/assets/{symbol}` — detail endpoint |
| `backend/app/activities/price_history.py` | `GET /api/assets/{symbol}/price-history` — OHLCV endpoint |
| `backend/app/activities/analyze.py` | `POST /api/analyze/{symbol}` — LLM analysis endpoint |
| `backend/requirements.txt` | Python dependencies |
| `tests/test_search.py` | Tests for search endpoint |
| `tests/test_asset_detail.py` | Tests for asset detail endpoint |
| `tests/test_price_history.py` | Tests for price history endpoint |
| `tests/test_analyze.py` | Tests for analyze endpoint |
| `frontend/src/api/client.ts` | Typed API client for all 4 endpoints |
| `frontend/src/components/SearchBar.tsx` | Autocomplete search input |
| `frontend/src/components/AssetDetail.tsx` | Asset profile and metrics display |
| `frontend/src/components/PriceChart.tsx` | Interactive price chart with period selector |
| `frontend/src/components/NewsList.tsx` | News headlines list |
| `frontend/src/components/SettingsDialog.tsx` | LLM configuration modal |
| `frontend/src/components/AnalyzePanel.tsx` | Analyze button + result display |
| `frontend/src/pages/SearchPage.tsx` | Search page layout |
| `frontend/src/pages/AssetPage.tsx` | Asset detail page layout |
| `frontend/src/App.tsx` | App shell with routing |

---

### Task 1: Backend Project Scaffold

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write requirements.txt**

```txt
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
yfinance>=0.2.36
httpx>=0.27.0
pydantic>=2.0.0
anthropic>=0.30.0
openai>=1.30.0
pytest>=8.0.0
```

- [ ] **Step 2: Install dependencies**

Run: `cd backend && pip install -r requirements.txt`

- [ ] **Step 3: Create app package init**

`backend/app/__init__.py` (empty file)

- [ ] **Step 4: Write main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Asset Analytics Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Write test conftest**

```python
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)
```

- [ ] **Step 6: Write and run health check test**

Create `tests/test_health.py`:

```python
def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

Run: `python -m pytest tests/test_health.py -v`
Expected: 1 passed

- [ ] **Step 7: Commit**

```bash
git add backend/ tests/
git commit -m "feat: scaffold FastAPI backend with health check"
```

---

### Task 2: Pydantic Models

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/schemas.py`

- [ ] **Step 1: Write all Pydantic schemas**

```python
from pydantic import BaseModel
from typing import Optional


class AssetSearchResult(BaseModel):
    symbol: str
    name: str
    exchange: str
    type: str
    market: str
    currency: str


class AssetProfile(BaseModel):
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    description: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None


class PriceData(BaseModel):
    current: float
    previous_close: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    currency: str = "USD"


class KeyMetrics(BaseModel):
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None


class NewsArticle(BaseModel):
    title: str
    publisher: Optional[str] = None
    link: Optional[str] = None
    published_at: Optional[str] = None
    summary: Optional[str] = None


class AssetDetail(BaseModel):
    symbol: str
    profile: AssetProfile
    price: PriceData
    metrics: KeyMetrics
    news: list[NewsArticle] = []


class OHLCV(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class AnalysisRequest(BaseModel):
    provider: str
    model: str
    api_key: str
    base_url: Optional[str] = None


class AnalysisResponse(BaseModel):
    symbol: str
    analysis: str
    model_used: str
    context_sent: dict
```

- [ ] **Step 2: Verify models import correctly**

Run: `python -c "from backend.app.models.schemas import AssetDetail, AnalysisRequest, AnalysisResponse; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add Pydantic schemas for all API models"
```

---

### Task 3: yfinance Proxy

**Files:**
- Create: `backend/app/proxy/__init__.py`
- Create: `backend/app/proxy/yfinance.py`
- Create: `tests/test_yfinance_proxy.py`

- [ ] **Step 1: Write the yfinance proxy**

```python
import yfinance as yf
from backend.app.models.schemas import (
    AssetSearchResult,
    AssetDetail,
    AssetProfile,
    PriceData,
    KeyMetrics,
    NewsArticle,
    OHLCV,
)

PERIOD_MAP = {
    "1mo": "1mo",
    "6mo": "6mo",
    "1y": "1y",
    "5y": "5y",
    "max": "max",
}


def search(query: str) -> list[AssetSearchResult]:
    if not query or len(query.strip()) < 1:
        return []

    results = []
    ticker = yf.Ticker(query.strip())

    try:
        info = ticker.get_info()
    except Exception:
        return []

    if not info or info.get("symbol") is None:
        try:
            search_results = yf.Search(query.strip())
            quotes = search_results.quotes if hasattr(search_results, "quotes") else []
            for q in quotes[:8]:
                results.append(AssetSearchResult(
                    symbol=q.get("symbol", ""),
                    name=q.get("shortname") or q.get("longname") or "",
                    exchange=q.get("exchange", ""),
                    type="ETF" if "etf" in str(q.get("quoteType", "")).lower() else "stock",
                    market=q.get("market", ""),
                    currency=q.get("currency", "USD"),
                ))
        except Exception:
            pass
    else:
        currency = info.get("currency", "USD")
        results.append(AssetSearchResult(
            symbol=info.get("symbol", query.strip()),
            name=info.get("shortName") or info.get("longName") or query.strip(),
            exchange=info.get("exchange", ""),
            type="ETF" if "etf" in str(info.get("quoteType", "")).lower() else "stock",
            market=info.get("market", ""),
            currency=currency,
        ))

    return results


def fetch_asset(symbol: str) -> AssetDetail:
    ticker = yf.Ticker(symbol.strip())
    info = ticker.get_info()

    profile = AssetProfile(
        name=info.get("shortName") or info.get("longName") or symbol,
        sector=info.get("sector"),
        industry=info.get("industry"),
        market_cap=info.get("marketCap"),
        description=info.get("longBusinessSummary"),
        country=info.get("country"),
        website=info.get("website"),
    )

    price = PriceData(
        current=info.get("currentPrice") or info.get("regularMarketPrice") or 0,
        previous_close=info.get("previousClose"),
        open=info.get("open"),
        high=info.get("dayHigh"),
        low=info.get("dayLow"),
        change=info.get("regularMarketChange"),
        change_pct=info.get("regularMarketChangePercent"),
        currency=info.get("currency", "USD"),
    )

    metrics = KeyMetrics(
        pe_ratio=info.get("trailingPE"),
        pb_ratio=info.get("priceToBook"),
        eps=info.get("trailingEps"),
        dividend_yield=info.get("dividendYield"),
        beta=info.get("beta"),
        fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
        fifty_two_week_low=info.get("fiftyTwoWeekLow"),
    )

    news = []
    raw_news = info.get("news", []) or []
    for item in raw_news[:10]:
        news.append(NewsArticle(
            title=item.get("title", ""),
            publisher=item.get("publisher"),
            link=item.get("link"),
            published_at=str(item.get("providerPublishTime", "")) if item.get("providerPublishTime") else None,
            summary=item.get("summary"),
        ))

    return AssetDetail(
        symbol=symbol.strip(),
        profile=profile,
        price=price,
        metrics=metrics,
        news=news,
    )


def fetch_price_history(symbol: str, period: str = "1mo") -> list[OHLCV]:
    valid_period = PERIOD_MAP.get(period, "1mo")
    ticker = yf.Ticker(symbol.strip())
    hist = ticker.history(period=valid_period)

    if hist.empty:
        return []

    results = []
    for idx, row in hist.iterrows():
        results.append(OHLCV(
            date=idx.strftime("%Y-%m-%d"),
            open=round(float(row["Open"]), 4),
            high=round(float(row["High"]), 4),
            low=round(float(row["Low"]), 4),
            close=round(float(row["Close"]), 4),
            volume=int(row["Volume"]),
        ))
    return results
```

- [ ] **Step 2: Write proxy tests (mocked yfinance)**

```python
from unittest.mock import patch, MagicMock
from backend.app.proxy.yfinance import search, fetch_asset, fetch_price_history


@patch("backend.app.proxy.yfinance.yf.Ticker")
def test_fetch_asset_returns_detail(mock_ticker):
    mock_ticker.return_value.get_info.return_value = {
        "symbol": "AAPL",
        "shortName": "Apple Inc.",
        "sector": "Technology",
        "marketCap": 3000000000000,
        "currentPrice": 195.50,
        "previousClose": 194.80,
        "trailingPE": 32.5,
        "currency": "USD",
        "news": [],
    }
    result = fetch_asset("AAPL")
    assert result.symbol == "AAPL"
    assert result.profile.name == "Apple Inc."
    assert result.price.current == 195.50
    assert result.metrics.pe_ratio == 32.5


@patch("backend.app.proxy.yfinance.yf.Search")
def test_search_returns_results(mock_search):
    mock_search.return_value.quotes = [
        {"symbol": "AAPL", "shortname": "Apple Inc.", "exchange": "NMS", "quoteType": "EQUITY", "market": "us_market", "currency": "USD"},
    ]
    results = search("AAPL")
    assert len(results) > 0


@patch("backend.app.proxy.yfinance.yf.Ticker")
def test_fetch_price_history_returns_ohlcv(mock_ticker):
    import pandas as pd
    mock_ticker.return_value.history.return_value = pd.DataFrame({
        "Open": [195.0, 196.0],
        "High": [196.5, 197.0],
        "Low": [194.5, 195.5],
        "Close": [196.0, 196.5],
        "Volume": [50000000, 52000000],
    }, index=pd.to_datetime(["2026-05-01", "2026-05-02"]))
    result = fetch_price_history("AAPL", "1mo")
    assert len(result) == 2
    assert result[0].date == "2026-05-01"
    assert result[0].open == 195.0
```

Run: `python -m pytest tests/test_yfinance_proxy.py -v`
Expected: 3 passed

- [ ] **Step 3: Commit**

```bash
git add backend/app/proxy/ tests/test_yfinance_proxy.py
git commit -m "feat: add yfinance proxy with search, asset data, and price history"
```

---

### Task 4: Search Activity

**Files:**
- Create: `backend/app/activities/__init__.py`
- Create: `backend/app/activities/search.py`
- Create: `tests/test_search.py`

- [ ] **Step 1: Write the test**

```python
from unittest.mock import patch
from backend.app.models.schemas import AssetSearchResult


def test_search_endpoint_returns_results(client):
    with patch("backend.app.activities.search.search_proxy") as mock_search:
        mock_search.return_value = [
            AssetSearchResult(
                symbol="AAPL",
                name="Apple Inc.",
                exchange="NMS",
                type="stock",
                market="us_market",
                currency="USD",
            )
        ]
        response = client.get("/api/search?q=AAPL")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"


def test_search_endpoint_empty_query_returns_empty(client):
    response = client.get("/api/search?q=")
    assert response.status_code == 200
    assert response.json() == []
```

- [ ] **Step 2: Run tests to see them fail**

Run: `python -m pytest tests/test_search.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Write the search activity**

```python
from fastapi import APIRouter, Query
from backend.app.models.schemas import AssetSearchResult
from backend.app.proxy.yfinance import search as search_proxy

router = APIRouter()


@router.get("/api/search", response_model=list[AssetSearchResult])
def search_assets(q: str = Query(default="", description="Search query")):
    return search_proxy(q)
```

- [ ] **Step 4: Register the route in main.py**

In `backend/app/main.py`, add after `app = FastAPI(...)`:

```python
from backend.app.activities.search import router as search_router
app.include_router(search_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_search.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/activities/ backend/app/main.py tests/test_search.py
git commit -m "feat: add search autocomplete endpoint"
```

---

### Task 5: Asset Detail Activity

**Files:**
- Create: `backend/app/activities/asset_detail.py`
- Create: `tests/test_asset_detail.py`

- [ ] **Step 1: Write the test**

```python
from unittest.mock import patch
from backend.app.models.schemas import (
    AssetDetail, AssetProfile, PriceData, KeyMetrics
)


def test_asset_detail_endpoint(client):
    mock_detail = AssetDetail(
        symbol="AAPL",
        profile=AssetProfile(name="Apple Inc.", sector="Technology"),
        price=PriceData(current=195.50, currency="USD"),
        metrics=KeyMetrics(pe_ratio=32.5),
        news=[],
    )
    with patch("backend.app.activities.asset_detail.fetch_asset", return_value=mock_detail):
        response = client.get("/api/assets/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["profile"]["name"] == "Apple Inc."
    assert data["price"]["current"] == 195.50
```

- [ ] **Step 2: Run test to see it fail**

Run: `python -m pytest tests/test_asset_detail.py -v`
Expected: FAIL

- [ ] **Step 3: Write the asset detail activity**

```python
from fastapi import APIRouter
from backend.app.models.schemas import AssetDetail
from backend.app.proxy.yfinance import fetch_asset

router = APIRouter()


@router.get("/api/assets/{symbol}", response_model=AssetDetail)
def get_asset(symbol: str):
    return fetch_asset(symbol)
```

- [ ] **Step 4: Register in main.py**

```python
from backend.app.activities.asset_detail import router as asset_router
app.include_router(asset_router)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_asset_detail.py -v`
Expected: 1 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/activities/asset_detail.py backend/app/main.py tests/test_asset_detail.py
git commit -m "feat: add asset detail endpoint"
```

---

### Task 6: Price History Activity

**Files:**
- Create: `backend/app/activities/price_history.py`
- Create: `tests/test_price_history.py`

- [ ] **Step 1: Write the test**

```python
from unittest.mock import patch
from backend.app.models.schemas import OHLCV


def test_price_history_endpoint(client):
    mock_data = [
        OHLCV(date="2026-05-01", open=195.0, high=196.5, low=194.5, close=196.0, volume=50000000),
    ]
    with patch("backend.app.activities.price_history.fetch_price_history", return_value=mock_data):
        response = client.get("/api/assets/AAPL/price-history?period=1mo")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["date"] == "2026-05-01"


def test_price_history_default_period(client):
    with patch("backend.app.activities.price_history.fetch_price_history", return_value=[]) as mock:
        response = client.get("/api/assets/AAPL/price-history")
    assert response.status_code == 200
    mock.assert_called_once_with("AAPL", "1mo")
```

- [ ] **Step 2: Run test to see it fail**

Run: `python -m pytest tests/test_price_history.py -v`
Expected: FAIL

- [ ] **Step 3: Write the price history activity**

```python
from fastapi import APIRouter, Query
from backend.app.models.schemas import OHLCV
from backend.app.proxy.yfinance import fetch_price_history

router = APIRouter()


@router.get("/api/assets/{symbol}/price-history", response_model=list[OHLCV])
def get_price_history(symbol: str, period: str = Query(default="1mo", description="1mo|6mo|1y|5y|max")):
    return fetch_price_history(symbol, period)
```

- [ ] **Step 4: Register in main.py**

```python
from backend.app.activities.price_history import router as price_history_router
app.include_router(price_history_router)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_price_history.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/activities/price_history.py backend/app/main.py tests/test_price_history.py
git commit -m "feat: add price history endpoint"
```

---

### Task 7: LLM Proxy

**Files:**
- Create: `backend/app/proxy/llm.py`
- Create: `tests/test_llm_proxy.py`

- [ ] **Step 1: Write the LLM proxy**

```python
from backend.app.models.schemas import AssetDetail


SYSTEM_PROMPT = """You are a professional financial analyst. Analyze the following asset based on the provided data and recent news. Structure your response with:

1. **Overview** — Brief summary of the company and current situation
2. **Key Metrics Analysis** — What the numbers mean
3. **Recent News Impact** — How recent news may affect the asset
4. **Risks & Opportunities**
5. **Outlook** — Short to medium term outlook

Be objective. Highlight both positives and negatives. Do not give specific buy/sell recommendations."""


def build_context(asset: AssetDetail) -> str:
    parts = [f"## Asset: {asset.profile.name} ({asset.symbol})"]

    if asset.profile.sector:
        parts.append(f"Sector: {asset.profile.sector}")
    if asset.profile.market_cap:
        parts.append(f"Market Cap: ${asset.profile.market_cap:,.0f}")
    if asset.profile.description:
        parts.append(f"\nDescription: {asset.profile.description}")

    parts.append(f"\n### Current Price")
    parts.append(f"Price: {asset.price.current} {asset.price.currency}")
    if asset.price.change_pct is not None:
        parts.append(f"Change: {asset.price.change_pct:.2f}%")

    parts.append(f"\n### Key Metrics")
    if asset.metrics.pe_ratio:
        parts.append(f"P/E Ratio: {asset.metrics.pe_ratio:.2f}")
    if asset.metrics.pb_ratio:
        parts.append(f"P/B Ratio: {asset.metrics.pb_ratio:.2f}")
    if asset.metrics.eps:
        parts.append(f"EPS: ${asset.metrics.eps:.2f}")
    if asset.metrics.dividend_yield:
        parts.append(f"Dividend Yield: {asset.metrics.dividend_yield * 100:.2f}%")
    if asset.metrics.beta:
        parts.append(f"Beta: {asset.metrics.beta:.2f}")

    if asset.news:
        parts.append(f"\n### Recent News ({len(asset.news)} articles)")
        for n in asset.news[:5]:
            parts.append(f"- {n.title}")
            if n.summary:
                parts.append(f"  {n.summary[:200]}")

    return "\n".join(parts)


def analyze(provider: str, model: str, api_key: str, context: str, base_url: str | None = None) -> str:
    if provider == "claude":
        return _analyze_claude(model, api_key, context, base_url)
    elif provider == "openai":
        return _analyze_openai(model, api_key, context, base_url)
    elif provider == "deepseek":
        return _analyze_deepseek(model, api_key, context, base_url)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def _analyze_claude(model: str, api_key: str, context: str, base_url: str | None) -> str:
    import anthropic
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = anthropic.Anthropic(**kwargs)
    message = client.messages.create(
        model=model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": context}],
    )
    return message.content[0].text


def _analyze_openai(model: str, api_key: str, context: str, base_url: str | None) -> str:
    from openai import OpenAI
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
        max_tokens=2048,
    )
    return response.choices[0].message.content or ""


def _analyze_deepseek(model: str, api_key: str, context: str, base_url: str | None) -> str:
    from openai import OpenAI
    kwargs = {
        "api_key": api_key,
        "base_url": base_url or "https://api.deepseek.com/v1",
    }
    client = OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
        max_tokens=2048,
    )
    return response.choices[0].message.content or ""
```

- [ ] **Step 2: Write LLM proxy tests**

```python
from unittest.mock import patch, MagicMock
from backend.app.proxy.llm import build_context, analyze
from backend.app.models.schemas import (
    AssetDetail, AssetProfile, PriceData, KeyMetrics, NewsArticle
)


def test_build_context_includes_key_sections():
    asset = AssetDetail(
        symbol="AAPL",
        profile=AssetProfile(name="Apple Inc.", sector="Technology", market_cap=3000000000000),
        price=PriceData(current=195.50, change_pct=0.36, currency="USD"),
        metrics=KeyMetrics(pe_ratio=32.5, eps=6.0),
        news=[
            NewsArticle(title="Apple Launches New Product", summary="Exciting new release...")
        ],
    )
    ctx = build_context(asset)
    assert "Apple Inc." in ctx
    assert "Technology" in ctx
    assert "195.50" in ctx
    assert "32.50" in ctx
    assert "Apple Launches New Product" in ctx


@patch("backend.app.proxy.llm._analyze_claude")
def test_analyze_routes_to_claude(mock_claude):
    mock_claude.return_value = "Analysis result from Claude"
    result = analyze("claude", "claude-sonnet-4-6", "sk-test", "some context")
    assert result == "Analysis result from Claude"
    mock_claude.assert_called_once()


@patch("backend.app.proxy.llm._analyze_openai")
def test_analyze_routes_to_openai(mock_openai):
    mock_openai.return_value = "Analysis from GPT"
    result = analyze("openai", "gpt-4o", "sk-test", "some context", None)
    assert result == "Analysis from GPT"


def test_analyze_unsupported_provider():
    try:
        analyze("unknown", "model", "key", "context")
    except ValueError as e:
        assert "Unsupported provider" in str(e)
```

Run: `python -m pytest tests/test_llm_proxy.py -v`
Expected: 4 passed

- [ ] **Step 3: Commit**

```bash
git add backend/app/proxy/llm.py tests/test_llm_proxy.py
git commit -m "feat: add LLM proxy with Claude, GPT, and DeepSeek support"
```

---

### Task 8: Analyze Activity

**Files:**
- Create: `backend/app/activities/analyze.py`
- Create: `tests/test_analyze.py`

- [ ] **Step 1: Write the analyze test**

```python
from unittest.mock import patch


def test_analyze_endpoint(client):
    with patch("backend.app.activities.analyze.fetch_asset") as mock_fetch, \
         patch("backend.app.activities.analyze.analyze_asset") as mock_analyze:

        from backend.app.models.schemas import AssetDetail, AssetProfile, PriceData, KeyMetrics
        mock_fetch.return_value = AssetDetail(
            symbol="AAPL",
            profile=AssetProfile(name="Apple Inc."),
            price=PriceData(current=195.50, currency="USD"),
            metrics=KeyMetrics(),
            news=[],
        )
        mock_analyze.return_value = "Great analysis here."

        response = client.post("/api/analyze/AAPL", json={
            "provider": "claude",
            "model": "claude-sonnet-4-6",
            "api_key": "sk-test-key",
        })

    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["analysis"] == "Great analysis here."
    assert data["model_used"] == "claude-sonnet-4-6"
    assert "data_points" in data["context_sent"]
    assert "news_count" in data["context_sent"]
```

- [ ] **Step 2: Run test to see it fail**

Run: `python -m pytest tests/test_analyze.py -v`
Expected: FAIL

- [ ] **Step 3: Write the analyze activity**

```python
from fastapi import APIRouter
from backend.app.models.schemas import AnalysisRequest, AnalysisResponse
from backend.app.proxy.yfinance import fetch_asset
from backend.app.proxy.llm import build_context, analyze as analyze_asset

router = APIRouter()


@router.post("/api/analyze/{symbol}", response_model=AnalysisResponse)
def analyze_endpoint(symbol: str, body: AnalysisRequest):
    asset = fetch_asset(symbol)
    context = build_context(asset)
    analysis_text = analyze_asset(
        provider=body.provider,
        model=body.model,
        api_key=body.api_key,
        context=context,
        base_url=body.base_url,
    )
    return AnalysisResponse(
        symbol=symbol,
        analysis=analysis_text,
        model_used=body.model,
        context_sent={
            "data_points": len(context.split("\n")),
            "news_count": len(asset.news),
        },
    )
```

- [ ] **Step 4: Register in main.py**

```python
from backend.app.activities.analyze import router as analyze_router
app.include_router(analyze_router)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_analyze.py -v`
Expected: 1 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/activities/analyze.py backend/app/main.py tests/test_analyze.py
git commit -m "feat: add LLM analyze endpoint"
```

---

### Task 9: Frontend Project Scaffold

**Files:**
- Create: `frontend/` (via Vite)

- [ ] **Step 1: Create Vite + React + TypeScript project**

Run: `npm create vite@latest frontend -- --template react-ts`
Then: `cd frontend && npm install`

- [ ] **Step 2: Install additional dependencies**

Run: `cd frontend && npm install react-router-dom recharts react-markdown`

- [ ] **Step 3: Clean up Vite defaults**

Delete `frontend/src/App.css`, remove unused imports from `App.tsx`.

- [ ] **Step 4: Configure Vite proxy**

Edit `frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 5: Start both servers to verify**

Terminal 1: `cd backend && uvicorn backend.app.main:app --reload --port 8000`
Terminal 2: `cd frontend && npm run dev`

Open http://localhost:5173/api/health → should return `{"status":"ok"}`

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold React + Vite frontend with proxy config"
```

---

### Task 10: API Client

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/types.ts`

- [ ] **Step 1: Write shared types**

```typescript
// frontend/src/api/types.ts
export interface AssetSearchResult {
  symbol: string;
  name: string;
  exchange: string;
  type: string;
  market: string;
  currency: string;
}

export interface AssetProfile {
  name: string;
  sector?: string;
  industry?: string;
  market_cap?: number;
  description?: string;
  country?: string;
  website?: string;
}

export interface PriceData {
  current: number;
  previous_close?: number;
  open?: number;
  high?: number;
  low?: number;
  change?: number;
  change_pct?: number;
  currency: string;
}

export interface KeyMetrics {
  pe_ratio?: number;
  pb_ratio?: number;
  eps?: number;
  dividend_yield?: number;
  beta?: number;
  fifty_two_week_high?: number;
  fifty_two_week_low?: number;
}

export interface NewsArticle {
  title: string;
  publisher?: string;
  link?: string;
  published_at?: string;
  summary?: string;
}

export interface AssetDetail {
  symbol: string;
  profile: AssetProfile;
  price: PriceData;
  metrics: KeyMetrics;
  news: NewsArticle[];
}

export interface OHLCV {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface AnalysisRequest {
  provider: string;
  model: string;
  api_key: string;
  base_url?: string;
}

export interface AnalysisResponse {
  symbol: string;
  analysis: string;
  model_used: string;
  context_sent: {
    data_points: number;
    news_count: number;
  };
}
```

- [ ] **Step 2: Write API client**

```typescript
// frontend/src/api/client.ts
import type {
  AssetSearchResult,
  AssetDetail,
  OHLCV,
  AnalysisRequest,
  AnalysisResponse,
} from './types';

const BASE = '/api';

async function get<T>(url: string): Promise<T> {
  const res = await fetch(`${BASE}${url}`);
  if (!res.ok) throw new Error(`GET ${url} failed: ${res.status}`);
  return res.json();
}

async function post<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${url} failed: ${res.status}`);
  return res.json();
}

export function searchAssets(q: string): Promise<AssetSearchResult[]> {
  return get<AssetSearchResult[]>(`/search?q=${encodeURIComponent(q)}`);
}

export function getAssetDetail(symbol: string): Promise<AssetDetail> {
  return get<AssetDetail>(`/assets/${encodeURIComponent(symbol)}`);
}

export function getPriceHistory(symbol: string, period: string): Promise<OHLCV[]> {
  return get<OHLCV[]>(`/assets/${encodeURIComponent(symbol)}/price-history?period=${period}`);
}

export function analyzeAsset(
  symbol: string,
  config: AnalysisRequest
): Promise<AnalysisResponse> {
  return post<AnalysisResponse>(`/analyze/${encodeURIComponent(symbol)}`, config);
}
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api/
git commit -m "feat: add typed API client for all endpoints"
```

---

### Task 11: SearchBar Component + SearchPage

**Files:**
- Create: `frontend/src/components/SearchBar.tsx`
- Create: `frontend/src/pages/SearchPage.tsx`

- [ ] **Step 1: Write SearchBar component**

```tsx
// frontend/src/components/SearchBar.tsx
import { useState, useEffect, useRef } from 'react';
import { searchAssets } from '../api/client';
import type { AssetSearchResult } from '../api/types';

export default function SearchBar({ onSelect }: { onSelect: (r: AssetSearchResult) => void }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<AssetSearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (query.length < 1) {
      setResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await searchAssets(query);
        setResults(data);
        setOpen(data.length > 0);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div ref={ref} style={{ position: 'relative', maxWidth: 560, margin: '0 auto' }}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length > 0 && setOpen(true)}
        placeholder="Search ticker or name (e.g. AAPL, 0700.HK, 300502.SZ)..."
        style={{
          width: '100%', padding: '12px 16px', fontSize: 16, borderRadius: 8,
          border: '1px solid #ccc', outline: 'none', boxSizing: 'border-box',
        }}
      />
      {loading && <div style={{ padding: '8px 16px', fontSize: 13, color: '#888' }}>Searching...</div>}
      {open && results.length > 0 && (
        <ul style={{
          position: 'absolute', top: '100%', left: 0, right: 0,
          background: 'white', border: '1px solid #e0e0e0', borderRadius: 8,
          margin: '4px 0 0', padding: 0, listStyle: 'none', zIndex: 50,
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)', maxHeight: 360, overflowY: 'auto',
        }}>
          {results.map((r) => (
            <li
              key={r.symbol}
              onClick={() => {
                onSelect(r);
                setQuery(r.symbol);
                setOpen(false);
              }}
              style={{
                padding: '10px 16px', cursor: 'pointer', display: 'flex',
                justifyContent: 'space-between', alignItems: 'center',
                borderBottom: '1px solid #f0f0f0',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#f5f5f5')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'white')}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{r.symbol}</div>
                <div style={{ fontSize: 12, color: '#666' }}>{r.name}</div>
              </div>
              <div style={{ fontSize: 12, color: '#999' }}>
                <span style={{
                  padding: '2px 6px', borderRadius: 4, fontSize: 11,
                  background: r.type === 'etf' ? '#e8f5e9' : '#e3f2fd',
                  color: r.type === 'etf' ? '#2e7d32' : '#1565c0',
                }}>
                  {r.type.toUpperCase()}
                </span>
                <span style={{ marginLeft: 6 }}>{r.exchange}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Write SearchPage**

```tsx
// frontend/src/pages/SearchPage.tsx
import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import type { AssetSearchResult } from '../api/types';

export default function SearchPage() {
  const navigate = useNavigate();

  function handleSelect(result: AssetSearchResult) {
    navigate(`/asset/${encodeURIComponent(result.symbol)}`);
  }

  return (
    <div style={{ maxWidth: 600, margin: '80px auto 0', padding: '0 20px', textAlign: 'center' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>Asset Analytics</h1>
      <p style={{ color: '#666', marginBottom: 32 }}>
        Search any stock or ETF across global markets. Get AI-powered analysis.
      </p>
      <SearchBar onSelect={handleSelect} />
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/SearchBar.tsx frontend/src/pages/SearchPage.tsx
git commit -m "feat: add SearchBar with autocomplete and SearchPage"
```

---

### Task 12: AssetDetail Component

**Files:**
- Create: `frontend/src/components/AssetDetail.tsx`

- [ ] **Step 1: Write AssetDetail component**

```tsx
// frontend/src/components/AssetDetail.tsx
import type { AssetDetail as AssetDetailType } from '../api/types';

function fmt(n?: number): string {
  if (n == null) return '—';
  if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  return n.toLocaleString();
}

export default function AssetDetail({ asset }: { asset: AssetDetailType }) {
  const { profile, price, metrics } = asset;
  const isPositive = (price.change ?? 0) >= 0;

  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 24 }}>{profile.name}</h2>
          <div style={{ color: '#888', fontSize: 14, marginTop: 2 }}>
            {asset.symbol} · {profile.sector || '—'} · {profile.country || '—'}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 28, fontWeight: 700 }}>
            {price.current.toLocaleString()} <span style={{ fontSize: 14, color: '#888' }}>{price.currency}</span>
          </div>
          {price.change != null && (
            <div style={{ color: isPositive ? '#2e7d32' : '#c62828', fontSize: 14, fontWeight: 500 }}>
              {isPositive ? '+' : ''}{price.change.toFixed(2)} ({isPositive ? '+' : ''}{price.change_pct?.toFixed(2)}%)
            </div>
          )}
        </div>
      </div>

      {profile.description && (
        <p style={{ color: '#555', lineHeight: 1.6, marginTop: 16, fontSize: 14 }}>{profile.description}</p>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: 12, marginTop: 20 }}>
        <Metric label="Market Cap" value={fmt(profile.market_cap)} />
        <Metric label="P/E Ratio" value={metrics.pe_ratio?.toFixed(2)} />
        <Metric label="P/B Ratio" value={metrics.pb_ratio?.toFixed(2)} />
        <Metric label="EPS" value={metrics.eps != null ? `$${metrics.eps.toFixed(2)}` : undefined} />
        <Metric label="Dividend Yield" value={metrics.dividend_yield != null ? `${(metrics.dividend_yield * 100).toFixed(2)}%` : undefined} />
        <Metric label="Beta" value={metrics.beta?.toFixed(2)} />
        <Metric label="52W High" value={metrics.fifty_two_week_high?.toFixed(2)} />
        <Metric label="52W Low" value={metrics.fifty_two_week_low?.toFixed(2)} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value?: string }) {
  return (
    <div style={{ background: '#f9f9f9', padding: '10px 14px', borderRadius: 8 }}>
      <div style={{ fontSize: 12, color: '#888' }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 600, marginTop: 2 }}>{value || '—'}</div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/AssetDetail.tsx
git commit -m "feat: add AssetDetail component with profile, price, and metrics"
```

---

### Task 13: PriceChart Component

**Files:**
- Create: `frontend/src/components/PriceChart.tsx`

- [ ] **Step 1: Write PriceChart component**

```tsx
// frontend/src/components/PriceChart.tsx
import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { getPriceHistory } from '../api/client';
import type { OHLCV } from '../api/types';

const PERIODS = [
  { label: '1M', value: '1mo' },
  { label: '6M', value: '6mo' },
  { label: '1Y', value: '1y' },
  { label: '5Y', value: '5y' },
  { label: 'Max', value: 'max' },
];

export default function PriceChart({ symbol }: { symbol: string }) {
  const [period, setPeriod] = useState('1mo');
  const [data, setData] = useState<OHLCV[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getPriceHistory(symbol, period)
      .then(setData)
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [symbol, period]);

  const chartData = data.map((d) => ({ date: d.date, price: d.close }));

  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h3 style={{ margin: 0, fontSize: 18 }}>Price History</h3>
        <div style={{ display: 'flex', gap: 4 }}>
          {PERIODS.map((p) => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              style={{
                padding: '4px 12px', border: '1px solid #ddd', borderRadius: 6,
                background: period === p.value ? '#1976d2' : 'white',
                color: period === p.value ? 'white' : '#555',
                cursor: 'pointer', fontSize: 13, fontWeight: 500,
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>
      {loading ? (
        <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>Loading chart...</div>
      ) : chartData.length === 0 ? (
        <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>No price data available</div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" fontSize={11} tick={{ fill: '#888' }} />
            <YAxis fontSize={11} tick={{ fill: '#888' }} domain={['auto', 'auto']} />
            <Tooltip />
            <Line type="monotone" dataKey="price" stroke="#1976d2" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/PriceChart.tsx
git commit -m "feat: add PriceChart component with period selector"
```

---

### Task 14: NewsList Component

**Files:**
- Create: `frontend/src/components/NewsList.tsx`

- [ ] **Step 1: Write NewsList component**

```tsx
// frontend/src/components/NewsList.tsx
import type { NewsArticle } from '../api/types';

export default function NewsList({ news }: { news: NewsArticle[] }) {
  if (news.length === 0) return null;

  return (
    <div style={{ marginBottom: 24 }}>
      <h3 style={{ fontSize: 18, marginBottom: 12 }}>Recent News</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {news.map((article, i) => (
          <a
            key={i}
            href={article.link || '#'}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              textDecoration: 'none', color: 'inherit',
              padding: '12px 14px', borderRadius: 8, border: '1px solid #eee',
              display: 'block',
            }}
          >
            <div style={{ fontWeight: 500, fontSize: 14, marginBottom: 3 }}>{article.title}</div>
            <div style={{ display: 'flex', gap: 10, fontSize: 12, color: '#888' }}>
              {article.publisher && <span>{article.publisher}</span>}
              {article.published_at && <span>{formatDate(article.published_at)}</span>}
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}

function formatDate(ts: string): string {
  try {
    const d = new Date(Number(ts) * 1000);
    return d.toLocaleDateString();
  } catch {
    return ts;
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/NewsList.tsx
git commit -m "feat: add NewsList component"
```

---

### Task 15: SettingsDialog Component

**Files:**
- Create: `frontend/src/components/SettingsDialog.tsx`

- [ ] **Step 1: Write SettingsDialog component**

```tsx
// frontend/src/components/SettingsDialog.tsx
import { useState } from 'react';
import type { AnalysisRequest } from '../api/types';

const STORAGE_KEY = 'llm_settings';

export function loadSettings(): AnalysisRequest | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

function saveSettings(settings: AnalysisRequest) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: (s: AnalysisRequest) => void;
}

const PROVIDERS = [
  { value: 'claude', label: 'Claude (Anthropic)' },
  { value: 'openai', label: 'GPT (OpenAI)' },
  { value: 'deepseek', label: 'DeepSeek' },
];

export default function SettingsDialog({ open, onClose, onSaved }: Props) {
  const existing = loadSettings();
  const [provider, setProvider] = useState(existing?.provider || 'claude');
  const [model, setModel] = useState(existing?.model || '');
  const [apiKey, setApiKey] = useState(existing?.api_key || '');
  const [baseUrl, setBaseUrl] = useState(existing?.base_url || '');

  if (!open) return null;

  function handleSave() {
    const settings: AnalysisRequest = { provider, model, api_key: apiKey, base_url: baseUrl || undefined };
    saveSettings(settings);
    onSaved(settings);
    onClose();
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100,
    }} onClick={onClose}>
      <div style={{
        background: 'white', borderRadius: 12, padding: 28, maxWidth: 420, width: '90%',
        boxShadow: '0 8px 30px rgba(0,0,0,0.2)',
      }} onClick={(e) => e.stopPropagation()}>
        <h3 style={{ margin: '0 0 20px', fontSize: 20 }}>LLM Settings</h3>

        <label style={labelStyle}>Provider</label>
        <select value={provider} onChange={(e) => setProvider(e.target.value)} style={inputStyle}>
          {PROVIDERS.map((p) => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>

        <label style={labelStyle}>Model Name</label>
        <input
          type="text" value={model} onChange={(e) => setModel(e.target.value)}
          placeholder={provider === 'claude' ? 'claude-sonnet-4-6' : provider === 'openai' ? 'gpt-4o' : 'deepseek-chat'}
          style={inputStyle}
        />

        <label style={labelStyle}>API Key</label>
        <input
          type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-..."
          style={inputStyle}
        />

        <label style={labelStyle}>Base URL (optional)</label>
        <input
          type="text" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)}
          placeholder={provider === 'deepseek' ? 'https://api.deepseek.com/v1' : 'Leave empty for default'}
          style={inputStyle}
        />

        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 20 }}>
          <button onClick={onClose} style={{ ...btnStyle, background: '#eee', color: '#555' }}>Cancel</button>
          <button
            onClick={handleSave}
            disabled={!model || !apiKey}
            style={{ ...btnStyle, background: !model || !apiKey ? '#ccc' : '#1976d2', color: 'white' }}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}

const labelStyle: React.CSSProperties = { display: 'block', fontSize: 13, fontWeight: 500, marginBottom: 4, marginTop: 12 };

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #ddd',
  fontSize: 14, boxSizing: 'border-box', outline: 'none',
};

const btnStyle: React.CSSProperties = {
  padding: '8px 20px', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontWeight: 500,
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/SettingsDialog.tsx
git commit -m "feat: add SettingsDialog for LLM configuration"
```

---

### Task 16: AnalyzePanel Component

**Files:**
- Create: `frontend/src/components/AnalyzePanel.tsx`

- [ ] **Step 1: Write AnalyzePanel component**

```tsx
// frontend/src/components/AnalyzePanel.tsx
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { analyzeAsset } from '../api/client';
import { loadSettings } from './SettingsDialog';
import type { AnalysisResponse } from '../api/types';

interface Props {
  symbol: string;
  onOpenSettings: () => void;
}

export default function AnalyzePanel({ symbol, onOpenSettings }: Props) {
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    const settings = loadSettings();
    if (!settings) {
      onOpenSettings();
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await analyzeAsset(symbol, settings);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          style={{
            padding: '10px 24px', background: loading ? '#ccc' : '#10b981', color: 'white',
            border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Analyzing...' : 'Analyze with AI'}
        </button>
        <button
          onClick={onOpenSettings}
          style={{
            padding: '10px 16px', background: 'transparent', border: '1px solid #ddd',
            borderRadius: 8, fontSize: 13, cursor: 'pointer', color: '#666',
          }}
        >
          LLM Settings
        </button>
      </div>

      {error && (
        <div style={{ padding: 12, background: '#fff3f3', color: '#c62828', borderRadius: 8, fontSize: 14, marginBottom: 12 }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ background: '#fafafa', border: '1px solid #eee', borderRadius: 12, padding: 20, marginTop: 8 }}>
          <div style={{ fontSize: 12, color: '#999', marginBottom: 16 }}>
            Analysis by {result.model_used} · {result.context_sent.news_count} news articles
          </div>
          <div style={{ lineHeight: 1.7, fontSize: 14 }}>
            <ReactMarkdown>{result.analysis}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/AnalyzePanel.tsx
git commit -m "feat: add AnalyzePanel with LLM analysis call and markdown rendering"
```

---

### Task 17: AssetPage

**Files:**
- Create: `frontend/src/pages/AssetPage.tsx`

- [ ] **Step 1: Write AssetPage**

```tsx
// frontend/src/pages/AssetPage.tsx
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getAssetDetail } from '../api/client';
import AssetDetailComponent from '../components/AssetDetail';
import PriceChart from '../components/PriceChart';
import NewsList from '../components/NewsList';
import SettingsDialog from '../components/SettingsDialog';
import AnalyzePanel from '../components/AnalyzePanel';
import type { AssetDetail, AnalysisRequest } from '../api/types';

export default function AssetPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const [asset, setAsset] = useState<AssetDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [, setSettings] = useState<AnalysisRequest | null>(null);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    setError(null);
    getAssetDetail(symbol)
      .then(setAsset)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: '#999' }}>Loading {symbol}...</div>;
  if (error) return <div style={{ padding: 40, textAlign: 'center', color: '#c62828' }}>Error: {error}</div>;
  if (!asset) return null;

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '24px 20px 60px' }}>
      <AssetDetailComponent asset={asset} />
      <PriceChart symbol={asset.symbol} />
      <NewsList news={asset.news} />
      <AnalyzePanel symbol={asset.symbol} onOpenSettings={() => setSettingsOpen(true)} />
      <SettingsDialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onSaved={setSettings}
      />
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/AssetPage.tsx
git commit -m "feat: add AssetPage combining detail, chart, news, and analyze"
```

---

### Task 18: App Routing

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Write App with routing**

```tsx
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import SearchPage from './pages/SearchPage';
import AssetPage from './pages/AssetPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/asset/:symbol" element={<AssetPage />} />
      </Routes>
    </BrowserRouter>
  );
}
```

Replace existing `App.tsx` content.

- [ ] **Step 2: Verify main.tsx works**

`frontend/src/main.tsx` should already have:

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **Step 3: Verify app loads**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

Start both servers and navigate to http://localhost:5173 → SearchPage appears.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: wire up routing for search and asset pages"
```

---

### Task 19: Integration Verification

**Files:** none (manual verification)

- [ ] **Step 1: Start backend**

Run: `cd backend && uvicorn backend.app.main:app --reload --port 8000`

- [ ] **Step 2: Start frontend**

Run: `cd frontend && npm run dev`

- [ ] **Step 3: Test search flow**

1. Open http://localhost:5173
2. Type "AAPL" in search bar → autocomplete shows results
3. Click a result → navigates to /asset/AAPL

- [ ] **Step 4: Test asset detail page**

1. Verify price and chart display
2. Verify metrics grid shows
3. Verify news list renders (if available)

- [ ] **Step 5: Test analyze flow**

1. Click "LLM Settings" → configure provider, model, API key → Save
2. Click "Analyze with AI" → loading state, then analysis renders

- [ ] **Step 6: Test multiple market tickers**

Search: `0700.HK` (HK), `300502.SZ` (CN), `7203.T` (JP), `SHEL.L` (UK) — all should return results.

- [ ] **Step 7: Mark phase complete**

Update `docs/superpowers/tasks/phase-1.md` status to `completed` and check all checkboxes.

- [ ] **Step 8: Commit if any fixes were made**

```bash
git add -A
git commit -m "chore: complete Phase 1 integration verification"
```
