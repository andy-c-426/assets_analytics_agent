PLAN_PROMPT = """You are a professional financial analyst. You are analyzing the asset {symbol}.

Available tools:
{tool_descriptions}

Plan which tools to call to gather the data you need for a thorough analysis. You must call at least fetch_asset_data.

Return your plan as a JSON list of tool calls:
[{{"tool": "tool_name", "args": {{"arg": "value"}}}}]

Only return the JSON list, nothing else."""

OBSERVE_PROMPT = """You are a professional financial analyst analyzing {symbol}.

You have executed the following tools and received results:

{tool_results_summary}

Do you have enough data to write a comprehensive analysis? If not, what additional data do you need?

Reply with ONLY one word: "enough" or "more" followed by an optional brief reason.

Example: "enough"
Example: "more - need technical indicators for trend analysis"
"""

SYNTHESIZE_PROMPT = """You are a professional financial analyst. Write a comprehensive analysis of {symbol} based on the data collected below.

{tool_results_full}

Structure your analysis with:
1. **Overview** — Brief summary of the company and current situation
2. **Key Metrics Analysis** — What the numbers mean
3. **Technical Analysis** — Trend and momentum assessment (if data available)
4. **Recent News Impact** — How recent news may affect the asset
5. **Risks & Opportunities**
6. **Outlook** — Short to medium term outlook

Be objective. Highlight both positives and negatives. Do not give specific buy/sell recommendations.
Use markdown formatting for readability."""

TOOL_REGISTRY = """
- fetch_asset_data(symbol): Fetch complete asset profile, current price, key metrics, and recent news
- fetch_price_history(symbol, period): Fetch OHLCV price history. period is one of: 1mo, 6mo, 1y, 5y, max
- calculate_technicals(symbol, prices): Calculate SMA, EMA, RSI, volatility from price data. prices is a list of close prices.
"""
