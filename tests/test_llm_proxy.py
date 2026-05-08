from unittest.mock import patch, MagicMock
from backend.app.proxy.llm import build_context, analyze
from backend.app.models.schemas import (
    AssetDetail, AssetProfile, PriceData, KeyMetrics, NewsArticle
)


def test_build_context_includes_key_sections():
    asset = AssetDetail(
        symbol="AAPL",
        profile=AssetProfile(name="Apple Inc.", sector="Technology", market_cap=3000000000000),
        price=PriceData(current=195.50, change_pct=0.36, currency="USD"),
        metrics=KeyMetrics(pe_ratio=32.5, eps=6.0),
        news=[
            NewsArticle(title="Apple Launches New Product", summary="Exciting new release...")
        ],
    )
    ctx = build_context(asset)
    assert "Apple Inc." in ctx
    assert "Technology" in ctx
    assert "195.5" in ctx
    assert "32.50" in ctx
    assert "Apple Launches New Product" in ctx


@patch("backend.app.proxy.llm._analyze_claude")
def test_analyze_routes_to_claude(mock_claude):
    mock_claude.return_value = "Analysis result from Claude"
    result = analyze("claude", "claude-sonnet-4-6", "sk-test", "some context")
    assert result == "Analysis result from Claude"
    mock_claude.assert_called_once()


@patch("backend.app.proxy.llm._analyze_openai")
def test_analyze_routes_to_openai(mock_openai):
    mock_openai.return_value = "Analysis from GPT"
    result = analyze("openai", "gpt-4o", "sk-test", "some context", None)
    assert result == "Analysis from GPT"


def test_analyze_unsupported_provider():
    try:
        analyze("unknown", "model", "key", "context")
    except ValueError as e:
        assert "Unsupported provider" in str(e)
