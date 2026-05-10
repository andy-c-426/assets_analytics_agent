"""Bloomberg-style derived analytics computed from raw yfinance data.

Pre-computes valuation context, momentum, risk, and profitability metrics so the LLM
receives analysis-ready data rather than having to infer everything from raw numbers.
"""

import math
from datetime import datetime, timezone


def compute_enriched_analytics(symbol: str, asset_data: str, price_history: str) -> dict:
    """Parse raw tool results and compute Bloomberg-style derived metrics.

    Returns a dict keyed by category, each containing pre-formatted markdown sections
    ready to inject into LLM prompts.
    """
    metrics: dict[str, list[str]] = {
        "valuation": [],
        "momentum": [],
        "risk": [],
        "profitability": [],
    }

    info = _parse_asset_data(asset_data)
    prices = _parse_price_history(price_history)

    # ── Valuation ──────────────────────────────────────────────
    pe = info.get("pe")
    pb = info.get("pb")
    mkt_cap = info.get("market_cap")
    price = info.get("current_price")

    if pe is not None:
        if pe < 0:
            metrics["valuation"].append(f"P/E: Negative (unprofitable)")
        elif pe < 15:
            metrics["valuation"].append(f"P/E: {pe:.1f} (Value territory — below 15x)")
        elif pe < 25:
            metrics["valuation"].append(f"P/E: {pe:.1f} (Fair value — 15-25x range)")
        else:
            metrics["valuation"].append(f"P/E: {pe:.1f} (Growth premium — above 25x)")

    if pb is not None:
        if pb < 1.0:
            metrics["valuation"].append(f"P/B: {pb:.2f} (Below book value)")
        elif pb < 3.0:
            metrics["valuation"].append(f"P/B: {pb:.2f} (Moderate premium to book)")
        else:
            metrics["valuation"].append(f"P/B: {pb:.2f} (High premium to book)")

    if mkt_cap is not None:
        metrics["valuation"].append(f"Market Cap: {_fmt_cap(mkt_cap)}")

    # ── Momentum ───────────────────────────────────────────────
    if prices and len(prices) >= 20:
        current = prices[-1]
        returns = _compute_returns(prices)
        sma_20 = sum(prices[-20:]) / 20
        sma_50 = sum(prices[-min(50, len(prices)):]) / min(50, len(prices))
        rsi = _compute_rsi(prices, 14)

        metrics["momentum"].append(f"Current Price: ${current:.2f}")

        if "1w" in returns:
            metrics["momentum"].append(f"1-Week Return: {returns['1w']:+.2f}%")
        if "1m" in returns:
            metrics["momentum"].append(f"1-Month Return: {returns['1m']:+.2f}%")
        if "3m" in returns:
            metrics["momentum"].append(f"3-Month Return: {returns['3m']:+.2f}%")

        vs_sma20 = ((current - sma_20) / sma_20) * 100
        metrics["momentum"].append(
            f"vs SMA(20): {vs_sma20:+.1f}% ({'Above' if vs_sma20 > 0 else 'Below'} short-term trend)"
        )

        if rsi is not None:
            if rsi > 70:
                zone = "Overbought"
            elif rsi < 30:
                zone = "Oversold"
            elif rsi > 50:
                zone = "Bullish momentum"
            else:
                zone = "Bearish momentum"
            metrics["momentum"].append(f"RSI(14): {rsi:.1f} ({zone})")

    # ── Risk ───────────────────────────────────────────────────
    beta = info.get("beta")
    if beta is not None:
        if beta < 0.8:
            metrics["risk"].append(f"Beta: {beta:.2f} (Defensive — less volatile than market)")
        elif beta < 1.2:
            metrics["risk"].append(f"Beta: {beta:.2f} (Market-like volatility)")
        else:
            metrics["risk"].append(f"Beta: {beta:.2f} (Aggressive — more volatile than market)")

    high_52w = info.get("high_52w")
    low_52w = info.get("low_52w")
    if price is not None and high_52w is not None and low_52w is not None and high_52w > 0:
        pct_from_high = ((price - high_52w) / high_52w) * 100
        pct_from_low = ((price - low_52w) / low_52w) * 100
        metrics["risk"].append(
            f"52-Week Range: ${low_52w:.2f} – ${high_52w:.2f}"
        )
        metrics["risk"].append(
            f"Position: {pct_from_high:+.1f}% from high, {pct_from_low:+.1f}% from low"
        )

    if prices and len(prices) >= 30:
        drawdown = _max_drawdown(prices)
        volatility = _daily_volatility(prices)
        if drawdown is not None:
            metrics["risk"].append(f"Max Drawdown ({len(prices)}d): {drawdown:.1f}%")
        if volatility is not None:
            metrics["risk"].append(f"Daily Volatility (ann.): {volatility:.1f}%")

    # ── Profitability ──────────────────────────────────────────
    eps = info.get("eps")
    if eps is not None and eps > 0:
        metrics["profitability"].append(f"EPS (TTM): ${eps:.2f}")

    div_yield = info.get("dividend_yield")
    if div_yield is not None:
        metrics["profitability"].append(f"Dividend Yield: {div_yield * 100:.2f}%")

    # Market cap context
    if mkt_cap is not None:
        if mkt_cap >= 200e9:
            metrics["profitability"].append("Size: Mega-cap (≥ $200B)")
        elif mkt_cap >= 10e9:
            metrics["profitability"].append("Size: Large-cap ($10B–$200B)")
        elif mkt_cap >= 2e9:
            metrics["profitability"].append("Size: Mid-cap ($2B–$10B)")
        else:
            metrics["profitability"].append("Size: Small-cap (< $2B)")

    return metrics


