import unittest
from unittest.mock import MagicMock, patch
from tools.simulation_tool import calculate_race_delta
from agents.intent_agent import classify_intent 
from google import genai 
from dotenv import load_dotenv 

class TestAgentEvaluation(unittest.TestCase):
    """
    Tests for the F1 Strategist's core components: Custom Tool and Intent Classification.
    This fulfills the 'Agent Evaluation' capstone requirement.
    """

    # --- 1. Custom Tool Evaluation ---

    def test_tool_delta_positive_gain(self):
        """Test: Tool returns expected positive delta (Gain)."""
        delta = calculate_race_delta(
            strategy_name="overcut", 
            pit_lap=30, 
            tire_type="Medium"
        )
        self.assertAlmostEqual(delta, 0.60, places=2)
        
    def test_tool_delta_negative_loss(self):
        """Test: Tool returns expected negative delta (Loss)."""
        delta = calculate_race_delta(
            strategy_name="undercut", 
            pit_lap=5, 
            tire_type="Soft"
        )
        self.assertAlmostEqual(delta, -1.50, places=2)

    def test_tool_invalid_tire_raises_error(self):
        """Test: Tool handles invalid arguments gracefully (TypeError)."""
        with self.assertRaises(TypeError):
            # This should fail the internal check in the tool
            calculate_race_delta(
                strategy_name="standard", 
                pit_lap=20, 
                tire_type="INVALID_TIRE"
            )

    # --- 2. Intent Agent Evaluation (Mocking the LLM) ---

    # patch the client call inside the module where it's used
    @patch('agents.intent_agent.genai.Client')
    def test_intent_classification_delete(self, MockClient):
        """Test: Intent Agent correctly classifies the DELETE intent."""
        
        # Mock the LLM's response to ensure deterministic testing
        mock_response = MagicMock()
        mock_response.text = '{"intent": "DELETE_ENTRY", "argument": "TBD"}'
        MockClient.return_value.models.generate_content.return_value = mock_response
        
        result = classify_intent(MockClient.return_value, "delete 5")
        
        self.assertEqual(result['intent'], 'DELETE_ENTRY')
        
    @patch('agents.intent_agent.genai.Client')
    def test_intent_classification_history(self, MockClient):
        """Test: Intent Agent correctly classifies the HISTORY intent (REVIEW_HISTORY)."""
        
        mock_response = MagicMock()
        mock_response.text = '{"intent": "REVIEW_HISTORY", "argument": null}'
        MockClient.return_value.models.generate_content.return_value = mock_response
        
        result = classify_intent(MockClient.return_value, "history")
        
        self.assertEqual(result['intent'], 'REVIEW_HISTORY')
        
    @patch('agents.intent_agent.genai.Client')
    def test_intent_classification_optimization(self, MockClient):
        """Test: Intent Agent correctly classifies the OPTIMIZE_STRATEGY intent."""
        
        mock_response = MagicMock()
        mock_response.text = '{"intent": "OPTIMIZE_STRATEGY", "argument": null}'
        MockClient.return_value.models.generate_content.return_value = mock_response
        
        result = classify_intent(MockClient.return_value, "run optimization")
        
        self.assertEqual(result['intent'], 'OPTIMIZE_STRATEGY')

# --- RUNNER BLOCK ---
if __name__ == '__main__':
    # Load environment variables just in case the Intent Agent needs them to initialize
    load_dotenv() 
    unittest.main()