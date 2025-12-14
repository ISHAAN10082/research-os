from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import kuzu
import networkx as nx
import networkx as nx
import json
from datetime import datetime
import os

class GraphBackend(ABC):
    """
    Abstract interface for graph database operations.
    Enables swapping KuzuDB → FalkorDB without code changes.
    """
    
    @abstractmethod
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute Cypher-like query"""
        pass
    
    @abstractmethod
    def add_node(self, label: str, properties: Dict) -> str:
        """Returns node ID"""
        pass
    
    @abstractmethod
    def add_edge(self, from_id: str, to_id: str, rel_type: str, properties: Dict = None) -> str:
        """Returns edge ID"""
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[Dict]:
        pass
    
    @abstractmethod
    def get_neighbors(self, node_id: str, rel_type: str = None) -> List[Dict]:
        pass
    
    @abstractmethod
    def close(self):
        """Clean up resources"""
        pass


class KuzuBackend(GraphBackend):
    """KuzuDB implementation (current)"""
    
    def __init__(self, db_path: str = "data/research.kuzu"):
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self.log_path = "data/graph_events.jsonl"
        self._initialize_schema()
    
    def _log_event(self, event_type: str, payload: Dict):
        """Append-only event log"""
        event = {
            "timestamp": str(datetime.now().isoformat()),
            "type": event_type,
            "payload": payload
        }
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(event) + "\n")
    
    def _initialize_schema(self):
        """Create node and edge tables if they don't exist"""
        schema_ddl = [
            # Nodes
            """CREATE NODE TABLE IF NOT EXISTS Claim(
                claim_id STRING PRIMARY KEY,
                text STRING,
                claim_type STRING,
                section STRING,
                confidence DOUBLE,
                paper_id STRING,
                specter2_embedding DOUBLE[]
            )""",
            
            """CREATE NODE TABLE IF NOT EXISTS Source(
                source_id STRING PRIMARY KEY,
                source_type STRING,
                url STRING,
                title STRING,
                trust_score DOUBLE,
                metadata STRING
            )""",
            
            # Relationships
            """CREATE REL TABLE IF NOT EXISTS RELATES(
                FROM Claim TO Claim,
                relation_type STRING,
                confidence DOUBLE,
                citations STRING,
                debate_log STRING
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS EXTRACTED_FROM(
                FROM Claim TO Source
            )"""
        ]
        
        for ddl in schema_ddl:
            try:
                self.conn.execute(ddl)
            except Exception as e:
                # Table may already exist
                pass
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        try:
            result = self.conn.execute(query, params or {})
            return [dict(row) for row in result.get_as_df().to_dict('records')]
        except Exception as e:
            print(f"Query error: {e}")
            return []
    
    def add_node(self, label: str, properties: Dict) -> str:
        # Extract ID from properties
        id_field = f"{label.lower()}_id"
        node_id = properties.get(id_field)
        
        if not node_id:
            raise ValueError(f"Missing {id_field} in properties")
        
        # Build CREATE query
        fields = ", ".join(properties.keys())
        placeholders = ", ".join([f"${k}" for k in properties.keys()])
        
        query = f"""CREATE (:{label} {{{fields}}})"""
        self.conn.execute(query, properties)
        
        # Log Event
        self._log_event("add_node", {"label": label, "properties": properties})
        
        return node_id
    
    def add_edge(self, from_id: str, to_id: str, rel_type: str, properties: Dict = None) -> str:
        properties = properties or {}
        
        # Determine node labels (assume Claim for now, improve later)
        query = f"""
        MATCH (a:Claim {{claim_id: $from_id}}), (b:Claim {{claim_id: $to_id}})
        CREATE (a)-[r:{rel_type}]->(b)
        SET r = $props
        RETURN id(r) AS edge_id
        """
        
        result = self.conn.execute(query, {"from_id": from_id, "to_id": to_id, "props": properties})
        rows = result.get_as_df()
        
        # Log Event
        self._log_event("add_edge", {"from_id": from_id, "to_id": to_id, "rel_type": rel_type, "properties": properties})
        
        return str(rows.iloc[0]['edge_id']) if len(rows) > 0 else ""
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        query = "MATCH (n) WHERE n.claim_id = $node_id OR n.source_id = $node_id RETURN n"
        results = self.execute_query(query, {"node_id": node_id})
        return results[0] if results else None
    
    def get_neighbors(self, node_id: str, rel_type: str = None) -> List[Dict]:
        if rel_type:
            query = f"MATCH (n)-[:{rel_type}]-(m) WHERE n.claim_id = $node_id RETURN m"
        else:
            query = "MATCH (n)--(m) WHERE n.claim_id = $node_id RETURN m"
        
        return self.execute_query(query, {"node_id": node_id})
    
    def close(self):
        # KuzuDB doesn't require explicit close
        pass


