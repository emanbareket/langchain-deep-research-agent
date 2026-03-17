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


@app.get("/")
async def index():
    return FileResponse(UI_DIR / "index.html")


@app.post("/api/research")
async def research(req: ResearchRequest):
    """Stream node progress as SSE, then the final report."""

    def event_stream():
        initial_state = {
            "messages": [HumanMessage(content=req.query)],
            "search_results": [],
            "research_plan": "",
            "findings": "",
            "iteration": 0,
            "queries": [],
            "next_queries": [],
        }

        final_report = ""
        for event in graph.stream(initial_state, stream_mode="updates"):
            for node_name, updates in event.items():
                payload = {"node": node_name}
                if "iteration" in updates:
                    payload["iteration"] = updates["iteration"]
                # Capture final report from write node
                if node_name == "write" and "messages" in updates:
                    msgs = updates["messages"]
                    if msgs:
                        final_report = msgs[-1].content
                        payload["report"] = final_report
                yield f"data: {json.dumps(payload)}\n\n"

        # If report wasn't in the last event, send it now
        if final_report and "report" not in json.dumps(payload):
            yield f"data: {json.dumps({'done': True, 'report': final_report})}\n\n"
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8123)
