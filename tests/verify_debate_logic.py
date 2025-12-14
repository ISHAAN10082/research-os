import sys
import unittest
from unittest.mock import MagicMock

# Mock mlx_lm before importing debate service
sys.modules["mlx.core"] = MagicMock()
sys.modules["mlx_lm"] = MagicMock()

# Mock load and generate
mock_load = MagicMock(return_value=(MagicMock(), MagicMock()))
mock_generate = MagicMock(return_value= \
    '{"verdict": "refutes", "confidence": 85, "explanation": "Direct contradiction found in methodology."}')

sys.modules["mlx_lm"].load = mock_load
sys.modules["mlx_lm"].generate = mock_generate

# Now import the service
# We need to add the parent dir to path since we are running as script
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jarvis_m4.services.debate import DebateAgents

class TestDebateLogic(unittest.TestCase):
    def test_debate_flow(self):
        print("Testing Debate Logic Flow (Mocked Model)...")
        debater = DebateAgents(model_path="test_model")
        
        # Override _generate_response to return context-aware mocks
        debater._generate_response = MagicMock(side_effect=[
            "Skeptic analysis: Method is weak.",     # Skeptic
            "Connector analysis: Similar to 1980s.", # Connector
            '{"verdict": "refutes", "confidence": 85, "explanation": "Test."}' # Synthesizer
        ])
        
        result = debater.run_debate("Sky is blue", "Sky is green")
        
        self.assertEqual(result['verdict'], 'refutes')
        self.assertEqual(len(result['log']), 3) # Skeptic, Connector, Synthesizer
        print("✅ Debate Flow Verified.")

if __name__ == '__main__':
    unittest.main()
