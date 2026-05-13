# Phase 3 — Agent Stabilization: Safety, Determinism, and Observability

**Status:** completed
**Branch:** `main`
**Date:** 2026-05-10 – 2026-05-13

## What Was Built

Three stabilization iterations hardened the LangGraph agent from a prototype into a production-safe system.

### Phase 3.1 — Safety, Config Scoping, Iteration Guard

- **Request-scoped config:** `finnhub_api_key` moved from global module variable to `AgentState` field, eliminating race conditions across concurrent requests
- **Tool result status:** every `ToolResult` now carries `status: "ok" | "error"` for deterministic error handling
- **Iteration guard:** `MAX_ITERATIONS = 3` enforced in `decide_next`, preventing infinite plan→execute→observe loops
- **`sentiment_news.py`:** removed `_api_key` global and `set_api_key()` function; `finnhub_api_key` now passed as a function parameter

### Phase 3.2 — Deterministic Core Data Collection + Structured Fields

- **New graph node `collect_core_data`:** replaces the first `plan` call for bootstrapping. Runs 3 core tools (`fetch_market_data`, `fetch_macro_research`, `fetch_sentiment_news`) in parallel via `ThreadPoolExecutor`. Cache-aware: skips tools already present with `status: "ok"`.
- **`CORE_TOOLS` constant:** defines the 3 mandatory data sources. Core = 市场基础数据 + 宏观研报 + 情绪舆情.
- **`_extract_fields()`:** regex-based parser extracts machine-readable fields from all 5 tool text outputs (current_price, pe, pb, eps, market_cap, sector, country, source, SMA/EMA/RSI/volatility/trend, OHLCV records). Enables deterministic logic without LLM parsing.
- **`validate_coverage()`:** deterministic function that checks all 3 core tools returned `status: "ok"`. Eliminates one LLM round-trip (initial plan → observe bookkeeping).
- **`observe_node` overhaul:** runs `validate_coverage()` first — if core data is incomplete, routes to `collect_core_data` for re-collection without invoking the LLM. LLM is only called for qualitative sufficiency judgment.
- **`plan_node` updated:** always assumes core data exists, plans only supplementary tools (`fetch_price_history`, `calculate_technicals`).
- **`_build_llm()` helper:** single LLM construction function from state config, used by plan/observe/synthesize nodes.
- **SSE `collect_core_data` events:** tool_called + tool_result events emitted for core data collection.

### Phase 3.3 — call_id Keys, Empty Plan Routing, Fallback Fix, Tests

- **`call_id` on all entities:** `ToolCallPlan`, `ToolResult`, `ReasoningStep` all carry `call_id` for precise plan→result→step matching, replacing fragile substring matching on `step["detail"]`
- **`decide_after_plan`:** new conditional edge function — if the plan is empty (`[]`), routes directly to `observe`, skipping `execute_tools`
- **Fallback fix:** `_parse_plan_response` fallback changed from `fetch_asset_data` (removed tool) to `fetch_price_history`
- **`collect_core_data_node`:** uses `call_id = f"{tool_name}_core"` for deterministic matching
- **`execute_tools_node`:** groups results by `call_id`, merges with previously accumulated results
- **Pre-fetched data:** `agent_router.py` assigns `call_id = f"{tool_name}_cached"` to pre-populated results

### Graph Flow (Final)

```
collect_core_data → plan → (empty plan? → observe : execute_tools → observe)
                                  ↑              ↓
                                  └── (need more? → re-plan, up to 3 iterations)
                                                       ↓
                                                  synthesize → END
```

## Files Changed

### Modified

```
agent-service/agent_service/app/
  state.py                    # +call_id on ToolCallPlan/ToolResult/ReasoningStep
                              # +finnhub_api_key +iteration_count +status +fields on AgentState
  graph.py                    # +collect_core_data_node +CORE_TOOLS +_extract_fields
                              # +validate_coverage +decide_after_plan +MAX_ITERATIONS
                              # rewritten plan_node, observe_node, execute_tools_node
                              # _parse_plan_response: fetch_asset_data→fetch_price_history fallback
  prompts.py                  # PLAN_PROMPT: +{available_data} placeholder, core tools listed as collected
                              # OBSERVE_PROMPT: simplified for qualitative judgment only
                              # TOOL_REGISTRY: rephrased "already collected" vs "supplementary"
  agent_router.py             # +_extract_fields import for pre-populated tool results
                              # +call_id on pre_tool_results
                              # +finnhub_api_key +iteration_count in initial_state
                              # +SSE events for collect_core_data node
  tools/sentiment_news.py     # removed global _api_key and set_api_key()
                              # finnhub_api_key as function parameter
  tools/__init__.py           # updated exports

agent-service/tests/
  test_graph.py               # rewritten: 3 → 30 unit tests (graph, routing, parsing,
                              # extraction, coverage, concurrency safety)
```

## Commits

```
edf7411 feat: Phase 3 — call_id keys, empty plan routing, fallback fix, 30 unit tests
2247b12 feat: Phase 2 — deterministic core data collection, structured fields, coverage check
81d2b11 fix: Phase 1 stabilization — scoped config, tool status, iteration guard
651309f fix: always plan first even with cached data, let model decide what tools to call
```
