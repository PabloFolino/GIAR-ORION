# -*- coding: utf-8 -*-
"""
GIAR-ORION
Experimento de fidelidad de generación.

Compara:
    1. Prompt actual.
    2. Prompt estricto.

Características:
    - Tres preguntas de prueba.
    - Evidencia RAG recuperada una sola vez por pregunta.
    - Mismos fragmentos para todas las condiciones.
    - Modos rápido e investigación.
    - Temperatura 0.0 y semilla 42.
    - No modifica archivos de producción.
"""

import json
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path


# ============================================================
# 1. RUTAS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CONFIG_FILE = ROOT / "config.json"


# ============================================================
# 2. PROMPTS
# ============================================================

SYSTEM_PROMPT = """Sos GIAR-ORION, un asistente técnico especializado en robótica y aprendizaje por refuerzo.
Respondé en español, con precisión y de forma directa.
Usá únicamente la evidencia proporcionada en los fragmentos.
No inventes datos ni completes con conocimiento externo.
Si la evidencia no alcanza para responder, señalá esa limitación.
Entregá una respuesta técnica verificable."""


STRICT_RULES = """REGLAS ESTRICTAS DE FIDELIDAD A LA EVIDENCIA

1. Cada afirmación técnica debe estar respaldada por los fragmentos proporcionados.
2. No agregues detalles técnicos basados en conocimiento externo, aunque sean generalmente correctos.
3. No infieras relaciones causales que la evidencia no establezca.
4. Conservá la precisión de los términos técnicos utilizados en las fuentes.
5. Si una definición está incompleta, no la completes por tu cuenta. Indicá qué información falta.
6. Diferenciá explícitamente los hechos documentados de las inferencias. Si no necesitás inferir, no agregues inferencias.
7. Priorizá la precisión y la cobertura de la consulta por encima de la extensión de la respuesta.
8. No afirmes que una característica mejora la estabilidad, precisión o rendimiento si los fragmentos no lo respaldan."""


PROMPTS = {
    "actual": SYSTEM_PROMPT,
    "estricto": SYSTEM_PROMPT + "\n\n" + STRICT_RULES,
}


# ============================================================
# 3. PREGUNTAS
# ============================================================

QUESTIONS = [
    {
        "id": "Q1_actor_critic",
        "query": (
            "Explica qué es la política del agente en aprendizaje por "
            "refuerzo, qué función cumple la función de valor y cómo se "
            "relacionan ambas en una arquitectura Actor-Critic."
        ),
    },
    {
        "id": "Q2_sac",
        "query": (
            "Según la documentación disponible, ¿qué es SAC y cuáles son "
            "las características que lo distinguen como algoritmo de "
            "aprendizaje por refuerzo?"
        ),
    },
    {
        "id": "Q3_critic_sac",
        "query": (
            "Según la documentación disponible, ¿qué función cumple el "
            "crítico en SAC y cómo contribuye al aprendizaje de la política "
            "del actor?"
        ),
    },
]


# ============================================================
# 4. ARCHIVOS JSON
# ============================================================

def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ============================================================
# 5. CONSTRUCCIÓN DEL PROMPT DE USUARIO
# ============================================================

def build_prompt(query, fragments):
    parts = [
        "CONSULTA DEL USUARIO:",
        query,
        "",
        "EVIDENCIA RECUPERADA:",
    ]

    for fragment in fragments:
        parts.extend([
            "",
            (
                f"--- FRAGMENTO {fragment['rank']} "
                f"| archivo={fragment['source']} "
                f"| score={fragment['score']} ---"
            ),
            fragment["text"],
            f"--- FIN FRAGMENTO {fragment['rank']} ---",
        ])

    parts.extend([
        "",
        (
            "Respondé basándote exclusivamente en estos fragmentos. "
            "Indicá expresamente si falta evidencia para alguna parte."
        ),
    ])

    return "\n".join(parts)


# ============================================================
# 6. COMUNICACIÓN CON OLLAMA
# ============================================================

