"""Tool 3/3: 情绪与舆情 (Sentiment & Alternative Data)

Primary: Finnhub API — structured financial news, headlines, summaries, categories
Secondary: yfinance news — ticker news from yfinance
Tertiary: DuckDuckGo — general web news search
"""

import os
from datetime import datetime, timedelta, timezone
from langchain_core.tools import tool


def _get_key(api_key: str | None = None) -> str | None:
    return api_key or os.environ.get("FINNHUB_API_KEY")


def _fetch_finnhub(symbol: str, api_key: str | None = None) -> str | None:
    """Primary: Finnhub API for structured financial news."""
    key = _get_key(api_key)
    if not key:
        return None

    import requests
    from dateutil.parser import parse as parse_date

    s = symbol.strip().upper()
    today = datetime.now(timezone.utc)
    week_ago = today - timedelta(days=7)

    try:
        resp = requests.get(
            "https://finnhub.io/api/v1/company-news",
            params={
                "symbol": s,
                "from": week_ago.strftime("%Y-%m-%d"),
                "to": today.strftime("%Y-%m-%d"),
                "token": key,
            },
            timeout=10,
        )
        resp.raise_for_status()
        articles = resp.json()

        if not isinstance(articles, list) or not articles:
            return None

        lines = [
            f"=== Sentiment & News (Finnhub): {symbol} ===",
            f"Period: {week_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}",
            f"Articles: {len(articles)}",
            "",
        ]

        # Categorize articles
        categories: dict[str, list[dict]] = {}
        for a in articles[:12]:
            cat = a.get("category", "general")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(a)

        for cat, items in categories.items():
            lines.append(f"--- {cat.upper()} ({len(items)} articles) ---")
            for a in items[:4]:
                headline = a.get("headline", "N/A")
                summary = a.get("summary", "")
                source = a.get("source", "N/A")
                url = a.get("url", "")
                published = a.get("datetime")
                date_str = ""
                if published:
                    try:
                        date_str = parse_date(str(published)).strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        date_str = str(published)[:16]

                lines.append(f"[{date_str}] {headline}")
                lines.append(f"  Source: {source} | {url}")
                if summary:
                    lines.append(f"  Summary: {summary[:300]}")
                lines.append("")

        return "\n".join(lines)

    except Exception:
        return None


def _fetch_yfinance_news(symbol: str) -> str | None:
    """Secondary: yfinance news."""
    import yfinance as yf

    try:
        ticker = yf.Ticker(symbol.strip())
        info = ticker.get_info()
        raw_news = info.get("news", []) or []

        if not raw_news:
            return None

        lines = [
            f"=== Sentiment & News (yfinance): {symbol} ===",
            f"Articles: {len(raw_news[:8])}",
            "",
        ]
        for item in raw_news[:8]:
            title = item.get("title", "N/A")
            publisher = item.get("publisher", "")
            link = item.get("link", "")
            published = item.get("providerPublishTime", "")
            if published:
                try:
                    published = datetime.fromtimestamp(int(published), tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass

            lines.append(f"[{published}] {title}")
            if publisher:
                lines.append(f"  Publisher: {publisher}")
            if link:
                lines.append(f"  Link: {link}")
            lines.append("")

        return "\n".join(lines)

    except Exception:
        return None


def _fetch_web_news(symbol: str) -> str:
    """Tertiary: DuckDuckGo web search for news."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS  # pre-rename package

        results = []
        with DDGS() as ddgs:
            for item in ddgs.news(f"{symbol} stock news", max_results=6):
                results.append(item)

        if not results:
            return f"No news found for {symbol} via web search."

        lines = [
            f"=== Sentiment & News (Web Search): {symbol} ===",
            f"Articles: {len(results)}",
            "",
        ]
        for item in results:
            lines.append(
                f"- [{item.get('date', 'N/A')}] {item['title']}\n"
                f"  {item.get('body', '')[:250]}\n"
                f"  Source: {item.get('source', 'N/A')} | URL: {item.get('url', 'N/A')}"
            )
            lines.append("")

        return "\n".join(lines)

    except ImportError:
        return "Error: duckduckgo_search package not installed"
    except Exception:
        return f"No web news available for {symbol} (search temporarily unavailable)."


# ── Main tool ──────────────────────────────────────────────────

@tool
def fetch_sentiment_news(symbol: str, finnhub_api_key: str | None = None) -> str:
    """情绪与舆情 — News sentiment and alternative data for a ticker.

    Fetches financial news articles with headlines, summaries, categories, and sources.
    Articles are grouped by category for sentiment assessment.

    Primary: Finnhub API — structured financial news with categories (requires API key)
    Secondary: yfinance — ticker news from yfinance
    Tertiary: DuckDuckGo — general web news search

    Args:
        symbol: Ticker symbol (e.g. AAPL, TSLA, 00700.HK)
        finnhub_api_key: Optional Finnhub API key for primary news source
    """
    # Primary: Finnhub
    result = _fetch_finnhub(symbol, api_key=finnhub_api_key)
    if result:
        return result

    # Secondary: yfinance
    result = _fetch_yfinance_news(symbol)
    if result:
        return result

    # Tertiary: DuckDuckGo
    return _fetch_web_news(symbol)
