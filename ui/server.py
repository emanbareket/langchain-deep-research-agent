"""Lightweight FastAPI server that runs the research graph directly."""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure the src directory is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from agent.graph import graph  # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402

app = FastAPI(title="Deep Research Agent")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

UI_DIR = Path(__file__).parent


class ResearchRequest(BaseModel):
    query: str
    max_iterations: int = 3
    comprehension_threshold: int = 90
    report_style: str = "detailed"


@app.get("/")
async def index():
    return FileResponse(UI_DIR / "index.html")


@app.post("/api/research")
async def research(req: ResearchRequest):
    """Stream node progress as SSE, then the final report."""

    def event_stream():
        def emit(payload: dict):
            return f"data: {json.dumps(payload)}\n\n"

        initial_state = {
            "messages": [HumanMessage(content=req.query)],
            "search_results": [],
            "research_plan": "",
            "findings": "",
            "iteration": 0,
            "queries": [],
            "next_queries": [],
            "comprehension_score": 0,
        }

        run_config = {"configurable": {
            "max_iterations": req.max_iterations,
            "comprehension_threshold": req.comprehension_threshold,
            "report_style": req.report_style,
        }}

        final_report = ""
        yield emit({"active_node": "plan", "status": "Planning research..."})
        for event in graph.stream(initial_state, config=run_config, stream_mode="updates"):
            for node_name, updates in event.items():
                payload = {"node": node_name}
                if "iteration" in updates:
                    payload["iteration"] = updates["iteration"]
                if "comprehension_score" in updates:
                    payload["score"] = updates["comprehension_score"]
                if "next_queries" in updates:
                    payload["pending_queries"] = updates["next_queries"]
                if node_name == "plan":
                    payload["status"] = "Planning research..."
                elif node_name == "search":
                    payload["search_complete"] = True
                    payload["status"] = "Searching the web..."
                elif node_name == "analyze":
                    payload["status"] = "Analyzing search results..."
                elif node_name == "reflect":
                    payload["status"] = "Evaluating coverage..."
                    if not updates.get("next_queries"):
                        payload["status"] = "Gathering final report..."
                elif node_name == "write":
                    payload["status"] = "Gathering final report..."
                # Capture final report from write node
                if node_name == "write" and "messages" in updates:
                    msgs = updates["messages"]
                    if msgs:
                        final_report = msgs[-1].content
                        payload["report"] = final_report
                yield emit(payload)

                if node_name == "plan":
                    yield emit(
                        {
                            "active_node": "search",
                            "status": "Searching the web...",
                            "iteration": 1,
                            "pending_queries": updates.get("next_queries", []),
                        }
                    )
                elif node_name == "search":
                    yield emit({"active_node": "analyze", "status": "Analyzing search results..."})
                elif node_name == "analyze":
                    yield emit({"active_node": "reflect", "status": "Evaluating coverage..."})
                elif node_name == "reflect":
                    next_queries = updates.get("next_queries", [])
                    if next_queries:
                        yield emit(
                            {
                                "active_node": "search",
                                "status": "Searching the web...",
                                "iteration": updates.get("iteration", 0) + 1,
                                "pending_queries": next_queries,
                            }
                        )
                    else:
                        yield emit({"active_node": "write", "status": "Gathering final report..."})

        # If report wasn't in the last event, send it now
        if final_report and "report" not in json.dumps(payload):
            yield emit({"done": True, "report": final_report})
        yield emit({"done": True})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8123)
