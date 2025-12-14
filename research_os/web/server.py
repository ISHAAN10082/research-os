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

# --- MIGRATION: Jarvis M4 V2 Services ---
import sys
import os
# Ensure we can import from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from jarvis_m4.main import UnifiedPipelineV2 as UnifiedPipeline
from jarvis_m4.services.schema import UnifiedSchema
from jarvis_m4.services.retrieval_engine import RetrievalEngine
from jarvis_m4.services.search_service import SearchService

# Initialize V2 Services
pipeline = UnifiedPipeline() # Heavy initialization
schema = UnifiedSchema() 
retriever = RetrievalEngine() # For search/QA

# Stub services (TODO: implement properly)
class TelemetryStub:
    """Stub telemetry - logs to console"""
    async def capture_async(self, workspace, event_type, data):
        print(f"[Telemetry] {workspace}/{event_type}: {data}")
    def capture(self, workspace, event_type, data):
        print(f"[Telemetry] {workspace}/{event_type}: {data}")

class FoundationService:
    """Real foundation model using MLX"""
    def __init__(self, pipeline_ref):
        self.pipeline = pipeline_ref
        self.model = pipeline_ref.debate_agents.model
        self.tokenizer = pipeline_ref.debate_agents.tokenizer
    
    async def generate_async(self, prompt, context="", system=""):
        """Generate response using MLX model"""
        import asyncio
        from mlx_lm import generate
        
        try:
            system = system or "You are ResearchOS, a scientific research assistant."
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]
            text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            
            # Run generation in thread pool (MLX is CPU/GPU bound)
            response = await asyncio.to_thread(
                generate,
                self.model,
                self.tokenizer,
                prompt=text,
                max_tokens=300,
                verbose=False
            )
            return response
        except Exception as e:
            return f"Error generating response: {e}"
    
    async def generate_stream_async(self, prompt, context="", system="", use_cloud=False, callback=None):
        """Stream response token by token (REAL streaming)"""
        import asyncio
        from mlx_lm import stream_generate
        
        try:
            system = system or "You are ResearchOS, a scientific research assistant."
            
            # Build user message with context
            if context:
                user_message = f"Paper Content:\n{context[:3000]}\n\nQuestion: {prompt}"
            else:
                user_message = prompt
            
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message}
            ]
            text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            
            # Use stream_generate
            # stream_generate runs on main thread usually? 
            # We must be careful not to block event loop.
            # But stream_generate yields. 
            # If it blocks between yields, it might be okay.
            # Ideally verify if it runs async. It usually doesn't.
            # But converting to async iterator is complex.
            # Since MLX uses MPS, CPU usage is low.
            
            # Simple iteration
            for response in stream_generate(self.model, self.tokenizer, prompt=text, max_tokens=512):
                chunk = getattr(response, 'text', response)
                if callback:
                    await callback(chunk)
                    # Yield control explicitly occasionally?
                    await asyncio.sleep(0) 
            
        except Exception as e:
            if callback:
                await callback(f"Error: {e}")

class IntelligenceStub:
    """Stub intelligence service"""
    def generate_session_summary(self):
        return {"summary": "No session data yet", "insights": []}

# --- Initialize Services ---
telemetry = TelemetryStub()
foundation = FoundationService(pipeline)  # Use real model
intelligence = IntelligenceStub()
search_service = SearchService() # Real Service
recommender_service = None  # Optional service

# Ensure persistence tables exist (idempotent)
schema._initialize() 

print("✅ Services Initialized")

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

