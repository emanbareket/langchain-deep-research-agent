"""Agent configuration — runtime-configurable parameters."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Configuration:
    """Configurable parameters for the deep research agent.

    These can be overridden at runtime via LangGraph's RunnableConfig:
        config = {"configurable": {"max_iterations": 5, "model": "anthropic/claude-3-5-sonnet-20241022"}}
    """

    model: str = "openai/gpt-4o"
    """LLM model in provider/model format (e.g. 'openai/gpt-4o', 'anthropic/claude-3-5-sonnet-20241022')."""

    max_iterations: int = 3
    """Maximum number of search-reflect iterations before forcing report generation."""

    max_results_per_search: int = 5
    """Number of results to retrieve per search query."""

    report_structure: str = "auto"
    """Report structure hint: 'auto' lets the LLM decide, or provide a custom outline."""
