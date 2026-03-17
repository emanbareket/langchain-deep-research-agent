"""Agent state definitions."""

from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages


@dataclass
class SearchResult:
    """A single search result with source metadata."""

    url: str
    title: str
    content: str


class AgentState(TypedDict):
    """Main graph state.

    Uses `add_messages` reducer on messages so new messages append rather than overwrite.
    Uses `operator.add` on queries so they accumulate across iterations.
    """

    messages: Annotated[list[AnyMessage], add_messages]
    """User input, internal tool calls / results, and final report."""

    search_results: list[SearchResult]
    """Latest batch of search results (overwritten each iteration for token management)."""

    research_plan: str
    """LLM-generated plan with sub-questions to investigate."""

    findings: str
    """Rolling compressed summary of research findings."""

    iteration: int
    """Current search-loop iteration (0-indexed)."""

    queries: Annotated[list[str], operator.add]
    """All search queries used so far (for REFLECT to avoid redundancy)."""

    next_queries: list[str]
    """Queries pending execution — set by PLAN/REFLECT, consumed by SEARCH."""
