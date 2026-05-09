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
