from unittest.mock import patch, MagicMock
from backend.app.proxy.yfinance import search, fetch_asset, fetch_price_history


@patch("backend.app.proxy.yfinance.yf.Ticker")
def test_fetch_asset_returns_detail(mock_ticker):
    mock_ticker.return_value.get_info.return_value = {
        "symbol": "AAPL",
        "shortName": "Apple Inc.",
        "sector": "Technology",
        "marketCap": 3000000000000,
        "currentPrice": 195.50,
        "previousClose": 194.80,
        "trailingPE": 32.5,
        "currency": "USD",
        "news": [],
    }
    result = fetch_asset("AAPL")
    assert result.symbol == "AAPL"
    assert result.profile.name == "Apple Inc."
    assert result.price.current == 195.50
    assert result.metrics.pe_ratio == 32.5


@patch("backend.app.proxy.yfinance.yf.Search")
def test_search_returns_results(mock_search):
    mock_search.return_value.quotes = [
        {"symbol": "AAPL", "shortname": "Apple Inc.", "exchange": "NMS", "quoteType": "EQUITY", "market": "us_market", "currency": "USD"},
    ]
    results = search("AAPL")
    assert len(results) > 0


@patch("backend.app.proxy.yfinance.yf.Ticker")
def test_fetch_price_history_returns_ohlcv(mock_ticker):
    import pandas as pd
    mock_ticker.return_value.history.return_value = pd.DataFrame({
        "Open": [195.0, 196.0],
        "High": [196.5, 197.0],
        "Low": [194.5, 195.5],
        "Close": [196.0, 196.5],
        "Volume": [50000000, 52000000],
    }, index=pd.to_datetime(["2026-05-01", "2026-05-02"]))
    result = fetch_price_history("AAPL", "1mo")
    assert len(result) == 2
    assert result[0].date == "2026-05-01"
    assert result[0].open == 195.0
