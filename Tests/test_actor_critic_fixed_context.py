# -*- coding: utf-8 -*-
"""
Prueba independiente de generación con evidencia RAG fija.
No modifica los archivos de producción ni los experimentos anteriores.
"""

import csv
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

QUERY = (
    "Explica qué es la política del agente en aprendizaje por refuerzo, "
    "qué función cumple la función de valor y cómo se relacionan ambas "
    "en una arquitectura Actor-Critic."
)

SYSTEM_PROMPT = """Sos GIAR-ORION, un asistente técnico especializado en robótica y aprendizaje por refuerzo.
Respondé en español, con precisión y de forma directa.
Usá únicamente la evidencia proporcionada en los fragmentos.
No inventes datos ni completes con conocimiento externo.
Si la evidencia no alcanza para responder, señalá esa limitación.
Entregá una respuesta técnica verificable."""


def consultar_ollama(base_url, model, prompt):
    payload = {
        "model": model,
        "stream": False,
        "think": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "options": {
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

    inicio = time.perf_counter()

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            data = json.loads(response.read().decode("utf-8"))

        return {
            "status": "OK",
            "answer": data.get("message", {}).get("content", ""),
            "elapsed_seconds": round(time.perf_counter() - inicio, 3),
            "error": "",
        }

    except Exception as exc:
        return {
            "status": "ERROR",
            "answer": "",
            "elapsed_seconds": round(time.perf_counter() - inicio, 3),
            "error": f"{type(exc).__name__}: {exc}",
        }


def main():
    config_path = ROOT / "config.json"

    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    rag = config.get("rag", {})
    paths = config.get("paths", {})

    knowledge_dir = Path(paths.get("knowledge", "Knowledge"))
    if not knowledge_dir.is_absolute():
        knowledge_dir = ROOT / knowledge_dir

    model = config.get("model", "qwen3:8b")
    base_url = config.get("base_url", "http://localhost:11434")

    print("Inicializando recuperador híbrido...")

    from Agent.MultilingualKnowledgeRetriever import (
        MultilingualKnowledgeRetriever,
    )

    retriever = MultilingualKnowledgeRetriever(
        knowledge_dir=str(knowledge_dir),
        mode=rag.get("mode", "hybrid"),
        device=rag.get("device", "cpu"),
        e5_weight=float(rag.get("e5_weight", 0.7)),
        bge_weight=float(rag.get("bge_weight", 0.3)),
        local_files_only=bool(rag.get("local_files_only", False)),
    )

    resultados = retriever.search(
        QUERY,
        top_k=int(rag.get("top_k", 5)),
    )

    if not resultados:
        raise RuntimeError("El recuperador no devolvió fragmentos.")

    fragmentos = []

    for posicion, resultado in enumerate(resultados, start=1):
        fragmentos.append({
            "rank": posicion,
            "source": str(resultado.get("source", "")),
            "score": resultado.get("score", ""),
            "text": resultado.get("text", ""),
        })

    partes = [
        "CONSULTA DEL USUARIO:",
        QUERY,
        "",
        "EVIDENCIA RECUPERADA:",
    ]

    for fragmento in fragmentos:
        partes.extend([
            "",
            f"--- FRAGMENTO {fragmento['rank']} "
            f"| archivo={fragmento['source']} "
            f"| score={fragmento['score']} ---",
            fragmento["text"],
            f"--- FIN FRAGMENTO {fragmento['rank']} ---",
        ])

    partes.extend([
        "",
        "Respondé basándote exclusivamente en estos fragmentos. "
        "Indicá expresamente si falta evidencia para alguna parte.",
    ])

    prompt = "\n".join(partes)

    # Crear un directorio nuevo para no sobrescribir resultados.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = (
        ROOT / "Tests" / "results_actor_critic_fixed_context" / timestamp
    )
    output_dir.mkdir(parents=True, exist_ok=False)

    # Guardar la evidencia antes de llamar al modelo.
    evidencia = {
        "query": QUERY,
        "model": model,
        "temperature": 0.0,
        "seed": 42,
        "system_prompt": SYSTEM_PROMPT,
        "user_prompt": prompt,
        "fragments": fragmentos,
    }

    (output_dir / "evidencia.json").write_text(
        json.dumps(evidencia, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Archivo reutilizable para entregar la misma evidencia a ChatGPT.
    (output_dir / "contexto_para_comparacion.txt").write_text(
        "INSTRUCCIÓN DE SISTEMA:\n"
        + SYSTEM_PROMPT
        + "\n\nPROMPT:\n"
        + prompt,
        encoding="utf-8",
    )

    print(f"Modelo: {model}")
    print(f"Fragmentos: {len(fragmentos)}")

    for fragmento in fragmentos:
        print(
            f"{fragmento['rank']}. {fragmento['source']} "
            f"| score={fragmento['score']}"
        )

    print("\nConsultando Ollama...")
    respuesta = consultar_ollama(base_url, model, prompt)

    resultado_final = {
        "query": QUERY,
        "model": model,
        "temperature": 0.0,
        "seed": 42,
        **respuesta,
    }

    (output_dir / "respuesta_qwen.json").write_text(
        json.dumps(resultado_final, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nEstado: {respuesta['status']}")

    if respuesta["status"] == "OK":
        print("\n===== RESPUESTA DE QWEN =====\n")
        print(respuesta["answer"])
    else:
        print(respuesta["error"])

    print("\nResultados guardados en:")
    print(output_dir)

    return 0 if respuesta["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())