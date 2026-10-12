"""
GIAR-ORION — Comparación automática de Qwen3:8B con y sin recuperación (RAG).

Configuraciones:
  A: Qwen3:8B sin consultar Knowledge.
  B: Qwen3:8B + recuperador E5.
  C: Qwen3:8B + recuperador BGE-M3.
  D: Qwen3:8B + recuperador híbrido E5/BGE-M3.

Ubicación recomendada:
  Tests\test_rag_comparison.py

Ejecutar desde la raíz del proyecto (con el entorno .venv activo):
  python Tests\test_rag_comparison.py

Opciones:
  --model qwen3:8b
  --ollama-url http://localhost:11434
  --top-k 5
  --judge              Evalúa automáticamente las respuestas con Qwen.
  --no-judge           Omite la evaluación automática (solo respuestas y tiempos).
  --modes A B C D      Ejecuta solo algunas configuraciones.
  --offline-retrievers Usa únicamente modelos de embeddings en caché local.

La evaluación automática es orientativa: el mismo LLM actúa como juez. Para
decisiones finales, conviene revisar manualmente respuestas y fuentes.
No modifica main.py ni los recuperadores existentes.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import traceback
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from Agent.MultilingualKnowledgeRetriever import MultilingualKnowledgeRetriever
except Exception:
    MultilingualKnowledgeRetriever = None  # A puede ejecutarse sin el módulo de recuperación.


TEST_CASES: list[dict[str, Any]] = [
    {
        "id": "SAC-01",
        "query": "¿Cómo funciona SAC y cómo se actualizan los críticos?",
        "rubric": (
            "Explicar que SAC es un algoritmo actor-crítico off-policy de máxima entropía; "
            "que usa dos críticos Q y normalmente el mínimo de sus estimaciones para reducir "
            "la sobreestimación; describir el objetivo de Bellman/target y distinguirlo de "
            "la actualización de la política. No inventar detalles del código local."
        ),
    },
    {
        "id": "SAC-02",
        "query": "¿Qué función cumple el Replay Buffer durante el entrenamiento de SAC?",
        "rubric": (
            "El Replay Buffer almacena transiciones (estado, acción, recompensa, siguiente "
            "estado y terminación); permite muestrear minibatches y reutilizar experiencias "
            "en un algoritmo off-policy, reduciendo la dependencia de muestras consecutivas."
        ),
    },
    {
        "id": "SAC-03",
        "query": "¿Qué relación existe entre la entropía y la política en Soft Actor-Critic?",
        "rubric": (
            "La política suele ser estocástica; SAC optimiza recompensa y entropía, favoreciendo "
            "exploración/diversidad. El coeficiente alpha regula el compromiso y puede ajustarse "
            "automáticamente. No confundir entropía con la recompensa por sí sola."
        ),
    },
    {
        "id": "RL-01",
        "query": "¿Qué es el aprendizaje por refuerzo y cómo aprende un agente?",
        "rubric": (
            "El agente interactúa con un entorno: observa estado, elige acción, recibe recompensa "
            "y nuevo estado; aprende una política para maximizar la recompensa acumulada. "
            "Puede mencionar MDP, política y exploración/explotación."
        ),
    },
    {
        "id": "DRL-01",
        "query": "¿Qué diferencia hay entre aprendizaje por refuerzo y aprendizaje profundo por refuerzo?",
        "rubric": (
            "RL es el marco general de aprendizaje por interacción y recompensa; DRL combina RL "
            "con redes neuronales profundas para representar políticas, funciones de valor o "
            "procesar observaciones complejas. No son categorías excluyentes."
        ),
    },
    {
        "id": "COPPELIA-01",
        "query": "¿Cómo se configuran las articulaciones y la dinámica física en CoppeliaSim?",
        "rubric": (
            "La respuesta debería distinguir articulaciones cinemáticas y dinámicas, mencionar "
            "modo de control/motor, límites y propiedades dinámicas, cuerpos respondables y "
            "motor físico de simulación. Para valores o pasos concretos de una escena local, "
            "debe reconocer que hacen falta el modelo y su configuración."
        ),
    },
    {
        "id": "UNITREE-01",
        "query": "¿Cuáles son las articulaciones principales de las piernas del robot Unitree G1?",
        "rubric": (
            "Para cada pierna debe identificar cadera/hip pitch, roll y yaw, rodilla/knee y "
            "tobillo/ankle pitch y roll (en el modelo de seis articulaciones por pierna). "
            "Debe distinguir la variante/modelo si el número de DoF difiere."
        ),
    },
    {
        "id": "PYTORCH-01",
        "query": "¿Cómo comprobar si PyTorch puede utilizar la GPU NVIDIA mediante CUDA?",
        "rubric": (
            "Mencionar torch.cuda.is_available(), torch.cuda.get_device_name(0), torch.version.cuda "
            "y, para comprobar uso real, ejecutar una operación/tensor en device='cuda'. "
            "CUDA disponible no demuestra por sí sola que un modelo concreto esté usando la GPU."
        ),
    },
    {
        "id": "ROBOT-01",
        "query": "¿Cómo se relacionan las observaciones, las acciones y la función de recompensa en el control de un robot?",
        "rubric": (
            "Las observaciones describen lo que el agente recibe del robot/entorno; las acciones "
            "son comandos; el entorno evoluciona y devuelve recompensa y siguiente observación. "
            "La recompensa combina señales alineadas con la tarea, con escalas y signos validados."
        ),
    },
    {
        "id": "AGENT-01",
        "query": "¿Cómo se recuperan documentos de la base de conocimientos de GIAR-ORION?",
        "rubric": (
            "En el recuperador multilingüe actual, los Markdown de Knowledge se dividen en "
            "fragmentos, se generan embeddings y se ordenan por similitud; el modo híbrido combina "
            "scores E5 y BGE-M3. No afirmar que este test ya está integrado en main.py."
        ),
    },
]

CONFIGS = {
    "A": {"label": "Qwen solo", "retriever_mode": None},
    "B": {"label": "Qwen + E5", "retriever_mode": "e5"},
    "C": {"label": "Qwen + BGE-M3", "retriever_mode": "bge-m3"},
    "D": {"label": "Qwen + híbrido", "retriever_mode": "hybrid"},
}

GENERATION_SYSTEM = (
    "Sos el asistente técnico GIAR-ORION. Respondé en español, con precisión y de forma "
    "estructurada. Diferenciá hechos generales de información específica del proyecto. "
    "No inventes archivos, parámetros, resultados experimentales ni detalles de una implementación. "
    "Si la información disponible no alcanza para afirmar algo sobre el proyecto, decilo."
)

RAG_SYSTEM = (
    "Sos el asistente técnico GIAR-ORION. Respondé en español usando el CONTEXTO DOCUMENTAL "
    "proporcionado como fuente principal. No afirmes que el contexto dice algo que no aparece "
    "en él. Podés explicar conceptos generales, pero diferenciá claramente esa explicación de "
    "los hechos documentados. Si el contexto no alcanza para responder un detalle del proyecto, "
    "indicá qué falta. No inventes archivos, parámetros ni resultados."
)

JUDGE_SYSTEM = """Sos un evaluador técnico independiente para respuestas de GIAR-ORION.
Evaluá la respuesta frente a la pregunta, los criterios de referencia y, cuando exista,
el contexto recuperado. No premies una respuesta por ser larga. Una respuesta que inventa
detalles del proyecto debe perder puntos. Devolvé exclusivamente un objeto JSON válido con:
correctness (1-5), groundedness (1-5), completeness (1-5), hallucination_risk (1-5),
reason (string). Para hallucination_risk, 1 significa riesgo bajo y 5 riesgo alto.
Los demás puntajes: 1 muy deficiente, 3 parcial/aceptable, 5 muy buena.
Si no hay contexto recuperado (configuración A), groundedness evalúa si distingue
adecuadamente conocimientos generales de datos específicos que no puede conocer."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compara Qwen3:8B solo y Qwen3:8B con E5, BGE-M3 e híbrido."
    )
    parser.add_argument("--model", default="qwen3:8b", help="Nombre del modelo en Ollama.")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="URL base de Ollama.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--modes", nargs="+", choices=["A", "B", "C", "D"],
                        default=["A", "B", "C", "D"])
    parser.add_argument("--judge", dest="judge", action="store_true", default=True,
                        help="Evalúa las respuestas automáticamente con el mismo Qwen (predeterminado).")
    parser.add_argument("--no-judge", dest="judge", action="store_false",
                        help="No usa Qwen como juez; guarda respuestas y tiempos.")
    parser.add_argument("--offline-retrievers", action="store_true",
                        help="No descarga modelos de embeddings; exige que estén en caché.")
    parser.add_argument("--knowledge-dir", default=str(PROJECT_ROOT / "Knowledge"))
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "Tests" / "results_rag_comparison"))
    parser.add_argument("--timeout", type=int, default=300)
    return parser.parse_args()


