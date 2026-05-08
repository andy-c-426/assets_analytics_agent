# Asset Analytics Agent

A web application for searching and analyzing financial assets (stocks, ETFs) across all major global markets. Search by ticker, view detailed asset information, and get AI-powered analysis using your own LLM API keys.

Built with Claude Code + DeepSeek V4 Pro.

## Features

- **Global search** — autocomplete search across US, HK, CN, JP, UK, KR, TW, EU, and more
- **Asset detail** — interactive price chart, key metrics (P/E, P/B, EPS, dividend yield, beta), company profile
- **AI analysis** — LLM-powered analysis using Claude, GPT, or DeepSeek with your own API keys
- **Settings** — configure your LLM provider, model, and API key (stored locally, never sent to our server)

## Architecture

```
Browser (React) → FastAPI → yfinance (market data + search)
                        └→ Claude / GPT / DeepSeek (LLM analysis)
```

- **Backend:** Python FastAPI — stateless API, fetches market data from yfinance, proxies LLM calls
- **Frontend:** React + Vite + TypeScript — single-page app with search, charts, and analysis
- **Data:** yfinance for multi-market price data, fundamentals, news, and search autocomplete

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+

### Install & Run

```bash
# Clone and enter the project
git clone https://github.com/chenhaoyu426/assets_analytics_agent.git
cd assets_analytics_agent

# Backend setup
cd backend
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Start both servers
cd ..
./start.sh
```

- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs

### Manual Start

```bash
# Terminal 1 — Backend
cd backend && uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/search?q={query}` | Autocomplete search across all markets |
| GET | `/api/assets/{symbol}` | Asset detail: profile, price, metrics, news |
| GET | `/api/assets/{symbol}/price-history?period=1mo` | OHLCV price series (1mo, 6mo, 1y, 5y, max) |
| POST | `/api/analyze/{symbol}` | LLM analysis with user-provided API config |

### POST /api/analyze/{symbol}

Request body:

```json
{
  "provider": "claude",
  "model": "claude-sonnet-4-6",
  "api_key": "sk-...",
  "base_url": null
}
```

Response:

```json
{
  "symbol": "AAPL",
  "analysis": "## Overview\nApple Inc. is...",
  "model_used": "claude-sonnet-4-6",
  "context_sent": {
    "data_points": 42,
    "news_count": 5
  }
}
```

## Usage

1. Open http://localhost:5173
2. Search for a ticker (e.g. `AAPL`, `0700.HK`, `300502.SZ`, `7203.T`)
3. Click a result to see detailed information and price chart
4. Click **LLM Settings** to configure your LLM provider and API key
5. Click **Analyze with AI** to get an AI-powered analysis

Your API key is stored in your browser's localStorage and sent directly to the backend per request. It is never stored on the server.

## Project Structure

```
assets_analytics_agent/
├── backend/                    # Python FastAPI
│   ├── app/
│   │   ├── main.py             # app entry point
│   │   ├── models/             # Pydantic schemas
│   │   ├── activities/         # one file per endpoint
│   │   │   ├── search.py       # GET /api/search
│   │   │   ├── asset_detail.py # GET /api/assets/{symbol}
│   │   │   ├── price_history.py# GET /api/assets/{symbol}/price-history
│   │   │   └── analyze.py      # POST /api/analyze/{symbol}
│   │   └── proxy/              # external dependency adapters
│   │       ├── yfinance.py     # market data + search + news
│   │       └── llm.py          # Claude / GPT / DeepSeek routing
│   └── requirements.txt
├── frontend/                   # React + Vite + TypeScript
│   ├── src/
│   │   ├── components/         # SearchBar, AssetDetail, PriceChart,
│   │   │                       # NewsList, SettingsDialog, AnalyzePanel
│   │   ├── pages/              # SearchPage, AssetPage
│   │   ├── api/                # API client + types
│   │   └── App.tsx             # routing
│   └── vite.config.ts
├── tests/                      # Python backend tests
├── docs/superpowers/           # design specs, plans, tasks
├── start.sh                    # start both servers
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

See `docs/superpowers/` for the full design spec, implementation plan, and task breakdown.

### Conventions

- `activities/` — one file per API endpoint, handles request/response only
- `proxy/` — adapters for all external dependencies (yfinance, LLM providers)
- `models/` — shared Pydantic schemas consumed by both activities and proxy
- No server-side API key storage — keys are passed per request
- No local search index — yfinance provides autocomplete

## License

MIT © 2026 chenhaoyu426
