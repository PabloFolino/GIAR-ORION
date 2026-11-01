"""
Pruebas independientes de EvidenceVerifier.py — GIAR-ORION.

Ejecutar desde la raíz del proyecto:
    python Tests/test_evidence_verifier.py

Estas pruebas usan datos sintéticos. No consultan Internet, Ollama ni el RAG real.
"""

import json
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT_DIR / "Agent"

if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from EvidenceVerifier import EvidenceVerifier, EvidenceVerifierError


RAG_SAMPLE = [
    {
        "source": "Fundamentos_de_SAC_GIAR_ORION.md",
        "text": "SAC es un algoritmo de aprendizaje por refuerzo off-policy.",
        "score": 0.82,
        "mode": "hybrid",
    }
]

WEB_SAMPLE = [
    {
        "title": "Soft Actor-Critic",
        "url": "https://spinningup.openai.com/en/latest/algorithms/sac.html",
        "description": "Documentación de referencia sobre Soft Actor-Critic.",
        "source": "spinningup.openai.com",
    }
]


class TestEvidenceVerifier(unittest.TestCase):

    def setUp(self):
        self.verifier = EvidenceVerifier()

    def test_ev001_url_recuperada(self):
        """Una URL incluida en DDGS debe reconocerse en la respuesta."""
        response = (
            "Referencia: "
            "https://spinningup.openai.com/en/latest/algorithms/sac.html"
        )
        report = self.verifier.verify(response, web_results=WEB_SAMPLE)

        check = report["checks"]["web_url_reference_check"]
        self.assertEqual(check["status"], "PASS")
        self.assertEqual(len(check["urls_matched_to_search_results"]), 1)
        self.assertEqual(check["urls_not_found_in_search_results"], [])

    def test_ev002_url_no_recuperada(self):
        """Una URL no presente en los resultados DDGS debe marcarse."""
        response = "Referencia: https://example.org/articulo-inexistente"
        report = self.verifier.verify(response, web_results=WEB_SAMPLE)

        check = report["checks"]["web_url_reference_check"]
        self.assertEqual(check["status"], "UNVERIFIED")
        self.assertEqual(
            check["urls_not_found_in_search_results"],
            ["https://example.org/articulo-inexistente"],
        )
        self.assertEqual(report["overall_status"], "UNVERIFIED_REFERENCES")

    def test_ev003_fuente_rag_mencionada(self):
        """Una ruta RAG recuperada y mencionada literalmente debe reconocerse."""
        response = (
            "Según Fundamentos_de_SAC_GIAR_ORION.md, "
            "SAC es un algoritmo off-policy."
        )
        report = self.verifier.verify(response, rag_results=RAG_SAMPLE)

        check = report["checks"]["rag_source_reference_check"]
        self.assertEqual(check["status"], "PASS")
        self.assertIn(
            "Fundamentos_de_SAC_GIAR_ORION.md",
            check["sources_mentioned_literally"],
        )

    def test_ev004_url_duplicada_en_evidencias(self):
        """Dos registros DDGS con la misma URL deben detectarse como duplicados."""
        duplicated_results = [
            dict(WEB_SAMPLE[0]),
            dict(WEB_SAMPLE[0], title="Mismo enlace con otro título"),
        ]
        report = self.verifier.verify(
            "La respuesta no incluye enlaces.",
            web_results=duplicated_results,
        )

        check = report["checks"]["duplicate_web_reference_check"]
        self.assertEqual(check["status"], "WARNING")
        self.assertEqual(len(check["duplicate_urls"]), 1)
        self.assertEqual(
            report["overall_status"],
            "WARNING_DUPLICATE_REFERENCES",
        )

    def test_ev005_respuesta_sin_referencias(self):
        """La ausencia de citas no debe clasificarse como falsedad."""
        report = self.verifier.verify(
            "SAC es un algoritmo de aprendizaje por refuerzo.",
            rag_results=RAG_SAMPLE,
            web_results=WEB_SAMPLE,
        )

        self.assertEqual(
            report["checks"]["web_url_reference_check"]["status"],
            "PASS",
        )
        self.assertEqual(
            report["checks"]["rag_source_reference_check"]["status"],
            "NOT_CITED",
        )
        self.assertEqual(
            report["checks"]["semantic_support_check"]["status"],
            "NOT_PERFORMED",
        )
        self.assertEqual(report["overall_status"], "RAG_SOURCES_NOT_CITED")

    def test_ev006_rechaza_resultado_web_sin_url_valida(self):
        """Los registros web incompletos deben generar un error controlado."""
        invalid_web = [{
            "title": "Página sin URL",
            "url": "no-es-una-url",
            "description": "Fragmento",
            "source": "example.org",
        }]
        with self.assertRaises(EvidenceVerifierError):
            self.verifier.verify("Respuesta", web_results=invalid_web)

    def test_ev007_informe_serializable_json(self):
        """El informe debe poder serializarse como JSON."""
        report = self.verifier.verify(
            "Respuesta de prueba.",
            rag_results=RAG_SAMPLE,
            web_results=WEB_SAMPLE,
        )
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertIsInstance(serialized, str)
        self.assertIn('"EvidenceVerifier"', serialized)


if __name__ == "__main__":
    unittest.main(verbosity=2)
