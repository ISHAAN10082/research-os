"""
BGE Reranker v2-m3 - SOTA Cross-Encoder Reranking (Dec 2024)
License: Apache 2.0 (FREE & Open Source)

Features:
- Cross-encoder for high-precision relevance scoring
- Multilingual support (100+ languages)
- Efficient enough for M4 Air
- Dramatically improves retrieval quality
"""
import asyncio
from typing import List, Tuple, Optional, Union
from loguru import logger

# Lazy loading
_RERANKER_MODEL = None
_RERANKER_AVAILABLE = None


def _check_reranker():
    """Check if reranker dependencies are available."""
    global _RERANKER_AVAILABLE
    if _RERANKER_AVAILABLE is None:
        try:
            from FlagEmbedding import FlagReranker
            _RERANKER_AVAILABLE = True
        except ImportError:
            _RERANKER_AVAILABLE = False
            logger.warning("FlagEmbedding not installed. Run: pip install FlagEmbedding")
    return _RERANKER_AVAILABLE


class BGEReranker:
    """
    BGE Reranker v2-m3 - SOTA open-source reranker.
    
    Cross-encoders process query and document together, enabling
    much more nuanced relevance judgments than bi-encoder retrieval.
    
    Pipeline:
    1. Initial retrieval returns top-50 candidates (fast, approximate)
    2. Reranker scores each candidate precisely
    3. Return top-10 after reranking (accurate, relevant)
    
    Example:
        reranker = BGEReranker()
        ranked = reranker.rerank("What is attention?", documents)
        # ranked = [(doc_idx, score), ...] sorted by relevance
    """
    
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", use_fp16: bool = True):
        self.model_name = model_name
        self.use_fp16 = use_fp16
        self._model = None
        self._initialized = False
        self._fallback_mode = False
    
    def _lazy_init(self):
        """Lazy load the reranker model."""
        if self._initialized:
            return
        
        logger.info(f"Loading reranker: {self.model_name}")
        
        try:
            from FlagEmbedding import FlagReranker
            
            self._model = FlagReranker(
                self.model_name,
                use_fp16=self.use_fp16
            )
            logger.info("✅ BGE Reranker loaded")
            
        except ImportError:
            logger.warning("FlagEmbedding not available, trying sentence-transformers")
            try:
                from sentence_transformers import CrossEncoder
                
                # Fallback to a smaller cross-encoder
                self._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
                self._fallback_mode = True
                logger.info("✅ Cross-encoder fallback loaded")
                
            except ImportError:
                logger.warning("No reranker available, using embedding similarity fallback")
                self._model = None
                self._fallback_mode = True
        
        self._initialized = True
    
    def rerank(
        self, 
        query: str, 
        documents: List[str], 
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Rerank documents by relevance to query.
        
        Args:
            query: The search query
            documents: List of document texts to rerank
            top_k: Number of top results to return
            
        Returns:
            List of (document_index, relevance_score) tuples, sorted by score descending
        """
        self._lazy_init()
        
        if not documents:
            return []
        
        if self._model is None:
            # No reranker available - return original order with uniform scores
            logger.debug("No reranker model, returning original order")
            return [(i, 1.0 - i * 0.01) for i in range(min(len(documents), top_k))]
        
        try:
            if self._fallback_mode:
                # sentence-transformers CrossEncoder
                pairs = [[query, doc] for doc in documents]
                scores = self._model.predict(pairs)
            else:
                # FlagEmbedding FlagReranker
                pairs = [[query, doc] for doc in documents]
                scores = self._model.compute_score(pairs)
            
            # Create (index, score) pairs and sort
            ranked = [(i, float(score)) for i, score in enumerate(scores)]
            ranked.sort(key=lambda x: x[1], reverse=True)
            
            return ranked[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return [(i, 1.0 - i * 0.01) for i in range(min(len(documents), top_k))]
    
    async def rerank_async(
        self, 
        query: str, 
        documents: List[str], 
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """Async wrapper for reranking."""
        return await asyncio.to_thread(self.rerank, query, documents, top_k)
    
    def rerank_with_docs(
        self, 
        query: str, 
        documents: List[str], 
        top_k: int = 10
    ) -> List[dict]:
        """
        Rerank and return documents with scores.
        
        Returns:
            List of dicts with 'document', 'score', and 'original_index'
        """
        ranked = self.rerank(query, documents, top_k)
        
        return [
            {
                "document": documents[idx],
                "score": score,
                "original_index": idx
            }
            for idx, score in ranked
        ]


# Singleton instance
_reranker: Optional[BGEReranker] = None

def get_reranker() -> BGEReranker:
    """Get or create singleton reranker."""
    global _reranker
    if _reranker is None:
        _reranker = BGEReranker()
    return _reranker
