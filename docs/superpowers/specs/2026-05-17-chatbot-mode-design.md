# Chatbot Mode Agent — Design Spec

## Overview

A conversational interface that guides users through a structured discovery conversation, understands their investment goals, collects relevant assets, and runs the existing analysis pipeline. Available as both a web UI page and a terminal CLI.

## User Flow

1. User opens Chat page (`/chat`) or runs `./chat.sh`
2. Agent asks discovery questions to understand the user's goal, scope, criteria, time horizon, risk tolerance, and desired report type
3. Agent proposes a research plan — summarizes what it will analyze and how
4. User confirms or adjusts
5. Agent runs the existing LangGraph pipeline, streaming results inline
6. User can ask follow-up questions, compare additional assets, or export the report

## Architecture

```
Browser Chat UI ──→ POST /api/chat ──→ Chat Router (new)
Terminal CLI ────→ same endpoint          │
                                    Intent Classifier
                                    (lightweight LLM)
                                          │
                              ┌───────────┼───────────┐
                              ▼           ▼           ▼
                          discovery    proposal     execute
                              │           │           │
                              ▼           ▼           ▼
                         Return next   Return      Proxy to
                         question +   proposal +   existing
                         direction    ready flag   Agent Service
                                                   │
                                          POST /api/analyze/{symbol}
                                          (unchanged)
```

**Key principle:** The existing search → analyze flow is unchanged. Chat is an additional mode accessed via nav bar (`/chat`) or CLI (`./chat.sh`).

## Consultation Workflow (Three Phases)

### Phase 1: Discovery

The agent asks one question at a time to form a research brief:

| Question area | Examples |
|---------------|----------|
| Goal | "Researching a purchase, portfolio review, or just learning?" |
| Scope | "Specific stocks in mind, or should I help find candidates?" |
| Criteria | "Growth, value, dividends, or sector exposure?" |
| Time horizon | "Short-term trade or long-term hold?" |
| Risk tolerance | "Comfortable with volatility, or prefer stable blue chips?" |
| Report type | "Quick snapshot, deep fundamentals report, or comparison?" |

The agent asks only relevant questions — not all of them, just enough to form a clear brief.

### Phase 2: Proposal

The agent summarizes the research plan back to the user:

> "Here's what I'm hearing: you want to compare AAPL and MSFT as long-term growth holdings, focusing on fundamentals, with a moderate risk profile. I'll pull market data, recent news, analyst consensus, and run a full comparison report. Sound right?"

User confirms or adjusts → agent proceeds to execution.

### Phase 3: Execute + Deliver

Agent runs the existing LangGraph pipeline with the research brief injected as context, streams results inline, and formats output according to the agreed report type.

## Intent Classifier

