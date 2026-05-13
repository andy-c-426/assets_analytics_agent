import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Literal

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from agent_service.app.state import AgentState, ToolCallPlan, ToolResult, ReasoningStep
from agent_service.app.llm.client_factory import create_chat_model
from agent_service.app.tools.yfinance_tools import fetch_price_history
from agent_service.app.tools.technicals import calculate_technicals
from agent_service.app.tools.market_data import fetch_market_data
from agent_service.app.tools.macro_research import fetch_macro_research
from agent_service.app.tools.sentiment_news import fetch_sentiment_news
from agent_service.app.prompts import (
    PLAN_PROMPT,
    OBSERVE_PROMPT,
    TOOL_REGISTRY,
    compress_tool_results,
    apply_language_instruction,
    build_synthesize_prompt,
    _now,
)
from agent_service.app.analytics.metrics import (
    compute_enriched_analytics,
    format_analytics_dashboard,
)
from agent_service.app.cache import get_cache


TOOLS_BY_NAME = {
    "fetch_market_data": fetch_market_data,
    "fetch_macro_research": fetch_macro_research,
    "fetch_sentiment_news": fetch_sentiment_news,
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


def _parse_plan_response(content: str, symbol: str) -> tuple[str, list[ToolCallPlan]]:
    """Parse LLM response into reasoning text and plan list."""
    reasoning = ""
    plan: list[ToolCallPlan] = []

    content = content.strip()

    # Try newline-separated format: reasoning line then JSON line
    lines = content.split("\n")
    json_str = ""

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            json_str = stripped
        elif stripped.startswith("{"):
            json_str = stripped
        elif not json_str and stripped:
            # Lines before JSON are reasoning
            if not reasoning:
                reasoning = stripped
            else:
                reasoning += " " + stripped

    # Fallback: treat whole content as JSON
    if not json_str:
        json_str = content
        if json_str.startswith("```"):
            json_str = json_str.split("\n", 1)[-1] if "\n" in json_str else ""
        if json_str.endswith("```"):
            json_str = json_str[:-3].strip()

    try:
        parsed = json.loads(json_str)
        if isinstance(parsed, list):
            plan = parsed
        elif isinstance(parsed, dict):
            plan = [parsed]
    except json.JSONDecodeError:
        plan = [{"tool": "fetch_asset_data", "args": {"symbol": symbol}}]
        if not reasoning:
            reasoning = "Gathering basic asset data"

    if not reasoning:
        reasoning = f"Planned {len(plan)} tool call(s)"

    return reasoning, plan


def plan_node(state: AgentState) -> dict:
    steps: list[ReasoningStep] = state.get("steps", [])
    iteration = state.get("iteration_count", 0) + 1
    steps.append({
        "step_type": "planning",
        "status": "active",
        "message": f"Planning analysis for {state['symbol']}...",
    })

    language = state.get("language", "en")
    llm = _build_llm(state)

    existing_results: list[ToolResult] = state.get("tool_results", [])
    if existing_results:
        available_names = [r["tool"] for r in existing_results]
        available_block = (
            "The following data is already available (do NOT re-request these tools):\n"
            + "\n".join(f"  - {name}: data already collected" for name in available_names)
            + "\n\nPlan only ADDITIONAL tools beyond what's already available. "
            "Focus on: fetch_price_history (for technical analysis) and "
            "calculate_technicals (if price data warrants it). "
            "If all useful data is already collected, plan an empty list []."
        )
    else:
        available_block = (
            "For a complete analysis, you MUST call ALL THREE core tools (plus additional tools as needed):\n\n"
            "1. fetch_market_data — structured data: price, metrics, fundamentals, market index\n"
            "2. fetch_macro_research — macro context: sector trends, policy, economic outlook\n"
            "3. fetch_sentiment_news — alternative data: news, sentiment, market mood\n\n"
            "Then supplement with:\n"
            "- fetch_price_history for technical analysis (use period relative to today's date)\n"
            "- calculate_technicals if you have price data"
        )

    prompt = apply_language_instruction(
        PLAN_PROMPT.format(
            symbol=state["symbol"],
            tool_descriptions=TOOL_REGISTRY,
            current_date=_now(),
            available_data=available_block,
        ),
        language,
    )

    messages = state.get("messages", [])
    messages.append(SystemMessage(content=prompt))

    response = llm.invoke(messages)
    messages.append(HumanMessage(content="Plan my analysis"))
    messages.append(response)

    content = response.content if hasattr(response, "content") else str(response)
    reasoning, plan = _parse_plan_response(content, state["symbol"])

    steps[-1]["status"] = "done"
    steps[-1]["detail"] = reasoning
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
        "iteration_count": iteration,
        "next_action": "execute_tools",
    }


