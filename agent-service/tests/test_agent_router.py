from fastapi.testclient import TestClient
from agent_service.app.main import app


def test_analyze_endpoint_returns_sse_stream():
    """Verify the analyze endpoint exists and returns SSE content type."""
    client = TestClient(app)
    response = client.post(
        "/analyze/AAPL",
        json={
            "provider": "claude",
            "model": "claude-sonnet-4-6",
            "api_key": "test-key",
        },
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")


def test_analyze_endpoint_validates_body():
    """Missing required fields should be rejected with 422."""
    client = TestClient(app)
    response = client.post(
        "/analyze/AAPL",
        json={"provider": "", "model": "", "api_key": ""},
    )
    assert response.status_code == 422


def test_router_is_mounted():
    """Verify the analyze route is registered."""
    client = TestClient(app)
    routes = [r.path for r in app.routes]
    assert "/analyze/{symbol}" in routes