def ollama_request(
    base_url: str,
    payload: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/api/chat"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"No se pudo conectar con Ollama en {base_url}. "
            "Verificá que Ollama esté iniciado."
        ) from exc


def check_model(base_url: str, model: str, timeout: int) -> None:
    url = base_url.rstrip("/") + "/api/tags"
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=min(timeout, 20)) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(
            f"No se pudo consultar Ollama en {base_url}. Iniciá Ollama y volvé a ejecutar."
        ) from exc
    names = [item.get("name", "") for item in data.get("models", [])]
    if model not in names and not any(name.split(":")[0] == model.split(":")[0] for name in names):
        raise RuntimeError(
            f"No se encontró el modelo '{model}' en Ollama. Modelos detectados: "
            f"{', '.join(names) if names else '(ninguno)'}. "
            f"Descargalo con: ollama pull {model}"
        )


def chat(
    base_url: str,
    model: str,
    system: str,
    user: str,
    timeout: int,
    json_format: bool = False,
) -> tuple[str, float]:
    payload: dict[str, Any] = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "options": {"temperature": 0},
    }
    if json_format:
        payload["format"] = "json"
    start = time.perf_counter()
    try:
        response = ollama_request(base_url, payload, timeout)
    except RuntimeError as exc:
        # Compatibilidad con instalaciones de Ollama que no acepten format=json.
        if json_format and "HTTP 400" in str(exc):
            payload.pop("format", None)
            response = ollama_request(base_url, payload, timeout)
        else:
            raise
    elapsed = time.perf_counter() - start
    message = response.get("message", {})
    text = str(message.get("content", "")).strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if not text:
        raise RuntimeError(f"Ollama devolvió una respuesta vacía: {response}")
    return text, elapsed


def extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    raise ValueError(f"El juez no devolvió JSON válido: {text[:500]}")


def evaluate_answer(
    base_url: str,
    model: str,
    case: dict[str, Any],
    config_label: str,
    answer: str,
    context: str,
    timeout: int,
) -> tuple[dict[str, Any], float]:
    judge_input = {
        "pregunta": case["query"],
        "criterios_de_referencia": case["rubric"],
        "configuracion": config_label,
        "contexto_recuperado": context or "(No se recuperó contexto; configuración sin RAG.)",
        "respuesta_a_evaluar": answer,
    }
    text, elapsed = chat(
        base_url, model, JUDGE_SYSTEM,
        json.dumps(judge_input, ensure_ascii=False, indent=2),
        timeout, json_format=True,
    )
    scores = extract_json(text)
    normalized: dict[str, Any] = {}
    for key in ("correctness", "groundedness", "completeness", "hallucination_risk"):
        try:
            value = int(round(float(scores.get(key, 0))))
        except (TypeError, ValueError):
            value = 0
        normalized[key] = max(1, min(5, value)) if value else 0
    normalized["reason"] = str(scores.get("reason", "")).strip()
    return normalized, elapsed


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_prompt(case: dict[str, Any], context: str, with_rag: bool) -> tuple[str, str]:
    if with_rag:
        user = (
            f"PREGUNTA:\n{case['query']}\n\n"
            f"CONTEXTO DOCUMENTAL RECUPERADO:\n{context}\n\n"
            "Respondé directamente a la pregunta. Basá los detalles específicos del proyecto "
            "en el contexto; si hay contradicciones o falta información, señalalo."
        )
        return RAG_SYSTEM, user
    user = (
        f"PREGUNTA:\n{case['query']}\n\n"
        "Respondé con tus conocimientos. No supongas que conocés el estado actual de los "
        "archivos o de la implementación local de GIAR-ORION. Si la pregunta requiere datos "
        "locales que no están disponibles, explicá esa limitación."
    )
    return GENERATION_SYSTEM, user


