"""Supplementary tools for China A-Share & Hong Kong markets.

Uses AKShare for capital flow (北向/南向资金), sector fund flow, Dragon Tiger
Board (龙虎榜), and market breadth data specific to CN/HK markets.
"""

from datetime import datetime, timezone

from langchain_core.tools import tool

from agent_service.app.tools.market_utils import detect_market


def _is_cn_or_hk(symbol: str) -> bool:
    """Check if symbol belongs to China A-Share or Hong Kong market."""
    market = detect_market(symbol)
    return market["region"] in ("China A-Share", "Hong Kong")


def _try_akshare():
    """Import akshare or raise a clean error."""
    try:
        import akshare as ak
        return ak
    except ImportError:
        raise ImportError("akshare package not installed. Run: pip install akshare")


# ── Capital Flow Tool ───────────────────────────────────────────

def _fetch_stock_connect_flow(ak) -> str | None:
    """Fetch daily Stock Connect northbound/southbound flow summary."""
    try:
        df = ak.stock_hsgt_fund_flow_summary_em()
        if df is None or df.empty:
            return None

        # Get today's rows
        today_rows = df[df["交易日"].str.contains(datetime.now(timezone.utc).strftime("%Y-%m-%d"), na=False)]
        if today_rows.empty:
            today_rows = df.tail(4)  # fallback: last 4 rows (沪港通 + 深港通)

        lines = ["--- Stock Connect Flow (沪深港通) ---"]
        for _, row in today_rows.iterrows():
            direction = row.get("资金方向", "")
            board = row.get("板块", "")
            net_buy = row.get("成交净买额", 0)
            net_flow = row.get("资金净流入", 0)
            up = row.get("上涨数", 0)
            flat = row.get("持平数", 0)
            down = row.get("下跌数", 0)
            index_name = row.get("相关指数", "")
            index_chg = row.get("指数涨跌幅", 0)

            direction_label = "Northbound (北向)" if "北" in str(direction) else "Southbound (南向)" if "南" in str(direction) else direction
            parts = [f"{board} — {direction_label}"]
            if net_buy and float(net_buy) != 0:
                sign = "+" if float(net_buy) >= 0 else ""
                parts.append(f"Net Buy: {sign}{net_buy:.2f} 亿元")
            if net_flow and float(net_flow) != 0:
                parts.append(f"Net Flow: {net_flow:.2f} 亿元")
            parts.append(f"Advances/Declines: {int(up)}/{int(down)} ({int(flat)} flat)")
            if index_name:
                sign = "+" if float(index_chg) >= 0 else ""
                parts.append(f"{index_name}: {sign}{float(index_chg):.2f}%")
            lines.append(", ".join(parts))

        return "\n".join(lines)
    except Exception:
        return None


def _fetch_stock_holdings(ak, symbol: str) -> str | None:
    """Fetch Stock Connect holdings for an individual stock."""
    try:
        # Try with the raw symbol first (without suffix for A-shares, with suffix for HK)
        s = symbol.strip().upper()
        market = detect_market(symbol)
        region = market["region"]

        # For HK stocks, use the numeric code part
        if region == "Hong Kong":
            code = s.replace(".HK", "")
        elif region == "China A-Share":
            code = s.replace(".SZ", "").replace(".SH", "").replace(".SS", "")
        else:
            return None

        # AKShare uses different lookup for SH/SZ — try both
        import re
        if re.match(r"^\d{6}$", code):
            # For A-shares, try the stock code directly
            df = ak.stock_hsgt_individual_em(symbol=code)
        else:
            # For HK stocks, try with the full code
            df = ak.stock_hsgt_individual_em(symbol=code)

        if df is None or df.empty:
            return None

        latest = df.iloc[-1]
        recent = df.tail(5)

        lines = [
            "",
            f"--- Stock Connect Holdings: {code} ---",
            f"Latest: {latest.get('持股日期', 'N/A')}",
            f"Close: {latest.get('当日收盘价', 'N/A')} | Change: {latest.get('当日涨跌幅', 'N/A')}%",
            f"Holdings: {latest.get('持股数量', 'N/A'):,.0f} shares | Value: {latest.get('持股市值', 'N/A')/1e8:.2f} 亿元",
            f"Holding %: {latest.get('持股数量占A股百分比', 'N/A')}%",
        ]

        # Recent trend
        if len(recent) >= 2:
            chg_1d = recent.iloc[-1].get("持股市值变化-1日", 0)
            chg_5d = recent.iloc[-1].get("持股市值变化-5日", 0)
            if chg_1d:
                lines.append(f"Holding Value Chg (1d): {chg_1d/1e8:+.2f} 亿元")
            if chg_5d:
                lines.append(f"Holding Value Chg (5d): {chg_5d/1e8:+.2f} 亿元")

        return "\n".join(lines)
    except Exception:
        return None


