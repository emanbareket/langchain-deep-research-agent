"""Node implementations for the deep research agent."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from time import perf_counter

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from agent.configuration import Configuration
from agent.prompts import (
    COMPRESS_PROMPT,
    PLAN_PROMPT,
    REFLECT_PROMPT,
    WRITE_BRIEF_PROMPT,
    WRITE_DETAILED_PROMPT,
)
from agent.schemas import PlanOutput, ReflectOutput
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
    """Initialize the LLM, defaulting by report style unless manually overridden."""
    cfg = _get_config(config)
    if cfg.model != "auto":
        model_str = cfg.model
    else:
        model_str = cfg.brief_model if cfg.report_style == "brief" else cfg.detailed_model
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


def _format_results(results: list[SearchResult]) -> str:
    """Format search results for inclusion in prompts."""
    return "\n\n".join(
        f"[{i}] {r.title}\nURL: {r.url}\n{r.content}"
        for i, r in enumerate(results, 1)
    )


def _log(message: str) -> None:
    """Emit timestamped logs for long-running agent steps."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[agent {timestamp}] {message}", flush=True)


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def plan_node(state: AgentState, config: RunnableConfig) -> dict:
    """Generate a research plan and initial search queries."""
    start = perf_counter()
    llm = _get_llm(config)
    query = _get_user_query(state)
    _log(f"PLAN start query={query[:120]!r}")

    today = date.today()
    system = PLAN_PROMPT.format(today=today.isoformat(), year=today.year)

    structured_llm = llm.with_structured_output(PlanOutput)
    plan: PlanOutput = structured_llm.invoke([
        SystemMessage(content=system),
        HumanMessage(content=query),
    ])

    queries = plan.search_queries or [query]  # fallback: use raw user query

    # Build a readable plan string for the REFLECT node
    plan_text = "\n".join(
        f"{i}. {q} → search: {s}"
        for i, (q, s) in enumerate(zip(plan.sub_questions, queries), 1)
    )
    _log(f"PLAN done queries={len(queries)} dur={perf_counter() - start:.2f}s")

    return {
        "messages": [AIMessage(content=plan_text)],
        "research_plan": plan_text,
        "next_queries": queries,
        "findings": "",
        "iteration": 0,
    }


def search_node(state: AgentState, config: RunnableConfig) -> dict:
    """Execute web searches for pending queries."""
    start = perf_counter()
    cfg = _get_config(config)
    queries = state.get("next_queries", [])

    if not queries:
        _log("SEARCH skipped (no pending queries)")
        return {
            "search_results": [],
            "queries": [],
            "next_queries": [],
        }

    results_by_query: dict[str, list[SearchResult]] = {q: [] for q in queries}
    failures: list[str] = []
    max_workers = min(5, len(queries))
    _log(f"SEARCH start queries={len(queries)} max_workers={max_workers}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_query = {
            executor.submit(search_web, q, max_results=cfg.max_results_per_search): q
            for q in queries
        }

        for future in as_completed(future_to_query):
            query = future_to_query[future]
            try:
                results_by_query[query] = future.result()
                _log(f"SEARCH result query={query[:80]!r} results={len(results_by_query[query])}")
            except Exception as exc:
                failures.append(f"{query}: {exc}")
                _log(f"SEARCH failed query={query[:80]!r} err={exc}")

    all_results: list[SearchResult] = []
    for query in queries:
        all_results.extend(results_by_query[query])

    messages = []
    if failures:
        messages.append(
            AIMessage(
                content=(
                    "Some searches failed but research continued:\n"
                    + "\n".join(f"- {failure}" for failure in failures)
                )
            )
        )

    _log(
        "SEARCH done "
        f"queries={len(queries)} results={len(all_results)} failures={len(failures)} "
        f"dur={perf_counter() - start:.2f}s"
    )

    return {
        "messages": messages,
        "search_results": all_results,
        "queries": queries,
        "next_queries": [],
    }


