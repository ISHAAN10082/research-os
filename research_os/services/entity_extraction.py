"""
ResearchOS Entity Extraction Service.
Uses SpaCy for NER and an optional DBpedia lookup for Entity Linking.
"""
import spacy
import asyncio
import logging
from typing import List, Dict, Optional, Any
import httpx

logger = logging.getLogger(__name__)

class EntityExtractor:
    def __init__(self, model: str = "en_core_web_sm"):
        try:
            self.nlp = spacy.load(model)
            logger.info(f"Loaded SpaCy model: {model}")
        except Exception:
            # Fallback if model not found
            logger.warning(f"Model {model} not found. Attempting download...")
            from spacy.cli import download
            download(model)
            self.nlp = spacy.load(model)

        self.dbpedia_client = httpx.AsyncClient(
            base_url='http://dbpedia.org/sparql',
            timeout=5.0 
        )

    async def extract(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text concurrently."""
        loop = asyncio.get_event_loop()
        # spaCy processing is CPU bound
        doc = await loop.run_in_executor(None, self.nlp, text)
        
        entities = []
        seen = set()
        
        for ent in doc.ents:
            if ent.text in seen: continue
            seen.add(ent.text)
            
            entity = {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            }
            
            # Simple heuristic linking for critical types
            if ent.label_ in ['PERSON', 'ORG', 'PRODUCT']:
               uri = await self._link_dbpedia(ent.text, ent.label_)
               if uri:
                   entity['uri'] = uri
            
            entities.append(entity)
            
        return entities

    async def _link_dbpedia(self, text: str, label: str) -> Optional[str]:
        """Simple SPARQL check."""
        try:
            query = f'SELECT ?r WHERE {{ ?r rdfs:label "{text}"@en }} LIMIT 1'
            resp = await self.dbpedia_client.get("", params={"query": query, "format": "json"})
            data = resp.json()
            if data['results']['bindings']:
                return data['results']['bindings'][0]['r']['value']
        except Exception:
            return None
        return None

# Global Singleton
# Lazy load to avoid startup penalty if not used immediately
_extractor = None

def get_extractor():
    global _extractor
    if not _extractor:
        _extractor = EntityExtractor()
    return _extractor
