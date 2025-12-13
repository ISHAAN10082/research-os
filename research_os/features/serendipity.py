# Serendipity Walk: Random Citation Graph Exploration
"""
Random walks through your knowledge graph for unexpected discoveries.
Like StumbleUpon for research papers.

Walk Types:
- CITATION: Follow citation paths
- AUTHOR: Papers by same authors
- TOPIC: Semantically similar papers
"""

import random
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
from datetime import datetime
from loguru import logger

class WalkType(Enum):
    CITATION = "citation"
    AUTHOR = "author"
    TOPIC = "topic"
    RANDOM = "random"

@dataclass
class WalkStep:
    paper_id: str
    title: str
    connection_story: str  # AI-generated narrative
    walk_type: WalkType

@dataclass
class SerendipityWalk:
    steps: List[WalkStep]
    start_paper: str
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_narrative(self) -> str:
        """Convert walk to readable narrative."""
        lines = [f"🎲 **Serendipity Walk** (started from: {self.start_paper})\n"]
        for i, step in enumerate(self.steps):
            lines.append(f"{i+1}. **{step.title}**")
            lines.append(f"   ↳ _{step.connection_story}_\n")
        return "\n".join(lines)

class SerendipityEngine:
    """Random walk engine for unexpected paper discovery."""
    
    def __init__(self, foundation, graph=None):
        self.foundation = foundation
        self.graph = graph
        self._sch = None
    
    @property
    def sch(self):
        if self._sch is None:
            from semanticscholar import SemanticScholar
            self._sch = SemanticScholar()
        return self._sch
    
    async def generate_connection(self, from_title: str, to_title: str) -> str:
        """Generate narrative connection between papers."""
        prompt = f"""In ONE sentence (max 15 words), explain the intellectual connection:
From: {from_title}
To: {to_title}"""
        
        try:
            return await self.foundation.generate_async(
                prompt=prompt,
                system="You are a research storyteller. Be poetic but accurate.",
                max_tokens=40
            )
        except:
            return "leads to"
    
    async def walk_from_paper(self, paper_id: str, steps: int = 5) -> SerendipityWalk:
        """Perform random walk starting from a paper."""
        import asyncio
        
        walk_steps = []
        current_id = paper_id
        start_title = "Unknown"
        
        try:
            def _get_paper(pid):
                return self.sch.get_paper(
                    pid, 
                    fields=["title", "citations", "references"]
                )
            
            for i in range(steps):
                paper = await asyncio.to_thread(_get_paper, current_id)
                
                if i == 0:
                    start_title = paper.title or "Unknown"
                
                # Combine citations and references
                neighbors = []
                if paper.citations:
                    neighbors.extend([c.paperId for c in paper.citations[:10] if c.paperId])
                if paper.references:
                    neighbors.extend([r.paperId for r in paper.references[:10] if r.paperId])
                
                if not neighbors:
                    break
                
                # Random jump
                next_id = random.choice(neighbors)
                next_paper = await asyncio.to_thread(_get_paper, next_id)
                
                if not next_paper or not next_paper.title:
                    continue
                
                # Generate connection story
                story = await self.generate_connection(
                    paper.title or "Previous",
                    next_paper.title
                )
                
                walk_steps.append(WalkStep(
                    paper_id=next_id,
                    title=next_paper.title,
                    connection_story=story.strip(),
                    walk_type=WalkType.CITATION
                ))
                
                current_id = next_id
                
        except Exception as e:
            logger.error(f"Serendipity walk failed: {e}")
        
        return SerendipityWalk(
            steps=walk_steps,
            start_paper=start_title
        )
    
    async def daily_random(self, topics: List[str]) -> Optional[WalkStep]:
        """Get a random paper for daily discovery."""
        if not topics:
            return None
        
        topic = random.choice(topics)
        
        try:
            def _search():
                return self.sch.search_paper(topic, limit=10)
            
            import asyncio
            papers = await asyncio.to_thread(_search)
            
            if papers:
                paper = random.choice(list(papers))
                return WalkStep(
                    paper_id=paper.paperId,
                    title=paper.title,
                    connection_story=f"Random discovery from your interest in '{topic}'",
                    walk_type=WalkType.RANDOM
                )
        except Exception as e:
            logger.error(f"Daily random failed: {e}")
        
        return None
