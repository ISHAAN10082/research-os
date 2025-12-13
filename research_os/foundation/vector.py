"""
BGE-M3 Vector Engine - SOTA Multilingual Embeddings (Dec 2024)
License: Apache 2.0 (FREE & Open Source)

Features:
- Multi-Functionality: Dense, Sparse, and ColBERT in one model
- Multi-Linguality: 100+ languages
- Multi-Granularity: Up to 8192 tokens
- MTEB Score: 71.67 (top-tier)
"""
import asyncio
from typing import List, Optional, Union
import numpy as np
from loguru import logger
from research_os.config import settings

# Lazy loading flags
_MODEL_LOADED = False
_EMBED_MODEL = None
_SPARSE_MODEL = None


class VectorEngine:
    """
    BGE-M3 powered vector engine with multi-vector support.
    
    Supports three embedding types:
    1. Dense: Traditional semantic embeddings (default)
    2. Sparse: BM25-like lexical embeddings
    3. ColBERT: Multi-vector for late interaction
    
    Example:
        engine = VectorEngine()
        dense = engine.embed(["Hello world"])
        sparse = engine.embed_sparse(["Hello world"])
    """
    
    def __init__(self, model_name: str = None, use_fp16: bool = True):
        self.model_name = model_name or getattr(settings, 'EMBEDDING_MODEL', 'BAAI/bge-m3')
        self.use_fp16 = use_fp16
        self.device = self._get_device()
        self._model = None
        self._initialized = False
        
    def _get_device(self) -> str:
        """Detect best available device."""
        try:
            import torch
            if torch.backends.mps.is_available():
                return "mps"
            elif torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"
    
    def _lazy_init(self):
        """Lazy load the embedding model."""
        if self._initialized:
            return
            
        logger.info(f"Loading embedding model: {self.model_name}")
        
        try:
            # Try FlagEmbedding first (optimized for BGE)
            from FlagEmbedding import BGEM3FlagModel
            
            self._model = BGEM3FlagModel(
                self.model_name,
                use_fp16=self.use_fp16,
                device=self.device
            )
            self._model_type = "bgem3"
            logger.info(f"✅ BGE-M3 loaded on {self.device}")
            
        except ImportError:
            # Fallback to sentence-transformers
            logger.warning("FlagEmbedding not found, using sentence-transformers fallback")
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(
                    self.model_name,
                    device=self.device
                )
                self._model_type = "sentence_transformer"
                logger.info(f"✅ SentenceTransformer loaded on {self.device}")
            except ImportError:
                # Ultimate fallback to FastEmbed
                logger.warning("sentence-transformers not found, using FastEmbed")
                from fastembed import TextEmbedding
                self._model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
                self._model_type = "fastembed"
                logger.info("✅ FastEmbed loaded (lightweight fallback)")
        
        self._initialized = True
        
        # Warmup
        _ = self.embed(["ResearchOS initialization"])
        logger.info("VectorEngine ready")
    
    def embed(self, texts: Union[str, List[str]], instruction: str = None) -> List[List[float]]:
        """
        Generate dense embeddings.
        
        Args:
            texts: Single text or list of texts
            instruction: Optional instruction prefix (for retrieval tasks)
            
        Returns:
            List of embedding vectors (1024-dim for BGE-M3)
        """
        self._lazy_init()
        
        if isinstance(texts, str):
            texts = [texts]
        
        # Add instruction prefix if provided
        if instruction:
            texts = [f"{instruction}: {t}" for t in texts]
        
        if self._model_type == "bgem3":
            result = self._model.encode(
                texts,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False
            )
            embeddings = result['dense_vecs']
        elif self._model_type == "sentence_transformer":
            embeddings = self._model.encode(
                texts,
                normalize_embeddings=True,
                convert_to_numpy=True
            )
        else:  # fastembed
            embeddings = list(self._model.embed(texts))
            embeddings = np.array(embeddings)
        
        return embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings
    
    def embed_query(self, text: str, instruction: str = "Represent this query for retrieval") -> List[float]:
        """Embed a single query with instruction prefix."""
        return self.embed([text], instruction=instruction)[0]
    
    def embed_document(self, text: str) -> List[float]:
        """Embed a document (no instruction prefix)."""
        return self.embed([text])[0]
    
    def embed_sparse(self, texts: Union[str, List[str]]) -> List[dict]:
        """
        Generate sparse (lexical) embeddings.
        Useful for hybrid search combining semantic + keyword matching.
        
        Returns:
            List of dicts with token indices and weights
        """
        self._lazy_init()
        
        if isinstance(texts, str):
            texts = [texts]
        
        if self._model_type == "bgem3":
            result = self._model.encode(
                texts,
                return_dense=False,
                return_sparse=True,
                return_colbert_vecs=False
            )
            return result.get('lexical_weights', [{}] * len(texts))
        else:
            # Fallback: no sparse support in other models
            logger.warning("Sparse embeddings only supported with BGE-M3")
            return [{}] * len(texts)
    
    def embed_colbert(self, texts: Union[str, List[str]]) -> List[np.ndarray]:
        """
        Generate ColBERT multi-vector embeddings.
        Returns one vector per token for late interaction search.
        
        Returns:
            List of numpy arrays, each shape [num_tokens, embedding_dim]
        """
        self._lazy_init()
        
        if isinstance(texts, str):
            texts = [texts]
        
        if self._model_type == "bgem3":
            result = self._model.encode(
                texts,
                return_dense=False,
                return_sparse=False,
                return_colbert_vecs=True
            )
            return result.get('colbert_vecs', [])
        else:
            logger.warning("ColBERT embeddings only supported with BGE-M3")
            # Fallback: return single vector repeated
            dense = self.embed(texts)
            return [np.array([d]) for d in dense]
    
    def compute_similarity(self, query_emb: List[float], doc_embs: List[List[float]]) -> List[float]:
        """Compute cosine similarity between query and documents."""
        query = np.array(query_emb)
        docs = np.array(doc_embs)
        
        # Normalize
        query_norm = query / np.linalg.norm(query)
        docs_norm = docs / np.linalg.norm(docs, axis=1, keepdims=True)
        
        # Cosine similarity
        similarities = np.dot(docs_norm, query_norm)
        return similarities.tolist()
    
    async def embed_async(self, texts: List[str]) -> List[List[float]]:
        """Async wrapper for embedding."""
        return await asyncio.to_thread(self.embed, texts)


# Global singleton instance
_vector_engine: Optional[VectorEngine] = None

def get_vector_engine() -> VectorEngine:
    """Get or create the global vector engine instance."""
    global _vector_engine
    if _vector_engine is None:
        _vector_engine = VectorEngine()
    return _vector_engine

# Backward compatibility alias
vector_engine = property(lambda self: get_vector_engine())

# Create default instance for import compatibility
class _VectorEngineModule:
    """Module-level vector engine for backward compatibility."""
    
    @property
    def vector_engine(self):
        return get_vector_engine()
    
    def embed(self, texts):
        return get_vector_engine().embed(texts)
    
    def embed_query(self, text):
        return get_vector_engine().embed_query(text)

# For backward compat: from research_os.foundation.vector import vector_engine
import sys
sys.modules[__name__].__class__ = type(
    'VectorModule', 
    (type(sys.modules[__name__]),), 
    {'vector_engine': property(lambda self: get_vector_engine())}
)
