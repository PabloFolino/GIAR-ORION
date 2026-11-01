"""
Validación estructural del conjunto de casos semánticos EV-008.
No evalúa semántica automáticamente: comprueba integridad del benchmark.
"""

import json
import unittest
from pathlib import Path

DATA_PATH = Path(__file__).with_name("evidence_semantic_cases.json")
VALID_LABELS = {
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "INSUFFICIENT",
    "CONTRADICTED",
}


class TestSemanticCaseDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with DATA_PATH.open("r", encoding="utf-8") as file:
            cls.dataset = json.load(file)

    def test_dataset_has_four_cases(self):
        self.assertEqual(len(self.dataset["cases"]), 4)

    def test_each_case_has_required_fields(self):
        for case in self.dataset["cases"]:
            with self.subTest(case=case.get("id")):
                self.assertTrue(case["id"])
                self.assertTrue(case["claim"])
                self.assertTrue(case["evidence"])
                self.assertIn(case["expected"], VALID_LABELS)
                self.assertTrue(case["rationale"])

    def test_case_ids_are_unique(self):
        ids = [case["id"] for case in self.dataset["cases"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_fixture_warning_is_present(self):
        self.assertIn("sintéticos", self.dataset["important_note"])
        self.assertIn("No son citas", self.dataset["important_note"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
