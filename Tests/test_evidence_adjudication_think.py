"""
GIAR-ORION - Diagnóstico aislado de adjudicación Qwen3
Compara think=True y think=False con el mismo prompt, afirmación y evidencias.
No modifica EvidenceVerifier.py ni los componentes del proyecto.

Ejecutar desde la carpeta raíz de GIAR-ORION:
    python test_evidence_adjudication_think.py

Antes de ejecutar, reemplazar CLAIM y EVIDENCE_ITEMS por una afirmación
y las evidencias reales de una consulta de GIAR-ORION.
"""

import json
import time
import urllib.request

from Agent.EvidenceVerifier import EvidenceVerifier

# Sustituir por la afirmación y evidencias reales de una ejecución de ORION.
CLAIM = (
    "En Soft Actor-Critic, el parámetro alpha controla la importancia "
    "del término de entropía en el objetivo de la política."
)
EVIDENCE_ITEMS = [
    {
        "source": "EVIDENCIA_DE_PRUEBA_1",
        "text": (
            "In Soft Actor-Critic, the temperature parameter alpha determines "
            "the relative importance of the entropy term against the reward "
            "in the policy objective."
        ),
    },
    {
        "source": "EVIDENCIA_DE_PRUEBA_2",
        "text": (
            "The entropy term encourages exploration by favoring policies "
            "with higher entropy."
        ),
    },
]

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen3:8b"
TIMEOUT_SECONDS = 180


def build_prompt(verifier):
    """Replica la construcción del prompt de EvidenceVerifier 0.3.3."""
    numbered = [
        {"id": i, "source": str(item.get("source", "")), "text": item["text"]}
        for i, item in enumerate(EVIDENCE_ITEMS)
    ]
    terminology = verifier._select_terminology(CLAIM, EVIDENCE_ITEMS)
    terminology_block = (
        "RELEVANT TERMINOLOGY FROM THE PROJECT GLOSSARY (context only; "
        "do not treat topical similarity as evidence):\n"
        + json.dumps(terminology, ensure_ascii=False)
        + "\n\n"
        if terminology
        else "RELEVANT TERMINOLOGY: no glossary entry matched the supplied claim/evidence.\n\n"
    )
    prompt = (
        "You are a strict evidence-verification component. Judge ONLY the supplied evidence; "
        "do not use outside knowledge and do not infer missing facts.\n"
        "For each evidence item return exactly one label:\n"
        "SUPPORTED = the evidence directly states or clearly entails the whole claim.\n"
        "CONTRADICTED = the evidence directly states an incompatible fact about the SAME "
        "subject, property and conditions.\n"
        "INSUFFICIENT = related topic, different component/aspect, partial support, "
        "or no information sufficient to decide. Lack of mention is NOT contradiction.\n"
        "Terminology and paraphrases may be equivalent across Spanish and English. "
        "Recognize synonyms only when the meaning is genuinely equivalent. "
        "Do not treat mere topical similarity as support.\n"
        "In the context of the Soft Actor-Critic (SAC) algorithm, "
        "'alpha' (α), 'entropy temperature', and "
        "'entropy temperature coefficient' refer to the same parameter: "
        "the coefficient that weights the entropy term in the policy objective. "
        "Treat these terms as equivalent when evaluating evidence about SAC.\n"
        "Return one item for every evidence id, exactly once. Reasons must be in Spanish and no longer than 20 words.\n\n"
        f"{terminology_block}"
        f"CLAIM:\n{CLAIM}\n\nEVIDENCE ITEMS:\n"
        f"{json.dumps(numbered, ensure_ascii=False)}"
    )
    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "minimum": 0},
                        "label": {
                            "type": "string",
                            "enum": ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT"],
                        },
                        "reason": {"type": "string", "maxLength": 240},
                    },
                    "required": ["id", "label", "reason"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["items"],
        "additionalProperties": False,
    }
    return prompt, schema, terminology


