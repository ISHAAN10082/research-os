import asyncio
from loguru import logger
from research_os.foundation.core import foundation
from research_os.system.state import state
from research_os.system.governor import governor

class Anticipator:
    """
    Anticipates user questions based on context and pre-computes answers.
    Respects thermal limits by checking governor.
    """
    
    def __init__(self):
        self.cache = {} # Simple in-memory cache for now
        
    async def prefetch_for_paper(self, paper_title: str, context_text: str):
        """
        Called when a paper is ingested/opened.
        Runs cheap local model queries in background.
        """
        if governor.check_thermal_status() == "critical":
            logger.warning("🌡️ Thermal limit reached. Skipping anticipation.")
            return

        logger.info(f"🧠 Anticipating needs for: {paper_title}")
        
        # Standard questions
        questions = [
            f"Summarize '{paper_title}' in 3 sentences.",
            f"What are the key contributions of '{paper_title}'?",
            "What are the limitations mentioned?"
        ]
        
        for q in questions:
            # Check cache
            if q in self.cache:
                continue
                
            # Run sequential generation (Phi-3.5 is fast)
            try:
                # We use a smaller context window for efficiency
                short_context = context_text[:2000] 
                
                answer = await foundation.generate_async(
                    prompt=q,
                    context=short_context,
                    system="You are a helpful research assistant. Be concise.",
                    max_tokens=256 # Keep it short and fast
                )
                self.cache[q] = answer
                logger.debug(f"✅ Cached answer for: {q}")
                
            except Exception as e:
                logger.error(f"Anticipation failed for {q}: {e}")
                
    def get_cached_answer(self, query: str) -> str | None:
        return self.cache.get(query)

anticipator_engine = Anticipator()
