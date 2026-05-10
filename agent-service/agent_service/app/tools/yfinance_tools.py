from langchain_core.tools import tool
import yfinance as yf


@tool
def fetch_asset_data(symbol: str) -> str:
    """Fetch complete asset data for a ticker symbol including profile, current price,
    key metrics, and recent news. Use this first when analyzing any asset.

    Args:
        symbol: The ticker symbol (e.g. AAPL, 0700.HK, 300502.SZ)
    """
    try:
        ticker = yf.Ticker(symbol.strip())
        info = ticker.get_info()

        if not info or info.get("symbol") is None:
            return f"No data found for symbol: {symbol}"

        name = info.get("shortName") or info.get("longName") or symbol
        sector = info.get("sector", "N/A")
        country = info.get("country", "N/A")
        market_cap = info.get("marketCap")
        description = info.get("longBusinessSummary", "No description available")
        # Compress to first two sentences (~200 chars) to reduce LLM token costs
        compressed_desc = _compress_description(description)

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

        news_items = []
        for item in (info.get("news") or [])[:5]:
            title = item.get("title", "")
            news_items.append(f"- {title}")

        lines = [
            f"Asset: {name} ({symbol})",
            f"Sector: {sector} | Country: {country}",
            f"Market Cap: {_fmt_big(market_cap)}" if market_cap is not None else "Market Cap: N/A",
            "",
            f"Current Price: {current_price} {currency}" if current_price is not None else "Price: N/A",
        ]
        if change is not None and change_pct is not None:
            lines.append(f"Change: {change:.2f} ({change_pct:.2f}%)")
        lines.extend([
            "",
            "Key Metrics:",
            f"  P/E: {pe:.2f}" if pe is not None else "  P/E: N/A",
            f"  P/B: {pb:.2f}" if pb is not None else "  P/B: N/A",
            f"  EPS: ${eps:.2f}" if eps is not None else "  EPS: N/A",
            f"  Dividend Yield: {dividend_yield*100:.2f}%" if dividend_yield is not None else "  Dividend Yield: N/A",
            f"  Beta: {beta:.2f}" if beta is not None else "  Beta: N/A",
            f"  52W High: {high_52w:.2f}" if high_52w is not None else "  52W High: N/A",
            f"  52W Low: {low_52w:.2f}" if low_52w is not None else "  52W Low: N/A",
            "",
            f"Description: {compressed_desc}",
            "",
            f"Recent News ({len(news_items)} articles):",
        ] + news_items)

        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching asset data for {symbol}: {e}"


@tool
def fetch_price_history(symbol: str, period: str = "1mo") -> str:
    """Fetch historical OHLCV price data for a ticker.

    Args:
        symbol: The ticker symbol (e.g. AAPL, 0700.HK)
        period: Time range — one of 1mo, 6mo, 1y, 5y, max
    """
    try:
        valid_periods = {"1mo", "6mo", "1y", "5y", "max"}
        if period not in valid_periods:
            period = "1mo"

        ticker = yf.Ticker(symbol.strip())
        hist = ticker.history(period=period)

        if hist.empty:
            return f"No price history available for {symbol} ({period})"

        records = []
        for idx, row in hist.iterrows():
            records.append(
                f"{idx.strftime('%Y-%m-%d')}: O={row['Open']:.2f} H={row['High']:.2f} "
                f"L={row['Low']:.2f} C={row['Close']:.2f} V={int(row['Volume'])}"
            )

        summary = (
            f"Price History for {symbol} ({period})\n"
            f"Data points: {len(records)}\n"
            f"First: {records[0]}\n"
            f"Last: {records[-1]}\n\n"
            + "\n".join(records[-30:])  # Last 30 records for context
        )
        return summary
    except Exception as e:
        return f"Error fetching price history for {symbol}: {e}"


def _fmt_big(n: float | None) -> str:
    if n is None:
        return "N/A"
    if abs(n) >= 1e12:
        return f"${n / 1e12:.2f}T"
    if abs(n) >= 1e9:
        return f"${n / 1e9:.2f}B"
    if abs(n) >= 1e6:
        return f"${n / 1e6:.2f}M"
    return f"${n:,.0f}"


def _compress_description(text: str) -> str:
    """Keep first two sentences, cap at ~250 chars for LLM token efficiency."""
    if not text or text == "No description available":
        return text
    sentences = text.replace("\n", " ").split(". ")
    result = ". ".join(sentences[:2])
    if not result.endswith("."):
        result += "."
    if len(result) > 250:
        result = result[:247] + "..."
    return result
