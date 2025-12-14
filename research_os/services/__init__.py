# ResearchOS Services Layer
"""
Utility services for document processing and recommendations.
"""

from .pdf_extraction import GrobidClient, grobid
from .entity_extraction import EntityExtractor
from .recommender import RecommenderService

__all__ = [
    "GrobidClient", "grobid",
    "EntityExtractor",
    "RecommenderService",
]
