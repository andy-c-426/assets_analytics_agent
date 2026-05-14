"""Supplementary tools for US markets.

Uses yfinance for analyst consensus, insider activity, institutional
ownership, earnings calendar, and SEC filings.
"""

from datetime import datetime, timezone

from langchain_core.tools import tool

from agent_service.app.tools.market_utils import detect_market


def _is_us(symbol: str) -> bool:
    """Check if symbol belongs to the US market."""
    market = detect_market(symbol)
    return market["region"] == "United States"


def _get_ticker(symbol: str):
    """Return a yfinance Ticker object."""
    import yfinance as yf
    return yf.Ticker(symbol.strip())


@tool
def fetch_us_fundamentals(symbol: str) -> str:
    """Fetch US-specific fundamentals: analyst consensus, insider trades,
    institutional ownership, upcoming earnings, and recent SEC filings.

    Only works for US equities (NYSE/NASDAQ).

    Args:
        symbol: Ticker symbol (e.g. AAPL, MSFT)
    """
    if not _is_us(symbol):
        return f"US fundamentals not applicable for {symbol} (US markets only)."

    try:
        t = _get_ticker(symbol)
    except Exception as e:
        return f"Error accessing yfinance for {symbol}: {e}"

    sections = [f"=== US Fundamentals: {symbol} ==="]

    # 1. Analyst Consensus
    try:
        targets = t.analyst_price_targets
        if targets and isinstance(targets, dict):
            current = targets.get("current")
            high = targets.get("high")
            low = targets.get("low")
            mean = targets.get("mean")
            median = targets.get("median")
            lines = ["--- Analyst Consensus ---"]
            if current is not None:
                lines.append(f"Current Price: ${current:.2f}")
            if low is not None:
                lines.append(f"Target Low: ${low:.2f}")
            if mean is not None:
                if current and current != 0:
                    lines.append(f"Target Mean: ${mean:.2f} ({((mean/current - 1)*100):+.1f}% vs current)")
                else:
                    lines.append(f"Target Mean: ${mean:.2f}")
            if median is not None:
                lines.append(f"Target Median: ${median:.2f}")
            if high is not None:
                lines.append(f"Target High: ${high:.2f}")
            sections.append("\n".join(lines))
    except Exception:
        pass

    # 2. Recommendations
    try:
        recs = t.recommendations
        if recs is not None and hasattr(recs, "iloc") and not recs.empty:
            latest = recs.iloc[-1]
            lines = ["--- Analyst Recommendations ---"]
            for label in ["strongBuy", "buy", "hold", "sell", "strongSell"]:
                val = latest.get(label, 0)
                if val:
                    lines.append(f"  {label}: {int(val)}")
            if len(lines) > 1:
                sections.append("\n".join(lines))
    except Exception:
        pass

    # 3. Insider Transactions (last 5)
    try:
        insider = t.insider_transactions
        if insider is not None and hasattr(insider, "head") and not insider.empty:
            recent = insider.head(5)
            lines = ["--- Recent Insider Transactions ---"]
            for _, row in recent.iterrows():
                name = row.get("Insider", row.get("Insider", "N/A"))
                shares = row.get("Shares", "N/A")
                value = row.get("Value", None)
                transaction = row.get("Transaction", row.get("Transaction", "N/A"))
                date = row.get("Start Date", "N/A")
                line = f"  [{date}] {name}: {transaction} — Shares: {shares}"
                if value is not None and str(value) != "nan":
                    try:
                        line += f" (${float(value):,.0f})"
                    except (ValueError, TypeError):
                        pass
                lines.append(line)
            if len(lines) > 1:
                sections.append("\n".join(lines))
    except Exception:
        pass

    # 4. Institutional Ownership
    try:
        inst = t.institutional_holders
        if inst is not None and hasattr(inst, "head") and not inst.empty:
            top = inst.head(5)
            lines = ["--- Top Institutional Holders ---"]
            for _, row in top.iterrows():
                holder = row.get("Holder", "N/A")
                shares = row.get("Shares", row.get("Shares", "N/A"))
                pct = row.get("pctHeld", row.get("pctHeld", None))
                s = f"  {holder}: {shares:,.0f} shares" if isinstance(shares, (int, float)) else f"  {holder}: {shares} shares"
                if pct is not None and str(pct) != "nan":
                    try:
                        s += f" ({float(pct)*100:.2f}%)" if float(pct) < 1 else f" ({float(pct):.2f}%)"
                    except (ValueError, TypeError):
                        pass
                lines.append(s)
            if len(lines) > 1:
                sections.append("\n".join(lines))

        major = t.major_holders
        if major is not None:
            mh = major.to_dict() if callable(getattr(major, "to_dict", None)) else major
            if isinstance(mh, dict):
                lines = ["--- Ownership Summary ---"]
                for k, v in mh.items():
                    if v and str(v) != "nan":
                        label = k.replace("_", " ").title()
                        lines.append(f"  {label}: {v}")
                if len(lines) > 1:
                    sections.append("\n".join(lines))
    except Exception:
        pass

    # 5. Earnings Calendar
    try:
        earnings = t.earnings_dates
        if earnings is not None and hasattr(earnings, "iloc") and not earnings.empty:
            lines = ["--- Earnings Calendar ---"]
            now = datetime.now(timezone.utc)
            shown = 0
            for idx, row in earnings.iterrows():
                date = idx if isinstance(idx, datetime) else None
                eps_est = row.get("EPS Estimate", None)
                eps_act = row.get("EPS Actual", None)
                surprise = row.get("Surprise(%)", None)
                if date is not None and date > now:
                    lines.append(f"  Upcoming — Estimate Date: {date.strftime('%Y-%m-%d')}")
                    if eps_est is not None and str(eps_est) != "nan":
                        lines.append(f"    EPS Estimate: ${float(eps_est):.2f}")
                    shown += 1
                elif date is not None:
                    lines.append(f"  [{date.strftime('%Y-%m-%d')}] Reported")
                    if eps_act is not None and str(eps_act) != "nan":
                        lines.append(f"    EPS Actual: ${float(eps_act):.2f}")
                    if eps_est is not None and str(eps_est) != "nan" and eps_act is not None:
                        if surprise is not None and str(surprise) != "nan":
                            lines.append(f"    Estimate: ${float(eps_est):.2f} | Surprise: {float(surprise):+.2f}%")
                if shown >= 3:
                    break
            if len(lines) > 1:
                sections.append("\n".join(lines))
    except Exception:
        pass

    # 6. Recent SEC Filings (last 5)
    try:
        filings = t.sec_filings
        if filings is not None and isinstance(filings, list) and len(filings) > 0:
            recent = filings[:5]
            lines = ["--- Recent SEC Filings ---"]
            for f in recent:
                f_type = f.get("Type", f.get("Form Type", "N/A"))
                f_date = f.get("Date", f.get("Filing Date", "N/A"))
                title = f.get("Title", f.get("Description", ""))
                url = f.get("EdgarUrl", f.get("URL", ""))
                line = f"  [{f_date}] {f_type}"
                if title:
                    line += f": {str(title)[:80]}"
                if url and isinstance(url, str) and url.startswith("http"):
                    line += f" ({url})"
                lines.append(line)
            if len(lines) > 1:
                sections.append("\n".join(lines))
    except Exception:
        pass

    if len(sections) <= 1:
        sections.append("No US fundamentals data available.")

    return "\n".join(sections)
