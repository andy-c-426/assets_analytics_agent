"""Shared market detection utility.

Used by all tools that need market-aware behavior: Futu code resolution,
currency formatting, sector ETF lookup, P/E threshold calibration, and
market-aware news queries.
"""

from datetime import datetime, timezone


def detect_market(symbol: str) -> dict:
    """Identify the stock's market region, exchange, currency, and metadata.

    Returns a dict with keys:
        region, market, index, currency (ISO), currency_symbol, queries,
        futu_prefixes, sector_indices, pe_thresholds
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
            "currency_symbol": "¥",
            "futu_prefixes": ["SH", "SZ", "HK", "US"],
            "sector_indices": {},
            "pe_thresholds": {"low": 15, "mid": 30, "high": 50},
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
            "currency_symbol": "HK$",
            "futu_prefixes": ["HK", "US"],
            "sector_indices": {},
            "pe_thresholds": {"low": 10, "mid": 18, "high": 30},
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
            "currency_symbol": "NT$",
            "futu_prefixes": ["TW", "US"],
            "sector_indices": {},
            "pe_thresholds": {"low": 12, "mid": 20, "high": 30},
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
            "currency_symbol": "C$",
            "futu_prefixes": ["CA", "US"],
            "sector_indices": {},
            "pe_thresholds": {"low": 12, "mid": 22, "high": 35},
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
            "currency_symbol": "¥",
            "futu_prefixes": ["JP", "US"],
            "sector_indices": {},
            "pe_thresholds": {"low": 12, "mid": 20, "high": 30},
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
            "currency_symbol": "₩",
            "futu_prefixes": ["KR", "US"],
            "sector_indices": {},
            "pe_thresholds": {"low": 10, "mid": 18, "high": 28},
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
            "currency_symbol": "S$",
            "futu_prefixes": ["SG", "US"],
            "sector_indices": {},
            "pe_thresholds": {"low": 12, "mid": 20, "high": 30},
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
            "currency_symbol": "A$",
            "futu_prefixes": ["AU", "US"],
            "sector_indices": {},
            "pe_thresholds": {"low": 12, "mid": 22, "high": 35},
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
            "currency_symbol": "£",
            "futu_prefixes": ["UK", "US"],
            "sector_indices": {},
            "pe_thresholds": {"low": 12, "mid": 20, "high": 30},
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
            prefix = "DE"; sym = "€"
        elif s.endswith(".PA"):
            country = "France"; index_name = "CAC 40"; cb = "ECB"
            prefix = "PA"; sym = "€"
        elif s.endswith(".MI"):
            country = "Italy"; index_name = "FTSE MIB"; cb = "ECB"
            prefix = "MI"; sym = "€"
        elif s.endswith(".MC"):
            country = "Spain"; index_name = "IBEX 35"; cb = "ECB"
            prefix = "MC"; sym = "€"
        elif s.endswith(".AS"):
            country = "Netherlands"; index_name = "AEX"; cb = "ECB"
            prefix = "AS"; sym = "€"
        elif s.endswith(".SW"):
            country = "Switzerland"; index_name = "SMI"; cb = "SNB"
            prefix = "SW"; sym = "CHF"
        else:
            country = "Europe"; index_name = "STOXX 600"; cb = "ECB"
            prefix = "US"; sym = "€"

        return {
            "region": country,
            "market": "Euronext" if country != "Switzerland" else "SIX",
            "index": index_name,
            "currency": "EUR" if country != "Switzerland" else "CHF",
            "currency_symbol": sym,
            "futu_prefixes": [prefix, "US"],
            "sector_indices": {},
            "pe_thresholds": {"low": 12, "mid": 20, "high": 30},
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
        "currency_symbol": "$",
        "futu_prefixes": ["US", "HK"],
        "sector_indices": {
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
        },
        "pe_thresholds": {"low": 15, "mid": 25, "high": 40},
        "queries": [
            f"stock market outlook {year}",
            "Federal Reserve interest rate monetary policy 2026",
            "sector rotation and market trends analysis",
        ],
    }
