from unittest.mock import patch

from backend.app.models.schemas import OHLCV


def test_price_history_endpoint(client):
    mock_data = [
        OHLCV(date="2026-05-01", open=195.0, high=196.5, low=194.5, close=196.0, volume=50000000),
    ]
    with patch("backend.app.activities.price_history.fetch_price_history", return_value=mock_data):
        response = client.get("/api/assets/AAPL/price-history?period=1mo")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["date"] == "2026-05-01"


def test_price_history_default_period(client):
    with patch("backend.app.activities.price_history.fetch_price_history", return_value=[]) as mock:
        response = client.get("/api/assets/AAPL/price-history")
    assert response.status_code == 200
    mock.assert_called_once_with("AAPL", "1mo")
