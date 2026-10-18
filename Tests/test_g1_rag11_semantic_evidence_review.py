#!/usr/bin/env python3
# G1-RAG-11A: prepara evaluación de evidencia semántica e híbrida.
# No llama a Ollama ni modifica el agente; prepara una planilla auditable para revisión.
import argparse, csv, json, re, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = ROOT / "Tests" / "results_g1_rag07_20261012_175223"

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

def val(row, *keys):
    for k in keys:
        if row.get(k) not in (None, ""):
            return str(row[k])
    return ""

def classify(query):
    q = query.lower()
    semantic = any(x in q for x in [
        "diferencia", "explica", "por qué", "porque", "cómo funciona",
        "qué representa", "qué mide", "recompensa", "política",
        "función de valor", "observación", "acción"
    ])
    exact = bool(re.search(r"`[^`]+`|\b[a-z]+(?:_[a-z0-9]+){2,}\b|nombre exacto|identificador", q))
    list_query = any(x in q for x in ["enumerá", "enumera", "lista", "cuáles son", "cuáles", "cuantas", "cuántas", "articulaciones"])
    ordered = any(x in q for x in ["orden exacto", "secuencia", "en orden", "orden del xml", "orden mjcf"])
    if semantic and (exact or list_query):
        return "hybrid", "La consulta pide identificar/listar y además explicar o interpretar."
    if semantic:
        return "semantic", "La consulta requiere interpretar conceptos."
    if ordered and ("actuador" in q or "actuator" in q):
        return "structured", "La consulta pide una secuencia de datos del XML."
    if exact or list_query:
        return "identifier", "La consulta pide nombres, identificadores o una lista explícita."
    return "manual", "Las reglas no clasifican con suficiente seguridad; revisar manualmente."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default=str(DEFAULT_RESULTS))
    args = ap.parse_args()
    d = Path(args.results_dir)
    if not d.is_absolute():
        d = ROOT / d
    summary_path, detail_path = d / "resumen.csv", d / "detalle.csv"
    if not summary_path.exists() or not detail_path.exists():
        print(f"ERROR: faltan resumen.csv o detalle.csv en {d}", file=sys.stderr)
        sys.exit(2)
    summaries, details = read_csv(summary_path), read_csv(detail_path)
    detail_by_id = {}
    for row in details:
        cid = val(row, "case_id", "query_id", "id")
        detail_by_id.setdefault(cid, []).append(row)
    out = []
    for s in summaries:
        cid = val(s, "case_id", "query_id", "id")
        query = val(s, "query", "consulta", "question")
        route = val(s, "predicted_route", "route", "ruta")
        cat, rationale = classify(query)
        chunks = detail_by_id.get(cid, [])
        if not chunks and query:
            chunks = [x for x in details if val(x, "query", "consulta", "question") == query]
        for rank, ch in enumerate(chunks, start=1):
            text = val(ch, "text", "retrieved_text", "fragment_text", "chunk_text")
            out.append({
                "case_id": cid,
                "query": query,
                "query_class_proposed": cat,
                "classification_rationale": rationale,
                "predicted_route": route,
                "fragment_rank": val(ch, "rank", "retrieval_rank") or rank,
                "source": val(ch, "source", "source_file", "document", "file_path"),
                "retrieved_text": text,
                "relevance_judgment": "PENDIENTE",
                "answers_query": "PENDIENTE",
                "evidence_sufficient": "PENDIENTE",
                "missing_information": "",
                "review_notes": ""
            })
    output = d / "g1_rag11a_semantic_review.csv"
    write_csv(output, out)
    # Resumen por consulta para hacer revisión menos tediosa.
    by_case = {}
    for row in out:
        by_case.setdefault(row["case_id"], row)
    case_rows = []
    for row in by_case.values():
        case_rows.append({
            "case_id": row["case_id"],
            "query": row["query"],
            "query_class_proposed": row["query_class_proposed"],
            "predicted_route": row["predicted_route"],
            "fragment_count": sum(1 for x in out if x["case_id"] == row["case_id"]),
            "overall_relevance": "PENDIENTE",
            "answerability_from_all_fragments": "PENDIENTE",
            "evidence_sufficient": "PENDIENTE",
            "missing_information": "",
            "review_notes": ""
        })
    case_path = d / "g1_rag11a_case_review.csv"
    write_csv(case_path, case_rows)
    meta = {
        "experiment": "G1-RAG-11A",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_results_dir": str(d),
        "queries": len(case_rows),
        "fragment_rows": len(out),
        "outputs": [str(output), str(case_path)],
        "status": "Review sheets prepared; judgments intentionally left pending.",
        "criteria": {
            "relevance_judgment": ["RELEVANTE", "PARCIAL", "IRRELEVANTE"],
            "answers_query": ["SI", "PARCIALMENTE", "NO"],
            "evidence_sufficient": ["SI", "NO", "NO_APLICA"],
            "overall_relevance": ["RELEVANTE", "PARCIAL", "IRRELEVANTE"],
            "answerability_from_all_fragments": ["SI", "PARCIALMENTE", "NO"]
        },
        "limitations": [
            "La clasificación de consultas es heurística y debe revisarse.",
            "No se genera un juicio semántico automático ni se asume que el modelo evaluador sea correcto.",
            "Las columnas PENDIENTE requieren revisión humana."
        ]
    }
    meta_path = d / "g1_rag11a_metadatos.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("G1-RAG-11A: planillas de revisión creadas.")
    print(f"Consultas: {len(case_rows)}")
    print(f"Filas de fragmentos: {len(out)}")
    print(f"Fragmentos: {output}")
    print(f"Resumen por consulta: {case_path}")
    print(f"Metadatos: {meta_path}")

if __name__ == "__main__":
    main()