def execute_tools_node(state: AgentState) -> dict:
    plan: list[ToolCallPlan] = state["plan"]
    steps: list[ReasoningStep] = state.get("steps", [])
    messages = state.get("messages", [])

    for step in steps:
        if step["status"] == "pending" and step["step_type"] == "tool_call":
            step["status"] = "active"
            step["message"] = f"Calling {step.get('detail', 'tool')}..."

    def _run_tool(call: ToolCallPlan) -> tuple[str, dict, str, bool]:
        tool_name = call["tool"]
        args = dict(call.get("args", {}))
        tool_fn = TOOLS_BY_NAME.get(tool_name)
        if tool_fn is None:
            return tool_name, args, f"Error: Unknown tool '{tool_name}'", False
        # Inject request-scoped config from state
        if tool_name == "fetch_sentiment_news" and "finnhub_api_key" not in args:
            key = state.get("finnhub_api_key") or state.get("llm_config", {}).get("finnhub_api_key")
            if key:
                args["finnhub_api_key"] = key
        try:
            return tool_name, args, tool_fn.invoke(args), True
        except Exception as e:
            return tool_name, args, f"Error executing {tool_name}: {str(e)}", False

    results_by_name: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=min(len(plan), 5)) as executor:
        futures = {
            executor.submit(_run_tool, call): call
            for call in plan
        }
        for future in as_completed(futures):
            tool_name, args, result_text, ok = future.result()
            results_by_name[tool_name] = (result_text, ok)

    tool_results: list[ToolResult] = []
    for call in plan:
        tool_name = call["tool"]
        args = call.get("args", {})
        entry = results_by_name.get(tool_name)
        if entry is None:
            result_text = f"Error: No result for '{tool_name}'"
            ok = False
        else:
            result_text, ok = entry

        for step in steps:
            if step["status"] == "active" and step["step_type"] == "tool_call":
                if tool_name in step.get("detail", ""):
                    step["status"] = "done"
                    step["message"] = f"Completed: {tool_name}"
                    break

        summary_lines = result_text.split("\n")
        summary = summary_lines[0] if summary_lines else f"Result from {tool_name}"
        if len(summary) > 150:
            summary = summary[:147] + "..."

        tool_results.append({
            "tool": tool_name,
            "args": args,
            "summary": summary,
            "status": "ok" if ok else "error",
            "data": {"full_result": result_text},
        })

        messages.append(HumanMessage(content=f"Tool: {tool_name}\nArgs: {json.dumps(args)}\nResult: {summary}"))

    # Merge with previously accumulated results (e.g. pre-fetched cached data)
    accumulated = list(state.get("tool_results", []))
    accumulated.extend(tool_results)

    return {
        "tool_results": accumulated,
        "steps": steps,
        "messages": messages,
        "next_action": "observe",
    }


