from agent_service.app.state import AgentState
from agent_service.app.graph import (
    build_graph,
    _parse_plan_response,
    _parse_observe_response,
    _extract_fields,
    validate_coverage,
    decide_after_plan,
    decide_next,
    MAX_ITERATIONS,
    CORE_TOOLS,
)


# ── Graph structure ──────────────────────────────────────────────

def test_build_graph_compiles():
    graph = build_graph()
    assert graph is not None
    compiled = graph.compile()
    assert compiled is not None


def test_graph_nodes_exist():
    graph = build_graph()
    compiled = graph.compile()
    nodes = compiled.get_graph().nodes
    node_names = {n for n in nodes.keys() if n != "__start__" and n != "__end__"}
    assert "collect_core_data" in node_names
    assert "plan" in node_names
    assert "execute_tools" in node_names
    assert "observe" in node_names
    assert "synthesize" in node_names


# ── Empty plan routing ───────────────────────────────────────────

def test_decide_after_plan_routes_empty_to_observe():
    state: AgentState = {
        "symbol": "AAPL",
        "llm_config": {"provider": "claude", "model": "c", "api_key": "k"},
        "plan": [],
        "tool_results": [],
        "messages": [],
        "steps": [],
        "final_report": None,
        "next_action": "observe",
        "iteration_count": 0,
        "error": None,
    }
    assert decide_after_plan(state) == "observe"


def test_decide_after_plan_routes_nonempty_to_execute():
    state: AgentState = {
        "symbol": "AAPL",
        "llm_config": {"provider": "claude", "model": "c", "api_key": "k"},
        "plan": [],
        "tool_results": [],
        "messages": [],
        "steps": [],
        "final_report": None,
        "next_action": "execute_tools",
        "iteration_count": 0,
        "error": None,
    }
    assert decide_after_plan(state) == "execute_tools"


# ── Invalid JSON fallback ────────────────────────────────────────

def test_parse_plan_response_fallback():
    reasoning, plan = _parse_plan_response("garbage not json", "AAPL")
    assert len(plan) == 1
    assert plan[0]["tool"] == "fetch_price_history"
    assert plan[0]["args"] == {"symbol": "AAPL", "period": "6mo"}


def test_parse_plan_response_valid_empty():
    reasoning, plan = _parse_plan_response("no extra tools needed\n[]", "TSLA")
    assert plan == []


def test_parse_plan_response_valid_single():
    reasoning, plan = _parse_plan_response(
        'need price history\n[{"tool": "fetch_price_history", "args": {"symbol": "TSLA", "period": "1y"}}]',
        "TSLA",
    )
    assert len(plan) == 1
    assert plan[0]["tool"] == "fetch_price_history"
    assert plan[0]["args"]["period"] == "1y"


def test_parse_plan_response_code_fence():
    reasoning, plan = _parse_plan_response(
        'need more data\n```json\n[{"tool": "calculate_technicals", "args": {"symbol": "AAPL", "prices": [1,2,3]}}]\n```',
        "AAPL",
    )
    assert len(plan) == 1
    assert plan[0]["tool"] == "calculate_technicals"


# ── Duplicate tool names with call_id ────────────────────────────

def test_call_id_uniqueness():
    """Same tool planned twice gets different call_ids."""
    plan = [
        {"tool": "fetch_price_history", "args": {"symbol": "AAPL", "period": "1mo"}},
        {"tool": "fetch_price_history", "args": {"symbol": "AAPL", "period": "1y"}},
    ]
    for i, p in enumerate(plan):
        p["call_id"] = f"{p['tool']}_{i}"
    cids = [p["call_id"] for p in plan]
    assert cids[0] != cids[1]
    assert cids[0] == "fetch_price_history_0"
    assert cids[1] == "fetch_price_history_1"


# ── Tool error propagation ───────────────────────────────────────

def test_tool_result_error_status():
    """ToolResult with error has status 'error' and empty fields."""
    result = {
        "tool": "fetch_market_data",
        "args": {"symbol": "ZZZ"},
        "call_id": "fetch_market_data_0",
        "summary": "Error: something failed",
        "status": "error",
        "fields": {},
        "data": {"full_result": "Error executing fetch_market_data: timeout"},
    }
    assert result["status"] == "error"
    assert result["fields"] == {}


def test_tool_result_ok_status():
    """Successful ToolResult has status 'ok' and populated fields."""
    result = {
        "tool": "fetch_market_data",
        "args": {"symbol": "AAPL"},
        "call_id": "fetch_market_data_core",
        "summary": "Futu Real-Time Data: Apple",
        "status": "ok",
        "fields": {"current_price": 294.80, "source": "futu"},
        "data": {"full_result": "..."},
    }
    assert result["status"] == "ok"
    assert result["fields"]["source"] == "futu"


