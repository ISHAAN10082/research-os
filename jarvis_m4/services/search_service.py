from typing import List, Dict
import arxiv
from semanticscholar import SemanticScholar
import logging

logger = logging.getLogger(__name__)

class SearchService:
    """Real search service using ArXiv and Semantic Scholar"""
    
    def __init__(self):
        self.sch = SemanticScholar()
        self.arxiv_client = arxiv.Client()
    
    def search_arxiv(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search ArXiv and return standard format"""
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            results = []
            for r in self.arxiv_client.results(search):
                results.append({
                    "id": r.entry_id.split('/')[-1],
                    "title": r.title,
                    "authors": [a.name for a in r.authors],
                    "year": r.published.year,
                    "abstract": r.summary.replace("\n", " "),
                    "url": r.pdf_url,
                    "source": "arxiv"
                })
            return results
        except Exception as e:
            logger.error(f"ArXiv search failed: {e}")
            return []

    def search_semantic_scholar(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search Semantic Scholar"""
        try:
            results = self.sch.search_paper(query, limit=max_results)
            papers = []
            for r in results:
                papers.append({
                    "id": r.paperId,
                    "title": r.title,
                    "authors": [a.name for a in r.authors] if r.authors else [],
                    "year": r.year,
                    "abstract": r.abstract,
                    "url": r.url,
                    "source": "semantic_scholar"
                })
            return papers
        except Exception as e:
            logger.error(f"S2 search failed: {e}")
            return []
