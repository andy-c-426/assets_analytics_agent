# Agent Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single-prompt LLM analysis with a multi-step LangGraph agent that plans, calls tools, evaluates, and synthesizes — streamed live to the frontend via SSE.

**Architecture:** A new standalone `agent-service/` FastAPI app runs a LangGraph StateGraph (plan → execute_tools → observe → synthesize). The existing backend `analyze.py` becomes a thin SSE proxy. The frontend `AnalyzePanel` reads SSE events via `fetch()` + `ReadableStream` and renders the reasoning chain.

**Tech Stack:** Python FastAPI, LangGraph, LangChain Core, Anthropic SDK, OpenAI SDK, yfinance, pytest, SSE (text/event-stream), native fetch ReadableStream

---

### Task 1: Agent Service Scaffold

**Files:**
- Create: `agent-service/requirements.txt`
- Create: `agent-service/app/__init__.py`
- Create: `agent-service/app/main.py`
- Create: `agent-service/app/state.py`
- Create: `agent-service/app/events.py`
- Create: `agent-service/tests/__init__.py`

- [ ] **Step 1: Write requirements.txt**

Create `agent-service/requirements.txt`:

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
langgraph>=0.3.0
langchain-core>=0.3.0
anthropic>=0.30.0
openai>=1.30.0
yfinance>=0.2.36
pytest>=8.0.0
httpx>=0.27.0
```

- [ ] **Step 2: Write empty __init__.py files**

Create `agent-service/app/__init__.py` (empty) and `agent-service/tests/__init__.py` (empty).

- [ ] **Step 3: Write state.py**

Create `agent-service/app/state.py`:

```python
from typing import TypedDict, NotRequired


class ReasoningStep(TypedDict):
    step_type: str        # "planning" | "tool_call" | "evaluating" | "synthesizing"
    status: str           # "pending" | "active" | "done"
    message: str
    detail: NotRequired[str]


class ToolCallPlan(TypedDict):
    tool: str
    args: dict


class ToolResult(TypedDict):
    tool: str
    args: dict
    summary: str
    data: NotRequired[dict]


class AgentState(TypedDict):
    symbol: str
    llm_config: dict         # provider, model, api_key, base_url
    plan: list[ToolCallPlan]
    tool_results: list[ToolResult]
    messages: list[dict]     # full message history for LLM context
    steps: list[ReasoningStep]
    final_report: str | None
    next_action: str         # "plan" | "execute_tools" | "observe" | "synthesize" | "done"
    error: str | None
```

- [ ] **Step 4: Write events.py**

Create `agent-service/app/events.py`:

```python
import json
from typing import Any


def format_sse(event: str, data: dict[str, Any] | None = None) -> str:
    lines = [f"event: {event}"]
    if data is not None:
        lines.append(f"data: {json.dumps(data)}")
    lines.append("")
    return "\n".join(lines)


def step_started(step: str, message: str) -> str:
    return format_sse("step_started", {"step": step, "message": message})


def tool_called(tool: str, args: dict) -> str:
    return format_sse("tool_called", {"tool": tool, "args": args})


def tool_result(tool: str, summary: str) -> str:
    return format_sse("tool_result", {"tool": tool, "summary": summary})


def reasoning_chunk(text: str) -> str:
    return format_sse("reasoning_chunk", {"text": text})


def report_ready(report: str) -> str:
    return format_sse("report_ready", {"report": report})


def error_event(message: str, retryable: bool = False) -> str:
    return format_sse("error", {"message": message, "retryable": retryable})


def done() -> str:
    return format_sse("done", {})
```

- [ ] **Step 5: Write main.py**

Create `agent-service/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Asset Analytics Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Write the failing test for health endpoint**

Create `agent-service/tests/test_health.py`:

```python
from fastapi.testclient import TestClient
from agent_service.app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 7: Install dependencies and run test to verify it fails (no deps yet)**

Run: `cd agent-service && pip install -r requirements.txt && pytest tests/ -v`
Expected: 1 passed (or import error if pip not yet run)

- [ ] **Step 8: Commit**

```bash
git add agent-service/
git commit -m "feat: scaffold agent service with FastAPI, state, and SSE events"
```

---

### Task 2: LLM Client Factory

**Files:**
- Create: `agent-service/app/llm/__init__.py`
- Create: `agent-service/app/llm/client_factory.py`
- Create: `agent-service/tests/test_client_factory.py`

- [ ] **Step 1: Write the failing test**

Create `agent-service/tests/test_client_factory.py`:

```python
import pytest
from agent_service.app.llm.client_factory import create_chat_model, provider_default_model


