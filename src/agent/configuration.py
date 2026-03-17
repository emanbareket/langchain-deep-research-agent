"""Agent configuration — runtime-configurable parameters."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Configuration:
    """Configurable parameters for the deep research agent.

    These can be overridden at runtime via LangGraph's RunnableConfig:
        config = {"configurable": {"max_iterations": 5, "model": "anthropic/claude-3-5-sonnet-20241022"}}
    """

    model: str = "auto"
    """Optional manual override for all LLM calls; use 'auto' to pick a model from report_style."""

    brief_model: str = "openai/gpt-5-mini"
    """Default model when report_style='brief' and model='auto'."""

    detailed_model: str = "openai/gpt-5.2"
    """Default model when report_style='detailed' and model='auto'."""

    max_iterations: int = 3
    """Maximum number of search-reflect iterations before forcing report generation."""

    comprehension_threshold: int = 90
    """Comprehension score (0-100) at which the agent stops researching and writes the report."""

    max_findings_chars: int = 50000
    """Soft maximum size for findings before they are compressed."""

    max_results_per_search: int = 5
    """Number of results to retrieve per search query."""

    report_style: str = "detailed"
    """Report style: 'brief' (~500-1000 words, key takeaways) or 'detailed' (~2000-4000 words, thorough)."""
