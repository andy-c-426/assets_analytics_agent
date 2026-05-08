from fastapi import APIRouter, Query
from backend.app.models.schemas import AssetSearchResult
from backend.app.proxy.yfinance import search as search_proxy

router = APIRouter()


@router.get("/api/search", response_model=list[AssetSearchResult])
def search_assets(q: str = Query(default="", description="Search query")):
    return search_proxy(q)