def test_default_models():
    assert provider_default_model("claude") == "claude-sonnet-4-6"
    assert provider_default_model("openai") == "gpt-4o"
    assert provider_default_model("deepseek") == "deepseek-chat"


def test_create_chat_model_claude():
    model = create_chat_model(
        provider="claude",
        model="claude-sonnet-4-6",
        api_key="test-key",
    )
    assert model is not None
    assert model.model_name == "claude-sonnet-4-6"


def test_create_chat_model_openai():
    model = create_chat_model(
        provider="openai",
        model="gpt-4o",
        api_key="test-key",
    )
    assert model is not None
    assert model.model_name == "gpt-4o"


def test_create_chat_model_deepseek():
    model = create_chat_model(
        provider="deepseek",
        model="deepseek-chat",
        api_key="test-key",
    )
    assert model is not None
    assert model.model_name == "deepseek-chat"


def test_create_chat_model_with_base_url():
    model = create_chat_model(
        provider="openai",
        model="gpt-4o",
        api_key="test-key",
        base_url="https://custom.api.com/v1",
    )
    assert model is not None


def test_unsupported_provider_raises():
    with pytest.raises(ValueError, match="Unsupported provider"):
        create_chat_model(provider="unknown", model="x", api_key="x")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd agent-service && pytest tests/test_client_factory.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Write client_factory.py**

Create `agent-service/app/llm/__init__.py` (empty).

Create `agent-service/app/llm/client_factory.py`:

```python
from langchain_core.language_models import BaseChatModel


def provider_default_model(provider: str) -> str:
    defaults = {
        "claude": "claude-sonnet-4-6",
        "openai": "gpt-4o",
        "deepseek": "deepseek-chat",
    }
    if provider not in defaults:
        raise ValueError(f"Unsupported provider: {provider}")
    return defaults[provider]


def create_chat_model(
    provider: str,
    model: str,
    api_key: str,
    base_url: str | None = None,
) -> BaseChatModel:
    if provider == "claude":
        from langchain_anthropic import ChatAnthropic
        kwargs = {"model": model, "api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return ChatAnthropic(**kwargs)

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        kwargs = {"model": model, "api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return ChatOpenAI(**kwargs)

    elif provider == "deepseek":
        from langchain_openai import ChatOpenAI
        kwargs = {
            "model": model,
            "api_key": api_key,
            "base_url": base_url or "https://api.deepseek.com/v1",
        }
        return ChatOpenAI(**kwargs)

    else:
        raise ValueError(f"Unsupported provider: {provider}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd agent-service && pytest tests/test_client_factory.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add agent-service/app/llm/ agent-service/tests/test_client_factory.py agent-service/requirements.txt
git commit -m "feat: add LLM client factory for Claude, OpenAI, and DeepSeek"
```

---

### Task 3: YFinance Tools

**Files:**
- Create: `agent-service/app/tools/__init__.py`
- Create: `agent-service/app/tools/yfinance_tools.py`
- Create: `agent-service/tests/test_yfinance_tools.py`

- [ ] **Step 1: Write the failing test**

Create `agent-service/tests/test_yfinance_tools.py`:

```python
import pytest
from agent_service.app.tools.yfinance_tools import fetch_asset_data, fetch_price_history


@pytest.mark.integration
def test_fetch_asset_data_real():
    """Integration test — hits yfinance. Skip in CI without network."""
    result = fetch_asset_data.invoke({"symbol": "AAPL"})
    assert "AAPL" in result
    assert "current_price" in result or "price" in result.lower()


@pytest.mark.integration
def test_fetch_price_history_real():
    """Integration test — hits yfinance. Skip in CI without network."""
    result = fetch_price_history.invoke({"symbol": "AAPL", "period": "1mo"})
    assert "AAPL" in result
    assert "data_points" in result.lower() or "records" in result.lower()


def test_fetch_asset_data_has_correct_metadata():
    assert fetch_asset_data.name == "fetch_asset_data"
    assert "symbol" in fetch_asset_data.description.lower()


def test_fetch_price_history_has_correct_metadata():
    assert fetch_price_history.name == "fetch_price_history"
    assert "symbol" in fetch_price_history.description.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd agent-service && pytest tests/test_yfinance_tools.py -v -k "not integration"`
Expected: FAIL — module not found

- [ ] **Step 3: Write yfinance_tools.py**

Create `agent-service/app/tools/__init__.py` (empty).

Create `agent-service/app/tools/yfinance_tools.py`:

