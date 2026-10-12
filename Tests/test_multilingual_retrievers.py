"""
test_multilingual_retrievers.py
Evaluación reproducible de E5, BGE-M3 e híbrido para GIAR-ORION.

Guardar en GIAR-ORION\Tests\test_multilingual_retrievers.py
Ejecutar desde la raíz:
    python Tests\test_multilingual_retrievers.py

Los indicadores expected_terms son aproximaciones por presencia de palabras,
no sustituyen la evaluación humana de la relevancia.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from Agent.MultilingualKnowledgeRetriever import MultilingualKnowledgeRetriever
except Exception as exc:
    print("ERROR: no se pudo importar Agent.MultilingualKnowledgeRetriever.")
    print(f"Detalle: {exc}")
    print("Verificá la ruta y el entorno virtual .venv.")
    raise

# Editá estas consultas cuando quieras ampliar la evaluación.
TEST_CASES: list[dict[str, Any]] = [
    {
        "id": "SAC-01",
        "query": "¿Cómo funciona SAC y cómo se actualizan los críticos?",
        "expected_terms": ["críticos", "función", "bellman"],
        "expected_source": r"SAC\Fundamentos_de_SAC_GIAR_ORION.md",
    },
    {
        "id": "SAC-02",
        "query": "¿Qué función cumple el Replay Buffer durante el entrenamiento de SAC?",
        "expected_terms": ["replay buffer", "transiciones", "experiencias"],
        "expected_source": r"SAC\Fundamentos_de_SAC_GIAR_ORION.md",
    },
    {
        "id": "SAC-03",
        "query": "¿Qué relación existe entre la entropía y la política en Soft Actor-Critic?",
        "expected_terms": ["entropía", "política", "máxima entropía"],
        "expected_source": r"SAC\Fundamentos_de_SAC_GIAR_ORION.md",
    },
    {
        "id": "RL-01",
        "query": "¿Qué es el aprendizaje por refuerzo y cómo aprende un agente?",
        "expected_terms": ["aprendizaje", "refuerzo", "agente"],
        "expected_source": "",
    },
    {
        "id": "DRL-01",
        "query": "¿Qué diferencia hay entre aprendizaje por refuerzo y aprendizaje profundo por refuerzo?",
        "expected_terms": ["aprendizaje", "refuerzo", "profundo"],
        "expected_source": "",
    },
    {
        "id": "COPPELIA-01",
        "query": "¿Cómo se configuran las articulaciones y la dinámica física en CoppeliaSim?",
        "expected_terms": ["articulación", "dinámica", "CoppeliaSim"],
        "expected_source": "",
    },
    {
        "id": "UNITREE-01",
        "query": "¿Cuáles son las articulaciones principales de las piernas del robot Unitree G1?",
        "expected_terms": ["hip", "knee", "ankle", "joint"],
        "expected_source": "",
    },
    {
        "id": "PYTORCH-01",
        "query": "¿Cómo comprobar si PyTorch puede utilizar la GPU NVIDIA mediante CUDA?",
        "expected_terms": ["torch", "cuda", "gpu"],
        "expected_source": "",
    },
    {
        "id": "ROBOT-01",
        "query": "¿Cómo se relacionan las observaciones, las acciones y la función de recompensa en el control de un robot?",
        "expected_terms": ["observación", "acción", "recompensa"],
        "expected_source": "",
    },
    {
        "id": "AGENT-01",
        "query": "¿Cómo se recuperan documentos de la base de conocimientos de GIAR-ORION?",
        "expected_terms": ["documento", "conocimiento", "recuperación"],
        "expected_source": "",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evalúa E5, BGE-M3 e híbrido en la base Knowledge."
    )
    parser.add_argument(
        "--modes", nargs="+", choices=["e5", "bge-m3", "hybrid"],
        default=["e5", "bge-m3", "hybrid"],
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--knowledge-dir", default=str(PROJECT_ROOT / "Knowledge"))
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "Tests" / "results_multilingual"),
    )
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--offline", action="store_true")
    return parser.parse_args()


def normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def terms_hit(results: list[dict[str, Any]], terms: list[str]) -> bool | None:
    if not terms:
        return None
    text = normalize(" ".join(str(item.get("text", "")) for item in results))
    return any(normalize(term) in text for term in terms)


def source_hit(results: list[dict[str, Any]], expected: str) -> bool | None:
    if not expected:
        return None
    expected_norm = normalize(expected.replace("/", "\\"))
    return any(
        expected_norm in normalize(str(r.get("source", "")).replace("/", "\\"))
        for r in results
    )


def gpu_info() -> dict[str, Any]:
    try:
        import torch
        available = bool(torch.cuda.is_available())
        return {
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "cuda_available": available,
            "gpu_name": torch.cuda.get_device_name(0) if available else "",
            "gpu_memory_allocated_mb": (
                round(torch.cuda.memory_allocated(0) / (1024 ** 2), 2)
                if available else None
            ),
        }
    except Exception as exc:
        return {"cuda_available": False, "gpu_check_error": str(exc)}


def save_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    if args.top_k < 1 or args.batch_size < 1:
        print("ERROR: --top-k y --batch-size deben ser mayores que cero.")
        return 2

    knowledge = Path(args.knowledge_dir).resolve()
    if not knowledge.is_dir():
        print(f"ERROR: no existe el directorio Knowledge: {knowledge}")
        return 2

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output_dir).resolve() / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    hardware = gpu_info()

    print("=" * 72)
    print("GIAR-ORION — EVALUACIÓN DE RECUPERADORES MULTILINGÜES")
    print("=" * 72)
    print(f"Directorio de conocimientos: {knowledge}")
    print(f"Modos: {', '.join(args.modes)}")
    print(f"Consultas: {len(TEST_CASES)} | Top-k: {args.top_k}")
    print(f"Salida: {out_dir}")
    print("Hardware:")
    print(json.dumps(hardware, ensure_ascii=False, indent=2))
    print("Nota: CUDA disponible no demuestra por sí sola que cada modelo use la GPU.")

    detail_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for mode in args.modes:
        print("\n" + "#" * 72)
        print(f"MODO: {mode}")
        print("#" * 72)
        retriever = None
        try:
            start_load = time.perf_counter()
            retriever = MultilingualKnowledgeRetriever(
                knowledge_dir=knowledge,
                mode=mode,
                batch_size=args.batch_size,
                local_files_only=args.offline,
            )
            load_time = time.perf_counter() - start_load
            print(f"Inicialización: {load_time:.2f} s; fragmentos: {len(retriever.chunks)}")

            for case in TEST_CASES:
                start = time.perf_counter()
                try:
                    results = retriever.search(case["query"], top_k=args.top_k)
                    elapsed = time.perf_counter() - start
                    term_flag = terms_hit(results, case["expected_terms"])
                    source_flag = source_hit(results, case["expected_source"])
                    top_source = results[0]["source"] if results else ""

                    summary_rows.append({
                        "test_id": case["id"],
                        "mode": mode,
                        "query": case["query"],
                        "load_seconds": round(load_time, 4),
                        "search_seconds": round(elapsed, 4),
                        "results_count": len(results),
                        "top1_source": top_source,
                        "expected_terms_hit_at_k": term_flag,
                        "expected_source_hit_at_k": source_flag,
                        "error": "",
                    })
                    print(
                        f"\n[{case['id']}] {case['query']}\n"
                        f"  búsqueda={elapsed:.3f}s | términos={term_flag} | "
                        f"archivo esperado={source_flag}"
                    )
                    for rank, result in enumerate(results, 1):
                        text = str(result.get("text", ""))
                        detail_rows.append({
                            "test_id": case["id"],
                            "mode": mode,
                            "query": case["query"],
                            "rank": rank,
                            "source": result.get("source", ""),
                            "score": result.get("score", ""),
                            "search_seconds": round(elapsed, 4),
                            "expected_terms": " | ".join(case["expected_terms"]),
                            "expected_source": case["expected_source"],
                            "text": text,
                        })
                        preview = " ".join(text.split())
                        if len(preview) > 180:
                            preview = preview[:177] + "..."
                        print(
                            f"  {rank}. {result.get('source', '')} "
                            f"score={float(result.get('score', 0.0)):.4f}\n"
                            f"     {preview}"
                        )
                except Exception as exc:
                    elapsed = time.perf_counter() - start
                    message = f"{type(exc).__name__}: {exc}"
                    print(f"ERROR en {case['id']}: {message}")
                    summary_rows.append({
                        "test_id": case["id"], "mode": mode,
                        "query": case["query"], "load_seconds": round(load_time, 4),
                        "search_seconds": round(elapsed, 4), "results_count": 0,
                        "top1_source": "", "expected_terms_hit_at_k": None,
                        "expected_source_hit_at_k": None, "error": message,
                    })
                    errors.append({"mode": mode, "test_id": case["id"], "error": message})
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            print(f"ERROR al inicializar {mode}: {message}")
            traceback.print_exc()
            errors.append({"mode": mode, "test_id": "LOAD", "error": message})
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

    save_csv(
        out_dir / "resultados_detallados.csv",
        detail_rows,
        ["test_id", "mode", "query", "rank", "source", "score",
         "search_seconds", "expected_terms", "expected_source", "text"],
    )
    save_csv(
        out_dir / "resumen_por_consulta.csv",
        summary_rows,
        ["test_id", "mode", "query", "load_seconds", "search_seconds",
         "results_count", "top1_source", "expected_terms_hit_at_k",
         "expected_source_hit_at_k", "error"],
    )
    metadata = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(PROJECT_ROOT),
        "knowledge_dir": str(knowledge),
        "modes": args.modes,
        "top_k": args.top_k,
        "batch_size": args.batch_size,
        "offline": args.offline,
        "test_cases": len(TEST_CASES),
        "hardware": hardware,
        "errors": errors,
        "metric_note": (
            "expected_terms_hit_at_k es una señal aproximada por presencia de "
            "palabras; no es una métrica de relevancia semántica. Los resultados "
            "deben revisarse manualmente antes de elegir un modelo."
        ),
    }
    (out_dir / "metadatos.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n" + "=" * 72)
    print("EVALUACIÓN FINALIZADA")
    print("=" * 72)
    print(f"Resultados: {out_dir / 'resultados_detallados.csv'}")
    print(f"Resumen:    {out_dir / 'resumen_por_consulta.csv'}")
    print(f"Metadatos:  {out_dir / 'metadatos.json'}")
    print(f"Filas detalladas: {len(detail_rows)} | Errores: {len(errors)}")
    print("Los indicadores automáticos son orientativos; revisá la relevancia real.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
