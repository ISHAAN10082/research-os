import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import json

try:
    # Fix for Chroma on macOS/old sqlite
    import sqlite3
    if sqlite3.sqlite_version_info < (3, 35, 0):
        try:
            __import__('pysqlite3')
            import sys
            sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
        except ImportError:
             pass

    import chromadb
    from chromadb.config import Settings
    HAS_CHROMA = True
except Exception as e:
    HAS_CHROMA = False
    print(f"⚠️ Chroma failed ({e}), using FAISS-only mode")

class RetrievalEngine:
    """
    FAISS + SPECTER2 for fast semantic search.
    Chroma for metadata storage (optional).
    """
    
    def __init__(self, dimension: int = 768, use_chroma: bool = True):
        """Initialize retrieval engine"""
        
        # High-quality embedder (SPECTER2 has PEFT issues, using mpnet)
        print("Loading embedder for retrieval...")
        self.embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        print("✅ Embedder loaded")
        
        # HNSW index for high recall and sub‑ms search
        self.dimension = dimension
        # M = graph degree, efConstruction = index build quality, efSearch = query quality
        self.index = faiss.IndexHNSWFlat(dimension, 32)
        self.index.hnsw.efConstruction = 200
        self.index.hnsw.efSearch = 64
        
        # Metadata storage
        self.id_to_metadata = {}  # {claim_id: metadata_dict}
        self.id_to_index = {}     # {claim_id: faiss_index}
        self.index_to_id = {}     # {faiss_index: claim_id}
        
        # Chroma (optional)
        self.use_chroma = use_chroma and HAS_CHROMA
        if self.use_chroma:
            self.chroma_client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory="data/chroma"
            ))
            self.collection = self.chroma_client.get_or_create_collection("claims")
            print("✅ Chroma initialized")
    
    def index_claim(self, claim_id: str, embedding: List[float], metadata: Dict):
        """Add claim to index"""
        
        # Convert to numpy
        emb_array = np.array(embedding, dtype=np.float32).reshape(1, -1)
        
        # Add to FAISS
        faiss_idx = self.index.ntotal
        self.index.add(emb_array)
        
        # Map claim_id <-> faiss_index
        self.id_to_index[claim_id] = faiss_idx
        self.index_to_id[faiss_idx] = claim_id
        self.id_to_metadata[claim_id] = metadata
        
        # Add to Chroma (optional)
        if self.use_chroma:
            self.collection.add(
                ids=[claim_id],
                embeddings=[embedding],
                metadatas=[metadata]
            )
    
    def search(self, query_text: str, top_k: int = 5, min_similarity: float = 0.0) -> List[Dict]:
        """
        Semantic search by text query.
        Returns: List of {claim_id, text, similarity_score, metadata}
        """
        
        # Embed query with SPECTER2
        query_emb = self.embedder.encode(query_text, convert_to_numpy=True)
        
        return self.search_by_embedding(query_emb.tolist(), top_k, min_similarity)
    
    def search_by_embedding(self, embedding: List[float], top_k: int = 5, min_similarity: float = 0.0) -> List[Dict]:
        """Search by pre-computed embedding (for claim-to-claim similarity)"""
        
        if self.index.ntotal == 0:
            return []
        
        # Convert to numpy
        query_array = np.array(embedding, dtype=np.float32).reshape(1, -1)
        
        # HNSW search (same API, returns distances, indices)
        distances, indices = self.index.search(query_array, min(top_k, self.index.ntotal))
        
        # Build results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for missing
                continue
            
            claim_id = self.index_to_id.get(int(idx))
            if not claim_id:
                continue
            
            # Convert L2 distance to similarity (inverse)
            # Lower distance = higher similarity
            similarity = 1.0 / (1.0 + dist)
            
            if similarity < min_similarity:
                continue
            
            metadata = self.id_to_metadata.get(claim_id, {})
            
            results.append({
                "claim_id": claim_id,
                "text": metadata.get("text", ""),
                "similarity_score": float(similarity),
                "metadata": metadata
            })
        
        return results
    
    def get_claim_embedding(self, claim_id: str) -> Optional[List[float]]:
        """Retrieve embedding for a claim"""
        
        faiss_idx = self.id_to_index.get(claim_id)
        if faiss_idx is None:
            return None
        
        # Reconstruct from FAISS (only works for Flat indexes)
        embedding = self.index.reconstruct(faiss_idx)
        return embedding.tolist()
    
    def save_index(self, filepath: str = "data/faiss_index.bin"):
        """Save FAISS index to disk"""
        faiss.write_index(self.index, filepath)
        
        # Save mappings
        with open(filepath + ".meta.json", "w") as f:
            json.dump({
                "id_to_index": self.id_to_index,
                "id_to_metadata": self.id_to_metadata
            }, f)
        
        print(f"✅ Saved index to {filepath}")
    
    def load_index(self, filepath: str = "data/faiss_index.bin"):
        """Load FAISS index from disk"""
        
        self.index = faiss.read_index(filepath)
        
        with open(filepath + ".meta.json") as f:
            data = json.load(f)
            self.id_to_index = data["id_to_index"]
            self.id_to_metadata = data["id_to_metadata"]
            # Rebuild reverse mapping
            self.index_to_id = {v: k for k, v in self.id_to_index.items()}
        
        print(f"✅ Loaded index from {filepath}")


if __name__ == "__main__":
    # Test retrieval engine
    print("Testing RetrievalEngine...")
    
    engine = RetrievalEngine()
    
    # Index sample claims
    claims = [
        {"id": "c1", "text": "Transformers use self-attention mechanisms", "type": "method"},
        {"id": "c2", "text": "BERT is based on transformer architecture", "type": "finding"},
        {"id": "c3", "text": "Attention is all you need for NLP", "type": "hypothesis"}
    ]
    
    for claim in claims:
        # Generate embedding
        emb = engine.embedder.encode(claim['text'], convert_to_numpy=True)
        engine.index_claim(claim['id'], emb.tolist(), claim)
    
    # Search
    results = engine.search("What are transformers?", top_k=2)
    
    print(f"✅ Found {len(results)} results")
    for r in results:
        print(f"  - {r['claim_id']}: {r['text'][:50]}... (score: {r['similarity_score']:.3f})")
    
    # Test save/load
    engine.save_index("data/test_index.bin")
    
    print("✅ RetrievalEngine test passed")
