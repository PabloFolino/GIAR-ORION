#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparación independiente de recuperación RAG:
A) fragmentación actual del recuperador de producción
B) fragmentación experimental agrupada por encabezados para el dossier G1

No modifica módulos de producción ni documentos. Usa el mismo modelo E5, las mismas
consultas, top_k y corpus; solo cambia la fragmentación del dossier G1 en B.

Ejecutar desde la raíz de GIAR-ORION:
  python Tests\compare_g1_chunking_retrieval.py
  python Tests\compare_g1_chunking_retrieval.py --mode e5 --top-k 5
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import sys
from datetime import datetime
from pathlib import Path

QUERIES = [
    {
        "id": "G1-01",
        "query": "Enumerá las seis articulaciones de la pierna izquierda del Unitree G1 usando los nombres exactos del modelo.",
        "expected": ["left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
                     "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint"],
    },
    {
        "id": "G1-02",
        "query": "¿Cuáles son las tres articulaciones de la cintura del G1 y en qué orden aparecen en el bloque actuator del MJCF?",
        "expected": ["waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint"],
    },
    {
        "id": "G1-03",
        "query": "¿Cuáles son los cuatro sensores IMU definidos en el modelo MJCF y qué mide cada uno?",
        "expected": ["imu-torso-angular-velocity", "imu-torso-linear-acceleration",
                     "imu-pelvis-angular-velocity", "imu-pelvis-linear-acceleration"],
    },
    {
        "id": "G1-04",
        "query": "Explicá la diferencia entre el sitio imu_in_torso y el sensor imu-torso-angular-velocity.",
        "expected": ["imu_in_torso", "imu-torso-angular-velocity"],
    },
    {
        "id": "G1-05",
        "query": "Enumerá las siete articulaciones de la mano derecha del G1 con sus identificadores exactos.",
        "expected": ["right_hand_thumb_0_joint", "right_hand_thumb_1_joint", "right_hand_thumb_2_joint",
                     "right_hand_index_0_joint", "right_hand_index_1_joint",
                     "right_hand_middle_0_joint", "right_hand_middle_1_joint"],
    },
    {
        "id": "G1-06",
        "query": "Enumerá los 43 actuadores del modelo G1 en el orden exacto en que aparecen en el bloque actuator del MJCF.",
        "expected": ["left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
                     "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",
                     "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
                     "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint",
                     "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
                     "left_shoulder_pitch_joint", "left_shoulder_roll_joint", "left_shoulder_yaw_joint",
                     "left_elbow_joint", "left_wrist_roll_joint", "left_wrist_pitch_joint", "left_wrist_yaw_joint",
                     "left_hand_thumb_0_joint", "left_hand_thumb_1_joint", "left_hand_thumb_2_joint",
                     "left_hand_middle_0_joint", "left_hand_middle_1_joint",
                     "left_hand_index_0_joint", "left_hand_index_1_joint",
                     "right_shoulder_pitch_joint", "right_shoulder_roll_joint", "right_shoulder_yaw_joint",
                     "right_elbow_joint", "right_wrist_roll_joint", "right_wrist_pitch_joint", "right_wrist_yaw_joint",
                     "right_hand_thumb_0_joint", "right_hand_thumb_1_joint", "right_hand_thumb_2_joint",
                     "right_hand_index_0_joint", "right_hand_index_1_joint",
                     "right_hand_middle_0_joint", "right_hand_middle_1_joint"],
    },
]

