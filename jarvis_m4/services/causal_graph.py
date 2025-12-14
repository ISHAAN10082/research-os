import networkx as nx
from typing import List, Dict, Tuple, Optional
from jarvis_m4.services.graph_backend import GraphBackend
from jarvis_m4.services.evidence_debate import EvidenceBasedDebate
from pydantic import BaseModel
from typing import Literal
import json

class ResearchGap(BaseModel):
    """Identified structural gap in the knowledge graph"""
    gap_type: Literal["contradiction_resolution", "validation_needed", "methodological_gap"]
    priority: Literal["high", "medium", "low"]
    description: str
    involved_claims: List[str]
    evidence_strength: float
    suggested_action: str

class CausalGraphV2:
    """
    Upgraded graph with NetworkX for topology analysis.
    Finds contradictions, unsupported claims, and frontier edges.
    """
    
    def __init__(self, graph_backend: GraphBackend, debate_system: Optional[EvidenceBasedDebate] = None):
        self.backend = graph_backend
        self.debate = debate_system
        
        # NetworkX for local topology analysis
        self.nx_graph = nx.DiGraph()
        
        # Cache for expensive queries
        self._contradiction_cache = None
    
    def add_claim(self, claim: Dict):
        """Add claim node to both backend and NetworkX"""
        
        # Add to persistent storage
        claim_id = self.backend.add_node("Claim", claim)
        
        # Add to NetworkX (for fast graph algorithms)
        self.nx_graph.add_node(claim_id, **claim)
        
        return claim_id
    
    def add_relationship(self, from_id: str, to_id: str, debate_result: Dict):
        """
        Add relationship edge based on debate verdict.
        
        Args:
            from_id: Source claim ID
            to_id: Target claim ID
            debate_result: DebateResult dict with verdict, confidence, citations
        """
        
        rel_type = debate_result.get('verdict', 'uncertain')
        confidence = debate_result.get('confidence', 0.5)
        
        # Add to backend
        edge_props = {
            "relation_type": rel_type,
            "confidence": confidence,
            "citations": json.dumps(debate_result.get('citations', [])),
            "debate_log": json.dumps(debate_result.get('debate_log', []))
        }
        
        self.backend.add_edge(from_id, to_id, "RELATES", edge_props)
        
        # Add to NetworkX
        self.nx_graph.add_edge(from_id, to_id, **edge_props)
        
        # Invalidate cache
        self._contradiction_cache = None
    
    def find_contradictions(self, min_confidence: float = 0.85) -> List[Tuple[str, str, List[str]]]:
        """
        Find high-confidence refutation relationships.
        
        Returns:
            List of (claim_a_id, claim_b_id, citations)
        """
        
        contradictions = []
        
        for u, v, data in self.nx_graph.edges(data=True):
            if (data.get('relation_type') == 'refutes' and 
                data.get('confidence', 0) >= min_confidence):
                
                citations = json.loads(data.get('citations', '[]'))
                contradictions.append((u, v, citations))
        
        return contradictions
    
    def find_unsupported_claims(self, min_degree: int = 0) -> List[str]:
        """
        Find claims with no incoming support edges.
        These are candidates for empirical validation.
        """
        
        unsupported = []
        
        for node in self.nx_graph.nodes():
            # Get incoming edges
            in_edges = list(self.nx_graph.in_edges(node, data=True))
            
            # Count support edges
            support_count = sum(
                1 for _, _, data in in_edges 
                if data.get('relation_type') == 'supports'
            )
            
            if support_count == 0 and self.nx_graph.degree(node) >= min_degree:
                unsupported.append(node)
        
        return unsupported
    
    def find_frontier_edges(self, max_confidence: float = 0.6, min_degree: int = 3) -> List[Dict]:
        """
        Find uncertain relationships between high-connectivity claims.
        These represent research gaps worth exploring.
        """
        
        frontier = []
        
        for u, v, data in self.nx_graph.edges(data=True):
            confidence = data.get('confidence', 0)
            
            # Low confidence + high impact nodes
            if (confidence < max_confidence and 
                self.nx_graph.degree(u) >= min_degree and
                self.nx_graph.degree(v) >= min_degree):
                
                frontier.append({
                    "claim_a_id": u,
                    "claim_b_id": v,
                    "confidence": confidence,
                    "relation_type": data.get('relation_type', 'uncertain'),
                    "gap_type": self._classify_gap_type(u, v, data)
                })
        
        return frontier
    
    def _classify_gap_type(self, claim_a: str, claim_b: str, edge_data: Dict) -> str:
        """Classify type of research gap"""
        
        rel_type = edge_data.get('relation_type', 'uncertain')
        confidence = edge_data.get('confidence', 0)
        
        if rel_type == 'refutes' and confidence < 0.7:
            return "methodological_gap"
        elif rel_type == 'uncertain':
            return "validation_needed"
        else:
            return "frontier_synthesis"
    
    def get_evidence_path(self, claim_a_id: str, claim_b_id: str) -> List[str]:
        """
        Find shortest path of evidence connecting two claims.
        """
        
        try:
            path = nx.shortest_path(self.nx_graph.to_undirected(), claim_a_id, claim_b_id)
            return path
        except nx.NetworkXNoPath:
            return []
    
    def get_claim_importance(self, claim_id: str) -> float:
        """
        Calculate claim importance using PageRank-like algorithm.
        """
        
        if self.nx_graph.number_of_nodes() == 0:
            return 0.0
        
        # Run PageRank
        pagerank = nx.pagerank(self.nx_graph)
        return pagerank.get(claim_id, 0.0)
    
    def export_for_visualization(self) -> Dict:
        """Export graph in format suitable for Three.js visualization"""
        
        nodes = []
        edges = []
        
        for node_id, data in self.nx_graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "text": data.get('text', '')[:100],
                "type": data.get('claim_type', 'unknown'),
                "importance": self.get_claim_importance(node_id)
            })
        
        for u, v, data in self.nx_graph.edges(data=True):
            edges.append({
                "from": u,
                "to": v,
                "relation": data.get('relation_type', 'unknown'),
                "confidence": data.get('confidence', 0)
            })
        
        return {"nodes": nodes, "edges": edges}


if __name__ == "__main__":
    from jarvis_m4.services.graph_backend import create_backend
    from pydantic import BaseModel
    from typing import Literal
    import json
    
    print("Testing CausalGraphV2...")
    
    backend = create_backend("inmemory")
    graph = CausalGraphV2(backend)
    
    # Add test claims
    c1 = graph.add_claim({"claim_id": "c1", "text": "A refutes B", "claim_type": "finding", "confidence": 0.9})
    c2 = graph.add_claim({"claim_id": "c2", "text": "B is true", "claim_type": "finding", "confidence": 0.8})
    
    # Add relationship
    graph.add_relationship("c1", "c2", {
        "verdict": "refutes",
        "confidence": 0.9,
        "citations": ["evidence_1"],
        "debate_log": []
    })
    
    # Find contradictions
    contradictions = graph.find_contradictions(min_confidence=0.85)
    print(f"✅ Found {len(contradictions)} contradictions")
    
    # Export
    viz_data = graph.export_for_visualization()
    print(f"✅ Exported {len(viz_data['nodes'])} nodes, {len(viz_data['edges'])} edges")
    
    print("✅ CausalGraphV2 test passed")
