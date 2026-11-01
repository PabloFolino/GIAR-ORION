"""
Pruebas deterministas de ClaimVerificationPipeline.

Ejecutar desde la raíz del proyecto:
    .venv\\Scripts\\python.exe Tests\\test_claim_verification_pipeline.py

Estas pruebas usan dobles controlados; no requieren Ollama ni descargar el
modelo NLI. Comprueban la orquestación y el tratamiento de estados/errores.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Agent.ClaimVerificationPipeline import ClaimVerificationPipeline


class FakeExtractor:
    VERSION = "fake-extractor"

    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def extract(self, response):
        self.calls.append(response)
        if self.error:
            raise self.error
        return self.result


class FakeVerifier:
    VERSION = "fake-verifier"

    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def verify(self, response, rag_results=None, web_results=None, claims=None):
        self.calls.append({
            "response": response,
            "rag_results": rag_results,
            "web_results": web_results,
            "claims": claims,
        })
        if self.error:
            raise self.error
        return self.result


def extraction(complete=True, claims=None, errors=None):
    return {
        "complete": complete,
        "unit_count": 1,
        "classified_unit_count": 1,
        "claim_count": len(claims or []),
        "claims": claims or [],
        "errors": errors or [],
    }


def verification(semantic_status=None, reference_status="OK"):
    checks = {}
    if semantic_status is not None:
        checks["semantic_support_check"] = {
            "overall_status": semantic_status,
            "claims": [],
        }
    return {
        "overall_status": reference_status,
        "checks": checks,
    }


class TestClaimVerificationPipeline(unittest.TestCase):

    def make_pipeline(self, extracted, verified=None, extract_error=None,
                      verify_error=None):
        extractor = FakeExtractor(extracted, extract_error)
        verifier = FakeVerifier(verified, verify_error)
        return ClaimVerificationPipeline(extractor, verifier), extractor, verifier

    def test_01_supported_claim(self):
        claims = [{"claim": "La Tierra orbita alrededor del Sol."}]
        pipeline, _, verifier = self.make_pipeline(
            extraction(claims=claims),
            verification("SUPPORTED", "REFERENCE_WARNING"),
        )
        result = pipeline.run("La Tierra orbita alrededor del Sol.")
        self.assertEqual(result["status"], "SUPPORTED")
        self.assertTrue(result["can_present_as_supported"])
        self.assertEqual(result["reference_status"], "REFERENCE_WARNING")
        self.assertEqual(verifier.calls[0]["claims"], [
            "La Tierra orbita alrededor del Sol."
        ])

    def test_02_partially_supported(self):
        pipeline, _, _ = self.make_pipeline(
            extraction(claims=[{"claim": "Afirmación A."}]),
            verification("PARTIALLY_SUPPORTED"),
        )
        result = pipeline.run("Afirmación A.")
        self.assertEqual(result["status"], "PARTIALLY_SUPPORTED")
        self.assertFalse(result["can_present_as_supported"])

    def test_03_contradicted(self):
        pipeline, _, _ = self.make_pipeline(
            extraction(claims=[{"claim": "Afirmación."}]),
            verification("CONTRADICTED"),
        )
        self.assertEqual(pipeline.run("Afirmación.")["status"], "CONTRADICTED")

    def test_04_insufficient(self):
        pipeline, _, _ = self.make_pipeline(
            extraction(claims=[{"claim": "Afirmación."}]),
            verification("INSUFFICIENT"),
        )
        self.assertEqual(pipeline.run("Afirmación.")["status"], "INSUFFICIENT")

    def test_05_conflicting_evidence(self):
        pipeline, _, _ = self.make_pipeline(
            extraction(claims=[{"claim": "Afirmación."}]),
            verification("CONFLICTING_EVIDENCE"),
        )
        self.assertEqual(
            pipeline.run("Afirmación.")["status"], "CONFLICTING_EVIDENCE"
        )

    def test_06_mixed_evidence(self):
        pipeline, _, _ = self.make_pipeline(
            extraction(claims=[{"claim": "Afirmación."}]),
            verification("MIXED_EVIDENCE"),
        )
        self.assertEqual(pipeline.run("Afirmación.")["status"], "MIXED_EVIDENCE")

    def test_07_no_factual_claims_does_not_send_empty_list(self):
        pipeline, _, verifier = self.make_pipeline(
            extraction(claims=[]),
            verification(None, "REFERENCE_CHECKED"),
        )
        result = pipeline.run("¿Cómo estás?")
        self.assertEqual(result["status"], "NO_FACTUAL_CLAIMS")
        self.assertEqual(result["semantic_status"], "NOT_PERFORMED")
        self.assertIsNone(verifier.calls[0]["claims"])
        self.assertFalse(result["can_present_as_supported"])

    def test_08_incomplete_extraction_stops_verification(self):
        pipeline, _, verifier = self.make_pipeline(
            extraction(complete=False, claims=[{"claim": "Afirmación."}]),
            verification("SUPPORTED"),
        )
        result = pipeline.run("Afirmación.")
        self.assertEqual(result["status"], "EXTRACTION_INCOMPLETE")
        self.assertEqual(verifier.calls, [])

    def test_09_extraction_exception(self):
        pipeline, _, verifier = self.make_pipeline(
            None, extract_error=RuntimeError("fallo extractor")
        )
        result = pipeline.run("Texto.")
        self.assertEqual(result["status"], "EXTRACTION_ERROR")
        self.assertEqual(verifier.calls, [])

    def test_10_invalid_extraction_structure(self):
        pipeline, _, verifier = self.make_pipeline({
            "complete": True, "claims": ["no es un objeto"]
        })
        result = pipeline.run("Texto.")
        self.assertEqual(result["status"], "EXTRACTION_ERROR")
        self.assertEqual(verifier.calls, [])

    def test_11_verifier_exception(self):
        pipeline, _, _ = self.make_pipeline(
            extraction(claims=[{"claim": "Afirmación."}]),
            verify_error=RuntimeError("fallo verificador"),
        )
        result = pipeline.run("Afirmación.")
        self.assertEqual(result["status"], "VERIFICATION_ERROR")
        self.assertFalse(result["can_present_as_supported"])

    def test_12_missing_semantic_report(self):
        pipeline, _, _ = self.make_pipeline(
            extraction(claims=[{"claim": "Afirmación."}]),
            verification(None),
        )
        result = pipeline.run("Afirmación.")
        self.assertEqual(
            result["status"], "SEMANTIC_VERIFICATION_NOT_PERFORMED"
        )

    def test_13_unknown_semantic_status(self):
        pipeline, _, _ = self.make_pipeline(
            extraction(claims=[{"claim": "Afirmación."}]),
            verification("UNKNOWN"),
        )
        result = pipeline.run("Afirmación.")
        self.assertEqual(
            result["status"], "SEMANTIC_VERIFICATION_NOT_PERFORMED"
        )

    def test_14_empty_response_rejected(self):
        pipeline, _, _ = self.make_pipeline(extraction())
        with self.assertRaises(ValueError):
            pipeline.run("   ")

    def test_15_forwards_evidence(self):
        rag = [{"text": "Evidencia RAG", "source": "doc.pdf"}]
        web = [{"title": "Página", "description": "Fragmento", "url": "https://example.org"}]
        pipeline, _, verifier = self.make_pipeline(
            extraction(claims=[{"claim": "Afirmación."}]),
            verification("SUPPORTED"),
        )
        pipeline.run("Afirmación.", rag_results=rag, web_results=web)
        self.assertIs(verifier.calls[0]["rag_results"], rag)
        self.assertIs(verifier.calls[0]["web_results"], web)

    def test_16_reference_status_is_not_semantic_status(self):
        pipeline, _, _ = self.make_pipeline(
            extraction(claims=[{"claim": "Afirmación."}]),
            verification("INSUFFICIENT", "SUPPORTED"),
        )
        result = pipeline.run("Afirmación.")
        self.assertEqual(result["reference_status"], "SUPPORTED")
        self.assertEqual(result["semantic_status"], "INSUFFICIENT")
        self.assertEqual(result["status"], "INSUFFICIENT")
        self.assertFalse(result["can_present_as_supported"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestClaimVerificationPipeline
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print("\nRESUMEN")
    print(f"Total: {result.testsRun}")
    print(f"PASS: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"FAIL: {len(result.failures)}")
    print(f"ERROR: {len(result.errors)}")
    sys.exit(0 if result.wasSuccessful() else 1)
