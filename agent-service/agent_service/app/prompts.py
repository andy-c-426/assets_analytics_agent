from datetime import datetime, timezone


def _now() -> str:
    """Human-readable current timestamp for prompt injection."""
    now = datetime.now(timezone.utc)
    return now.strftime("%B %d, %Y at %H:%M UTC (%A)")


PLAN_PROMPT = """You are a professional financial analyst. You are analyzing the asset {symbol}.

Today is {current_date}.

Available tools (core data already collected, use these for supplementary research):
{tool_descriptions}

{available_data}

Plan supplementary tool calls to deepen the analysis.

Reply with your reasoning on the first line, then the JSON plan on the second line:

Your reasoning here (one line explaining what additional data you need and why)
[{{"tool": "tool_name", "args": {{"arg": "value"}}}}]

Only return these two lines, nothing else."""

OBSERVE_PROMPT = """You are a professional financial analyst analyzing {symbol}.

Today is {current_date}.

Core data (market data, macro research, sentiment news) has been collected.
You also have these supplementary results:

{tool_results_summary}

Is the supplementary data sufficient for a thorough analysis?

- If price history or technicals would add meaningful depth and haven't been collected yet, request them.
- If the data is comprehensive enough, mark decision "enough".

Reply in JSON format exactly like this:
{{"decision": "enough", "missing": [], "reasoning": "Data is comprehensive"}}
or
{{"decision": "more", "missing": ["fetch_price_history"], "reasoning": "Need price history for technical context"}}

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
1. **Market Context** — Broader market environment: how major indices are performing, current macro themes (interest rates, inflation, geopolitical factors), and sector-level trends. Connect this to how the overall market backdrop affects this specific asset.
2. **Overview** — Brief summary of the company and current situation (mention the analysis date)
3. **Key Metrics Analysis** — What the numbers mean, in the context of the broader market and sector
4. **Technical Analysis** — Trend and momentum assessment (if data available), relative to market index performance
5. **Recent News Impact** — How both ticker-specific news AND macro/sector news may affect the asset
6. **Risks & Opportunities** — Include both company-specific and macro-driven risks
7. **Outlook** — Short to medium term outlook factoring in market trends

Be objective. Highlight both positives and negatives. Do not give specific buy/sell recommendations.
Use markdown formatting for readability.""",
    "zh-CN": """请按以下结构撰写分析报告：
1. **市场环境** — 整体市场背景：主要指数表现、当前宏观主题（利率、通胀、地缘政治因素）以及行业趋势。将这些宏观背景与目标资产关联分析。
2. **概述** — 公司及当前情况简要介绍（注明分析日期）
3. **关键指标分析** — 结合更广泛市场与行业背景解读各项数据
4. **技术分析** — 趋势与动能评估（如有数据），与市场指数表现对比
5. **近期新闻影响** — 公司特定新闻及宏观/行业新闻对资产的综合影响
6. **风险与机遇** — 涵盖公司特定风险及宏观驱动的风险
7. **展望** — 结合市场趋势的中短期前景

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
Core data (already collected — do NOT re-request):
  fetch_market_data → price, metrics, fundamentals, 52W range, market index
  fetch_macro_research → macro news, sector trends, policy updates
  fetch_sentiment_news → news articles grouped by category, sentiment

Supplementary tools you may plan:
- fetch_price_history(symbol, period): OHLCV price history. period: 1mo, 6mo, 1y, 5y, max
- calculate_technicals(symbol): SMA, EMA, RSI, volatility from price history. Prices are auto-wired from the previous fetch_price_history result — do NOT pass a "prices" argument, just pass {"symbol": "..."}.
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
