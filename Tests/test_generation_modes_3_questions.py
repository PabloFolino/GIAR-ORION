# -*- coding: utf-8 -*-
"""Compara los modos de generación usando evidencia RAG fija."""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
CONFIG_FILE = ROOT / "config.json"

SYSTEM_PROMPT = """Sos GIAR-ORION, un asistente técnico especializado en robótica y aprendizaje por refuerzo.
Respondé en español, con precisión y de forma directa.
Usá únicamente la evidencia proporcionada en los fragmentos.
No inventes datos ni completes con conocimiento externo.
Si la evidencia no alcanza para responder, señalá esa limitación.
Entregá una respuesta técnica verificable."""

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


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.perf_counter()

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            data = json.loads(response.read().decode("utf-8"))

        message = data.get("message", {})

        return {
            "status": "OK",
            "answer": message.get("content", ""),
            "thinking": message.get("thinking", ""),
            "elapsed_seconds_wall": round(
                time.perf_counter() - started, 3
            ),
            "total_duration_ns": data.get("total_duration"),
            "load_duration_ns": data.get("load_duration"),
            "prompt_eval_count": data.get("prompt_eval_count"),
            "prompt_eval_duration_ns": data.get(
                "prompt_eval_duration"
            ),
            "eval_count": data.get("eval_count"),
            "eval_duration_ns": data.get("eval_duration"),
            "done_reason": data.get("done_reason"),
            "error": "",
        }

    except Exception as exc:
        return {
            "status": "ERROR",
            "answer": "",
            "thinking": "",
            "elapsed_seconds_wall": round(
                time.perf_counter() - started, 3
            ),
            "error": f"{type(exc).__name__}: {exc}",
        }


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
            f"--- FRAGMENTO {fragment['rank']} "
            f"| archivo={fragment['source']} "
            f"| score={fragment['score']} ---",
            fragment["text"],
            f"--- FIN FRAGMENTO {fragment['rank']} ---",
        ])

    parts.extend([
        "",
        "Respondé basándote exclusivamente en estos fragmentos. "
        "Indicá expresamente si falta evidencia para alguna parte.",
    ])

    return "\n".join(parts)


def main():
    config = load_json(CONFIG_FILE)
    rag = config["rag"]
    llm = config["llm"]
    modes = config["generation"]["modes"]

    paths = config.get("paths", {})
    knowledge_dir = Path(paths.get("knowledge", "Knowledge"))

    if not knowledge_dir.is_absolute():
        knowledge_dir = ROOT / knowledge_dir

    from Agent.MultilingualKnowledgeRetriever import (
        MultilingualKnowledgeRetriever,
    )

    print("Inicializando recuperador híbrido...")

    retriever = MultilingualKnowledgeRetriever(
        knowledge_dir=str(knowledge_dir),
        mode=rag.get("mode", "hybrid"),
        device=rag.get("device", "cpu"),
        e5_weight=float(rag.get("e5_weight", 0.7)),
        bge_weight=float(rag.get("bge_weight", 0.3)),
        local_files_only=bool(rag.get("local_files_only", False)),
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = (
        ROOT / "Tests" / "results_generation_modes_3q" / timestamp
    )
    output_dir.mkdir(parents=True, exist_ok=False)

    summary = {
        "timestamp": timestamp,
        "model": llm["model"],
        "rag_mode": rag.get("mode", "hybrid"),
        "top_k": int(rag.get("top_k", 5)),
        "e5_weight": float(rag.get("e5_weight", 0.7)),
        "bge_weight": float(rag.get("bge_weight", 0.3)),
        "temperature": 0.0,
        "seed": 42,
        "questions": [],
    }

    total = len(QUESTIONS) * 2
    execution = 0

    for question in QUESTIONS:
        query_id = question["id"]
        query = question["query"]

        print("\n" + "=" * 70)
        print(f"{query_id}: {query}")
        print("Recuperando evidencia una sola vez...")

        retrieved = retriever.search(
            query,
            top_k=summary["top_k"],
        )

        if not retrieved:
            print("ERROR: el recuperador no devolvió fragmentos.")
            summary["questions"].append({
                "id": query_id,
                "query": query,
                "status": "RAG_EMPTY",
                "fragments": [],
                "modes": {},
            })
            continue

        fragments = []

        for rank, item in enumerate(retrieved, start=1):
            fragments.append({
                "rank": rank,
                "source": str(item.get("source", "")),
                "score": item.get("score", ""),
                "text": item.get("text", ""),
            })

        user_prompt = build_prompt(query, fragments)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        question_dir = output_dir / query_id
        question_dir.mkdir(parents=True, exist_ok=False)

        save_json(question_dir / "evidencia.json", {
            "id": query_id,
            "query": query,
            "system_prompt": SYSTEM_PROMPT,
            "user_prompt": user_prompt,
            "fragments": fragments,
        })

        question_result = {
            "id": query_id,
            "query": query,
            "status": "OK",
            "fragments": fragments,
            "modes": {},
        }

        print(f"Fragmentos recuperados: {len(fragments)}")
        for fragment in fragments:
            print(
                f"  {fragment['rank']}. {fragment['source']} "
                f"| score={fragment['score']}"
            )

        for mode_name in ("rapido", "investigacion"):
            execution += 1
            parameters = modes[mode_name]

            print(
                f"\n[{execution}/{total}] {query_id} - {mode_name}"
                f" | think={parameters['think']}"
                f" | num_predict={parameters['num_predict']}"
            )

            result = call_ollama(
                base_url=llm["base_url"],
                model=llm["model"],
                messages=messages,
                parameters=parameters,
            )

            result["parameters"] = {
                "think": parameters["think"],
                "num_predict": parameters["num_predict"],
                "temperature": 0.0,
                "seed": 42,
            }

            question_result["modes"][mode_name] = result
            save_json(question_dir / f"{mode_name}.json", result)

            print(f"Estado: {result['status']}")
            if result["status"] == "OK":
                print(f"Tiempo: {result['elapsed_seconds_wall']} s")
                print(f"Tokens generados: {result.get('eval_count')}")
                print(f"Finalización: {result.get('done_reason')}")
                print("Respuesta:")
                print(result["answer"])
            else:
                print(f"Error: {result['error']}")

        save_json(question_dir / "resultado.json", question_result)
        summary["questions"].append(question_result)

    save_json(output_dir / "resumen.json", summary)

    print("\n" + "=" * 70)
    print("PRUEBA FINALIZADA")
    print(f"Resultados: {output_dir}")
    print(f"Resumen: {output_dir / 'resumen.json'}")
    print("=" * 70)


if __name__ == "__main__":
    main()

