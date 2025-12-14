
import sys
import os
import time
from loguru import logger

# Add parent path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def verify_reranker():
    logger.info("🧪 Verifying FastEmbed Reranker...")
    
    try:
        from research_os.foundation.model_cache import get_reranker
        reranker = get_reranker()
        
        query = "What is deep learning?"
        docs = [
            "Deep learning is a subset of machine learning using neural networks.",
            "Apples are a type of fruit that grow on trees.",
            "Neural networks can model complex patterns."
        ]
        
        logger.info(f"Query: {query}")
        
        # DEBUG: Inspect methods
        logger.info(f"CrossEncoder Methods: {dir(reranker.model)}")

        # Test wrapper API directly
        logger.info("Computing scores (direct rerank)...")
        # Direct test to inspect output
        results = list(reranker.model.rerank(query, docs))
        logger.info(f"Rerank Results: {results}")
        
        # Test my wrapper logic (Production Check)
        pairs = [[query, doc] for doc in docs]
        scores = reranker.compute_score(pairs)
        logger.info(f"Wrapper Scores: {scores}")
        
        # Validating order
        assert scores[0] > scores[1], "Deep learning doc should score higher than apples"
        
        logger.info("✅ Reranker Logic Verified")
        return True
        
    except Exception as e:
        logger.error(f"❌ Reranker Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if verify_reranker():
        sys.exit(0)
    else:
        sys.exit(1)
