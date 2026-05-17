"""Terminal chat client for Asset Analytics Agent.

Usage: python3 -m backend.app.chat.cli
"""

import json
import os
import sys
import urllib.request
import urllib.error


# ── ANSI helpers ──
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def _print_header():
    print()
    print(f"{BOLD}{'═' * 46}{RESET}")
    print(f"{BOLD}  Asset Analytics Agent — Chat Mode{RESET}")
    print(f"{DIM}  Type /help for commands, Ctrl+C to exit{RESET}")
    print(f"{BOLD}{'═' * 46}{RESET}")
    print()


def _print_help():
    print(f"""
{CYAN}Commands:{RESET}
  /help          Show this help
  /settings      Show current LLM config
  /settings set <key> <value>  Change config (provider, model, api_key, base_url, finnhub_key, language)
  /export <file> Save last report to markdown file
  /history       Show recent conversation
  /clear         Reset conversation
  /quit          Exit

{CYAN}Tips:{RESET}
  Type naturally — the agent will guide you through research.
  Mention ticker symbols (AAPL, 0700.HK) to analyze specific stocks.
""")


SETTINGS_FILE = os.path.expanduser("~/.asset_analytics_chat.json")


def _load_settings() -> dict:
    try:
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_settings(s: dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f, indent=2)


def _print_settings(settings: dict):
    print(f"\n{CYAN}Current settings:{RESET}")
    for k, v in settings.items():
        if "key" in k.lower() and v:
            v = v[:8] + "..." if len(str(v)) > 8 else v
        print(f"  {k}: {v}")
    if not settings:
        print(f"  {DIM}(not configured — run /settings set to configure){RESET}")
    print()


