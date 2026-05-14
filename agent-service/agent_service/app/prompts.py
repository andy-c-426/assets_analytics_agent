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

MARKET_FRAMING: dict[str, dict[str, str]] = {
    "China A-Share": {
        "en": (
            "This is a **China A-Share** stock. Key market characteristics:\n"
            "- T+1 settlement; no same-day round-trips.\n"
            "- Policy-driven market — CSRC, PBoC liquidity, fiscal stimulus can shift sectors sharply.\n"
            "- Retail-dominated flows (~70%); sentiment and fund flows drive short-term moves.\n"
            "- Benchmarks: CSI 300 (large-cap), SSE Composite (broad).\n"
            "- Stock Connect northbound flows (北向资金) track foreign sentiment.\n"
            "- CNY exchange rate and bond yields influence capital flows."
        ),
        "zh-CN": (
            "这是一只**A股**标的。市场核心特征：\n"
            "- T+1 交收制度，当日买入次日方可卖出。\n"
            "- 政策驱动型市场——证监会、央行流动性操作及财政刺激政策可显著影响行业走向。\n"
            "- 散户主导交易量（约70%），情绪和资金流向引发短期波动。\n"
            "- 参考基准：沪深300（大盘）、上证综指（全市场）。\n"
            "- 沪深港通北向资金流向反映外资情绪。\n"
            "- 人民币汇率与国债收益率影响资金面。"
        ),
    },
    "Hong Kong": {
        "en": (
            "This is a **Hong Kong** stock. Key market characteristics:\n"
            "- Dual market: mainland China exposure via Stock Connect + international capital flows.\n"
            "- HKD-USD peg (7.75-7.85 band) — HKMA intervention affects liquidity.\n"
            "- Benchmarks: Hang Seng Index (HSI), HSTECH.\n"
            "- Sensitive to both China policy shifts and global risk appetite.\n"
            "- Stock Connect southbound flows (南向资金) track mainland sentiment toward HK.\n"
            "- Tax/listing regime changes (e.g., 18C tech listings) can reshape sector dynamics."
        ),
        "zh-CN": (
            "这是一只**港股**标的。市场核心特征：\n"
            "- 双重市场属性：通过沪深港通连接内地 + 国际资本流动。\n"
            "- 港元与美元挂钩（7.75-7.85 区间）的联系汇率制度。\n"
            "- 参考基准：恒生指数、恒生科技指数。\n"
            "- 对中国政策和全球风险偏好均高度敏感。\n"
            "- 南向资金（内地流入香港）追踪内地情绪。\n"
            "- 上市制度改革（如18C特专科技公司）可改变行业格局。"
        ),
    },
    "United States": {
        "en": (
            "This is a **US** stock. Key market characteristics:\n"
            "- Federal Reserve monetary policy (FFR path, QT/QE) is the dominant macro driver.\n"
            "- Earnings-driven catalysts — quarterly EPS beats/misses and guidance revisions drive re-ratings.\n"
            "- Institutional-dominated flows (~70-80%); watch fund flows, options positioning, short interest.\n"
            "- Benchmarks: S&P 500 (large-cap), NASDAQ-100 (tech/growth).\n"
            "- Treasury yields, VIX, and USD index (DXY) set the macro backdrop.\n"
            "- SEC filings (10-K, 10-Q, 8-K) and insider transactions provide transparency."
        ),
        "zh-CN": (
            "这是一只**美股**标的。市场核心特征：\n"
            "- 美联储货币政策（联邦基金利率路径、缩表/扩表）为主要宏观驱动因素。\n"
            "- 盈利驱动型催化剂——季度每股收益超预期/不及预期、前瞻指引调整驱动估值重定。\n"
            "- 机构主导交易量（约70-80%）；关注资金流向、期权仓位、做空比例。\n"
            "- 参考基准：标普500（大盘）、纳斯达克100（科技/成长）。\n"
            "- 美债收益率、VIX 恐慌指数、美元指数构成宏观背景。\n"
            "- SEC 文件（10-K、10-Q、8-K）及内部人交易提供透明度。"
        ),
    },
    "Japan": {
        "en": (
            "This is a **Japan** stock. Key market characteristics:\n"
            "- BOJ monetary policy (rate path, YCC adjustments) and JPY FX are dominant drivers.\n"
            "- TSE corporate governance reforms (P/B > 1x push, share buybacks) reshaping valuations.\n"
            "- Benchmarks: Nikkei 225 (price-weighted), TOPIX (market-cap).\n"
            "- Export-driven sectors sensitive to JPY strength/weakness.\n"
            "- NISA retail flows and GPIF institutional rebalancing are notable catalysts."
        ),
        "zh-CN": (
            "这是一只**日股**标的。市场核心特征：\n"
            "- 日本央行货币政策（利率路径、YCC 调整）和日元汇率为主要驱动因素。\n"
            "- 东证所企业治理改革（P/B > 1 倍推动、股份回购）重塑估值体系。\n"
            "- 参考基准：日经225（价格加权）、东证指数（市值加权）。\n"
            "- 出口导向型行业对日元走弱/走强高度敏感。\n"
            "- NISA 零售资金和 GPIF 机构再平衡是重要资金面催化剂。"
        ),
    },
    "South Korea": {
        "en": (
            "This is a **South Korea** stock. Key market characteristics:\n"
            "- Bank of Korea (BoK) rate decisions and KRW FX are key macro drivers.\n"
            "- Heavy semiconductor/tech concentration; Samsung + SK Hynix dominate KOSPI.\n"
            "- \"Korea Discount\" — conglomerate governance, inheritance tax, and chaebol reform themes.\n"
            "- Benchmarks: KOSPI (main board), KOSDAQ (tech growth).\n"
            "- Short-selling bans and regulatory interventions can distort price discovery."
        ),
        "zh-CN": (
            "这是一只**韩股**标的。市场核心特征：\n"
            "- 韩国央行利率决策及韩元汇率是核心宏观驱动因素。\n"
            "- 半导体/科技高度集中；三星和 SK 海力士主导 KOSPI。\n"
            "- \"韩国折价\"——财阀治理、遗产税及企业改革主题。\n"
            "- 参考基准：KOSPI（主板）、KOSDAQ（科技成长）。\n"
            "- 做空禁令及监管干预可能扭曲价格发现。"
        ),
    },
    "Taiwan": {
        "en": (
            "This is a **Taiwan** stock. Key market characteristics:\n"
            "- TSMC-heavy (30%+ of TAIEX); semiconductor cycle and global tech capex are key drivers.\n"
            "- Central bank rate decisions and TWD FX matter for export competitiveness.\n"
            "- Cross-strait geopolitics create a persistent risk premium.\n"
            "- Foreign investor flows dominate (~30%+ of turnover); watch ADR arbitrage.\n"
            "- Strong dividend culture; ex-dividend dates cause mechanical index drops."
        ),
        "zh-CN": (
            "这是一只**台股**标的。市场核心特征：\n"
            "- 台积电权重极高（占加权指数30%+）；半导体周期及全球科技资本支出为关键驱动。\n"
            "- 央行利率决策及新台币汇率影响出口竞争力。\n"
            "- 两岸地缘政治构成持续性风险溢价。\n"
            "- 外资主导交易量（约30%+）；关注 ADR 套利。\n"
            "- 高股息文化；除权除息日导致指数技术性下跌。"
        ),
    },
    "Canada": {
        "en": (
            "This is a **Canada** stock. Key market characteristics:\n"
            "- Bank of Canada (BoC) rate path and CAD FX tied to commodity prices.\n"
            "- Heavy resources/financials concentration; S&P/TSX Composite benchmark.\n"
            "- Oil sands and mining exposure make commodity super-cycles relevant.\n"
            "- US-Canada trade integration — USMCA, tariffs, and cross-border flows.\n"
            "- Housing market dynamics frequently spill into the financial sector."
        ),
    },
    "United Kingdom": {
        "en": (
            "This is a **UK** stock. Key market characteristics:\n"
            "- Bank of England (BoE) MPC rate decisions and GBP FX.\n"
            "- FTSE 100 is heavily international (mining, energy, pharma) — GBP weakness boosts earnings.\n"
            "- Post-Brexit regulatory divergence; UK listings reform (FinTech, life sciences).\n"
            "- Stamp duty (0.5% on share purchases) creates friction for short-term trading."
        ),
    },
    "Germany": {
        "en": (
            "This is a **Germany** stock. Key market characteristics:\n"
            "- ECB monetary policy (deposit rate, PEPP) across Eurozone.\n"
            "- DAX 40 benchmark; export-driven industrial/auto concentration.\n"
            "- Energy transition (Energiewende) and China demand are key macro themes.\n"
            "- Fiscal policy debates (debt brake reform) can create sectoral shifts."
        ),
    },
    "France": {
        "en": (
            "This is a **France** stock. Key market characteristics:\n"
            "- ECB monetary policy and EUR FX are shared Eurozone drivers.\n"
            "- CAC 40 benchmark; luxury goods (LVMH, Hermes) and energy (TotalEnergies) heavy.\n"
            "- French fiscal policy and political risk premium around elections.\n"
            "- EU regulatory environment (MiFID II, ESG/SFDR) shapes market structure."
        ),
    },
    "Switzerland": {
        "en": (
            "This is a **Switzerland** stock. Key market characteristics:\n"
            "- SNB monetary policy and CHF (safe-haven currency) strength.\n"
            "- SMI benchmark; pharma (Novartis, Roche) and financials (UBS) dominant.\n"
            "- Negative interest rate history shapes unique equity dynamics.\n"
            "- Banking secrecy reforms and EU bilateral agreements influence flows."
        ),
    },
    "Italy": {
        "en": (
            "This is an **Italy** stock. Key market characteristics:\n"
            "- ECB monetary policy shared across Eurozone.\n"
            "- FTSE MIB benchmark; banking and energy concentration.\n"
            "- BTP-Bund spread as key domestic risk barometer.\n"
            "- EU Recovery Fund (PNRR) disbursement creates fiscal tailwind."
        ),
    },
    "Spain": {
        "en": (
            "This is a **Spain** stock. Key market characteristics:\n"
            "- ECB monetary policy; IBEX 35 benchmark.\n"
            "- Banking (Santander, BBVA) and utilities concentration.\n"
            "- Tourism and services sensitivity to European demand cycles.\n"
            "- EU recovery funds and domestic political dynamics."
        ),
    },
    "Netherlands": {
        "en": (
            "This is a **Netherlands** stock. Key market characteristics:\n"
            "- ECB monetary policy; AEX benchmark.\n"
            "- Tech/semiconductor heavy (ASML, ASM International) — global chip cycle exposure.\n"
            "- Benign corporate governance and tax treaty network attract multinational listings.\n"
            "- Small, open economy sensitive to global trade volumes."
        ),
    },
    "Singapore": {
        "en": (
            "This is a **Singapore** stock. Key market characteristics:\n"
            "- MAS manages via SGD NEER (exchange rate band) rather than interest rates.\n"
            "- Defensive, yield-oriented market — REITs and banks dominate STI.\n"
            "- ASEAN gateway; sensitive to regional trade and China demand.\n"
            "- Strong regulatory environment; lower volatility profile."
        ),
    },
    "Australia": {
        "en": (
            "This is an **Australia** stock. Key market characteristics:\n"
            "- RBA cash rate and AUD FX (commodity currency) are key drivers.\n"
            "- Resources-heavy ASX 200 — BHP, Rio Tinto dominate alongside Big Four banks.\n"
            "- China demand (iron ore, LNG) is the single biggest external driver.\n"
            "- Superannuation (pension) system creates large domestic institutional flows."
        ),
    },
    "Europe": {
        "en": (
            "This is a **European** stock. Key market characteristics:\n"
            "- ECB monetary policy (deposit rate, quantitative tightening) is the dominant regional driver.\n"
            "- EUR FX and EU economic sentiment indices set the macro backdrop.\n"
            "- EU regulatory framework (MiFID II, SFDR/ESG, CSRD) shapes market structure.\n"
            "- Benchmarks: STOXX 600 (pan-European), plus national indices (DAX, CAC 40, AEX, etc.).\n"
            "- Energy transition and EU Green Deal create sector-specific policy tailwinds."
        ),
    },
}

