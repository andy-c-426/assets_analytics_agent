from typing import Optional

from pydantic import BaseModel


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
    finnhub_api_key: Optional[str] = None
    language: Optional[str] = None


class AnalysisResponse(BaseModel):
    symbol: str
    analysis: str
    model_used: str
    context_sent: dict
