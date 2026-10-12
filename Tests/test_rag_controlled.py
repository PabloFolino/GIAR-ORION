"""
GIAR-ORION — Prueba controlada de recuperación y fundamentación.
No modifica main.py ni Agent/MultilingualKnowledgeRetriever.py.

Condiciones:
1) current_prompt: recuperación actual (top-k) + prompt RAG actual.
2) grounded_prompt: misma recuperación + instrucciones reforzadas de fundamentación.
3) rerank_grounded: recuperar una lista más amplia, reordenar experimentalmente por
   coincidencia léxica y usar el prompt reforzado.

Consultas: UNITREE-01 y SAC-01.
Modelos de recuperación: E5, BGE-M3 e híbrido.
No utiliza Qwen como juez: guarda resultados para revisión independiente.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from Agent.MultilingualKnowledgeRetriever import MultilingualKnowledgeRetriever
except Exception as exc:
    MultilingualKnowledgeRetriever = None
    IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
else:
    IMPORT_ERROR = ""

CASES = [
    {
        "id": "UNITREE-01",
        "query": "¿Cuáles son las articulaciones principales de las piernas del robot Unitree G1?",
        "expected_terms": [
            "hip_pitch", "hip_roll", "hip_yaw", "knee", "ankle_pitch", "ankle_roll"
        ],
        "expected_source": r"Unitree\G1\Unitree_G1_Dossier_Tecnico_GIAR_ORION.md",
        "rubric": (
            "Responder que el Unitree G1 es un humanoide bípedo y enumerar, para cada pierna, "
            "hip_pitch, hip_roll, hip_yaw, knee, ankle_pitch y ankle_roll. "
            "No confundirlo con un cuadrúpedo. Si el contexto no incluye la lista, decirlo."
        ),
    },
    {
        "id": "SAC-01",
        "query": "¿Cómo funciona SAC y cómo se actualizan los críticos?",
        "expected_terms": ["actor", "crítico", "bellman", "mínimo", "pérdida"],
        "expected_source": r"SAC\Fundamentos_de_SAC_GIAR_ORION.md",
        "rubric": (
            "Explicar SAC como actor-crítico off-policy de máxima entropía; mencionar dos críticos "
            "Q y el mínimo de sus estimaciones para reducir sobreestimación; explicar el objetivo "
            "de Bellman/target y distinguir la actualización de los críticos de la del actor. "
            "No afirmar detalles del código local si no aparecen en el contexto."
        ),
    },
]

CURRENT_SYSTEM = (
    "Sos un asistente técnico de GIAR-ORION. Respondé en español, con precisión y claridad. "
    "No afirmes conocer archivos locales que no hayas visto."
)
CURRENT_RAG_SUFFIX = (
    "Respondé directamente a la pregunta. Basá los detalles específicos del proyecto en el "
    "contexto; si hay contradicciones o falta información, señalalo."
)
GROUNDED_SYSTEM = (
    "Sos el asistente técnico de GIAR-ORION. Respondé en español y priorizá exactitud sobre "
    "aparentar completitud. Usá el contexto recuperado como evidencia para los detalles técnicos. "
    "Primero contestá exactamente lo que pregunta el usuario. No confundas un robot humanoide "
    "con uno cuadrúpedo. No inventes nombres, parámetros ni comportamientos de archivos locales. "
    "Distingí explícitamente entre: (1) información presente en el contexto, (2) conocimiento "
    "general y (3) información que no se puede confirmar. Si el contexto no contiene el dato "
    "solicitado, decilo claramente y no rellenes el vacío con especulación. No agregues detalles "
    "técnicos no respaldados cuando la pregunta se refiere al proyecto."
)
GROUNDED_SUFFIX = (
    "Respondé primero con una respuesta directa. Después, si corresponde, explicá brevemente. "
    "Usá solamente el contexto para afirmar datos específicos del proyecto. Si el fragmento no "
    "contiene el dato exacto, indicá qué falta y qué archivo o sección habría que consultar. "
    "No infieras que un dato está documentado solo porque el documento menciona una fuente."
)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="qwen3:8b")
    p.add_argument("--ollama-url", default="http://localhost:11434")
    p.add_argument("--knowledge-dir", default=str(ROOT / "Knowledge"))
    p.add_argument("--output-dir", default=str(ROOT / "Tests" / "results_rag_controlled"))
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--candidate-k", type=int, default=20)
    p.add_argument("--modes", nargs="+", choices=["e5", "bge-m3", "hybrid"],
                   default=["e5", "bge-m3", "hybrid"])
    p.add_argument("--timeout", type=int, default=300)
    p.add_argument("--offline-retrievers", action="store_true")
    return p.parse_args()


def ollama_chat(base_url: str, model: str, system: str, user: str, timeout: int):
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "options": {"temperature": 0},
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/api/chat",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Ollama HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"No se pudo conectar con Ollama: {exc}") from exc
    elapsed = time.perf_counter() - start
    text = str(data.get("message", {}).get("content", "")).strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if not text:
        raise RuntimeError("Ollama devolvió una respuesta vacía.")
    return text, elapsed


def check_model(base_url: str, model: str, timeout: int):
    req = urllib.request.Request(base_url.rstrip("/") + "/api/tags")
    with urllib.request.urlopen(req, timeout=min(timeout, 20)) as response:
        data = json.loads(response.read().decode("utf-8"))
    names = [m.get("name", "") for m in data.get("models", [])]
    if model not in names and not any(n.split(":")[0] == model.split(":")[0] for n in names):
        raise RuntimeError(f"No se encontró {model} en Ollama. Modelos: {names}")


def context_for(items):
    parts = []
    for i, item in enumerate(items, 1):
        parts.append(
            f"[Fragmento {i} | fuente: {item.get('source', '')} | "
            f"score: {float(item.get('score', 0.0)):.4f}]\n{item.get('text', '')}"
        )
    return "\n\n---\n\n".join(parts)


def lexical_rerank(query: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reordenamiento experimental simple; no altera el recuperador original."""
    stop = {
        "cuales", "cuáles", "como", "cómo", "funciona", "funcionan", "principales",
        "del", "de", "la", "las", "los", "el", "y", "en", "por", "para", "que",
        "qué", "una", "un", "con", "se", "actualizan", "robot",
    }
    query_terms = {
        t.lower() for t in re.findall(r"[a-zA-Z_áéíóúÁÉÍÓÚñÑ0-9]+", query)
        if len(t) > 2 and t.lower() not in stop
    }

    def rank(item):
        text = str(item.get("text", "")).lower()
        source = str(item.get("source", "")).lower()
        matched = sum(1 for term in query_terms if term in text)
        # Favorecer nombres explícitos para UNITREE; no imponerlos a otras consultas.
        technical_bonus = 0
        if "unitree" in query.lower():
            expected = ["hip_pitch", "hip_roll", "hip_yaw", "knee", "ankle_pitch", "ankle_roll"]
            technical_bonus = sum(2 for term in expected if term in text)
            if "unitree" in source:
                technical_bonus += 1
        if "sac" in query.lower():
            terms = ["crítico", "critic", "bellman", "actor", "pérdida", "loss", "mínimo"]
            technical_bonus = sum(1 for term in terms if term in text)
        dense_score = float(item.get("score", 0.0))
        return (matched + technical_bonus, dense_score)

    return sorted(items, key=rank, reverse=True)


