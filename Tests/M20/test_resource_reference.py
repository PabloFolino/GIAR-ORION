"""
GIAR-ORION M20 - Validación exhaustiva ResourceReference + MultimodalInput.

Estructura esperada:
  Tests/M20/test_resource_reference.py
  Tests/M20/ResourceReference_test_cases_40.json
  Tests/Schemas/M20/ResourceReference.schema.json
  Tests/Schemas/M20/MultimodalInput.schema.json

Ejecutar desde la raíz:
  python Tests/M20/test_resource_reference.py

Dependencia:
  python -m pip install jsonschema
"""
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

HERE = Path(__file__).resolve().parent
TESTS_ROOT = HERE.parent
SCHEMAS_DIR = TESTS_ROOT / "Schemas" / "M20"
RESOURCE_SCHEMA_PATH = SCHEMAS_DIR / "ResourceReference.schema.json"
MULTIMODAL_SCHEMA_PATH = SCHEMAS_DIR / "MultimodalInput.schema.json"
CASES_PATH = HERE / "ResourceReference_test_cases_40.json"
RESOURCE_SCHEMA_ID = "urn:giar-orion:schema:resource-reference:1.0"


def load_json(path):
    if not path.is_file():
        raise FileNotFoundError(f"No se encontró: {path}")
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def main():
    print("GIAR-ORION - M20 - ResourceReference / MultimodalInput")
    print(f"Resource schema:  {RESOURCE_SCHEMA_PATH}")
    print(f"Multimodal schema: {MULTIMODAL_SCHEMA_PATH}")
    print(f"Test cases:       {CASES_PATH}")
    print("=" * 78)

    try:
        resource_schema = load_json(RESOURCE_SCHEMA_PATH)
        multimodal_schema = load_json(MULTIMODAL_SCHEMA_PATH)
        suite = load_json(CASES_PATH)
        Draft202012Validator.check_schema(resource_schema)
        Draft202012Validator.check_schema(multimodal_schema)
        registry = Registry().with_resource(
            RESOURCE_SCHEMA_ID, Resource.from_contents(resource_schema)
        )
        resource_validator = Draft202012Validator(resource_schema)
        multimodal_validator = Draft202012Validator(
            multimodal_schema, registry=registry
        )
    except Exception as exc:
        print(f"ERROR DE CONFIGURACIÓN: {type(exc).__name__}: {exc}")
        return 2

    failures = []
    positives = negatives = 0
    for case in suite["cases"]:
        if case["id"].startswith("RR-"):
            validator = resource_validator
        elif case["id"].startswith("MMI-"):
            validator = multimodal_validator
        else:
            failures.append((case["id"], "Prefijo de caso desconocido"))
            continue

        errors = sorted(
            validator.iter_errors(case["data"]),
            key=lambda e: (list(map(str, e.absolute_path)), e.message)
        )
        actual = not errors
        expected = case["expected_valid"]
        if expected:
            positives += 1
        else:
            negatives += 1

        passed = actual == expected
        print(f"[{'PASS' if passed else 'FAIL'}] {case['id']} - {case['name']}")
        if not passed:
            failures.append((case["id"], case["name"]))
            for error in errors:
                path = "/".join(map(str, error.absolute_path)) or "<raíz>"
                print(f"       {path}: {error.message}")
            if not errors:
                print("       El esquema aceptó un caso que debía rechazar.")

    total = len(suite["cases"])
    print("=" * 78)
    print(f"Casos positivos:   {positives}")
    print(f"Casos negativos:   {negatives}")
    print(f"Total:             {total}")
    print(f"Correctos:         {total - len(failures)}/{total}")
    print(f"Fallidos:          {len(failures)}")

    if failures:
        print("RESULTADO: FAIL")
        return 1
    print("RESULTADO: PASS - TODOS LOS CASOS SUPERADOS")
    print("Nota: valida estructura JSON Schema; no prueba existencia del recurso,")
    print("resolución real de URI, autorización, integridad del archivo ni acceso físico.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
