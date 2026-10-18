#!/usr/bin/env python3
# G1-RAG-09: validación determinista de identificadores y extracción estructurada.
# No modifica archivos de producción ni sobrescribe resultados previos.

import argparse
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = ROOT / "Tests" / "results_g1_rag07_20261012_175223"
DEFAULT_MJCF = ROOT / "Knowledge" / "Unitree" / "G1" / "g1_29dof_with_hand.xml"

def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

def get_actuators(xml_path):
    root = ET.parse(xml_path).getroot()
    actuator = root.find("actuator")
    if actuator is None:
        raise ValueError("El MJCF no contiene un bloque <actuator> en la raíz.")
    names = []
    for elem in list(actuator):
        name = elem.get("name")
        if name:
            names.append(name)
    return names

def names_for_query(query, actuator_names):
    q = query.lower()
    # Deriva conjuntos esperados desde los nombres reales del XML, no desde el texto recuperado.
    if "pierna izquierda" in q or "left leg" in q or "left_hip" in q:
        return [n for n in actuator_names if n.startswith(("left_hip_", "left_knee_", "left_ankle_"))]
    if "pierna derecha" in q or "right leg" in q or "right_hip" in q:
        return [n for n in actuator_names if n.startswith(("right_hip_", "right_knee_", "right_ankle_"))]
    if "cintura" in q or "waist" in q:
        return [n for n in actuator_names if n.startswith("waist_")]
    if "mano derecha" in q or "right hand" in q:
        return [n for n in actuator_names if n.startswith("right_hand_")]
    if "mano izquierda" in q or "left hand" in q:
        return [n for n in actuator_names if n.startswith("left_hand_")]
    if "brazo izquierdo" in q or "left arm" in q:
        return [n for n in actuator_names if n.startswith(("left_shoulder_", "left_elbow_", "left_wrist_"))]
    if "brazo derecho" in q or "right arm" in q:
        return [n for n in actuator_names if n.startswith(("right_shoulder_", "right_elbow_", "right_wrist_"))]
    if any(x in q for x in ("todos los actuadores", "todos los actuadores", "secuencia de actuadores", "orden exacto", "comprueba si son 43", "extrae todos los actuadores", "actuator")):
        return actuator_names
    return None