def _parse_observe_response(content: str) -> tuple[str, list[str], str]:
    """Parse observe LLM response. Returns (decision, missing_fields, reasoning)."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1] if "\n" in content else ""
    if content.endswith("```"):
        content = content[:-3].strip()

    try:
        data = json.loads(content)
        return (
            data.get("decision", "enough"),
            data.get("missing", []),
            data.get("reasoning", ""),
        )
    except json.JSONDecodeError:
        content_lower = content.lower()
        if content_lower.startswith("more"):
            return "more", [], content
        return "enough", [], content


def observe_node(state: AgentState) -> dict:
    steps: list[ReasoningStep] = state.get("steps", [])
    steps.append({
        "step_type": "evaluating",
        "status": "active",
        "message": "Evaluating collected data...",
    })

    language = state.get("language", "en")
    llm = _build_llm(state)

    compressed = compress_tool_results(state["tool_results"])

    prompt = apply_language_instruction(
        OBSERVE_PROMPT.format(
            symbol=state["symbol"],
            tool_results_summary=compressed,
            current_date=_now(),
        ),
        language,
    )

    messages = state.get("messages", [])
    messages.append(SystemMessage(content=prompt))
    response = llm.invoke(messages)
    messages.append(response)

    content = response.content if hasattr(response, "content") else str(response)
    decision, missing, reasoning = _parse_observe_response(content)

    steps[-1]["status"] = "done"

    if decision == "more":
        steps[-1]["detail"] = f"Need more data — re-planning: {reasoning}"
        steps.append({
            "step_type": "planning",
            "status": "pending",
            "message": f"Re-planning{f' (need: {chr(44).join(missing)})' if missing else ''}...",
            "detail": reasoning,
        })
        return {
            "messages": messages,
            "steps": steps,
            "next_action": "plan",
        }

    steps[-1]["detail"] = f"Data sufficient — {reasoning}" if reasoning else "Data sufficient — ready to synthesize"
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
        "message": "Computing analytics dashboard...",
    })

    llm = _build_llm(state)

    # Compute Bloomberg-style analytics from raw tool results
    asset_data_str = ""
    price_history_str = ""
    for r in state["tool_results"]:
        if r["tool"] in ("fetch_market_data", "fetch_asset_data"):
            asset_data_str = r.get("data", {}).get("full_result", "")
        elif r["tool"] == "fetch_price_history":
            price_history_str = r.get("data", {}).get("full_result", "")

    symbol = state["symbol"]
    language = state.get("language", "en")
    cache = get_cache()
    cache_key = f"{symbol}:{language}"
    cached = cache.get(cache_key)

    if cached and cached.get("asset_data") == asset_data_str and cached.get("price_history") == price_history_str:
        dashboard = cached["dashboard"]
    else:
        analytics = compute_enriched_analytics(symbol, asset_data_str, price_history_str, language)
        dashboard = format_analytics_dashboard(analytics, symbol, language)
        cache.set(cache_key, {
            "asset_data": asset_data_str,
            "price_history": price_history_str,
            "dashboard": dashboard,
        }, ttl=300)

    # Use full results for final report (not compressed)
    tool_results_full = "\n\n".join(
        r.get("data", {}).get("full_result", r["summary"])
        for r in state["tool_results"]
    )

    # Inject analytics dashboard between raw data and instructions
    enriched_data = tool_results_full + "\n\n" + dashboard

    prompt = build_synthesize_prompt(
        symbol=symbol,
        enriched_data=enriched_data,
        current_date=_now(),
        language=language,
    )

    steps[-1]["status"] = "done"
    steps[-1]["detail"] = "Analytics computed — writing report"
    steps.append({
        "step_type": "synthesizing",
        "status": "active",
        "message": "Writing analysis report...",
    })

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


MAX_ITERATIONS = 3


def decide_next(state: AgentState) -> Literal["plan", "synthesize", "__end__"]:
    action = state.get("next_action", "synthesize")
    if action == "plan":
        if state.get("iteration_count", 0) >= MAX_ITERATIONS:
            return "synthesize"
        return "plan"
    if action == "synthesize":
        return "synthesize"
    return "__end__"
