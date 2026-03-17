"""Search tool integration."""

from __future__ import annotations

from tavily import TavilyClient

from agent.state import SearchResult


def search_web(query: str, *, max_results: int = 5) -> list[SearchResult]:
    """Execute a web search via Tavily and return structured results."""
    client = TavilyClient()  # reads TAVILY_API_KEY from env
    response = client.search(query, max_results=max_results)

    return [
        SearchResult(
            url=r.get("url", ""),
            title=r.get("title", ""),
            content=r.get("content", ""),
        )
        for r in response.get("results", [])
    ]
