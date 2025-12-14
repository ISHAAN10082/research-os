# Jarvis M4 Module
"""
ResearchOS 3.0 - Unified Research Intelligence System.
Provides claim extraction, multi-agent debate, causal graphs,
hypothesis generation, and spatial organization.
"""

from .services import (
    ClaimExtractorV2,
    DebateAgents,
    EvidenceBasedDebate,
    CausalGraph,
    UnifiedSchema,
    MemoryPalace,
    SceneGenerator,
    ResearchReporter,
)

__all__ = [
    "ClaimExtractorV2",
    "DebateAgents",
    "EvidenceBasedDebate",
    "CausalGraph",
    "UnifiedSchema",
    "MemoryPalace",
    "SceneGenerator",
    "ResearchReporter",
]
