from fastapi import APIRouter
from backend.app.models.schemas import AssetDetail
from backend.app.proxy.yfinance import fetch_asset

router = APIRouter()


@router.get("/api/assets/{symbol}", response_model=AssetDetail)
def get_asset(symbol: str):
    return fetch_asset(symbol)
