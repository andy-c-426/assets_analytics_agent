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
    status: NotRequired[str]  # "ok" | "error"
    data: NotRequired[dict]


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
    error: str | None
