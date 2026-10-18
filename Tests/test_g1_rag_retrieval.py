#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prueba independiente de recuperación RAG para el dossier Unitree G1.
No modifica main.py, los recuperadores ni los documentos de conocimiento.

Ejecutar desde la raíz de GIAR-ORION:
  python Tests\test_g1_rag_retrieval.py
  python Tests\test_g1_rag_retrieval.py --mode e5
  python Tests\test_g1_rag_retrieval.py --mode hybrid
"""
import argparse
import csv
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

QUERIES = [
    {
        "id": "G1-01",
        "query": "Enumerá las seis articulaciones de la pierna izquierda del Unitree G1 usando los nombres exactos del modelo.",
        "expected": [
            "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
            "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint"
        ],
    },
    {
        "id": "G1-02",
        "query": "¿Cuáles son las tres articulaciones de la cintura del G1 y en qué orden aparecen en el bloque actuator del MJCF?",
        "expected": ["waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint"],
    },
    {
        "id": "G1-03",
        "query": "¿Cuáles son los cuatro sensores IMU definidos en el modelo MJCF y qué mide cada uno?",
        "expected": [
            "imu-torso-angular-velocity", "imu-torso-linear-acceleration",
            "imu-pelvis-angular-velocity", "imu-pelvis-linear-acceleration"
        ],
    },
    {
        "id": "G1-04",
        "query": "Explicá la diferencia entre el sitio imu_in_torso y el sensor imu-torso-angular-velocity.",
        "expected": ["imu_in_torso", "imu-torso-angular-velocity"],
    },
    {
        "id": "G1-05",
        "query": "Enumerá las siete articulaciones de la mano derecha del G1 con sus identificadores exactos.",
        "expected": [
            "right_hand_thumb_0_joint", "right_hand_thumb_1_joint", "right_hand_thumb_2_joint",
            "right_hand_index_0_joint", "right_hand_index_1_joint",
            "right_hand_middle_0_joint", "right_hand_middle_1_joint"
        ],
    },
    {
        "id": "G1-06",
        "query": "Enumerá los 43 actuadores del modelo G1 en el orden exacto en que aparecen en el bloque actuator del MJCF.",
        "expected": [
            "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
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
            "right_hand_middle_0_joint", "right_hand_middle_1_joint"
        ],
    },
]

def locate_retriever():
    candidates = [
        Path("Agent/MultilingualKnowledgeRetriever.py"),
        Path("Agent/KnowledgeRetriever.py"),
        Path("Agent/KnowledgeRetriever_revisado.py"),
    ]
    for candidate in candidates:
        if candidate.is_file() and candidate.name == "MultilingualKnowledgeRetriever.py":
            return candidate
    return None

def load_module(path):
    spec = importlib.util.spec_from_file_location("g1_test_retriever", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo cargar el módulo del recuperador.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def main():
    parser = argparse.ArgumentParser(description="Evalúa recuperación de fragmentos del dossier G1.")
    parser.add_argument("--mode", choices=["e5", "bge", "hybrid"], default="e5",
                        help="Modo semántico; por defecto e5 para reducir consumo de memoria.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--knowledge-dir", type=Path, default=Path("Knowledge"))
    parser.add_argument("--device", default=None, help="Por ejemplo cuda o cpu; predeterminado automático.")
    args = parser.parse_args()

    retriever_path = locate_retriever()
    if not retriever_path:
        print("ERROR: no encuentro Agent/MultilingualKnowledgeRetriever.py desde la raíz del proyecto.")
        return 2
    if not args.knowledge_dir.is_dir():
        print("ERROR: no encuentro el directorio de conocimiento:", args.knowledge_dir.resolve())
        return 2

    print("Recuperador:", retriever_path.resolve())
    print("Conocimiento:", args.knowledge_dir.resolve())
    print("Modo:", args.mode, "| top_k:", args.top_k)
    print("Se ejecutará solo recuperación; no se invoca Qwen y no se modifican archivos fuente.")

    module = load_module(retriever_path)
    Retriever = getattr(module, "MultilingualKnowledgeRetriever", None)
    if Retriever is None:
        print("ERROR: el módulo no expone MultilingualKnowledgeRetriever.")
        return 2

    # Constructor con los argumentos documentados del recuperador actual.
    kwargs = {"knowledge_dir": args.knowledge_dir, "mode": args.mode}
    if args.device:
        kwargs["device"] = args.device
    try:
        retriever = Retriever(**kwargs)
    except TypeError as exc:
        print("ERROR al inicializar el recuperador con los argumentos esperados:", exc)
        print("No se modificó el código. Revisá la firma del constructor y compartime este error.")
        return 2

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = Path("Tests") / f"results_g1_rag_retrieval_{timestamp}"
    outdir.mkdir(parents=True, exist_ok=True)
    detailed_path = outdir / "resultados_detallados.csv"
    summary_path = outdir / "resumen.csv"
    detail_fields = ["case_id", "query", "rank", "source", "score", "mode", "expected_terms_found", "text"]
    summary_rows = []
    detail_rows = []

    for case in QUERIES:
        print(f"\n[{case['id']}] {case['query']}")
        try:
            results = retriever.search(case["query"], top_k=args.top_k)
        except Exception as exc:
            print("ERROR durante search:", repr(exc))
            return 2
        if not isinstance(results, list):
            print("ERROR: search() no devolvió una lista.")
            return 2
        combined = "\n".join(str(item.get("text", "")) for item in results)
        found = [term for term in case["expected"] if term in combined]
        missing = [term for term in case["expected"] if term not in combined]
        coverage = len(found) / len(case["expected"]) if case["expected"] else 1.0
        summary_rows.append({
            "case_id": case["id"], "query": case["query"], "top_k": args.top_k,
            "expected_count": len(case["expected"]), "found_count": len(found),
            "coverage": round(coverage, 4), "found_terms": ";".join(found),
            "missing_terms": ";".join(missing),
        })
        print(f"  Fragmentos: {len(results)} | términos encontrados: {len(found)}/{len(case['expected'])} ({coverage:.1%})")
        if missing:
            print("  Faltantes:", ", ".join(missing[:12]) + (" ..." if len(missing) > 12 else ""))
        for rank, item in enumerate(results, 1):
            text = str(item.get("text", ""))
            row = {
                "case_id": case["id"], "query": case["query"], "rank": rank,
                "source": item.get("source", ""), "score": item.get("score", ""),
                "mode": item.get("mode", args.mode),
                "expected_terms_found": ";".join(t for t in case["expected"] if t in text),
                "text": text,
            }
            detail_rows.append(row)
            preview = " ".join(text.split())[:220]
            print(f"  #{rank} score={row['score']} fuente={row['source']}")
            print("    " + preview)

    with summary_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    with detailed_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=detail_fields)
        writer.writeheader()
        writer.writerows(detail_rows)
    metadata = {
        "retriever": str(retriever_path),
        "knowledge_dir": str(args.knowledge_dir),
        "mode": args.mode,
        "top_k": args.top_k,
        "query_count": len(QUERIES),
        "note": "Mide presencia de términos esperados en los fragmentos recuperados; no evalúa respuestas de Qwen."
    }
    (outdir / "metadatos.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nPrueba terminada.")
    print("Resumen:", summary_path.resolve())
    print("Detalle:", detailed_path.resolve())
    print("Metadatos:", (outdir / "metadatos.json").resolve())
    print("\nCobertura global:", f"{sum(r['found_count'] for r in summary_rows)}/{sum(r['expected_count'] for r in summary_rows)}",
          f"({sum(r['found_count'] for r in summary_rows)/sum(r['expected_count'] for r in summary_rows):.1%})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
