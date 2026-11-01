"""
EV-010 — Prueba de integración de EvidenceVerifier v0.2.

Ejecutar desde la raíz de GIAR-ORION:
    python .\Tests\test_evidence_verifier_ev010.py

La prueba utiliza un fragmento sintético de evidencia SAC y el modelo NLI
multilingüe configurado en EvidenceVerifier. No consulta RAG ni DDGS reales.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = PROJECT_ROOT / "Agent"
RESULTS_PATH = PROJECT_ROOT / "Tests" / "evidence_verifier_ev010_results.json"

if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from EvidenceVerifier import EvidenceVerifier  # noqa: E402


def main() -> int:
    print("EV-010 — Integración NLI en EvidenceVerifier v0.2")
    print("=" * 72)

    rag_results = [
        {
            "source": "EV010_SAC_evidence_synthetic.md",
            "text": (
                "Soft Actor-Critic (SAC) es un algoritmo de aprendizaje por "
                "refuerzo off-policy. Su objetivo incorpora una recompensa "
                "acumulada y un término de entropía para favorecer políticas "
                "estocásticas."
            ),
            "score": 1.0,
            "mode": "synthetic_test",
        }
    ]

    web_results = []

    test_cases = [
        {
            "id": "EV-010-A",
            "claim": "SAC es un algoritmo de aprendizaje por refuerzo off-policy.",
            "expected": "SUPPORTED",
        },
        {
            "id": "EV-010-B",
            "claim": "SAC es un algoritmo de aprendizaje por refuerzo on-policy.",
            "expected": "CONTRADICTED",
        },
        {
            "id": "EV-010-C",
            "claim": (
                "SAC fue desarrollado originalmente para clasificar imágenes médicas."
            ),
            "expected": "INSUFFICIENT",
        },
    ]

    verifier = EvidenceVerifier()
    print(f"Modelo NLI: {verifier.nli_model_name}")
    print(f"Dispositivo solicitado: {verifier.device or 'automático'}")
    print("Evidencia: fragmento RAG sintético")
    print()

    try:
        response = (
            "La afirmación de prueba se contrasta con la evidencia sintética. "
            "Fuente: EV010_SAC_evidence_synthetic.md"
        )
        report = verifier.verify(
            response=response,
            rag_results=rag_results,
            web_results=web_results,
            claims=[case["claim"] for case in test_cases],
        )
    except Exception:
        print("ERROR durante la ejecución de EvidenceVerifier v0.2:")
        traceback.print_exc()
        return 1

    semantic_report = report.get("checks", {}).get("semantic_support_check")
    if not isinstance(semantic_report, dict):
        print("FAIL: falta checks.semantic_support_check en el informe.")
        return 1

    observed_claims = semantic_report.get("claims")
    if not isinstance(observed_claims, list) or len(observed_claims) != len(test_cases):
        print("FAIL: cantidad o estructura de afirmaciones incorrecta.")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    print(f"Versión informada: {report.get('version')}")
    print(f"Dispositivo utilizado: {semantic_report.get('device')}")
    print("-" * 72)

    case_results = []
    for case, observed in zip(test_cases, observed_claims):
        observed_status = observed.get("status")
        entailment = observed.get("best_entailment_score", 0.0)
        contradiction = observed.get("best_contradiction_score", 0.0)
        passed = observed_status == case["expected"]

        print(case["id"])
        print(f"Afirmación: {case['claim']}")
        print(f"Esperado: {case['expected']}")
        print(f"Obtenido: {observed_status}")
        print(
            f"Scores: entailment={entailment:.4f} | "
            f"contradiction={contradiction:.4f}"
        )
        print(f"Resultado: {'PASS' if passed else 'REVISAR'}")
        print("-" * 72)

        case_results.append({
            "case_id": case["id"],
            "claim": case["claim"],
            "expected_status": case["expected"],
            "observed_status": observed_status,
            "passed": passed,
            "best_entailment_score": entailment,
            "best_contradiction_score": contradiction,
        })

    try:
        serialized_report = json.dumps(report, ensure_ascii=False, indent=2)
        json.loads(serialized_report)
    except (TypeError, ValueError):
        print("FAIL: el informe no es serializable como JSON.")
        traceback.print_exc()
        return 1

    final_report = {
        "test": "EV-010",
        "verifier_version": report.get("version"),
        "nli_model": semantic_report.get("model"),
        "device": semantic_report.get("device"),
        "cases": case_results,
        "integration_report": report,
        "note": (
            "Evidencia sintética. Esta prueba evalúa integración técnica; "
            "no demuestra exactitud científica general ni valida documentos reales."
        ),
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps(final_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    passed_count = sum(item["passed"] for item in case_results)
    print()
    print("=" * 72)
    print(f"EV-010: {passed_count}/{len(test_cases)} coincidencias de clasificación")
    print("Serialización JSON: PASS")
    print(f"Informe: {RESULTS_PATH}")
    print(
        "Nota: los scores NLI no son probabilidades calibradas de verdad. "
        "No ajustar umbrales usando solamente estos tres casos."
    )

    # Se devuelve código 0 si la integración produjo un informe válido.
    # Las discrepancias de clasificación quedan visibles en el resultado.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