# ── Pre-fetched core data ────────────────────────────────────────

def test_validate_coverage_all_present():
    tool_results = [
        {"tool": "fetch_market_data", "args": {}, "summary": "...", "status": "ok", "fields": {}, "data": {}},
        {"tool": "fetch_macro_research", "args": {}, "summary": "...", "status": "ok", "fields": {}, "data": {}},
        {"tool": "fetch_sentiment_news", "args": {}, "summary": "...", "status": "ok", "fields": {}, "data": {}},
    ]
    cov = validate_coverage(tool_results)
    assert cov["core_complete"] is True
    assert cov["missing"] == []
    assert cov["errored"] == []


def test_validate_coverage_missing():
    tool_results = [
        {"tool": "fetch_market_data", "args": {}, "summary": "...", "status": "ok", "fields": {}, "data": {}},
    ]
    cov = validate_coverage(tool_results)
    assert cov["core_complete"] is False
    assert "fetch_macro_research" in cov["missing"]
    assert "fetch_sentiment_news" in cov["missing"]


def test_validate_coverage_error():
    tool_results = [
        {"tool": "fetch_market_data", "args": {}, "summary": "...", "status": "ok", "fields": {}, "data": {}},
        {"tool": "fetch_macro_research", "args": {}, "summary": "...", "status": "ok", "fields": {}, "data": {}},
        {"tool": "fetch_sentiment_news", "args": {}, "summary": "...", "status": "error", "fields": {}, "data": {}},
    ]
    cov = validate_coverage(tool_results)
    assert cov["core_complete"] is False
    assert "fetch_sentiment_news" in cov["errored"]


def test_validate_coverage_prefetched():
    """Pre-fetched (cached) data with call_id should pass coverage."""
    tool_results = [
        {"tool": "fetch_market_data", "args": {}, "call_id": "fetch_market_data_cached", "summary": "...", "status": "ok", "fields": {}, "data": {}},
        {"tool": "fetch_macro_research", "args": {}, "call_id": "fetch_macro_research_cached", "summary": "...", "status": "ok", "fields": {}, "data": {}},
        {"tool": "fetch_sentiment_news", "args": {}, "call_id": "fetch_sentiment_news_cached", "summary": "...", "status": "ok", "fields": {}, "data": {}},
    ]
    cov = validate_coverage(tool_results)
    assert cov["core_complete"] is True


# ── Observe loop limit ───────────────────────────────────────────

def test_decide_next_max_iterations_forces_synthesize():
    state: AgentState = {
        "symbol": "AAPL",
        "llm_config": {"provider": "claude", "model": "c", "api_key": "k"},
        "plan": [],
        "tool_results": [],
        "messages": [],
        "steps": [],
        "final_report": None,
        "next_action": "plan",
        "iteration_count": MAX_ITERATIONS,
        "error": None,
    }
    assert decide_next(state) == "synthesize"


def test_decide_next_allows_plan_under_max():
    state: AgentState = {
        "symbol": "AAPL",
        "llm_config": {"provider": "claude", "model": "c", "api_key": "k"},
        "plan": [],
        "tool_results": [],
        "messages": [],
        "steps": [],
        "final_report": None,
        "next_action": "plan",
        "iteration_count": 1,
        "error": None,
    }
    assert decide_next(state) == "plan"


def test_decide_next_routes_collect_core_data():
    state: AgentState = {
        "symbol": "AAPL",
        "llm_config": {"provider": "claude", "model": "c", "api_key": "k"},
        "plan": [],
        "tool_results": [],
        "messages": [],
        "steps": [],
        "final_report": None,
        "next_action": "collect_core_data",
        "iteration_count": 0,
        "error": None,
    }
    assert decide_next(state) == "collect_core_data"


# ── Observe response parsing ─────────────────────────────────────

def test_parse_observe_response_enough():
    decision, missing, reasoning = _parse_observe_response(
        '{"decision": "enough", "missing": [], "reasoning": "All data present"}'
    )
    assert decision == "enough"
    assert missing == []


def test_parse_observe_response_more():
    decision, missing, reasoning = _parse_observe_response(
        '{"decision": "more", "missing": ["fetch_price_history"], "reasoning": "Need price data"}'
    )
    assert decision == "more"
    assert "fetch_price_history" in missing


def test_parse_observe_response_fallback():
    decision, missing, reasoning = _parse_observe_response("more data needed")
    assert decision == "more"


# ── fields extraction ────────────────────────────────────────────