@tool
def fetch_capital_flow(symbol: str) -> str:
    """沪深港通资金流向 — Stock Connect capital flow and holdings data.

    Fetches northbound (foreign into A-share) and southbound (mainland into HK)
    capital flow summaries, plus individual stock Stock Connect holdings.

    Only works for China A-Share (.SZ/.SH/.SS) and Hong Kong (.HK) tickers.

    Args:
        symbol: Ticker symbol (e.g. 600519.SS, 00700.HK)
    """
    if not _is_cn_or_hk(symbol):
        return f"Capital flow data not applicable for {symbol} (CN/HK markets only)."

    try:
        ak = _try_akshare()
    except ImportError as e:
        return f"Error: {e}"

    sections = [
        f"=== Capital Flow & Stock Connect: {symbol} ===",
    ]

    # Stock Connect daily flow
    flow_section = _fetch_stock_connect_flow(ak)
    if flow_section:
        sections.append(flow_section)

    # Individual stock holdings
    holdings_section = _fetch_stock_holdings(ak, symbol)
    if holdings_section:
        sections.append(holdings_section)

    if len(sections) <= 1:
        sections.append("No Stock Connect data available (may be outside trading hours).")

    return "\n".join(sections)


# ── Market Sentiment Tool ────────────────────────────────────────

def _fetch_sector_flow(ak) -> str | None:
    """Fetch sector/industry fund flow ranking. Falls back gracefully."""
    try:
        # Try East Money endpoint (may be blocked outside China)
        df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流向")
        if df is not None and not df.empty:
            top_in = df.nlargest(5, "今日主力净流入-净额")
            top_out = df.nsmallest(5, "今日主力净流入-净额")

            lines = ["--- Sector Fund Flow (行业资金流向) ---"]
            lines.append("Top 5 Inflows (主力净流入):")
            for _, row in top_in.iterrows():
                name = row.get("名称", "N/A")
                net = row.get("今日主力净流入-净额", 0) / 1e8
                pct = row.get("今日主力净流入-净占比", 0)
                lines.append(f"  {name}: +{net:.2f} 亿元 ({pct:.1f}%)")

            lines.append("Top 5 Outflows (主力净流出):")
            for _, row in top_out.iterrows():
                name = row.get("名称", "N/A")
                net = row.get("今日主力净流入-净额", 0) / 1e8
                pct = row.get("今日主力净流入-净占比", 0)
                lines.append(f"  {name}: {net:.2f} 亿元 ({pct:.1f}%)")

            return "\n".join(lines)
    except Exception:
        pass
    return None


