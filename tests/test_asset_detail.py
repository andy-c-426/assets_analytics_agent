from unittest.mock import patch
from backend.app.models.schemas import (
    AssetDetail, AssetProfile, PriceData, KeyMetrics
)


def test_asset_detail_endpoint(client):
    mock_detail = AssetDetail(
        symbol="AAPL",
        profile=AssetProfile(name="Apple Inc.", sector="Technology"),
        price=PriceData(current=195.50, currency="USD"),
        metrics=KeyMetrics(pe_ratio=32.5),
        news=[],
    )
    with patch("backend.app.activities.asset_detail.fetch_asset", return_value=mock_detail):
        response = client.get("/api/assets/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["profile"]["name"] == "Apple Inc."
    assert data["price"]["current"] == 195.50
