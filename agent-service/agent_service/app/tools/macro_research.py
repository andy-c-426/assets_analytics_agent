"""Tool 2/3: 宏观与研报 (Macro & Research Reports)

Primary: DuckDuckGo web search — macro news, sector trends, analyst reports
Secondary: yfinance sector/industry summary
"""

from langchain_core.tools import tool

from agent_service.app.tools.market_utils import detect_market


# ── Primary: Web search ──────────────────────────────────────────

def _search_macro(symbol: str) -> str:
    """Primary: DuckDuckGo search for macro/sector research."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS  # pre-rename package
    except ImportError:
        return "Error: ddgs package not installed"

    market = detect_market(symbol)

    lines = [
        f"=== Macro & Sector Research ({market['region']} / {market['index']}) ===",
        f"Market: {market['market']} | Currency: {market['currency']}",
        "",
    ]

    s = symbol.strip().upper()
    ticker_query = f"{s} stock sector industry news"

    all_queries = [ticker_query] + market["queries"]
    all_results = []
    try:
        with DDGS() as ddgs:
            for query in all_queries:
                try:
                    results = list(ddgs.news(query, max_results=2))
                except Exception:
                    results = []
                if results:
                    label = f"Ticker: \"{s}\"" if query == ticker_query else f"Macro: \"{query}\""
                    lines.append(f"--- {label} ---")
                    for item in results:
                        lines.append(
                            f"- [{item.get('date', 'N/A')}] {item['title']}\n"
                            f"  {item.get('body', '')[:250]}\n"
                            f"  Source: {item.get('source', 'N/A')}"
                        )
                    lines.append("")
                    all_results.extend(results)
    except Exception:
        pass

    if not all_results:
        lines.append("No macro/sector news found. The market outlook may be uncertain.")

    return "\n".join(lines)


# ── Secondary: yfinance sector context ───────────────────────────

def _fetch_sector_context(symbol: str) -> str:
    """Secondary: yfinance sector/industry classification with region-aware ETFs."""
    import yfinance as yf

    try:
        ticker = yf.Ticker(symbol.strip())
        info = ticker.get_info()

        if not info:
            return ""

        sector = info.get("sector", "")
        industry = info.get("industry", "")
        if not sector and not industry:
            return ""

        market = detect_market(symbol)
        currency_symbol = market["currency_symbol"]

        lines = [
            "",
            "=== Sector & Industry Context ===",
            f"Sector: {sector or 'N/A'}",
            f"Industry: {industry or 'N/A'}",
        ]

        # Region-aware sector index lookup
        sector_indices = market.get("sector_indices", {})
        if sector_indices:
            sector_lower = sector.lower()
            for key, etf in sector_indices.items():
                if key in sector_lower:
                    try:
                        etf_ticker = yf.Ticker(etf)
                        etf_info = etf_ticker.get_info()
                        etf_price = etf_info.get("currentPrice") or etf_info.get("regularMarketPrice")
                        if etf_price:
                            lines.append(f"{sector} Sector ETF ({etf}): {currency_symbol}{etf_price:.2f}")
                    except Exception:
                        pass
                    break

        return "\n".join(lines)
    except Exception:
        return ""


# ── Main tool ──────────────────────────────────────────────────

@tool
def fetch_macro_research(symbol: str) -> str:
    """宏观与研报 — Macroeconomic research and sector analysis for a ticker.

    Identifies the stock's market (US, HK, CN, JP, KR, TW, SG, AU, CA, UK, EU),
    then searches for macro trends, central bank policy, sector conditions, and
    ticker-specific industry news relevant to that market.

    Primary: Web search (DuckDuckGo) — macro news, sector trends, ticker news
    Secondary: yfinance — sector/industry classification and sector ETF performance

    Args:
        symbol: Ticker symbol (e.g. AAPL, 00700.HK, 300502.SZ, 7203.T, 005930.KS)
    """
    primary = _search_macro(symbol)
    secondary = _fetch_sector_context(symbol)
    return primary + secondary
