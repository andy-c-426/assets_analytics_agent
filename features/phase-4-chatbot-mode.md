# Phase 4 — Chatbot Mode: Conversational Agent Interface

**Status:** completed
**Branch:** `main`
**Date:** 2026-05-17

## What Was Built

A conversational chat interface (web + CLI) that guides users through asset discovery, proposes research plans, and streams analysis results using the existing LangGraph agent pipeline.

### Three-Phase Consultation Workflow

- **Discovery** — Agent asks one question at a time to understand goal, scope, criteria, time horizon, risk tolerance, and report type
- **Proposal** — Agent summarizes the research plan and asks for confirmation before running anything
- **Execute** — Agent runs the existing LangGraph pipeline, streaming results inline

### Intent Classifier

Lightweight LLM (configurable via `CHAT_CLASSIFIER_PROVIDER`/`CHAT_CLASSIFIER_MODEL`/`CHAT_CLASSIFIER_API_KEY` env vars) routes messages into: `discovery` | `proposal` | `execute` | `follow_up`. Direction accumulates across turns. JSON parse fallback for robustness.

### API Endpoint

- **`POST /api/chat`** — SSE streaming with typed events: `clarification`, `proposal`, `tool_start`, `tool_result`, `reasoning_chunk`, `asset_card`, `report_ready`, `comparison`, `text`, `error`, `done`
- Stateless — history and direction sent per request, no server sessions

### Web Chat UI (`/chat`)

- ChatMessage component with 6 message types (text, asset_card, analysis_stream, clarification, error, loading)
- ChatInput with auto-resize, Enter-to-send, Stop button during streaming
- SSE reader with streaming analysis blocks, settings integration, abort support
- Nav bar "Chat" link, bilingual i18n labels (en + zh-CN)

### CLI Chat Client (`./chat.sh`)

- Terminal interface with ANSI rendering, slash commands (`/help`, `/settings`, `/history`, `/export`, `/clear`, `/quit`)
- Calls the same `POST /api/chat` endpoint — thin frontend, no separate code path
- Settings persisted to `~/.asset_analytics_chat.json`

### Backend LLM Factory

- Shared `create_llm()` in `backend/app/llm.py` — supports Claude, GPT, and DeepSeek
- Used by both the intent classifier and the chat response generator

## Changed Files

### New (16 files)

| File | Purpose |
|------|---------|
| `backend/app/chat/__init__.py` | Package init |
| `backend/app/chat/prompts.py` | System prompts (classifier, discovery, proposal, chat) |
| `backend/app/chat/intent.py` | Intent classifier with LLM routing + JSON fallback |
| `backend/app/chat/cli.py` | Terminal chat client with ANSI rendering |
| `backend/app/activities/chat.py` | `POST /api/chat` SSE endpoint |
| `backend/app/llm.py` | Shared LLM client factory |
| `chat.sh` | CLI convenience wrapper |
| `backend/tests/test_chat_intent.py` | Intent classifier tests (6) |
| `backend/tests/test_chat_endpoint.py` | Chat endpoint tests (6) |
| `frontend/src/pages/ChatPage.tsx` | Chat page with SSE streaming |
| `frontend/src/pages/ChatPage.module.css` | Chat page styles |
| `frontend/src/components/ChatMessage.tsx` | Message renderer (6 types) |
| `frontend/src/components/ChatMessage.module.css` | Message styles |
| `frontend/src/components/ChatInput.tsx` | Input bar with send/stop |
| `frontend/src/components/ChatInput.module.css` | Input bar styles |

### Modified (5 files)

| File | Change |
|------|--------|
| `backend/app/main.py` | Registered chat router |
| `frontend/src/App.tsx` | Added `/chat` route + nav link |
| `frontend/src/api/client.ts` | Added `postChat()` + ChatRequest/ChatDirection types |
| `frontend/src/i18n/translations.ts` | Added chat labels (en + zh-CN) |
| `start.sh` / `start_agent.sh` | Fixed to `cd` into `agent-service/` directory |

## Architecture Decisions

- **Stateless backend** — no server-side sessions or DB, history per request
- **Cheap classifier** — intent classification uses server-side API key for a fast model, not the user's LLM
- **Two-tier depth** — chat runs standard or deep analysis depending on research brief
- **No new dependencies** — CLI uses only stdlib + HTTP client for SSE
- **CLI calls same API** — thin terminal frontend, no separate code path
- **Existing agent pipeline unchanged** — chat proxies analysis to `POST /api/analyze/{symbol}`

## Commits

```
d1c58c1 feat: add chatbot prompts for discovery, proposal, and classification
62b677f feat: add shared LLM client factory for backend
917478d feat: add intent classifier for chat routing
823871e feat: add POST /api/chat endpoint with intent routing and SSE streaming
4956647 feat: add CLI chat client with ANSI rendering and slash commands
6a352fa feat: add postChat API function with SSE stream support
5eeafb3 feat: add ChatMessage and ChatInput components
8c3c77a feat: add ChatPage component with SSE streaming and settings integration
d2675c2 feat: wire chat page into routing, nav, and i18n
42dfc00 fix: start_agent.sh and start.sh to cd into agent-service/ directory
```

## Tests

- 62 total backend tests pass (50 agent-service + 12 backend)
- TypeScript compiles clean
- Chat API tested with SSE fallback on invalid API key
- CLI loads and exits cleanly
