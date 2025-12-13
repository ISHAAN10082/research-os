"""
ResearchOS "Intelligence" Module.
Aggregates low-level telemetry into high-level insights and predictions.
"""
from typing import Dict, List, Any
from research_os.system.workspace_analytics import analytics

class ResearchIntelligence:
    def __init__(self):
        pass

    def predict_next_action(self, current_workspace: str) -> str:
        """Heuristic prediction of what the user should do next."""
        # Simple rule-based system for MVP
        if current_workspace == "synthesis":
            # If high crystallization rate, suggest reading more
            # If low, suggest finalizing threads
            rate = analytics.get_crystallization_rate()
            if rate < 0.3:
                return "📝 Many active threads. Consider crystalizing insights into a document."
            else:
                return "📚 Synthesis pipeline clear. Gather more source material in Reading Mode."
        
        elif current_workspace == "reading":
            # If reading speed is fast, suggest deep dive in graph
            # If slow, suggest spawning explanation thread
            return "🕸️ Explore related citations in Graph Mode."

        elif current_workspace == "graph":
            return "🧠 Return to Synthesis to connect discovered clusters."
        
        return "Keep exploring."

    def generate_session_summary(self) -> Dict[str, Any]:
        """High-level summary for the dashboard."""
        return {
            "crystallization_rate": analytics.get_crystallization_rate(),
            "reading_stats": analytics.get_reading_velocity(),
            "recommendation": self.predict_next_action("synthesis") 
        }

intelligence = ResearchIntelligence()
