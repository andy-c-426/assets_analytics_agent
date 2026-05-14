from langchain_core.tools import tool

from agent_service.app.tools.market_utils import detect_market


def _resolve_futu_codes(symbol: str) -> list[str]:
    """Convert a ticker into candidate Futu codes to try (MARKET.CODE format)."""
    s = symbol.strip().upper()

    # Already in Futu format (US.AAPL, HK.00700)
    if "." in s:
        return [s]

    market = detect_market(symbol)
    prefixes = market.get("futu_prefixes", ["US", "HK"])

    stripped = s.lstrip("0") or "0"
    return [f"{p}.{stripped}" for p in prefixes]


def _get_quote_context():
    """Try to connect to running Futu OpenD."""
    try:
        from futu import OpenQuoteContext
        ctx = OpenQuoteContext(host="127.0.0.1", port=11111)
        return ctx, None
    except ImportError:
        return None, "futu-api package not installed"
    except Exception as e:
        return None, f"Cannot connect to Futu OpenD: {e}"


def _snapshot_to_text(code: str, row) -> str:
    """Convert a single market snapshot row into readable multi-section text."""
    import pandas as pd

    def _v(key):
        val = row.get(key)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        return val

    def _vf(key):
        """Get a value as float (or None). Handles string→float conversion."""
        val = _v(key)
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    # Derive currency symbol from Futu code prefix
    prefix = code.split(".")[0] if "." in code else ""
    currency_map = {
        "US": "$", "HK": "HK$", "SH": "¥", "SZ": "¥",
        "JP": "¥", "KR": "₩", "TW": "NT$", "SG": "S$",
        "AU": "A$", "CA": "C$", "UK": "£",
    }
    currency_symbol = currency_map.get(prefix, "$")

    name = _v("name") or code
    update = _v("update_time")

    lines = [f"Futu Market Snapshot: {name} ({code})"]
    if update:
        lines.append(f"Data as of: {update}")

    # Price section
    last = _vf("last_price")
    prev = _vf("prev_close_price")
    change = last - prev if (last is not None and prev is not None) else None
    change_pct = (change / prev * 100) if (change is not None and prev and prev != 0) else None

    lines.append("")
    lines.append("Price:")
    if last is not None:
        change_str = ""
        if change is not None and change_pct is not None:
            sign = "+" if change >= 0 else ""
            change_str = f"  (Change: {sign}{change:.2f} / {sign}{change_pct:.2f}%)"
        lines.append(f"  Current: {last:.2f}{change_str}")
    for f, label in [("open_price", "Open"), ("high_price", "High"), ("low_price", "Low"),
                      ("prev_close_price", "Prev Close")]:
        val = _vf(f)
        if val is not None:
            lines.append(f"  {label}: {val:.2f}")

    # Extended hours
    pre = _vf("pre_price")
    after = _vf("after_price")
    if pre or after:
        lines.append("")
        lines.append("Extended Hours:")
        if pre is not None:
            pre_chg = _vf("pre_change_rate")
            chg_str = f" ({pre_chg:+.2f}%)" if pre_chg is not None else ""
            lines.append(f"  Pre-Market: {pre:.2f}{chg_str}")
        if after is not None:
            after_chg = _vf("after_change_rate")
            chg_str = f" ({after_chg:+.2f}%)" if after_chg is not None else ""
            lines.append(f"  After-Hours: {after:.2f}{chg_str}")

    # Volume
    lines.append("")
    lines.append("Volume:")
    for f, label in [("volume", "Volume"), ("turnover", "Turnover"), ("turnover_rate", "Turnover Rate"),
                      ("volume_ratio", "Volume Ratio"), ("avg_price", "VWAP")]:
        val = _vf(f)
        if val is not None:
            if f == "turnover_rate":
                lines.append(f"  {label}: {val:.3f}%")
            elif f in ("volume_ratio", "avg_price"):
                lines.append(f"  {label}: {val:.2f}")
            else:
                lines.append(f"  {label}: {val:,.0f}")

    # Valuation
    lines.append("")
    lines.append("Valuation:")
    for f, label in [("pe_ratio", "P/E"), ("pe_ttm_ratio", "P/E (TTM)"), ("pb_ratio", "P/B"),
                      ("ey_ratio", "Earnings Yield (%)"), ("total_market_val", "Market Cap"),
                      ("circular_market_val", "Circular Market Cap")]:
        val = _vf(f)
        if val is not None:
            if "market" in f.lower():
                lines.append(f"  {label}: {_fmt_big(val, currency_symbol)}")
            elif "ey" in f:
                lines.append(f"  {label}: {val:.2f}%")
            else:
                lines.append(f"  {label}: {val:.2f}")

    # Fundamentals
    lines.append("")
    lines.append("Fundamentals:")
    for f, label in [("earning_per_share", "EPS"), ("net_asset_per_share", "Book Value/Share"),
                      ("dividend_ttm", "Dividend TTM"), ("dividend_ratio_ttm", "Dividend Yield TTM (%)"),
                      ("issued_shares", "Issued Shares"), ("net_profit", "Net Profit"),
                      ("net_asset", "Net Asset")]:
        val = _vf(f)
        if val is not None:
            if f == "dividend_ratio_ttm":
                lines.append(f"  {label}: {val:.2f}%")
            elif f in ("net_profit", "net_asset"):
                lines.append(f"  {label}: {_fmt_big(val, currency_symbol)}")
            elif f == "issued_shares":
                lines.append(f"  {label}: {val:,.0f}")
            else:
                lines.append(f"  {label}: {val:.2f}")

    # Range
    high52 = _vf("highest52weeks_price")
    low52 = _vf("lowest52weeks_price")
    amp = _vf("amplitude")
    if high52 or low52:
        lines.append("")
        lines.append("Price Range:")
        if high52 is not None:
            lines.append(f"  52W High: {high52:.2f}")
        if low52 is not None:
            lines.append(f"  52W Low: {low52:.2f}")
        if amp is not None:
            lines.append(f"  Day Amplitude: {amp:.3f}%")

    # Status (text fields)
    status = _v("sec_status")
    lot = _vf("lot_size")
    listing = _v("listing_date")
    if status:
        lines.append("")
        lines.append(f"Status: {status}")
    if lot is not None:
        lines.append(f"Lot Size: {int(lot)}")
    if listing:
        lines.append(f"Listed: {listing}")

    return "\n".join(lines)


