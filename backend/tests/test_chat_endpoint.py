import json
from unittest.mock import patch
from fastapi.testclient import TestClient


def make_test_app():
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    from backend.app.activities.chat import router as chat_router
    app.include_router(chat_router)

    return app


client = TestClient(make_test_app())


def test_chat_endpoint_requires_message():
    body = {
        "message": "",
        "history": [],
        "direction": None,
        "user_preferences": {
            "language": "en",
            "llm_config": {"provider": "claude", "model": "c", "api_key": "k"},
        },
    }
    resp = client.post("/api/chat", json=body)
    assert resp.status_code == 422  # validation error for empty message


def test_chat_endpoint_returns_sse():
    """Chat endpoint returns text/event-stream."""
    with patch("backend.app.activities.chat._handle_chat") as mock_handle:
        async def fake_stream():
            yield b"event: done\ndata: {}\n\n"
        mock_handle.return_value = fake_stream()

        body = {
            "message": "I want to analyze AAPL",
            "history": [],
            "direction": None,
            "user_preferences": {
                "language": "en",
                "llm_config": {"provider": "claude", "model": "claude-sonnet-4-6", "api_key": "sk-test"},
            },
        }
        resp = client.post("/api/chat", json=body)
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")


def test_chat_endpoint_stream_contains_done_event():
    """SSE stream ends with done event."""
    with patch("backend.app.activities.chat._handle_chat") as mock_handle:
        async def fake_stream():
            yield b"event: clarification\ndata: {\"phase\": \"discovery\"}\n\n"
            yield b"event: done\ndata: {}\n\n"
        mock_handle.return_value = fake_stream()

        body = {
            "message": "Hi",
            "history": [],
            "direction": None,
            "user_preferences": {
                "language": "en",
                "llm_config": {"provider": "openai", "model": "gpt-4o-mini", "api_key": "sk-test"},
            },
        }
        resp = client.post("/api/chat", json=body)
        assert resp.status_code == 200
        assert b"event: done" in resp.content


def test_chat_endpoint_requires_user_preferences():
    body = {
        "message": "Hi",
        "history": [],
        "direction": None,
    }
    resp = client.post("/api/chat", json=body)
    assert resp.status_code == 422  # missing required user_preferences


def test_format_sse():
    """Test the SSE formatter helper."""
    from backend.app.activities.chat import _format_sse
    result = _format_sse("test", {"key": "value"})
    assert "event: test" in result
    assert '{"key": "value"}' in result


def test_format_sse_no_data():
    """Test the SSE formatter with no data."""
    from backend.app.activities.chat import _format_sse
    result = _format_sse("done")
    assert "event: done" in result
    assert result.endswith("\n\n")
