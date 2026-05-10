from fastapi import APIRouter, Query
from backend.app.models.schemas import AssetDetail
from backend.app.proxy.yfinance import fetch_asset

router = APIRouter()


@router.get("/api/assets/{symbol}", response_model=AssetDetail)
def get_asset(symbol: str, finnhub_key: str | None = Query(default=None)):
    return fetch_asset(symbol, finnhub_key=finnhub_key)