def run_case(label, think, prompt, schema):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": schema,
        "think": think,
        "options": {"temperature": 0, "num_predict": 700},
    }
    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        body = json.loads(response.read().decode("utf-8"))
    wall_time = time.perf_counter() - started

    message = body.get("message", {})
    raw = message.get("content", "") if isinstance(message, dict) else ""
    thinking = message.get("thinking", "") if isinstance(message, dict) else ""
    parsed, validation_error = None, None
    try:
        parsed = json.loads(raw)
        rows = parsed.get("items") if isinstance(parsed, dict) else None
        if not isinstance(rows, list) or len(rows) != len(EVIDENCE_ITEMS):
            raise ValueError("Cantidad de clasificaciones distinta de la cantidad de evidencias.")
        ids = [row.get("id") for row in rows if isinstance(row, dict)]
        if sorted(ids) != list(range(len(EVIDENCE_ITEMS))):
            raise ValueError(f"IDs incompletos o duplicados: {ids}")
        allowed = {"SUPPORTED", "CONTRADICTED", "INSUFFICIENT"}
        if any(row.get("label") not in allowed for row in rows):
            raise ValueError("Etiqueta no permitida.")
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        validation_error = f"{type(exc).__name__}: {exc}"

    def seconds(key):
        value = body.get(key)
        return round(value / 1_000_000_000, 3) if isinstance(value, (int, float)) else None

    return {
        "test": label,
        "think_requested": think,
        "wall_time_seconds": round(wall_time, 3),
        "ollama_total_seconds": seconds("total_duration"),
        "load_seconds": seconds("load_duration"),
        "prompt_eval_seconds": seconds("prompt_eval_duration"),
        "generation_seconds": seconds("eval_duration"),
        "prompt_tokens": body.get("prompt_eval_count"),
        "generated_tokens": body.get("eval_count"),
        "thinking_characters": len(thinking),
        "done_reason": body.get("done_reason"),
        "json_valid": validation_error is None,
        "validation_error": validation_error,
        "adjudication": parsed,
        "thinking_preview": thinking[:500],
    }


def main():
    verifier = EvidenceVerifier(
        ollama_url=OLLAMA_URL,
        adjudication_model=MODEL,
        use_ollama_adjudication=False,
    )
    prompt, schema, terminology = build_prompt(verifier)
    print("=" * 68)
    print("DIAGNÓSTICO DE ADJUDICACIÓN QWEN3")
    print(f"Modelo: {MODEL}")
    print(f"Afirmación: {CLAIM}")
    print(f"Evidencias: {len(EVIDENCE_ITEMS)}")
    print(f"Términos de glosario: {len(terminology)}")
    print(f"Caracteres del prompt: {len(prompt)}")
    print("=" * 68)
    print("Mismo prompt y JSON Schema; primero think=True y luego think=False.")

    results = []
    for label, think in (("A - THINK ACTIVADO", True), ("B - THINK DESACTIVADO", False)):
        print(f"\nEjecutando {label}...")
        try:
            result = run_case(label, think, prompt, schema)
            results.append(result)
            print(
                f"Tiempo: {result['wall_time_seconds']} s | "
                f"Generación: {result['generation_seconds']} s | "
                f"Tokens: {result['generated_tokens']} | "
                f"Thinking: {result['thinking_characters']} caracteres | "
                f"JSON válido: {result['json_valid']}"
            )
            if result["validation_error"]:
                print("Error:", result["validation_error"])
            else:
                print("Adjudicación:", json.dumps(result["adjudication"], ensure_ascii=False))
        except Exception as exc:
            print(f"ERROR: {type(exc).__name__}: {exc}")
            results.append({"test": label, "error": f"{type(exc).__name__}: {exc}"})

    with open("test_evidence_adjudication_think_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\nResultados guardados en test_evidence_adjudication_think_results.json")

    if len(results) == 2 and all("wall_time_seconds" in r for r in results):
        a, b = results
        if b["wall_time_seconds"] > 0:
            print(f"Relación de tiempos A/B: {a['wall_time_seconds'] / b['wall_time_seconds']:.2f}x")
        print(f"¿Adjudicaciones idénticas?: {a.get('adjudication') == b.get('adjudication')}")


if __name__ == "__main__":
    main()