DEFAULT_MARKET_FRAMING: dict[str, str] = {
    "en": (
        "No specific market framing is available for this region. "
        "Use global macro context (central bank policy, currency, sector trends) "
        "and the benchmark index referenced in the data above."
    ),
}


def _get_market_framing(market_info: dict | None, language: str) -> str:
    """Get region-specific market framing text for prompt injection."""
    if market_info is None:
        return DEFAULT_MARKET_FRAMING.get("en", "")
    region = market_info.get("region", "")
    framing = MARKET_FRAMING.get(region, {})
    return framing.get(language) or framing.get("en") or DEFAULT_MARKET_FRAMING.get("en", "")


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


def build_synthesize_prompt(symbol: str, enriched_data: str, current_date: str, language: str, market_info: dict | None = None) -> str:
    """Build the synthesize prompt with language-appropriate structure."""
    instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["en"])
    structure = SYNTHESIZE_STRUCTURE.get(language, SYNTHESIZE_STRUCTURE["en"])
    framing = _get_market_framing(market_info, language)

    return f"""{instruction}

You are a professional financial analyst. Write a comprehensive analysis of {symbol} based on the data collected below.

Today is {current_date}.

{enriched_data}

---
**Market Context Note:**
{framing}
---

{structure}"""


TOOL_REGISTRY = """
Core data (already collected — do NOT re-request):
  fetch_market_data → price, metrics, fundamentals, 52W range, market index
  fetch_macro_research → macro news, sector trends, policy updates
  fetch_sentiment_news → news articles grouped by category, sentiment
  fetch_capital_flow → Stock Connect capital flow (沪深港通), auto-collected for CN/HK markets
  fetch_us_fundamentals → analyst consensus, insider trades, institutional ownership, earnings calendar, recent SEC filings. Auto-collected for US markets.

Supplementary tools you may plan:
- fetch_price_history(symbol, period): OHLCV price history. period: 1mo, 6mo, 1y, 5y, max
- calculate_technicals(symbol): SMA, EMA, RSI, volatility from price history. Prices are auto-wired from the previous fetch_price_history result — do NOT pass a "prices" argument, just pass {"symbol": "..."}.
- fetch_cn_market_sentiment(symbol): CN/HK market sentiment, sector fund flow, Dragon Tiger Board (龙虎榜), top capital flow leaders. Only works for China A-Share and Hong Kong markets.
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
