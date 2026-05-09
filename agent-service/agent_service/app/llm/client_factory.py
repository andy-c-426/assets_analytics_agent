from langchain_core.language_models import BaseChatModel


def provider_default_model(provider: str) -> str:
    defaults = {
        "claude": "claude-sonnet-4-6",
        "openai": "gpt-4o",
        "deepseek": "deepseek-chat",
    }
    if provider not in defaults:
        raise ValueError(f"Unsupported provider: {provider}")
    return defaults[provider]


def create_chat_model(
    provider: str,
    model: str,
    api_key: str,
    base_url: str | None = None,
) -> BaseChatModel:
    if provider == "claude":
        from langchain_anthropic import ChatAnthropic

        kwargs = {"model": model, "api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return ChatAnthropic(**kwargs)

    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        kwargs = {"model": model, "api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return ChatOpenAI(**kwargs)

    elif provider == "deepseek":
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": model,
            "api_key": api_key,
            "base_url": base_url or "https://api.deepseek.com/v1",
        }
        return ChatOpenAI(**kwargs)

    else:
        raise ValueError(f"Unsupported provider: {provider}")
