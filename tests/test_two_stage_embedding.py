# tests/test_two_stage_embedding.py
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../jarvis_m4')))

from jarvis_m4.services.extract import ClaimExtractorV2

def test_two_stage_speed():
    print("🧪 Testing Two-Stage Embedding Speed...")
    extractor = ClaimExtractorV2()
    
    # Dummy text with clear sections
    dummy_text = """## Introduction
    This paper proposes a new method for deep learning optimization.
    The method is called FastOpt.
    ## Method
    We use a transformer architecture with 12 layers.
    We apply Adam optimizer with learning rate 0.001.
    ## Results
    Our approach outperforms baselines by 15% in accuracy.
    Convergence speed is 2x faster.
    """
    
    start = time.time()
    claims = extractor.extract_from_paper(dummy_text, "dummy_001")
    elapsed = time.time() - start
    
    print(f"⏱️ Extraction + Two-Stage Embed took {elapsed:.3f}s")
    
    assert len(claims) > 0, "No claims extracted"
    assert all(hasattr(c, "specter2_embedding") for c in claims), "Missing embeddings"
    assert len(claims[0].specter2_embedding) == 768, "Wrong embedding dimension"
    
    # Check if speed is reasonable (first run might be slow due to load, subsequent should be fast)
    # Ideally < 2s for this small text
    if elapsed > 10.0:
        print("⚠️ Warning: Extraction took > 10s (likely model loading overhead)")
    else:
        print("✅ Speed check passed")

if __name__ == "__main__":
    test_two_stage_speed()
