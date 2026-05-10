import os
from datetime import datetime, timedelta, timezone
from langchain_core.tools import tool

# Module-level API key — set by agent router before streaming
_api_key: str | None = None


def set_api_key(key: str | None) -> None:
    global _api_key
    _api_key = key


def _get_key() -> str | None:
    return _api_key or os.environ.get("FINNHUB_API_KEY")


@tool
def fetch_finnhub_news(symbol: str) -> str:
    """PRIMARY news tool — Fetch structured financial news for a ticker from Finnhub API.

    Always use this first for any stock/ETF news. Returns headlines, summaries,
    sources, and publish dates. Automatically falls back to web search if the
    API key is missing or the API returns no results or errors.

    Args:
        symbol: Ticker symbol (e.g. AAPL, TSLA, 00700.HK)
    """
    key = _get_key()
    if not key:
        from agent_service.app.tools.news_search import search_latest_news
        return (
            "Note: Finnhub API key not configured. Using web search instead.\n\n"
            + search_latest_news.invoke({"query": f"{symbol} stock news", "max_results": 5})
        )

    import requests
    from dateutil.parser import parse as parse_date

    s = symbol.strip().upper()
    today = datetime.now(timezone.utc)
    week_ago = today - timedelta(days=7)

    to_date = today.strftime("%Y-%m-%d")
    from_date = week_ago.strftime("%Y-%m-%d")

    try:
        resp = requests.get(
            "https://finnhub.io/api/v1/company-news",
            params={"symbol": s, "from": from_date, "to": to_date, "token": key},
            timeout=10,
        )
        resp.raise_for_status()
        articles = resp.json()

        if not isinstance(articles, list) or not articles:
            from agent_service.app.tools.news_search import search_latest_news
            return (
                f"Finnhub returned no news for {symbol}. Falling back to web search.\n\n"
                + search_latest_news.invoke({"query": f"{symbol} stock news", "max_results": 5})
            )

        lines = [f"Finnhub News for {symbol} ({len(articles)} articles, {from_date} to {to_date}):\n"]
        for a in articles[:8]:
            headline = a.get("headline", "N/A")
            summary = a.get("summary", "")
            source = a.get("source", "N/A")
            url = a.get("url", "")
            published = a.get("datetime")
            category = a.get("category", "")

            date_str = ""
            if published:
                try:
                    date_str = parse_date(str(published)).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    date_str = str(published)[:16]

            meta = f"[{date_str}]" if date_str else ""
            if category:
                meta += f" [{category}]"

            lines.append(f"- {meta} {headline}")
            lines.append(f"  Source: {source} | {url}")
            if summary:
                lines.append(f"  {summary[:250]}")
            lines.append("")

        return "\n".join(lines)

    except Exception as e:
        from agent_service.app.tools.news_search import search_latest_news
        return (
            f"Note: Finnhub API error ({e}), falling back to web search.\n\n"
            + search_latest_news.invoke({"query": f"{symbol} stock news", "max_results": 5})
        )
