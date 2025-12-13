# ResearchOS Web Server
"""
FastAPI backend for the High-Fidelity ResearchOS Canvas UI.
Serves the React frontend and provides API endpoints for the Hybrid Engine.
"""

from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import os
from typing import List

from research_os.foundation.core import foundation
from research_os.foundation.graph import graph_engine
from research_os.features import PaperWhisper, Bibliography

app = FastAPI(title="ResearchOS Canvas")
# ... (CORS middleware) ...

# Shared State
class ServerState:
    whisper = PaperWhisper(foundation)
    bibliography = Bibliography()

state = ServerState()

from research_os.system.spatial_telemetry import telemetry
from research_os.system.workspace_analytics import analytics
from research_os.system.research_intelligence import intelligence
from research_os.services.entity_extraction import get_extractor
from research_os.services.pdf_extraction import grobid
from research_os.services.recommender import init_recommender, recommender_service

# Models
class QueryRequest(BaseModel):
    prompt: str
    context: str = ""

class SearchRequest(BaseModel):
    query: str

class IngestRequest(BaseModel):
    title: str
    pdf_url: str
    abstract: str = ""
    authors: List[str] = []

class EventRequest(BaseModel):
    workspace: str
    event_type: str
    data: dict

# API Endpoints

# --- Telemetry & Intelligence ---
@app.post("/api/telemetry/event")
async def record_event(evt: EventRequest):
    """Log frontend events to SQLite WAL."""
    await telemetry.capture_async(evt.workspace, evt.event_type, evt.data)
    return {"status": "recorded"}

@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    """Get high-level insights."""
    return intelligence.generate_session_summary()

# --- Data & Reading ---
@app.get("/api/papers")
async def list_papers():
    """List all papers for Reading Mode."""
    papers = graph_engine.get_all_papers()
    # Initialize recommender with latest data if needed
    # Note: In production, this should be done on a schedule/background task
    if recommender_service is None or len(papers) > 0:
         init_recommender(papers)
    return papers

@app.post("/api/search")
async def search_papers(req: SearchRequest):
    """Search ArXiv for papers."""
    results = search_service.search_arxiv(req.query, max_results=15)
    return results

@app.post("/api/ingest")
async def ingest_paper(req: IngestRequest):
    """Download paper and add to Graph with advanced extraction."""
    try:
        # 1. Download
        path = search_service.download_paper(req.pdf_url, req.title)
        if not path:
             raise HTTPException(status_code=500, detail="Failed to download PDF")
             
        # 2. Add to Graph
        graph_engine.add_paper(req.title, path, req.abstract)
        
        # 3. Optional: Advanced Extraction
        # Run in background to not block UI
        telemetry.capture("system", "ingest_start", {"title": req.title})
        
        return {"status": "success", "path": path}
    except Exception as e:
        print(f"Ingest Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommend/similar/{paper_id}")
async def recommend_similar(paper_id: str):
    if recommender_service:
        return recommender_service.recommend(paper_id)
    return []

@app.get("/api/extract/entities/{paper_id}")
async def extract_entities(paper_id: str):
    """Extract NER entities from paper abstract (full text TODO)."""
    # For now, just extracting from abstract usually stored in DB could operate on PDF text
    # This is a placeholder hooking up the service
    return {"entities": []} # TODO: Fetch abstract from DB and run get_extractor().extract(abst)

@app.get("/api/papers/pdf")
async def get_paper_pdf(path: str):
    """Serve PDF file (requires full path)."""
    if os.path.exists(path) and path.lower().endswith(".pdf"):
        # Log reading event
        telemetry.capture("reading", "open_pdf", {"path": path})
        return FileResponse(path, media_type='application/pdf')
    raise HTTPException(status_code=404, detail="PDF not found")

@app.post("/api/ask")
async def ask(query: QueryRequest):
    """Generate answer (non-streaming legacy endpoint)."""
    response = await foundation.generate_async(
        prompt=query.prompt,
        context=query.context,
        system="You are ResearchOS Copilot. Be concise."
    )
    return {"answer": response}

@app.get("/api/graph")
async def get_graph_data():
    """Serve real citation network for 3D visualization."""
    return graph_engine.get_citation_graph()

# Websocket for Real-Time Canvas & Reading Copilot
@app.websocket("/ws/chat")
async def chat_socket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            prompt = data.get("prompt")
            context = data.get("context", "")
            use_cloud = data.get("use_cloud", False) # Support Model Choice
            
            if not prompt:
                continue
            
            # Log usage
            telemetry.capture("reading", "chat_query", {"use_cloud": use_cloud, "len": len(prompt)})

            async def on_token_callback(token: str):
                try:
                    await websocket.send_json({"type": "token", "content": token})
                except Exception:
                    pass

            # Start generation
            await foundation.generate_stream_async(
                prompt=prompt,
                context=context,
                system="You are ResearchOS. Answer concisely.",
                use_cloud=use_cloud,
                callback=on_token_callback
            )
            
            # Signal done
            await websocket.send_json({"type": "done"})
            
    except Exception as e:
        print(f"Chat WS Error: {e}")

@app.websocket("/ws/canvas")
async def canvas_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # Log canvas event
            telemetry.capture("synthesis", "canvas_update", {"type": data.get("type")})
            
            # Echo back for now
            await websocket.send_json({"event": "echo", "data": data})
    except Exception as e:
        print(f"WS Error: {e}")

# Static Files (Frontend)
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

@app.get("/graph")
async def graph_ui():
    """Serve the Graph Exploration UI."""
    return FileResponse(os.path.join(static_dir, "graph.html"))

def start_server(port=8000):
    import uvicorn
    # Minimal config to silence Uvicorn explicitly
    # This avoids TypeError: Handler.__init__() got an unexpected keyword argument 'stream'
    # by not inheriting the default uvicorn config kwargs.
    log_config = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "null": {
                "class": "logging.NullHandler",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["null"], "level": "CRITICAL", "propagate": False},
            "uvicorn.error": {"handlers": ["null"], "level": "CRITICAL", "propagate": False},
            "uvicorn.access": {"handlers": ["null"], "level": "CRITICAL", "propagate": False},
        },
    }
    
    # Run without standard signal handlers to play nice with TUI threads
    uvicorn.run(app, host="0.0.0.0", port=port, log_config=log_config, access_log=False)

if __name__ == "__main__":
    start_server()