def analyze_node(state: AgentState, config: RunnableConfig) -> dict:
    """Append raw search results, compressing accumulated findings only when needed."""
    start = perf_counter()
    cfg = _get_config(config)
    results_text = _format_results(state.get("search_results", []))
    previous = state.get("findings", "")
    iteration = state.get("iteration", 0) + 1
    new_section = f"### Iteration {iteration}\n{results_text}"
    updated = f"{previous}\n\n{new_section}".strip()
    _log(
        f"ANALYZE start iteration={iteration} new_chars={len(results_text)} "
        f"updated_chars={len(updated)} threshold={cfg.max_findings_chars}"
    )

    if len(updated) <= cfg.max_findings_chars:
        _log(f"ANALYZE stored raw findings iteration={iteration} dur={perf_counter() - start:.2f}s")
        return {
            "messages": [AIMessage(content=f"Stored raw findings from iteration {iteration} ({len(results_text)} chars).")],
            "findings": updated,
        }

    llm = _get_llm(config)
    score = max(0, state.get("comprehension_score", 0))
    threshold = max(1, cfg.comprehension_threshold)
    compression_ratio = min(1.0, score / threshold)
    compression_ratio = max(0.25, compression_ratio)
    target_chars = int(cfg.max_findings_chars * compression_ratio)
    min_chars = max(1000, int(target_chars * 0.9))

    prompt = COMPRESS_PROMPT.format(
        findings=updated,
        input_chars=len(updated),
        target_chars=target_chars,
        min_chars=min_chars,
    )
    _log(
        f"ANALYZE compress iteration={iteration} input={len(updated)} "
        f"target={target_chars} min={min_chars} score={score}/{cfg.comprehension_threshold}"
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    _log(
        f"ANALYZE compressed iteration={iteration} output={len(response.content)} "
        f"dur={perf_counter() - start:.2f}s"
    )

    return {
        "messages": [
            AIMessage(
                content=(
                    f"Compressed findings from {len(updated)} to {len(response.content)} chars "
                    f"(target ~{target_chars}, score={score}/{cfg.comprehension_threshold})."
                )
            )
        ],
        "findings": response.content,
    }


def reflect_node(state: AgentState, config: RunnableConfig) -> dict:
    """Evaluate coverage and decide whether to continue researching."""
    start = perf_counter()
    llm = _get_llm(config)
    cfg = _get_config(config)
    query = _get_user_query(state)
    _log(
        f"REFLECT start iteration={state.get('iteration', 0) + 1} "
        f"findings_chars={len(state.get('findings', ''))}"
    )

    prompt = REFLECT_PROMPT.format(
        query=query,
        research_plan=state.get("research_plan", ""),
        findings=state.get("findings", ""),
        queries="\n".join(f"- {q}" for q in state.get("queries", [])),
        year=date.today().year,
        target_score=cfg.comprehension_threshold,
    )

    structured_llm = llm.with_structured_output(ReflectOutput)
    reflection: ReflectOutput = structured_llm.invoke([HumanMessage(content=prompt)])

    score = max(0, min(100, reflection.comprehension_score))
    should_continue = score < cfg.comprehension_threshold

    # Enforce max iterations
    iteration = state.get("iteration", 0) + 1
    if iteration >= cfg.max_iterations:
        should_continue = False

    new_queries = reflection.new_search_queries if should_continue else []
    _log(
        f"REFLECT done iteration={iteration} score={score} "
        f"next_queries={len(new_queries)} dur={perf_counter() - start:.2f}s"
    )

    return {
        "messages": [AIMessage(content=f"[score={score}] {reflection.assessment}")],
        "iteration": iteration,
        "comprehension_score": score,
        "next_queries": new_queries,
    }


def write_node(state: AgentState, config: RunnableConfig) -> dict:
    """Generate the final research report."""
    start = perf_counter()
    llm = _get_llm(config)
    cfg = _get_config(config)
    query = _get_user_query(state)
    _log(f"WRITE start style={cfg.report_style} findings_chars={len(state.get('findings', ''))}")

    template = WRITE_BRIEF_PROMPT if cfg.report_style == "brief" else WRITE_DETAILED_PROMPT
    prompt = template.format(
        query=query,
        findings=state.get("findings", ""),
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    _log(f"WRITE done output_chars={len(response.content)} dur={perf_counter() - start:.2f}s")

    return {"messages": [response]}
