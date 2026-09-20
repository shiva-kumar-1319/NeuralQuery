"""
Unit tests for LLM provider abstraction and NeuralQuery LoRA engine.
"""

import os
import unittest

os.environ['TESTING'] = 'True'

from config import Config
from llm_providers import get_llm_provider, GeminiProvider, NeuralQueryProvider


class TestLLMProviders(unittest.TestCase):
    def test_gemini_provider_selection(self):
        Config.MODEL_PROVIDER = 'gemini'
        provider = get_llm_provider()
        self.assertIsInstance(provider, GeminiProvider)

    def test_neuralquery_provider_selection(self):
        Config.MODEL_PROVIDER = 'neuralquery'
        provider = get_llm_provider()
        self.assertIsInstance(provider, NeuralQueryProvider)
        # Verify model is NOT loaded eagerly at factory call
        self.assertFalse(provider._is_loaded)

    def test_prompt_formatting_and_constraints(self):
        provider = NeuralQueryProvider()
        sources = [
            {
                "title": "Quantum Sensor Tech",
                "url": "https://example.com/quantum",
                "snippet": "Quantum sensors improve magnetometry.",
                "content": "Quantum sensors achieve sub-picotesla sensitivity."
            }
        ]
        prompt = provider._build_prompt("What is the sensitivity?", sources)
        self.assertIn("Research Question:", prompt)
        self.assertIn("Retrieved Evidence:", prompt)
        self.assertIn("[Source 1]: Quantum Sensor Tech", prompt)
        self.assertIn("https://example.com/quantum", prompt)
        self.assertIn("CRITICAL OPERATIONAL CONSTRAINTS", prompt)

    def test_graceful_error_handling_when_weights_missing(self):
        Config.MODEL_PROVIDER = 'neuralquery'
        Config.NEURALQUERY_FALLBACK_TO_GEMINI = False
        provider = NeuralQueryProvider()
        # Should return a helpful diagnostic string rather than crashing
        res = provider.generate("Test query", [{"title": "T", "url": "http://t.com", "snippet": "S"}])
        self.assertTrue(len(res) > 0)


if __name__ == "__main__":
    unittest.main()
