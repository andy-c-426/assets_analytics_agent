from unittest.mock import patch


def test_analyze_endpoint(client):
    with patch("backend.app.activities.analyze.fetch_asset") as mock_fetch, \
         patch("backend.app.activities.analyze.analyze_asset") as mock_analyze:

        from backend.app.models.schemas import AssetDetail, AssetProfile, PriceData, KeyMetrics
        mock_fetch.return_value = AssetDetail(
            symbol="AAPL",
            profile=AssetProfile(name="Apple Inc."),
            price=PriceData(current=195.50, currency="USD"),
            metrics=KeyMetrics(),
            news=[],
        )
        mock_analyze.return_value = "Great analysis here."

        response = client.post("/api/analyze/AAPL", json={
            "provider": "claude",
            "model": "claude-sonnet-4-6",
            "api_key": "sk-test-key",
        })

    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["analysis"] == "Great analysis here."
    assert data["model_used"] == "claude-sonnet-4-6"
    assert "data_points" in data["context_sent"]
    assert "news_count" in data["context_sent"]