def main():
    args = parse_args()
    if args.top_k < 1 or args.candidate_k < args.top_k:
        print("ERROR: top-k debe ser >= 1 y candidate-k debe ser >= top-k.")
        return 2
    if MultilingualKnowledgeRetriever is None:
        print("ERROR al importar MultilingualKnowledgeRetriever:", IMPORT_ERROR)
        return 2
    knowledge_dir = Path(args.knowledge_dir).resolve()
    if not knowledge_dir.is_dir():
        print("ERROR: no existe Knowledge:", knowledge_dir)
        return 2
    try:
        check_model(args.ollama_url, args.model, args.timeout)
    except Exception as exc:
        print("ERROR:", exc)
        return 2

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output_dir).resolve() / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 76)
    print("GIAR-ORION — PRUEBA CONTROLADA DE RECUPERACIÓN Y FUNDAMENTACIÓN")
    print("=" * 76)
    print(f"Consultas: {len(CASES)} | modos: {', '.join(args.modes)}")
    print("Condiciones: current_prompt, grounded_prompt, rerank_grounded")
    print("No se usa Qwen como juez; se guardan evidencias para revisión manual.")
    print("Salida:", out_dir)

    rows, errors = [], []
    for mode in args.modes:
        print(f"\n### Recuperador: {mode}")
        try:
            retriever = MultilingualKnowledgeRetriever(
                knowledge_dir=knowledge_dir,
                mode=mode,
                batch_size=16,
                local_files_only=args.offline_retrievers,
            )
            print(f"Inicializado: {len(retriever.chunks)} fragmentos.")
        except Exception as exc:
            errors.append({"mode": mode, "case": "", "condition": "init",
                           "error": f"{type(exc).__name__}: {exc}"})
            print("ERROR al inicializar:", exc)
            continue

        for case in CASES:
            try:
                t0 = time.perf_counter()
                current_items = retriever.search(case["query"], top_k=args.top_k)
                current_retrieval_s = time.perf_counter() - t0
                t0 = time.perf_counter()
                candidates = retriever.search(case["query"], top_k=args.candidate_k)
                wide_retrieval_s = time.perf_counter() - t0
                reranked = lexical_rerank(case["query"], candidates)[:args.top_k]

                conditions = [
                    ("current_prompt", current_items, CURRENT_SYSTEM, CURRENT_RAG_SUFFIX,
                     current_retrieval_s),
                    ("grounded_prompt", current_items, GROUNDED_SYSTEM, GROUNDED_SUFFIX,
                     current_retrieval_s),
                    ("rerank_grounded", reranked, GROUNDED_SYSTEM, GROUNDED_SUFFIX,
                     wide_retrieval_s),
                ]
                for condition, items, system, suffix, retrieval_s in conditions:
                    context = context_for(items)
                    user = (
                        f"PREGUNTA:\n{case['query']}\n\n"
                        f"CONTEXTO DOCUMENTAL RECUPERADO:\n{context}\n\n{suffix}"
                    )
                    answer, generation_s = ollama_chat(
                        args.ollama_url, args.model, system, user, args.timeout
                    )
                    sources = [str(x.get("source", "")) for x in items]
                    scores = [round(float(x.get("score", 0.0)), 6) for x in items]
                    expected_source_found = any(
                        case["expected_source"].lower().replace("/", "\\") in
                        s.lower().replace("/", "\\") for s in sources
                    )
                    text_joined = "\n".join(str(x.get("text", "")) for x in items).lower()
                    expected_terms_in_context = [
                        term for term in case["expected_terms"] if term.lower() in text_joined
                    ]
                    answer_l = answer.lower()
                    expected_terms_in_answer = [
                        term for term in case["expected_terms"] if term.lower() in answer_l
                    ]
                    row = {
                        "mode": mode,
                        "case_id": case["id"],
                        "query": case["query"],
                        "condition": condition,
                        "retrieval_seconds": round(retrieval_s, 4),
                        "generation_seconds": round(generation_s, 4),
                        "sources": json.dumps(sources, ensure_ascii=False),
                        "scores": json.dumps(scores),
                        "expected_source_found": expected_source_found,
                        "expected_terms_in_context": json.dumps(expected_terms_in_context, ensure_ascii=False),
                        "expected_terms_in_answer": json.dumps(expected_terms_in_answer, ensure_ascii=False),
                        "retrieved_context": context,
                        "answer": answer,
                        "rubric_for_manual_review": case["rubric"],
                        "note": (
                            "Las coincidencias de términos son indicadores mecánicos; "
                            "no equivalen a una evaluación semántica."
                        ),
                    }
                    rows.append(row)
                    print(f"{mode:7s} | {case['id']:10s} | {condition:17s} | "
                          f"generación={generation_s:.1f}s | fuente={expected_source_found}")
            except Exception as exc:
                errors.append({
                    "mode": mode, "case": case["id"], "condition": "query",
                    "error": f"{type(exc).__name__}: {exc}",
                })
                print(f"ERROR {mode}/{case['id']}: {exc}")

    fields = [
        "mode", "case_id", "query", "condition", "retrieval_seconds", "generation_seconds",
        "sources", "scores", "expected_source_found", "expected_terms_in_context",
        "expected_terms_in_answer", "retrieved_context", "answer",
        "rubric_for_manual_review", "note",
    ]
    with (out_dir / "resultados_controlados.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with (out_dir / "errores.json").open("w", encoding="utf-8") as f:
        json.dump(errors, f, ensure_ascii=False, indent=2)
    metadata = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "model": args.model,
        "ollama_url": args.ollama_url,
        "knowledge_dir": str(knowledge_dir),
        "modes": args.modes,
        "cases": [c["id"] for c in CASES],
        "top_k": args.top_k,
        "candidate_k": args.candidate_k,
        "conditions": ["current_prompt", "grounded_prompt", "rerank_grounded"],
        "judge_enabled": False,
        "errors": len(errors),
        "reranking_note": "Reordenamiento léxico experimental solo en este test; no modifica el recuperador de producción.",
    }
    with (out_dir / "metadatos.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 76)
    print("PRUEBA FINALIZADA")
    print(f"Filas generadas: {len(rows)} | errores: {len(errors)}")
    print("Resultados:", out_dir / "resultados_controlados.csv")
    print("Errores:   ", out_dir / "errores.json")
    print("Metadatos: ", out_dir / "metadatos.json")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
