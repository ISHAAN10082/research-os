"""
ResearchOS Spatial Telemetry: The "Consciousness" of the System.
Handles high-speed event logging using SQLite in WAL mode for maximum write concurrency.
"""
import sqlite3
import json
import logging
import asyncio
from typing import Dict, Optional, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

from research_os.config import settings

logger = logging.getLogger(__name__)

# --- Events / Data Classes ---

@dataclass
class TelemetryEvent:
    workspace: str  # 'synthesis', 'reading', 'graph'
    event_type: str # 'spawn', 'scroll', 'click'
    data: Dict[str, Any]
    timestamp: float

# --- Database Manager ---

class SpatialTelemetry:
    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Default to settings or hidden folder
            brain_dir = Path(settings.KUZU_DB_PATH).parent
            self.db_path = brain_dir / "spatial_telemetry.db"
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite with WAL mode for performance."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable Write-Ahead Logging for concurrency
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;") # Faster writes, slight risk on power loss
                
                # Create main event table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        workspace TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        data JSON NOT NULL
                    );
                """)
                
                # Indexes for fast analytics
                conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_workspace ON events(workspace);")
                
                logger.info(f"Spatial Telemetry initialized at {self.db_path} (WAL Mode)")
        except Exception as e:
            logger.error(f"Failed to initialize telemetry DB: {e}")

    def capture(self, workspace: str, event_type: str, data: Dict[str, Any]):
        """
        Log an event. Designed to be fast and non-blocking.
        Note: In a high-load async server, we might want to offload strict DB writes 
        to a separate thread/queue, but SQLite WAL is incredibly fast for single-writer.
        """
        try:
            timestamp = datetime.now().timestamp()
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO events (timestamp, workspace, event_type, data) VALUES (?, ?, ?, ?)",
                    (timestamp, workspace, event_type, json.dumps(data))
                )
        except Exception as e:
            logger.error(f"Telemetry capture error: {e}")

    async def capture_async(self, workspace: str, event_type: str, data: Dict[str, Any]):
        """Async wrapper for use in FastAPI routes."""
        capture_func = lambda: self.capture(workspace, event_type, data)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, capture_func)

    def get_recent_events(self, limit: int = 100):
        """Fetch recent logs for debugging/dashboard."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", 
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

# Global Instance
telemetry = SpatialTelemetry()
