from typing import TypedDict, NotRequired


class ReasoningStep(TypedDict):
    step_type: str        # "planning" | "tool_call" | "evaluating" | "synthesizing"
    status: str           # "pending" | "active" | "done"
    message: str
    detail: NotRequired[str]
    call_id: NotRequired[str]


class ToolCallPlan(TypedDict):
    tool: str
    args: dict
    call_id: NotRequired[str]  # "toolname_index" — unique per invocation


class ToolResult(TypedDict):
    tool: str
    args: dict
    summary: str
    call_id: NotRequired[str]  # matches ToolCallPlan.call_id
    status: NotRequired[str]   # "ok" | "error"
    fields: NotRequired[dict]  # machine-readable structured fields
    data: NotRequired[dict]
    source: NotRequired[str]     # "futu" | "yfinance" | "finnhub" | "web_search" | "akshare" | "unknown"
    freshness: NotRequired[str]  # "realtime" | "delayed" | "cached" | "unknown"
    warnings: NotRequired[list[str]]  # human-readable degradation/failure notes


class ToolOutput(TypedDict):
    """Structured return from a tool function.

    Tools should return this instead of a raw string so the graph layer
    can access both the human-readable text and machine-readable fields
    without regex parsing.
    """
    text: str
    fields: dict
    source: NotRequired[str]
    freshness: NotRequired[str]
    warnings: NotRequired[list[str]]


class AgentState(TypedDict):
    symbol: str
    language: NotRequired[str]
    llm_config: dict              # provider, model, api_key, base_url
    finnhub_api_key: NotRequired[str | None]
    plan: list[ToolCallPlan]
    tool_results: list[ToolResult]
    messages: list[dict]          # full message history for LLM context
    steps: list[ReasoningStep]
    final_report: str | None
    next_action: str              # "plan" | "execute_tools" | "observe" | "synthesize" | "done"
    iteration_count: NotRequired[int]
    core_retries: NotRequired[int]
    error: str | None
