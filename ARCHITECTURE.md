# ResearchOS 3.0 – Architecture Definition
> **Single Source of Truth for Implementation**

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                     │
│  FastAPI Endpoints | Three.js Palace | Obsidian Reports    │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                         │
│  main.py (Orchestrator) | reporter.py | scene.py           │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    REASONING LAYER                          │
│  debate.py (Evidence-Based) | hypothesis_generator.py      │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                     GRAPH LAYER                             │
│  graph_backend.py (Abstract) | causal_graph.py (NetworkX) │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  RETRIEVAL LAYER                            │
│  retrieval_engine.py (FAISS + Chroma) | SPECTER2           │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  EXTRACTION LAYER                           │
│  extract.py (Outlines + Phi-3.5) | SPECTER2 Embeddings     │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                            │
│  KuzuDB/FalkorDB (Graph) | Chroma (Vectors) | Files (Raw) │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Extraction Layer

**File:** `jarvis_m4/services/extract_v2.py`

**Dependencies:**
```python
outlines >= 0.1.0
mlx-lm >= 0.28.0
sentence-transformers >= 2.3.0
```

**Interface:**
```python
class ClaimExtractorV2:
    def __init__(self):
        # Outlines for structured generation
        # SPECTER2 for embeddings (NOT generic)
        pass
    
    def extract_from_paper(self, text: str, paper_id: str) -> List[ExtractedClaim]:
        """
        Returns: List of claims with SPECTER2 embeddings
        Guarantee: 100% JSON validity
        """
        pass
```

**Data Model:**
```python
from pydantic import BaseModel
from typing import List, Literal

class ExtractedClaim(BaseModel):
    text: str
    claim_type: Literal["finding", "method", "implication", "hypothesis"]
    section: str
    confidence: float
    evidence_snippets: List[str]
    specter2_embedding: List[float]  # 768-dim
```

---

### 2. Graph Layer

**File:** `jarvis_m4/services/graph_backend.py`

**Purpose:** Abstract graph operations to enable KuzuDB → FalkorDB migration

