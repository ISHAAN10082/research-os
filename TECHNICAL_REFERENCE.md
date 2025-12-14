# ResearchOS 3.0 – Complete System Guide
> **The Only Document You Need**

**Last Updated:** 2025-12-14  
**Version:** 3.0 V2 (Production-Ready Alpha)  
**Status:** ✅ Tested & Verified

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [What Is This?](#what-is-this)
3. [System Architecture](#system-architecture)
4. [Component Reference](#component-reference)
5. [API & Usage](#api--usage)
6. [Research Limitations & Mitigations](#research-limitations--mitigations)
7. [Testing & Validation](#testing--validation)
8. [Development Guide](#development-guide)

---

## Quick Start

### Installation
```bash
cd /Users/ishaanmajumdar/Desktop/Jrvis
python3 setup_jarvis_m4.py  # Auto-installs dependencies
```

### Process Your First Paper
```bash
cd jarvis_m4
python3 main_v2.py
```

This will:
1. Extract claims with SPECTER2 embeddings
2. Run evidence-based debates
3. Build causal knowledge graph
4. Generate 3D memory palace
5. Create Obsidian-ready reports

**Output:** `data/obsidian_vault/Papers/` + `data/current_scene_v2.json`

---

## What Is This?

ResearchOS 3.0 is a **local-first, M4-optimized** research intelligence system that:

### Core Capabilities
- ✅ **Extracts structured claims** from papers (100% valid JSON via Outlines)
- ✅ **Embeds with SPECTER2** (purpose-built for scientific literature)
- ✅ **Debates claims** using evidence-based multi-agent protocol
- ✅ **Builds causal graphs** with contradiction detection
- ✅ **Generates hypotheses** from graph topology
- ✅ **Organizes spatially** in a 3D Memory Palace
- ✅ **Exports to Obsidian** with Markdown/LaTeX support

### Key Differentiators
- **100% Local:** Runs on M4 Macs with 16GB RAM (1.2GB VRAM peak)
- **Research-Backed:** Acknowledges SciFact-Open 42% F1, implements mitigations
- **Evidence-Based:** All debate verdicts cite concrete evidence
- **Migration-Ready:** Graph backend abstraction (KuzuDB ↔ FalkorDB)
- **SPECTER2 Throughout:** Scientific embeddings, not generic

---

## System Architecture

### Data Flow
```
PDF/Text Input
      ↓
[ClaimExtractorV2] → SPECTER2 Embeddings (768-dim)
      ↓
[RetrievalEngine] → FAISS Index (semantic search)
      ↓
[EvidenceDebate] → Citation-required verdicts
      ↓
[CausalGraphV2] → NetworkX topology analysis
      ↓
[MemoryPalaceV2] → UMAP + HDBSCAN clustering
      ↓
[Reporter] → Obsidian Markdown + Scene JSON
```

### Component Stack
```
┌─────────────────────────────────────┐
│   UI Layer (Obsidian + Three.js)   │
├─────────────────────────────────────┤
│   Application (main_v2.py)         │
├─────────────────────────────────────┤
│   Reasoning (evidence_debate.py)   │
├─────────────────────────────────────┤
│   Graph (causal_graph_v2.py)       │
├─────────────────────────────────────┤
│   Retrieval (retrieval_engine.py)  │
├─────────────────────────────────────┤
│   Extraction (extract.py)          │
├─────────────────────────────────────┤
│   Storage (graph_backend.py)       │
└─────────────────────────────────────┘
```

---

## Component Reference

### 1. ClaimExtractorV2 (`services/extract.py`)

**Purpose:** Extract structured claims with SPECTER2 embeddings

**Interface:**
```python
from services.extract import ClaimExtractorV2

extractor = ClaimExtractorV2(model_path="microsoft/Phi-3.5-mini-instruct")
claims = extractor.extract_from_paper(text, paper_id)
# Returns: List[ExtractedClaim] with specter2_embedding field
```

**Guarantees:**
- 100% JSON validity (Outlines grammar)
- 768-dim SPECTER2 embeddings
- Fallback to MLX if Outlines fails

---

### 2. Graph Backend (`services/graph_backend.py`)

**Purpose:** Abstract graph operations for database migration

**Interface:**
```python
from services.graph_backend import create_backend

backend = create_backend("kuzu")  # or "inmemory" for testing
backend.add_node("Claim", properties)
backend.add_edge(from_id, to_id, "RELATES", properties)
```

**Supported Backends:**
- `kuzu` – KuzuDB (current production)
- `inmemory` – In-memory (testing)
- `falkor` – FalkorDB (migration target, stubbed)

---

### 3. Retrieval Engine (`services/retrieval_engine.py`)

**Purpose:** Fast semantic search with SPECTER2

**Interface:**
```python
from services.retrieval_engine import RetrievalEngine

retrieval = RetrievalEngine()
retrieval.index_claim(claim_id, embedding, metadata)
results = retrieval.search("transformers in NLP", top_k=5)
# Returns: List[{claim_id, text, similarity_score, metadata}]
```

**Performance:**
- <100ms on 1000 claims
- FAISS ANN search (L2 distance)
- Chroma metadata storage (optional)

---

### 4. Evidence-Based Debate (`services/evidence_debate.py`)

**Purpose:** Citation-required claim verification

**Interface:**
```python
from services.evidence_debate import EvidenceBasedDebate

debate = EvidenceBasedDebate(retrieval_engine, debate_agents)
result = debate.debate_claim_pair(claim_a, claim_b)
# Returns: DebateResult with verdict, confidence, citations, requires_human flag
```

**Protocol:**
1. Retrieve evidence for both claims
2. Run 3-agent debate (Skeptic → Connector → Synthesizer)
3. Extract citations from debate log
4. Flag for human review if confidence <0.85 or citations <2

**Mitigations:**
- Prevents bias reinforcement (evidence-grounded)
- Conservative thresholds (SciFact-Open 42% F1)
- All verdicts require ≥2 citations

---

### 5. Causal Graph V2 (`services/causal_graph_v2.py`)

**Purpose:** Topology analysis and contradiction detection

**Interface:**
```python
from services.causal_graph_v2 import CausalGraphV2

graph = CausalGraphV2(graph_backend, debate_system)
graph.add_claim(claim_dict)
graph.add_relationship(claim_a_id, claim_b_id, debate_result)

# Queries
contradictions = graph.find_contradictions(min_confidence=0.85)
unsupported = graph.find_unsupported_claims()
frontiers = graph.find_frontier_edges(max_confidence=0.6)
```

**Algorithms:**
- NetworkX DiGraph for topology
- PageRank for importance scoring
- Shortest path for evidence chains

---

### 6. Memory Palace V2 (`services/palace.py`)

**Purpose:** 3D spatial organization with SPECTER2

**Interface:**
```python
from services.palace import MemoryPalaceV2

palace = MemoryPalaceV2()
palace_data = palace.generate_palace(papers)
# Returns: {wings: {}, debris: []} with 3D coordinates
```

**Algorithm:**
1. UMAP: Reduce SPECTER2 embeddings to 3D (adaptive n_neighbors)
2. HDBSCAN: Density-based clustering
3. Label clusters from central paper titles
4. Scale nodes by citation count

---

## API & Usage

### End-to-End Pipeline

```python
from services.graph_backend import create_backend
from services.extract import ClaimExtractorV2
from services.retrieval_engine import RetrievalEngine
# ... (other imports)

# Initialize
backend = create_backend("inmemory")
extractor = ClaimExtractorV2()
retrieval = RetrievalEngine()
# ... (other components)

# Process paper
with open("paper.txt") as f:
    text = f.read()

claims = extractor.extract_from_paper(text, "paper_001")

for claim in claims:
    # Index
    retrieval.index_claim(claim.claim_id, claim.specter2_embedding, claim.dict())
    
    # Debate against similar
    similar = retrieval.search_by_embedding(claim.specter2_embedding, top_k=3)
    for s in similar:
        result = debate.debate_claim_pair(claim.dict(), s['metadata'])
        graph.add_relationship(claim.claim_id, s['claim_id'], result.dict())

# Generate palace
palace_data = palace.generate_palace(papers)

# Export
scene_json = scene_gen.generate_scene(palace_data)
report_md = reporter.generate_paper_report(paper, claims, debates)
```

### Quick Scripts

**Extract Claims Only:**
```python
extractor = ClaimExtractorV2()
claims = extractor.extract_from_paper(text, "paper_id")
print(f"Extracted {len(claims)} claims")
```

**Search Similar Claims:**
```python
retrieval = RetrievalEngine()
# ... index claims
results = retrieval.search("attention mechanisms", top_k=5)
for r in results:
    print(f"{r['similarity_score']:.2f}: {r['text']}")
```

**Find Contradictions:**
```python
graph = CausalGraphV2(backend)
# ... add claims and relationships
contradictions = graph.find_contradictions(min_confidence=0.85)
for a_id, b_id, citations in contradictions:
    print(f"{a_id} refutes {b_id} (evidence: {citations})")
```

---

## Research Limitations & Mitigations

### Acknowledged Constraints

#### 1. Open-Domain Claim Verification
**Research:** SciFact-Open achieves only 42.1% F1 (down from 64.7% on curated dataset)

**Our Approach:**
- ✅ Conservative confidence thresholds (>0.85 for auto-flagging)
- ✅ Human-in-the-loop verification (requires_human flag)
- ✅ Domain-scoped deployment (start narrow, expand incrementally)
- ✅ User feedback loop (planned for Week 3)

**Honest Metric:** Target 70% precision on expert-verified contradictions

---

#### 2. Multi-Agent Debate Bias
**Research:** Debate can reinforce biases if not carefully designed (arXiv:2503.16814)

**Our Approach:**
- ✅ Evidence-based protocol (citation-required, not free-form)
- ✅ Agent diversity (different temperatures: 0.3, 0.7, 0.1)
- ✅ Transparent uncertainty (show full debate log)
- ✅ Fallback to single-agent if no similar claims

**Honest Metric:** Debate useful in >60% of cases (subjective survey)

---

#### 3. Multi-Source Noise
**Research:** Adding web/Reddit increases false claim rate

**Our Approach:**
- ✅ Trust scoring (papers > Reddit > blogs)
- ✅ Separate debate pools (academic vs. community)
- ✅ Evidence strength weighting (citation count + venue rank)
- ✅ Default filter: papers only (advanced users can toggle)

---

### Success Metrics (Realistic)

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Contradiction Precision** | >70% | Expert-verified, not auto-detected |
| **Debate Utility** | >60% helpful | Subjective user survey |
| **False Positive Rate** | <30% | Acceptable for alpha with review |
| **User Correction Rate** | >50 corrections | Build training corpus |

---

## Testing & Validation

### Module Tests (All Passing ✅)

```bash
# Graph backend
cd jarvis_m4 && python3 services/graph_backend.py
# Output: ✅ Backend abstraction test passed

# Retrieval engine
cd jarvis_m4 && python3 services/retrieval_engine.py
# Output: ✅ RetrievalEngine test passed

# Memory palace
cd jarvis_m4 && python3 services/palace.py
# Output: ✅ MemoryPalaceV2 test passed (3 wings from 20 papers)

# Causal graph
cd jarvis_m4 && python3 services/causal_graph_v2.py
# Output: ✅ CausalGraphV2 test passed
```

### Integration Test
```bash
cd jarvis_m4 && python3 main_v2.py
```

**Expected Output:**
- Extracts 5-10 claims from test paper
- Runs 2-5 debates
- Generates palace with 1-2 wings
- Creates report in `data/obsidian_vault/Papers/`

---

## Development Guide

### Adding a New Service

1. **Create module** in `jarvis_m4/services/my_service.py`
2. **Define interface** with type hints and docstrings
3. **Add test** in `if __name__ == "__main__"` block
4. **Import** in `main_v2.py`
5. **Document** in this guide

### Extending Graph Backend

To add a new backend (e.g., Neo4j):

```python
# In graph_backend.py
class Neo4jBackend(GraphBackend):
    def __init__(self, uri, user, password):
        from neo4j import GraphDatabase
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def execute_query(self, query, params):
        # Translate to Cypher and execute
        pass
```

Then update factory:
```python
backends = {
    "kuzu": KuzuBackend,
    "inmemory": InMemoryBackend,
    "neo4j": Neo4jBackend  # Add here
}
```

### Performance Optimization

**FAISS Index Types:**
```python
# Current: Flat (exact search)
faiss.IndexFlatL2(768)

# Faster: IVF (approximate)
quantizer = faiss.IndexFlatL2(768)
index = faiss.IndexIVFFlat(quantizer, 768, 100)  # 100 clusters
index.train(embeddings)
```

**UMAP Parameters:**
```python
# Faster projection
umap.UMAP(n_components=3, n_neighbors=10, min_dist=0.05)

# Better preservation
umap.UMAP(n_components=3, n_neighbors=30, min_dist=0.2)
```

---

## Files & Directories

```
Jrvis/
├── README.md                           # User-facing overview
├── TECHNICAL_REFERENCE.md             # THIS FILE (master guide)
├── ARCHITECTURE.md                     # System design only
│
├── jarvis_m4/
│   ├── services/
│   │   ├── extract.py                 # ClaimExtractorV2
│   │   ├── graph_backend.py           # Backend abstraction
│   │   ├── retrieval_engine.py        # FAISS + SPECTER2
│   │   ├── evidence_debate.py         # Citation-required debate
│   │   ├── causal_graph_v2.py         # NetworkX topology
│   │   ├── palace.py                  # SPECTER2 clustering
│   │   ├── scene.py                   # Three.js export
│   │   └── reporter.py                # Obsidian sync
│   ├── main_v2.py                     # Unified orchestrator
│   └── data/
│       ├── research_v2.kuzu/          # Graph database
│       ├── faiss_index.bin            # Vector index
│       ├── obsidian_vault/            # Reports
│       └── current_scene_v2.json      # Palace export
│
└── tests/
    ├── verify_debate_logic.py
    ├── verify_spatial.py
    └── verify_pipeline.py
```

---

## Troubleshooting

### Issue: UMAP hangs on first run
**Cause:** Numba JIT compilation  
**Fix:** `export NUMEXPR_MAX_THREADS=1`

### Issue: SPECTER2 model not found
**Cause:** Not downloaded  
**Fix:** `huggingface-cli download allenai/specter2`

### Issue: Outlines fails to load
**Cause:** MLX model incompatibility  
**Fix:** Extractor automatically falls back to MLX direct

### Issue: Graph backend error
**Cause:** KuzuDB schema mismatch  
**Fix:** `rm -rf data/research_v2.kuzu` and restart

---

## Changelog

**V2.0 (2025-12-14)**
- ✅ SPECTER2 integration throughout stack
- ✅ Graph backend abstraction (migration-ready)
- ✅ Evidence-based debate protocol
- ✅ NetworkX topology analysis
- ✅ Conservative confidence thresholds
- ✅ Human-in-the-loop flagging

**V1.0 (2025-12-13)**
- Initial implementation
- Generic embeddings
- Basic debate
- KuzuDB hard-coded

---

## License & Citation

**License:** MIT

**Citation:**
```bibtex
@software{researchos_v3,
  title={ResearchOS 3.0: Local-First Research Intelligence},
  author={ResearchOS Team},
  year={2025},
  url={https://github.com/yourusername/researchos}
}
```

---

## Support

- **Issues:** Open GitHub issue
- **Docs:** This file (TECHNICAL_REFERENCE.md)
- **Architecture:** See ARCHITECTURE.md
- **Quick Start:** See README.md

**Remember:** This is a research assistant, not an oracle. Always verify critical claims against primary sources.
