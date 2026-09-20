"""
Unit tests for configuration management.
"""

import os
import unittest

os.environ['TESTING'] = 'True'
os.environ['JWT_SECRET'] = 'test-secret'

from config import Config


class TestConfig(unittest.TestCase):
    def test_provider_attributes_exist(self):
        self.assertTrue(hasattr(Config, 'MODEL_PROVIDER'))
        self.assertTrue(hasattr(Config, 'NEURALQUERY_BASE_MODEL'))
        self.assertTrue(hasattr(Config, 'NEURALQUERY_ADAPTER_PATH'))
        self.assertTrue(hasattr(Config, 'NEURALQUERY_DEVICE'))
        self.assertTrue(hasattr(Config, 'NEURALQUERY_FALLBACK_TO_GEMINI'))

    def test_default_device_auto(self):
        self.assertIn(Config.NEURALQUERY_DEVICE, ['auto', 'cuda', 'cpu', 'mps'])


if __name__ == "__main__":
    unittest.main()
