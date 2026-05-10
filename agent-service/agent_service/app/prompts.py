from datetime import datetime, timezone


def _now() -> str:
    """Human-readable current timestamp for prompt injection."""
    now = datetime.now(timezone.utc)
    return now.strftime("%B %d, %Y at %H:%M UTC (%A)")


PLAN_PROMPT = """You are a professional financial analyst. You are analyzing the asset {symbol}.

Today is {current_date}.

Available tools:
{tool_descriptions}

First, think about what data you need for a thorough analysis. Consider:
- Basic asset information and current metrics (fetch_futu_data for richer real-time data, fetch_asset_data as alternative)
- Recent price history for technical analysis (use period relative to today's date)
- Latest news for market sentiment — include the current year/month in search queries
- If you need more current information, use search_latest_news

Then plan which tools to call. You must call at least one data tool (fetch_futu_data or fetch_asset_data).

Reply with your reasoning on the first line, then the JSON plan on the second line:

Your reasoning here (one line explaining what data you need and why, referencing the date)
[{{"tool": "tool_name", "args": {{"arg": "value"}}}}]

Only return these two lines, nothing else."""

OBSERVE_PROMPT = """You are a professional financial analyst analyzing {symbol}.

Today is {current_date}.

You have executed tools and received results:

{tool_results_summary}

Do you have enough data to write a comprehensive analysis? If not, what specific data is missing?
Consider whether the data is current enough relative to today's date.

Reply in JSON format exactly like this:
{{"decision": "enough", "missing": [], "reasoning": "Data is sufficient for analysis"}}
or
{{"decision": "more", "missing": ["technicals"], "reasoning": "Need technical indicators for trend assessment"}}

Only return the JSON object, nothing else."""

SYNTHESIZE_PROMPT = """You are a professional financial analyst. Write a comprehensive analysis of {symbol} based on the data collected below.

Today is {current_date}.

{tool_results_full}

Structure your analysis with:
1. **Overview** — Brief summary of the company and current situation (mention the analysis date)
2. **Key Metrics Analysis** — What the numbers mean
3. **Technical Analysis** — Trend and momentum assessment (if data available)
4. **Recent News Impact** — How recent news may affect the asset
5. **Risks & Opportunities**
6. **Outlook** — Short to medium term outlook

Be objective. Highlight both positives and negatives. Do not give specific buy/sell recommendations.
Use markdown formatting for readability."""

LANGUAGE_INSTRUCTIONS: dict[str, str] = {
    "en": "You are writing in English. All analysis and output must be in English.",
    "zh-CN": "You are writing in Simplified Chinese (简体中文). All analysis and output must be in Chinese. Use Chinese financial terminology naturally.",
}

SYNTHESIZE_STRUCTURE: dict[str, str] = {
    "en": """Structure your analysis with:
1. **Overview** — Brief summary of the company and current situation (mention the analysis date)
2. **Key Metrics Analysis** — What the numbers mean
3. **Technical Analysis** — Trend and momentum assessment (if data available)
4. **Recent News Impact** — How recent news may affect the asset
5. **Risks & Opportunities**
6. **Outlook** — Short to medium term outlook

Be objective. Highlight both positives and negatives. Do not give specific buy/sell recommendations.
Use markdown formatting for readability.""",
    "zh-CN": """请按以下结构撰写分析报告：
1. **概述** — 公司及当前情况简要介绍（注明分析日期）
2. **关键指标分析** — 解读各项数据的含义
3. **技术分析** — 趋势与动能评估（如有数据）
4. **近期新闻影响** — 近期新闻对资产的潜在影响
5. **风险与机遇**
6. **展望** — 中短期前景

保持客观，同时呈现利好和利空因素。不要给出具体的买入/卖出建议。
使用 Markdown 格式提升可读性。""",
}


def apply_language_instruction(prompt: str, language: str) -> str:
    """Prepend language instruction to the prompt."""
    instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["en"])
    return instruction + "\n\n" + prompt


def build_synthesize_prompt(symbol: str, enriched_data: str, current_date: str, language: str) -> str:
    """Build the synthesize prompt with language-appropriate structure."""
    instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["en"])
    structure = SYNTHESIZE_STRUCTURE.get(language, SYNTHESIZE_STRUCTURE["en"])

    return f"""{instruction}

You are a professional financial analyst. Write a comprehensive analysis of {symbol} based on the data collected below.

Today is {current_date}.

{enriched_data}

{structure}"""


TOOL_REGISTRY = """
- fetch_asset_data(symbol): Fetch complete asset profile, current price, key metrics, and recent news from yfinance
- fetch_futu_data(symbol): Fetch real-time stock/ETF data from Futu OpenD with yfinance fallback. Richer real-time data (market snapshot, basic info) when Futu is available
- fetch_price_history(symbol, period): Fetch OHLCV price history. period is one of: 1mo, 6mo, 1y, 5y, max
- calculate_technicals(symbol, prices): Calculate SMA, EMA, RSI, volatility from price data. prices is a list of close prices.
- search_latest_news(query, max_results): Search the web for latest news via DuckDuckGo. query is the search term. max_results is results count (default 5).
- fetch_finnhub_news(symbol): Fetch financial news for a ticker from Finnhub (headlines, summaries, sources, dates). Falls back to web search if no API key configured.
"""


def compress_tool_results(tool_results: list) -> str:
    """Compress tool results into a concise summary for LLM prompts.

    Keeps key data points while stripping verbose output to reduce token costs.
    """
    lines = []
    for r in tool_results:
        data = r.get("data", {}).get("full_result", r["summary"])
        data_lines = data.split("\n")
        compressed = "\n".join(data_lines[:8])
        if len(data_lines) > 8:
            compressed += f"\n... ({len(data_lines) - 8} more lines truncated)"

        lines.append(f"## {r['tool']}\n{compressed}")

    return "\n\n".join(lines)
