import pytest
from agent_service.app.tools.yfinance_tools import fetch_asset_data, fetch_price_history


@pytest.mark.integration
def test_fetch_asset_data_real():
    """Integration test — hits yfinance. Skip in CI without network."""
    result = fetch_asset_data.invoke({"symbol": "AAPL"})
    assert "AAPL" in result


@pytest.mark.integration
def test_fetch_price_history_real():
    """Integration test — hits yfinance. Skip in CI without network."""
    result = fetch_price_history.invoke({"symbol": "AAPL", "period": "1mo"})
    assert "AAPL" in result


def test_fetch_asset_data_has_correct_metadata():
    assert fetch_asset_data.name == "fetch_asset_data"
    assert "symbol" in fetch_asset_data.description.lower()


def test_fetch_price_history_has_correct_metadata():
    assert fetch_price_history.name == "fetch_price_history"
    assert "symbol" in fetch_price_history.description.lower()
