# Paper Whispers: Ambient Paper Discovery
"""
Background task that monitors Semantic Scholar for new relevant papers
and generates AI "relevance hooks" before showing notifications.

SOTA Features:
- Semantic Scholar API integration
- AI-generated relevance hooks
- Background async monitoring
- Rate-limit aware
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Optional, Set
from datetime import datetime
from loguru import logger

@dataclass
class Paper:
    paper_id: str
    title: str
    abstract: str
    authors: List[str]
    year: int
    url: str
    citation_count: int = 0

@dataclass
class Whisper:
    paper: Paper
    hook: str  # AI-generated relevance sentence
    topic: str  # Which topic triggered this
    timestamp: datetime = field(default_factory=datetime.now)
    dismissed: bool = False

class PaperWhisper:
    """Ambient paper discovery with AI-generated relevance hooks."""
    
    def __init__(self, foundation):
        self.foundation = foundation
        self.topics: List[str] = []
        self.whispers: List[Whisper] = []
        self.seen_ids: Set[str] = set()
        self._running = False
        self._sch = None  # Lazy-loaded Semantic Scholar client
    
    @property
    def sch(self):
        """Lazy-load Semantic Scholar client."""
        if self._sch is None:
            from semanticscholar import SemanticScholar
            self._sch = SemanticScholar()
        return self._sch
    
    def set_topics(self, topics: List[str]):
        """Set research topics to monitor."""
        self.topics = topics
        logger.info(f"🔮 Whisper topics set: {topics}")
    
    async def generate_hook(self, paper: Paper, topic: str) -> str:
        """Generate a one-sentence relevance hook."""
        prompt = f"""You're researching "{topic}". In ONE sentence (max 20 words), explain why this paper matters:

Title: {paper.title}
Abstract: {paper.abstract[:400]}"""
        
        try:
            hook = await self.foundation.generate_async(
                prompt=prompt,
                system="You are a research curator. Be concise, insightful, actionable.",
                max_tokens=50
            )
            return hook.strip()
        except Exception as e:
            logger.error(f"Hook generation failed: {e}")
            return f"New paper on {topic}: {paper.title[:50]}..."
    
    async def search_papers(self, topic: str, limit: int = 5) -> List[Paper]:
        """Search Semantic Scholar for recent papers."""
        try:
            def _search():
                results = self.sch.search_paper(
                    topic,
                    year=f"{datetime.now().year - 1}-{datetime.now().year}",
                    limit=limit,
                    fields=["paperId", "title", "abstract", "authors", "year", "url", "citationCount"]
                )
                return results
            
            # Run blocking API call in thread
            results = await asyncio.to_thread(_search)
            
            papers = []
            for r in results:
                if r.paperId and r.paperId not in self.seen_ids:
                    papers.append(Paper(
                        paper_id=r.paperId,
                        title=r.title or "Untitled",
                        abstract=r.abstract or "",
                        authors=[a.name for a in (r.authors or [])[:3]],
                        year=r.year or datetime.now().year,
                        url=r.url or f"https://www.semanticscholar.org/paper/{r.paperId}",
                        citation_count=r.citationCount or 0
                    ))
            return papers
        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            return []
    
    async def check_new_papers(self) -> List[Whisper]:
        """Check all topics for new relevant papers."""
        new_whispers = []
        
        for topic in self.topics:
            papers = await self.search_papers(topic, limit=3)
            
            for paper in papers:
                if paper.paper_id not in self.seen_ids:
                    self.seen_ids.add(paper.paper_id)
                    
                    hook = await self.generate_hook(paper, topic)
                    whisper = Whisper(paper=paper, hook=hook, topic=topic)
                    new_whispers.append(whisper)
                    self.whispers.append(whisper)
                    
                    logger.info(f"🔮 New whisper: {paper.title[:40]}...")
        
        return new_whispers
    
    async def start_monitoring(self, interval_seconds: int = 3600):
        """Start background paper monitoring loop."""
        self._running = True
        logger.info(f"🔮 Paper Whispers active (interval: {interval_seconds}s)")
        
        while self._running:
            try:
                if self.topics:
                    await self.check_new_papers()
            except Exception as e:
                logger.error(f"Whisper monitoring error: {e}")
            
            await asyncio.sleep(interval_seconds)
    
    def stop(self):
        """Stop monitoring."""
        self._running = False
        logger.info("🔮 Paper Whispers stopped")
    
    def get_recent(self, count: int = 5) -> List[Whisper]:
        """Get most recent unread whispers."""
        unread = [w for w in self.whispers if not w.dismissed]
        return unread[-count:]
    
    def dismiss(self, paper_id: str):
        """Mark a whisper as dismissed."""
        for w in self.whispers:
            if w.paper.paper_id == paper_id:
                w.dismissed = True
                break
