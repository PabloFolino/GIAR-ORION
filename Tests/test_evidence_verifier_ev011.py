"""
EV-011 — Evaluación ampliada de robustez semántica de EvidenceVerifier v0.2.

Ejecutar desde la raíz de GIAR-ORION:
    python .\\Tests\\test_evidence_verifier_ev011.py

Usa evidencia sintética controlada. No consulta RAG/DDGS reales.
Evalúa español e inglés, paráfrasis, contradicción, neutralidad,
evidencia parcial y evidencia conflictiva.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from collections import Counter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = PROJECT_ROOT / "Agent"
RESULTS_PATH = PROJECT_ROOT / "Tests" / "evidence_verifier_ev011_results.json"

if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from EvidenceVerifier import EvidenceVerifier  # noqa: E402


CASES = [
    {
        "id": "EV011-01",
        "language": "es",
        "category": "supported_paraphrase",
        "evidence": [
            "SAC es un algoritmo de aprendizaje por refuerzo off-policy."
        ],
        "claim": "Soft Actor-Critic pertenece a los métodos off-policy de aprendizaje por refuerzo.",
        "expected": "SUPPORTED",
    },
    {
        "id": "EV011-02",
        "language": "en",
        "category": "supported_paraphrase",
        "evidence": [
            "Soft Actor-Critic is an off-policy deep reinforcement learning algorithm."
        ],
        "claim": "SAC is a deep RL method that learns from previously collected experience rather than only the current policy.",
        "expected": "SUPPORTED",
    },
    {
        "id": "EV011-03",
        "language": "es",
        "category": "contradiction",
        "evidence": [
            "En SAC, la política del actor es estocástica y modela una distribución de probabilidad sobre las acciones."
        ],
        "claim": "En SAC, el actor utiliza exclusivamente una política determinista y no representa distribuciones de probabilidad.",
        "expected": "CONTRADICTED",
    },
    {
        "id": "EV011-04",
        "language": "en",
        "category": "contradiction",
        "evidence": [
            "The SAC actor produces a probability distribution over actions; it is not defined as a purely deterministic policy."
        ],
        "claim": "The SAC actor is purely deterministic and does not represent a probability distribution over actions.",
        "expected": "CONTRADICTED",
    },
    {
        "id": "EV011-05",
        "language": "es",
        "category": "neutral_unrelated",
        "evidence": [
            "SAC es un algoritmo de aprendizaje por refuerzo off-policy."
        ],
        "claim": "SAC fue creado originalmente para detectar tumores en imágenes de resonancia magnética.",
        "expected": "INSUFFICIENT",
    },
    {
        "id": "EV011-06",
        "language": "en",
        "category": "neutral_unrelated",
        "evidence": [
            "The replay buffer stores transitions collected while interacting with the environment."
        ],
        "claim": "The first implementation of SAC was written in the Rust programming language.",
        "expected": "INSUFFICIENT",
    },
    {
        "id": "EV011-07",
        "language": "es",
        "category": "lexical_overlap_wrong_relation",
        "evidence": [
            "La red Actor recibe el vector de estado y genera los parámetros de una distribución Normal."
        ],
        "claim": "La red Actor recibe los parámetros de una distribución Normal y genera el vector de estado.",
        "expected": "CONTRADICTED",
    },
    {
        "id": "EV011-08",
        "language": "en",
        "category": "lexical_overlap_wrong_relation",
        "evidence": [
            "The critic estimates the action value from the state and action."
        ],
        "claim": "The actor estimates the action value from the state and action.",
        "expected": "INSUFFICIENT",
    },
]

PARTIAL_CASE = {
    "id": "EV011-09",
    "description": "Agregación de varias afirmaciones atómicas: una respaldada y otra sin respaldo.",
    "evidence": [
        "SAC es un algoritmo de aprendizaje por refuerzo off-policy."
    ],
    "claims": [
        "SAC es un algoritmo de aprendizaje por refuerzo off-policy.",
        "SAC fue implementado originalmente en el lenguaje Rust.",
    ],
    "expected_overall": "PARTIALLY_SUPPORTED",
}

CONFLICT_CASE = {
    "id": "EV011-10",
    "description": "Dos fragmentos con información mutuamente incompatible sobre la misma afirmación.",
    "claim": "SAC es un algoritmo off-policy.",
    "evidence": [
        "SAC es un algoritmo de aprendizaje por refuerzo off-policy.",
        "SAC es un algoritmo de aprendizaje por refuerzo on-policy.",
    ],
    "expected": "CONFLICTING_EVIDENCE",
}


def make_rag(texts: list[str]) -> list[dict]:
    return [
        {
            "source": f"EV011_synthetic_evidence_{i + 1}.md",
            "text": text,
            "score": 1.0,
            "mode": "synthetic_test",
        }
        for i, text in enumerate(texts)
    ]


def run_one_claim(verifier: EvidenceVerifier, case: dict) -> dict:
    report = verifier.verify_claims(
        claims=[case["claim"]],
        rag_results=make_rag(case["evidence"]),
        web_results=[],
    )
    return report["claims"][0]


def main() -> int:
    print("EV-011 — Evaluación ampliada de robustez semántica")
    print("=" * 78)
    print(f"Casos individuales: {len(CASES)}")
    print("Idiomas: español e inglés")
    print("Evidencia: sintética y controlada")
    print()

    verifier = EvidenceVerifier()
    individual_results = []

    try:
        for case in CASES:
            observed = run_one_claim(verifier, case)
            observed_status = observed.get("status")
            passed = observed_status == case["expected"]

            entailment = observed.get("best_entailment_score", 0.0)
            contradiction = observed.get("best_contradiction_score", 0.0)

            print(
                f"{case['id']} [{case['language']}] "
                f"{case['category']}"
            )
            print(f"Evidencia: {' | '.join(case['evidence'])}")
            print(f"Afirmación: {case['claim']}")
            print(
                f"Esperado: {case['expected']} | "
                f"Obtenido: {observed_status} | "
                f"{'PASS' if passed else 'REVISAR'}"
            )
            print(
                f"Scores: entailment={entailment:.4f} | "
                f"contradiction={contradiction:.4f}"
            )
            print("-" * 78)

            individual_results.append({
                "case_id": case["id"],
                "language": case["language"],
                "category": case["category"],
                "claim": case["claim"],
                "evidence": case["evidence"],
                "expected": case["expected"],
                "observed": observed_status,
                "passed": passed,
                "entailment_score": entailment,
                "contradiction_score": contradiction,
                "comparisons": observed.get("comparisons", []),
            })

        # Prueba de agregación parcial: no se fuerza una clase NLI inexistente.
        partial_report = verifier.verify_claims(
            claims=PARTIAL_CASE["claims"],
            rag_results=make_rag(PARTIAL_CASE["evidence"]),
            web_results=[],
        )
        partial_observed = partial_report.get("overall_status")
        partial_passed = partial_observed == PARTIAL_CASE["expected_overall"]

        print(PARTIAL_CASE["id"])
        print(PARTIAL_CASE["description"])
        print(
            f"Esperado: {PARTIAL_CASE['expected_overall']} | "
            f"Obtenido: {partial_observed} | "
            f"{'PASS' if partial_passed else 'REVISAR'}"
        )
        print("-" * 78)

        # Prueba de evidencia conflictiva.
        conflict_report = verifier.verify_claims(
            claims=[CONFLICT_CASE["claim"]],
            rag_results=make_rag(CONFLICT_CASE["evidence"]),
            web_results=[],
        )
        conflict_observed = conflict_report["claims"][0].get("status")
        conflict_passed = conflict_observed == CONFLICT_CASE["expected"]

        print(CONFLICT_CASE["id"])
        print(CONFLICT_CASE["description"])
        print(
            f"Esperado: {CONFLICT_CASE['expected']} | "
            f"Obtenido: {conflict_observed} | "
            f"{'PASS' if conflict_passed else 'REVISAR'}"
        )
        print("-" * 78)

    except Exception:
        print("ERROR durante EV-011:")
        traceback.print_exc()
        return 1

    # Métricas de clasificación para los ocho casos individuales.
    labels = ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT"]
    confusion = {
        expected: {
            predicted: sum(
                1 for item in individual_results
                if item["expected"] == expected and item["observed"] == predicted
            )
            for predicted in labels
        }
        for expected in labels
    }

    false_positives = [
        item for item in individual_results
        if item["expected"] != "SUPPORTED" and item["observed"] == "SUPPORTED"
    ]
    false_negatives = [
        item for item in individual_results
        if item["expected"] == "SUPPORTED" and item["observed"] != "SUPPORTED"
    ]

    # La precisión/recall binaria SUPPORTED se calcula solo sobre estos fixtures.
    tp = sum(
        1 for item in individual_results
        if item["expected"] == "SUPPORTED" and item["observed"] == "SUPPORTED"
    )
    fp = len(false_positives)
    fn = len(false_negatives)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None

    partial_result = {
        "case_id": PARTIAL_CASE["id"],
        "expected": PARTIAL_CASE["expected_overall"],
        "observed": partial_observed,
        "passed": partial_passed,
        "claim_results": partial_report.get("claims", []),
    }
    conflict_result = {
        "case_id": CONFLICT_CASE["id"],
        "expected": CONFLICT_CASE["expected"],
        "observed": conflict_observed,
        "passed": conflict_passed,
        "claim_results": conflict_report.get("claims", []),
    }

    all_passed = sum(item["passed"] for item in individual_results)
    special_passed = int(partial_passed) + int(conflict_passed)
    total_passed = all_passed + special_passed
    total_cases = len(CASES) + 2

    final_report = {
        "test": "EV-011",
        "verifier_version": verifier.VERSION,
        "nli_model": verifier.nli_model_name,
        "device": verifier.device,
        "individual_cases": individual_results,
        "special_cases": [partial_result, conflict_result],
        "metrics": {
            "individual_case_count": len(CASES),
            "individual_matches": all_passed,
            "confusion_matrix_expected_rows_predicted_columns": confusion,
            "supported_precision": precision,
            "supported_recall": recall,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "partial_aggregation_passed": partial_passed,
            "conflicting_evidence_passed": conflict_passed,
            "total_matches_including_special_cases": total_passed,
            "total_cases_including_special_cases": total_cases,
        },
        "limitations": [
            "Los diez casos son sintéticos y fueron diseñados para esta evaluación.",
            "El conjunto es pequeño y no representa una muestra estadística del uso real.",
            "Las etiquetas esperadas describen la relación con los fragmentos proporcionados, no la verdad universal de cada afirmación.",
            "Los scores NLI no son probabilidades calibradas de verdad.",
            "Un resultado satisfactorio no garantiza ausencia de alucinaciones.",
            "La métrica de falsos positivos/falsos negativos se calcula sobre los ocho casos individuales, no sobre las pruebas especiales.",
        ],
    }

    try:
        RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        RESULTS_PATH.write_text(
            json.dumps(final_report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    except Exception:
        print("ERROR al guardar o validar el informe JSON:")
        traceback.print_exc()
        return 1

    print()
    print("=" * 78)
    print(f"EV-011: {total_passed}/{total_cases} coincidencias")
    print(f"Casos individuales: {all_passed}/{len(CASES)}")
    print(f"Agregación parcial: {'PASS' if partial_passed else 'REVISAR'}")
    print(f"Evidencia conflictiva: {'PASS' if conflict_passed else 'REVISAR'}")
    print(f"Falsos positivos SUPPORTED: {fp}")
    print(f"Falsos negativos SUPPORTED: {fn}")
    print(f"Precisión SUPPORTED: {precision}")
    print(f"Recall SUPPORTED: {recall}")
    print(f"Informe: {RESULTS_PATH}")
    print()
    print(
        "Interpretación: estas métricas describen únicamente este conjunto "
        "sintético; no deben extrapolarse como rendimiento general del sistema."
    )

    # El código de salida indica que la prueba pudo ejecutarse y producir
    # resultados completos. Los fallos de clasificación quedan explícitos
    # en consola y en el JSON, sin ocultarlos.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
