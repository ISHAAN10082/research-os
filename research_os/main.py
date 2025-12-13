# research_os/main.py
"""Ambient Hybrid TUI entry point for ResearchOS.

Features:
- Full-screen TUI using prompt_toolkit + rich layout.
- Input field accepts commands (Enter to submit).
- Background log integration (loguru sink) displayed in sidebar.
- File watcher monitors ~/Downloads for PDFs and auto‑ingests.
- Arxiv integration for external search.
- Async command handling (search, ingest, ask, visualize, benchmark, topology).
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env vars from .env file
load_dotenv()

from loguru import logger
from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, HSplit, VSplit
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

# Local imports
from research_os.foundation.core import foundation
from research_os.ingestion.hydra import IngestionHydra
from research_os.ingestion.watcher import FileWatcher
from research_os.ingestion.resources import resources_client

# ---------------------------------------------------------------------------
# UI Components
# ---------------------------------------------------------------------------
class ResearchTUI:
    def __init__(self):
        # Log buffer for sidebar (max 10 lines)
        self.log_buffer: list[str] = []
        self.max_log_lines = 10

        # Output area (conversation / command results)
        self.output_field = TextArea(
            text="Welcome to ResearchOS Ambient Mode!\nType 'help' for commands.\n",
            scrollbar=True,
            wrap_lines=False,
            read_only=True,
            height=20,
        )

        # Input field – will capture Enter key via accept_handler
        self.input_field = TextArea(
            height=1,
            prompt=">>> ",
            multiline=False,
        )
        self.input_field.accept_handler = self._on_enter

        # Sidebar – shows system status, context, and log whispers
        self.sidebar = TextArea(
            text=self._build_sidebar(),
            read_only=True,
            height=24,
        )

        # Layout composition
        self.root_container = HSplit(
            [
                VSplit(
                    [
                        Frame(self.output_field, title="Uncertainty Engine (Conversation)"),
                        Frame(self.sidebar, title="Ambient Context (Watcher)"),
                    ],
                    padding=1,
                ),
                self.input_field,
            ]
        )
        self.layout = Layout(self.root_container, focused_element=self.input_field)

        # Key bindings (Ctrl+C to exit)
        self.kb = KeyBindings()
        @self.kb.add("c-c")
        def _(event):
            event.app.exit()

        # Prompt_toolkit style (optional)
        self.style = Style.from_dict({
            "frame.border": "#00ff00",
            "input-field": "bg:#444444 #ffffff",
        })

        # Application instance
        self.app = Application(
            layout=self.layout,
            key_bindings=self.kb,
            style=self.style,
            full_screen=True,
        )

    # -----------------------------------------------------------------------
    # UI helpers
    # -----------------------------------------------------------------------
    def _build_sidebar(self) -> str:
        """Construct sidebar text from current status and log buffer."""
        lines = []
        lines.append("[System]")
        lines.append("Status: NOMINAL")
        lines.append("Model: phi-3.5-mini-instruct-4bit")
        lines.append(f"Time: {self._current_time()}")
        lines.append("")
        lines.append("[Context]")
        lines.append("Paper: None")
        lines.append("Queries: 0")
        lines.append("")
        lines.append("[Log / Whispers]")
        for entry in self.log_buffer[-self.max_log_lines :]:
            lines.append(entry)
        return "\n".join(lines)

    def _current_time(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def add_log(self, message: str) -> None:
        """Append a log line and refresh sidebar."""
        # Trim and keep only last max_log_lines entries
        self.log_buffer.append(message)
        if len(self.log_buffer) > self.max_log_lines:
            self.log_buffer = self.log_buffer[-self.max_log_lines :]
        self.sidebar.text = self._build_sidebar()

    # -----------------------------------------------------------------------
    # Input handling
    # -----------------------------------------------------------------------
    def _on_enter(self, buffer) -> bool:
        """Called when user presses Enter in the input field.
        Returns True to keep the application running.
        """
        command = buffer.text.strip()
        buffer.text = ""  # clear input
        # Process command asynchronously – schedule on event loop
        asyncio.create_task(self.process_command(command))
        return False  # keep focus on input field

    async def process_command(self, command: str) -> None:
        """Parse and execute a single command string."""
        if not command:
            return
        parts = command.split(maxsplit=1)
        op = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        self.add_log(f"▶ {command}")
        if op == "help":
            self.print_output(
                """Commands:
  ask <question> – RAG answer with streaming
  search <query> – Hybrid retrieval
  ingest <path> – Process PDF/document
  
  === Novel Features ===
  whisper topics <t1,t2> – Set paper discovery topics
  whisper check – Check for new papers
  doubt on|off – Toggle devil's advocate mode
  doubt <claim> – Challenge a specific claim
  crystallize [topic] – Turn conversation into outline
  walk [paper_id] – Random citation graph walk
  bibtex export|clear – Manage bibliography
  
  === System ===
  benchmark – Run performance tests
  topology – Show graph stats
  exit – Quit
