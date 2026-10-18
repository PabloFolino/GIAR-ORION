#!/usr/bin/env python3
# G1-RAG-10: clasificación de consultas y evaluación de cobertura de evidencia.
# Independiente; no modifica main.py, retrievers ni resultados previos.

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
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def actuator_names(xml_path):
    root = ET.parse(xml_path).getroot()
    block = root.find("actuator")
    if block is None:
        raise ValueError("No se encontró <actuator> en el nivel raíz del MJCF.")
    return [el.get("name") for el in list(block) if el.get("name")]

def classify_query(query):
    q = query.lower()
    exact_patterns = (
        r"`[^`]+`",
        r"\b[a-z]+(?:_[a-z0-9]+){2,}\b",
        r"\bidentificador(?:es)? exact",
        r"\bnombre exact",
        r"\bc[oó]mo se llama\b",
        r"\bcu[aá]l es el nombre\b",
    )
    list_patterns = (
        r"\benumer[aá]",
        r"\blista\b",
        r"\bcu[aá]ntas?\b",
        r"\btodas las articulaciones\b",
        r"\bseis articulaciones\b",
        r"\bsiete articulaciones\b",
        r"\bactuadores\b",
    )
    structured_patterns = (
        r"\border(?:n|en) exact",
        r"\bsecuencia\b",
        r"\borden.*(?:mjcf|xml|actuator)",
        r"\bactuadores.*orden\b",
        r"\bextra(?:e|er|cci[oó]n).*actuadores\b",
        r"\bcomprueba.*43\b",
    )
    semantic_patterns = (
        r"\bdiferencia\b",
        r"\bexplica",
        r"\bpor qu[eé]\b",
        r"\bc[oó]mo funciona\b",
        r"\bqu[eé] representa\b",
        r"\bqu[eé] mide\b",
        r"\brecompensa\b",
        r"\bpol[ií]tica\b",
        r"\bfunci[oó]n de valor\b",
        r"\bobservaciones?\b.*\bacci[oó]n\b",
    )
    tags = []
    if any(re.search(p, q) for p in exact_patterns):
        tags.append("identifier")
    if any(re.search(p, q) for p in list_patterns):
        tags.append("identifier_list")
    if any(re.search(p, q) for p in structured_patterns):
        tags.append("structured")
    if any(re.search(p, q) for p in semantic_patterns):
        tags.append("semantic")
    if not tags:
        tags.append("manual_classification")
    if len(tags) > 1:
        primary = "hybrid"
    else:
        primary = tags[0]
    return primary, tags

def expected_names(query, actuators):
    q = query.lower()
    if "pierna izquierda" in q or "left leg" in q or "left_hip" in q:
        return [n for n in actuators if n.startswith(("left_hip_", "left_knee_", "left_ankle_"))]
    if "pierna derecha" in q or "right leg" in q or "right_hip" in q:
        return [n for n in actuators if n.startswith(("right_hip_", "right_knee_", "right_ankle_"))]
    if "cintura" in q or "waist" in q:
        return [n for n in actuators if n.startswith("waist_")]
    if "mano derecha" in q or "right hand" in q:
        return [n for n in actuators if n.startswith("right_hand_")]
    if "mano izquierda" in q or "left hand" in q:
        return [n for n in actuators if n.startswith("left_hand_")]
    if "brazo izquierdo" in q or "left arm" in q:
        return [n for n in actuators if n.startswith(("left_shoulder_", "left_elbow_", "left_wrist_"))]
    if "brazo derecho" in q or "right arm" in q:
        return [n for n in actuators if n.startswith(("right_shoulder_", "right_elbow_", "right_wrist_"))]
    if any(x in q for x in ("todos los actuadores", "secuencia de actuadores", "orden exacto", "comprueba si son 43", "extrae todos los actuadores", "actuator")):
        return actuators
    return None

def pick(row, *names):
    for n in names:
        if n in row and row[n] not in (None, ""):
            return row[n]
    return ""

