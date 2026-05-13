"""Tool 2/3: 宏观与研报 (Macro & Research Reports)

Primary: DuckDuckGo web search — macro news, sector trends, analyst reports
Secondary: yfinance sector/industry summary
Future: bigdata.com MCP API (requires API key)
"""

from datetime import datetime, timezone
from langchain_core.tools import tool


def _search_macro(symbol: str) -> str:
    """Primary: DuckDuckGo search for macro/sector research around a symbol."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS  # pre-rename package
    except ImportError:
        return "Error: ddgs package not installed"

    # Build macro-focused queries based on the symbol
    s = symbol.strip().upper()
    year = datetime.now(timezone.utc).year

    # Resolve market region
    if ".HK" in s or s.isdigit() and len(s) <= 5:
        region = "Hong Kong"
        index = "Hang Seng"
        macro_queries = [
            f"Hong Kong stock market outlook {year}",
            f"Hang Seng Index sector trends {year}",
            f"China economy policy impact {year}",
        ]
    elif ".SZ" in s or ".SH" in s or (s.isdigit() and len(s) == 6):
        region = "China A-share"
        index = "SSE/SZSE"
        macro_queries = [
            f"China A-share market outlook {year}",
            f"China economic policy {year}",
            f"China sector rotation {year}",
        ]
    elif ".T" in s or ".JP" in s:
        region = "Japan"
        index = "Nikkei 225"
        macro_queries = [
            f"Japan stock market outlook {year}",
            f"BOJ monetary policy {year}",
            f"Japan sector trends {year}",
        ]
    elif ".L" in s:
        region = "UK"
        index = "FTSE 100"
        macro_queries = [
            f"UK stock market outlook {year}",
            f"Bank of England interest rate {year}",
            f"FTSE sector performance {year}",
        ]
    else:
        region = "US"
        index = "S&P 500"
        macro_queries = [
            f"stock market outlook {year}",
            f"Federal Reserve interest rate policy {year}",
            f"sector rotation and market trends {year}",
        ]

    lines = [
        f"=== Macro & Sector Research ({region} / {index}) ===",
        "",
    ]

    all_results = []
    try:
        with DDGS() as ddgs:
            for query in macro_queries[:3]:
                try:
                    results = list(ddgs.news(query, max_results=3))
                except Exception:
                    results = []
                if results:
                    lines.append(f"--- Query: \"{query}\" ---")
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


def _fetch_sector_context(symbol: str) -> str:
    """Secondary: yfinance sector/industry context."""
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

        lines = [
            "",
            "=== Sector & Industry Context ===",
            f"Sector: {sector or 'N/A'}",
            f"Industry: {industry or 'N/A'}",
        ]

        # Try to get sector ETF performance
        sector_etf_map = {
            "technology": "XLK",
            "financial": "XLF",
            "healthcare": "XLV",
            "energy": "XLE",
            "consumer": "XLY",
            "industrial": "XLI",
            "real estate": "XLRE",
            "utilities": "XLU",
            "materials": "XLB",
            "communication": "XLC",
        }
        sector_lower = sector.lower()
        for key, etf in sector_etf_map.items():
            if key in sector_lower:
                try:
                    etf_ticker = yf.Ticker(etf)
                    etf_info = etf_ticker.get_info()
                    etf_price = etf_info.get("currentPrice") or etf_info.get("regularMarketPrice")
                    if etf_price:
                        lines.append(f"{sector} Sector ETF ({etf}): ${etf_price:.2f}")
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

    Searches for market-wide macro trends, central bank policy, sector rotation,
    and economic conditions relevant to the asset's market region.

    Primary: Web search (DuckDuckGo) — macro news, sector trends, policy updates
    Secondary: yfinance — sector/industry classification and sector ETF performance
    Future: bigdata.com API — structured financial research reports (requires API key)

    Args:
        symbol: Ticker symbol to research market context for (e.g. AAPL, 00700.HK)
    """
    primary = _search_macro(symbol)
    secondary = _fetch_sector_context(symbol)
    return primary + secondary