Uses a cheap model (GPT-4o-mini / Claude Haiku) with a server-side API key (env var, not the user's key). Takes user message + last 3 exchanges + accumulated direction. Returns structured JSON:

```json
{
  "phase": "discovery" | "proposal" | "execute" | "follow_up",
  "direction": {
    "goal": "comparison" | "screening" | "deep_dive" | "monitoring",
    "tickers": ["AAPL", "MSFT"],
    "criteria": ["growth", "fundamentals"],
    "report_type": "comparison" | "snapshot" | "full_report"
  },
  "next_question": "Would you like me to include technical indicators too?",
  "ready_to_analyze": false
}
```

The `direction` accumulates across turns. When `ready_to_analyze` is true, the agent proposes before executing.

## API Endpoint

### POST /api/chat

Request:
```json
{
  "message": "I want to compare Apple and Microsoft",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "direction": null,
  "user_preferences": {
    "language": "en",
    "llm_config": {
      "provider": "claude",
      "model": "claude-opus-4-7",
      "api_key": "sk-..."
    },
    "finnhub_api_key": "fhb-..."
  }
}
```

Response: SSE stream with typed events:
- `clarification` — next discovery question + updated direction
- `proposal` — research plan summary + ready flag
- `tool_start` — tool name + args
- `tool_result` — tool name + summary
- `reasoning_chunk` — streaming analysis text
- `asset_card` — asset card with key metrics
- `report_ready` — full analysis report
- `comparison` — multi-asset comparison
- `error` — error message and retryable flag
- `done` — stream complete

## Web Chat UI

New page at `/chat` route.

### Layout

```
┌─────────────────────────────────────────────┐
│  ← Chat                      [⚙ Settings]  │
├─────────────────────────────────────────────┤
│  Message list (scrollable)                  │
│  - Text messages                            │
│  - Asset cards (inline, clickable)          │
│  - Streaming analysis blocks                │
│  - Comparison tables                        │
│  - Clarification choice buttons             │
├─────────────────────────────────────────────┤
│  [_____________________________] [Send] 🛑  │
└─────────────────────────────────────────────┘
```

### Message Types Rendered

| Type | Component | Trigger |
|------|-----------|---------|
| `text` | Markdown block | Chitchat, explanations |
| `asset_card` | Mini AssetDetail card | Ticker detected, partial data ready |
| `analysis_stream` | Streaming text block | Full agent pipeline running |
| `comparison` | Side-by-side cards | Multi-asset compare |
| `clarification` | Choice buttons | Ambiguous or discovery question |
| `error` | Red error banner | API failure |
| `loading` | Skeleton pulse | Waiting for response |

### Input Bar

- Text input with auto-resize
- Send button (or Enter)
- Stop button (visible during streaming)
- Quick-action chips after analysis: "Explain P/E", "Show chart", "Compare with..."

### State Management

- Chat history lives in React state (like current Settings)
- `direction` object persisted in chat state, sent with each request
- No server-side session storage
- User preferences (LLM config, language) loaded from localStorage

## CLI Mode

Terminal chat client using the same `POST /api/chat` endpoint.

### Entry Point

```bash
./chat.sh
# or
python3 -m backend.app.chat.cli
```

### Rendering

| Event | ANSI Rendering |
|-------|---------------|
| `tool_start` | Yellow `⏳` spinner |
| `tool_result` | Green `✓` + summary |
| `reasoning_chunk` | Plain text, buffered |
| `asset_card` | Box-drawing chars + key metrics |
| `report_ready` | Full text output |
| `error` | Red text |
| `clarification` | Numbered choice list |

### Commands

| Command | Action |
|---------|--------|
| `/help` | Show commands |
| `/settings` | Show current config |
| `/settings set <key> <value>` | Change provider, model, language |
| `/export <file.md>` | Save last report to markdown |
| `/history` | Show recent conversation |
| `/clear` | Reset conversation |
| `/quit` or `Ctrl+C` | Exit |

## File Plan

### New Files

| File | Purpose |
|------|---------|
| `backend/app/activities/chat.py` | `POST /api/chat` endpoint with SSE streaming |
| `backend/app/chat/__init__.py` | Package init |
| `backend/app/chat/intent.py` | Intent classifier (LLM call + JSON parse) |
| `backend/app/chat/prompts.py` | System prompts for discovery, proposal, chat |
| `backend/app/chat/cli.py` | Terminal chat loop, SSE consumer, ANSI rendering |
| `chat.sh` | CLI convenience wrapper |
| `frontend/src/pages/ChatPage.tsx` | Chat page component |
| `frontend/src/pages/ChatPage.module.css` | Chat page styles |
| `frontend/src/components/ChatMessage.tsx` | Message renderer (text, asset card, analysis, etc.) |
| `frontend/src/components/ChatMessage.module.css` | Message styles |
| `frontend/src/components/ChatInput.tsx` | Input bar with send/stop/suggest |
| `frontend/src/components/ChatInput.module.css` | Input bar styles |

### Modified Files

| File | Change |
|------|--------|
| `backend/app/main.py` | Include chat router |
| `frontend/src/App.tsx` | Add `/chat` route |
| `frontend/src/components/NavBar.tsx` | Add Chat nav link |
| `frontend/src/i18n/translations.ts` | Chat UI labels (en + zh-CN) |
| `frontend/src/api/client.ts` | Add `postChat()` function with SSE reader |

### Unchanged

| Component | Notes |
|-----------|-------|
| Agent service (`agent_service/`) | No changes — reused via existing `POST /analyze/{symbol}` |
| Existing search/analyze flow | Fully preserved, side-by-side with chat |
| LangGraph pipeline | No changes — chat direction injected via `prefetched_data` or prompt prefix |

## Design Decisions

- **Stateless backend** — Chat history and direction sent per request, no server-side sessions or DB
- **Cheap classifier** — Intent classification uses a shared server API key for a fast model, not the user's LLM
- **Two-tier depth** — Chat runs standard or deep analysis depending on the research brief; follow-ups short-circuit to re-synthesize with cached data
- **Configurable classifier model** — The classifier model is set via env var `CHAT_CLASSIFIER_MODEL` (default: `claude-haiku-4-5-20251001`) with provider set via `CHAT_CLASSIFIER_PROVIDER` (default: `claude`)
- **No new dependencies** — CLI uses only stdlib (`input`, `print`, ANSI codes) + HTTP client for SSE
- **CLI calls same API** — The CLI is a thin terminal frontend to `POST /api/chat`, not a separate code path
