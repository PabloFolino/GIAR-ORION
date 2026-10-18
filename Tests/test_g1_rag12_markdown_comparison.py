# -*- coding: utf-8 -*-
"""
G1-RAG-12: comparación aislada de dos representaciones Markdown del MJCF del G1.

Compara el Markdown anterior y el especializado usando:
- el mismo recuperador MultilingualKnowledgeRetriever.py;
- el mismo modelo E5;
- los mismos parámetros de chunking;
- las mismas consultas y el mismo top-k.

No modifica main.py, el recuperador ni el corpus Knowledge del proyecto.
Ejecutar desde la raíz de GIAR-ORION:
    python Tests/test_g1_rag12_markdown_comparison.py

Si las rutas de los Markdown son diferentes:
    python Tests/test_g1_rag12_markdown_comparison.py --old-md "..." --new-md "..."

Los resultados requieren revisión humana: score y coincidencia literal no equivalen
por sí solos a relevancia semántica.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

CASES = [
    {
        "case_id": "R07-06",
        "query": "Explicá la diferencia entre el sitio imu_in_torso y el sensor imu-torso-angular-velocity.",
        "expected_terms": ["imu_in_torso", "imu-torso-angular-velocity"],
        "goal": "Recuperar tanto el site como el sensor y su relación explícita.",
    },
    {
        "case_id": "R07-07",
        "query": "¿Qué diferencia conceptual hay entre un site y un sensor en MJCF?",
        "expected_terms": ["site", "sensor"],
        "goal": "Comprobar si el fragmento ayuda a distinguir los dos tipos de elemento.",
    },
    {
        "case_id": "R07-14",
        "query": "¿Dónde está definido imu-pelvis-linear-acceleration y qué representa?",
        "expected_terms": ["imu-pelvis-linear-acceleration", "imu_in_pelvis", "accelerometer"],
        "goal": "Recuperar el tipo de sensor y el site al que referencia.",
    },
    {
        "case_id": "R07-19",
        "query": "Buscá el nombre imu_in_pelvis y decime si es sensor o site.",
        "expected_terms": ["imu_in_pelvis", "site"],
        "goal": "Identificar el tipo correcto de imu_in_pelvis.",
    },
    {
        "case_id": "CONTROL-RL-12",
        "query": "Explicá la relación entre política del agente y función de valor en RL.",
        "expected_terms": ["política", "valor"],
        "goal": "Control negativo: esta consulta es de RL y no debería resolverse solo con el Markdown del MJCF.",
    },
]

def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("g1_rag12_retriever", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar el recuperador: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def literal_terms(text: str, terms: list[str]) -> list[str]:
    # Para términos simples y nombres técnicos; comparación sin distinguir mayúsculas.
    folded = text.casefold()
    return [term for term in terms if term.casefold() in folded]

def write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def main() -> int:
    parser = argparse.ArgumentParser(description="Compara dos Markdown del MJCF del G1 con recuperación E5 aislada.")
    parser.add_argument("--old-md", type=Path, default=Path("Knowledge/Unitree/G1/g1_29dof_with_hand_rag.md"))
    parser.add_argument("--new-md", type=Path, default=Path("Knowledge/Unitree/G1/g1_29dof_with_hand_rag_v2.md"))
    parser.add_argument("--retriever", type=Path, default=Path("Agent/MultilingualKnowledgeRetriever.py"))
    parser.add_argument("--output-dir", type=Path, default=Path("Tests/results_g1_rag12"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--chunk-chars", type=int, default=1100)
    parser.add_argument("--overlap-chars", type=int, default=150)
    parser.add_argument("--device", default=None)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    for path in (args.old_md, args.new_md, args.retriever):
        if not path.is_file():
            print(f"ERROR: no se encuentra el archivo: {path.resolve()}", file=sys.stderr)
            return 2
    if args.top_k < 1:
        print("ERROR: --top-k debe ser >= 1", file=sys.stderr)
        return 2

    module = load_module(args.retriever)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = args.output_dir / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    detail_rows = []
    metadata = {
        "experiment": "G1-RAG-12",
        "timestamp": stamp,
        "method": "E5 dense semantic retrieval, each candidate Markdown indexed in isolation",
        "retriever": str(args.retriever.resolve()),
        "model": module.E5_MODEL_NAME,
        "top_k": args.top_k,
        "chunk_chars": args.chunk_chars,
        "overlap_chars": args.overlap_chars,
        "candidates": {},
        "limitations": [
            "La comparación aísla cada Markdown; no evalúa el comportamiento del router de G1-RAG-07.",
            "La cobertura literal no mide relevancia ni corrección semántica.",
            "Los resultados deben revisarse manualmente.",
            "CONTROL-RL-12 es una consulta de control ajena al contenido MJCF.",
        ],
    }

    # Dos corpus temporales de un solo documento evitan que una versión compita con la otra.
    with tempfile.TemporaryDirectory(prefix="g1_rag12_") as temp_root:
        temp_root = Path(temp_root)
        for label, source_path in (("old", args.old_md), ("new", args.new_md)):
            isolated_dir = temp_root / label
            isolated_dir.mkdir()
            isolated_copy = isolated_dir / source_path.name
            shutil.copy2(source_path, isolated_copy)

            kwargs = {
                "knowledge_dir": isolated_dir,
                "mode": "e5",
                "chunk_chars": args.chunk_chars,
                "overlap_chars": args.overlap_chars,
            }
            if args.device:
                kwargs["device"] = args.device
            if args.offline:
                kwargs["local_files_only"] = True

            print(f"\n[{label.upper()}] Indexando {source_path.name} ...")
            start = time.perf_counter()
            retriever = module.MultilingualKnowledgeRetriever(**kwargs)
            init_seconds = time.perf_counter() - start
            metadata["candidates"][label] = {
                "file": str(source_path.resolve()),
                "bytes": source_path.stat().st_size,
                "chunks": len(retriever.chunks),
                "initialization_seconds": round(init_seconds, 3),
                "device": str(retriever.device),
            }

            try:
                for case in CASES:
                    results = retriever.search(case["query"], top_k=args.top_k)
                    joined = "\n".join(item["text"] for item in results)
                    found = literal_terms(joined, case["expected_terms"])
                    summary_rows.append({
                        "candidate": label,
                        "file": source_path.name,
                        "case_id": case["case_id"],
                        "query": case["query"],
                        "goal": case["goal"],
                        "top_k": args.top_k,
                        "retrieved_count": len(results),
                        "expected_term_count": len(case["expected_terms"]),
                        "found_term_count": len(found),
                        "literal_coverage": round(len(found) / len(case["expected_terms"]), 4),
                        "found_terms": ";".join(found),
                        "missing_terms": ";".join(t for t in case["expected_terms"] if t not in found),
                        "human_relevance_review": "PENDIENTE",
                        "answer_supported": "PENDIENTE",
                    })
                    print(f"  {case['case_id']}: cobertura literal {len(found)}/{len(case['expected_terms'])}")
                    for rank, item in enumerate(results, 1):
                        item_found = literal_terms(item["text"], case["expected_terms"])
                        detail_rows.append({
                            "candidate": label,
                            "case_id": case["case_id"],
                            "query": case["query"],
                            "rank": rank,
                            "source": item["source"],
                            "score": round(float(item["score"]), 6),
                            "expected_terms_found": ";".join(item_found),
                            "text": item["text"],
                            "human_relevance": "PENDIENTE",
                        })
            finally:
                retriever.close()

    write_csv(out_dir / "resumen.csv", summary_rows)
    write_csv(out_dir / "detalle.csv", detail_rows)
    (out_dir / "metadatos.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nComparación terminada.")
    print(f"Resultados: {out_dir.resolve()}")
    print("Archivos: resumen.csv, detalle.csv, metadatos.json")
    print("IMPORTANTE: revisar detalle.csv y completar las columnas humanas antes de concluir cuál versión es mejor.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
