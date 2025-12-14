# tests/test_hnsw_retrieval.py
import numpy as np
import sys
import os
import shutil
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../jarvis_m4')))

from jarvis_m4.services.retrieval_engine import RetrievalEngine

def test_hnsw_recall():
    print("🧪 Testing HNSW Retrieval Recall...")
    
    # Cleanup previous chroma/faiss data to ensure fresh start
    if os.path.exists("data"):
        pass # keep data dir
        
    engine = RetrievalEngine(use_chroma=False)
    
    # Create a "known" target vector (normalized)
    known_vec = np.random.rand(768).astype(np.float32)
    known_vec /= np.linalg.norm(known_vec)
    
    engine.index_claim("target_01", known_vec.tolist(), {"text": "This is the target claim"})
    
    # Add 1000 distractor vectors
    print("  Indexing 1000 distractors...")
    for i in range(1000):
        vec = np.random.rand(768).astype(np.float32)
        vec /= np.linalg.norm(vec)
        engine.index_claim(f"distractor_{i}", vec.tolist(), {"text": f"Noise {i}"})
        
    # Search with the exact vector (should be #1 match with score ~1.0)
    print("  Searching...")
    results = engine.search_by_embedding(known_vec.tolist(), top_k=5)
    
    found = False
    for r in results:
        if r['claim_id'] == "target_01":
            found = True
            print(f"  ✅ Found target! Score: {r['similarity_score']:.4f}")
            # L2 distance for identical vector is 0, so similarity 1/(1+0) = 1.0
            # Floating point error might make it 0.9999
            assert r['similarity_score'] > 0.99, "Similarity score should be near 1.0 for exact match"
            break
            
    assert found, "❌ HNSW Failed to retrieve exact match"
    print("✅ HNSW Recall Test Passed")

if __name__ == "__main__":
    test_hnsw_recall()