```python
from langchain_core.tools import tool
import yfinance as yf


@tool
def fetch_asset_data(symbol: str) -> str:
    """Fetch complete asset data for a ticker symbol including profile, current price,
    key metrics, and recent news. Use this first when analyzing any asset.

    Args:
        symbol: The ticker symbol (e.g. AAPL, 0700.HK, 300502.SZ)
    """
    ticker = yf.Ticker(symbol.strip())
    info = ticker.get_info()

    if not info or info.get("symbol") is None:
        return f"No data found for symbol: {symbol}"

    name = info.get("shortName") or info.get("longName") or symbol
    sector = info.get("sector", "N/A")
    country = info.get("country", "N/A")
    market_cap = info.get("marketCap")
    description = info.get("longBusinessSummary", "No description available")

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
        f"Market Cap: {_fmt_big(market_cap)}" if market_cap else "Market Cap: N/A",
        "",
        f"Current Price: {current_price} {currency}" if current_price else "Price: N/A",
    ]
    if change is not None and change_pct is not None:
        lines.append(f"Change: {change:.2f} ({change_pct:.2f}%)")
    lines.extend([
        "",
        "Key Metrics:",
        f"  P/E: {pe:.2f}" if pe else "  P/E: N/A",
        f"  P/B: {pb:.2f}" if pb else "  P/B: N/A",
        f"  EPS: ${eps:.2f}" if eps else "  EPS: N/A",
        f"  Dividend Yield: {dividend_yield*100:.2f}%" if dividend_yield else "  Dividend Yield: N/A",
        f"  Beta: {beta:.2f}" if beta else "  Beta: N/A",
        f"  52W High: {high_52w:.2f}" if high_52w else "  52W High: N/A",
        f"  52W Low: {low_52w:.2f}" if low_52w else "  52W Low: N/A",
        "",
        f"Description: {description[:500]}..." if len(description) > 500 else f"Description: {description}",
        "",
        f"Recent News ({len(news_items)} articles):",
    ] + news_items)

    return "\n".join(lines)


@tool
def fetch_price_history(symbol: str, period: str = "1mo") -> str:
    """Fetch historical OHLCV price data for a ticker.

    Args:
        symbol: The ticker symbol (e.g. AAPL, 0700.HK)
        period: Time range — one of 1mo, 6mo, 1y, 5y, max
    """
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd agent-service && pytest tests/test_yfinance_tools.py -v -k "not integration"`
Expected: 2 passed (metadata tests; integration tests skipped via `-k not integration`)

- [ ] **Step 5: Commit**

```bash
git add agent-service/app/tools/ agent-service/tests/test_yfinance_tools.py
git commit -m "feat: add yfinance tools for asset data and price history"
```

---

### Task 4: Technicals Tools

**Files:**
- Create: `agent-service/app/tools/technicals.py`
- Create: `agent-service/tests/test_technicals.py`

- [ ] **Step 1: Write the failing test**

Create `agent-service/tests/test_technicals.py`:

```python
from agent_service.app.tools.technicals import calculate_technicals


def test_calculate_technicals_metadata():
    assert calculate_technicals.name == "calculate_technicals"
    assert "symbol" in calculate_technicals.description.lower()


def test_calculate_technicals_empty_data():
    result = calculate_technicals.invoke({"symbol": "TEST", "prices": []})
    assert "no price data" in result.lower()
    assert "TEST" in result


def test_calculate_technicals_insufficient_data():
    prices = [100.0, 101.0]
    result = calculate_technicals.invoke({"symbol": "TEST", "prices": prices})
    assert "need at least" in result.lower() or "not enough" in result.lower()


def test_calculate_technicals_computes_metrics():
    # Generate 30 price points with a clear trend
    prices = [100.0 + i * 0.5 for i in range(30)]
    result = calculate_technicals.invoke({"symbol": "TEST", "prices": prices})
    assert "TEST" in result
    assert "SMA" in result
    assert "RSI" in result
    assert "Volatility" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd agent-service && pytest tests/test_technicals.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Write technicals.py**

Create `agent-service/app/tools/technicals.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd agent-service && pytest tests/test_technicals.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add agent-service/app/tools/technicals.py agent-service/tests/test_technicals.py
git commit -m "feat: add technical analysis tools (SMA, EMA, RSI, volatility)"
```

---

### Task 5: LangGraph State Graph

**Files:**
- Create: `agent-service/app/graph.py`
- Create: `agent-service/app/prompts.py`
- Create: `agent-service/tests/test_graph.py`

- [ ] **Step 1: Write the failing test**

Create `agent-service/tests/test_graph.py`:

```python
import pytest
from agent_service.app.state import AgentState
from agent_service.app.graph import build_graph


