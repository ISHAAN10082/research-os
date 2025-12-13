# ResearchOS Novel Features Module
"""
Modular research features that extend the core intelligence layer.
Each feature is a self-contained plugin with a consistent interface.

Features:
- whispers: Ambient paper discovery (Semantic Scholar)
- bibliography: Live citation management
- crystallizer: Conversation → structured output
- doubt: Devil's advocate mode
- serendipity: Random citation walks
- voice: Push-to-talk ideation
"""

from .whispers import PaperWhisper, Whisper
from .bibliography import Bibliography, Citation
from .crystallizer import Crystallizer
from .doubt import DoubtEngine, DoubtStrength
from .serendipity import SerendipityEngine, SerendipityWalk
from .voice import VoiceLoop, VoiceNote

__all__ = [
    "PaperWhisper", "Whisper",
    "Bibliography", "Citation",
    "Crystallizer",
    "DoubtEngine", "DoubtStrength",
    "SerendipityEngine", "SerendipityWalk",
    "VoiceLoop", "VoiceNote",
]
