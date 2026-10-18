# -*- coding: utf-8 -*-
"""
G1-RAG-03: comparación experimental de fragmentación anatómica.
No modifica el recuperador ni ningún archivo de producción.

Desde la raíz del proyecto:
  python Tests\compare_g1_chunking_retrieval_v3.py
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

CASES = [
    ("G1-01", "Enumerá las seis articulaciones de la pierna izquierda del Unitree G1 usando los nombres exactos del modelo.",
     ["left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint", "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint"]),
    ("G1-02", "¿Cuáles son las tres articulaciones de la cintura del G1 y en qué orden aparecen en el bloque actuator del MJCF?",
     ["waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint"]),
    ("G1-03", "¿Cuáles son los cuatro sensores IMU definidos en el modelo MJCF y qué mide cada uno?",
     ["imu-torso-angular-velocity", "imu-torso-linear-acceleration", "imu-pelvis-angular-velocity", "imu-pelvis-linear-acceleration"]),
    ("G1-04", "Explicá la diferencia entre el sitio imu_in_torso y el sensor imu-torso-angular-velocity.",
     ["imu_in_torso", "imu-torso-angular-velocity"]),
    ("G1-05", "Enumerá las siete articulaciones de la mano derecha del G1 con sus identificadores exactos.",
     ["right_hand_thumb_0_joint", "right_hand_thumb_1_joint", "right_hand_thumb_2_joint", "right_hand_index_0_joint", "right_hand_index_1_joint", "right_hand_middle_0_joint", "right_hand_middle_1_joint"]),
    ("G1-06", "Enumerá los 43 actuadores del modelo G1 en el orden exacto en que aparecen en el bloque actuator del MJCF.",
     ["left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint", "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",
      "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint", "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint",
      "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
      "left_shoulder_pitch_joint", "left_shoulder_roll_joint", "left_shoulder_yaw_joint", "left_elbow_joint", "left_wrist_roll_joint", "left_wrist_pitch_joint", "left_wrist_yaw_joint",
      "left_hand_thumb_0_joint", "left_hand_thumb_1_joint", "left_hand_thumb_2_joint", "left_hand_middle_0_joint", "left_hand_middle_1_joint", "left_hand_index_0_joint", "left_hand_index_1_joint",
      "right_shoulder_pitch_joint", "right_shoulder_roll_joint", "right_shoulder_yaw_joint", "right_elbow_joint", "right_wrist_roll_joint", "right_wrist_pitch_joint", "right_wrist_yaw_joint",
      "right_hand_thumb_0_joint", "right_hand_thumb_1_joint", "right_hand_thumb_2_joint", "right_hand_index_0_joint", "right_hand_index_1_joint", "right_hand_middle_0_joint", "right_hand_middle_1_joint"]),
]

def load_module(path):
    spec = importlib.util.spec_from_file_location("g1_rag03_retriever", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def split_text(text, limit, overlap):
    text = text.strip()
    if not text:
        return []
    if len(text) <= limit:
        return [text]
    pieces, start = [], 0
    while start < len(text):
        end = min(start + limit, len(text))
        if end < len(text):
            # Prioriza salto de párrafo, luego salto de línea, luego espacio.
            candidates = [text.rfind("\n\n", start, end), text.rfind("\n", start, end), text.rfind(" ", start, end)]
            boundary = max(candidates)
            if boundary > start + limit * 0.50:
                end = boundary
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return pieces

def markdown_heading_chunks(md_path, limit, overlap):
    """Baseline estructurado por encabezados Markdown."""
    lines = md_path.read_text(encoding="utf-8-sig").splitlines()
    blocks, stack, body, heading_path = [], [], [], ""
    def flush():
        nonlocal body
        content = "\n".join(body).strip()
        if content:
            blocks.append((heading_path, content))
        body = []
    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if m:
            flush()
            level, title = len(m.group(1)), m.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            heading_path = " > ".join(t for _, t in stack)
        elif line.strip():
            body.append(line.rstrip())
        elif body:
            flush()
    flush()
    out = []
    for path, content in blocks:
        prefix = f"{path}\n" if path else ""
        out.extend(split_text(prefix + content, limit, overlap))
    return out

def anatomical_chunks(md_path, limit, overlap):
    """
    Divide la sección 6.3 en unidades anatómicas usando subtítulos en negrita
    como separadores; las otras secciones siguen agrupadas por encabezados.
    Los bloques largos se subdividen respetando listas y párrafos cuando es posible.
    """
    lines = md_path.read_text(encoding="utf-8-sig").splitlines()
    section63 = False
    section64 = False
    before, after, anatomy_blocks = [], [], []
    current_title, current_body = None, []

    def flush_anatomy():
        nonlocal current_body, current_title
        body = "\n".join(current_body).strip()
        if current_title or body:
            title = current_title or "Inventario anatómico"
            anatomy_blocks.append((title, body))
        current_title, current_body = None, []

    for line in lines:
        h = re.match(r"^###\s+6\.3\b.*$", line)
        hnext = re.match(r"^###\s+6\.4\b.*$", line)
        if h:
            flush_anatomy()
            section63, section64 = True, False
            before.append(line)
            continue
        if hnext and section63:
            flush_anatomy()
            section63, section64 = False, True
            after.append(line)
            continue
        if section63:
            # Subtítulos anatómicos en negrita: A. Pierna izquierda, C. Cintura, etc.
            sub = re.match(r"^\*\*([A-G]\.\s+.+?)\*\*\s*$", line.strip())
            if sub:
                flush_anatomy()
                current_title = sub.group(1).strip()
            else:
                current_body.append(line.rstrip())
        elif section64:
            after.append(line.rstrip())
        else:
            before.append(line.rstrip())
    flush_anatomy()

    # Fragmentos de secciones no anatómicas: misma política por encabezados.
    non63_text = "\n".join(before + after)
    non63_temp = split_text(non63_text, limit, overlap)
    out = list(non63_temp)
    for title, body in anatomy_blocks:
        # Conserva encabezado general + etiqueta anatómica para mejorar el contexto semántico.
        full = f"6.3 Inventario nominal de las 43 articulaciones actuadas\n{title}\n{body}".strip()
        out.extend(split_text(full, limit, overlap))
    return [x for x in out if len(x) > 25]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["e5"], default="e5")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--knowledge-dir", type=Path, default=Path("Knowledge"))
    parser.add_argument("--dossier", type=Path, default=Path("Knowledge/Unitree/G1/Unitree_G1_Dossier_Tecnico_GIAR_ORION.md"))
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    retriever_file = Path("Agent/MultilingualKnowledgeRetriever.py")
    if not retriever_file.is_file():
        print("ERROR: ejecutá desde la raíz del proyecto; no se encuentra", retriever_file.resolve())
        return 2
    if not args.dossier.is_file():
        print("ERROR: no se encuentra el dossier:", args.dossier.resolve())
        return 2

    module = load_module(retriever_file)
    Retriever = module.MultilingualKnowledgeRetriever
    kwargs = {"knowledge_dir": args.knowledge_dir, "mode": "e5"}
    if args.device:
        kwargs["device"] = args.device
    retriever = Retriever(**kwargs)
    original_chunks = list(retriever.chunks)

    dossier_rel = str(args.dossier.resolve().relative_to(args.knowledge_dir.resolve())).replace("\\", "/")
    actual_chunks = [c for c in original_chunks if c.source.replace("\\", "/") == dossier_rel]
    if not actual_chunks:
        print("ERROR: el recuperador no cargó el dossier. Fuente buscada:", dossier_rel)
        return 2

    heading_texts = markdown_heading_chunks(args.dossier, retriever.chunk_chars, retriever.overlap_chars)
    anatomical_texts = anatomical_chunks(args.dossier, retriever.chunk_chars, retriever.overlap_chars)

    # A = producción; B = experimento previo; C = agrupación anatómica.
    # Para hacer comparación reproducible, re-embebe B y C con el mismo E5.
    def build_chunks(texts):
        chunks = [module.KnowledgeChunk(source=dossier_rel, text=t) for t in texts]
        vectors = retriever._e5_model.encode(
            ["passage: " + c.text for c in chunks],
            batch_size=retriever.batch_size, convert_to_numpy=True,
            normalize_embeddings=True, show_progress_bar=True
        )
        for c, v in zip(chunks, vectors):
            c.embedding_e5 = v.astype("float32")
        return chunks

    b_chunks = build_chunks(heading_texts)
    c_chunks = build_chunks(anatomical_texts)
    other_chunks = [c for c in original_chunks if c.source.replace("\\", "/") != dossier_rel]
    strategies = [
        ("A_current", original_chunks),
        ("B_grouped_headings", other_chunks + b_chunks),
        ("C_anatomical_groups", other_chunks + c_chunks),
    ]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path("Tests") / f"results_g1_rag03_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    summary, details = [], []

    print(f"Dossier: {args.dossier.resolve()}")
    print(f"Fragmentos actuales del dossier: {len(actual_chunks)}")
    print(f"Fragmentos B por encabezados: {len(b_chunks)}")
    print(f"Fragmentos C anatómicos: {len(c_chunks)}")
    print(f"Consultas: {len(CASES)} | top_k={args.top_k} | modelo=E5")
    print("No se modifica ningún archivo de producción.")

    for strategy_name, chunks in strategies:
        retriever.chunks = chunks
        print(f"\n=== {strategy_name} ===")
        for case_id, query, expected in CASES:
            results = retriever.search(query, top_k=args.top_k)
            texts = [str(x.get("text", "")) for x in results]
            joined = "\n".join(texts)
            found = [term for term in expected if term in joined]
            ranks = [i for i, t in enumerate(texts, 1) if any(term in t for term in expected)]
            first_rank = ranks[0] if ranks else ""
            hit = int(bool(ranks))
            row = {
                "strategy": strategy_name, "case_id": case_id, "query": query,
                "top_k": args.top_k, "expected_count": len(expected),
                "found_count": len(found), "recall_at_k_literal": round(len(found)/len(expected), 4),
                "hit_at_k": hit, "first_relevant_rank": first_rank,
                "all_terms_found": int(len(found) == len(expected)),
                "found_terms": ";".join(found),
                "missing_terms": ";".join(t for t in expected if t not in joined),
            }
            summary.append(row)
            print(f"{case_id}: {len(found)}/{len(expected)}; Hit@{args.top_k}={hit}; "
                  f"primer relevante={first_rank or 'no'}; completo={row['all_terms_found']}")
            for rank, item in enumerate(results, 1):
                text = str(item.get("text", ""))
                details.append({
                    "strategy": strategy_name, "case_id": case_id, "rank": rank,
                    "score": item.get("score", ""), "source": item.get("source", ""),
                    "expected_terms_found": ";".join(t for t in expected if t in text),
                    "text": text,
                })

    for name, rows in [
        ("resumen.csv", summary),
        ("detalle.csv", details),
    ]:
        with (out / name).open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    global_rows = []
    for strategy_name, _ in strategies:
        rows = [r for r in summary if r["strategy"] == strategy_name]
        total = sum(r["expected_count"] for r in rows)
        found = sum(r["found_count"] for r in rows)
        global_rows.append({
            "strategy": strategy_name, "found_terms": found, "expected_terms": total,
            "recall_literal": round(found/total, 4),
            "queries_complete": sum(r["all_terms_found"] for r in rows),
            "queries_total": len(rows), "hit_at_k_count": sum(r["hit_at_k"] for r in rows),
        })
    with (out / "global.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(global_rows[0].keys()))
        writer.writeheader()
        writer.writerows(global_rows)

    metadata = {
        "experiment": "G1-RAG-03",
        "mode": "e5", "top_k": args.top_k,
        "dossier": str(args.dossier.resolve()),
        "production_retriever": str(retriever_file.resolve()),
        "A": "Fragmentación actual del recuperador.",
        "B": "Fragmentación experimental por encabezados Markdown.",
        "C": "Fragmentación experimental por subdivisiones anatómicas en negrita dentro de la sección 6.3.",
        "note": "Las métricas evalúan presencia literal en top-k; no evalúan respuestas generadas por Qwen.",
        "dossier_chunks": {"A": len(actual_chunks), "B": len(b_chunks), "C": len(c_chunks)},
    }
    (out / "metadatos.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== RESUMEN GLOBAL ===")
    for r in global_rows:
        print(f"{r['strategy']}: {r['found_terms']}/{r['expected_terms']} "
              f"({r['recall_literal']:.1%}); consultas completas "
              f"{r['queries_complete']}/{r['queries_total']}; Hit@{args.top_k} {r['hit_at_k_count']}/{r['queries_total']}")
    print("Resultados guardados en:", out.resolve())
    print("Archivos: global.csv, resumen.csv, detalle.csv, metadatos.json")
    print("No se modificó ningún archivo de producción.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
