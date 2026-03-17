"""Graph assembly — wires nodes and edges into a compiled LangGraph."""

from langgraph.graph import END, StateGraph

from agent.nodes import analyze_node, plan_node, reflect_node, search_node, write_node
from agent.state import AgentState


def _should_continue(state: AgentState) -> str:
    """Route after REFLECT: loop back to SEARCH if there are pending queries, else WRITE."""
    if state.get("next_queries"):
        return "search"
    return "write"


# Build the graph
builder = StateGraph(AgentState)

builder.add_node("plan", plan_node)
builder.add_node("search", search_node)
builder.add_node("analyze", analyze_node)
builder.add_node("reflect", reflect_node)
builder.add_node("write", write_node)

builder.set_entry_point("plan")
builder.add_edge("plan", "search")
builder.add_edge("search", "analyze")
builder.add_edge("analyze", "reflect")
builder.add_conditional_edges("reflect", _should_continue, {"search": "search", "write": "write"})
builder.add_edge("write", END)

graph = builder.compile()