def main():
    ap = argparse.ArgumentParser(description="G1-RAG-09: validación determinista de evidencia.")
    ap.add_argument("--results-dir", default=str(DEFAULT_RESULTS), help="Directorio con resumen.csv y detalle.csv.")
    ap.add_argument("--mjcf", default=str(DEFAULT_MJCF), help="Ruta al g1_29dof_with_hand.xml.")
    args = ap.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.is_absolute():
        results_dir = ROOT / results_dir
    mjcf = Path(args.mjcf)
    if not mjcf.is_absolute():
        mjcf = ROOT / mjcf

    summary_path = results_dir / "resumen.csv"
    detail_path = results_dir / "detalle.csv"
    if not summary_path.exists() or not detail_path.exists():
        print(f"ERROR: no encuentro resumen.csv y detalle.csv en: {results_dir}", file=sys.stderr)
        print('Usá --results-dir "Tests\\results_g1_rag07_20261012_175223"', file=sys.stderr)
        sys.exit(2)
    if not mjcf.exists():
        # Buscar el nombre exacto dentro del árbol Knowledge, sin modificar nada.
        matches = list((ROOT / "Knowledge").rglob("g1_29dof_with_hand.xml")) if (ROOT / "Knowledge").exists() else []
        if matches:
            mjcf = matches[0]
        else:
            print(f"ERROR: no encuentro el MJCF: {mjcf}", file=sys.stderr)
            print("Indicá su ruta con --mjcf.", file=sys.stderr)
            sys.exit(2)

    summary = read_csv(summary_path)
    details = read_csv(detail_path)
    actuators = get_actuators(mjcf)
    detail_by_case = {}
    for row in details:
        detail_by_case.setdefault(row.get("case_id", ""), []).append(row)

    out = []
    for s in summary:
        case_id = s.get("case_id", "")
        query = s.get("query", "")
        kind = (s.get("case_kind") or "").lower()
        chunks = detail_by_case.get(case_id, [])
        texts = [r.get("text", "") or "" for r in chunks]
        combined = "\n".join(texts)
        expected = names_for_query(query, actuators)
        route = (s.get("predicted_route") or "").lower()

        if expected is not None and (kind in ("identifier", "hybrid", "structured") or route in ("identifier", "structured")):
            found = [name for name in expected if name in combined]
            missing = [name for name in expected if name not in combined]
            ordered_in_evidence = [name for name in expected if name in combined]
            order_ok = ordered_in_evidence == expected and len(found) == len(expected)
            verdict = "PASS" if len(found) == len(expected) else ("PARTIAL" if found else "FAIL")
            method = "XML_ground_truth_vs_retrieved_text"
            expected_n = len(expected)
            found_n = len(found)
            notes = "Lista esperada derivada del MJCF; presencia verificada en fragmentos recuperados."
            if kind == "structured" or "orden" in query.lower() or "secuencia" in query.lower():
                notes += " La igualdad de orden en el texto recuperado se informa por separado."
        else:
            found = []
            missing = []
            expected_n = ""
            found_n = ""
            order_ok = ""
            verdict = "NEEDS_SEMANTIC_REVIEW"
            method = "manual_or_semantic_review"
            notes = "No se aplica conteo literal automático: requiere juicio sobre significado y suficiencia."

        # Para listas ordenadas, evaluar secuencia encontrada en el texto, no solo cobertura.
        if expected is not None and expected:
            positions = [combined.find(name) for name in expected if name in combined]
            sequence_order = all(a < b for a, b in zip(positions, positions[1:])) if positions else False
        else:
            sequence_order = ""

        out.append({
            "case_id": case_id,
            "query": query,
            "case_kind": kind,
            "predicted_route": route,
            "validation_method": method,
            "expected_identifier_count": expected_n,
            "found_identifier_count": found_n,
            "coverage": round(found_n / expected_n, 4) if isinstance(expected_n, int) and expected_n else "",
            "missing_identifiers": ";".join(missing),
            "all_identifiers_present": verdict == "PASS" if verdict != "NEEDS_SEMANTIC_REVIEW" else "",
            "sequence_order_in_retrieved_text": sequence_order,
            "deterministic_verdict": verdict,
            "manual_review_required": "SI" if verdict != "PASS" else ("SI" if kind == "semantic" else "NO"),
            "review_notes": notes,
        })

    output_path = results_dir / "g1_rag09_deterministic_review.csv"
    write_csv(output_path, out)
    summary_counts = {}
    for row in out:
        summary_counts[row["deterministic_verdict"]] = summary_counts.get(row["deterministic_verdict"], 0) + 1
    meta = {
        "experiment": "G1-RAG-09",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "results_dir": str(results_dir),
        "mjcf": str(mjcf),
        "mjcf_actuator_count": len(actuators),
        "cases": len(out),
        "verdict_counts": summary_counts,
        "output": str(output_path),
        "limitations": [
            "La validación literal verifica presencia de identificadores, no que una respuesta redactada sea correcta.",
            "Las consultas semánticas quedan pendientes de revisión semántica.",
            "Los grupos anatómicos se derivan de prefijos de nombres del MJCF y deben revisarse si cambia la variante del robot.",
            "La comprobación de orden en texto recuperado no sustituye la extracción estructurada del XML."
        ]
    }
    meta_path = results_dir / "g1_rag09_metadatos.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"G1-RAG-09 completado.")
    print(f"MJCF: {mjcf}")
    print(f"Actuadores en XML: {len(actuators)}")
    print(f"Casos: {len(out)}")
    print(f"Resultados: {summary_counts}")
    print(f"CSV: {output_path}")
    print(f"Metadatos: {meta_path}")

if __name__ == "__main__":
    main()
