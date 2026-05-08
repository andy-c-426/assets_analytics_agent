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
