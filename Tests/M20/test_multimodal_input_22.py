"""
GIAR-ORION - M20
Ejecutor de 22 casos de prueba para MultimodalInput.schema.json.

Ubicaciones esperadas:
    Tests/M20/test_multimodal_input.py
    Tests/M20/MultimodalInput_test_cases_22.json
    Tests/Shemas/M20/MultimodalInput.schema.json

Ejecución desde la raíz de GIAR-ORION:
    python Tests/M20/test_multimodal_input.py

Dependencia:
    python -m pip install jsonschema
"""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

# Este script está en GIAR-ORION/Tests/M20/.
# parent.parent apunta a GIAR-ORION/Tests/.
TESTS_ROOT = Path(__file__).resolve().parent.parent

SCHEMA_PATH = (
    TESTS_ROOT
    / "Shemas"
    / "M20"
    / "MultimodalInput.schema.json"
)

CASES_PATH = (
    Path(__file__).resolve().parent
    / "MultimodalInput_test_cases_22.json"
)


def load_json(path):
    if not path.is_file():
        raise FileNotFoundError(f"No se encontró el archivo: {path}")
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main():
    print("GIAR-ORION - M20 - Test de entrada multimodal")
    print(f"Esquema: {SCHEMA_PATH}")
    print(f"Casos:   {CASES_PATH}")
    print("-" * 72)

    try:
        schema = load_json(SCHEMA_PATH)
        suite = load_json(CASES_PATH)
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR al cargar o comprobar archivos: {error}")
        return 2

    results = []

    for case in suite["cases"]:
        errors = sorted(
            validator.iter_errors(case["data"]),
            key=lambda error: (
                list(map(str, error.absolute_path)),
                error.message
            )
        )

        actual_valid = not errors
        expected_valid = case["expected_valid"]
        passed = actual_valid == expected_valid
        results.append(passed)

        print(f"[{'PASS' if passed else 'FAIL'}] {case['id']} - {case['name']}")

        if not passed:
            if errors:
                for error in errors:
                    location = (
                        "/".join(str(part) for part in error.absolute_path)
                        or "<raíz>"
                    )
                    print(f"       {location}: {error.message}")
            else:
                print(
                    "       Se esperaba que el documento fuera inválido, "
                    "pero fue aceptado."
                )

    total = len(suite["cases"])
    passed_count = sum(results)
    failed_count = total - passed_count
    positive = sum(
        1 for case in suite["cases"] if case["expected_valid"]
    )
    negative = total - positive

    print("-" * 72)
    print(f"Casos positivos:    {positive}")
    print(f"Casos negativos:    {negative}")
    print(f"Pruebas correctas:  {passed_count}/{total}")
    print(f"Pruebas fallidas:   {failed_count}/{total}")

    if failed_count:
        print("RESULTADO GENERAL: HAY PRUEBAS FALLIDAS")
        return 1

    print("RESULTADO GENERAL: TODAS LAS PRUEBAS PASARON")
    return 0


if __name__ == "__main__":
    sys.exit(main())