def _basicinfo_to_text(code: str, row) -> str:
    """Convert stock basic info row into readable text."""
    import pandas as pd

    def _v(key):
        val = row.get(key)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        return val

    name = _v("name") or code
    lines = [f"Futu Stock Info: {name} ({code})"]
    for f, label in [("stock_type", "Type"), ("exchange_type", "Exchange"),
                      ("stock_id", "Stock ID"), ("listing_date", "Listed")]:
        val = _v(f)
        if val is not None:
            lines.append(f"  {label}: {val}")
    lot = _v("lot_size")
    if lot is not None:
        try:
            lines.append(f"  Lot Size: {int(lot)}")
        except (ValueError, TypeError):
            lines.append(f"  Lot Size: {lot}")
    delisted = _v("delisting")
    if delisted is not None:
        lines.append(f"  Delisted: {delisted}")

    return "\n".join(lines)


def _fmt_big(n: float, currency_symbol: str = "$") -> str:
    if abs(n) >= 1e12:
        return f"{currency_symbol}{n / 1e12:.2f}T"
    if abs(n) >= 1e9:
        return f"{currency_symbol}{n / 1e9:.2f}B"
    if abs(n) >= 1e6:
        return f"{currency_symbol}{n / 1e6:.2f}M"
    return f"{currency_symbol}{n:,.0f}"


@tool
def fetch_futu_data(symbol: str) -> str:
    """Fetch real-time stock/ETF data from Futu OpenD (primary) with yfinance fallback.

    Use this for richer real-time market data including market snapshots (price,
    volume, valuation, fundamentals, 52W range) and basic stock information.
    Automatically falls back to yfinance if Futu OpenD is not running.

    Args:
        symbol: Ticker symbol (e.g. AAPL, 00700.HK, US.AAPL, 300502.SZ)
    """
    ctx, err = _get_quote_context()
    if ctx is None:
        from agent_service.app.tools.yfinance_tools import fetch_asset_data
        return (
            f"Note: Futu OpenD unavailable ({err}), falling back to yfinance.\n\n"
            + fetch_asset_data.invoke({"symbol": symbol})
        )

    try:
        codes = _resolve_futu_codes(symbol)
        results: list[str] = []
        snapshot_code = None

        for code in codes:
            ret, data = ctx.get_market_snapshot([code])
            if ret == 0 and data is not None and not data.empty:
                results.append(_snapshot_to_text(code, data.iloc[0]))
                snapshot_code = code
                break

        if snapshot_code is None:
            ctx.close()
            from agent_service.app.tools.yfinance_tools import fetch_asset_data
            return (
                f"Note: Futu returned no data for {symbol} (tried {codes}), "
                f"falling back to yfinance.\n\n"
                + fetch_asset_data.invoke({"symbol": symbol})
            )

        # Basic info via stock_basicinfo
        market_str = snapshot_code.split(".")[0]
        from futu import Market
        market_map = {
            "US": Market.US, "HK": Market.HK, "SH": Market.SH, "SZ": Market.SZ,
            "JP": Market.JP, "SG": Market.SG, "AU": Market.AU, "MY": Market.MY,
            "CA": Market.CA,
        }
        futu_market = market_map.get(market_str)

        if futu_market is not None:
            ret, info = ctx.get_stock_basicinfo(futu_market, code_list=[snapshot_code])
            if ret == 0 and info is not None and not info.empty:
                results.append(_basicinfo_to_text(snapshot_code, info.iloc[0]))

        ctx.close()
        return "\n\n".join(results)

    except Exception as e:
        try:
            ctx.close()
        except Exception:
            pass
        from agent_service.app.tools.yfinance_tools import fetch_asset_data
        return (
            f"Note: Futu API error ({e}), falling back to yfinance.\n\n"
            + fetch_asset_data.invoke({"symbol": symbol})
        )
