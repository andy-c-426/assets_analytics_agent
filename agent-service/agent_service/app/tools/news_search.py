from langchain_core.tools import tool


@tool
def search_latest_news(query: str, max_results: int = 5) -> str:
    """General web search for broad topics via DuckDuckGo. NOT for ticker-specific news — use fetch_finnhub_news instead.

    Use this only when you need information that fetch_finnhub_news cannot cover,
    such as macroeconomic news, sector/industry trends, or non-ticker queries.

    Args:
        query: Search query (e.g. "semiconductor industry outlook 2026", "Fed interest rate decision")
        max_results: Maximum number of results to return (default 5)
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
