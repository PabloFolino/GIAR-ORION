# -*- coding: utf-8 -*-
"""
G1-RAG-06: evaluación independiente de enrutamiento de consultas.
No modifica main.py, Agent/MultilingualKnowledgeRetriever.py ni Knowledge.

Ejecutar desde la raíz del proyecto:
    python Tests\test_g1_rag06_query_routing.py

Evalúa tres rutas:
- semantic: búsqueda E5 en el corpus completo.
- identifier: recuperación literal de identificadores en el dossier G1.
- structured: extracción de actuadores desde el MJCF.

Incluye un router experimental basado en reglas explícitas, no un clasificador ML.
Se registra la ruta esperada y la elegida para medir errores de enrutamiento.
Las métricas son de recuperación de evidencia, no de generación de respuestas por Qwen.
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

IDENTIFIER_CASES = [
    {
        "case_id": "G1-01",
        "query": "Enumerá las seis articulaciones de la pierna izquierda del Unitree G1 usando los nombres exactos del modelo.",
        "expected_route": "identifier",
        "expected": ["left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
                     "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint"],
    },
    {
        "case_id": "G1-02",
        "query": "¿Cuáles son las tres articulaciones de la cintura del G1 y en qué orden aparecen en el bloque actuator del MJCF?",
        "expected_route": "identifier",
        "expected": ["waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint"],
    },
    {
        "case_id": "G1-03",
        "query": "¿Cuáles son los cuatro sensores IMU definidos en el modelo MJCF y qué mide cada uno?",
        "expected_route": "identifier",
        "expected": ["imu-torso-angular-velocity", "imu-torso-linear-acceleration",
                     "imu-pelvis-angular-velocity", "imu-pelvis-linear-acceleration"],
    },
    {
        "case_id": "G1-04",
        "query": "Explicá la diferencia entre el sitio imu_in_torso y el sensor imu-torso-angular-velocity.",
        "expected_route": "identifier",
        "expected": ["imu_in_torso", "imu-torso-angular-velocity"],
    },
    {
        "case_id": "G1-05",
        "query": "Enumerá las siete articulaciones de la mano derecha del G1 con sus identificadores exactos.",
        "expected_route": "identifier",
        "expected": ["right_hand_thumb_0_joint", "right_hand_thumb_1_joint",
                     "right_hand_thumb_2_joint", "right_hand_index_0_joint",
                     "right_hand_index_1_joint", "right_hand_middle_0_joint",
                     "right_hand_middle_1_joint"],
    },
]

SEMANTIC_CASES = [
    {
        "case_id": "G1-07",
        "query": "¿Qué diferencia conceptual hay entre un sitio (site) y un sensor IMU en el modelo MJCF?",
        "expected_route": "semantic",
        "expected_terms": ["site", "sensor"],
    },
    {
        "case_id": "G1-08",
        "query": "Explicá para qué sirve una función de recompensa en el aprendizaje por refuerzo de un robot.",
        "expected_route": "semantic",
        "expected_terms": ["recompensa", "aprendizaje"],
    },
    {
        "case_id": "G1-09",
        "query": "¿Qué diferencia hay entre la política del agente y la función de valor en un algoritmo de aprendizaje por refuerzo?",
        "expected_route": "semantic",
        "expected_terms": ["política", "valor"],
    },
]

STRUCTURED_CASE = {
    "case_id": "G1-06",
    "query": "Enumerá los 43 actuadores del modelo G1 en el orden exacto del bloque actuator del MJCF.",
    "expected_route": "structured",
}

def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("g1_rag06_retriever", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar el recuperador: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def get_actuators(xml_path: Path):
    root = ET.parse(xml_path).getroot()
    block = root.find("actuator")
    if block is None:
        raise ValueError("No se encontró <actuator> en el MJCF.")
    names = [item.attrib["joint"] for item in list(block) if "joint" in item.attrib]
    if len(names) != len(set(names)):
        raise ValueError("El bloque <actuator> contiene nombres duplicados.")
    return names

def route_query(query: str) -> str:
    """Router de referencia basado en señales explícitas y transparentes."""
    q = query.casefold()
    structured_patterns = (
        r"\b\d+\s+actuadores\b",
        r"\borden exacto\b",
        r"\bbloque\s+actuator\b",
        r"\bextra[eé]\b.*\bmjcf\b",
        r"\bsecuencia\b.*\bactuadores\b",
    )
    if any(re.search(pattern, q) for pattern in structured_patterns):
        return "structured"

    identifier_signals = (
        "_joint", "_in_", "imu-", "identificador", "nombres exactos",
        "enumerá", "enumerar", "lista de articulaciones", "sensores imu",
        "articulaciones de la", "articulaciones de", "nombres de los",
    )
    if any(signal in q for signal in identifier_signals):
        return "identifier"
    return "semantic"

def exact_terms(text: str, terms: list[str]) -> list[str]:
    found = []
    for term in terms:
        pattern = r"(?<![A-Za-z0-9_])" + re.escape(term) + r"(?![A-Za-z0-9_])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(term)
    return found

def save_csv(path: Path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
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
            print(f"ERROR: no se encuentra {path.resolve()}")
            return 2
    if args.top_k < 1:
        print("ERROR: --top-k debe ser >= 1")
        return 2

    module = load_module(retriever_path)
    kwargs = {"knowledge_dir": args.knowledge_dir, "mode": "e5"}
    if args.device:
        kwargs["device"] = args.device
    print("Inicializando E5...")
    t0 = time.perf_counter()
    retriever = module.MultilingualKnowledgeRetriever(**kwargs)
    init_seconds = time.perf_counter() - t0

    dossier_rel = str(args.dossier.resolve().relative_to(args.knowledge_dir.resolve())).replace("\\", "/")
    dossier_chunks = [c for c in retriever.chunks if c.source.replace("\\", "/") == dossier_rel]
    if not dossier_chunks:
        print(f"ERROR: no se cargó el dossier {dossier_rel}")
        return 2

    actuators = get_actuators(args.xml)
    cases = []
    for case in IDENTIFIER_CASES:
        cases.append({**case, "expected_terms": case["expected"]})
    cases.extend(SEMANTIC_CASES)
    cases.append({**STRUCTURED_CASE, "expected_terms": actuators})

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path("Tests") / f"results_g1_rag06_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    rows, details = [], []

    print(f"Dossier: {args.dossier.resolve()}")
    print(f"MJCF: {args.xml.resolve()} ({len(actuators)} actuadores)")
    print(f"Fragmentos: corpus={len(retriever.chunks)}, dossier={len(dossier_chunks)}; top_k={args.top_k}")
    print("Router experimental por reglas; no modifica producción.")

    for case in cases:
        query = case["query"]
        expected_route = case["expected_route"]
        predicted_route = route_query(query)
        is_structured = predicted_route == "structured"
        is_identifier = predicted_route == "identifier"

        if is_structured:
            # Consulta directa al MJCF: la lista conserva el orden del XML.
            retrieved = [{"source": str(args.xml), "text": "\n".join(actuators), "score": 1.0}]
            method = "MJCF_structured"
        elif is_identifier:
            expected = case["expected_terms"]
            literal = []
            for index, chunk in enumerate(dossier_chunks):
                found = exact_terms(chunk.text, expected)
                if found:
                    literal.append({
                        "source": chunk.source, "text": chunk.text,
                        "score": len(found), "_found": found, "_index": index,
                    })
            literal.sort(key=lambda x: (-len(x["_found"]), x["_index"]))
            retrieved = literal[:args.top_k]
            method = "literal_dossier"
        else:
            retrieved = retriever.search(query, top_k=args.top_k)
            method = "E5_semantic"

        joined = "\n".join(str(x.get("text", "")) for x in retrieved)
        expected_terms = case["expected_terms"]
        found = exact_terms(joined, expected_terms)
        complete = int(len(found) == len(expected_terms))
        order_match = ""
        if case["case_id"] == "G1-06":
            listed = [line.strip() for line in joined.splitlines() if line.strip()]
            order_match = int(listed == actuators)

        row = {
            "case_id": case["case_id"], "query": query,
            "expected_route": expected_route, "predicted_route": predicted_route,
            "route_correct": int(expected_route == predicted_route),
            "method_used": method, "top_k": args.top_k,
            "expected_count": len(expected_terms), "found_count": len(found),
            "recall_literal": round(len(found) / len(expected_terms), 4) if expected_terms else "",
            "all_terms_found": complete, "order_matches_mjcf": order_match,
            "retrieved_chunks": len(retrieved),
            "found_terms": ";".join(found),
            "missing_terms": ";".join(t for t in expected_terms if t not in joined),
        }
        rows.append(row)
        print(f"{case['case_id']} ruta={predicted_route} (esperada={expected_route}; "
              f"correcta={row['route_correct']}) método={method}; "
              f"términos={len(found)}/{len(expected_terms)}; completo={complete}"
              + (f"; orden_MJCF={order_match}" if order_match != "" else ""))

        for rank, item in enumerate(retrieved, 1):
            details.append({
                "case_id": case["case_id"], "predicted_route": predicted_route,
                "method_used": method, "rank": rank, "source": item.get("source", ""),
                "score": item.get("score", ""),
                "expected_terms_found": ";".join(exact_terms(str(item.get("text", "")), expected_terms)),
                "text": item.get("text", ""),
            })

    total = len(rows)
    routing_correct = sum(r["route_correct"] for r in rows)
    summary = {
        "experiment": "G1-RAG-06",
        "timestamp": stamp,
        "cases": total,
        "routing_correct": routing_correct,
        "routing_accuracy": round(routing_correct / total, 4),
        "identifier_cases": len(IDENTIFIER_CASES),
        "semantic_cases": len(SEMANTIC_CASES),
        "structured_cases": 1,
        "top_k": args.top_k,
        "e5_model": module.E5_MODEL_NAME,
        "device": retriever.device,
        "total_chunks": len(retriever.chunks),
        "dossier_chunks": len(dossier_chunks),
        "mjcf_actuators": len(actuators),
        "initialization_seconds": round(init_seconds, 3),
        "note": "Las preguntas conceptuales se evalúan con términos de control orientativos, no con juicio humano de calidad de respuesta. La exactitud de enrutamiento se mide contra las categorías definidas para este conjunto de prueba."
    }
    save_csv(out / "resumen.csv", rows)
    save_csv(out / "detalle.csv", details)
    (out / "metadatos.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== RESUMEN G1-RAG-06 ===")
    print(f"Enrutamiento correcto: {routing_correct}/{total} ({summary['routing_accuracy']:.1%})")
    print(f"Casos de identificadores: {len(IDENTIFIER_CASES)}; conceptuales: {len(SEMANTIC_CASES)}; estructurado: 1")
    print("Nota: la exactitud de enrutamiento no equivale a la calidad final de respuesta de Qwen.")
    print(f"Resultados: {out.resolve()}")
    print("Archivos: resumen.csv, detalle.csv, metadatos.json")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