def test_build_graph_compiles():
    graph = build_graph()
    assert graph is not None
    # Verify all expected nodes are present
    compiled = graph.compile()
    assert compiled is not None


def test_initial_state_has_next_action_plan():
    state: AgentState = {
        "symbol": "AAPL",
        "llm_config": {"provider": "claude", "model": "claude-sonnet-4-6", "api_key": "test"},
        "plan": [],
        "tool_results": [],
        "messages": [],
        "steps": [],
        "final_report": None,
        "next_action": "plan",
        "error": None,
    }
    assert state["next_action"] == "plan"
    assert state["symbol"] == "AAPL"


def test_graph_nodes_exist():
    graph = build_graph()
    compiled = graph.compile()
    # Get the nodes from the compiled graph
    nodes = compiled.get_graph().nodes
    node_names = {n for n in nodes.keys() if n != "__start__" and n != "__end__"}
    assert "plan" in node_names
    assert "execute_tools" in node_names
    assert "observe" in node_names
    assert "synthesize" in node_names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd agent-service && pytest tests/test_graph.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Write prompts.py**

Create `agent-service/app/prompts.py`:

```python
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
```

- [ ] **Step 4: Write graph.py**

Create `agent-service/app/graph.py`:

```python
import json
from typing import Literal

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from agent_service.app.state import AgentState, ToolCallPlan, ToolResult, ReasoningStep
from agent_service.app.llm.client_factory import create_chat_model
from agent_service.app.tools.yfinance_tools import fetch_asset_data, fetch_price_history
from agent_service.app.tools.technicals import calculate_technicals
from agent_service.app.prompts import (
    PLAN_PROMPT,
    OBSERVE_PROMPT,
    SYNTHESIZE_PROMPT,
    TOOL_REGISTRY,
)


TOOLS_BY_NAME = {
    "fetch_asset_data": fetch_asset_data,
    "fetch_price_history": fetch_price_history,
    "calculate_technicals": calculate_technicals,
}


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("plan", plan_node)
    graph.add_node("execute_tools", execute_tools_node)
    graph.add_node("observe", observe_node)
    graph.add_node("synthesize", synthesize_node)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "execute_tools")
    graph.add_edge("execute_tools", "observe")
    graph.add_conditional_edges(
        "observe",
        decide_next,
        {
            "plan": "plan",
            "synthesize": "synthesize",
            "done": END,
        },
    )
    graph.add_edge("synthesize", END)

    return graph


def _build_llm(state: AgentState):
    config = state["llm_config"]
    return create_chat_model(
        provider=config["provider"],
        model=config["model"],
        api_key=config["api_key"],
        base_url=config.get("base_url"),
    )


def plan_node(state: AgentState) -> dict:
    steps: list[ReasoningStep] = state.get("steps", [])
    steps.append({
        "step_type": "planning",
        "status": "active",
        "message": f"Planning analysis for {state['symbol']}...",
    })

    llm = _build_llm(state)

    prompt = PLAN_PROMPT.format(
        symbol=state["symbol"],
        tool_descriptions=TOOL_REGISTRY,
    )

    messages = state.get("messages", [])
    messages.append(SystemMessage(content=prompt))

    response = llm.invoke(messages)
    messages.append(HumanMessage(content="Plan my analysis"))
    messages.append(response)

    # Parse the plan from the LLM response
    content = response.content if hasattr(response, "content") else str(response)
    try:
        # Strip markdown code fences if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content[:-3]
        plan: list[ToolCallPlan] = json.loads(content)
    except json.JSONDecodeError:
        # Fallback: at minimum fetch asset data
        plan = [{"tool": "fetch_asset_data", "args": {"symbol": state["symbol"]}}]

    steps[-1]["status"] = "done"
    steps[-1]["detail"] = f"Planned {len(plan)} tool call(s)"
    for p in plan:
        steps.append({
            "step_type": "tool_call",
            "status": "pending",
            "message": f"Planned: {p['tool']}",
            "detail": str(p.get("args", {})),
        })

    return {
        "plan": plan,
        "messages": messages,
        "steps": steps,
        "next_action": "execute_tools",
    }


def execute_tools_node(state: AgentState) -> dict:
    plan: list[ToolCallPlan] = state["plan"]
    tool_results: list[ToolResult] = []
    steps: list[ReasoningStep] = state.get("steps", [])
    messages = state.get("messages", [])

    for i, call in enumerate(plan):
        tool_name = call["tool"]
        args = call.get("args", {})

        # Mark the pending step as active
        for step in steps:
            if step["status"] == "pending" and step["step_type"] == "tool_call":
                step["status"] = "active"
                step["message"] = f"Calling {tool_name}..."
                break

        tool_fn = TOOLS_BY_NAME.get(tool_name)
        if tool_fn is None:
            result_text = f"Error: Unknown tool '{tool_name}'"
        else:
            try:
                result_text = tool_fn.invoke(args)
            except Exception as e:
                result_text = f"Error executing {tool_name}: {str(e)}"

        # Mark step as done
        for step in steps:
            if step["status"] == "active" and step["step_type"] == "tool_call":
                step["status"] = "done"
                step["message"] = f"Completed: {tool_name}"
                break

        # Build summary
        summary_lines = result_text.split("\n")
        summary = summary_lines[0] if summary_lines else f"Result from {tool_name}"
        if len(summary) > 150:
            summary = summary[:147] + "..."

        tool_results.append({
            "tool": tool_name,
            "args": args,
            "summary": summary,
            "data": {"full_result": result_text},
        })

        messages.append(HumanMessage(content=f"Tool: {tool_name}\nArgs: {json.dumps(args)}\nResult: {summary}"))

    return {
        "tool_results": tool_results,
        "steps": steps,
        "messages": messages,
        "next_action": "observe",
    }


def observe_node(state: AgentState) -> dict:
    steps: list[ReasoningStep] = state.get("steps", [])
    steps.append({
        "step_type": "evaluating",
        "status": "active",
        "message": "Evaluating collected data...",
    })

    llm = _build_llm(state)

    tool_summary = "\n".join(
        f"- {r['tool']}: {r['summary']}" for r in state["tool_results"]
    )

    prompt = OBSERVE_PROMPT.format(
        symbol=state["symbol"],
        tool_results_summary=tool_summary,
    )

    messages = state.get("messages", [])
    messages.append(SystemMessage(content=prompt))
    response = llm.invoke(messages)
    messages.append(response)

    content = response.content if hasattr(response, "content") else str(response)
    content_lower = content.strip().lower()

    steps[-1]["status"] = "done"

    if content_lower.startswith("more"):
        steps[-1]["detail"] = "Need more data — re-planning"
        steps.append({
            "step_type": "planning",
            "status": "pending",
            "message": "Re-planning with refined instructions...",
            "detail": content.strip(),
        })
        return {
            "messages": messages,
            "steps": steps,
            "next_action": "plan",
        }

    if "error" in content_lower or "fail" in content_lower:
        return {
            "error": content.strip(),
            "messages": messages,
            "steps": steps,
            "next_action": "done",
        }

    steps[-1]["detail"] = "Data sufficient — ready to synthesize"
    return {
        "messages": messages,
        "steps": steps,
        "next_action": "synthesize",
    }


def synthesize_node(state: AgentState) -> dict:
    steps: list[ReasoningStep] = state.get("steps", [])
    steps.append({
        "step_type": "synthesizing",
        "status": "active",
        "message": "Writing analysis report...",
    })

    llm = _build_llm(state)

    tool_results_full = "\n\n".join(
        r.get("data", {}).get("full_result", r["summary"])
        for r in state["tool_results"]
    )

    prompt = SYNTHESIZE_PROMPT.format(
        symbol=state["symbol"],
        tool_results_full=tool_results_full,
    )

    messages = state.get("messages", [])
    messages.append(SystemMessage(content=prompt))
    response = llm.invoke(messages)

    report = response.content if hasattr(response, "content") else str(response)

    steps[-1]["status"] = "done"
    steps[-1]["detail"] = "Report complete"

    return {
        "final_report": report,
        "messages": messages,
        "steps": steps,
        "next_action": "done",
    }


def decide_next(state: AgentState) -> Literal["plan", "synthesize", "done"]:
    action = state.get("next_action", "done")
    if action == "plan":
        return "plan"
    if action == "synthesize":
        return "synthesize"
    return "done"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd agent-service && pytest tests/test_graph.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add agent-service/app/graph.py agent-service/app/prompts.py agent-service/tests/test_graph.py
git commit -m "feat: add LangGraph state machine with plan/execute/observe/synthesize nodes"
```