**Interface:**
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class GraphBackend(ABC):
    @abstractmethod
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute Cypher-like query"""
        pass
    
    @abstractmethod
    def add_node(self, label: str, properties: Dict) -> str:
        """Returns node ID"""
        pass
    
    @abstractmethod
    def add_edge(self, from_id: str, to_id: str, rel_type: str, properties: Dict) -> str:
        """Returns edge ID"""
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Dict:
        pass
    
    @abstractmethod
    def get_neighbors(self, node_id: str, rel_type: str = None) -> List[Dict]:
        pass

class KuzuBackend(GraphBackend):
    """Current implementation"""
    pass

class FalkorBackend(GraphBackend):
    """Future migration target"""
    pass

class InMemoryBackend(GraphBackend):
    """For testing"""
    pass
```

---

### 3. Retrieval Layer

**File:** `jarvis_m4/services/retrieval_engine.py`

**Dependencies:**
```python
faiss-cpu >= 1.7.4
chromadb >= 0.4.0
sentence-transformers >= 2.3.0
```

**Interface:**
```python
class RetrievalEngine:
    def __init__(self, backend: str = "faiss"):
        self.embedder = SentenceTransformer("allenai/specter2")
        self.faiss_index = faiss.IndexFlatL2(768)
        self.chroma = chromadb.Client()
    
    def index_claim(self, claim_id: str, embedding: List[float], metadata: Dict):
        """Index claim for retrieval"""
        pass
    
    def search(self, query_text: str, top_k: int = 5, min_similarity: float = 0.7) -> List[Dict]:
        """
        Returns: List of {claim_id, text, similarity_score, metadata}
        Guarantee: <100ms on 10k claims
        """
        pass
    
    def search_by_embedding(self, embedding: List[float], top_k: int = 5) -> List[Dict]:
        """For claim-to-claim similarity"""
        pass
```

---

### 4. Debate Layer

**File:** `jarvis_m4/services/evidence_debate.py`

**Interface:**
```python
class EvidenceBasedDebate:
    def __init__(self, retrieval_engine: RetrievalEngine):
        self.retrieval = retrieval_engine
        self.agents = DebateAgents()
    
    def debate_claim_pair(self, claim_a: ExtractedClaim, claim_b: ExtractedClaim) -> DebateResult:
        """
        Returns: DebateResult with verdict, confidence, citations, requires_human flag
        Guarantee: All verdicts cite evidence
        """
        pass
```

**Data Model:**
```python
class DebateResult(BaseModel):
    verdict: Literal["refutes", "supports", "extends", "uncertain"]
    confidence: float  # 0.0-1.0
    citations: List[str]  # Evidence claim IDs
    requires_human: bool
    debate_log: List[str]
    agent_confidences: Dict[str, float]  # {"skeptic": 0.8, ...}
```

---

### 5. Causal Graph Layer

**File:** `jarvis_m4/services/causal_graph_v2.py`

**Interface:**
```python
import networkx as nx

class CausalGraph:
    def __init__(self, graph_backend: GraphBackend):
        self.backend = graph_backend
        self.nx_graph = nx.DiGraph()  # For local analysis
    
    def add_claim(self, claim: ExtractedClaim):
        """Add claim node"""
        pass
    
    def add_relationship(self, from_id: str, to_id: str, verdict: DebateResult):
        """Add edge with debate metadata"""
        pass
    
    def find_contradictions(self, min_confidence: float = 0.85) -> List[Tuple[str, str]]:
        """Returns: List of (claim_a_id, claim_b_id) pairs"""
        pass
    
    def find_frontier_edges(self, max_confidence: float = 0.6) -> List[Dict]:
        """Returns: Uncertain relationships worth exploring"""
        pass
    
    def get_evidence_path(self, claim_a_id: str, claim_b_id: str) -> List[str]:
        """Returns: Chain of evidence linking two claims"""
        pass
```

---

### 6. Hypothesis Generator

**File:** `jarvis_m4/services/hypothesis_generator_v2.py`

**Interface:**
```python
class HypothesisGenerator:
    def __init__(self, causal_graph: CausalGraph):
        self.graph = causal_graph
    
    def identify_gaps(self, domain_filter: str = None) -> List[ResearchGap]:
        """
        Returns: List of structural gaps (NOT novel hypotheses)
        Types: contradiction_resolution, validation_needed, methodological_gap
        """
        pass
```

**Data Model:**
```python
class ResearchGap(BaseModel):
    gap_type: Literal["contradiction_resolution", "validation_needed", "methodological_gap"]
    priority: Literal["high", "medium", "low"]
    description: str
    involved_claims: List[str]
    evidence_strength: float
    suggested_action: str  # e.g., "Design critical experiment"
```

---

## Data Flow

### Ingestion Flow
```
1. Raw PDF → MinerU parser → Plain text
2. Text → ClaimExtractorV2 → List[ExtractedClaim] (with SPECTER2 embeddings)
3. ExtractedClaim → GraphBackend.add_node()
4. ExtractedClaim → RetrievalEngine.index_claim()
```

### Debate Flow
```
1. New claim arrives
2. RetrievalEngine.search(new_claim) → Similar existing claims
3. For each similar claim:
   a. EvidenceBasedDebate.debate_claim_pair()
   b. DebateResult → CausalGraph.add_relationship()
4. If DebateResult.requires_human == True:
   → Flag for user review
```

### Query Flow
```
1. User asks: "What contradicts claim X?"
2. CausalGraph.find_contradictions() → List of claim pairs
3. For each pair:
   a. CausalGraph.get_evidence_path() → Citation chain
   b. Format as report
```

---

## Storage Schema

### Graph Nodes

**Claim Node:**
```python
{
    "claim_id": str,
    "text": str,
    "claim_type": str,
    "paper_id": str,
    "confidence": float,
    "citation_count": int,
    "specter2_embedding": List[float]
}
```

**Source Node:**
```python
{
    "source_id": str,
    "source_type": str,  # paper | web | reddit | note
    "url": str,
    "title": str,
    "trust_score": float,
    "metadata": str  # JSON
}
```

### Graph Edges

**RELATES Edge:**
```python
{
    "relation_type": str,  # refutes | supports | extends | uncertain
    "confidence": float,
    "citations": List[str],  # Evidence claim IDs
    "debate_log": str,  # JSON
    "created_at": datetime
}
```

---

## Success Criteria (Per Milestone)

### Milestone 1: Extraction
- [ ] 100% JSON validity on 20 test papers
- [ ] SPECTER2 embeddings cluster semantically similar claims
- [ ] Zero post-hoc repair needed

### Milestone 2: Graph Backend
- [ ] Tests pass with both KuzuDB and InMemoryBackend
- [ ] Migration script KuzuDB → FalkorDB completes without data loss

### Milestone 3: Retrieval
- [ ] Query "attention mechanisms" returns relevant claims in top-5
- [ ] Search latency <100ms on 1000 claims
- [ ] Recall@10 >80% on curated test set

### Milestone 4: Evidence-Based Debate
- [ ] On SciFact subset: Precision >70%, Recall >40%
- [ ] All "refutes" verdicts have ≥2 cited evidence IDs
- [ ] Low-confidence debates flagged for human review

### Milestone 5: Graph Queries
- [ ] Find 3-5 contradictions experts confirm
- [ ] Identify 5-10 frontier edges experts deem plausible

### Milestone 6: Memory Palace
- [ ] Users report improved recall in pilot
- [ ] <3 clicks to return to "main thread"
- [ ] Clusters correspond to known topic boundaries

---

## Development Workflow

1. **Define** – Create this architecture doc (DONE)
2. **Build** – Implement component by component
3. **Test** – Each component has unit tests
4. **Integrate** – Connect components via defined interfaces
5. **Validate** – Run success criteria tests
6. **Iterate** – Improve based on results

**Current Status:** Ready to build Milestone 1
**Next File:** `jarvis_m4/services/extract_v2.py`
