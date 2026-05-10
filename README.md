# Asset Analytics Agent

A web application for searching and analyzing financial assets (stocks, ETFs) across all major global markets. Search by ticker, view detailed asset information, and get AI-powered analysis using your own LLM API keys.

Built with Claude Code + DeepSeek V4 Pro.

## Features

- **Global search** — autocomplete search across US, HK, CN, JP, UK, KR, TW, EU, and more
- **Asset detail** — interactive price chart, key metrics (P/E, P/B, EPS, dividend yield, beta), company profile with description toggle
- **AI analysis** — multi-step LangGraph agent (plan → execute → observe → synthesize) with live streaming visibility into each stage
- **Real-time market data** — Futu OpenD integration for market snapshots (price, volume, valuation, fundamentals, 52W range), with automatic yfinance fallback
- **News sources** — Finnhub API for ticker-specific financial news, DuckDuckGo web search fallback
- **Bloomberg-style analytics** — pre-computed valuation zones, momentum returns, RSI, drawdown, volatility with TTL cache
- **Parallel tool execution** — concurrent data fetching to reduce latency
- **Settings** — configure LLM provider, model, API key, and optional Finnhub key (stored locally, never sent to our server)

## Architecture

```
Browser (React SPA)
    │
    ▼
FastAPI Backend (port 8000)
    ├─→ yfinance (market data + search + autocomplete)
    └─→ Agent Service (port 8001, SSE streaming)
            ├─→ LangGraph agent (plan → execute → observe → synthesize)
            ├─→ Futu OpenD (real-time snapshots, optional)
            ├─→ Finnhub / DuckDuckGo (news)
            └─→ Claude / GPT / DeepSeek (LLM)
```

