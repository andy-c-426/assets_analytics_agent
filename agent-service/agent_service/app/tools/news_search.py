from langchain_core.tools import tool


@tool
def search_latest_news(query: str, max_results: int = 5) -> str:
    """Search the web for latest news and information about a topic or symbol.
    Use this when you need current news, analyst opinions, or recent developments
    that yfinance might not have.

    Args:
        query: Search query (e.g. "AAPL stock news today", "Tesla earnings 2026")
        max_results: Maximum number of news results to return (default 5)
    """
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for item in ddgs.news(query, max_results=max_results):
                results.append(
                    f"- [{item.get('date', 'N/A')}] {item['title']}\n"
                    f"  {item.get('body', '')[:300]}\n"
                    f"  Source: {item.get('source', 'N/A')} | URL: {item.get('url', 'N/A')}"
                )

        if not results:
            return f"No news found for query: {query}"

        return f"Latest news for '{query}' ({len(results)} results):\n\n" + "\n\n".join(results)

    except ImportError:
        return "Error: duckduckgo_search package not installed"
    except Exception as e:
        return f"Error searching news for '{query}': {e}"
