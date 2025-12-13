from dataclasses import dataclass, field
from typing import List, Optional, Dict
import time

@dataclass
class ResearchContext:
    """Holds the current focus of the user."""
    active_paper_id: Optional[str] = None
    active_paper_title: Optional[str] = None
    recent_queries: List[str] = field(default_factory=list)
    short_term_memory: List[Dict[str, str]] = field(default_factory=list) # [{"role": "user", "content": "..."}]

class SessionState:
    """Singleton to track global research session state."""
    
    def __init__(self):
        self.context = ResearchContext()
        self.start_time = time.time()
        self.stats = {
            "queries": 0,
            "cache_hits": 0,
            "papers_ingested": 0
        }
    
    def set_active_paper(self, paper_id: str, title: str):
        self.context.active_paper_id = paper_id
        self.context.active_paper_title = title
        
    def add_interaction(self, query: str, response: str):
        self.context.recent_queries.append(query)
        self.context.short_term_memory.append({"role": "user", "content": query})
        self.context.short_term_memory.append({"role": "assistant", "content": response})
        
        # Keep memory bounded
        if len(self.context.short_term_memory) > 10:
            self.context.short_term_memory = self.context.short_term_memory[-10:]
            
    def get_last_n_interactions(self, n: int = 3) -> str:
        """Format recent history for LLM context."""
        history = ""
        for msg in self.context.short_term_memory[-n*2:]:
            history += f"{msg['role'].upper()}: {msg['content']}\n"
        return history

# Global singleton
state = SessionState()