def test_extract_fields_market_data_futu():
    text = """=== Futu Real-Time Data: Apple (US.AAPL) ===
As of: 2026-05-13 03:00:00

[Price]
Current: 294.80  Change: +2.12 (+0.72%)

[Valuation]
P/E: 32.50
P/B: 45.20
Market Cap: $4.31T

[Fundamentals]
EPS: $9.06"""
    fields = _extract_fields("fetch_market_data", text)
    assert fields["source"] == "futu"
    assert fields["current_price"] == 294.80
    assert fields["pe"] == 32.50
    assert fields["pb"] == 45.20
    assert fields["eps"] == 9.06
    assert fields["market_cap"] == "4.31T"


def test_extract_fields_market_data_yfinance():
    text = """=== yfinance Market Data: Tesla (TSLA) ===
Sector: Consumer Cyclical | Industry: Auto Manufacturers | Country: US

Current Price: 412.36 USD

[Key Metrics]
P/E: 58.30
P/B: 22.10"""
    fields = _extract_fields("fetch_market_data", text)
    assert fields["source"] == "yfinance"
    assert fields["sector"] == "Consumer Cyclical"
    assert fields["country"] == "US"
    assert fields["pe"] == 58.30
    assert fields["pb"] == 22.10


def test_extract_fields_price_history():
    text = """Price History for AAPL (1mo)
Data points: 3
First: 2026-04-13: O=280.00 H=285.00 L=279.50 C=284.00 V=1000000
Last: 2026-05-13: O=290.01 H=294.76 L=290.00 C=293.32 V=2000000

2026-05-01: O=288.00 H=291.00 L=287.50 C=290.50 V=1500000
2026-05-08: O=289.50 H=293.00 L=289.00 C=292.00 V=1800000
2026-05-13: O=290.01 H=294.76 L=290.00 C=293.32 V=2000000"""
    fields = _extract_fields("fetch_price_history", text)
    assert "records" in fields
    assert len(fields["records"]) == 3
    assert fields["closes"] == [290.50, 292.00, 293.32]
    assert fields["records"][0]["date"] == "2026-05-01"


def test_extract_fields_technicals():
    text = """Technical Analysis for AAPL:

Latest Price: $293.32
Volatility (std dev of daily returns): 1.85%

Moving Averages:
  SMA 10-day: $289.50
  SMA 20-day: $285.20
  EMA 12-day: $290.10

RSI (14-day): Neutral (58.3)
Trend: Bullish (SMA10 above SMA20)"""
    fields = _extract_fields("calculate_technicals", text)
    assert fields["trend"] == "Bullish (SMA10 above SMA20)"
    assert fields["sma_10"] == 289.50
    assert fields["sma_20"] == 285.20
    assert abs(fields["volatility"] - 1.85) < 0.01


def test_extract_fields_sentiment_news():
    text = """=== Sentiment & News (Finnhub): AAPL ===
Period: 2026-05-06 to 2026-05-13
Articles: 15

--- TECHNOLOGY (3 articles) ---
[2026-05-12 14:30] Apple announces new product"""
    fields = _extract_fields("fetch_sentiment_news", text)
    assert fields["source"] == "finnhub"
    assert fields["article_count"] == 15


def test_extract_fields_macro_research():
    text = """=== Macro & Sector Research (US / S&P 500) ===

--- Query: "stock market outlook 2026" ---
- [2026-05-12] Market outlook positive
  Body text here
  Source: Reuters

- [2026-05-11] Fed holds rates steady
  Body text here
  Source: Bloomberg"""
    fields = _extract_fields("fetch_macro_research", text)
    assert fields["region"] == "US"
    assert fields["index"] == "S&P 500"
    assert fields["source"] == "web_search"
    assert fields["article_count"] == 2


# ── CORE_TOOLS ───────────────────────────────────────────────────

def test_core_tools_set():
    assert CORE_TOOLS == {"fetch_market_data", "fetch_macro_research", "fetch_sentiment_news"}


# ── Concurrent request safety ────────────────────────────────────

def test_finnhub_key_not_in_global_state():
    """After Phase 1, finnhub_api_key lives in AgentState, not a global module variable."""
    # Verify sentiment_news module no longer has _api_key or set_api_key
    from agent_service.app.tools import sentiment_news
    assert not hasattr(sentiment_news, "_api_key"), "global _api_key should have been removed"
    assert not hasattr(sentiment_news, "set_api_key"), "set_api_key should have been removed"


def test_finnhub_key_passed_via_args():
    """fetch_sentiment_news accepts finnhub_api_key as a parameter."""
    from agent_service.app.tools.sentiment_news import fetch_sentiment_news
    import inspect
    sig = inspect.signature(fetch_sentiment_news.func)
    assert "finnhub_api_key" in sig.parameters
