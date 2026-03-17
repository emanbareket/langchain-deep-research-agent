"""Search tool integration."""

from __future__ import annotations

from datetime import datetime
from threading import current_thread
from time import perf_counter

from tavily import TavilyClient

from agent.state import SearchResult


def search_web(query: str, *, max_results: int = 5) -> list[SearchResult]:
    """Execute a web search via Tavily and return structured results."""
    start = perf_counter()
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(
        f"[search {timestamp}] start thread={current_thread().name} "
        f"max_results={max_results} query={query[:120]!r}",
        flush=True,
    )
    client = TavilyClient()  # reads TAVILY_API_KEY from env
    response = client.search(query, max_results=max_results)
    results = [
        SearchResult(
            url=r.get("url", ""),
            title=r.get("title", ""),
            content=r.get("content", ""),
        )
        for r in response.get("results", [])
    ]
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(
        f"[search {timestamp}] done thread={current_thread().name} "
        f"results={len(results)} dur={perf_counter() - start:.2f}s query={query[:120]!r}",
        flush=True,
    )
    return results