def format_analytics_dashboard(metrics: dict, symbol: str) -> str:
    """Render the analytics dict as a markdown dashboard for LLM prompts."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sections = [f"## Pre-Computed Analytics Dashboard: {symbol}"]

    section_labels = {
        "valuation": "Valuation Context",
        "momentum": "Momentum & Trend",
        "risk": "Risk & Positioning",
        "profitability": "Profitability & Scale",
    }

    for key, label in section_labels.items():
        items = metrics.get(key, [])
        if items:
            sections.append(f"\n### {label}")
            for item in items:
                sections.append(f"- {item}")

    return "\n".join(sections)


# ── Parsing helpers ────────────────────────────────────────────

def _parse_asset_data(data: str) -> dict:
    """Extract key metrics from fetch_asset_data output text."""
    info: dict = {}
    lines = data.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("Market Cap:"):
            # Parse "$3.5T" or "$890.45B" or "$250M"
            cap_str = line.split(":", 1)[-1].strip().replace("$", "").replace(",", "")
            try:
                if cap_str.endswith("T"):
                    info["market_cap"] = float(cap_str[:-1]) * 1e12
                elif cap_str.endswith("B"):
                    info["market_cap"] = float(cap_str[:-1]) * 1e9
                elif cap_str.endswith("M"):
                    info["market_cap"] = float(cap_str[:-1]) * 1e6
                elif cap_str != "N/A":
                    info["market_cap"] = float(cap_str)
            except ValueError:
                pass
        elif line.startswith("Current Price:"):
            parts = line.split(":", 1)[-1].strip().split()
            if parts:
                try:
                    info["current_price"] = float(parts[0].replace("$", "").replace(",", ""))
                except ValueError:
                    pass
        elif "P/E:" in line and "P/B:" not in line:
            val = line.split("P/E:", 1)[-1].strip()
            try:
                info["pe"] = float(val)
            except ValueError:
                pass
        elif "P/B:" in line:
            val = line.split("P/B:", 1)[-1].strip()
            try:
                info["pb"] = float(val)
            except ValueError:
                pass
        elif "EPS:" in line:
            val = line.split("EPS:", 1)[-1].strip().replace("$", "")
            try:
                info["eps"] = float(val)
            except ValueError:
                pass
        elif "Dividend Yield:" in line:
            val = line.split(":", 1)[-1].strip().replace("%", "")
            try:
                info["dividend_yield"] = float(val) / 100
            except ValueError:
                pass
        elif "Beta:" in line:
            val = line.split("Beta:", 1)[-1].strip()
            try:
                info["beta"] = float(val)
            except ValueError:
                pass
        elif "52W High:" in line:
            val = line.split(":", 1)[-1].strip().replace("$", "").replace(",", "")
            try:
                info["high_52w"] = float(val)
            except ValueError:
                pass
        elif "52W Low:" in line:
            val = line.split(":", 1)[-1].strip().replace("$", "").replace(",", "")
            try:
                info["low_52w"] = float(val)
            except ValueError:
                pass
    return info


def _parse_price_history(data: str) -> list[float]:
    """Extract closing prices from fetch_price_history output."""
    prices = []
    for line in data.split("\n"):
        line = line.strip()
        # Lines look like: "2026-04-10: O=195.23 H=198.45 L=194.10 C=197.80 V=12345678"
        if " C=" in line:
            try:
                close = float(line.split(" C=")[1].split(" ")[0])
                prices.append(close)
            except (ValueError, IndexError):
                pass
    return prices


# ── Financial math ─────────────────────────────────────────────

def _compute_returns(prices: list[float]) -> dict[str, float]:
    """Compute period returns in percent."""
    returns = {}
    current = prices[-1]
    # Approximate: 5 trading days = 1 week, 21 = 1 month, 63 = 3 month
    for days, label in [(5, "1w"), (21, "1m"), (63, "3m")]:
        if len(prices) > days:
            prev = prices[-(days + 1)]
            if prev > 0:
                returns[label] = ((current - prev) / prev) * 100
    return returns


def _compute_rsi(prices: list[float], period: int = 14) -> float | None:
    """Compute RSI for the most recent period."""
    if len(prices) < period + 1:
        return None
    gains = 0.0
    losses = 0.0
    for i in range(len(prices) - period, len(prices)):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains += change
        else:
            losses += abs(change)
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _max_drawdown(prices: list[float]) -> float | None:
    """Maximum drawdown as a percentage."""
    if len(prices) < 2:
        return None
    peak = prices[0]
    max_dd = 0.0
    for p in prices[1:]:
        if p > peak:
            peak = p
        dd = (peak - p) / peak * 100
        if dd > max_dd:
            max_dd = dd
    return max_dd


def _daily_volatility(prices: list[float]) -> float | None:
    """Annualized daily volatility."""
    if len(prices) < 2:
        return None
    returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] > 0:
            returns.append(math.log(prices[i] / prices[i - 1]))
    if len(returns) < 2:
        return None
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return math.sqrt(variance) * math.sqrt(252) * 100


def _fmt_cap(n: float) -> str:
    if n >= 1e12:
        return f"${n / 1e12:.2f}T"
    if n >= 1e9:
        return f"${n / 1e9:.2f}B"
    if n >= 1e6:
        return f"${n / 1e6:.2f}M"
    return f"${n:,.0f}"
