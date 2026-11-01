"""
Suite integral de pruebas para Agent/ClaimExtractor.py

Ejecutar desde la raíz de GIAR-ORION:
    python .\Tests\test_claim_extractor_completo.py

Realiza:
1. Pruebas deterministas de validación, segmentación y JSON.
2. Pruebas de integración reales contra Ollama/qwen3:8b.
3. Informe JSON y resumen de resultados.

Importante:
- Las pruebas de integración evalúan el comportamiento observado del LLM.
- No prueban que las afirmaciones extraídas sean verdaderas.
- "complete=True" sólo acredita cobertura estructural, no exhaustividad semántica.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Agent.ClaimExtractor import (  # noqa: E402
    ClaimExtractor,
    ClaimExtractorError,
)

BASE_URL = "http://localhost:11434"
MODEL = "qwen3:8b"

results: list[dict[str, Any]] = []


def record(test_id: str, category: str, status: str, detail: str = "") -> None:
    results.append({
        "id": test_id,
        "category": category,
        "status": status,
        "detail": detail,
    })
    print(f"[{status}] {test_id} - {detail}")


def deterministic_test(test_id, fn):
    try:
        detail = fn()
        record(test_id, "deterministic", "PASS", str(detail or ""))
    except Exception as exc:
        record(test_id, "deterministic", "FAIL", f"{type(exc).__name__}: {exc}")


def expect_raises(expected, fn):
    try:
        fn()
    except expected:
        return f"Se produjo {expected.__name__} como se esperaba."
    raise AssertionError(f"Se esperaba {expected.__name__}.")


def run_deterministic_tests():
    # D01-D05: validación de parámetros.
    deterministic_test("D01_constructor_valido", lambda:
        ClaimExtractor(BASE_URL, MODEL).model)

    deterministic_test("D02_base_url_vacia", lambda:
        expect_raises(ValueError, lambda: ClaimExtractor("", MODEL)))

    deterministic_test("D03_modelo_vacio", lambda:
        expect_raises(ValueError, lambda: ClaimExtractor(BASE_URL, "")))

    deterministic_test("D04_num_predict_invalido", lambda:
        expect_raises(ValueError, lambda: ClaimExtractor(BASE_URL, MODEL, num_predict=0)))

    deterministic_test("D05_timeout_invalido", lambda:
        expect_raises(ValueError, lambda: ClaimExtractor(BASE_URL, MODEL, timeout=-1)))

    # D06-D08: segmentación.
    deterministic_test("D06_segmentacion_dos_oraciones", lambda:
        _assert_equal(
            ClaimExtractor._split_units("SAC es off-policy. El Actor produce acciones."),
            ["SAC es off-policy.", "El Actor produce acciones."]
        ))

    deterministic_test("D07_ignora_lineas_vacias", lambda:
        _assert_equal(
            ClaimExtractor._split_units("Primera afirmación.\n\nSegunda afirmación."),
            ["Primera afirmación.", "Segunda afirmación."]
        ))

    deterministic_test("D08_texto_vacio_sin_unidades", lambda:
        _assert_equal(ClaimExtractor._split_units(" \n "), []))

    # D09-D11: parser JSON.
    deterministic_test("D09_json_directo", lambda:
        _assert_equal(ClaimExtractor._extract_json('{"coverage": [], "notes": []}')["coverage"], []))

    deterministic_test("D10_json_en_fence", lambda:
        _assert_equal(
            ClaimExtractor._extract_json('```json\n{"coverage": [], "notes": []}\n```')["coverage"],
            []
        ))

    deterministic_test("D11_json_malformado", lambda:
        expect_raises(ClaimExtractorError, lambda: ClaimExtractor._extract_json("esto no es json")))

    # D12-D17: validador de estructura.
    one_unit = ["SAC es off-policy."]
    valid = {"coverage": [{"unit_id": 1, "status": "FACTUAL",
                          "claims": ["SAC es off-policy."]}], "notes": []}

    deterministic_test("D12_validacion_correcta", lambda:
        _assert_true(ClaimExtractor._validate_extraction(one_unit, valid, MODEL)["complete"]))

    deterministic_test("D13_detecta_unidad_omitida", lambda:
        _assert_false(ClaimExtractor._validate_extraction(
            ["Una.", "Dos."],
            {"coverage": [{"unit_id": 1, "status": "FACTUAL", "claims": ["Una."]}], "notes": []},
            MODEL
        )["complete"]))

    deterministic_test("D14_detecta_id_duplicado", lambda:
        _assert_false(ClaimExtractor._validate_extraction(
            one_unit,
            {"coverage": [
                {"unit_id": 1, "status": "FACTUAL", "claims": ["Una."]},
                {"unit_id": 1, "status": "FACTUAL", "claims": ["Una."]}],
             "notes": []},
            MODEL
        )["complete"]))

    deterministic_test("D15_detecta_status_invalido", lambda:
        _assert_false(ClaimExtractor._validate_extraction(
            one_unit,
            {"coverage": [{"unit_id": 1, "status": "UNKNOWN", "claims": []}], "notes": []},
            MODEL
        )["complete"]))

    deterministic_test("D16_detecta_factual_sin_claims", lambda:
        _assert_false(ClaimExtractor._validate_extraction(
            one_unit,
            {"coverage": [{"unit_id": 1, "status": "FACTUAL", "claims": []}], "notes": []},
            MODEL
        )["complete"]))

    deterministic_test("D17_detecta_nonfactual_con_claims", lambda:
        _assert_false(ClaimExtractor._validate_extraction(
            ["¿Qué es SAC?"],
            {"coverage": [{"unit_id": 1, "status": "NON_FACTUAL",
                           "claims": ["SAC es un algoritmo."]}], "notes": []},
            MODEL
        )["complete"]))


def _assert_equal(actual, expected):
    if actual != expected:
        raise AssertionError(f"Obtenido: {actual!r}; esperado: {expected!r}")
    return "Resultado coincidente."


def _assert_true(value):
    if not value:
        raise AssertionError("Se esperaba True.")
    return "Valor True."


def _assert_false(value):
    if value:
        raise AssertionError("Se esperaba False.")
    return "Valor False."


LIVE_CASES = [
    {
        "id": "L01_texto_tecnico_simple",
        "text": "SAC es un algoritmo off-policy. Su Actor genera acciones mediante una distribución probabilística.",
        "min_claims": 2,
        "max_claims": 5,
        "expected_units": 2,
        "purpose": "Dos afirmaciones técnicas explícitas."
    },
    {
        "id": "L02_oracion_compuesta",
        "text": "SAC es off-policy y utiliza un replay buffer para reutilizar experiencias; además, optimiza una política estocástica.",
        "min_claims": 3,
        "max_claims": 7,
        "expected_units": 1,
        "purpose": "Separación de varias afirmaciones dentro de una oración."
    },
    {
        "id": "L03_pregunta",
        "text": "¿Qué es Soft Actor-Critic y cómo aprende su política?",
        "min_claims": 0,
        "max_claims": 0,
        "expected_units": 1,
        "purpose": "No convertir preguntas en afirmaciones."
    },
    {
        "id": "L04_opinion",
        "text": "En mi opinión, SAC es el mejor algoritmo para cualquier robot.",
        "min_claims": 0,
        "max_claims": 2,
        "expected_units": 1,
        "purpose": "Distinguir opinión de afirmaciones factuales."
    },
    {
        "id": "L05_negacion",
        "text": "SAC no es un algoritmo on-policy. SAC utiliza aprendizaje basado en datos almacenados en un replay buffer.",
        "min_claims": 2,
        "max_claims": 5,
        "expected_units": 2,
        "purpose": "Preservar negación y contenido afirmativo."
    },
    {
        "id": "L06_datos_numericos",
        "text": "La red Actor recibe un vector de estado de 48 valores y produce 12 parámetros de acción. El entrenamiento se ejecutó durante 300 episodios.",
        "min_claims": 3,
        "max_claims": 6,
        "expected_units": 2,
        "purpose": "Conservar cantidades y relaciones numéricas."
    },
    {
        "id": "L07_condicional",
        "text": "Si la entropía objetivo aumenta, el ajuste automático puede modificar el coeficiente alpha. Cuando alpha aumenta, cambia el peso del término de entropía en el objetivo del Actor.",
        "min_claims": 2,
        "max_claims": 6,
        "expected_units": 2,
        "purpose": "No convertir condiciones en hechos universales."
    },
    {
        "id": "L08_causa_y_consecuencia",
        "text": "La normalización de las observaciones limita diferencias de escala entre variables. Esto puede mejorar la estabilidad del entrenamiento.",
        "min_claims": 2,
        "max_claims": 5,
        "expected_units": 2,
        "purpose": "Separar afirmación y consecuencia potencial."
    },
    {
        "id": "L09_no_factual_mixto",
        "text": "Configuración recomendada para la prueba. ¿Conviene aumentar el tamaño del replay buffer? No modificar todavía el código.",
        "min_claims": 0,
        "max_claims": 2,
        "expected_units": 3,
        "purpose": "Títulos, preguntas e instrucciones."
    },
    {
        "id": "L10_parrafo_extenso",
        "text": (
            "Soft Actor-Critic es un algoritmo de aprendizaje por refuerzo off-policy. "
            "Su arquitectura incluye un Actor y dos redes Critic. El Actor representa una política "
            "estocástica y genera una distribución de acciones. Las redes Critic estiman valores "
            "Q para pares estado-acción. El algoritmo incorpora un término de entropía en su "
            "función objetivo para favorecer la exploración."
        ),
        "min_claims": 5,
        "max_claims": 10,
        "expected_units": 5,
        "purpose": "Cobertura de un párrafo técnico con varias unidades."
    },
    {
        "id": "L11_citas_y_atribucion",
        "text": "Según el registro de entrenamiento, el episodio 25 terminó con una recompensa de -12.4. El archivo SAC.py contiene la implementación del algoritmo.",
        "min_claims": 2,
        "max_claims": 4,
        "expected_units": 2,
        "purpose": "Afirmaciones atribuidas a una fuente o archivo."
    },
    {
        "id": "L12_ingles_tecnico",
        "text": "Soft Actor-Critic is an off-policy reinforcement learning algorithm. Its actor represents a stochastic policy and outputs action distribution parameters.",
        "min_claims": 2,
        "max_claims": 5,
        "expected_units": 2,
        "purpose": "Texto técnico en inglés."
    },
]


def run_live_tests():
    print("\nConectando con Ollama para pruebas de integración...")
    extractor = ClaimExtractor(BASE_URL, MODEL, timeout=180)

    for case in LIVE_CASES:
        try:
            result = extractor.extract(case["text"])
            units = result.get("unit_count", -1)
            count = result.get("claim_count", -1)
            complete = result.get("complete") is True

            problems = []
            if not complete:
                problems.append("complete=False")
            if units != case["expected_units"]:
                problems.append(
                    f"unidades={units}, esperadas={case['expected_units']}"
                )
            if not (case["min_claims"] <= count <= case["max_claims"]):
                problems.append(
                    f"claims={count}, rango esperado="
                    f"{case['min_claims']}-{case['max_claims']}"
                )

            status = "PASS" if not problems else "REVIEW"
            detail = (
                f"units={units}; claims={count}; complete={complete}; "
                f"esperado={case['min_claims']}-{case['max_claims']}; "
                f"{case['purpose']}"
            )
            if problems:
                detail += "; OBSERVACIONES: " + ", ".join(problems)

            record(case["id"], "ollama_integration", status, detail)
            case["result"] = result
        except Exception as exc:
            record(
                case["id"],
                "ollama_integration",
                "ERROR",
                f"{type(exc).__name__}: {exc}"
            )
            case["exception"] = traceback.format_exc()


def main():
    print("=" * 72)
    print("GIAR-ORION | CLAIM EXTRACTOR v0.1.1 | SUITE INTEGRAL")
    print("=" * 72)

    run_deterministic_tests()
    run_live_tests()

    passed = sum(r["status"] == "PASS" for r in results)
    reviewed = sum(r["status"] == "REVIEW" for r in results)
    failed = sum(r["status"] == "FAIL" for r in results)
    errors = sum(r["status"] == "ERROR" for r in results)

    report = {
        "suite": "ClaimExtractor comprehensive",
        "extractor_version": ClaimExtractor.VERSION,
        "model": MODEL,
        "summary": {
            "total": len(results),
            "passed": passed,
            "review": reviewed,
            "failed": failed,
            "errors": errors,
        },
        "tests": results,
    }

    report_path = ROOT / "Tests" / "claim_extractor_comprehensive_results.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("\n" + "=" * 72)
    print("RESUMEN")
    print("=" * 72)
    print(f"Total:   {len(results)}")
    print(f"PASS:    {passed}")
    print(f"REVIEW:  {reviewed}  (requieren análisis semántico)")
    print(f"FAIL:    {failed}")
    print(f"ERROR:   {errors}")
    print(f"Informe: {report_path}")

    if failed or errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
