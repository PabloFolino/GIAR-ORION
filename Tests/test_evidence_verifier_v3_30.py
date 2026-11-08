"""
Batería controlada de 30 casos para EvidenceVerifier 0.3.0 (3.0).

Uso:
    python Tests/test_evidence_verifier_v3_30.py

Ejecutar desde la raíz de GIAR-ORION con el entorno virtual activo.
No modifica EvidenceVerifier, RAG, ClaimExtractor ni la arquitectura.
Genera CSV y JSON en output/evidence_verifier_v3_30/.
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

from Agent.EvidenceVerifier import EvidenceVerifier


EVIDENCE_EQUIVALENCE = [
    {
        "id": "EQ01",
        "category": "equivalencia_es_en",
        "claim": "El Replay Buffer almacena experiencias anteriores para reutilizarlas durante el entrenamiento.",
        "evidence": "The replay buffer stores past transitions and samples them later to train the agent.",
        "expected": "SUPPORTED",
    },
    {
        "id": "EQ02",
        "category": "equivalencia_es_en",
        "claim": "El Actor representa la política y produce una distribución de acciones a partir del estado.",
        "evidence": "The actor parameterizes the policy distribution over actions conditioned on the current state.",
        "expected": "SUPPORTED",
    },
    {
        "id": "EQ03",
        "category": "equivalencia_es_en",
        "claim": "SAC utiliza dos redes críticas para estimar el valor Q de una acción en un estado.",
        "evidence": "SAC employs two independent Q-functions, also called twin critics, to estimate Q(s,a).",
        "expected": "SUPPORTED",
    },
    {
        "id": "EQ04",
        "category": "equivalencia_es_en",
        "claim": "La entropía objetivo establece el nivel de aleatoriedad que se desea para la política.",
        "evidence": "The target entropy specifies the desired entropy level of the policy.",
        "expected": "SUPPORTED",
    },
    {
        "id": "EQ05",
        "category": "equivalencia_es_en",
        "claim": "El coeficiente alfa determina cuánto pesa la entropía en el objetivo de la política.",
        "evidence": "The temperature parameter alpha controls the relative weight of the entropy term in the policy objective.",
        "expected": "SUPPORTED",
    },
    {
        "id": "EQ06",
        "category": "equivalencia_es_en",
        "claim": "La técnica de reparametrización permite calcular gradientes a través de una acción muestreada de forma estocástica.",
        "evidence": "The reparameterization trick expresses a stochastic action as a differentiable transformation, allowing gradients to pass through the sampled action.",
        "expected": "SUPPORTED",
    },
    {
        "id": "EQ07",
        "category": "equivalencia_es_en",
        "claim": "El crítico se entrena minimizando el error entre su estimación Q y un objetivo de Bellman.",
        "evidence": "The critic is optimized by minimizing the difference between its Q-value prediction and the Bellman target.",
        "expected": "SUPPORTED",
    },
    {
        "id": "EQ08",
        "category": "equivalencia_es_en",
        "claim": "El Actor busca acciones que tengan un valor Q alto sin perder el incentivo de mantener entropía.",
        "evidence": "The actor objective encourages high expected Q-values while retaining an entropy regularization term.",
        "expected": "SUPPORTED",
    },
    {
        "id": "EQ09",
        "category": "equivalencia_es_en",
        "claim": "El ajuste automático de entropía modifica alfa para aproximar la entropía de la política a la entropía objetivo.",
        "evidence": "Automatic entropy tuning updates the temperature coefficient alpha so that policy entropy approaches the target entropy.",
        "expected": "SUPPORTED",
    },
    {
        "id": "EQ10",
        "category": "equivalencia_es_en",
        "claim": "La actualización suave de la red objetivo combina sus parámetros anteriores con los parámetros actuales de la red principal.",
        "evidence": "A soft target update performs a Polyak averaging step, interpolating target-network parameters with the current network parameters.",
        "expected": "SUPPORTED",
    },
]

EVIDENCE_PARAPHRASE = [
    {
        "id": "PA01",
        "category": "parafrasis_conceptual",
        "claim": "En SAC, la política no está obligada a seleccionar siempre una única acción fija para cada estado.",
        "evidence": "For a given observation, the policy can represent a probability distribution from which different actions may be sampled.",
        "expected": "SUPPORTED",
    },
    {
        "id": "PA02",
        "category": "parafrasis_conceptual",
        "claim": "El Replay Buffer desacopla temporalmente la recopilación de experiencias y las actualizaciones de las redes.",
        "evidence": "Stored transitions can be sampled for learning after the environment interaction that generated them has already finished.",
        "expected": "SUPPORTED",
    },
    {
        "id": "PA03",
        "category": "parafrasis_conceptual",
        "claim": "Las dos estimaciones Q permiten reducir el riesgo de sobreestimar el valor de las acciones.",
        "evidence": "SAC takes the minimum of the two critic estimates when constructing its target, which helps mitigate overestimation.",
        "expected": "SUPPORTED",
    },
    {
        "id": "PA04",
        "category": "parafrasis_conceptual",
        "claim": "La temperatura regula el compromiso entre obtener recompensas y conservar diversidad en las acciones.",
        "evidence": "The entropy temperature balances reward maximization against the policy's tendency to remain stochastic.",
        "expected": "SUPPORTED",
    },
    {
        "id": "PA05",
        "category": "parafrasis_conceptual",
        "claim": "Las redes objetivo se actualizan gradualmente en lugar de copiarse íntegramente en cada paso.",
        "evidence": "Target parameters are moved incrementally toward the online parameters using a small interpolation coefficient.",
        "expected": "SUPPORTED",
    },
]

EVIDENCE_CONTRADICTION = [
    {
        "id": "CO01",
        "category": "contradiccion_explicita",
        "claim": "En SAC, aumentar alfa reduce el peso del término de entropía en el objetivo de la política.",
        "evidence": "A higher entropy temperature coefficient increases the weight of the entropy term in the policy objective.",
        "expected": "CONTRADICTED",
    },
    {
        "id": "CO02",
        "category": "contradiccion_explicita",
        "claim": "La implementación descrita de SAC utiliza una única red crítica para estimar Q(s,a).",
        "evidence": "This SAC implementation uses two separate Q-functions, commonly referred to as twin critics, to estimate Q(s,a).",
        "expected": "CONTRADICTED",
    },
    {
        "id": "CO03",
        "category": "contradiccion_explicita",
        "claim": "El Replay Buffer descarta cada transición anterior cuando se incorpora una experiencia nueva.",
        "evidence": "The replay buffer retains previously collected transitions and samples from this stored collection during training.",
        "expected": "CONTRADICTED",
    },
    {
        "id": "CO04",
        "category": "contradiccion_explicita",
        "claim": "En SAC, el Actor produce exclusivamente una acción determinista y no representa una distribución de acciones.",
        "evidence": "The SAC actor represents a stochastic policy distribution and samples actions from that distribution.",
        "expected": "CONTRADICTED",
    },
    {
        "id": "CO05",
        "category": "contradiccion_explicita",
        "claim": "En el ajuste automático de entropía, alfa permanece fijo y nunca se actualiza.",
        "evidence": "Automatic entropy adjustment optimizes the temperature coefficient alpha during training to match a target entropy.",
        "expected": "CONTRADICTED",
    },
]

EVIDENCE_INSUFFICIENT = [
    {
        "id": "IN01",
        "category": "evidencia_insuficiente",
        "claim": "En SAC, el Replay Buffer determina directamente el valor del coeficiente alfa.",
        "evidence": "SAC uses a replay buffer to store transitions collected during interaction with the environment.",
        "expected": "INSUFFICIENT",
    },
    {
        "id": "IN02",
        "category": "evidencia_insuficiente",
        "claim": "La entropía objetivo de SAC se calcula a partir de la recompensa acumulada de cada episodio.",
        "evidence": "The SAC actor is trained using a stochastic policy and an entropy-related objective.",
        "expected": "INSUFFICIENT",
    },
    {
        "id": "IN03",
        "category": "evidencia_insuficiente",
        "claim": "SAC necesita exactamente 256 neuronas en cada capa oculta del Actor.",
        "evidence": "The actor is represented by a neural network that maps observations to a policy distribution.",
        "expected": "INSUFFICIENT",
    },
    {
        "id": "IN04",
        "category": "evidencia_insuficiente",
        "claim": "El uso de dos críticos en SAC garantiza que el entrenamiento siempre converja.",
        "evidence": "SAC uses two Q-functions and takes the smaller estimate in the target calculation to mitigate overestimation.",
        "expected": "INSUFFICIENT",
    },
    {
        "id": "IN05",
        "category": "evidencia_insuficiente",
        "claim": "El Replay Buffer de SAC almacena las experiencias durante exactamente 24 horas.",
        "evidence": "The replay buffer stores transitions so that they can be sampled during subsequent training updates.",
        "expected": "INSUFFICIENT",
    },
]

EVIDENCE_PARTIAL = [
    {
        "id": "PAI01",
        "category": "evidencia_parcial",
        "claim": "SAC utiliza un Replay Buffer y dos redes críticas para estimar los valores Q.",
        "evidence": "SAC stores previously collected transitions in a replay buffer for later sampling during training.",
        "expected": "INSUFFICIENT",
    },
    {
        "id": "PAI02",
        "category": "evidencia_parcial",
        "claim": "El Actor de SAC produce una distribución de acciones y el Replay Buffer almacena los gradientes de la política.",
        "evidence": "The actor outputs a stochastic policy distribution over actions conditioned on the current state.",
        "expected": "INSUFFICIENT",
    },
    {
        "id": "PAI03",
        "category": "evidencia_parcial",
        "claim": "El coeficiente alfa pondera la entropía y se calcula directamente como el promedio de las recompensas.",
        "evidence": "The temperature coefficient alpha controls the weight of the entropy term in the SAC policy objective.",
        "expected": "INSUFFICIENT",
    },
    {
        "id": "PAI04",
        "category": "evidencia_parcial",
        "claim": "Las redes objetivo se actualizan suavemente y utilizan siempre una tasa de actualización de 0,5.",
        "evidence": "SAC updates target-network parameters gradually through Polyak averaging.",
        "expected": "INSUFFICIENT",
    },
    {
        "id": "PAI05",
        "category": "evidencia_parcial",
        "claim": "El crítico minimiza el error de Bellman y el Actor se actualiza mediante gradiente descendente sobre la pérdida del crítico.",
        "evidence": "The critic is trained to minimize the Bellman error between its Q estimate and the target value.",
        "expected": "INSUFFICIENT",
    },
]

TEST_CASES = (
    EVIDENCE_EQUIVALENCE
    + EVIDENCE_PARAPHRASE
    + EVIDENCE_CONTRADICTION
    + EVIDENCE_INSUFFICIENT
    + EVIDENCE_PARTIAL
)


def main() -> None:
    if len(TEST_CASES) != 30:
        raise RuntimeError(f"Se esperaban 30 casos; se encontraron {len(TEST_CASES)}.")

    print("=" * 76)
    print("GIAR-ORION | BATERÍA CONTROLADA EVIDENCEVERIFIER 3.0")
    print("=" * 76)
    print(f"Casos: {len(TEST_CASES)}")
    print("Se ejecutará una adjudicación Qwen por afirmación.")
    print("La evidencia se suministra manualmente: esta prueba NO evalúa el RAG.")
    print("La extracción de afirmaciones tampoco forma parte de esta prueba.")
    print("\nInicializando EvidenceVerifier...")

    verifier = EvidenceVerifier()
    print(f"Versión: {verifier.VERSION}")
    print(f"Adjudicador: {verifier.adjudication_model}")
    print(f"Ollama habilitado: {verifier.use_ollama_adjudication}")
    print("\nComenzando pruebas...\n")

    rows: list[dict] = []
    details: list[dict] = []
    total_start = time.perf_counter()

    for position, case in enumerate(TEST_CASES, start=1):
        start = time.perf_counter()
        try:
            result = verifier.verify(
                response=case["claim"],
                rag_results=[
                    {
                        "source": f"controlled_test_{case['id']}",
                        "text": case["evidence"],
                    }
                ],
                claims=[case["claim"]],
            )
            elapsed = time.perf_counter() - start
            semantic = result["checks"]["semantic_support_check"]
            claim_report = semantic["claims"][0]
            comparison = (
                claim_report.get("comparisons", [{}])[0]
                if claim_report.get("comparisons")
                else {}
            )
            adjudication = comparison.get("adjudication", {})
            scores = comparison.get("scores", {})

            obtained = claim_report.get("status", "ERROR")
            expected = case["expected"]
            row = {
                "id": case["id"],
                "category": case["category"],
                "expected": expected,
                "nli_entailment": scores.get("entailment"),
                "nli_neutral": scores.get("neutral"),
                "nli_contradiction": scores.get("contradiction"),
                "qwen_label": adjudication.get("label"),
                "qwen_reason": adjudication.get("reason"),
                "final_status": obtained,
                "correct": obtained == expected,
                "adjudication_available": claim_report.get("adjudication_available"),
                "adjudication_error": claim_report.get("adjudication_error"),
                "elapsed_seconds": round(elapsed, 3),
                "claim": case["claim"],
                "evidence": case["evidence"],
            }
            rows.append(row)
            details.append(
                {
                    "test": case,
                    "result": result,
                    "elapsed_seconds": round(elapsed, 3),
                }
            )

            marker = "OK" if row["correct"] else "ERROR"
            print(
                f"[{position:02d}/30] {case['id']} | "
                f"esperado={expected:<12} obtenido={obtained:<12} "
                f"{marker} | {elapsed:.2f}s"
            )
            if row["adjudication_error"]:
                print(f"       Error de adjudicación: {row['adjudication_error']}")

        except Exception as exc:
            elapsed = time.perf_counter() - start
            row = {
                "id": case["id"],
                "category": case["category"],
                "expected": case["expected"],
                "nli_entailment": None,
                "nli_neutral": None,
                "nli_contradiction": None,
                "qwen_label": None,
                "qwen_reason": None,
                "final_status": "EXECUTION_ERROR",
                "correct": False,
                "adjudication_available": False,
                "adjudication_error": f"{type(exc).__name__}: {exc}",
                "elapsed_seconds": round(elapsed, 3),
                "claim": case["claim"],
                "evidence": case["evidence"],
            }
            rows.append(row)
            details.append({"test": case, "execution_error": row["adjudication_error"]})
            print(
                f"[{position:02d}/30] {case['id']} | ERROR DE EJECUCIÓN: "
                f"{type(exc).__name__}: {exc}"
            )

    total_elapsed = time.perf_counter() - total_start
    output_dir = Path("output") / "evidence_verifier_v3_30"
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "evidence_verifier_v3_30_results.csv"
    json_path = output_dir / "evidence_verifier_v3_30_details.json"

    fieldnames = list(rows[0].keys())
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "verifier_version": verifier.VERSION,
                "adjudication_model": verifier.adjudication_model,
                "ollama_url": verifier.ollama_url,
                "total_cases": len(TEST_CASES),
                "total_elapsed_seconds": round(total_elapsed, 3),
                "results": details,
            },
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 76)
    print("RESUMEN")
    print("=" * 76)
    print(f"Casos ejecutados: {len(rows)}")
    print(f"Correctos: {sum(bool(row['correct']) for row in rows)}")
    print(f"Incorrectos / errores: {sum(not bool(row['correct']) for row in rows)}")
    print(f"Tiempo total: {total_elapsed:.2f} segundos")

    print("\nRESULTADOS POR CATEGORÍA")
    for category in dict.fromkeys(case["category"] for case in TEST_CASES):
        category_rows = [row for row in rows if row["category"] == category]
        correct = sum(bool(row["correct"]) for row in category_rows)
        print(f"{category}: {correct}/{len(category_rows)}")

    print("\nRESULTADOS POR MODELO")
    qwen_available = sum(row["adjudication_available"] is True for row in rows)
    print(f"Adjudicaciones Qwen disponibles: {qwen_available}/{len(rows)}")

    nli_rows = [
        row for row in rows
        if all(row[key] is not None for key in (
            "nli_entailment", "nli_neutral", "nli_contradiction"
        ))
    ]
    if nli_rows:
        nli_argmax_correct = 0
        for row in nli_rows:
            nli_label = max(
                (
                    ("SUPPORTED", row["nli_entailment"]),
                    ("INSUFFICIENT", row["nli_neutral"]),
                    ("CONTRADICTED", row["nli_contradiction"]),
                ),
                key=lambda pair: pair[1],
            )[0]
            if nli_label == row["expected"]:
                nli_argmax_correct += 1
        print(
            f"mDeBERTa argmax frente a etiqueta esperada: "
            f"{nli_argmax_correct}/{len(nli_rows)}"
        )

    print("\nARCHIVOS GENERADOS")
    print(csv_path.resolve())
    print(json_path.resolve())
    print("\nNOTA: batería controlada; 30 casos no constituyen una validación general.")
    print("Revisar manualmente los casos incorrectos y la calidad de las etiquetas esperadas.")


if __name__ == "__main__":
    main()