def main():
    parser = argparse.ArgumentParser(description="G1-RAG-10: clasificación y cobertura de evidencia.")
    parser.add_argument("--results-dir", default=str(DEFAULT_RESULTS))
    parser.add_argument("--mjcf", default=str(DEFAULT_MJCF))
    args = parser.parse_args()
    results_dir = Path(args.results_dir)
    if not results_dir.is_absolute():
        results_dir = ROOT / results_dir
    mjcf = Path(args.mjcf)
    if not mjcf.is_absolute():
        mjcf = ROOT / mjcf
    if not (results_dir / "resumen.csv").exists() or not (results_dir / "detalle.csv").exists():
        print(f"ERROR: faltan resumen.csv o detalle.csv en {results_dir}", file=sys.stderr)
        sys.exit(2)
    if not mjcf.exists():
        candidates = list((ROOT / "Knowledge").rglob("g1_29dof_with_hand.xml")) if (ROOT / "Knowledge").exists() else []
        if not candidates:
            print(f"ERROR: no se encontró el MJCF: {mjcf}", file=sys.stderr)
            print("Indicá su ruta con --mjcf.", file=sys.stderr)
            sys.exit(2)
        mjcf = candidates[0]

    summary = read_csv(results_dir / "resumen.csv")
    details = read_csv(results_dir / "detalle.csv")
    actuators = actuator_names(mjcf)
    grouped = {}
    for d in details:
        key = pick(d, "case_id", "query_id", "id")
        grouped.setdefault(key, []).append(d)

    out = []
    for s in summary:
        cid = pick(s, "case_id", "query_id", "id")
        query = pick(s, "query", "consulta", "question")
        primary, tags = classify_query(query)
        chunks = grouped.get(cid, [])
        # Fallback: match detail rows by query text if IDs differ.
        if not chunks and query:
            chunks = [d for d in details if pick(d, "query", "consulta", "question") == query]
        texts = [pick(d, "text", "retrieved_text", "fragment_text", "chunk_text") for d in chunks]
        combined = "\n".join(texts)
        expected = expected_names(query, actuators)
        found = [n for n in expected if n in combined] if expected is not None else []
        missing = [n for n in expected if n not in combined] if expected is not None else []
        coverage = round(len(found) / len(expected), 4) if expected else ""
        # Sequence check uses occurrence order in combined retrieved text, not just set coverage.
        positions = [combined.find(n) for n in expected] if expected is not None else []
        order_match = bool(expected) and all(pos >= 0 for pos in positions) and positions == sorted(positions)
        needs_semantic = "semantic" in tags or primary == "manual_classification"
        if expected is not None:
            coverage_verdict = "PASS" if not missing else ("PARTIAL" if found else "FAIL")
        else:
            coverage_verdict = "NOT_APPLICABLE"
        if "structured" in tags and expected is not None:
            sequence_verdict = "ORDER_MATCH_IN_EVIDENCE" if order_match else "ORDER_NOT_VERIFIED_IN_EVIDENCE"
        else:
            sequence_verdict = "NOT_APPLICABLE"
        out.append({
            "case_id": cid,
            "query": query,
            "primary_class": primary,
            "all_class_tags": ";".join(tags),
            "predicted_route": pick(s, "predicted_route", "route", "ruta"),
            "retrieved_fragment_count": len(texts),
            "expected_identifier_count": len(expected) if expected is not None else "",
            "found_identifier_count": len(found) if expected is not None else "",
            "identifier_coverage": coverage,
            "missing_identifiers": ";".join(missing),
            "identifier_coverage_verdict": coverage_verdict,
            "sequence_check": sequence_verdict,
            "semantic_review_required": "SI" if needs_semantic else "NO",
            "semantic_judgment": "PENDIENTE" if needs_semantic else "NO_APLICA",
            "notes": "La cobertura verifica presencia literal. El orden se evalúa solo dentro del texto recuperado; no valida la respuesta final."
        })

    out_csv = results_dir / "g1_rag10_evidence_coverage.csv"
    write_csv(out_csv, out)
    counts = {}
    for row in out:
        counts[row["primary_class"]] = counts.get(row["primary_class"], 0) + 1
    meta = {
        "experiment": "G1-RAG-10",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "cases": len(out),
        "mjcf": str(mjcf),
        "mjcf_actuator_count": len(actuators),
        "primary_class_counts": counts,
        "output": str(out_csv),
        "limitations": [
            "Clasificación basada en reglas y expresiones regulares; revisar manualmente los casos híbridos.",
            "La presencia de identificadores no garantiza que la respuesta final sea correcta.",
            "La verificación de orden solo observa el texto recuperado y no sustituye la extracción del XML.",
            "Las consultas semánticas quedan pendientes de juicio sobre relevancia y suficiencia."
        ]
    }
    meta_path = results_dir / "g1_rag10_metadatos.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("G1-RAG-10 completado.")
    print(f"Casos: {len(out)}")
    print(f"Actuadores en MJCF: {len(actuators)}")
    print(f"Clases: {counts}")
    print(f"CSV: {out_csv}")
    print(f"Metadatos: {meta_path}")

if __name__ == "__main__":
    main()
