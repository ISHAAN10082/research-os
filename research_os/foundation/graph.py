import kuzu
from pathlib import Path
from research_os.config import settings
from loguru import logger

class GraphEngine:
    """
    KùzuDB wrapper for embedded graph operations.
    Optimized for zero-copy and embedded usage on M4.
    """
    def __init__(self):
        self.db_path = settings.KUZU_DB_PATH
        self.db = None
        self.conn = None
        self._initialize_db()

    def _initialize_db(self):
        """Initialize KuzuDB instance and connection."""
        try:
            settings.ensure_dirs()
            self.db = kuzu.Database(str(self.db_path))
            self.conn = kuzu.Connection(self.db)
            logger.info(f"GraphEngine connected to {self.db_path}")
            self._ensure_schema()
        except Exception as e:
            logger.error(f"Failed to initialize GraphEngine: {e}")
            raise

    def _ensure_schema(self):
        """Define the core ResearchOS schema if not exists."""
        # Check if tables exist
        # Note: robust checks usually involve querying catalogue, here we try/except creation
        
        # 1. Concept Nodes
        try:
            self.conn.execute(
                "CREATE NODE TABLE Concept(name STRING, embedding FULL_FLOAT_LIST, PRIMARY KEY (name))"
            )
            logger.info("Created table: Concept")
        except RuntimeError:
            pass # Already exists

        # 2. Paper Nodes
        try:
            self.conn.execute(
                "CREATE NODE TABLE Paper(title STRING, path STRING, abstract STRING, PRIMARY KEY (title))"
            )
            logger.info("Created table: Paper")
        except RuntimeError:
            pass

        # 3. Relationships (Edges)
        try:
            self.conn.execute(
                "CREATE REL TABLE RELATED_TO(FROM Concept TO Concept, strength FLOAT)"
            )
            logger.info("Created edge: RELATED_TO")
        except RuntimeError:
            pass

        try:
            self.conn.execute(
                "CREATE REL TABLE MENTIONS(FROM Paper TO Concept, confidence FLOAT)"
            )
            logger.info("Created edge: MENTIONS")
        except RuntimeError:
            pass

        try:
            self.conn.execute(
                "CREATE REL TABLE CITES(FROM Paper TO Paper)"
            )
            logger.info("Created edge: CITES")
        except RuntimeError:
            pass

    def execute(self, query: str, parameters: dict = None):
        """Run Cypher query."""
        return self.conn.execute(query, parameters)

    def add_concept(self, name: str, embedding: list[float]):
        """Add a concept with its vector embedding."""
        try:
            query = "MERGE (c:Concept {name: $name}) ON CREATE SET c.embedding = $embedding"
            self.conn.execute(query, {"name": name, "embedding": embedding})
        except Exception as e:
            logger.error(f"Error adding concept {name}: {e}")

    def add_paper(self, title: str, path: str, abstract: str = ""):
        """Add a paper to the graph."""
        try:
            query = "MERGE (p:Paper {title: $title}) ON CREATE SET p.path = $path, p.abstract = $abstract"
            self.conn.execute(query, {"title": title, "path": path, "abstract": abstract})
            return True
        except Exception as e:
            logger.error(f"Error adding paper {title}: {e}")
            return False

    def add_citation(self, from_title: str, to_title: str):
        """Add a citation edge between existing papers."""
        try:
            # Check if both exist first? MERGE should handle node creation if needed, 
            # but usually we only cite known nodes. For now, strict match.
            query = """
                MATCH (a:Paper {title: $from}), (b:Paper {title: $to})
                MERGE (a)-[:CITES]->(b)
            """
            self.conn.execute(query, {"from": from_title, "to": to_title})
        except Exception as e:
            logger.error(f"Error citing {from_title} -> {to_title}: {e}")

    def get_all_papers(self):
        """Get list of all ingested papers using Cypher."""
        try:
            result = self.conn.execute("MATCH (p:Paper) RETURN p.title, p.path")
            papers = []
            while result.has_next():
                row = result.get_next()
                papers.append({"title": row[0], "path": row[1]})
            return papers
        except Exception as e:
            logger.error(f"Graph query error: {e}")
            return []

    def get_citation_graph(self):
        """Get nodes and links for 3D visualization."""
        try:
            nodes = []
            links = []
            
            # Nodes
            res_nodes = self.conn.execute("MATCH (p:Paper) RETURN p.title, p.path")
            while res_nodes.has_next():
                row = res_nodes.get_next()
                nodes.append({"id": row[0], "group": 1, "path": row[1]})
                
            # Links
            res_links = self.conn.execute("MATCH (a:Paper)-[r:CITES]->(b:Paper) RETURN a.title, b.title")
            while res_links.has_next():
                row = res_links.get_next()
                links.append({"source": row[0], "target": row[1]})
                
            return {"nodes": nodes, "links": links}
        except Exception as e:
            logger.error(f"Graph query error: {e}")
            return {"nodes": [], "links": []}

# Global Instance
graph_engine = GraphEngine()