def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("g1_compare_retriever", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def split_long(text: str, limit: int, overlap: int) -> list[str]:
    text = re.sub(r"[ \t]+", " ", text).strip()
    if len(text) <= limit:
        return [text]
    out, start = [], 0
    while start < len(text):
        end = min(start + limit, len(text))
        if end < len(text):
            boundary = max(text.rfind(". ", start, end),
                           text.rfind("; ", start, end),
                           text.rfind(" ", start, end))
            if boundary > start + limit // 2:
                end = boundary + 1
        out.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return out

def grouped_markdown_chunks(path: Path, limit: int, overlap: int):
    """Divide por encabezados Markdown; conserva título/ruta de encabezados en cada fragmento."""
    raw = path.read_text(encoding="utf-8-sig")
    headings: list[tuple[int, str]] = []
    for line_no, line in enumerate(raw.splitlines()):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match:
            headings.append((len(match.group(1)), match.group(2).strip()))
    lines = raw.splitlines()
    stack: list[tuple[int, str]] = []
    blocks: list[tuple[str, str]] = []
    current_lines: list[str] = []
    current_path = ""
    heading_idx = 0

    def flush():
        nonlocal current_lines
        body = "\n".join(current_lines).strip()
        if body:
            blocks.append((current_path, body))
        current_lines = []

    for line in lines:
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match:
            flush()
            level, title = len(match.group(1)), match.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            current_path = " > ".join(t for _, t in stack)
        else:
            if line.strip():
                current_lines.append(line.strip())
            elif current_lines:
                flush()
    flush()

    chunks = []
    for heading_path, body in blocks:
        # Mantiene juntos listas/tablas/párrafos pertenecientes a un encabezado cuando caben.
        # Si un bloque es muy largo, se subdivide con los mismos límites de caracteres del baseline.
        full = f"{heading_path}\n{body}".strip() if heading_path else body
        for piece in split_long(full, limit, overlap):
            if len(piece) >= 25:
                chunks.append(piece)
    return chunks

def make_chunk(source: str, text: str, cls):
    return cls(source=source, text=text)

def embed_e5_chunks(retriever, chunks, batch_size: int):
    texts = ["passage: " + chunk.text for chunk in chunks]
    vectors = retriever._e5_model.encode(
        texts, batch_size=batch_size, convert_to_numpy=True,
        normalize_embeddings=True, show_progress_bar=True
    )
    for chunk, vector in zip(chunks, vectors):
        chunk.embedding_e5 = vector.astype("float32")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["e5"], default="e5",
                    help="Esta comparación usa E5 para mantener la prueba acotada y reproducible.")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--knowledge-dir", type=Path, default=Path("Knowledge"))
    ap.add_argument("--dossier", type=Path,
                    default=Path("Knowledge/Unitree/G1/Unitree_G1_Dossier_Tecnico_GIAR_ORION.md"))
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    retriever_path = Path("Agent/MultilingualKnowledgeRetriever.py")
    if not retriever_path.is_file():
        print("ERROR: no encuentro", retriever_path.resolve())
        return 2
    if not args.knowledge_dir.is_dir():
        print("ERROR: no encuentro", args.knowledge_dir.resolve())
        return 2
    if not args.dossier.is_file():
        print("ERROR: no encuentro el dossier:", args.dossier.resolve())
        return 2

    print("Recuperador de producción (solo lectura):", retriever_path.resolve())
    print("Dossier a re-fragmentar en B:", args.dossier.resolve())
    print("Modo:", args.mode, "| top_k:", args.top_k)
    print("Se crearán dos evaluaciones; no se modifica ningún archivo de producción.")

    module = load_module(retriever_path)
    Retriever = module.MultilingualKnowledgeRetriever
    kwargs = {"knowledge_dir": args.knowledge_dir, "mode": "e5"}
    if args.device:
        kwargs["device"] = args.device
    retriever = Retriever(**kwargs)

    # A: copia de la fragmentación/corpus actual.
    baseline_chunks = list(retriever.chunks)
    dossier_rel = str(args.dossier.resolve().relative_to(args.knowledge_dir.resolve())).replace("\\", "/")
    target_sources = {dossier_rel, dossier_rel.replace("/", "\\")}
    actual_target = [c for c in baseline_chunks if c.source.replace("\\", "/") == dossier_rel]
    if not actual_target:
        print("ERROR: el recuperador no cargó fragmentos del dossier indicado.")
        print("Fuentes parecidas:", sorted({c.source for c in baseline_chunks if "Unitree" in c.source or "G1" in c.source})[:20])
        return 2

    # B: mismo corpus, reemplazando solo los fragmentos de ese dossier.
    grouped_texts = grouped_markdown_chunks(args.dossier, retriever.chunk_chars, retriever.overlap_chars)
    other_chunks = [c for c in baseline_chunks if c.source.replace("\\", "/") != dossier_rel]
    grouped_chunks = [make_chunk(dossier_rel, text, module.KnowledgeChunk) for text in grouped_texts]
    print(f"\nFragmentos del dossier en A: {len(actual_target)}")
    print(f"Fragmentos del dossier en B: {len(grouped_chunks)}")
    embed_e5_chunks(retriever, grouped_chunks, retriever.batch_size)
    grouped_all = other_chunks + grouped_chunks

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = Path("Tests") / f"results_g1_chunking_comparison_{timestamp}"
    outdir.mkdir(parents=True, exist_ok=True)
    summary_rows, detail_rows = [], []

    for strategy, chunks in (("A_current", baseline_chunks), ("B_grouped_headings", grouped_all)):
        retriever.chunks = chunks
        print(f"\n{'='*72}\nESTRATEGIA {strategy}\n{'='*72}")
        for case in QUERIES:
            results = retriever.search(case["query"], top_k=args.top_k)
            combined = "\n".join(str(x.get("text", "")) for x in results)
            found = [t for t in case["expected"] if t in combined]
            coverage = len(found) / len(case["expected"]) if case["expected"] else 1.0
            first_relevant_rank = ""
            for rank, item in enumerate(results, 1):
                if any(t in str(item.get("text", "")) for t in case["expected"]):
                    first_relevant_rank = rank
                    break
            summary_rows.append({
                "strategy": strategy, "case_id": case["id"], "query": case["query"],
                "top_k": args.top_k, "expected_count": len(case["expected"]),
                "found_count": len(found), "coverage": round(coverage, 4),
                "first_relevant_rank": first_relevant_rank,
                "found_terms": ";".join(found),
                "missing_terms": ";".join(t for t in case["expected"] if t not in combined),
            })
            print(f"[{case['id']}] cobertura {len(found)}/{len(case['expected'])} ({coverage:.1%}); "
                  f"primer fragmento relevante: {first_relevant_rank or 'no encontrado'}")
            for rank, item in enumerate(results, 1):
                txt = str(item.get("text", ""))
                row = {
                    "strategy": strategy, "case_id": case["id"], "query": case["query"],
                    "rank": rank, "source": item.get("source", ""),
                    "score": item.get("score", ""), "mode": item.get("mode", "e5"),
                    "expected_terms_found": ";".join(t for t in case["expected"] if t in txt),
                    "text": txt,
                }
                detail_rows.append(row)
                preview = " ".join(txt.split())[:180]
                print(f"  #{rank} score={row['score']} fuente={row['source']}")
                print("    " + preview)

    fields = list(summary_rows[0].keys())
    with (outdir / "comparacion_resumen.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(summary_rows)
    detail_fields = list(detail_rows[0].keys())
    with (outdir / "comparacion_detallada.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=detail_fields); w.writeheader(); w.writerows(detail_rows)

    global_rows = []
    for strategy in ("A_current", "B_grouped_headings"):
        rows = [r for r in summary_rows if r["strategy"] == strategy]
        found = sum(r["found_count"] for r in rows)
        total = sum(r["expected_count"] for r in rows)
        global_rows.append({"strategy": strategy, "found_terms": found,
                            "expected_terms": total, "coverage": round(found/total, 4)})
    with (outdir / "comparacion_global.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(global_rows[0].keys())); w.writeheader(); w.writerows(global_rows)

    metadata = {
        "retriever": str(retriever_path.resolve()),
        "knowledge_dir": str(args.knowledge_dir.resolve()),
        "dossier": str(args.dossier.resolve()),
        "mode": "e5", "top_k": args.top_k,
        "strategy_A": "Fragmentación de producción sin cambios.",
        "strategy_B": "Solo el dossier G1 se vuelve a fragmentar por encabezados; el resto del corpus queda igual.",
        "dossier_chunks_A": len(actual_target), "dossier_chunks_B": len(grouped_chunks),
        "query_count": len(QUERIES),
        "note": "La cobertura es presencia literal de términos esperados en top-k; no evalúa respuestas generadas por Qwen.",
    }
    (outdir / "metadatos.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nComparación finalizada.")
    print("Resultados:", outdir.resolve())
    print("Resumen:", (outdir / "comparacion_resumen.csv").resolve())
    print("Detalle:", (outdir / "comparacion_detallada.csv").resolve())
    print("Global:", (outdir / "comparacion_global.csv").resolve())
    print("\nResumen global:")
    for row in global_rows:
        print(f"  {row['strategy']}: {row['found_terms']}/{row['expected_terms']} "
              f"({row['coverage']:.1%})")
    print("\nNo se modificó ningún archivo de producción.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
