from fastapi import APIRouter, Query

from backend.app.models.schemas import OHLCV
from backend.app.proxy.yfinance import fetch_price_history

router = APIRouter()


@router.get("/api/assets/{symbol}/price-history", response_model=list[OHLCV])
def get_price_history(symbol: str, period: str = Query(default="1mo", description="1mo|6mo|1y|5y|max")):
    return fetch_price_history(symbol, period)