def call_ollama(base_url, model, messages, parameters):
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": parameters["think"],
        "options": {
            "num_predict": parameters["num_predict"],
            "temperature": 0.0,
            "seed": 42,
        },
    }

    request = urllib.request.Request(
        base_url.rstrip("/") + "/api/chat",
        data=json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    started = time.perf_counter()

    try:
        with urllib.request.urlopen(
            request,
            timeout=300,
        ) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        message = data.get("message", {})

        return {
            "status": "OK",
            "answer": message.get("content", ""),
            "thinking": message.get("thinking", ""),
            "elapsed_seconds_wall": round(
                time.perf_counter() - started,
                3,
            ),
            "total_duration_ns": data.get(
                "total_duration"
            ),
            "load_duration_ns": data.get(
                "load_duration"
            ),
            "prompt_eval_count": data.get(
                "prompt_eval_count"
            ),
            "prompt_eval_duration_ns": data.get(
                "prompt_eval_duration"
            ),
            "eval_count": data.get("eval_count"),
            "eval_duration_ns": data.get(
                "eval_duration"
            ),
            "done_reason": data.get("done_reason"),
            "error": "",
        }

    except Exception as exc:
        return {
            "status": "ERROR",
            "answer": "",
            "thinking": "",
            "elapsed_seconds_wall": round(
                time.perf_counter() - started,
                3,
            ),
            "error": (
                f"{type(exc).__name__}: {exc}"
            ),
        }


# ============================================================
# 7. EJECUCIÓN DEL EXPERIMENTO
# ============================================================

def main():
    config = load_json(CONFIG_FILE)

    rag = config["rag"]
    llm = config["llm"]
    modes = config["generation"]["modes"]

    paths = config.get("paths", {})

    knowledge_dir = Path(
        paths.get("knowledge", "Knowledge")
    )

    if not knowledge_dir.is_absolute():
        knowledge_dir = ROOT / knowledge_dir

    # Importamos el recuperador existente.
    # No modificamos su implementación.
    from Agent.MultilingualKnowledgeRetriever import (
        MultilingualKnowledgeRetriever,
    )

    print("=" * 72)
    print("GIAR-ORION - EXPERIMENTO DE FIDELIDAD")
    print("=" * 72)

    print("Modelo:", llm["model"])
    print("Recuperador:", rag.get("mode", "hybrid"))
    print("Top K:", rag.get("top_k", 5))

    print("\nInicializando recuperador híbrido...")

    retriever = MultilingualKnowledgeRetriever(
        knowledge_dir=str(knowledge_dir),
        mode=rag.get("mode", "hybrid"),
        device=rag.get("device", "cpu"),
        e5_weight=float(
            rag.get("e5_weight", 0.7)
        ),
        bge_weight=float(
            rag.get("bge_weight", 0.3)
        ),
        local_files_only=bool(
            rag.get("local_files_only", False)
        ),
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_dir = (
        ROOT
        / "Tests"
        / "results_prompt_fidelity_comparison"
        / timestamp
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    summary = {
        "timestamp": timestamp,
        "model": llm["model"],
        "base_url": llm["base_url"],
        "rag_mode": rag.get("mode", "hybrid"),
        "top_k": int(rag.get("top_k", 5)),
        "e5_weight": float(
            rag.get("e5_weight", 0.7)
        ),
        "bge_weight": float(
            rag.get("bge_weight", 0.3)
        ),
        "temperature": 0.0,
        "seed": 42,
        "conditions": {
            "actual": SYSTEM_PROMPT,
            "estricto": PROMPTS["estricto"],
        },
        "questions": [],
    }

    # Se alterna el orden de los prompts entre modos.
    # Esto reduce parcialmente posibles efectos del orden.
    execution_order = {
        "rapido": [
            "actual",
            "estricto",
        ],
        "investigacion": [
            "estricto",
            "actual",
        ],
    }

    total = len(QUESTIONS) * 4
    execution = 0

    # --------------------------------------------------------
    # Procesar preguntas
    # --------------------------------------------------------

    for question in QUESTIONS:
        query_id = question["id"]
        query = question["query"]

        print("\n" + "=" * 72)
        print(query_id)
        print(query)

        # La recuperación se ejecuta una sola vez por pregunta.
        print("\nRecuperando evidencia una sola vez...")

        retrieved = retriever.search(
            query,
            top_k=summary["top_k"],
        )

        fragments = []

        for rank, item in enumerate(
            retrieved or [],
            start=1,
        ):
            fragments.append({
                "rank": rank,
                "source": str(
                    item.get("source", "")
                ),
                "score": item.get("score", ""),
                "text": item.get("text", ""),
            })

        question_dir = output_dir / query_id

        question_dir.mkdir(
            parents=True,
            exist_ok=False,
        )

        user_prompt = build_prompt(
            query,
            fragments,
        )

        # Guardamos la evidencia exacta que recibirán
        # las cuatro generaciones.
        save_json(
            question_dir / "evidencia.json",
            {
                "id": query_id,
                "query": query,
                "user_prompt": user_prompt,
                "fragments": fragments,
            },
        )

        question_result = {
            "id": query_id,
            "query": query,
            "status": (
                "OK" if fragments else "RAG_EMPTY"
            ),
            "fragment_count": len(fragments),
            "results": {},
        }

        print(
            "Fragmentos recuperados:",
            len(fragments),
        )

        for fragment in fragments:
            print(
                f"  {fragment['rank']}. "
                f"{fragment['source']} "
                f"| score={fragment['score']}"
            )

        if not fragments:
            print(
                "ERROR: no hay evidencia. "
                "Se omiten las generaciones de esta pregunta."
            )

            save_json(
                question_dir / "resultado.json",
                question_result,
            )

            summary["questions"].append(
                question_result
            )

            continue

        # ----------------------------------------------------
        # Generar con ambos prompts y ambos modos
        # ----------------------------------------------------

        for mode_name in (
            "rapido",
            "investigacion",
        ):
            parameters = modes[mode_name]

            for condition in execution_order[
                mode_name
            ]:
                execution += 1

                print("\n" + "-" * 72)
                print(
                    f"[{execution}/{total}] "
                    f"{query_id} | "
                    f"modo={mode_name} | "
                    f"prompt={condition}"
                )

                print(
                    f"think={parameters['think']} | "
                    f"num_predict={parameters['num_predict']}"
                )

                messages = [
                    {
                        "role": "system",
                        "content": PROMPTS[condition],
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ]

                result = call_ollama(
                    base_url=llm["base_url"],
                    model=llm["model"],
                    messages=messages,
                    parameters=parameters,
                )

                result["condition"] = condition
                result["mode"] = mode_name

                result["parameters"] = {
                    "think": parameters["think"],
                    "num_predict": parameters[
                        "num_predict"
                    ],
                    "temperature": 0.0,
                    "seed": 42,
                }

                result["system_prompt"] = (
                    PROMPTS[condition]
                )

                result["user_prompt"] = user_prompt

                result_key = (
                    f"{condition}_{mode_name}"
                )

                question_result["results"][
                    result_key
                ] = result

                save_json(
                    question_dir
                    / f"{result_key}.json",
                    result,
                )

                print("Estado:", result["status"])

                if result["status"] == "OK":
                    print(
                        "Tiempo:",
                        result["elapsed_seconds_wall"],
                        "s",
                    )

                    print(
                        "Tokens generados:",
                        result.get("eval_count"),
                    )

                    print("\nRespuesta:")
                    print(result["answer"])

                else:
                    print("Error:", result["error"])

        save_json(
            question_dir / "resultado.json",
            question_result,
        )

        summary["questions"].append(
            question_result
        )

    # --------------------------------------------------------
    # Resumen general
    # --------------------------------------------------------

    save_json(
        output_dir / "resumen.json",
        summary,
    )

    print("\n" + "=" * 72)
    print("EXPERIMENTO FINALIZADO")
    print("Directorio:", output_dir)
    print("Resumen:", output_dir / "resumen.json")
    print("=" * 72)


if __name__ == "__main__":
    main()