def _stream_chat(message: str, history: list[dict], direction: dict | None, settings: dict, last_report: list[str]):
    """Send POST /api/chat and render SSE events in the terminal."""
    body = json.dumps({
        "message": message,
        "history": history,
        "direction": direction,
        "user_preferences": {
            "language": settings.get("language", "en"),
            "llm_config": {
                "provider": settings.get("provider", "claude"),
                "model": settings.get("model", "claude-sonnet-4-6"),
                "api_key": settings.get("api_key", ""),
                "base_url": settings.get("base_url", ""),
            },
            "finnhub_api_key": settings.get("finnhub_key", ""),
        },
    }).encode()

    req = urllib.request.Request(
        "http://localhost:8000/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )

    new_direction = direction

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            buffer = ""
            event_type = ""

            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break

                buffer += chunk.decode()
                lines = buffer.split("\n")
                buffer = lines.pop() or ""

                for line in lines:
                    if line.startswith("event: "):
                        event_type = line[7:].strip()
                    elif line.startswith("data: ") and event_type:
                        try:
                            data = json.loads(line[6:])
                        except json.JSONDecodeError:
                            event_type = ""
                            continue

                        if event_type == "clarification":
                            new_direction = data.get("direction", new_direction)
                            print(f"\n{GREEN}Agent:{RESET} {data['message']}")

                        elif event_type == "proposal":
                            new_direction = data.get("direction", new_direction)
                            print(f"\n{GREEN}Agent:{RESET}")
                            print(f"  {data['message']}")

                        elif event_type == "tool_start":
                            tool = data.get("tool", "")
                            print(f"  {YELLOW}⏳{RESET} {tool}...", end="\r")

                        elif event_type == "tool_result":
                            tool = data.get("tool", "")
                            summary = data.get("summary", "")[:100]
                            print(f"  {GREEN}✓{RESET} {tool}: {summary}")

                        elif event_type == "reasoning_chunk":
                            print(data.get("text", ""), end="", flush=True)

                        elif event_type == "report_ready":
                            report_text = data.get("report", "")
                            print(f"\n{BOLD}{'─' * 50}{RESET}")
                            print(report_text)
                            print(f"{BOLD}{'─' * 50}{RESET}")
                            last_report.clear()
                            last_report.append(report_text)

                        elif event_type == "asset_card":
                            symbol = data.get("symbol", "")
                            print(f"\n{CYAN}┌── {symbol} ──────────{RESET}")

                        elif event_type == "comparison":
                            print(f"\n{BOLD}Comparison: {data.get('message', '')}{RESET}")

                        elif event_type == "text":
                            print(f"\n{GREEN}Agent:{RESET} {data.get('message', '')}")

                        elif event_type == "error":
                            print(f"\n{RED}Error: {data.get('message', '')}{RESET}")

                        elif event_type == "done":
                            pass  # stream end

                        event_type = ""

    except urllib.error.HTTPError as e:
        print(f"\n{RED}Server error: {e.code} — {e.reason}{RESET}")
    except urllib.error.URLError:
        print(f"\n{RED}Cannot reach backend at http://localhost:8000{RESET}")
        print(f"{DIM}Make sure the backend is running: ./start_backend.sh{RESET}")
    except KeyboardInterrupt:
        print(f"\n{DIM}Stopped.{RESET}")

    return new_direction


def main():
    settings = _load_settings()
    history: list[dict] = []
    direction = None
    last_report: list[str] = []

    _print_header()

    # Check if settings are configured
    if not settings.get("api_key"):
        print(f"{YELLOW}First-time setup: configure your LLM settings.{RESET}")
        print(f"  Use {CYAN}/settings set provider claude{RESET}")
        print(f"  Use {CYAN}/settings set model claude-sonnet-4-6{RESET}")
        print(f"  Use {CYAN}/settings set api_key sk-ant-...{RESET}")
        print()

    # Welcome message
    print(f"{GREEN}Agent:{RESET} Welcome! I can help you research and analyze stocks globally.")
    print(f"  What are you interested in today?")
    print()

    while True:
        try:
            user_input = input(f"{CYAN}You:{RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{DIM}Goodbye!{RESET}")
            break

        if not user_input:
            continue

        # ── Handle slash commands ──
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=2)
            cmd = parts[0].lower()

            if cmd == "/quit" or cmd == "/exit":
                print(f"{DIM}Goodbye!{RESET}")
                break

            elif cmd == "/help":
                _print_help()

            elif cmd == "/settings":
                if len(parts) >= 3 and parts[1] == "set":
                    key = parts[2].lower()
                    value = input(f"  {key}: ").strip()
                    if key == "api_key":
                        settings["api_key"] = value
                    elif key == "base_url":
                        settings["base_url"] = value
                    elif key == "finnhub_key":
                        settings["finnhub_key"] = value
                    elif key == "language":
                        settings["language"] = value
                    else:
                        settings[key] = value
                    _save_settings(settings)
                    print(f"  {GREEN}✓ Saved{RESET}")
                else:
                    _print_settings(settings)

            elif cmd == "/export":
                if len(parts) >= 2 and last_report:
                    filename = parts[1]
                    with open(filename, "w") as f:
                        f.write(last_report[0])
                    print(f"  {GREEN}✓ Saved to {filename}{RESET}")
                elif not last_report:
                    print(f"  {DIM}No report to export yet.{RESET}")

            elif cmd == "/history":
                print(f"\n{DIM}── Conversation ──{RESET}")
                for h in history:
                    role = h["role"].capitalize()
                    content = h["content"][:200]
                    print(f"  {BOLD if role == 'User' else ''}{role}:{RESET} {content}")
                print()

            elif cmd == "/clear":
                history = []
                direction = None
                last_report = []
                print(f"  {GREEN}✓ Conversation cleared.{RESET}")

            else:
                print(f"  {RED}Unknown command: {cmd}{RESET}  (use /help)")

            continue

        # ── Send message to chat API ──
        history.append({"role": "user", "content": user_input})
        direction = _stream_chat(user_input, history, direction, settings, last_report)
        # Add a placeholder assistant entry for history tracking
        history.append({"role": "assistant", "content": "[response rendered above]"})


if __name__ == "__main__":
    main()
