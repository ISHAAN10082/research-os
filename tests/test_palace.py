# tests/test_palace.py
import numpy as np
import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../jarvis_m4')))

from jarvis_m4.services.palace import MemoryPalaceV2
from unittest.mock import MagicMock

def test_palace_speed():
    print("🧪 Testing Memory Palace Generation Speed (PCA + Agglomerative)...")
    
    # Mock Embedder to skip loading
    palace = MemoryPalaceV2()
    palace.embedder = MagicMock()
    palace.embedder.encode.return_value = np.random.rand(768)
    
    # Generate 500 dummy papers with random embeddings
    print("  Generating 500 dummy papers...")
    papers = []
    for i in range(500):
        vec = np.random.rand(768).astype(np.float32)
        papers.append({
            "paper_id": f"p{i}",
            "specter2_embedding": vec.tolist(),
            "title": f"Paper {i}",
            "citation_count": i % 50
        })
        
    start = time.time()
    result = palace.generate_palace(papers)
    elapsed = time.time() - start
    
    print(f"⏱️ Generation took {elapsed:.3f}s")
    
    assert len(result["wings"]) > 0, "No wings generated"
    assert len(result["wings"]) <= max(2, int(np.sqrt(500))), "Too many wings"
    
    # Check structure
    wing_ids = list(result["wings"].keys())
    first_wing = result["wings"][wing_ids[0]]
    assert "center" in first_wing
    assert "papers" in first_wing
    
    print(f"✅ Generated {len(result['wings'])} wings correctly.")
    
    if elapsed > 2.0:
        print("⚠️ Warning: Palace generation slow (>2s)")
    else:
        print("✅ Speed check passed")

if __name__ == "__main__":
    test_palace_speed()
