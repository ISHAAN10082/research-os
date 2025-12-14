"""
Production-Safe Model Cache with Lifecycle Management

Prevents redundant model loading while ensuring safe cleanup and no memory leaks.
Thread-safe with usage tracking to prevent cleanup during active operations.

Usage:
    from research_os.foundation.model_cache import get_mpnet, get_minilm, get_phi35
    
    # Always returns cached instance, thread-safe
    embedder = get_mpnet()
    
    # Cleanup happens automatically on shutdown
"""

import threading
import time
import gc
import atexit
from functools import wraps
from typing import Tuple, Any, Callable, Optional
from contextlib import contextmanager
from loguru import logger

try:
    from fastembed import TextEmbedding
    FASTEMBED_AVAILABLE = True
except ImportError:
    logger.warning("fastembed not available")
    FASTEMBED_AVAILABLE = False
# Legacy fallback (kept for compatibility in signatures but unused in improved implementation)
SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from mlx_lm import load
    import torch
    MLX_AVAILABLE = True
except ImportError:
    logger.warning("mlx_lm not available")
    MLX_AVAILABLE = False


class ModelCache:
    """
    Thread-safe singleton model cache with safe lifecycle management.
    
    Features:
    - Prevents duplicate model loading
    - Thread-safe concurrent access
    - Usage tracking prevents cleanup during operations
    - Graceful shutdown with timeout
    - Automatic registration with atexit
    """
    
    _instance: Optional['ModelCache'] = None
    _init_lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        
        self._models = {}
        self._locks = {}  # Per-model locks
        self._usage_count = {}  # Track active users per model
        self._cleanup_lock = threading.Lock()
        self._initialized = True
        
        # Register cleanup
        atexit.register(self.cleanup)
        logger.info("✅ Model cache initialized with safe cleanup")
    
    def get_model(self, key: str, loader_fn: Callable, force_reload: bool = False):
        """
        Get cached model or load it.
        
        Args:
            key: Unique model identifier
            loader_fn: Function to load model if not cached
            force_reload: Force reload even if cached
            
        Returns:
            Cached or newly loaded model
        """
        with self._cleanup_lock:
            if force_reload or key not in self._models:
                logger.info(f"Loading model: {key}...")
                self._models[key] = loader_fn()
                self._locks[key] = threading.Lock()
                self._usage_count[key] = 0
                logger.info(f"✅ Model loaded: {key}")
            
            self._usage_count[key] += 1
        
        return self._models[key]
    
    @contextmanager
    def use_model(self, key: str, loader_fn: Callable):
        """
        Context manager for safe model usage with tracking.
        
        Example:
            with cache.use_model('mpnet', lambda: SentenceTransformer(...)) as model:
                embeddings = model.encode(texts)
        """
        # Get or load model
        model = self.get_model(key, loader_fn)
        
        # Lock for this specific model
        with self._locks[key]:
            try:
                yield model
            finally:
                with self._cleanup_lock:
                    self._usage_count[key] -= 1
    
    def unload_model(self, key: str):
        """
        Explicitly unload a specific model.
        
        Args:
            key: Model identifier to unload
        """
        with self._cleanup_lock:
            if key in self._models:
                # Wait for active operations
                max_wait = 10
                waited = 0
                while self._usage_count.get(key, 0) > 0:
                    if waited >= max_wait:
                        logger.warning(f"Forcing unload of {key} (active operations may fail)")
                        break
                    time.sleep(0.5)
                    waited += 0.5
                
                # Unload
                del self._models[key]
                if key in self._locks:
                    del self._locks[key]
                if key in self._usage_count:
                    del self._usage_count[key]
                
                # Force garbage collection
                gc.collect()
                if MLX_AVAILABLE and torch.backends.mps.is_available():
                    torch.mps.empty_cache()
                
                logger.info(f"🗑️  Unloaded model: {key}")
    
    def cleanup(self):
        """
        Safe cleanup of all models.
        
        Waits up to 30 seconds for active operations to complete
        before forcing cleanup. Called automatically on shutdown.
        """
        with self._cleanup_lock:
            # Wait for all operations to finish
            max_wait = 30  # seconds
            waited = 0
            
            while any(count > 0 for count in self._usage_count.values()):
                if waited >= max_wait:
                    active = {k: v for k, v in self._usage_count.items() if v > 0}
                    logger.warning(
                        f"Forcing cleanup (timeout) - active operations: {active}"
                    )
                    break
                
                time.sleep(0.5)
                waited += 0.5
            
            # Now safe to cleanup
            model_count = len(self._models)
            for key in list(self._models.keys()):
                del self._models[key]
            
            self._locks.clear()
            self._usage_count.clear()
            
            # Force garbage collection
            gc.collect()
            if MLX_AVAILABLE and torch.backends.mps.is_available():
                torch.mps.empty_cache()
            
            if model_count > 0:
                logger.info(f"🧹 Cleaned up {model_count} models")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            'loaded_models': list(self._models.keys()),
            'model_count': len(self._models),
            'usage_count': dict(self._usage_count)
        }


