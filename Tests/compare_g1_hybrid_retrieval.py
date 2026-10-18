# -*- coding: utf-8 -*-
"""
G1-RAG-04: comparación controlada entre búsqueda semántica E5, literal e híbrida.
No modifica archivos de producción.

Ejecutar desde la raíz de GIAR-ORION:
    python Tests\compare_g1_hybrid_retrieval.py

Estrategias:
  A_E5: orden del recuperador E5 actual.
  B_literal: ranking por presencia de identificadores exactos en cada fragmento.
  C_RRF: fusión de rankings E5 y literal mediante Reciprocal Rank Fusion.

La lista de actuadores de G1-06 se extrae del bloque <actuator> del MJCF indicado,
no se toma de una lista manual.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

CASES_BASE = [
    ("G1-01", "Enumerá las seis articulaciones de la pierna izquierda del Unitree G1 usando los nombres exactos del modelo.",
     ["left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
      "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint"]),
    ("G1-02", "¿Cuáles son las tres articulaciones de la cintura del G1 y en qué orden aparecen en el bloque actuator del MJCF?",
     ["waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint"]),
    ("G1-03", "¿Cuáles son los cuatro sensores IMU definidos en el modelo MJCF y qué mide cada uno?",
     ["imu-torso-angular-velocity", "imu-torso-linear-acceleration",
      "imu-pelvis-angular-velocity", "imu-pelvis-linear-acceleration"]),
    ("G1-04", "Explicá la diferencia entre el sitio imu_in_torso y el sensor imu-torso-angular-velocity.",
     ["imu_in_torso", "imu-torso-angular-velocity"]),
    ("G1-05", "Enumerá las siete articulaciones de la mano derecha del G1 con sus identificadores exactos.",
     ["right_hand_thumb_0_joint", "right_hand_thumb_1_joint",
      "right_hand_thumb_2_joint", "right_hand_index_0_joint",
      "right_hand_index_1_joint", "right_hand_middle_0_joint",
      "right_hand_middle_1_joint"]),
]

def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("g1_rag04_retriever", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar el recuperador: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def actuator_names_from_mjcf(xml_path: Path) -> list[str]:
    root = ET.parse(xml_path).getroot()
    actuator = root.find("actuator")
    if actuator is None:
        raise ValueError(f"No se encontró <actuator> en {xml_path}")
    names = []
    for item in list(actuator):
        joint = item.attrib.get("joint")
        if joint:
            names.append(joint)
    if not names:
        raise ValueError(f"No se encontraron atributos joint en <actuator> de {xml_path}")
    if len(names) != len(set(names)):
        duplicates = sorted({x for x in names if names.count(x) > 1})
        raise ValueError(f"Hay articulaciones actuadas duplicadas en MJCF: {duplicates}")
    return names

def literal_score(text: str, expected: list[str]) -> tuple[int, int]:
    # Devuelve cantidad de identificadores exactos y cantidad de coincidencias
    # como tokens completos (evita que un nombre parcial cuente por accidente).
    found = 0
    occurrences = 0
    for term in expected:
        hits = len(re.findall(r"(?<![A-Za-z0-9_])" + re.escape(term) + r"(?![A-Za-z0-9_])", text))
        if hits:
            found += 1
            occurrences += hits
    return found, occurrences

def rrf_fusion(semantic_results, literal_ranked, top_k: int, k: int = 60):
    scores = {}
    by_key = {}
    for rank, item in enumerate(semantic_results, 1):
        key = (item.get("source", ""), item.get("text", ""))
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
        by_key[key] = item
    for rank, item in enumerate(literal_ranked, 1):
        key = (item.get("source", ""), item.get("text", ""))
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
        by_key[key] = item
    ordered = sorted(scores, key=scores.get, reverse=True)[:top_k]
    return [{**by_key[key], "score": scores[key]} for key in ordered]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--knowledge-dir", type=Path, default=Path("Knowledge"))
    parser.add_argument("--dossier", type=Path, default=Path("Knowledge/Unitree/G1/Unitree_G1_Dossier_Tecnico_GIAR_ORION.md"))
    parser.add_argument("--xml", type=Path, default=Path("Knowledge/Unitree/G1/g1_29dof_with_hand.xml"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--device", default=None)
    parser.add_argument("--rrf-k", type=int, default=60)
    args = parser.parse_args()

    retriever_path = Path("Agent/MultilingualKnowledgeRetriever.py")
    for path in (retriever_path, args.knowledge_dir, args.dossier, args.xml):
        if not path.exists():
            print(f"ERROR: no se encuentra: {path.resolve()}")
            return 2
    if args.top_k < 1:
        print("ERROR: --top-k debe ser >= 1")
        return 2

    actuators = actuator_names_from_mjcf(args.xml)
    cases = CASES_BASE + [
        ("G1-06", f"Enumerá los {len(actuators)} actuadores del modelo G1 en el orden exacto del bloque actuator del MJCF.",
         actuators)
    ]

    module = load_module(retriever_path)
    kwargs = {"knowledge_dir": args.knowledge_dir, "mode": "e5"}
    if args.device:
        kwargs["device"] = args.device

    print("Inicializando recuperador E5; puede tardar según el tamaño de Knowledge...")
    started = time.perf_counter()
    retriever = module.MultilingualKnowledgeRetriever(**kwargs)
    init_seconds = time.perf_counter() - started

    # Conserva solo fragmentos del dossier para el análisis literal dirigido al dossier.
    dossier_rel = str(args.dossier.resolve().relative_to(args.knowledge_dir.resolve())).replace("\\", "/")
    dossier_chunks = [c for c in retriever.chunks if c.source.replace("\\", "/") == dossier_rel]
    if not dossier_chunks:
        print(f"ERROR: E5 no cargó el dossier esperado: {dossier_rel}")
        print("Verificá que el archivo esté dentro de --knowledge-dir y sea Markdown.")
        return 2

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path("Tests") / f"results_g1_rag04_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    summary, detail = [], []
    print(f"\nDossier: {args.dossier.resolve()}")
    print(f"MJCF: {args.xml.resolve()}")
    print(f"Actuadores extraídos del XML: {len(actuators)}")
    print(f"Fragmentos E5 totales: {len(retriever.chunks)}; fragmentos del dossier: {len(dossier_chunks)}")
    print(f"top_k={args.top_k}; inicialización E5={init_seconds:.1f} s")
    print("No se modifica ningún archivo de producción.")

    for case_id, query, expected in cases:
        t0 = time.perf_counter()
        semantic = retriever.search(query, top_k=max(args.top_k, 20))
        semantic_seconds = time.perf_counter() - t0

        # Ranking literal sobre todos los fragmentos del dossier. Se registra
        # también la cobertura por si los términos están repartidos en muchos chunks.
        literal_all = []
        for idx, chunk in enumerate(dossier_chunks):
            found, occurrences = literal_score(chunk.text, expected)
            if found:
                literal_all.append({
                    "source": chunk.source, "text": chunk.text,
                    "score": float(found) + min(occurrences, 100) / 1000.0,
                    "_literal_found": found, "_index": idx,
                })
        literal_all.sort(key=lambda x: (x["_literal_found"], x["score"]), reverse=True)
        literal_top = literal_all[:max(args.top_k, 20)]

        # RRF se aplica a las listas de candidatos semantic/literal; mantiene
        # las dos señales separadas y no altera los embeddings.
        fused = rrf_fusion(semantic, literal_top, max(args.top_k, 20), args.rrf_k)
        strategies = [
            ("A_E5", semantic[:args.top_k]),
            ("B_literal", literal_all[:args.top_k]),
            ("C_RRF", fused[:args.top_k]),
        ]

        for strategy, results in strategies:
            joined = "\n".join(str(x.get("text", "")) for x in results)
            found_terms = [term for term in expected if term in joined]
            ranks = [i for i, item in enumerate(results, 1)
                     if any(term in str(item.get("text", "")) for term in expected)]
            row = {
                "strategy": strategy, "case_id": case_id, "query": query,
                "top_k": args.top_k, "expected_count": len(expected),
                "found_count": len(found_terms),
                "recall_at_k_literal": round(len(found_terms) / len(expected), 4),
                "hit_at_k": int(bool(ranks)),
                "first_relevant_rank": ranks[0] if ranks else "",
                "all_terms_found": int(len(found_terms) == len(expected)),
                "found_terms": ";".join(found_terms),
                "missing_terms": ";".join(x for x in expected if x not in joined),
                "candidate_count_literal": len(literal_all),
                "e5_search_seconds": round(semantic_seconds, 6),
            }
            summary.append(row)
            print(f"{strategy:10} {case_id}: {len(found_terms)}/{len(expected)}; "
                  f"Hit@{args.top_k}={row['hit_at_k']}; completo={row['all_terms_found']}")
            for rank, item in enumerate(results, 1):
                text = str(item.get("text", ""))
                detail.append({
                    "strategy": strategy, "case_id": case_id, "rank": rank,
                    "score": item.get("score", ""), "source": item.get("source", ""),
                    "expected_terms_found": ";".join(x for x in expected if x in text),
                    "text": text,
                })

    global_rows = []
    for strategy in ("A_E5", "B_literal", "C_RRF"):
        rows = [r for r in summary if r["strategy"] == strategy]
        expected_n = sum(r["expected_count"] for r in rows)
        found_n = sum(r["found_count"] for r in rows)
        global_rows.append({
            "strategy": strategy, "found_terms": found_n, "expected_terms": expected_n,
            "recall_literal": round(found_n / expected_n, 4) if expected_n else 0,
            "queries_complete": sum(r["all_terms_found"] for r in rows),
            "queries_total": len(rows),
            "hit_at_k_count": sum(r["hit_at_k"] for r in rows),
        })

    for filename, rows in (("global.csv", global_rows), ("resumen.csv", summary), ("detalle.csv", detail)):
        if rows:
            with (out / filename).open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

    metadata = {
        "experiment": "G1-RAG-04",
        "timestamp": stamp,
        "knowledge_dir": str(args.knowledge_dir.resolve()),
        "dossier": str(args.dossier.resolve()),
        "mjcf": str(args.xml.resolve()),
        "mjcf_actuator_count": len(actuators),
        "mjcf_actuator_order": actuators,
        "top_k": args.top_k,
        "rrf_k": args.rrf_k,
        "device": retriever.device,
        "e5_model": module.E5_MODEL_NAME,
        "total_chunks": len(retriever.chunks),
        "dossier_chunks": len(dossier_chunks),
        "initialization_seconds": round(init_seconds, 3),
        "note": "B_literal puntúa identificadores esperados solo en fragmentos del dossier; C_RRF fusiona ranking E5 global y ranking literal del dossier."
    }
    (out / "metadatos.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== RESUMEN GLOBAL ===")
    for row in global_rows:
        print(f"{row['strategy']}: {row['found_terms']}/{row['expected_terms']} "
              f"({row['recall_literal']:.1%}); consultas completas "
              f"{row['queries_complete']}/{row['queries_total']}; "
              f"Hit@{args.top_k} {row['hit_at_k_count']}/{row['queries_total']}")
    print(f"\nResultados guardados en: {out.resolve()}")
    print("Archivos: global.csv, resumen.csv, detalle.csv, metadatos.json")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