def _fetch_dragon_tiger(ak, symbol: str) -> str | None:
    """Fetch Dragon Tiger Board (龙虎榜) data for a specific stock.

    Uses Sina source (more reliable cross-network), falls back to East Money.
    """
    try:
        s = symbol.strip().upper()
        code = s.replace(".SZ", "").replace(".SH", "").replace(".SS", "").replace(".HK", "")

        lines = [f"--- Dragon Tiger Board (龙虎榜): {s} ---"]

        # Primary: Sina LHB aggregate — filter for this stock
        try:
            df_all = ak.stock_lhb_ggtj_sina()
            stock_rows = df_all[df_all["股票代码"] == code] if df_all is not None else None
            if stock_rows is not None and not stock_rows.empty:
                row = stock_rows.iloc[0]
                times = row.get("上榜次数", 0)
                buy_cum = row.get("累积购买额", 0)
                sell_cum = row.get("累积卖出额", 0)
                lines.append(f"LHB Appearances: {int(times)} times")
                lines.append(f"Cumulative Buy: {float(buy_cum)/1e8:.2f} 亿元 | Sell: {float(sell_cum)/1e8:.2f} 亿元")

                # Recent detail from Sina
                try:
                    detail = ak.stock_lhb_detail_daily_sina()
                    stock_detail = detail[detail["股票代码"] == code].head(5) if detail is not None else None
                    if stock_detail is not None and not stock_detail.empty:
                        lines.append("Recent Appearances:")
                        for _, d in stock_detail.iterrows():
                            date = d.get("交易日期", d.get("股票名称", "N/A"))
                            price = d.get("收盘价", "N/A")
                            reason = str(d.get("指标", ""))[:80]
                            lines.append(f"  [{date}] Close: {price} — {reason}")
                except Exception:
                    pass

                return "\n".join(lines)
        except Exception:
            pass

        # Fallback: East Money LHB detail
        try:
            df = ak.stock_lhb_stock_detail_em(symbol=code)
            if df is not None and not df.empty:
                recent = df.head(5)
                lines.append(f"Recent appearances ({len(df)} total):")
                for _, row in recent.iterrows():
                    date = row.get("上榜日", "N/A")
                    reason = row.get("上榜原因", row.get("解读", "N/A"))
                    close = row.get("收盘价", "N/A")
                    change = row.get("涨跌幅", "N/A")
                    net_buy = row.get("龙虎榜净买额", 0)
                    buy = row.get("龙虎榜买入额", 0)
                    sell = row.get("龙虎榜卖出额", 0)

                    lines.append(f"\n  [{date}] {reason}")
                    lines.append(f"  Close: {close} | Change: {change}%")
                    if net_buy and float(net_buy) != 0:
                        sign = "+" if float(net_buy) >= 0 else ""
                        lines.append(f"  LHB Net Buy: {sign}{float(net_buy)/1e8:.2f} 亿元 (Buy: {float(buy)/1e8:.2f} / Sell: {float(sell)/1e8:.2f})")

                return "\n".join(lines)
        except Exception:
            pass

        return f"Dragon Tiger Board: {s} has not appeared on 龙虎榜 recently."
    except Exception:
        return None


def _fetch_top_flow_stocks(ak) -> str | None:
    """Fetch top stocks by main capital flow for market breadth context."""
    try:
        df = ak.stock_individual_fund_flow_rank(indicator="今日")
        if df is None or df.empty:
            return None

        top_in = df.nlargest(5, "今日主力净流入-净额")

        lines = ["--- Top Capital Flow Leaders (主力资金净流入前5) ---"]
        for _, row in top_in.iterrows():
            code = row.get("代码", "N/A")
            name = row.get("名称", "N/A")
            price = row.get("最新价", "N/A")
            change = row.get("今日涨跌幅", 0)
            net = row.get("今日主力净流入-净额", 0) / 1e8
            pct = row.get("今日主力净流入-净占比", 0)
            sign = "+" if float(change) >= 0 else ""
            lines.append(f"  {code} {name}: {price} ({sign}{change}%) | Net: +{net:.2f} 亿元 ({pct:.1f}%)")

        return "\n".join(lines)
    except Exception:
        return None


@tool
def fetch_cn_market_sentiment(symbol: str) -> str:
    """A股/港股市场情绪 — China/HK market sentiment, sector flow, and Dragon Tiger Board.

    Fetches sector fund flow rankings, Dragon Tiger Board (龙虎榜) appearances
    for the stock, and top capital flow leaders across the market.

    Only works for China A-Share (.SZ/.SH/.SS) and Hong Kong (.HK) tickers.

    Args:
        symbol: Ticker symbol (e.g. 600519.SS, 00700.HK)
    """
    if not _is_cn_or_hk(symbol):
        return f"Market sentiment data not applicable for {symbol} (CN/HK markets only)."

    try:
        ak = _try_akshare()
    except ImportError as e:
        return f"Error: {e}"

    sections = [
        f"=== CN/HK Market Sentiment: {symbol} ===",
    ]

    # Sector fund flow
    sector = _fetch_sector_flow(ak)
    if sector:
        sections.append(sector)

    # Dragon Tiger Board for this stock
    lhb = _fetch_dragon_tiger(ak, symbol)
    if lhb:
        sections.append(lhb)

    # Top flow stocks
    flow = _fetch_top_flow_stocks(ak)
    if flow:
        sections.append(flow)

    if len(sections) <= 1:
        sections.append("No market sentiment data available (may be outside trading hours).")

    return "\n".join(sections)