class InMemoryBackend(GraphBackend):
    """In-memory implementation for testing"""
    
    def __init__(self):
        self.nodes = {}  # {node_id: properties}
        self.edges = []  # List of (from_id, to_id, rel_type, properties)
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        # Simplified query execution (not full Cypher)
        return []
    
    def add_node(self, label: str, properties: Dict) -> str:
        id_field = f"{label.lower()}_id"
        node_id = properties.get(id_field)
        
        if not node_id:
            raise ValueError(f"Missing {id_field}")
        
        self.nodes[node_id] = {"label": label, **properties}
        return node_id
    
    def add_edge(self, from_id: str, to_id: str, rel_type: str, properties: Dict = None) -> str:
        edge_id = f"{from_id}-{rel_type}-{to_id}"
        self.edges.append({
            "edge_id": edge_id,
            "from": from_id,
            "to": to_id,
            "type": rel_type,
            "properties": properties or {}
        })
        return edge_id
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        return self.nodes.get(node_id)
    
    def get_neighbors(self, node_id: str, rel_type: str = None) -> List[Dict]:
        neighbors = []
        for edge in self.edges:
            if edge['from'] == node_id:
                if not rel_type or edge['type'] == rel_type:
                    neighbor = self.nodes.get(edge['to'])
                    if neighbor:
                        neighbors.append(neighbor)
        return neighbors
    
    def close(self):
        self.nodes.clear()
        self.edges.clear()


class FalkorBackend(GraphBackend):
    """FalkorDB implementation (future migration target)"""
    
    def __init__(self, connection_string: str = "falkordb://localhost:6379"):
        # Placeholder for FalkorDB connection
        # from falkordb import FalkorDB
        # self.client = FalkorDB(connection_string)
        raise NotImplementedError("FalkorDB backend not yet implemented")
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        raise NotImplementedError()
    
    def add_node(self, label: str, properties: Dict) -> str:
        raise NotImplementedError()
    
    def add_edge(self, from_id: str, to_id: str, rel_type: str, properties: Dict = None) -> str:
        raise NotImplementedError()
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        raise NotImplementedError()
    
    def get_neighbors(self, node_id: str, rel_type: str = None) -> List[Dict]:
        raise NotImplementedError()
    
    def close(self):
        raise NotImplementedError()


def create_backend(backend_type: str = "kuzu", **kwargs) -> GraphBackend:
    """Factory function to create graph backend"""
    backends = {
        "kuzu": KuzuBackend,
        "inmemory": InMemoryBackend,
        "falkor": FalkorBackend
    }
    
    if backend_type not in backends:
        raise ValueError(f"Unknown backend: {backend_type}")
    
    return backends[backend_type](**kwargs)


if __name__ == "__main__":
    # Test backend abstraction
    print("Testing InMemoryBackend...")
    backend = create_backend("inmemory")
    
    # Add nodes
    backend.add_node("Claim", {
        "claim_id": "claim_001",
        "text": "Test claim",
        "claim_type": "finding",
        "confidence": 0.9
    })
    
    backend.add_node("Claim", {
        "claim_id": "claim_002",
        "text": "Another claim",
        "claim_type": "method",
        "confidence": 0.8
    })
    
    # Add edge
    backend.add_edge("claim_001", "claim_002", "RELATES", {"relation_type": "supports"})
    
    # Query
    node = backend.get_node("claim_001")
    print(f"✅ Retrieved node: {node}")
    
    neighbors = backend.get_neighbors("claim_001")
    print(f"✅ Found {len(neighbors)} neighbors")
    
    backend.close()
    print("✅ Backend abstraction test passed")
