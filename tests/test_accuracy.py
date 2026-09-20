"""
Unit tests for accuracy and citation heuristics.
"""

import unittest
from accuracy import calculate_accuracy


class TestAccuracyMetrics(unittest.TestCase):
    def test_empty_sources(self):
        metrics = calculate_accuracy([], "Some response")
        self.assertEqual(metrics["overall_accuracy"], 0)
        self.assertEqual(metrics["sources_analyzed"], 0)

    def test_empty_response(self):
        sources = [{"url": "https://example.com", "title": "Test", "content": "Content"}]
        metrics = calculate_accuracy(sources, "")
        self.assertEqual(metrics["overall_accuracy"], 0)

    def test_high_overlap_and_citations(self):
        sources = [
            {
                "url": "https://example.com/energy",
                "title": "Clean Energy Storage",
                "snippet": "Solid state batteries reach high energy density.",
                "content": "Solid state batteries reach high energy density with sulfide electrolyte."
            }
        ]
        response = (
            "Solid state batteries reach high energy density with sulfide electrolyte. "
            "Source: https://example.com/energy"
        )
        metrics = calculate_accuracy(sources, response)
        self.assertGreaterEqual(metrics["overall_accuracy"], 75)
        self.assertGreater(metrics["citation_score"], 0)
        self.assertIn(metrics["confidence_level"], ["High", "Moderate"])


if __name__ == "__main__":
    unittest.main()