def main() -> int:
    args = parse_args()
    if args.top_k < 1 or args.timeout < 1:
        print("ERROR: --top-k y --timeout deben ser mayores que cero.")
        return 2

    knowledge_dir = Path(args.knowledge_dir).resolve()
    if any(mode in {"B", "C", "D"} for mode in args.modes):
        if MultilingualKnowledgeRetriever is None:
            print("ERROR: no se pudo importar Agent.MultilingualKnowledgeRetriever.")
            print("Detalle: verificá la ruta y las dependencias del entorno virtual.")
            return 2
        if not knowledge_dir.is_dir():
            print(f"ERROR: no existe el directorio Knowledge: {knowledge_dir}")
            return 2

    try:
        check_model(args.ollama_url, args.model, args.timeout)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output_dir).resolve() / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 76)
    print("GIAR-ORION — COMPARACIÓN QWEN3:8B / RAG")
    print("=" * 76)
    print(f"Modelo: {args.model}")
    print(f"Ollama: {args.ollama_url}")
    print(f"Configuraciones: {', '.join(args.modes)}")
    print(f"Consultas: {len(TEST_CASES)} | Top-k: {args.top_k}")
    print(f"Evaluación automática con Qwen como juez: {'sí' if args.judge else 'no'}")
    print(f"Salida: {out_dir}")
    print("Aviso: el juez automático es orientativo y puede compartir sesgos con el modelo evaluado.")

    detail_rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    aggregate: dict[str, dict[str, Any]] = {}
    retriever_modes = {"B": "e5", "C": "bge-m3", "D": "hybrid"}

    for config_key in args.modes:
        config = CONFIGS[config_key]
        retriever = None
        print("\n" + "-" * 76)
        print(f"CONFIGURACIÓN {config_key}: {config['label']}")
        print("-" * 76)

        try:
            if config_key in retriever_modes:
                retriever = MultilingualKnowledgeRetriever(
                    knowledge_dir=knowledge_dir,
                    mode=retriever_modes[config_key],
                    batch_size=16,
                    local_files_only=args.offline_retrievers,
                )
                print(f"Recuperador inicializado: {retriever_modes[config_key]} "
                      f"({len(retriever.chunks)} fragmentos).")

            for index, case in enumerate(TEST_CASES, 1):
                retrieval_seconds = 0.0
                context = ""
                sources: list[str] = []
                scores: list[float] = []
                retrieval_error = ""

                if retriever is not None:
                    try:
                        t0 = time.perf_counter()
                        retrieved = retriever.search(case["query"], top_k=args.top_k)
                        retrieval_seconds = time.perf_counter() - t0
                        sources = [str(item.get("source", "")) for item in retrieved]
                        scores = [round(float(item.get("score", 0.0)), 6) for item in retrieved]
                        context_parts = []
                        for rank, item in enumerate(retrieved, 1):
                            context_parts.append(
                                f"[Fragmento {rank} | fuente: {item.get('source', '')} | "
                                f"score: {float(item.get('score', 0.0)):.4f}]\n"
                                f"{item.get('text', '')}"
                            )
                        context = "\n\n---\n\n".join(context_parts)
                    except Exception as exc:
                        retrieval_error = f"{type(exc).__name__}: {exc}"
                        errors.append({"config": config_key, "test_id": case["id"],
                                       "stage": "retrieval", "error": retrieval_error})

                system, user = build_prompt(case, context, with_rag=(config_key != "A"))
                answer = ""
                generation_seconds = 0.0
                judge_seconds = 0.0
                error = retrieval_error
                judge: dict[str, Any] = {
                    "correctness": "", "groundedness": "", "completeness": "",
                    "hallucination_risk": "", "reason": "",
                }

                if not retrieval_error:
                    try:
                        answer, generation_seconds = chat(
                            args.ollama_url, args.model, system, user, args.timeout
                        )
                        print(f"[{index:02d}/{len(TEST_CASES)}] {case['id']} "
                              f"| generación={generation_seconds:.2f}s")
                    except Exception as exc:
                        error = f"{type(exc).__name__}: {exc}"
                        errors.append({"config": config_key, "test_id": case["id"],
                                       "stage": "generation", "error": error})
                        print(f"ERROR {case['id']}: {error}")

                if answer and args.judge:
                    try:
                        judge, judge_seconds = evaluate_answer(
                            args.ollama_url, args.model, case, config["label"],
                            answer, context, args.timeout,
                        )
                    except Exception as exc:
                        judge["reason"] = f"Error del juez: {type(exc).__name__}: {exc}"
                        errors.append({"config": config_key, "test_id": case["id"],
                                       "stage": "judge", "error": judge["reason"]})

                detail_rows.append({
                    "config": config_key,
                    "config_label": config["label"],
                    "test_id": case["id"],
                    "query": case["query"],
                    "rubric": case["rubric"],
                    "retriever_mode": retriever_modes.get(config_key, ""),
                    "top_k": args.top_k if retriever is not None else 0,
                    "retrieval_seconds": round(retrieval_seconds, 4),
                    "retrieved_sources": json.dumps(sources, ensure_ascii=False),
                    "retrieval_scores": json.dumps(scores, ensure_ascii=False),
                    "retrieved_context": context,
                    "generation_seconds": round(generation_seconds, 4),
                    "answer": answer,
                    "judge_seconds": round(judge_seconds, 4),
                    "correctness": judge.get("correctness", ""),
                    "groundedness": judge.get("groundedness", ""),
                    "completeness": judge.get("completeness", ""),
                    "hallucination_risk": judge.get("hallucination_risk", ""),
                    "judge_reason": judge.get("reason", ""),
                    "error": error,
                })

        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            errors.append({"config": config_key, "test_id": "INIT",
                           "stage": "initialization", "error": message})
            print(f"ERROR al inicializar configuración {config_key}: {message}")
            traceback.print_exc()
        finally:
            if retriever is not None:
                try:
                    retriever.close()
                except Exception:
                    pass
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

    # Resumen: una fila por configuración, promedios sobre las evaluaciones disponibles.
    summary_rows: list[dict[str, Any]] = []
    for config_key in args.modes:
        rows = [row for row in detail_rows if row["config"] == config_key and row["answer"]]
        def mean_numeric(field: str) -> float | str:
            vals = []
            for row in rows:
                try:
                    value = float(row[field])
                    if value > 0:
                        vals.append(value)
                except (ValueError, TypeError, KeyError):
                    pass
            return round(sum(vals) / len(vals), 3) if vals else ""

        summary_rows.append({
            "config": config_key,
            "config_label": CONFIGS[config_key]["label"],
            "answers_generated": len(rows),
            "answers_expected": len(TEST_CASES),
            "mean_retrieval_seconds": mean_numeric("retrieval_seconds"),
            "mean_generation_seconds": mean_numeric("generation_seconds"),
            "mean_correctness_1_5": mean_numeric("correctness"),
            "mean_groundedness_1_5": mean_numeric("groundedness"),
            "mean_completeness_1_5": mean_numeric("completeness"),
            "mean_hallucination_risk_1_5": mean_numeric("hallucination_risk"),
            "errors": sum(1 for err in errors if err["config"] == config_key),
        })

    detail_fields = [
        "config", "config_label", "test_id", "query", "rubric", "retriever_mode", "top_k",
        "retrieval_seconds", "retrieved_sources", "retrieval_scores", "retrieved_context",
        "generation_seconds", "answer", "judge_seconds", "correctness", "groundedness",
        "completeness", "hallucination_risk", "judge_reason", "error",
    ]
    summary_fields = [
        "config", "config_label", "answers_generated", "answers_expected",
        "mean_retrieval_seconds", "mean_generation_seconds", "mean_correctness_1_5",
        "mean_groundedness_1_5", "mean_completeness_1_5",
        "mean_hallucination_risk_1_5", "errors",
    ]
    write_csv(out_dir / "resultados_detallados.csv", detail_rows, detail_fields)
    write_csv(out_dir / "resumen_comparativo.csv", summary_rows, summary_fields)
    (out_dir / "errores.json").write_text(
        json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    metadata = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(PROJECT_ROOT),
        "knowledge_dir": str(knowledge_dir),
        "model": args.model,
        "ollama_url": args.ollama_url,
        "configurations": args.modes,
        "top_k": args.top_k,
        "test_cases": len(TEST_CASES),
        "judge_enabled": args.judge,
        "judge_model": args.model if args.judge else None,
        "offline_retrievers": args.offline_retrievers,
        "errors": errors,
        "metric_note": (
            "Las puntuaciones automáticas las genera el mismo LLM evaluado y son orientativas; "
            "pueden tener sesgos. Revisar manualmente respuestas y contexto antes de decidir."
        ),
    }
    (out_dir / "metadatos.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n" + "=" * 76)
    print("RESUMEN COMPARATIVO")
    print("=" * 76)
    for row in summary_rows:
        print(
            f"{row['config']} — {row['config_label']}: "
            f"respuestas={row['answers_generated']}/{row['answers_expected']}, "
            f"correctitud={row['mean_correctness_1_5']}, "
            f"fundamentación={row['mean_groundedness_1_5']}, "
            f"completitud={row['mean_completeness_1_5']}, "
            f"riesgo_alucinación={row['mean_hallucination_risk_1_5']}, "
            f"generación_media={row['mean_generation_seconds']} s"
        )
    print(f"\nResultados detallados: {out_dir / 'resultados_detallados.csv'}")
    print(f"Resumen comparativo:   {out_dir / 'resumen_comparativo.csv'}")
    print(f"Errores:               {out_dir / 'errores.json'}")
    print(f"Metadatos:             {out_dir / 'metadatos.json'}")
    print(f"Total de errores: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
