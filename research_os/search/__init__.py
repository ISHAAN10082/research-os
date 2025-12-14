# ResearchOS Search Layer
"""
SOTA hybrid retrieval and reranking pipeline.
Implements dense + sparse retrieval with cross-encoder reranking.
"""

from .retriever import get_retriever, HybridRetriever, Chunk, SearchResult
from .reranker import get_reranker, BGEReranker
from .colpali_indexer import ColPaliIndexer

__all__ = [
    "get_retriever", "HybridRetriever", "Chunk", "SearchResult",
    "get_reranker", "BGEReranker",
    "ColPaliIndexer",
]
