import kuzu
import json
import time
from datetime import datetime
import os

class UnifiedSchema:
    """
    Single source of truth for all data structures in ResearchOS 3.0.
    Every feature (Debate, Palace, HypothesisGen) reads/writes through this layer.
    """
    
    def __init__(self, db_path: str = "data/research.kuzu"):
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._initialize()
    
    def _initialize(self):
        """Create schema if not exists"""
        
        # NODE: Paper (Source)
        try:
            self.conn.execute("""
                CREATE NODE TABLE Paper(
                    paper_id STRING,
                    title STRING,
                    authors STRING,
                    year INT64,
                    doi STRING,
                    raw_text STRING,
                    embedding FLOAT[],
                    importance_score FLOAT,
                    processed_timestamp TIMESTAMP,
                    user_read BOOLEAN DEFAULT false,
                    user_dwell_time_ms INT64 DEFAULT 0,
                    PRIMARY KEY (paper_id)
                )
            """)
            print("Created table: Paper")
        except RuntimeError: pass # Exists
        
        # NODE: Claim (Extracted Facts)
        try:
            self.conn.execute("""
                CREATE NODE TABLE Claim(
                    claim_id STRING,
                    text STRING,
                    claim_type STRING, 
                    paper_id STRING,
                    section STRING,
                    evidence_count INT64,
                    confidence FLOAT,
                    embedding FLOAT[],
                    created_timestamp TIMESTAMP,
                    debate_history STRING,
                    hypothesis_score FLOAT,
                    contradictions INT64 DEFAULT 0,
                    PRIMARY KEY (claim_id)
                )
            """)
            print("Created table: Claim")
        except RuntimeError: pass
        
        # RELATIONSHIP: Papers cite each other
        try:
            self.conn.execute("""
                CREATE REL TABLE CITES(
                    FROM Paper TO Paper,
                    citation_count INT64
                )
            """)
            print("Created rel: CITES")
        except RuntimeError: pass
        
        # RELATIONSHIP: Claims extracted from papers
        try:
            self.conn.execute("""
                CREATE REL TABLE EXTRACTED_FROM(
                    FROM Claim TO Paper
                )
            """)
            print("Created rel: EXTRACTED_FROM")
        except RuntimeError: pass
        
        # RELATIONSHIP: Claims relate to each other (Debate Output)
        try:
            self.conn.execute("""
                CREATE REL TABLE RELATES(
                    FROM Claim TO Claim,
                    relation_type STRING,
                    strength FLOAT,
                    debate_rounds INT64,
                    is_controversial BOOLEAN
                )
            """)
            print("Created rel: RELATES")
        except RuntimeError: pass
        
        # NODE: UserInteraction (Telemetry)
        try:
            self.conn.execute("""
                CREATE NODE TABLE UserInteraction(
                    interaction_id STRING,
                    user_id STRING,
                    paper_id STRING,
                    interaction_type STRING,
                    timestamp TIMESTAMP,
                    duration_ms INT64,
                    user_feedback STRING,
                    PRIMARY KEY (interaction_id)
                )
            """)
            print("Created table: UserInteraction")
        except RuntimeError: pass
        
        # NODE: PalaceWing (Spatial)
        try:
            self.conn.execute("""
                CREATE NODE TABLE PalaceWing(
                    wing_id STRING,
                    wing_name STRING,
                    topic STRING,
                    spatial_center FLOAT[],
                    papers_in_wing INT64,
                    PRIMARY KEY (wing_id)
                )
            """)
            print("Created table: PalaceWing")
        except RuntimeError: pass
        
        # RELATIONSHIP: Papers located in palace
        try:
            self.conn.execute("""
                CREATE REL TABLE LOCATED_IN(
                    FROM Paper TO PalaceWing,
                    position_xyz FLOAT[],
                    importance_weight FLOAT
                )
            """)
            print("Created rel: LOCATED_IN")
        except RuntimeError: pass

        # NODE: ChatSession (Persistence)
        try:
            self.conn.execute("""
                CREATE NODE TABLE ChatSession(
                    session_id STRING,
                    name STRING,
                    created_at TIMESTAMP,
                    last_updated TIMESTAMP,
                    user_id STRING,
                    PRIMARY KEY (session_id)
                )
            """)
            print("Created table: ChatSession")
        except RuntimeError: pass

        # NODE: ChatMessage (Persistence)
        try:
            self.conn.execute("""
                CREATE NODE TABLE ChatMessage(
                    msg_id STRING,
                    session_id STRING,
                    role STRING,
                    content STRING,
                    timestamp TIMESTAMP,
                    context_paper_id STRING,
                    tokens INT64,
                    PRIMARY KEY (msg_id)
                )
            """)
            print("Created table: ChatMessage")
        except RuntimeError: pass
        
        # RELATIONSHIP: Message belongs to Session
        try:
            self.conn.execute("""
                CREATE REL TABLE BELONGS_TO(
                    FROM ChatMessage TO ChatSession
                )
            """)
            print("Created rel: BELONGS_TO")
        except RuntimeError: pass
        
        print("✅ Unified Schema Initialized.")
    
    def get_all_claims(self) -> list:
        """Central query used by debate, hypothesis gen, causal graph"""
        result = self.conn.execute("""
            MATCH (c:Claim) 
            RETURN c.claim_id, c.text, c.embedding, c.confidence
        """)
        # Convert Kuzu result to list of dicts
        columns = result.get_column_names()
        rows = []
        while result.has_next():
            rows.append(dict(zip(columns, result.get_next())))
        return rows
    
    def get_relationships(self, claim_id: str) -> list:
        """Central query for graph operations"""
        result = self.conn.execute("""
            MATCH (c1:Claim)-[r:RELATES]-(c2:Claim)
            WHERE c1.claim_id = $claim_id
            RETURN r.relation_type, c2.text, r.strength
        """, {"claim_id": claim_id})
        columns = result.get_column_names()
        rows = []
        while result.has_next():
            rows.append(dict(zip(columns, result.get_next())))
        return rows

    
    def ingest_paper(self, paper_data: dict):
        """Insert or update a paper in the graph"""
        try:
            # Check if exists
            result = self.conn.execute("MATCH (p:Paper {paper_id: $id}) RETURN p.paper_id", {"id": paper_data["paper_id"]})
            if result.has_next():
                return # Already exists
                
            self.conn.execute("""
                CREATE (p:Paper {
                    paper_id: $id,
                    title: $title,
                    authors: $authors,
                    year: $year,
                    doi: $doi,
                    raw_text: $raw_text,
                    embedding: $embedding,
                    importance_score: $score,
                    processed_timestamp: timestamp($ts),
                    user_read: false
                })
            """, {
                "id": paper_data["paper_id"],
                "title": paper_data.get("title", "Unknown"),
                "authors": paper_data.get("authors", "Unknown"),
                "year": paper_data.get("year", 2024),
                "doi": paper_data.get("doi", ""),
                "raw_text": paper_data.get("raw_text", ""),
                "embedding": paper_data.get("embedding", [0.0]*768),
                "score": paper_data.get("importance_score", 0.5),
                "ts": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Schema Ingest Error: {e}")

    def get_all_papers(self) -> list:
        """Fetch all papers from the graph"""
        try:
            result = self.conn.execute("""
                MATCH (p:Paper)
                RETURN p.paper_id, p.title, p.authors, p.year, p.processed_timestamp, p.raw_text
                ORDER BY p.processed_timestamp DESC
            """)
            columns = result.get_column_names()
            rows = []
            while result.has_next():
                row = dict(zip(columns, result.get_next()))
                # Inject inferred path
                # Handle potential column naming differences in Kuzu return
                p_id = row.get('paper_id') or row.get('p.paper_id')
                if not p_id:
                     # Skip invalid rows or debug
                     continue
                     
                path = f"data/papers/{p_id}.pdf"
                if os.path.exists(path):
                    row['path'] = os.path.abspath(path)
                
                # Normalize column names for frontend
                row['paper_id'] = p_id
                row['raw_text'] = row.get('raw_text') or row.get('p.raw_text') or ""
                row['title'] = row.get('title') or row.get('p.title') or "Untitled"
                row['authors'] = row.get('authors') or row.get('p.authors') or ""
                
                rows.append(row)
            return rows
        except Exception as e:
            print(f"Error fetching papers: {e}")
            return []

    def update_paper_text(self, paper_id: str, text: str):
        """Update the raw_text of a paper"""
        try:
            # Escape text for Cypher (simplistic)
            # Actually Kuzu params are safer.
            self.conn.execute(
                "MATCH (p:Paper {paper_id: $id}) SET p.raw_text = $text",
                {"id": paper_id, "text": text}
            )
            print(f"✅ Updated text for paper {paper_id} ({len(text)} chars)")
        except Exception as e:
            print(f"❌ Failed to update paper text: {e}")

    def save_chat_message(self, session_id: str, role: str, content: str, paper_id: str = None):
        """Persist a chat message"""
        try:
            ts = datetime.now().isoformat()
            # Ensure session exists (simple check)
            self.conn.execute("""
                MERGE (s:ChatSession {session_id: $sid})
                ON CREATE SET s.created_at = timestamp($ts), s.name = "New Chat"
                ON MATCH SET s.last_updated = timestamp($ts)
            """, {"sid": session_id, "ts": ts})
            
            msg_id = f"msg_{int(time.time()*1000)}"
            
            # Create message and link
            self.conn.execute("""
                CREATE (m:ChatMessage {
                    msg_id: $mid,
                    session_id: $sid,
                    role: $role,
                    content: $content,
                    timestamp: timestamp($ts),
                    context_paper_id: $pid
                })
                WITH m
                MATCH (s:ChatSession {session_id: $sid})
                CREATE (m)-[:BELONGS_TO]->(s)
            """, {
                "mid": msg_id,
                "sid": session_id,
                "role": role,
                "content": content,
                "ts": ts,
                "pid": paper_id or ""
            })
        except Exception as e:
            print(f"Chat Persistence Error: {e}")

    def get_chat_history(self, session_id: str) -> list:
        """Retrieve chat history for a session"""
        try:
            result = self.conn.execute("""
                MATCH (m:ChatMessage)-[:BELONGS_TO]->(s:ChatSession {session_id: $sid})
                RETURN m.role, m.content, m.timestamp
                ORDER BY m.timestamp ASC
            """, {"sid": session_id})
            
            columns = result.get_column_names()
            rows = []
            while result.has_next():
                row = dict(zip(columns, result.get_next()))
                rows.append(row)
            return rows
        except Exception as e:
            return []

    def add_claim(self, claim_data: dict):
        """Insert a extracted claim into the graph"""
        self.conn.execute("""
            CREATE (c:Claim {
                claim_id: $claim_id,
                text: $text,
                claim_type: $claim_type,
                paper_id: $paper_id,
                section: $section,
                confidence: $confidence,
                embedding: $embedding,
                created_timestamp: timestamp($ts),
                debate_history: $debate_history
            })
        """, {
            "claim_id": claim_data["claim_id"],
            "text": claim_data["text"],
            "claim_type": claim_data["claim_type"],
            "paper_id": claim_data["paper_id"],
            "section": claim_data["section"],
            "confidence": claim_data["confidence"],
            "embedding": claim_data.get("embedding", [0.0]*768), # Default zero vector
            "ts": datetime.now().isoformat(),
            "debate_history": "[]"
        })

if __name__ == "__main__":
    # Test the schema
    schema = UnifiedSchema()