- **Backend:** Python FastAPI — stateless API proxy, fetches market data from yfinance, forwards analyze requests to agent service
- **Agent Service:** Python FastAPI + LangGraph — multi-step reasoning with tool-calling, parallel execution, SSE streaming, and pre-computed analytics
- **Frontend:** React + Vite + TypeScript — SPA with live-streamed analysis, plan reasoning display, and settings
- **Data sources:** yfinance (primary), Futu OpenD (real-time, optional), Finnhub (news, optional), DuckDuckGo (news fallback)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- (Optional) [Futu OpenD](https://www.futunn.com/download/OpenD) — for real-time market snapshots
- (Optional) [Finnhub API key](https://finnhub.io/register) — for ticker-specific news

### Install & Run

```bash
# Clone and enter the project
git clone https://github.com/chenhaoyu426/assets_analytics_agent.git
cd assets_analytics_agent

# Backend setup
cd backend
pip install -r requirements.txt

# Agent service setup
cd ../agent-service
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Start all three servers
cd ..
./start.sh
```

- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs
- Agent API docs: http://localhost:8001/docs

### Manual Start

```bash
# Terminal 1 — Backend (run from project root)
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 — Agent Service
cd agent-service && uvicorn agent_service.app.main:app --reload --port 8001

# Terminal 3 — Frontend
cd frontend && npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/search?q={query}` | Autocomplete search across all markets |
| GET | `/api/assets/{symbol}` | Asset detail: profile, price, metrics, news |
| GET | `/api/assets/{symbol}/price-history?period=1mo` | OHLCV price series (1mo, 6mo, 1y, 5y, max) |
| POST | `/api/analyze/{symbol}` | LLM agent analysis with SSE streaming |

### POST /api/analyze/{symbol}

This endpoint returns a Server-Sent Events (SSE) stream with real-time progress updates. Each stage of the agent's reasoning is emitted as it happens.

Request body:

```json
{
  "provider": "claude",
  "model": "claude-sonnet-4-6",
  "api_key": "sk-...",
  "base_url": null,
  "finnhub_api_key": "c..."
}
```

SSE event types:

| Event | Description |
|-------|-------------|
| `step_started` | Agent stage began (planning, evaluating, synthesizing) |
| `plan_reasoning` | LLM's reasoning about tool selection |
| `tool_called` | Tool invocation started |
| `tool_result` | Tool returned data summary |
| `report_ready` | Final analysis report (markdown) |
| `error` | Recoverable or non-recoverable error |
| `done` | Stream complete |

### Agent Tools

| Tool | Source | Description |
|------|--------|-------------|
| `fetch_futu_data` | Futu OpenD | Real-time market snapshot, valuation, fundamentals |
| `fetch_asset_data` | yfinance | Asset profile, price, metrics (fallback) |
| `fetch_price_history` | yfinance | OHLCV historical price series |
| `calculate_technicals` | computed | SMA, EMA, RSI, volatility |
| `fetch_finnhub_news` | Finnhub | Ticker-specific financial news |
| `search_latest_news` | DuckDuckGo | Web news search (fallback) |

## Usage

1. Open http://localhost:5173
2. Search for a ticker (e.g. `AAPL`, `0700.HK`, `300502.SZ`, `7203.T`)
3. Click a result to see detailed information and price chart
4. Click **LLM Settings** to configure your LLM provider, API key, and optional Finnhub key
5. Click **Analyze with AI** to watch the agent reason through a multi-step analysis in real time

Your API keys are stored in your browser's localStorage and sent directly to the backend per request. They are never stored on the server.

## Project Structure

```
assets_analytics_agent/
├── backend/                         # Python FastAPI (proxy layer)
│   ├── app/
│   │   ├── main.py                  # app entry point
│   │   ├── models/                  # Pydantic schemas
│   │   ├── activities/              # one file per endpoint
│   │   │   ├── search.py            # GET /api/search
│   │   │   ├── asset_detail.py      # GET /api/assets/{symbol}
│   │   │   ├── price_history.py     # GET /api/assets/{symbol}/price-history
│   │   │   └── analyze.py           # POST /api/analyze/{symbol} (SSE proxy)
│   │   └── proxy/                   # external adapters
│   │       ├── yfinance.py          # market data + search + news
│   │       └── llm.py               # Claude / GPT / DeepSeek routing
│   └── requirements.txt
├── agent-service/                   # Python FastAPI + LangGraph agent
│   ├── agent_service/app/
│   │   ├── main.py                  # entry point (port 8001)
│   │   ├── agent_router.py          # SSE streaming endpoint
│   │   ├── graph.py                 # StateGraph (plan→execute→observe→synthesize)
│   │   ├── prompts.py               # LLM prompts + tool registry
│   │   ├── events.py                # SSE event formatters
│   │   ├── state.py                 # AgentState definition
│   │   ├── cache.py                 # TTL analytics cache
│   │   ├── analytics/               # Bloomberg-style derived metrics
│   │   │   ├── __init__.py
│   │   │   └── metrics.py
│   │   ├── tools/                   # LangChain tools
│   │   │   ├── yfinance_tools.py    # fetch_asset_data, fetch_price_history
│   │   │   ├── futu_data.py         # fetch_futu_data (Futu OpenD)
│   │   │   ├── finnhub_news.py      # fetch_finnhub_news (Finnhub)
│   │   │   ├── news_search.py       # search_latest_news (DuckDuckGo)
│   │   │   └── technicals.py        # calculate_technicals
│   │   └── llm/                     # LLM client factory
│   │       ├── __init__.py
│   │       └── client_factory.py
│   └── requirements.txt
├── frontend/                        # React + Vite + TypeScript
│   ├── src/
│   │   ├── components/              # SearchBar, AssetDetail, PriceChart,
│   │   │                            # NewsList, SettingsDialog, AnalyzePanel
│   │   ├── pages/                   # SearchPage, AssetPage
│   │   ├── api/                     # API client + types
│   │   └── App.tsx                  # routing
│   └── vite.config.ts
├── tests/                           # Python backend tests
├── docs/superpowers/                # design specs, plans, tasks
├── features/                        # completed feature records
├── start.sh                         # start all three servers
└── README.md
```

## Development

### Run Tests

```bash
# All backend tests
python3 -m pytest tests/ -v

# Single test file
python3 -m pytest tests/test_search.py -v

# Frontend type check
cd frontend && npx tsc --noEmit
```

### Design Documents

See `docs/superpowers/` for the full design spec, implementation plan, and task breakdown. See `features/` for completed feature records with changed files and commits.

### Conventions

- `activities/` — one file per API endpoint, handles request/response only
- `proxy/` — adapters for all external dependencies (yfinance, LLM providers)
- `tools/` — one file per LangChain agent tool
- `models/` — shared Pydantic schemas consumed by both activities and proxy
- No server-side API key storage — keys are passed per request
- No local search index — yfinance provides autocomplete

## License

MIT © 2026 chenhaoyu426