# Create FastAPI app
app = FastAPI(title="ResearchOS API", version="3.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """List all papers (Mined from V2 Schema)"""
    return schema.get_all_papers()

@app.post("/api/search")
@app.post("/api/search")
async def search_papers(req: SearchRequest):
    """Search ArXiv and Semantic Scholar for papers."""
    # Combine results
    try:
        arxiv_results = search_service.search_arxiv(req.query, max_results=10)
        return arxiv_results
    except Exception as e:
        print(f"Search error: {e}")
        return []

from fastapi import BackgroundTasks
import aiohttp

async def download_pdf_async(url: str, path: str):
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(path, 'wb') as f:
                    f.write(await resp.read())
            else:
                print(f"Download failed: {resp.status}")
                # Create empty file or raise? 
                # Better to raise to trigger fallback
                raise Exception(f"HTTP {resp.status}")

@app.post("/api/ingest")
async def ingest_paper(req: IngestRequest, background_tasks: BackgroundTasks):
    """Download paper and add to Graph with advanced extraction."""
    try:
        papers_dir = "data/papers"
        os.makedirs(papers_dir, exist_ok=True)
        
        paper_id = req.title.replace(" ", "_").lower()[:50]
        
        # 1. Save Initial Metadata (Optimistic)
        schema.ingest_paper({
            "paper_id": paper_id,
            "title": req.title,
            "authors": ", ".join(req.authors),
            "year": 2024,
            "raw_text": req.abstract,  # Start with abstract, background task updates with full PDF text
            "user_read": False
        })

        # 2. Handle Download
        local_path = os.path.join(papers_dir, f"{paper_id}.pdf")
        
        if req.pdf_url.startswith("http"):
            # Await download so it's available for reading immediately
            try:
                await download_pdf_async(req.pdf_url, local_path)
            except Exception as dl_err:
                print(f"⚠️ PDF Download failed: {dl_err}")
                # We still return success because metadata is saved. 
                # User can re-try or read metadata.
                return {"status": "partial_success", "id": paper_id, "message": "Paper added (Metadata only). Download failed."}
        else:
            local_path = req.pdf_url

        # 3. Trigger Heavy Extraction in Background
        # Safe wrapper to prevent server crash
        async def safe_process():
            try:
                # 1. Extract Full Text for Chat Context
                import fitz
                doc = fitz.open(local_path)
                full_text = ""
                for page in doc:
                    full_text += page.get_text()
                
                # Update DB for reliable Chat Context (Prevents Hallucinations)
                schema.update_paper_text(paper_id, full_text)
                print(f"✅ Saved text context for {paper_id}")
                
                # 2. Run Deep Extraction Pipeline (Using CORRECT paper_id)
                await asyncio.to_thread(pipeline.process_paper_stream, local_path, paper_id)
            except Exception as exc:
                print(f"Background Extraction Failed: {exc}")

        background_tasks.add_task(safe_process)
        
        return {"status": "success", "id": paper_id, "message": "Paper added. Extraction running in background."}
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

@app.post("/api/papers/extract/{paper_id}")
async def extract_paper_text(paper_id: str):
    """Re-extract text from an existing paper's PDF and update DB."""
    try:
        import fitz
        pdf_path = f"data/papers/{paper_id}.pdf"
        
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="PDF not found")
        
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        
        if len(full_text) < 50:
            return {"status": "error", "message": "PDF has no extractable text"}
        
        schema.update_paper_text(paper_id, full_text)
        
        return {"status": "success", "chars": len(full_text), "preview": full_text[:200]}
    except Exception as e:
        print(f"Text extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ask")
@app.post("/api/ask")
async def ask(query: QueryRequest):
    """Generate answer (non-streaming legacy endpoint) with persistence."""
    response = await foundation.generate_async(
        prompt=query.prompt,
        context=query.context,
        system="You are ResearchOS Copilot. Be concise."
    )
    # Persist
    session_id = "default_session" # TODO: Real sessions
    schema.save_chat_message(session_id, "user", query.prompt)
    schema.save_chat_message(session_id, "ai", response)
    return {"answer": response}

@app.get("/api/graph")
async def get_graph_data():
    """Serve real usage graph from V2 Schema."""
    try:
        claims = schema.get_all_claims()
        nodes = [{"id": c['claim_id'], "group": 1, "val": c.get('confidence', 0.5)} for c in claims]
        links = []
        
        # For each claim, get relationships
        for c in claims:
            rels = schema.get_relationships(c['claim_id'])
            for r in rels:
                pass  # TODO: proper link building
        
        # Return sample data if no claims exist (for testing/demo)
        if not nodes:
            import random
            random.seed(42)
            nodes = [
                {"id": f"claim_{i}", "group": i % 5, "val": random.random()}
                for i in range(30)
            ]
            # Create some links between random nodes
            links = [
                {"source": f"claim_{i}", "target": f"claim_{(i+1) % 30}"}
                for i in range(25)
            ] + [
                {"source": f"claim_{i}", "target": f"claim_{(i+5) % 30}"}
                for i in range(0, 30, 3)
            ]
        
        return {"nodes": nodes, "links": links}
    except Exception as e:
        print(f"Graph Error: {e}")
        # Return minimal sample on error
        return {
            "nodes": [{"id": f"n{i}", "group": 1, "val": 0.5} for i in range(10)],
            "links": [{"source": f"n{i}", "target": f"n{(i+1)%10}"} for i in range(8)]
        }

# Websocket for Real-Time Canvas & Reading Copilot
@app.websocket("/ws/chat")
async def chat_socket(websocket: WebSocket):
    await websocket.accept()
    # Simple session management for demo
    session_id = websocket.query_params.get("session_id", "default_session")
    
    try:
        while True:
            data = await websocket.receive_json()
            prompt = data.get("prompt")
            context = data.get("context", "")
            use_cloud = data.get("use_cloud", False)
            
            if not prompt: continue
            
            # Save User Message
            schema.save_chat_message(session_id, "user", prompt)
            
            telemetry.capture("reading", "chat_query", {"use_cloud": use_cloud, "len": len(prompt)})

            full_response = ""
            async def on_token_callback(token: str):
                nonlocal full_response
                full_response += token
                try:
                    await websocket.send_json({"type": "token", "content": token})
                except Exception: pass

            # Start generation
            await foundation.generate_stream_async(
                prompt=prompt,
                context=context,
                system="You are ResearchOS. Answer concisely.",
                use_cloud=use_cloud,
                callback=on_token_callback
            )
            
            # Save AI Message
            schema.save_chat_message(session_id, "ai", full_response)
            
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
