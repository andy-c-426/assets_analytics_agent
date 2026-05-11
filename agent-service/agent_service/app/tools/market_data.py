"""Tool 1/3: 市场基础数据 (Structured Market Data)

Primary: Futu OpenD — real-time price, volume, valuation, fundamentals, 52W range
Secondary: yfinance — delayed but comprehensive profile, metrics, index data
"""

from langchain_core.tools import tool


# ── Futu helpers (reused from futu_data.py) ─────────────────────

def _resolve_futu_codes(symbol: str) -> list[str]:
    s = symbol.strip().upper()
    if "." in s:
        return [s]
    _known = {
        "AAPL": "US", "MSFT": "US", "GOOGL": "US", "AMZN": "US", "TSLA": "US",
        "META": "US", "NVDA": "US", "NFLX": "US", "BRK.A": "US", "BRK.B": "US",
        "JPM": "US", "V": "US", "WMT": "US", "JNJ": "US", "PG": "US", "XOM": "US",
        "BAC": "US", "MA": "US", "DIS": "US", "ADBE": "US", "CRM": "US",
        "00700": "HK", "09988": "HK", "09618": "HK", "03690": "HK",
        "00388": "HK", "02318": "HK", "00005": "HK", "00941": "HK",
        "01810": "HK", "01398": "HK", "03988": "HK", "01299": "HK",
    }
    if s in _known:
        return [f"{_known[s]}.{s}"]
    stripped = s.lstrip("0") or "0"
    return [f"US.{s}", f"HK.{stripped}"]


def _try_futu(symbol: str) -> str | None:
    """Try Futu OpenD for real-time data. Returns result string or None."""
    try:
        from futu import OpenQuoteContext
        ctx = OpenQuoteContext(host="127.0.0.1", port=11111)
    except ImportError:
        return None
    except Exception:
        return None

    try:
        codes = _resolve_futu_codes(symbol)
        snapshot_text = None

        for code in codes:
            ret, data = ctx.get_market_snapshot([code])
            if ret == 0 and data is not None and not data.empty:
                snapshot_text = _format_snapshot(code, data.iloc[0])
                break

        if snapshot_text is None:
            ctx.close()
            return None

        parts = [snapshot_text]

        market_str = codes[0].split(".")[0] if snapshot_text else ""
        from futu import Market
        market_map = {
            "US": Market.US, "HK": Market.HK, "SH": Market.SH, "SZ": Market.SZ,
            "JP": Market.JP, "SG": Market.SG, "AU": Market.AU, "MY": Market.MY,
            "CA": Market.CA,
        }
        futu_market = market_map.get(market_str)
        if futu_market is not None:
            ret, info = ctx.get_stock_basicinfo(futu_market, code_list=[codes[0]])
            if ret == 0 and info is not None and not info.empty:
                parts.append(_format_basicinfo(codes[0], info.iloc[0]))

        ctx.close()
        return "\n\n".join(parts)
    except Exception:
        try:
            ctx.close()
        except Exception:
            pass
        return None