"""
            )
        elif op == "exit":
            self.app.exit()
        elif op == "ingest" and arg:
            # Ingest via Hydra (async)
            hydra = IngestionHydra()
            await hydra.ingest_file(arg)
            self.print_output(f"✅ Ingested {arg}\n")
        elif op == "search" and arg:
            from research_os.search.retriever import get_retriever
            retriever = get_retriever()
            results = await retriever.search(arg, top_k=3)
            if not results:
                self.print_output("No results found.\n")
                return
            out = []
            for i, r in enumerate(results, 1):
                out.append(f"[{i}] (score: {r.score:.3f}) {r.chunk.source}")
                out.append(f"  {r.chunk.text[:150]}...\n")
            self.print_output("\n".join(out))
        elif op == "ask" and arg:
            # Retrieve context then generate answer with streaming
            from research_os.search.retriever import get_retriever
            retriever = get_retriever()
            results = await retriever.search(arg, top_k=3)
            context = "\n\n".join([r.chunk.text for r in results])
            
            # Show "thinking" indicator
            self.print_output("\n💡 Answer: ")
            
            # Get event loop for thread-safe updates
            loop = asyncio.get_event_loop()
            
            # Streaming callback - must use call_soon_threadsafe for TUI updates
            def on_token(token: str):
                def update_ui():
                    self.output_field.text += token
                    self.output_field.buffer.cursor_position = len(self.output_field.text)
                    self.app.invalidate()
                loop.call_soon_threadsafe(update_ui)
            
            await foundation.generate_stream_async(
                prompt=arg,
                context=context,
                system="You are ResearchOS, an expert research assistant. Answer concisely.",
                max_tokens=256,
                callback=on_token
            )
            self.print_output("\n")
            
            if results:
                srcs = "\n".join([f"  - {r.chunk.source}" for r in results])
                self.print_output(f"📚 Sources:\n{srcs}\n")
        elif op == "visualize" and arg:
            self.print_output(f"🚧 Visualization not implemented yet (topic: {arg}).\n")
        elif op == "benchmark":
            self.print_output("🚧 Benchmark not implemented yet.\n")
        elif op == "topology":
            self.print_output("🚧 Topology view not implemented yet.\n")
        
        # ============ NEW FEATURES ============
        elif op == "whisper":
            # Paper Whispers - show recent or set topics
            from research_os.features import PaperWhisper
            if not hasattr(self, '_whisper'):
                self._whisper = PaperWhisper(foundation)
            
            if arg.startswith("topics "):
                topics = arg.replace("topics ", "").split(",")
                self._whisper.set_topics([t.strip() for t in topics])
                self.print_output(f"🔮 Whisper topics set: {topics}\n")
            elif arg == "check":
                self.print_output("🔮 Checking for new papers...\n")
                whispers = await self._whisper.check_new_papers()
                if whispers:
                    for w in whispers:
                        self.print_output(f"📄 {w.paper.title}\n   💬 {w.hook}\n\n")
                else:
                    self.print_output("No new papers found.\n")
            else:
                recent = self._whisper.get_recent(3)
                if recent:
                    for w in recent:
                        self.print_output(f"🔮 {w.hook}\n   → {w.paper.title}\n\n")
                else:
                    self.print_output("No whispers yet. Try: whisper topics attention,transformers\n")
        
        elif op == "doubt":
            # Doubt Mode - toggle or challenge
            from research_os.features import DoubtEngine
            if not hasattr(self, '_doubt'):
                from research_os.search.retriever import get_retriever
                self._doubt = DoubtEngine(foundation, get_retriever())
            
            if arg == "on":
                self._doubt.enabled = True
                self.print_output("🤨 Doubt Mode: ON (I will challenge your claims)\n")
            elif arg == "off":
                self._doubt.enabled = False
                self.print_output("🤨 Doubt Mode: OFF\n")
            elif arg:
                challenge = await self._doubt.challenge(arg)
                self.print_output(f"\n⚠️ Challenge: {challenge.objection}\n")
                self.print_output(f"📄 Source: {challenge.source or 'General reasoning'}\n")
                self.print_output(f"❓ Question: {challenge.question}\n\n")
            else:
                status = "ON" if self._doubt.enabled else "OFF"
                self.print_output(f"🤨 Doubt Mode: {status}\nUsage: doubt on|off|<claim to challenge>\n")
        
        elif op == "crystallize":
            # Crystallize conversation
            from research_os.features import Crystallizer
            crystallizer = Crystallizer(foundation)
            # Fake conversation from output (simplified)
            self.print_output("\n💎 Crystallizing conversation...\n")
            result = await crystallizer.crystallize([
                {"role": "user", "content": arg or "Summarize my research session"}
            ])
            self.print_output(result.raw_markdown + "\n")
        
        elif op == "walk":
            # Serendipity Walk
            from research_os.features import SerendipityEngine
            engine = SerendipityEngine(foundation)
            self.print_output("🎲 Starting serendipity walk...\n")
            if arg:
                # Use arg as paper ID or search term
                walk = await engine.walk_from_paper(arg, steps=3)
                self.print_output(walk.to_narrative())
            else:
                # Daily random
                step = await engine.daily_random(["machine learning", "transformers"])
                if step:
                    self.print_output(f"🎲 Random discovery: {step.title}\n   {step.connection_story}\n")
                else:
                    self.print_output("No random paper found. Try: walk <paper_id>\n")
        
        elif op == "bibtex":
            # Export bibliography
            from research_os.features import Bibliography
            if not hasattr(self, '_bib'):
                self._bib = Bibliography()
            
            if arg == "export":
                bib = self._bib.export_bibtex()
                self.print_output(f"📚 BibTeX:\n{bib}\n")
            elif arg == "clear":
                self._bib.clear()
                self.print_output("📚 Bibliography cleared.\n")
            else:
                self.print_output(f"📚 {len(self._bib.citations)} citations tracked.\nUsage: bibtex export|clear\n")
        
        elif op == "voice":
            # Voice Loop
            from research_os.features import VoiceLoop
            if not hasattr(self, '_voice'):
                self._voice = VoiceLoop(foundation)
            
            if arg == "record":
                self.print_output("🎙️ Recording... (Press ENTER to stop)\n")
                self._voice.start_recording()
                # We expect the user to hit Enter which sends an empty command or next command
                # Ideally, we should have a way to toggle.
                # For UI, maybe just "voice stop" is better explicit command.
                self.print_output("   Type 'voice stop' to finish.\n")
            elif arg == "stop":
                self.print_output("🛑 Processing audio...\n")
                note = await self._voice.stop_processing()
                if note:
                    self.print_output(f"\n{note.structured_content}\n")
                    self.print_output(f"   (Saved to {os.path.basename(note.audio_path)})\n\n")
                else:
                    self.print_output("No recording found.\n")
            else:
                self.print_output("🎙️ Voice usage: voice record | voice stop\n")

        elif op == "web":
            # Launch Web UI
            if arg == "start":
                import threading
                from research_os.web import start_server
                
                # Run in daemon thread
                t = threading.Thread(target=start_server, args=(8000,), daemon=True)
                t.start()
                self.print_output("🚀 Web Canvas running at http://localhost:8000\n")
            else:
                self.print_output("Usage: web start\n")

        else:
            self.print_output(f"❓ Unknown command: {command}\n")

    def print_output(self, text: str) -> None:
        """Append text to the output area, trimming if it becomes huge."""
        # Append and keep a reasonable size (max ~5000 chars)
        new_text = self.output_field.text + text
        if len(new_text) > 5000:
            new_text = new_text[-5000:]
        self.output_field.text = new_text
        # Ensure the view scrolls to the bottom
        self.output_field.buffer.cursor_position = len(self.output_field.text)

# ---------------------------------------------------------------------------
# Loguru integration – forward logs to the TUI sidebar
# ---------------------------------------------------------------------------
def tui_log_sink(message):
    # message is a LogRecord; extract the formatted string
    try:
        txt = message.record["message"].strip()
        # Avoid flooding – keep short snippets
        if len(txt) > 120:
            txt = txt[:117] + "..."
        # Append to TUI if it exists
        if hasattr(tui_log_sink, "tui"):
            tui_log_sink.tui.add_log(txt)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main() -> None:
    # Initialize TUI first (so we have a place for logs)
    tui = ResearchTUI()
    # Attach TUI instance to log sink for later use
    tui_log_sink.tui = tui

    # Configure logger – file + UI sink
    logger.remove()  # remove default stderr handler
    logger.add("research_os.log", rotation="10 MB")
    logger.add(tui_log_sink, format="{message}", level="INFO")

    # Start background file watcher (runs in its own thread)
    watcher = FileWatcher(watch_path=Path.home() / "Downloads")
    watcher.start()

    # Run the TUI application (async)
    loop = asyncio.get_event_loop()
    # Refresh sidebar (time, etc.) every second
    async def refresh_sidebar():
        while True:
            tui.sidebar.text = tui._build_sidebar()
            await asyncio.sleep(1)

    loop.create_task(refresh_sidebar())
    loop.run_until_complete(tui.app.run_async())

if __name__ == "__main__":
    main()
