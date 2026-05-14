"""Bloomberg-style derived analytics computed from raw yfinance data.

Pre-computes valuation context, momentum, risk, and profitability metrics so the LLM
receives analysis-ready data rather than having to infer everything from raw numbers.
"""

import math
from datetime import datetime, timezone


def compute_enriched_analytics(
    symbol: str, asset_data: str, price_history: str, language: str = "en",
    market_info: dict | None = None,
) -> dict:
    """Parse raw tool results and compute Bloomberg-style derived metrics.

    Returns a dict keyed by category, each containing pre-formatted markdown sections
    ready to inject into LLM prompts.
    """
    is_zh = language == "zh-CN"

    metrics: dict[str, list[str]] = {
        "valuation": [],
        "momentum": [],
        "risk": [],
        "profitability": [],
    }

    info = _parse_asset_data(asset_data)
    prices = _parse_price_history(price_history)

    # Determine thresholds and currency from market detection
    if market_info is None:
        from agent_service.app.tools.market_utils import detect_market
        try:
            market_info = detect_market(symbol)
        except Exception:
            market_info = {"currency_symbol": "$", "pe_thresholds": {"low": 15, "mid": 25, "high": 40}}

    thresholds = market_info.get("pe_thresholds", {"low": 15, "mid": 25, "high": 40})
    csym = market_info.get("currency_symbol", "$")
    pe_low = thresholds.get("low", 15)
    pe_mid = thresholds.get("mid", 25)
    pe_high = thresholds.get("high", 40)

    # ── Valuation ──────────────────────────────────────────────
    pe = info.get("pe")
    pb = info.get("pb")
    mkt_cap = info.get("market_cap")
    price = info.get("current_price")

    if pe is not None:
        if pe < 0:
            metrics["valuation"].append(
                "P/E: Negative (unprofitable)" if not is_zh else "市盈率: 负值（亏损）"
            )
        elif pe < pe_low:
            metrics["valuation"].append(
                f"P/E: {pe:.1f} (Value territory — below {pe_low}x)" if not is_zh
                else f"市盈率: {pe:.1f}（价值区间 — 低于 {pe_low} 倍）"
            )
        elif pe < pe_mid:
            metrics["valuation"].append(
                f"P/E: {pe:.1f} (Fair value — {pe_low}-{pe_mid}x range)" if not is_zh
                else f"市盈率: {pe:.1f}（合理估值 — {pe_low}-{pe_mid} 倍区间）"
            )
        else:
            metrics["valuation"].append(
                f"P/E: {pe:.1f} (Growth premium — above {pe_mid}x)" if not is_zh
                else f"市盈率: {pe:.1f}（成长溢价 — 高于 {pe_mid} 倍）"
            )

    if pb is not None:
        if pb < 1.0:
            metrics["valuation"].append(
                f"P/B: {pb:.2f} (Below book value)" if not is_zh
                else f"市净率: {pb:.2f}（低于账面价值）"
            )
        elif pb < 3.0:
            metrics["valuation"].append(
                f"P/B: {pb:.2f} (Moderate premium to book)" if not is_zh
                else f"市净率: {pb:.2f}（适度溢价）"
            )
        else:
            metrics["valuation"].append(
                f"P/B: {pb:.2f} (High premium to book)" if not is_zh
                else f"市净率: {pb:.2f}（高溢价）"
            )

    if mkt_cap is not None:
        label = "Market Cap" if not is_zh else "总市值"
        metrics["valuation"].append(f"{label}: {_fmt_cap(mkt_cap, csym)}")

    # ── Momentum ───────────────────────────────────────────────
    if prices and len(prices) >= 20:
        current = prices[-1]
        returns = _compute_returns(prices)
        sma_20 = sum(prices[-20:]) / 20
        sma_50 = sum(prices[-min(50, len(prices)):]) / min(50, len(prices))
        rsi = _compute_rsi(prices, 14)

        if is_zh:
            metrics["momentum"].append(f"当前价格: {csym}{current:.2f}")
        else:
            metrics["momentum"].append(f"Current Price: {csym}{current:.2f}")

        if "1w" in returns:
            if is_zh:
                metrics["momentum"].append(f"1 周回报: {returns['1w']:+.2f}%")
            else:
                metrics["momentum"].append(f"1-Week Return: {returns['1w']:+.2f}%")
        if "1m" in returns:
            if is_zh:
                metrics["momentum"].append(f"1 月回报: {returns['1m']:+.2f}%")
            else:
                metrics["momentum"].append(f"1-Month Return: {returns['1m']:+.2f}%")
        if "3m" in returns:
            if is_zh:
                metrics["momentum"].append(f"3 月回报: {returns['3m']:+.2f}%")
            else:
                metrics["momentum"].append(f"3-Month Return: {returns['3m']:+.2f}%")

        vs_sma20 = ((current - sma_20) / sma_20) * 100
        if is_zh:
            direction = "高于" if vs_sma20 > 0 else "低于"
            metrics["momentum"].append(
                f"相对 SMA(20): {vs_sma20:+.1f}%（{direction}短期趋势）"
            )
        else:
            direction = "Above" if vs_sma20 > 0 else "Below"
            metrics["momentum"].append(
                f"vs SMA(20): {vs_sma20:+.1f}% ({direction} short-term trend)"
            )

        if rsi is not None:
            if rsi > 70:
                zone = "Overbought" if not is_zh else "超买"
            elif rsi < 30:
                zone = "Oversold" if not is_zh else "超卖"
            elif rsi > 50:
                zone = "Bullish momentum" if not is_zh else "看涨动能"
            else:
                zone = "Bearish momentum" if not is_zh else "看跌动能"
            metrics["momentum"].append(f"RSI(14): {rsi:.1f} ({zone})")

    # ── Risk ───────────────────────────────────────────────────
    beta = info.get("beta")
    if beta is not None:
        if beta < 0.8:
            metrics["risk"].append(
                f"Beta: {beta:.2f} (Defensive — less volatile than market)" if not is_zh
                else f"贝塔系数: {beta:.2f}（防御型 — 波动性低于市场）"
            )
        elif beta < 1.2:
            metrics["risk"].append(
                f"Beta: {beta:.2f} (Market-like volatility)" if not is_zh
                else f"贝塔系数: {beta:.2f}（市场同步波动）"
            )
        else:
            metrics["risk"].append(
                f"Beta: {beta:.2f} (Aggressive — more volatile than market)" if not is_zh
                else f"贝塔系数: {beta:.2f}（激进型 — 波动性高于市场）"
            )

    high_52w = info.get("high_52w")
    low_52w = info.get("low_52w")
    if price is not None and high_52w is not None and low_52w is not None and high_52w > 0:
        pct_from_high = ((price - high_52w) / high_52w) * 100
        pct_from_low = ((price - low_52w) / low_52w) * 100
        if is_zh:
            metrics["risk"].append(
                f"52 周区间: {csym}{low_52w:.2f} – {csym}{high_52w:.2f}"
            )
            metrics["risk"].append(
                f"位置: 距高点 {pct_from_high:+.1f}%，距低点 {pct_from_low:+.1f}%"
            )
        else:
            metrics["risk"].append(
                f"52-Week Range: {csym}{low_52w:.2f} – {csym}{high_52w:.2f}"
            )
            metrics["risk"].append(
                f"Position: {pct_from_high:+.1f}% from high, {pct_from_low:+.1f}% from low"
            )

    if prices and len(prices) >= 30:
        drawdown = _max_drawdown(prices)
        volatility = _daily_volatility(prices)
        if drawdown is not None:
            if is_zh:
                metrics["risk"].append(f"最大回撤（{len(prices)} 日）: {drawdown:.1f}%")
            else:
                metrics["risk"].append(f"Max Drawdown ({len(prices)}d): {drawdown:.1f}%")
        if volatility is not None:
            if is_zh:
                metrics["risk"].append(f"年化日波动率: {volatility:.1f}%")
            else:
                metrics["risk"].append(f"Daily Volatility (ann.): {volatility:.1f}%")

    # ── Profitability ──────────────────────────────────────────
    eps = info.get("eps")
    if eps is not None and eps > 0:
        if is_zh:
            metrics["profitability"].append(f"每股收益 (TTM): {csym}{eps:.2f}")
        else:
            metrics["profitability"].append(f"EPS (TTM): {csym}{eps:.2f}")

    div_yield = info.get("dividend_yield")
    if div_yield is not None:
        if is_zh:
            metrics["profitability"].append(f"股息率: {div_yield * 100:.2f}%")
        else:
            metrics["profitability"].append(f"Dividend Yield: {div_yield * 100:.2f}%")

    # Market cap context (with currency symbol)
    if mkt_cap is not None:
        if mkt_cap >= 200e9:
            label = f"Size: Mega-cap (≥ {csym}200B)" if not is_zh else f"规模: 超大盘（≥ 2000 亿）"
        elif mkt_cap >= 10e9:
            label = f"Size: Large-cap ({csym}10B–{csym}200B)" if not is_zh else f"规模: 大盘（100 亿 – 2000 亿）"
        elif mkt_cap >= 2e9:
            label = f"Size: Mid-cap ({csym}2B–{csym}10B)" if not is_zh else f"规模: 中盘（20 亿 – 100 亿）"
        else:
            label = f"Size: Small-cap (< {csym}2B)" if not is_zh else f"规模: 小盘（< 20 亿）"
        metrics["profitability"].append(label)

    return metrics


def format_analytics_dashboard(metrics: dict, symbol: str, language: str = "en") -> str:
    """Render the analytics dict as a markdown dashboard for LLM prompts."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    is_zh = language == "zh-CN"

    title = f"## Pre-Computed Analytics Dashboard: {symbol}" if not is_zh else f"## 预计算分析面板: {symbol}"
    sections = [title]

    section_labels: dict[str, str]
    if is_zh:
        section_labels = {
            "valuation": "估值分析",
            "momentum": "动能与趋势",
            "risk": "风险与仓位",
            "profitability": "盈利能力与规模",
        }
    else:
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


def _fmt_cap(n: float, currency_symbol: str = "$") -> str:
    if n >= 1e12:
        return f"{currency_symbol}{n / 1e12:.2f}T"
    if n >= 1e9:
        return f"{currency_symbol}{n / 1e9:.2f}B"
    if n >= 1e6:
        return f"{currency_symbol}{n / 1e6:.2f}M"
    return f"{currency_symbol}{n:,.0f}"
