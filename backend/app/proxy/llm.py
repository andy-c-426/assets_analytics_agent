from backend.app.models.schemas import AssetDetail


SYSTEM_PROMPT = """You are a professional financial analyst. Analyze the following asset based on the provided data and recent news. Structure your response with:

1. **Overview** — Brief summary of the company and current situation
2. **Key Metrics Analysis** — What the numbers mean
3. **Recent News Impact** — How recent news may affect the asset
4. **Risks & Opportunities**
5. **Outlook** — Short to medium term outlook

Be objective. Highlight both positives and negatives. Do not give specific buy/sell recommendations."""


def build_context(asset: AssetDetail) -> str:
    parts = [f"## Asset: {asset.profile.name} ({asset.symbol})"]

    if asset.profile.sector:
        parts.append(f"Sector: {asset.profile.sector}")
    if asset.profile.market_cap:
        parts.append(f"Market Cap: ${asset.profile.market_cap:,.0f}")
    if asset.profile.description:
        parts.append(f"\nDescription: {asset.profile.description}")

    parts.append(f"\n### Current Price")
    parts.append(f"Price: {asset.price.current} {asset.price.currency}")
    if asset.price.change_pct is not None:
        parts.append(f"Change: {asset.price.change_pct:.2f}%")

    parts.append(f"\n### Key Metrics")
    if asset.metrics.pe_ratio:
        parts.append(f"P/E Ratio: {asset.metrics.pe_ratio:.2f}")
    if asset.metrics.pb_ratio:
        parts.append(f"P/B Ratio: {asset.metrics.pb_ratio:.2f}")
    if asset.metrics.eps:
        parts.append(f"EPS: ${asset.metrics.eps:.2f}")
    if asset.metrics.dividend_yield:
        parts.append(f"Dividend Yield: {asset.metrics.dividend_yield * 100:.2f}%")
    if asset.metrics.beta:
        parts.append(f"Beta: {asset.metrics.beta:.2f}")

    if asset.news:
        parts.append(f"\n### Recent News ({len(asset.news)} articles)")
        for n in asset.news[:5]:
            parts.append(f"- {n.title}")
            if n.summary:
                parts.append(f"  {n.summary[:200]}")

    return "\n".join(parts)


def analyze(provider: str, model: str, api_key: str, context: str, base_url: str | None = None) -> str:
    if provider == "claude":
        return _analyze_claude(model, api_key, context, base_url)
    elif provider == "openai":
        return _analyze_openai(model, api_key, context, base_url)
    elif provider == "deepseek":
        return _analyze_deepseek(model, api_key, context, base_url)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def _analyze_claude(model: str, api_key: str, context: str, base_url: str | None) -> str:
    import anthropic
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = anthropic.Anthropic(**kwargs)
    message = client.messages.create(
        model=model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": context}],
    )
    return message.content[0].text


def _analyze_openai(model: str, api_key: str, context: str, base_url: str | None) -> str:
    from openai import OpenAI
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
        max_tokens=2048,
    )
    return response.choices[0].message.content or ""


def _analyze_deepseek(model: str, api_key: str, context: str, base_url: str | None) -> str:
    from openai import OpenAI
    kwargs = {
        "api_key": api_key,
        "base_url": base_url or "https://api.deepseek.com/v1",
    }
    client = OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
        max_tokens=2048,
    )
    return response.choices[0].message.content or ""
