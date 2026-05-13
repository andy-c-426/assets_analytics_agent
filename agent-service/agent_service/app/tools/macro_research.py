"""Tool 2/3: 宏观与研报 (Macro & Research Reports)

Primary: DuckDuckGo web search — macro news, sector trends, analyst reports
Secondary: yfinance sector/industry summary
"""

from datetime import datetime, timezone
from langchain_core.tools import tool


# ── Market detection ─────────────────────────────────────────────

def _detect_market(symbol: str) -> dict:
    """Identify the stock's market region, index, and currency from its symbol.

    Uses endswith() for precise suffix matching. Longer suffixes (e.g. .TW, .TO)
    are checked before shorter ones (e.g. .T) to prevent false matches.
    """
    s = symbol.strip().upper()
    year = datetime.now(timezone.utc).year

    # China A-Share: .SH/.SS (Shanghai) or .SZ (Shenzhen), or 6-digit numeric
    if s.endswith(".SZ") or s.endswith(".SH") or s.endswith(".SS") or (s.isdigit() and len(s) == 6):
        return {
            "region": "China A-Share",
            "market": "SSE/SZSE",
            "index": "SSE Composite / SZSE Component",
            "currency": "CNY",
            "queries": [
                f"China A-share market outlook {year}",
                "China economic policy stimulus 2026",
                "China sector rotation technology manufacturing",
            ],
        }

    # Hong Kong: .HK suffix, or 4-5 digit numeric (SEHK codes)
    if s.endswith(".HK") or (s.isdigit() and len(s) <= 5):
        return {
            "region": "Hong Kong",
            "market": "HKEX",
            "index": "Hang Seng Index (HSI)",
            "currency": "HKD",
            "queries": [
                f"Hong Kong stock market outlook {year}",
                "Hang Seng Index sector trends analysis",
                "China economic policy Greater Bay Area impact",
            ],
        }

    # Taiwan: .TW / .TWO — before .T (Tokyo) to avoid false match
    if s.endswith(".TW") or s.endswith(".TWO"):
        return {
            "region": "Taiwan",
            "market": "TWSE",
            "index": "TAIEX",
            "currency": "TWD",
            "queries": [
                f"Taiwan stock market outlook {year}",
                "Taiwan semiconductor foundry industry trends",
                "Taiwan central bank policy dollar",
            ],
        }

    # Canada: .TO / .V — before .T (Tokyo) to avoid false match
    if s.endswith(".TO") or s.endswith(".V"):
        return {
            "region": "Canada",
            "market": "TSX",
            "index": "S&P/TSX Composite",
            "currency": "CAD",
            "queries": [
                f"Canada stock market outlook {year}",
                "Bank of Canada interest rate policy",
                "TSX energy financial sector trends",
            ],
        }

    # Japan: .T (Tokyo) or .JP
    if s.endswith(".T") or s.endswith(".JP"):
        return {
            "region": "Japan",
            "market": "TSE",
            "index": "Nikkei 225",
            "currency": "JPY",
            "queries": [
                f"Japan stock market outlook {year}",
                "BOJ monetary policy interest rate yen",
                "Japan sector trends technology manufacturing",
            ],
        }

    # South Korea: .KS (KOSPI) or .KQ (KOSDAQ)
    if s.endswith(".KS") or s.endswith(".KQ"):
        return {
            "region": "South Korea",
            "market": "KRX",
            "index": "KOSPI / KOSDAQ",
            "currency": "KRW",
            "queries": [
                f"South Korea stock market outlook {year}",
                "Bank of Korea monetary policy won",
                "KOSPI technology semiconductor sector trends",
            ],
        }

    # Singapore: .SI
    if s.endswith(".SI"):
        return {
            "region": "Singapore",
            "market": "SGX",
            "index": "Straits Times Index (STI)",
            "currency": "SGD",
            "queries": [
                f"Singapore stock market outlook {year}",
                "Singapore economy MAS monetary policy",
                "ASEAN market trends analysis",
            ],
        }

    # Australia: .AX
    if s.endswith(".AX"):
        return {
            "region": "Australia",
            "market": "ASX",
            "index": "ASX 200",
            "currency": "AUD",
            "queries": [
                f"Australia stock market outlook {year}",
                "RBA interest rate policy Australian dollar",
                "ASX mining resources sector trends",
            ],
        }

    # UK: .L (London Stock Exchange)
    if s.endswith(".L"):
        return {
            "region": "United Kingdom",
            "market": "LSE",
            "index": "FTSE 100",
            "currency": "GBP",
            "queries": [
                f"UK stock market outlook {year}",
                "Bank of England interest rate monetary policy",
                "FTSE 100 sector performance analysis",
            ],
        }

    # Europe (.DE, .PA, .AS, .MI, .MC, .SW, .F, .BE, .VI, .LS, .ST, .CO, .HE)
    eu_suffixes = [".DE", ".PA", ".AS", ".BR", ".MI", ".MC", ".SW",
                   ".F", ".BE", ".VI", ".LS", ".ST", ".CO", ".HE"]
    if any(s.endswith(sfx) for sfx in eu_suffixes):
        if s.endswith(".DE"):
            country = "Germany"; index_name = "DAX"; cb = "ECB"
        elif s.endswith(".PA"):
            country = "France"; index_name = "CAC 40"; cb = "ECB"
        elif s.endswith(".MI"):
            country = "Italy"; index_name = "FTSE MIB"; cb = "ECB"
        elif s.endswith(".MC"):
            country = "Spain"; index_name = "IBEX 35"; cb = "ECB"
        elif s.endswith(".AS"):
            country = "Netherlands"; index_name = "AEX"; cb = "ECB"
        elif s.endswith(".SW"):
            country = "Switzerland"; index_name = "SMI"; cb = "SNB"
        else:
            country = "Europe"; index_name = "STOXX 600"; cb = "ECB"

        return {
            "region": country,
            "market": "Euronext" if country != "Switzerland" else "SIX",
            "index": index_name,
            "currency": "EUR" if country != "Switzerland" else "CHF",
            "queries": [
                f"European stock market outlook {year}",
                f"{cb} monetary policy interest rate decision",
                "European sector trends market analysis",
            ],
        }

    # Default: US market (NASDAQ / NYSE)
    return {
        "region": "United States",
        "market": "NASDAQ / NYSE",
        "index": "S&P 500",
        "currency": "USD",
        "queries": [
            f"stock market outlook {year}",
            "Federal Reserve interest rate monetary policy 2026",
            "sector rotation and market trends analysis",
        ],
    }


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

    market = _detect_market(symbol)

    lines = [
        f"=== Macro & Sector Research ({market['region']} / {market['index']}) ===",
        f"Market: {market['market']} | Currency: {market['currency']}",
        "",
    ]

    # Ticker-specific sector query + macro queries
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
    """Secondary: yfinance sector/industry classification."""
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
