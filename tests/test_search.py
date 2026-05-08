from unittest.mock import patch
from backend.app.models.schemas import AssetSearchResult


def test_search_endpoint_returns_results(client):
    with patch("backend.app.activities.search.search_proxy") as mock_search:
        mock_search.return_value = [
            AssetSearchResult(
                symbol="AAPL",
                name="Apple Inc.",
                exchange="NMS",
                type="stock",
                market="us_market",
                currency="USD",
            )
        ]
        response = client.get("/api/search?q=AAPL")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"


def test_search_endpoint_empty_query_returns_empty(client):
    response = client.get("/api/search?q=")
    assert response.status_code == 200
    assert response.json() == []
