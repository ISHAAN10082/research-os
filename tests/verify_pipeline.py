import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, patch

# Add parent path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock MLX/Kuzu modules BEFORE importing services
# This allows us to run logic tests without heavy loading
sys.modules["mlx.core"] = MagicMock()
sys.modules["mlx_lm"] = MagicMock()
sys.modules["kuzu"] = MagicMock()
sys.modules["outlines"] = MagicMock()

# Setup Outlines Mock
mock_claims = MagicMock()
mock_claims.claims = [
    MagicMock(dict=lambda: {"text": "A", "confidence": 0.9, "claim_type": "finding", "section": "1", "evidence_snippets": []}),
    MagicMock(dict=lambda: {"text": "B", "confidence": 0.8, "claim_type": "method", "section": "2", "evidence_snippets": []})
]
sys.modules["outlines"].generate.json.return_value = MagicMock(return_value=mock_claims)

# Now import Pipeline
from jarvis_m4.main import UnifiedPipeline

class TestUnifiedPipeline(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        print("\n🚀 Starting Pipeline Stress Test...")
        # Patch init to avoid real heavyweight service loads
        pass

    async def test_full_pipeline_flow(self):
        """
        Simulate processing a paper from ingestion to reporting.
        """
        print("Paper 1: Normal Flow Simulation...")
        
        # We patch the components insided unified pipeline
        with patch("jarvis_m4.services.schema.UnifiedSchema") as MockSchema, \
             patch("jarvis_m4.services.extract.ClaimExtractor") as MockExtract, \
             patch("jarvis_m4.services.debate.DebateAgents") as MockDebate, \
             patch("jarvis_m4.services.causal_graph.CausalGraph") as MockGraph, \
             patch("jarvis_m4.services.palace.MemoryPalace") as MockPalace, \
             patch("jarvis_m4.services.scene.SceneGenerator") as MockScene, \
             patch("jarvis_m4.services.reporter.ResearchReporter") as MockReporter:
            
            # Setup returns
            pipeline = UnifiedPipeline()
            
            # Mock Extraction
            MockExtract.return_value.extract_from_paper.return_value = mock_claims.claims
            
            # Mock Graph/Debate (async)
            MockGraph.return_value.add_claim_and_debate = MagicMock() # Mock specific asyncio method if needed
            
            # Mock Palace
            MockPalace.return_value.generate_palace.return_value = {"wings": {}}
            
            # Mock Reporter
            MockReporter.return_value.generate_paper_report.return_value = "# Report"
            
            # EXECUTE
            success = await pipeline.process_paper("data/test_paper.txt", "p_101")
            
            # ASSERTIONS covering all phases
            self.assertTrue(success, "Pipeline should return True on success")
            
            MockExtract.return_value.extract_from_paper.assert_called()
            print("✅ Ingestion & Extraction: OK")
            
            # Verify Graph Update called for each claim
            self.assertEqual(MockGraph.return_value.add_claim_and_debate.call_count, 2)
            print("✅ Serial Debate & Graph Update: OK")
            
            MockPalace.return_value.generate_palace.assert_called()
            print("✅ Spatial Palace Regeneration: OK")
            
            MockReporter.return_value.save_to_vault.assert_called()
            print("✅ Obsidian Report Sync: OK")

    async def test_edge_case_empty_extraction(self):
        """
        Scenario: Paper has text but no claims found. Pipeline should not crash.
        """
        print("Paper 2: Edge Case (Empty Extraction)...")
        
        with patch("jarvis_m4.services.schema.UnifiedSchema"), \
             patch("jarvis_m4.services.extract.ClaimExtractor") as MockExtract, \
             patch("jarvis_m4.services.debate.DebateAgents"), \
             patch("jarvis_m4.services.causal_graph.CausalGraph"), \
             patch("jarvis_m4.services.palace.MemoryPalace"), \
             patch("jarvis_m4.services.scene.SceneGenerator"), \
             patch("jarvis_m4.services.reporter.ResearchReporter"):
            
            pipeline = UnifiedPipeline()
            MockExtract.return_value.extract_from_paper.return_value = [] # Empty!
            
            success = await pipeline.process_paper("data/test_paper.txt", "p_empty")
            
            self.assertTrue(success)
            print("✅ Handled Empty Extraction Gracefully (No crash).")

if __name__ == "__main__":
    unittest.main()
