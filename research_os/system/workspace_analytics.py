"""
ResearchOS Workspace Analytics.
Uses DuckDB to run heavy analytical queries on the SQLite telemetry log without blocking writers.
"""
import duckdb
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from research_os.system.spatial_telemetry import telemetry

class WorkspaceAnalytics:
    def __init__(self):
        # We attach to the SQLite DB in read-only mode via DuckDB
        self.db_path = str(telemetry.db_path)

    def _query(self, sql: str) -> pd.DataFrame:
        """Execute analytic query using DuckDB's SQLite extension."""
        try:
            # Connect to in-memory DuckDB
            con = duckdb.connect(database=':memory:')
            
            # Install/Load sqlite extension if needed (usually built-in for many duckdb distributions)
            con.execute("INSTALL sqlite; LOAD sqlite;")
            
            # Attach the actual DB
            con.execute(f"CALL sqlite_attach('{self.db_path}');")
            
            # Run query
            df = con.execute(sql).fetchdf()
            return df
        except Exception as e:
            print(f"Analytics Error: {e}")
            return pd.DataFrame()

    def get_crystallization_rate(self) -> float:
        """
        Calculate the ratio of 'crystallized' threads to total threads.
        """
        # Note: We need to parse the JSON field in DuckDB.
        # Data structure assumption: data.action == 'crystallize'
        sql = """
            SELECT 
                data->>'$.action' as action
            FROM events 
            WHERE workspace = 'synthesis'
        """
        df = self._query(sql)
        if df.empty: 
            return 0.0
            
        total = len(df)
        crystallized = len(df[df['action'] == 'crystallize'])
        
        return crystallized / total if total > 0 else 0.0

    def get_reading_velocity(self) -> Dict[str, float]:
        """
        Calculate avg time spent per page.
        """
        # Complex implementation simplified for MVP:
        # Just count 'scroll' events for now.
        sql = """
            SELECT count(*) as count FROM events 
            WHERE workspace = 'reading' AND event_type = 'scroll'
        """
        df = self._query(sql)
        return {"total_scrolls": float(df['count'][0]) if not df.empty else 0.0}

analytics = WorkspaceAnalytics()
