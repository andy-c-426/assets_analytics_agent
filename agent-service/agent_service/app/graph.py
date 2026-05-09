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

    content = response.content if hasattr(response, "content") else str(response)
    try:
        content = content.strip()
        if content.startswith("```"):
            # Remove opening fence (with optional language specifier like ```json)
            content = content.split("\n", 1)[-1] if "\n" in content else ""
        if content.endswith("```"):
            content = content[:-3].strip()
        plan: list[ToolCallPlan] = json.loads(content)
    except json.JSONDecodeError:
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

        for step in steps:
            if step["status"] == "active" and step["step_type"] == "tool_call":
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

    # Default: enough data collected, proceed to synthesis
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


def decide_next(state: AgentState) -> Literal["plan", "synthesize", "__end__"]:
    action = state.get("next_action", "synthesize")
    if action == "plan":
        return "plan"
    if action == "synthesize":
        return "synthesize"
    return "__end__"
