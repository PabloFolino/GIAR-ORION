"""
GIAR-ORION — Experimento independiente de fusión de rankings mediante RRF.

No modifica main.py ni los recuperadores existentes.
Compara, para cada consulta:
  1. recuperación léxica sola;
  2. recuperación semántica sola (E5, BGE-M3 o híbrido);
  3. fusión de ambos rankings mediante Reciprocal Rank Fusion (RRF).

Ejecutar desde la raíz de GIAR-ORION:
  python Tests\test_rag_fusion_rrf.py

Ejemplos:
  python Tests\test_rag_fusion_rrf.py --semantic-mode e5
  python Tests\test_rag_fusion_rrf.py --semantic-mode e5 --lexical-version revisado --offline
  python Tests\test_rag_fusion_rrf.py --semantic-mode bge-m3 --lexical-version original

El script mide recuperación; NO genera respuestas con Qwen y NO evalúa semánticamente
la calidad de las respuestas. Los términos esperados son indicadores de cobertura,
no una evaluación completa de relevancia.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CASES: list[dict[str, Any]] = [
    {
        "id": "UNITREE-01",
        "query": "¿Cuáles son las articulaciones principales de las piernas del robot Unitree G1?",
        "expected_terms": [
            "hip_pitch", "hip_roll", "hip_yaw", "knee", "ankle_pitch", "ankle_roll"
        ],
        "expected_source": r"Unitree\G1\Unitree_G1_Dossier_Tecnico_GIAR_ORION.md",
    },
    {
        "id": "SAC-01",
        "query": "¿Cómo funciona SAC y cómo se actualizan los críticos?",
        "expected_terms": ["actor", "crítico", "bellman", "mínimo", "pérdida"],
        "expected_source": r"SAC\Fundamentos_de_SAC_GIAR_ORION.md",
    },
    {
        "id": "SAC-02",
        "query": "¿Qué función cumple el Replay Buffer durante el entrenamiento de SAC?",
        "expected_terms": ["replay buffer", "transiciones", "minibatches", "off-policy"],
        "expected_source": r"SAC\Fundamentos_de_SAC_GIAR_ORION.md",
    },
    {
        "id": "SAC-03",
        "query": "¿Qué relación existe entre la entropía y la política en Soft Actor-Critic?",
        "expected_terms": ["entropía", "política", "alpha", "exploración"],
        "expected_source": r"SAC\Fundamentos_de_SAC_GIAR_ORION.md",
    },
    {
        "id": "RL-01",
        "query": "¿Qué es el aprendizaje por refuerzo y cómo aprende un agente?",
        "expected_terms": ["agente", "estado", "acción", "recompensa", "política"],
        "expected_source": "",
    },
    {
        "id": "DRL-01",
        "query": "¿Qué diferencia hay entre aprendizaje por refuerzo y aprendizaje profundo por refuerzo?",
        "expected_terms": ["redes neuronales", "política", "recompensa"],
        "expected_source": "",
    },
    {
        "id": "COPPELIA-01",
        "query": "¿Cómo se configuran las articulaciones y la dinámica física en CoppeliaSim?",
        "expected_terms": ["articulaciones", "dinámica", "motor", "límites"],
        "expected_source": "",
    },
    {
        "id": "PYTORCH-01",
        "query": "¿Cómo comprobar si PyTorch puede utilizar la GPU NVIDIA mediante CUDA?",
        "expected_terms": ["torch.cuda.is_available", "get_device_name", "cuda"],
        "expected_source": "",
    },
    {
        "id": "ROBOT-01",
        "query": "¿Cómo se relacionan las observaciones, las acciones y la función de recompensa en el control de un robot?",
        "expected_terms": ["observaciones", "acciones", "recompensa", "entorno"],
        "expected_source": "",
    },
    {
        "id": "AGENT-01",
        "query": "¿Cómo se recuperan documentos de la base de conocimientos de GIAR-ORION?",
        "expected_terms": ["markdown", "fragmentos", "embeddings", "similitud"],
        "expected_source": "",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compara recuperación léxica, semántica y fusión RRF."
    )
    parser.add_argument("--knowledge-dir", default=str(ROOT / "Knowledge"))
    parser.add_argument(
        "--output-dir", default=str(ROOT / "Tests" / "results_rag_fusion_rrf")
    )
    parser.add_argument(
        "--semantic-mode", choices=["e5", "bge-m3", "hybrid"], default="e5"
    )
    parser.add_argument(
        "--lexical-version", choices=["original", "revisado"], default="revisado"
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--candidate-k", type=int, default=20)
    parser.add_argument("--rrf-k", type=int, default=60)
    parser.add_argument("--lexical-weight", type=float, default=1.0)
    parser.add_argument("--semantic-weight", type=float, default=1.0)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--case-ids", nargs="*", default=None)
    return parser.parse_args()


def norm(text: str) -> str:
    return str(text or "").casefold().replace("-", "_").replace(" ", "_")


def source_key(source: str) -> str:
    return str(source or "").replace("/", "\\").casefold()


def reciprocal_rank_fusion(
    lexical_items: list[dict[str, Any]],
    semantic_items: list[dict[str, Any]],
    rrf_k: int = 60,
    lexical_weight: float = 1.0,
    semantic_weight: float = 1.0,
) -> list[dict[str, Any]]:
    """Fusiona listas ordenadas sin sumar sus scores originales."""
    fused: dict[tuple[str, str], dict[str, Any]] = {}

    for channel, items, weight in (
        ("lexical", lexical_items, lexical_weight),
        ("semantic", semantic_items, semantic_weight),
    ):
        for rank, item in enumerate(items, start=1):
            key = (source_key(item.get("source", "")), str(item.get("text", "")))
            if key not in fused:
                fused[key] = {
                    "source": item.get("source", ""),
                    "text": item.get("text", ""),
                    "rrf_score": 0.0,
                    "lexical_rank": None,
                    "semantic_rank": None,
                    "lexical_score": None,
                    "semantic_score": None,
                    "channels": set(),
                }
            row = fused[key]
            row["rrf_score"] += weight / (rrf_k + rank)
            row[f"{channel}_rank"] = rank
            row[f"{channel}_score"] = item.get("score")
            row["channels"].add(channel)

    results = list(fused.values())
    results.sort(
        key=lambda row: (
            row["rrf_score"],
            len(row["channels"]),
            -len(row["text"]),
        ),
        reverse=True,
    )
    for row in results:
        row["channels"] = "+".join(sorted(row["channels"]))
        row["rrf_score"] = round(float(row["rrf_score"]), 8)
    return results


def evaluate_items(items: list[dict[str, Any]], case: dict[str, Any]) -> dict[str, Any]:
    text = "\n".join(str(item.get("text", "")) for item in items).casefold()
    terms = case.get("expected_terms", [])
    found_terms = [term for term in terms if str(term).casefold() in text]
    expected_source = str(case.get("expected_source", "")).strip()
    found_source = bool(
        expected_source
        and any(source_key(expected_source) in source_key(item.get("source", "")) for item in items)
    )
    return {
        "expected_term_count": len(terms),
        "found_term_count": len(found_terms),
        "term_coverage": round(len(found_terms) / len(terms), 4) if terms else None,
        "found_terms": " | ".join(found_terms),
        "expected_source": expected_source,
        "expected_source_found": found_source if expected_source else None,
    }


def result_rows(
    case: dict[str, Any],
    method: str,
    items: list[dict[str, Any]],
    retrieval_seconds: float,
) -> list[dict[str, Any]]:
    metrics = evaluate_items(items, case)
    rows = []
    for rank, item in enumerate(items, start=1):
        rows.append({
            "case_id": case["id"],
            "query": case["query"],
            "method": method,
            "rank": rank,
            "source": item.get("source", ""),
            "score": item.get("score", ""),
            "rrf_score": item.get("rrf_score", ""),
            "channels": item.get("channels", ""),
            "lexical_rank": item.get("lexical_rank", ""),
            "semantic_rank": item.get("semantic_rank", ""),
            "text": item.get("text", ""),
            "retrieval_seconds": round(retrieval_seconds, 4),
            **metrics,
        })
    return rows


def main() -> int:
    args = parse_args()
    if args.top_k < 1 or args.candidate_k < args.top_k:
        print("ERROR: top-k debe ser >= 1 y candidate-k debe ser >= top-k.")
        return 2
    if args.rrf_k < 1:
        print("ERROR: rrf-k debe ser >= 1.")
        return 2
    if args.lexical_weight < 0 or args.semantic_weight < 0:
        print("ERROR: los pesos no pueden ser negativos.")
        return 2
    if args.lexical_weight + args.semantic_weight <= 0:
        print("ERROR: al menos uno de los pesos debe ser mayor que cero.")
        return 2

    knowledge_dir = Path(args.knowledge_dir).resolve()
    if not knowledge_dir.is_dir():
        print(f"ERROR: no existe el directorio Knowledge: {knowledge_dir}")
        return 2

    selected_cases = CASES
    if args.case_ids:
        wanted = {case_id.upper() for case_id in args.case_ids}
        selected_cases = [case for case in CASES if case["id"].upper() in wanted]
        missing = wanted - {case["id"].upper() for case in selected_cases}
        if missing:
            print(f"ERROR: identificadores desconocidos: {', '.join(sorted(missing))}")
            return 2
    if not selected_cases:
        print("ERROR: no hay consultas para ejecutar.")
        return 2

    try:
        from Agent.MultilingualKnowledgeRetriever import MultilingualKnowledgeRetriever
        if args.lexical_version == "original":
            from Agent.KnowledgeRetriever import KnowledgeRetriever as LexicalRetriever
        else:
            from Agent.KnowledgeRetriever_revisado import KnowledgeRetriever as LexicalRetriever
    except Exception as exc:
        print(f"ERROR al importar recuperadores: {type(exc).__name__}: {exc}")
        return 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir).resolve() / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    print("GIAR-ORION — Experimento independiente de fusión RRF")
    print(f"Knowledge: {knowledge_dir}")
    print(f"Recuperador léxico: {args.lexical_version}")
    print(f"Recuperador semántico: {args.semantic_mode}")
    print(f"Consultas: {len(selected_cases)} | top-k={args.top_k} | candidatos={args.candidate_k}")
    print(f"Salida: {output_dir}")
    print("Se medirán rankings y cobertura; no se generarán respuestas con Qwen.")

    lexical = None
    semantic = None
    all_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    try:
        lexical = LexicalRetriever(knowledge_dir)
        semantic = MultilingualKnowledgeRetriever(
            knowledge_dir=knowledge_dir,
            mode=args.semantic_mode,
            local_files_only=args.offline,
        )

        for case in selected_cases:
            print(f"\n[{case['id']}] {case['query']}")
            try:
                start = time.perf_counter()
                lexical_candidates = lexical.buscar(
                    case["query"], max_resultados=args.candidate_k
                )
                lexical_seconds = time.perf_counter() - start

                start = time.perf_counter()
                semantic_candidates = semantic.search(
                    case["query"], top_k=args.candidate_k
                )
                semantic_seconds = time.perf_counter() - start

                fused_candidates = reciprocal_rank_fusion(
                    lexical_candidates,
                    semantic_candidates,
                    rrf_k=args.rrf_k,
                    lexical_weight=args.lexical_weight,
                    semantic_weight=args.semantic_weight,
                )

                methods = [
                    ("lexical_only", lexical_candidates[:args.top_k], lexical_seconds),
                    ("semantic_only", semantic_candidates[:args.top_k], semantic_seconds),
                    (
                        "rrf_fusion",
                        fused_candidates[:args.top_k],
                        lexical_seconds + semantic_seconds,
                    ),
                ]
                for method, items, elapsed in methods:
                    metrics = evaluate_items(items, case)
                    summary_rows.append({
                        "case_id": case["id"],
                        "query": case["query"],
                        "method": method,
                        "lexical_version": args.lexical_version,
                        "semantic_mode": args.semantic_mode,
                        "top_k": args.top_k,
                        "candidate_k": args.candidate_k,
                        "rrf_k": args.rrf_k,
                        "lexical_weight": args.lexical_weight,
                        "semantic_weight": args.semantic_weight,
                        "retrieval_seconds": round(elapsed, 4),
                        "returned_results": len(items),
                        **metrics,
                    })
                    all_rows.extend(result_rows(case, method, items, elapsed))
                    print(
                        f"  {method:14s} cobertura={metrics['term_coverage']} "
                        f"términos={metrics['found_term_count']}/{metrics['expected_term_count']} "
                        f"fuente={metrics['expected_source_found']}"
                    )
            except Exception as exc:
                errors.append({
                    "case_id": case["id"],
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                })
                print(f"  ERROR: {type(exc).__name__}: {exc}")

    except Exception as exc:
        errors.append({
            "case_id": "__initialization__",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        })
        print(f"ERROR al inicializar: {type(exc).__name__}: {exc}")
    finally:
        if semantic is not None:
            try:
                semantic.close()
            except Exception:
                pass

    detailed_path = output_dir / "resultados_detallados.csv"
    summary_path = output_dir / "resumen_por_consulta.csv"
    metadata_path = output_dir / "metadatos.json"
    errors_path = output_dir / "errores.json"

    detail_fields = [
        "case_id", "query", "method", "rank", "source", "score", "rrf_score",
        "channels", "lexical_rank", "semantic_rank", "text", "retrieval_seconds",
        "expected_term_count", "found_term_count", "term_coverage", "found_terms",
        "expected_source", "expected_source_found",
    ]
    summary_fields = [
        "case_id", "query", "method", "lexical_version", "semantic_mode", "top_k",
        "candidate_k", "rrf_k", "lexical_weight", "semantic_weight",
        "retrieval_seconds", "returned_results", "expected_term_count",
        "found_term_count", "term_coverage", "found_terms", "expected_source",
        "expected_source_found",
    ]
    for path, rows, fields in (
        (detailed_path, all_rows, detail_fields),
        (summary_path, summary_rows, summary_fields),
    ):
        with path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    metadata = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "experiment": "independent_rrf_ranking_fusion",
        "project_root": str(ROOT),
        "knowledge_dir": str(knowledge_dir),
        "lexical_version": args.lexical_version,
        "semantic_mode": args.semantic_mode,
        "top_k": args.top_k,
        "candidate_k": args.candidate_k,
        "rrf_k": args.rrf_k,
        "lexical_weight": args.lexical_weight,
        "semantic_weight": args.semantic_weight,
        "cases": [case["id"] for case in selected_cases],
        "methods": ["lexical_only", "semantic_only", "rrf_fusion"],
        "generation_enabled": False,
        "offline_retrievers": args.offline,
        "errors": len(errors),
        "metric_note": (
            "La cobertura de términos y la presencia de fuente son indicadores parciales. "
            "No equivalen a relevancia semántica ni a calidad de respuesta."
        ),
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    errors_path.write_text(
        json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\nExperimento finalizado.")
    print(f"Resumen: {summary_path}")
    print(f"Detalle: {detailed_path}")
    print(f"Metadatos: {metadata_path}")
    print(f"Errores: {errors_path}")
    print(f"Errores registrados: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
