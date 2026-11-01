"""
Prueba final de integración real:
ClaimExtractor (Ollama/Qwen3:8b) + EvidenceVerifier (NLI/CUDA)
orquestados por ClaimVerificationPipeline.

Ejecutar desde la raíz de GIAR-ORION:
    .venv\Scripts\python.exe Tests\test_integracion_final_pipeline.py

No usa mocks. Ejecuta dos escenarios:
1) Varias afirmaciones con evidencia de respaldo, contradicción e insuficiencia.
2) Evidencia deliberadamente contradictoria para una misma afirmación.

Los resultados NLI se registran, no se fuerzan: las expectativas son
orientativas y cualquier discrepancia debe analizarse como REVIEW.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Agent.ClaimVerificationPipeline import ClaimVerificationPipeline


def print_claims(report):
    verification = report.get("verification") or {}
    checks = verification.get("checks") or {}
    semantic = checks.get("semantic_support_check") or {}
    claims = semantic.get("claims") or []

    if not claims:
        print("  No hay resultados individuales de claims.")
        return

    for item in claims:
        print(
            "  - "
            + str(item.get("claim"))
            + " => "
            + str(item.get("status"))
            + " | entailment="
            + str(item.get("best_entailment_score"))
            + " | contradiction="
            + str(item.get("best_contradiction_score"))
        )


def main():
    pipeline = ClaimVerificationPipeline()

    # ESCENARIO 1:
    # Incluye afirmaciones diseñadas para producir respaldo, contradicción,
    # insuficiencia y un enunciado compuesto cuyo respaldo puede ser parcial.
    response_1 = (
        "La Tierra orbita alrededor del Sol. "
        "La Tierra tiene dos lunas naturales. "
        "La Tierra es el centro del sistema solar. "
        "La Tierra posee un satélite natural llamado Luna y su diámetro "
        "medio es de 12.742 kilómetros."
    )

    rag_1 = [
        {
            "source": "Astronomia - órbita terrestre",
            "text": (
                "La Tierra orbita alrededor del Sol. Los planetas del "
                "sistema solar orbitan alrededor del Sol."
            ),
        },
        {
            "source": "Astronomia - satélite natural",
            "text": (
                "La Tierra tiene un único satélite natural conocido, "
                "la Luna. La Luna es el satélite natural de la Tierra."
            ),
        },
    ]

    print("=" * 78)
    print("ESCENARIO 1: RESPALDO, CONTRADICCIÓN, INSUFICIENCIA Y RESPALDO PARCIAL")
    print("=" * 78)

    report_1 = pipeline.run(response_1, rag_results=rag_1)
    print("Pipeline status:", report_1.get("status"))
    print("Semantic status:", report_1.get("semantic_status"))
    print("Reference status:", report_1.get("reference_status"))
    print("Claims extraídos:", report_1.get("claims_submitted"))
    print("Extracción completa:", (report_1.get("extraction") or {}).get("complete"))
    print("Resultados individuales:")
    print_claims(report_1)

    print("\n" + "=" * 78)
    print("ESCENARIO 2: EVIDENCIA CONTRADICTORIA")
    print("=" * 78)

    response_2 = "La Tierra tiene dos lunas naturales."
    rag_2 = [
        {
            "source": "Fuente A - astronomía",
            "text": (
                "La Tierra tiene un único satélite natural conocido, "
                "la Luna."
            ),
        },
        {
            "source": "Fuente B - afirmación opuesta",
            "text": "La Tierra tiene dos lunas naturales.",
        },
    ]

    report_2 = pipeline.run(response_2, rag_results=rag_2)
    print("Pipeline status:", report_2.get("status"))
    print("Semantic status:", report_2.get("semantic_status"))
    print("Reference status:", report_2.get("reference_status"))
    print("Claims extraídos:", report_2.get("claims_submitted"))
    print("Extracción completa:", (report_2.get("extraction") or {}).get("complete"))
    print("Resultados individuales:")
    print_claims(report_2)

    # Guardar informes completos para auditoría y revisión posterior.
    output_dir = ROOT / "output" / "Pipeline"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "integracion_final_report.json"

    final_report = {
        "test": "ClaimExtractor + EvidenceVerifier + ClaimVerificationPipeline",
        "test_timestamp": datetime.now().astimezone().isoformat(),
        "pipeline_version": pipeline.VERSION,
        "scenarios": {
            "mixed_evidence": report_1,
            "conflicting_evidence": report_2,
        },
        "test_limitations": [
            "La evidencia es sintética y controlada; no mide confiabilidad en fuentes reales.",
            "El escenario de respaldo parcial depende de cómo Qwen atomice el enunciado y de la inferencia NLI.",
            "El escenario contradictorio comprueba la respuesta del NLI ante dos fragmentos opuestos, no la veracidad externa de las fuentes.",
            "Esta prueba usa evidencias RAG; no evalúa recuperación DDGS ni descarga de páginas web.",
            "Los resultados NLI no son probabilidades calibradas ni certificaciones científicas.",
        ],
    }

    output_file.write_text(
        json.dumps(final_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n" + "=" * 78)
    print("RESUMEN DE EJECUCIÓN")
    print("=" * 78)
    print("Escenario 1 ejecutado: PASS (ejecución completada)")
    print("Escenario 2 ejecutado: PASS (ejecución completada)")
    print("Informe completo:", output_file)
    print(
        "Nota: PASS indica que el escenario se ejecutó; la calidad de cada "
        "clasificación debe juzgarse por los estados observados."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR EN LA PRUEBA: {type(exc).__name__}: {exc}")
        raise
