"""Shared LLM client factory for backend services."""

from langchain_core.language_models import BaseChatModel


def create_llm(
    provider: str,
    model: str,
    api_key: str,
    base_url: str | None = None,
) -> BaseChatModel:
    """Create a LangChain chat model for the given provider.

    Supported providers: claude, openai, deepseek
    """
    if provider == "claude":
        from langchain_anthropic import ChatAnthropic

        kwargs: dict = {
            "model": model,
            "api_key": api_key,
            "max_tokens": 4096,
        }
        if base_url:
            kwargs["base_url"] = base_url
        return ChatAnthropic(**kwargs)

    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": model,
            "api_key": api_key,
        }
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
        raise ValueError(f"Unsupported LLM provider: {provider}")
