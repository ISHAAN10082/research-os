import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Literal
from loguru import logger

class RouteDestination(Enum):
    LOCAL = "local_3b"
    CLOUD = "groq_70b"

@dataclass
class RouteDecision:
    destination: RouteDestination
    reason: str
    estimated_latency_ms: int

class HybridRouter:
    """
    Decides where to send a query based on complexity, current thermal state,
    and available latency budget.
    """
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
    def route(self, prompt: str, context_length: int = 0) -> RouteDecision:
        """
        Determine the optimal model for the query.
        """
        # 1. Check for Cloud capability
        if not self.groq_api_key:
            return RouteDecision(
                destination=RouteDestination.LOCAL,
                reason="No Groq API key found",
                estimated_latency_ms=1500
            )

        # 2. Heuristic Complexity Analysis
        # Long prompt or context implies need for stronger reasoning or larger window
        is_complex = len(prompt.split()) > 30 or context_length > 3000
        keywords = ["synthesize", "compare", "reason", "plan", "hypothesis", "fusion"]
        has_complex_intent = any(k in prompt.lower() for k in keywords)

        if is_complex or has_complex_intent:
            return RouteDecision(
                destination=RouteDestination.CLOUD,
                reason="Complex reasoning required (Tier 3)",
                estimated_latency_ms=800 # Groq is fast!
            )
            
        # 3. Default to Local (Tier 2)
        return RouteDecision(
            destination=RouteDestination.LOCAL,
            reason="Simple query, saving cloud budget",
            estimated_latency_ms=600
        )

router = HybridRouter()