def _format_snapshot(code: str, row) -> str:
    import pandas as pd

    def _vf(key):
        val = row.get(key)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def _vs(key):
        val = row.get(key)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        return str(val)

    name = _vs("name") or code
    update = _vs("update_time")
    lines = [f"=== Futu Real-Time Data: {name} ({code}) ==="]
    if update:
        lines.append(f"As of: {update}")

    last = _vf("last_price")
    prev = _vf("prev_close_price")
    change = last - prev if (last is not None and prev is not None) else None
    change_pct = (change / prev * 100) if (change is not None and prev and prev != 0) else None

    lines.append("\n[Price]")
    if last is not None:
        sign = ""
        if change is not None and change_pct is not None:
            sign = "+" if change >= 0 else ""
            lines.append(f"Current: {last:.2f}  Change: {sign}{change:.2f} ({sign}{change_pct:.2f}%)")
        else:
            lines.append(f"Current: {last:.2f}")
    for f, label in [("open_price", "Open"), ("high_price", "High"), ("low_price", "Low"),
                      ("prev_close_price", "Prev Close")]:
        val = _vf(f)
        if val is not None:
            lines.append(f"{label}: {val:.2f}")

    lines.append("\n[Volume]")
    for f, label in [("volume", "Volume"), ("turnover", "Turnover"), ("turnover_rate", "Turnover Rate (%)"),
                      ("volume_ratio", "Volume Ratio")]:
        val = _vf(f)
        if val is not None:
            fmt = f"{val:.3f}" if f == "turnover_rate" else f"{val:,.0f}"
            lines.append(f"{label}: {fmt}")

    lines.append("\n[Valuation]")
    for f, label in [("pe_ratio", "P/E"), ("pe_ttm_ratio", "P/E TTM"), ("pb_ratio", "P/B"),
                      ("total_market_val", "Market Cap"), ("ey_ratio", "Earnings Yield (%)")]:
        val = _vf(f)
        if val is not None:
            fmt = _fmt_big(val) if "market" in f.lower() else f"{val:.2f}"
            lines.append(f"{label}: {fmt}")

    lines.append("\n[Fundamentals]")
    for f, label in [("earning_per_share", "EPS"), ("net_asset_per_share", "Book Value/Share"),
                      ("dividend_ttm", "Dividend TTM"), ("dividend_ratio_ttm", "Dividend Yield (%)"),
                      ("issued_shares", "Issued Shares")]:
        val = _vf(f)
        if val is not None:
            fmt = f"{val:,.0f}" if f == "issued_shares" else f"{val:.2f}"
            lines.append(f"{label}: {fmt}")

    high52 = _vf("highest52weeks_price")
    low52 = _vf("lowest52weeks_price")
    if high52 or low52:
        lines.append("\n[52-Week Range]")
        if high52 is not None:
            lines.append(f"High: {high52:.2f}")
        if low52 is not None:
            lines.append(f"Low: {low52:.2f}")

    return "\n".join(lines)


def _format_basicinfo(code: str, row) -> str:
    import pandas as pd

    def _v(key):
        val = row.get(key)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        return val

    name = _v("name") or code
    lines = [f"=== Stock Info: {name} ({code}) ==="]
    for f, label in [("stock_type", "Type"), ("exchange_type", "Exchange"),
                      ("listing_date", "Listed"), ("lot_size", "Lot Size")]:
        val = _v(f)
        if val is not None:
            lines.append(f"{label}: {val}")
    return "\n".join(lines)


def _fmt_big(n: float) -> str:
    if abs(n) >= 1e12:
        return f"${n / 1e12:.2f}T"
    if abs(n) >= 1e9:
        return f"${n / 1e9:.2f}B"
    if abs(n) >= 1e6:
        return f"${n / 1e6:.2f}M"
    return f"${n:,.0f}"


# ── yfinance fallback ──────────────────────────────────────────

