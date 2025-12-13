"""
ResearchOS Recommender System.
Content-Based Filtering using TF-IDF on paper abstracts.
"""
import logging
from typing import List, Dict
import numpy as np

# Lazy load sklearn to fast-start server
_vectorizer = None
_paper_vectors = None
_paper_ids = []

logger = logging.getLogger(__name__)

class PaperRecommender:
    def __init__(self, papers_data: List[Dict]):
        """
        papers_data: List of dicts with {'id': ..., 'title': ..., 'abstract': ...}
        """
        self.papers = papers_data
        self._build_index()

    def _build_index(self):
        global _vectorizer, _paper_vectors, _paper_ids
        
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            
            logger.info(f"Building TF-IDF index for {len(self.papers)} papers...")
            texts = [f"{p['title']} {p.get('abstract', '')}" for p in self.papers]
            
            _vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            _paper_vectors = _vectorizer.fit_transform(texts)
            _paper_ids = [str(p.get('id', p.get('title'))) for p in self.papers] # Use title as ID if no ID
            
            logger.info("TF-IDF Index built.")
        except ImportError:
            logger.warning("Scikit-learn not found. Recommender disabled.")

    def recommend(self, paper_id: str, top_k: int = 5) -> List[Dict]:
        """Find similar papers."""
        if _paper_vectors is None: return []

        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            if paper_id not in _paper_ids:
                return []
                
            idx = _paper_ids.index(paper_id)
            query_vec = _paper_vectors[idx]
            
            # Compute similarity
            scores = cosine_similarity(query_vec, _paper_vectors).flatten()
            
            # Get top k indices
            top_indices = scores.argsort()[::-1][1:top_k+1] # Skip self
            
            results = []
            for i in top_indices:
                results.append({
                    "title": self.papers[i]['title'],
                    "score": float(scores[i])
                })
            return results
        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            return []

# Singleton placeholder - will be initialized with data from GraphEngine
recommender_service = None

def init_recommender(papers):
    global recommender_service
    recommender_service = PaperRecommender(papers)
