from agent_service.app.tools.technicals import calculate_technicals


def test_calculate_technicals_metadata():
    assert calculate_technicals.name == "calculate_technicals"
    assert "symbol" in calculate_technicals.description.lower()


def test_calculate_technicals_empty_data():
    result = calculate_technicals.invoke({"symbol": "TEST", "prices": []})
    assert "no price data" in result.lower()
    assert "TEST" in result


def test_calculate_technicals_insufficient_data():
    prices = [100.0, 101.0]
    result = calculate_technicals.invoke({"symbol": "TEST", "prices": prices})
    assert "need at least" in result.lower()


def test_calculate_technicals_computes_metrics():
    prices = [100.0 + i * 0.5 for i in range(30)]
    result = calculate_technicals.invoke({"symbol": "TEST", "prices": prices})
    assert "TEST" in result
    assert "SMA" in result
    assert "RSI" in result
    assert "Volatility" in result