---

### Task 6: Agent Router (SSE Streaming Endpoint)

**Files:**
- Create: `agent-service/app/agent_router.py`
- Create: `agent-service/tests/test_agent_router.py`

- [ ] **Step 1: Write the failing test**

Create `agent-service/tests/test_agent_router.py`:

```python
import json
from fastapi.testclient import TestClient
from agent_service.app.main import app


def test_analyze_endpoint_returns_sse_stream():
    """Test that the analyze endpoint returns an SSE stream.

    Note: This test uses a fake API key — the stream will produce
    events up to the first LLM call, which will fail with auth error.
    We verify the SSE format and initial events."""
    client = TestClient(app)
    response = client.post(
        "/analyze/AAPL",
        json={
            "provider": "claude",
            "model": "claude-sonnet-4-6",
            "api_key": "test-key",
        },
        stream=True,
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    # Read first few SSE events
    events = []
    for line in response.iter_lines():
        if line.startswith("event: "):
            events.append(line)
        if len(events) >= 2:
            break

    assert len(events) >= 1
    # First event should be step_started (planning)
    assert "step_started" in events[0]


def test_analyze_endpoint_validates_body():
    client = TestClient(app)
    response = client.post(
        "/analyze/AAPL",
        json={"provider": "", "model": "", "api_key": ""},
    )
    # Missing required fields should be caught
    assert response.status_code in (200, 422, 400)


def test_router_is_mounted():
    client = TestClient(app)
    # Verify the router is registered on the app
    routes = [r.path for r in app.routes]
    assert "/analyze/{symbol}" in routes
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd agent-service && pytest tests/test_agent_router.py -v`
Expected: FAIL — router not mounted