# Global cache instance
_cache = ModelCache()



class FastEmbedWrapper:
    """Wrapper to make FastEmbed behave like SentenceTransformer (output arrays)"""
    def __init__(self, model_name: str):
        from fastembed import TextEmbedding
        self.model = TextEmbedding(model_name=model_name)
    
    def encode(self, sentences, **kwargs):
        # FastEmbed returns generator, convert to list/array
        return list(self.model.embed(sentences, batch_size=kwargs.get('batch_size', 256)))


class FastRerankerWrapper:
    """Wrapper for FastEmbed CrossEncoder"""
    def __init__(self, model_name: str):
        from fastembed.rerank.cross_encoder import TextCrossEncoder 
        # Using BAAI/bge-reranker-base (Supported by FastEmbed)
        self.model = TextCrossEncoder(model_name=model_name)
    
    def compute_score(self, pairs, **kwargs):
        # FastEmbed rerank returns iterator of scores
        # Input pairs: [[q, d1], [q, d2]]
        if not pairs:
            return []
            
        query = pairs[0][0]
        docs = [p[1] for p in pairs]
        
        # rerank returns scores [float, float, ...] corresponding to docs order
        return list(self.model.rerank(query, docs))


def get_mpnet() -> Any:
    """
    Get singleton MPNet embedder instance (all-mpnet-base-v2).
    
    Returns:
        SentenceTransformer: Cached 768-dim embedder
    
    Note:
        First call loads model (~4s), subsequent calls are instant.
    """
    if not FASTEMBED_AVAILABLE:
        raise ImportError("fastembed is required for embeddings")
    
    # MPNet equivalent (BGE-Base is better, 768 dim)
    # Using BGE-Base-En-v1.5
    return _cache.get_model(
        'bge_base',
        lambda: FastEmbedWrapper("BAAI/bge-base-en-v1.5")
    )


def get_minilm() -> Any:
    """
    Get singleton MiniLM embedder instance (all-MiniLM-L6-v2).
    
    Returns:
        SentenceTransformer: Cached 384-dim embedder (fast)
    """
    if not FASTEMBED_AVAILABLE:
        raise ImportError("fastembed is required for MiniLM")
    
    # MiniLM equivalent (BGE-Small is better, 384 dim)
    return _cache.get_model(
        'bge_small',
        lambda: FastEmbedWrapper("BAAI/bge-small-en-v1.5")
    )


def get_phi35() -> Tuple[Any, Any]:
    """
    Get singleton Phi-3.5 LLM instance (4-bit quantized).
    
    Returns:
        Tuple[Model, Tokenizer]: Cached MLX model and tokenizer
    """
    if not MLX_AVAILABLE:
        raise ImportError("mlx_lm is required for Phi-3.5")
    
    return _cache.get_model(
        'phi35',
        lambda: load("mlx-community/phi-3.5-mini-instruct-4bit")
    )


def get_bge_m3() -> Any:
    """
    Get singleton BGE-M3 embedder instance (BAAI/bge-m3).
    
    Returns:
        SentenceTransformer: Cached 1024-dim multi-vector embedder
    """
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        raise ImportError("sentence-transformers is required for BGE-M3")
    
    return _cache.get_model(
        'bge_m3',
        lambda: SentenceTransformer('BAAI/bge-m3')
    )


def get_reranker() -> Any:
    """
    Get singleton Reranker instance (BGE-Reranker-Base).
    
    Returns:
        FastRerankerWrapper: Cached reranker
    """
    if not FASTEMBED_AVAILABLE:
        raise ImportError("fastembed is required for Reranker")
    
    return _cache.get_model(
        'reranker',
        lambda: FastRerankerWrapper("BAAI/bge-reranker-base")
    )


def cleanup_models():
    """
    Explicit cleanup function for app shutdown.
    
    Automatically called on exit, but can be called manually
    if needed (e.g., in FastAPI lifespan manager).
    """
    _cache.cleanup()


def get_cache_stats() -> dict:
    """
    Get cache statistics for monitoring.
    
    Returns:
        dict: Loaded models, usage counts
    """
    return _cache.get_stats()


if __name__ == "__main__":
    # Test the cache
    import time
    
    print("Testing model cache...")
    
    # First load (slow)
    print("\n1. First load (should take ~4s):")
    start = time.time()
    model1 = get_mpnet()
    first_load = time.time() - start
    print(f"   Loaded in {first_load:.2f}s")
    
    # Second load (should be instant from cache)
    print("\n2. Second load (should be instant):")
    start = time.time()
    model2 = get_mpnet()
    second_load = time.time() - start
    print(f"   Loaded in {second_load:.4f}s (from cache)")
    
    # Verify it's the same instance
    assert model1 is model2, "Should be same instance!"
    print("   ✅ Same instance confirmed")
    
    # Show cache stats
    print("\n3. Cache stats:")
    stats = get_cache_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test cleanup
    print("\n4. Testing cleanup...")
    cleanup_models()
    print("   ✅ Cleanup complete")
    
    print("\n✅ All tests passed")

