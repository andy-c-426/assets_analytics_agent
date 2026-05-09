from langchain_core.tools import tool


@tool
def calculate_technicals(symbol: str, prices: list[float]) -> str:
    """Calculate technical indicators from a price series.

    Computes SMA (10/20-day), EMA (12/26-day), RSI (14-day), and daily volatility.
    Use this after fetching price history to identify trends and momentum.

    Args:
        symbol: The ticker symbol
        prices: List of closing prices in chronological order (oldest first)
    """
    try:
        if not prices:
            return f"No price data provided for {symbol}"

        if len(prices) < 14:
            return f"{symbol}: Need at least 14 price points, got {len(prices)}"

        sma_10 = _sma(prices, 10)
        sma_20 = _sma(prices, 20)
        ema_12 = _ema(prices, 12)
        ema_26 = _ema(prices, 26)
        rsi = _rsi(prices, 14)
        volatility = _volatility(prices)

        last_price = prices[-1]

        # Determine trend
        if sma_10 and sma_20:
            if sma_10 > sma_20:
                trend = "Bullish (SMA10 above SMA20)"
            elif sma_10 < sma_20:
                trend = "Bearish (SMA10 below SMA20)"
            else:
                trend = "Neutral (SMA10 equals SMA20)"
        else:
            trend = "Insufficient data for trend"

        # Determine RSI condition
        if rsi:
            if rsi > 70:
                rsi_signal = f"Overbought ({rsi:.1f})"
            elif rsi < 30:
                rsi_signal = f"Oversold ({rsi:.1f})"
            else:
                rsi_signal = f"Neutral ({rsi:.1f})"
        else:
            rsi_signal = "N/A"

        lines = [
            f"Technical Analysis for {symbol}:",
            "",
            f"Latest Price: ${last_price:.2f}",
            f"Volatility (std dev of daily returns): {volatility:.2f}%" if volatility else "Volatility: N/A",
            "",
            "Moving Averages:",
            f"  SMA 10-day: ${sma_10:.2f}" if sma_10 else "  SMA 10-day: N/A",
            f"  SMA 20-day: ${sma_20:.2f}" if sma_20 else "  SMA 20-day: N/A",
            f"  EMA 12-day: ${ema_12:.2f}" if ema_12 else "  EMA 12-day: N/A",
            f"  EMA 26-day: ${ema_26:.2f}" if ema_26 else "  EMA 26-day: N/A",
            "",
            f"RSI (14-day): {rsi_signal}",
            f"Trend: {trend}",
        ]

        return "\n".join(lines)
    except Exception as e:
        return f"Error calculating technicals for {symbol}: {e}"


def _sma(prices: list[float], period: int) -> float | None:
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def _ema(prices: list[float], period: int) -> float | None:
    if len(prices) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return ema


def _rsi(prices: list[float], period: int = 14) -> float | None:
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


def _volatility(prices: list[float]) -> float | None:
    if len(prices) < 2:
        return None
    returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] != 0:
            returns.append((prices[i] - prices[i - 1]) / prices[i - 1])
    if not returns:
        return None
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / len(returns)
    return (variance ** 0.5) * 100  # as percentage
