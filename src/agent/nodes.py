"""Node implementations for the deep research agent."""

from __future__ import annotations

import re
from datetime import date

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from agent.configuration import Configuration
from agent.prompts import ANALYZE_PROMPT, PLAN_PROMPT, REFLECT_PROMPT, WRITE_PROMPT
from agent.state import AgentState, SearchResult
from agent.tools import search_web


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_config(config: RunnableConfig) -> Configuration:
    """Extract our Configuration from LangGraph's RunnableConfig."""
    raw = config.get("configurable", {})
    valid = {k: v for k, v in raw.items() if k in Configuration.__dataclass_fields__}
    return Configuration(**valid)


def _get_llm(config: RunnableConfig):
    """Initialize the LLM from the config's model string (e.g. 'openai/gpt-4o')."""
    model_str = _get_config(config).model
    if "/" in model_str:
        provider, model_name = model_str.split("/", 1)
        return init_chat_model(model_name, model_provider=provider)
    return init_chat_model(model_str)


def _get_user_query(state: AgentState) -> str:
    """Extract the original user query from the first HumanMessage."""
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            return msg.content
    return ""


def _parse_numbered_items(text: str, header: str) -> list[str]:
    """Extract numbered list items following a markdown header."""
    pattern = rf"#+\s*{re.escape(header)}\s*\n([\s\S]*?)(?=\n#+\s|\Z)"
    match = re.search(pattern, text)
    if not match:
        return []
    return [s.strip() for s in re.findall(r"\d+\.\s*(.+)", match.group(1))]


def _format_results(results: list[SearchResult]) -> str:
    """Format search results for inclusion in prompts."""
    return "\n\n".join(
        f"[{i}] {r.title}\nURL: {r.url}\n{r.content}"
        for i, r in enumerate(results, 1)
    )


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def plan_node(state: AgentState, config: RunnableConfig) -> dict:
    """Generate a research plan and initial search queries."""
    llm = _get_llm(config)
    query = _get_user_query(state)

    today = date.today()
    system = PLAN_PROMPT.format(today=today.isoformat(), year=today.year)

    response = llm.invoke([
        SystemMessage(content=system),
        HumanMessage(content=query),
    ])

    queries = _parse_numbered_items(response.content, "Search Queries")
    if not queries:
        queries = [query]  # fallback: use raw user query

    return {
        "messages": [response],
        "research_plan": response.content,
        "next_queries": queries,
        "findings": "",
        "iteration": 0,
    }


def search_node(state: AgentState, config: RunnableConfig) -> dict:
    """Execute web searches for pending queries."""
    cfg = _get_config(config)
    queries = state.get("next_queries", [])

    all_results: list[SearchResult] = []
    for q in queries:
        all_results.extend(search_web(q, max_results=cfg.max_results_per_search))

    return {
        "search_results": all_results,
        "queries": queries,       # appended to accumulated list
        "next_queries": [],       # consumed
    }


def analyze_node(state: AgentState, config: RunnableConfig) -> dict:
    """Compress search results into rolling findings summary."""
    llm = _get_llm(config)

    previous = state.get("findings", "")
    previous_section = f"## Previous Findings\n{previous}" if previous else "No previous findings."
    results_text = _format_results(state.get("search_results", []))

    prompt = ANALYZE_PROMPT.format(
        previous_findings=previous_section,
        search_results=results_text,
    )
    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "messages": [response],
        "findings": response.content,
    }


def reflect_node(state: AgentState, config: RunnableConfig) -> dict:
    """Evaluate coverage and decide whether to continue researching."""
    llm = _get_llm(config)
    cfg = _get_config(config)
    query = _get_user_query(state)

    prompt = REFLECT_PROMPT.format(
        query=query,
        research_plan=state.get("research_plan", ""),
        findings=state.get("findings", ""),
        queries="\n".join(f"- {q}" for q in state.get("queries", [])),
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content

    # Parse decision from the "### Decision" section
    decision_match = re.search(r"###\s*Decision\s*\n\s*(\w+)", content)
    should_continue = decision_match and decision_match.group(1).upper() == "CONTINUE"

    # Enforce max iterations
    iteration = state.get("iteration", 0) + 1
    if iteration >= cfg.max_iterations:
        should_continue = False

    new_queries: list[str] = []
    if should_continue:
        new_queries = _parse_numbered_items(content, "New Search Queries")

    return {
        "messages": [response],
        "iteration": iteration,
        "next_queries": new_queries,
    }


def write_node(state: AgentState, config: RunnableConfig) -> dict:
    """Generate the final research report."""
    llm = _get_llm(config)
    query = _get_user_query(state)

    prompt = WRITE_PROMPT.format(
        query=query,
        findings=state.get("findings", ""),
    )
    response = llm.invoke([HumanMessage(content=prompt)])

    return {"messages": [response]}
