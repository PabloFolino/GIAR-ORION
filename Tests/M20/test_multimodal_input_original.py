"""
Prueba del esquema de entrada multimodal de GIAR-ORION (M20).

Estructura esperada:
    GIAR-ORION/
    ├── schemas/M20/MultimodalInput.schema.json
    └── Tests/test_multimodal_input.py

Ejecución desde la raíz del proyecto:
    python Tests/test_multimodal_input.py

Dependencia:
    python -m pip install jsonschema
"""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


# Tests está directamente dentro de la raíz de GIAR-ORION.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

SCHEMA_PATH = (
    PROJECT_ROOT
    / "schemas"
    / "M20"
    / "MultimodalInput.schema.json"
)


def load_validator():
    """Carga el esquema y comprueba que sea un JSON Schema válido."""
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(
            f"No se encontró el esquema JSON: {SCHEMA_PATH}"
        )

    with SCHEMA_PATH.open("r", encoding="utf-8") as file:
        schema = json.load(file)

    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def run_test(validator, name, data, expected_valid):
    """Ejecuta un caso y compara el resultado con el esperado."""
    errors = sorted(
        validator.iter_errors(data),
        key=lambda error: list(error.absolute_path)
    )

    is_valid = not errors
    passed = is_valid == expected_valid

    print(f"[{'OK' if passed else 'FALLO'}] {name}")

    for error in errors:
        location = "/".join(str(part) for part in error.absolute_path)
        print(f"    {location or '<raíz>'}: {error.message}")

    return passed


def main():
    print("GIAR-ORION - Test de entrada multimodal")
    print(f"Esquema: {SCHEMA_PATH}")
    print("-" * 60)

    try:
        validator = load_validator()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR al cargar o comprobar el esquema: {error}")
        return 2

    cases = [
        (
            "Entrada válida con texto",
            {
                "modality": "text",
                "items": [
                    {"type": "text", "content": "Analizar esta información."}
                ]
            },
            True
        ),
        (
            "Entrada válida con referencia a imagen",
            {
                "modality": "image",
                "items": [
                    {"type": "image", "reference": "data/images/imagen_001.png"}
                ]
            },
            True
        ),
        (
            "Entrada válida con texto e imagen",
            {
                "modality": "multimodal",
                "items": [
                    {"type": "text", "content": "Describe la imagen."},
                    {"type": "image", "reference": "data/images/imagen_001.png"}
                ],
                "metadata": {"source": "test_multimodal_input"}
            },
            True
        ),
        (
            "Entrada inválida sin modality",
            {
                "items": [{"type": "text", "content": "Texto de prueba."}]
            },
            False
        ),
        (
            "Entrada inválida con items vacío",
            {"modality": "text", "items": []},
            False
        ),
        (
            "Entrada inválida sin content ni reference",
            {"modality": "text", "items": [{"type": "text"}]},
            False
        ),
        (
            "Entrada inválida con content null",
            {
                "modality": "text",
                "items": [{"type": "text", "content": None}]
            },
            False
        )
    ]

    results = [
        run_test(validator, name, data, expected)
        for name, data, expected in cases
    ]

    passed = sum(results)
    failed = len(results) - passed

    print("-" * 60)
    print(f"Pruebas correctas: {passed}/{len(cases)}")
    print(f"Pruebas fallidas:  {failed}/{len(cases)}")

    if failed:
        print("RESULTADO: HAY PRUEBAS FALLIDAS")
        return 1

    print("RESULTADO: TODAS LAS PRUEBAS PASARON")
    return 0


if __name__ == "__main__":
    sys.exit(main())
