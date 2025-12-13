# Living Bibliography: Auto-extracted citations
"""
Extracts citations from AI responses, maintains a live bibliography,
and exports to BibTeX format.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Citation:
    title: str
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    relevance_score: float = 0.0
    source_query: str = ""

class Bibliography:
    """Live bibliography manager with BibTeX export."""
    
    def __init__(self):
        self.citations: List[Citation] = []
    
    def extract_from_response(self, response: str, query: str) -> List[Citation]:
        """Extract paper references from an AI response."""
        # Simple pattern: "Author et al. (YYYY)" or similar
        pattern = r'([A-Z][a-z]+(?:\s+et\s+al\.)?)\s*\((\d{4})\)'
        matches = re.findall(pattern, response)
        
        new_citations = []
        for author, year in matches:
            cite = Citation(
                title=f"[Extracted] {author} {year}",
                authors=[author],
                year=int(year),
                source_query=query
            )
            if cite not in self.citations:
                self.citations.append(cite)
                new_citations.append(cite)
        
        return new_citations
    
    def add(self, citation: Citation):
        """Manually add a citation."""
        self.citations.append(citation)
    
    def export_bibtex(self) -> str:
        """Export all citations as BibTeX."""
        entries = []
        for i, cite in enumerate(self.citations):
            key = f"cite{i+1}"
            author_str = " and ".join(cite.authors) if cite.authors else "Unknown"
            entry = f"""@article{{{key},
    title = {{{cite.title}}},
    author = {{{author_str}}},
    year = {{{cite.year or "n.d."}}}
}}"""
            entries.append(entry)
        
        return "\n\n".join(entries)
    
    def clear(self):
        self.citations = []