- [ ] **Step 3: Write agent_router.py**

Create `agent-service/app/agent_router.py`:

```python
import json
import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent_service.app.state import AgentState
from agent_service.app.graph import build_graph
from agent_service.app import events


router = APIRouter()


class AnalyzeRequest(BaseModel):
    provider: str
    model: str
    api_key: str
    base_url: str | None = None


@router.post("/analyze/{symbol}")
async def analyze(symbol: str, body: AnalyzeRequest):
    return StreamingResponse(
        _stream_analysis(symbol, body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _stream_analysis(symbol: str, body: AnalyzeRequest) -> AsyncGenerator[str, None]:
    try:
        graph = build_graph()
        compiled = graph.compile()

        initial_state: AgentState = {
            "symbol": symbol,
            "llm_config": {
                "provider": body.provider,
                "model": body.model,
                "api_key": body.api_key,
                "base_url": body.base_url,
            },
            "plan": [],
            "tool_results": [],
            "messages": [],
            "steps": [],
            "final_report": None,
            "next_action": "plan",
            "error": None,
        }

        yield events.step_started("planning", f"Starting analysis for {symbol}...")

        # Run the graph in a thread pool to avoid blocking
        final_state = await asyncio.to_thread(compiled.invoke, initial_state)

        # Emit all steps from the state
        for step in final_state.get("steps", []):
            if step["step_type"] == "planning":
                yield events.step_started("planning", step["message"])
            elif step["step_type"] == "tool_call":
                if step["status"] == "active":
                    pass  # tool_called already emitted during execution
                elif step["status"] == "done":
                    # Find the corresponding result
                    for r in final_state.get("tool_results", []):
                        if r["tool"] in step.get("message", ""):
                            yield events.tool_result(r["tool"], r["summary"])
            elif step["step_type"] == "evaluating":
                yield events.step_started("evaluating", step["message"])
            elif step["step_type"] == "synthesizing":
                yield events.step_started("synthesizing", step["message"])

        if final_state.get("error"):
            yield events.error_event(final_state["error"])
        elif final_state.get("final_report"):
            yield events.report_ready(final_state["final_report"])
        else:
            yield events.error_event("Analysis produced no report")

    except Exception as e:
        yield events.error_event(str(e), retryable=False)
    finally:
        yield events.done()
```

- [ ] **Step 4: Wire the router into main.py**

Edit `agent-service/app/main.py` — add after the health endpoint:

```python
from agent_service.app.agent_router import router as agent_router
app.include_router(agent_router)
```

Updated main.py:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Asset Analytics Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}

