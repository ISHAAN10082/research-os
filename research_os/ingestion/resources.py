import arxiv
from loguru import logger
from typing import List, Dict

class ArxivClient:
    """Fetcher for external Arxiv papers."""
    
    def __init__(self):
        self.client = arxiv.Client()
        
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search Arxiv and return clean dicts."""
        logger.info(f"🔎 Searching Arxiv for: {query}")
        
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = []
        for r in self.client.results(search):
            results.append({
                "title": r.title,
                "authors": [a.name for a in r.authors],
                "summary": r.summary,
                "url": r.pdf_url,
                "published": r.published.strftime("%Y-%m-%d")
            })
            
        return results

resources_client = ArxivClient()
