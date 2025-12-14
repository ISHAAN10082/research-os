# tests/run_logic_tests.py
import sys
from unittest.mock import MagicMock

# 1. MOCK HEAVY ML LIBS BEFORE IMPORT
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["sentence_transformers"].SentenceTransformer = MagicMock
sys.modules["torch"] = MagicMock()
sys.modules["faiss"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["outlines"] = MagicMock()
sys.modules["mlx_lm"] = MagicMock()
sys.modules["mlx"] = MagicMock()
sys.modules["mlx.core"] = MagicMock()

# Mock FAISS index behavior
mock_index = MagicMock()
mock_index.ntotal = 0
sys.modules["faiss"].IndexHNSWFlat.return_value = mock_index
sys.modules["faiss"].IndexFlatL2.return_value = mock_index

# Allow numpy/scikit-learn (they are fast/needed)
import numpy as np

# Now import services
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../jarvis_m4')))

from jarvis_m4.services.palace import MemoryPalaceV2
from jarvis_m4.services.evidence_debate import EvidenceBasedDebate, DebateResult
from jarvis_m4.services.retrieval_engine import RetrievalEngine

def test_palace_logic():
    print("🧪 Testing Memory Palace Logic (Mocked ML)...")
    palace = MemoryPalaceV2()
    
    # Mock embeddings directly in data
    papers = [{"paper_id": f"p{i}", "specter2_embedding": np.random.rand(768).tolist(), "title": f"T{i}"} for i in range(50)]
    
    result = palace.generate_palace(papers)
    assert len(result["wings"]) > 0
    print("✅ Palace logic correct")

def test_debate_cache_logic():
    print("🧪 Testing Debate Cache Logic...")
    
    # Setup
    if os.path.exists("data/debate_cache.json"):
        os.remove("data/debate_cache.json")
        
    retrieval = MagicMock() # Mock retrieval
    agents = MagicMock()     # Mock agents
    agents.run_debate.return_value = {"verdict": "refutes", "confidence": 0.8, "log": []}
    
    debate = EvidenceBasedDebate(retrieval, agents)
    
    claim_a = {"claim_id": "A", "text": "A", "specter2_embedding": np.random.rand(768).tolist()}
    claim_b = {"claim_id": "B", "text": "B", "specter2_embedding": np.random.rand(768).tolist()}
    
    # 1. First Pass (Computation)
    res1 = debate.debate_claim_pair(claim_a, claim_b)
    
    # 2. Second Pass (Cache Hit)
    # Change agents to return something else to prove we didn't call them
    agents.run_debate.return_value = {"verdict": "supports", "confidence": 0.1}
    res2 = debate.debate_claim_pair(claim_b, claim_a) # Symmetric
    
    assert res1.verdict == res2.verdict # Should still be 'refutes' from cache
    print("✅ Symmetric Cache logic correct")
    
    # 3. Similarity Filter
    # Identical vectors
    claim_c = {"claim_id": "C", "text": "C", "specter2_embedding": claim_a["specter2_embedding"]}
    res3 = debate.debate_claim_pair(claim_a, claim_c)
    assert res3.verdict == "supports"
    assert "high similarity" in res3.debate_log[0]
    print("✅ Similarity Filter logic correct")

def test_retrieval_logic():
    print("🧪 Testing Retrieval Logic...")
    engine = RetrievalEngine(use_chroma=False)
    # RetrievalEngine uses FAISS mock
    engine.index.ntotal = 10
    engine.index.search.return_value = (np.array([[0.5]]), np.array([[1]])) # Distance, Index
    engine.index_to_id = {1: "c1"}
    engine.id_to_metadata = {"c1": {"text": "found"}}
    
    res = engine.search_by_embedding([0.1]*768)
    assert len(res) == 1
    assert res[0]['claim_id'] == "c1"
    print("✅ Retrieval logic correct")

if __name__ == "__main__":
    try:
        test_palace_logic()
        test_debate_cache_logic()
        test_retrieval_logic()
        print("\n🎉 ALL LOGIC TESTS PASSED")
    except Exception as e:
        print(f"\n❌ TESTS FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
