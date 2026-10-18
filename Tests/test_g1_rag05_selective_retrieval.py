# -*- coding: utf-8 -*-
"""
G1-RAG-05: recuperación selectiva experimental para el dossier Unitree G1.

No modifica Agent/MultilingualKnowledgeRetriever.py, main.py ni archivos de Knowledge.
Ejecutar desde la raíz del proyecto:
    python Tests\test_g1_rag05_selective_retrieval.py

Evalúa:
- E5 semántico sobre Knowledge.
- búsqueda literal en fragmentos del dossier G1.
- recuperación selectiva: combina candidatos semánticos y literales, dando prioridad
  a los fragmentos que contienen identificadores esperados.
- extracción estructurada de actuadores directamente del MJCF, con orden exacto.

Nota: los términos esperados de las consultas anatómicas se declaran explícitamente.
La consulta de los 43 actuadores se construye desde el MJCF real, no desde una lista
manual. Esta es una prueba de recuperación de identificadores, no una evaluación de
la respuesta generada por Qwen.
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

CASES = [
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
    spec = importlib.util.spec_from_file_location("g1_rag05_retriever", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar el recuperador: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def get_actuators(xml_path: Path) -> list[str]:
    root = ET.parse(xml_path).getroot()
    block = root.find("actuator")
    if block is None:
        raise ValueError("El MJCF no contiene un bloque <actuator> en la raíz.")
    names = [element.attrib["joint"] for element in list(block) if "joint" in element.attrib]
    if len(names) != len(set(names)):
        raise ValueError("Se encontraron nombres de articulación actuada duplicados en el MJCF.")
    return names

def exact_terms(text: str, expected: list[str]) -> list[str]:
    found = []
    for term in expected:
        pattern = r"(?<![A-Za-z0-9_])" + re.escape(term) + r"(?![A-Za-z0-9_])"
        if re.search(pattern, text):
            found.append(term)
    return found

def literal_rank(chunks, expected):
    scored = []
    for index, chunk in enumerate(chunks):
        found = exact_terms(chunk.text, expected)
        if found:
            scored.append({
                "source": chunk.source, "text": chunk.text,
                "score": len(found), "_found": found, "_index": index,
            })
    scored.sort(key=lambda item: (-len(item["_found"]), item["_index"]))
    return scored

def selective_rank(semantic_results, literal_results, top_k):
    # Prioridad a los fragmentos que contienen identificadores esperados;
    # dentro de cada grupo conserva el orden literal o semántico de origen.
    output, seen = [], set()
    for item in literal_results + semantic_results:
        key = (item.get("source", ""), item.get("text", ""))
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
        if len(output) >= top_k:
            break
    return output

def save_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--knowledge-dir", type=Path, default=Path("Knowledge"))
    parser.add_argument("--dossier", type=Path, default=Path("Knowledge/Unitree/G1/Unitree_G1_Dossier_Tecnico_GIAR_ORION.md"))
    parser.add_argument("--xml", type=Path, default=Path("Knowledge/Unitree/G1/g1_29dof_with_hand.xml"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    retriever_path = Path("Agent/MultilingualKnowledgeRetriever.py")
    for path in (retriever_path, args.knowledge_dir, args.dossier, args.xml):
        if not path.exists():
            print(f"ERROR: no se encuentra: {path.resolve()}")
            return 2
    if args.top_k < 1:
        print("ERROR: --top-k debe ser >= 1")
        return 2

    actuator_names = get_actuators(args.xml)
    cases = CASES + [
        ("G1-06", f"Enumerá los {len(actuator_names)} actuadores del modelo G1 en el orden exacto del bloque actuator del MJCF.",
         actuator_names)
    ]

    module = load_module(retriever_path)
    kwargs = {"knowledge_dir": args.knowledge_dir, "mode": "e5"}
    if args.device:
        kwargs["device"] = args.device

    print("Inicializando E5...")
    init_start = time.perf_counter()
    retriever = module.MultilingualKnowledgeRetriever(**kwargs)
    init_seconds = time.perf_counter() - init_start

    dossier_rel = str(args.dossier.resolve().relative_to(args.knowledge_dir.resolve())).replace("\\", "/")
    dossier_chunks = [chunk for chunk in retriever.chunks
                      if chunk.source.replace("\\", "/") == dossier_rel]
    if not dossier_chunks:
        print(f"ERROR: el recuperador no cargó el dossier: {dossier_rel}")
        return 2

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path("Tests") / f"results_g1_rag05_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    summary, details = [], []

    print(f"Dossier: {args.dossier.resolve()}")
    print(f"MJCF: {args.xml.resolve()}")
    print(f"Actuadores extraídos del MJCF: {len(actuator_names)}")
    print(f"Fragmentos del corpus: {len(retriever.chunks)}; del dossier: {len(dossier_chunks)}")
    print(f"top_k={args.top_k}; inicialización={init_seconds:.1f} s")
    print("Producción intacta: no se modifica ningún archivo de Agent ni main.py.")

    for case_id, query, expected in cases:
        start = time.perf_counter()
        semantic_results = retriever.search(query, top_k=args.top_k)
        semantic_time = time.perf_counter() - start
        literal_results = literal_rank(dossier_chunks, expected)
        # La estrategia selectiva usa fragmentos literales primero y rellena
        # con E5 solo si no alcanza top_k.
        selective_results = selective_rank(semantic_results, literal_results, args.top_k)

        # Caso especial: los 43 actuadores se extraen del MJCF; no se mide como
        # si el RAG tuviera que reconstruir el XML a partir de fragmentos.
        structured_result = None
        if case_id == "G1-06":
            structured_result = actuator_names

        strategies = [
            ("A_E5", semantic_results),
            ("B_literal", literal_results[:args.top_k]),
            ("C_selective", selective_results),
        ]
        if case_id == "G1-06":
            strategies.append(("D_MJCF_structured", [{
                "source": str(args.xml), "text": "\n".join(structured_result),
                "score": 1.0
            }]))

        for strategy, results in strategies:
            joined = "\n".join(str(item.get("text", "")) for item in results)
            found = exact_terms(joined, expected)
            order_ok = ""
            if case_id == "G1-06" and strategy == "D_MJCF_structured":
                extracted = [line.strip() for line in joined.splitlines() if line.strip()]
                order_ok = int(extracted == actuator_names)
            elif case_id == "G1-06":
                # El orden de apariciones se calcula sobre el texto concatenado,
                # y solo se informa; no equivale a demostrar el orden del XML.
                positions = [joined.find(term) for term in expected if term in joined]
                order_ok = int(len(found) == len(expected) and positions == sorted(positions))
            relevant_ranks = [rank for rank, item in enumerate(results, 1)
                              if exact_terms(str(item.get("text", "")), expected)]
            row = {
                "strategy": strategy, "case_id": case_id, "query": query,
                "top_k": args.top_k, "expected_count": len(expected),
                "found_count": len(found),
                "recall_literal": round(len(found) / len(expected), 4),
                "hit_at_k": int(bool(relevant_ranks)),
                "first_relevant_rank": relevant_ranks[0] if relevant_ranks else "",
                "all_terms_found": int(len(found) == len(expected)),
                "order_matches_mjcf": order_ok,
                "found_terms": ";".join(found),
                "missing_terms": ";".join(term for term in expected if term not in joined),
                "literal_candidate_chunks": len(literal_results),
                "e5_search_seconds": round(semantic_time, 6),
            }
            summary.append(row)
            print(f"{strategy:18} {case_id}: {len(found)}/{len(expected)}; "
                  f"completo={row['all_terms_found']}"
                  + (f"; orden_MJCF={order_ok}" if order_ok != "" else ""))

            for rank, item in enumerate(results, 1):
                text = str(item.get("text", ""))
                details.append({
                    "strategy": strategy, "case_id": case_id, "rank": rank,
                    "score": item.get("score", ""), "source": item.get("source", ""),
                    "expected_terms_found": ";".join(exact_terms(text, expected)),
                    "text": text,
                })

    global_rows = []
    for strategy in ("A_E5", "B_literal", "C_selective"):
        rows = [r for r in summary if r["strategy"] == strategy]
        expected_count = sum(r["expected_count"] for r in rows)
        found_count = sum(r["found_count"] for r in rows)
        global_rows.append({
            "strategy": strategy, "found_terms": found_count,
            "expected_terms": expected_count,
            "recall_literal": round(found_count / expected_count, 4),
            "queries_complete": sum(r["all_terms_found"] for r in rows),
            "queries_total": len(rows),
            "hit_at_k_count": sum(r["hit_at_k"] for r in rows),
        })

    # Resultado estructurado separado: no se mezcla con el promedio de RAG.
    structured = [r for r in summary if r["strategy"] == "D_MJCF_structured"]
    for filename, rows in (
        ("global.csv", global_rows),
        ("resumen.csv", summary),
        ("detalle.csv", details),
    ):
        save_csv(out / filename, rows)

    metadata = {
        "experiment": "G1-RAG-05",
        "timestamp": stamp,
        "knowledge_dir": str(args.knowledge_dir.resolve()),
        "dossier": str(args.dossier.resolve()),
        "mjcf": str(args.xml.resolve()),
        "mjcf_actuator_names_in_xml_order": actuator_names,
        "mjcf_actuator_count": len(actuator_names),
        "top_k": args.top_k,
        "device": retriever.device,
        "e5_model": module.E5_MODEL_NAME,
        "total_chunks": len(retriever.chunks),
        "dossier_chunks": len(dossier_chunks),
        "initialization_seconds": round(init_seconds, 3),
        "structured_actuator_check": structured,
        "note": "Métricas de RAG e extracción estructurada se informan por separado. El orden de texto recuperado no demuestra orden original del MJCF."
    }
    (out / "metadatos.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== RESUMEN GLOBAL RAG ===")
    for row in global_rows:
        print(f"{row['strategy']}: {row['found_terms']}/{row['expected_terms']} "
              f"({row['recall_literal']:.1%}); completas "
              f"{row['queries_complete']}/{row['queries_total']}; "
              f"Hit@{args.top_k} {row['hit_at_k_count']}/{row['queries_total']}")
    print("\n=== EXTRACCIÓN ESTRUCTURADA MJCF ===")
    if structured:
        row = structured[0]
        print(f"Actuadores: {row['found_count']}/{row['expected_count']}; "
              f"coincidencia de orden: {row['order_matches_mjcf']}")
    print(f"\nResultados guardados en: {out.resolve()}")
    print("Archivos: global.csv, resumen.csv, detalle.csv, metadatos.json")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