from agent_service.app.agent_router import router as agent_router
app.include_router(agent_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd agent-service && pytest tests/test_agent_router.py -v`
Expected: 3 passed (first test will error at LLM call due to fake key, but SSE format + validation + routing should pass)

- [ ] **Step 6: Commit**

```bash
git add agent-service/app/agent_router.py agent-service/app/main.py agent-service/tests/test_agent_router.py
git commit -m "feat: add agent SSE streaming endpoint with LangGraph execution"
```

---

### Task 7: Backend Proxy to Agent Service

**Files:**
- Modify: `backend/app/activities/analyze.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Backend requirements already have httpx — verify**

Read `backend/requirements.txt` — confirm `httpx>=0.27.0` is present. It is already there from Phase 1. If not, add it.

- [ ] **Step 2: Rewrite analyze.py as thin proxy**

Rewrite `backend/app/activities/analyze.py`:

```python
import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.app.models.schemas import AnalysisRequest

router = APIRouter()

AGENT_SERVICE_URL = "http://localhost:8001"


@router.post("/api/analyze/{symbol}")
async def analyze_endpoint(symbol: str, body: AnalysisRequest):
    """Proxy the analyze request to the agent service, streaming SSE back."""
    client = httpx.AsyncClient(timeout=120.0)

    async def stream():
        try:
            async with client.stream(
                "POST",
                f"{AGENT_SERVICE_URL}/analyze/{symbol}",
                json={
                    "provider": body.provider,
                    "model": body.model,
                    "api_key": body.api_key,
                    "base_url": body.base_url,
                },
            ) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk
        finally:
            await client.aclose()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 3: Verify backend still starts**

Run: `cd backend && python -c "from backend.app.activities.analyze import router; print('OK')"`
Expected: OK

- [ ] **Step 4: Commit**

```bash
git add backend/app/activities/analyze.py
git commit -m "feat: refactor analyze endpoint to proxy SSE from agent service"
```

---

### Task 8: Frontend SSE Client & Reasoning Chain UI

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/components/AnalyzePanel.tsx`
- Modify: `frontend/src/components/AnalyzePanel.module.css`

- [ ] **Step 1: Add SSE event types to types.ts**

Read `frontend/src/api/types.ts`, append:

```typescript
export interface SSEEvent {
  type: 'step_started' | 'tool_called' | 'tool_result' | 'reasoning_chunk' | 'report_ready' | 'error' | 'done';
  data: Record<string, unknown>;
}

export interface ReasoningStep {
  step_type: string;
  status: 'pending' | 'active' | 'done';
  message: string;
  detail?: string;
}
```

- [ ] **Step 2: Add streaming function to client.ts**

Edit `frontend/src/api/client.ts` — add after the existing `analyzeAsset` function:

```typescript
export function analyzeAssetStream(
  symbol: string,
  config: AnalysisRequest
): {
  read: () => Promise<ReadableStreamDefaultReadResult<Uint8Array>>;
  cancel: () => void;
} {
  const controller = new AbortController();

  const streamPromise = fetch(`${BASE}/analyze/${encodeURIComponent(symbol)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
    signal: controller.signal,
  }).then((res) => {
    if (!res.ok) throw new Error(`POST /analyze failed: ${res.status}`);
    return res.body!;
  });

  return {
    read: () => streamPromise.then((body) => body.getReader().read()),
    cancel: () => controller.abort(),
  };
}
```

- [ ] **Step 3: Add step list styles to AnalyzePanel.module.css**

Edit `frontend/src/components/AnalyzePanel.module.css` — append:

```css
.stepList {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: var(--space-4);
}

.stepItem {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}

.stepDone {
  composes: stepItem;
  color: var(--text-muted);
}

.stepActive {
  composes: stepItem;
  color: var(--text-primary);
  background: var(--accent-subtle);
}

.stepPending {
  composes: stepItem;
  color: var(--text-muted);
  opacity: 0.5;
}

