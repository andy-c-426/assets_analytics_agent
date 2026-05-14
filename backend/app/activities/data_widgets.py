import httpx
from fastapi import APIRouter, Query

router = APIRouter()

AGENT_SERVICE_URL = "http://localhost:8001"


@router.get("/api/assets/{symbol}/market-data")
async def get_market_data(symbol: str):
    """Proxy to agent service: structured market data."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{AGENT_SERVICE_URL}/market-data/{symbol}")
        resp.raise_for_status()
        return resp.json()


@router.get("/api/assets/{symbol}/macro-research")
async def get_macro_research(symbol: str):
    """Proxy to agent service: macro research and sector analysis."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{AGENT_SERVICE_URL}/macro-research/{symbol}")
        resp.raise_for_status()
        return resp.json()


@router.get("/api/assets/{symbol}/sentiment-news")
async def get_sentiment_news(symbol: str, finnhub_api_key: str | None = Query(default=None)):
    """Proxy to agent service: sentiment news."""
    params = ""
    if finnhub_api_key:
        params = f"?finnhub_api_key={finnhub_api_key}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{AGENT_SERVICE_URL}/sentiment-news/{symbol}{params}")
        resp.raise_for_status()
        return resp.json()


@router.get("/api/assets/{symbol}/capital-flow")
async def get_capital_flow(symbol: str):
    """Proxy to agent service: Stock Connect capital flow (CN/HK only)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{AGENT_SERVICE_URL}/capital-flow/{symbol}")
        resp.raise_for_status()
        return resp.json()


@router.get("/api/assets/{symbol}/cn-sentiment")
async def get_cn_sentiment(symbol: str):
    """Proxy to agent service: CN/HK market sentiment (CN/HK only)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{AGENT_SERVICE_URL}/cn-sentiment/{symbol}")
        resp.raise_for_status()
        return resp.json()


@router.get("/api/assets/{symbol}/us-fundamentals")
async def get_us_fundamentals(symbol: str):
    """Proxy to agent service: US fundamentals (US only)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{AGENT_SERVICE_URL}/us-fundamentals/{symbol}")
        resp.raise_for_status()
        return resp.json()