def _fetch_yfinance_market_data(symbol: str) -> str:
    """Fallback: yfinance for profile, price, metrics + relevant index data."""
    import yfinance as yf

    try:
        ticker = yf.Ticker(symbol.strip())
        info = ticker.get_info()

        if not info or info.get("symbol") is None:
            return f"No data found for symbol: {symbol}"

        name = info.get("shortName") or info.get("longName") or symbol
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")
        country = info.get("country", "N/A")
        market_cap = info.get("marketCap")
        description = info.get("longBusinessSummary", "")
        if description:
            sentences = description.replace("\n", " ").split(". ")
            description = ". ".join(sentences[:2]) + "."

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        currency = info.get("currency", "USD")
        change = info.get("regularMarketChange")
        change_pct = info.get("regularMarketChangePercent")

        pe = info.get("trailingPE")
        pb = info.get("priceToBook")
        eps = info.get("trailingEps")
        dividend_yield = info.get("dividendYield")
        beta = info.get("beta")
        high_52w = info.get("fiftyTwoWeekHigh")
        low_52w = info.get("fiftyTwoWeekLow")

        lines = [
            f"=== yfinance Market Data: {name} ({symbol}) ===",
            f"(Note: yfinance data may be delayed. Futu OpenD was unavailable.)",
            "",
            f"Sector: {sector} | Industry: {industry} | Country: {country}",
            f"Market Cap: {_fmt_big(market_cap)}" if market_cap else "Market Cap: N/A",
            "",
            f"Current Price: {current_price} {currency}" if current_price else "Price: N/A",
        ]
        if change is not None and change_pct is not None:
            sign = "+" if change >= 0 else ""
            lines.append(f"Change: {sign}{change:.2f} ({sign}{change_pct:.2f}%)")

        lines.append("\n[Key Metrics]")
        lines.append(f"P/E: {pe:.2f}" if pe else "P/E: N/A")
        lines.append(f"P/B: {pb:.2f}" if pb else "P/B: N/A")
        lines.append(f"EPS: ${eps:.2f}" if eps else "EPS: N/A")
        lines.append(f"Dividend Yield: {dividend_yield * 100:.2f}%" if dividend_yield else "Dividend Yield: N/A")
        lines.append(f"Beta: {beta:.2f}" if beta else "Beta: N/A")
        lines.append(f"52W High: ${high_52w:.2f}" if high_52w else "52W High: N/A")
        lines.append(f"52W Low: ${low_52w:.2f}" if low_52w else "52W Low: N/A")

        if description:
            lines.append(f"\n{description}")

        # Fetch a relevant market index for context
        market = info.get("market", "").lower()
        exchange = info.get("exchange", "").lower()
        index_symbol = _pick_index(market, exchange, country)
        if index_symbol:
            try:
                idx_ticker = yf.Ticker(index_symbol)
                idx_info = idx_ticker.get_info()
                idx_price = idx_info.get("currentPrice") or idx_info.get("regularMarketPrice")
                idx_change = idx_info.get("regularMarketChangePercent")
                if idx_price:
                    idx_line = f"\n[Market Index: {index_symbol} = {idx_price:.2f}"
                    if idx_change is not None:
                        sign = "+" if idx_change >= 0 else ""
                        idx_line += f" ({sign}{idx_change:.2f}%)"
                    idx_line += "]"
                    lines.append(idx_line)
            except Exception:
                pass

        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching market data for {symbol}: {e}"


def _pick_index(market: str, exchange: str, country: str) -> str | None:
    idx_map = {
        "hk": "^HSI",
        "cn": "^SSEC",
        "jp": "^N225",
        "gb": "^FTSE",
        "uk": "^FTSE",
        "de": "^GDAXI",
        "fr": "^FCHI",
        "ca": "^GSPTSE",
        "au": "^AXJO",
        "sg": "^STI",
        "kr": "^KS11",
        "tw": "^TWII",
        "in": "^BSESN",
        "br": "^BVSP",
        "us": "^GSPC",
    }
    market_lower = market.lower()
    exchange_lower = exchange.lower()

    if "nasdaq" in exchange_lower:
        return "^IXIC"
    for key, idx in idx_map.items():
        if key in market_lower or key in exchange_lower or key in country.lower():
            return idx
    return "^GSPC"


# ── Main tool ──────────────────────────────────────────────────

@tool
def fetch_market_data(symbol: str) -> str:
    """市场基础数据 — Structured market data for a ticker.

    Fetches price, volume, valuation, fundamentals, and 52-week range data.
    Also includes a relevant market index for context (S&P 500, Hang Seng, etc.)

    Primary: Futu OpenD (real-time snapshots + basic info)
    Secondary: yfinance (delayed but comprehensive profile, metrics, index data)

    Args:
        symbol: Ticker symbol (e.g. AAPL, 0700.HK, 300502.SZ)
    """
    # Primary: Futu OpenD
    futu_result = _try_futu(symbol)
    if futu_result:
        return futu_result

    # Secondary: yfinance
    return _fetch_yfinance_market_data(symbol)