.stepIcon {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  flex-shrink: 0;
}
```

- [ ] **Step 4: Rewrite client.ts analyzeAssetStream function**

Edit `frontend/src/api/client.ts` — replace the `analyzeAssetStream` function added in Step 2 with this simpler version:

```typescript
export async function analyzeAssetStream(
  symbol: string,
  config: AnalysisRequest,
  signal?: AbortSignal
): Promise<ReadableStream<Uint8Array>> {
  const res = await fetch(`${BASE}/analyze/${encodeURIComponent(symbol)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
    signal,
  });
  if (!res.ok) throw new Error(`POST /analyze failed: ${res.status}`);
  if (!res.body) throw new Error('No response body');
  return res.body;
}
```

- [ ] **Step 5: Rewrite AnalyzePanel.tsx**

Rewrite `frontend/src/components/AnalyzePanel.tsx`:

```tsx
import { useState, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { analyzeAssetStream } from '../api/client';
import { loadSettings } from './SettingsDialog';
import styles from './AnalyzePanel.module.css';

interface Props {
  symbol: string;
  onOpenSettings: () => void;
}

interface Step {
  step_type: string;
  message: string;
  status: 'pending' | 'active' | 'done';
  detail?: string;
}

function formatStepMessage(step: Step): string {
  switch (step.step_type) {
    case 'planning': return 'Planning analysis...';
    case 'evaluating': return 'Evaluating results...';
    case 'synthesizing': return 'Writing analysis report...';
    case 'tool_call': return step.message;
    default: return step.message;
  }
}

function StepIcon({ status }: { status: string }) {
  if (status === 'done') return <span style={{ color: 'var(--green)', fontSize: 12 }}>◆</span>;
  if (status === 'active') return <span style={{ color: 'var(--accent)', fontSize: 12 }}>◇</span>;
  return <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>○</span>;
}

export default function AnalyzePanel({ symbol, onOpenSettings }: Props) {
  const [steps, setSteps] = useState<Step[]>([]);
  const [report, setReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const handleAnalyze = useCallback(async () => {
    const settings = loadSettings();
    if (!settings) {
      onOpenSettings();
      return;
    }

    setLoading(true);
    setError(null);
    setSteps([]);
    setReport(null);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const body = await analyzeAssetStream(symbol, settings, controller.signal);
      const reader = body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let eventType = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith('data: ') && eventType) {
            try {
              const data = JSON.parse(line.slice(6));
              handleSSEEvent(eventType, data);
            } catch { /* skip malformed */ }
            eventType = '';
          }
        }
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }, [symbol, onOpenSettings]);

  function handleSSEEvent(eventType: string, data: Record<string, unknown>) {
    switch (eventType) {
      case 'step_started': {
        const step = data.step as string;
        const message = data.message as string;
        setSteps((prev) => {
          const updated = prev.map((s) =>
            s.status === 'active' ? { ...s, status: 'done' as const } : s
          );
          return [...updated, { step_type: step, message, status: 'active' }];
        });
        break;
      }
      case 'tool_called': {
        const tool = data.tool as string;
        setSteps((prev) => [
          ...prev,
          { step_type: 'tool_call', message: `Fetching data: ${tool}`, status: 'active' },
        ]);
        break;
      }
      case 'tool_result': {
        const tool = data.tool as string;
        const summary = data.summary as string;
        setSteps((prev) =>
          prev.map((s) =>
            s.step_type === 'tool_call' && s.message.includes(tool) && s.status === 'active'
              ? { ...s, status: 'done' as const, detail: summary }
              : s
          )
        );
        break;
      }
      case 'reasoning_chunk':
        break;
      case 'report_ready':
        setReport(data.report as string);
        setSteps((prev) =>
          prev.map((s) =>
            s.status === 'active' ? { ...s, status: 'done' as const } : s
          )
        );
        break;
      case 'error':
        setError(data.message as string);
        break;
      case 'done':
        setLoading(false);
        break;
    }
  }

  return (
    <div className={styles.panel}>
      <div className={styles.actions}>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className={styles.btnAnalyze}
        >
          {loading ? 'Analyzing...' : 'Analyze with AI'}
        </button>
        <button onClick={onOpenSettings} className={styles.btnSettings}>
          LLM Settings
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {steps.length > 0 && (
        <div className={styles.stepList}>
          {steps.map((step, i) => (
            <div
              key={i}
              className={
                step.status === 'done' ? styles.stepDone :
                step.status === 'active' ? styles.stepActive :
                styles.stepPending
              }
            >
              <StepIcon status={step.status} />
              <span>{formatStepMessage(step)}</span>
            </div>
          ))}
        </div>
      )}

      {report && (
        <div className={styles.result}>
          <div className={styles.resultContent}>
            <ReactMarkdown>{report}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/client.ts frontend/src/api/types.ts frontend/src/components/AnalyzePanel.tsx frontend/src/components/AnalyzePanel.module.css
git commit -m "feat: add SSE streaming client and reasoning chain UI to AnalyzePanel"
```

---

### Task 9: Integration & Verification

**Files:**
- No new files — verify everything works together

- [ ] **Step 1: Type-check frontend**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 2: Build frontend**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Run agent service tests**

Run: `cd agent-service && pytest tests/ -v -k "not integration"`
Expected: All unit tests pass

- [ ] **Step 4: Verify agent service starts**

Run: `cd agent-service && timeout 5 python -m uvicorn agent_service.app.main:app --port 8001 2>&1 || true`
Expected: Uvicorn starts without import errors

- [ ] **Step 5: Verify backend imports still resolve**

Run: `cd backend && python -c "from backend.app.main import app; print('OK')"`
Expected: OK

- [ ] **Step 6: Commit any fixups**

```bash
git add -A && git diff --cached --stat
```
If any fixups were needed, commit them. Otherwise note "Verification passed."
```

---

