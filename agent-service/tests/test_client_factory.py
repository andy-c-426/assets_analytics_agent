import pytest
from agent_service.app.llm.client_factory import create_chat_model, provider_default_model


def test_default_models():
    assert provider_default_model("claude") == "claude-sonnet-4-6"
    assert provider_default_model("openai") == "gpt-4o"
    assert provider_default_model("deepseek") == "deepseek-chat"


def test_create_chat_model_claude():
    model = create_chat_model(
        provider="claude",
        model="claude-sonnet-4-6",
        api_key="test-key",
    )
    assert model is not None
    assert model.model == "claude-sonnet-4-6"


def test_create_chat_model_openai():
    model = create_chat_model(
        provider="openai",
        model="gpt-4o",
        api_key="test-key",
    )
    assert model is not None
    assert model.model_name == "gpt-4o"


def test_create_chat_model_deepseek():
    model = create_chat_model(
        provider="deepseek",
        model="deepseek-chat",
        api_key="test-key",
    )
    assert model is not None
    assert model.model_name == "deepseek-chat"


def test_create_chat_model_with_base_url():
    model = create_chat_model(
        provider="openai",
        model="gpt-4o",
        api_key="test-key",
        base_url="https://custom.api.com/v1",
    )
    assert model is not None


def test_unsupported_provider_raises():
    with pytest.raises(ValueError, match="Unsupported provider"):
        create_chat_model(provider="unknown", model="x", api_key="x")
