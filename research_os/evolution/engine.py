from research_os.config import settings
from loguru import logger
from research_os.foundation.core import foundation

class EvolutionEngine:
    """
    Layer 4: Online Evolution.
    Adapts the system to your research style over time.
    Mechanism: Dynamic System Prompt Optimization (Simulated Online Distillation).
    """
    
    def __init__(self):
        self.base_persona = "You are ResearchOS, a hyper-intelligent research assistant."
        self.learned_context = [] # Short-term memory of 'wins'

    def evolve(self, interaction_log: dict):
        """
        Learn from a successful interaction.
        If user accepted a hypothesis, allow that to bias future generation.
        """
        topic = interaction_log.get("topic")
        if topic:
            logger.info(f"Evolving weights toward topic: {topic}")
            self.learned_context.append(f"User is interested in {topic}.")
            # Keep context window small
            if len(self.learned_context) > 5:
                self.learned_context.pop(0)

    def get_system_prompt(self) -> str:
        """
        Construct the evolved system prompt.
        """
        adaptation = " ".join(self.learned_context)
        return f"{self.base_persona} Current Focus: {adaptation}"

evolution_engine = EvolutionEngine()
