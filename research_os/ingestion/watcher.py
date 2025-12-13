import time
import os
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger
from pathlib import Path

# Defer imports to avoid circular deps during startup
# from research_os.ingestion.hydra import hydra
# from research_os.system.anticipator import anticipator_engine

class ResearchHandler(FileSystemEventHandler):
    """Handles file system events for PDFs."""
    
    def __init__(self, loop):
        self.loop = loop
        
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(".pdf"):
            logger.info(f"👀 Detected new PDF: {event.src_path}")
            # Schedule async ingestion safely
            asyncio.run_coroutine_threadsafe(
                self.process_new_file(event.src_path), 
                self.loop
            )

    async def process_new_file(self, path):
        """Pipeline: Ingest -> Embed -> Anticipate"""
        from research_os.ingestion.hydra import hydra
        from research_os.system.anticipator import anticipator_engine
        
        try:
            # 1. Ingest
            logger.info(f"⚡ Auto-ingesting: {Path(path).name}")
            # Note: We assume ingest_file returns the text or concept. 
            # If not, we might need to fetch it from DB.
            # For now, let's assume it runs successfully.
            await hydra.ingest_file(path)
            
            # 2. Trigger Anticipation (using mock context for now if not returned)
            # In a real impl, ingest_file should return the Extracted Content.
            # We'll pass a placeholder or read the file.
            
            # Simple read of first 2k chars for context window
            # (In reality, MinerU gives better text, but we want speed here)
            # Or we can query the DB. 
            # Let's just trigger it with the filename for now.
            logger.info("🧠 Triggering anticipator...")
            await anticipator_engine.prefetch_for_paper(Path(path).name, "Context loading...")

            # Notify UI (TODO: Hook into global state or event bus)
            # logger.info("✅ Ready!") 
            
        except Exception as e:
            logger.error(f"Auto-ingest failed: {e}")

class FileWatcher:
    """Manages the watchdog observer."""
    
    def __init__(self, watch_path):
        """
        Initialize the FileWatcher.

        Args:
            watch_path (str | Path): Directory to monitor for new PDFs.
        """
        # Accept both Path objects and plain strings
        self.watch_dir = str(watch_path) if not isinstance(watch_path, str) else watch_path
        self.observer = Observer()
        
    def start(self):
        """Start watching in background thread."""
        if not os.path.exists(self.watch_dir):
            logger.warning(f"Watch directory {self.watch_dir} does not exist.")
            return

        loop = asyncio.get_event_loop()
        handler = ResearchHandler(loop)
        self.observer.schedule(handler, self.watch_dir, recursive=False)
        self.observer.start()
        logger.info(f"👁️  Watcher active on: {self.watch_dir}")
        
    def stop(self):
        self.observer.stop()
        self.observer.join()
