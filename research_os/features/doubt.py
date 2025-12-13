# Doubt Mode: Devil's Advocate Engine
"""
Challenges user claims with counter-evidence from the knowledge base.
Forces rigorous thinking by actively questioning assumptions.

Modes:
- GENTLE: Soft challenges, alternative perspectives
- MODERATE: Direct objections with sources
- HARSH: Aggressive challenge of all claims
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
from datetime import datetime
from loguru import logger

class DoubtStrength(Enum):
    GENTLE = "gentle"
    MODERATE = "moderate"
    HARSH = "harsh"

@dataclass
class Challenge:
    original_claim: str
    objection: str
    source: Optional[str] = None
    question: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class DoubtEngine:
    """Devil's advocate mode for research validation."""
    
    PROMPT_TEMPLATE = """The user claims: "{claim}"

Your job: Find weaknesses in this claim. Be a skeptical peer reviewer.
{strength_instruction}

Counter-evidence from papers:
{evidence}

Format your response:
⚠️ Challenge: [specific objection in 1-2 sentences]
📄 Source: [brief citation if available]
❓ Question: [one clarifying question to probe further]"""

    STRENGTH_INSTRUCTIONS = {
        DoubtStrength.GENTLE: "Be gentle but probing. Offer alternative perspectives.",
        DoubtStrength.MODERATE: "Be direct. Point out logical gaps or missing evidence.",
        DoubtStrength.HARSH: "Be aggressive. Assume the claim is wrong until proven otherwise."
    }
    
    def __init__(self, foundation, retriever=None):
        self.foundation = foundation
        self.retriever = retriever
        self.enabled = False
        self.strength = DoubtStrength.MODERATE
        self.history: List[Challenge] = []
    
    def toggle(self) -> bool:
        """Toggle doubt mode on/off."""
        self.enabled = not self.enabled
        logger.info(f"🤨 Doubt Mode: {'ON' if self.enabled else 'OFF'}")
        return self.enabled
    
    def set_strength(self, strength: DoubtStrength):
        """Set challenge intensity."""
        self.strength = strength
        logger.info(f"🤨 Doubt strength: {strength.value}")
    
    async def challenge(self, claim: str, context: str = "") -> Challenge:
        """Generate a challenge to a user's claim."""
        # Find counter-evidence
        evidence = ""
        if self.retriever:
            try:
                results = await self.retriever.search(f"evidence against: {claim}", top_k=2)
                evidence = "\n".join([r.chunk.text[:200] for r in results])
            except:
                evidence = "(No specific counter-evidence found in knowledge base)"
        else:
            evidence = "(Retriever not available)"
        
        prompt = self.PROMPT_TEMPLATE.format(
            claim=claim,
            strength_instruction=self.STRENGTH_INSTRUCTIONS[self.strength],
            evidence=evidence or "(No papers loaded)"
        )
        
        response = await self.foundation.generate_async(
            prompt=prompt,
            system="You are a skeptical peer reviewer. Challenge assumptions rigorously.",
            max_tokens=200
        )
        
        # Parse response
        challenge = Challenge(
            original_claim=claim,
            objection=self._extract_field(response, "⚠️ Challenge:"),
            source=self._extract_field(response, "📄 Source:"),
            question=self._extract_field(response, "❓ Question:")
        )
        
        self.history.append(challenge)
        return challenge
    
    def _extract_field(self, text: str, prefix: str) -> str:
        """Extract a field from formatted response."""
        for line in text.split('\n'):
            if prefix in line:
                return line.replace(prefix, "").strip()
        return ""
    
    async def respond(self, user_input: str, context: str = "") -> str:
        """Main entry point - either challenge or pass through."""
        if not self.enabled:
            return None  # Let normal response happen
        
        challenge = await self.challenge(user_input, context)
        
        result = f"""🤨 **DOUBT MODE ACTIVE**

⚠️ **Challenge:** {challenge.objection}

📄 **Source:** {challenge.source or 'General reasoning'}

❓ **Question:** {challenge.question or 'Can you provide evidence?'}

---
*Toggle off with `doubt off`*"""
        
        return result
