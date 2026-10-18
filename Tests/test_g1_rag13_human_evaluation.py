#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G1-RAG-13 — Evaluación humana de fragmentos recuperados en G1-RAG-12.

Lee los CSV existentes de G1-RAG-12, genera una planilla de evaluación humana
con una fila por consulta/documento/ranking y luego calcula un resumen a partir
de las calificaciones ingresadas por el evaluador.

No carga E5, no vuelve a ejecutar la recuperación y no modifica archivos del
proyecto. Los archivos de salida se escriben en un directorio nuevo.

Uso desde la raíz de GIAR-ORION:
  python Tests/test_g1_rag13_human_evaluation.py
  python Tests/test_g1_rag13_human_evaluation.py --results-dir Tests/results_g1_rag12
  python Tests/test_g1_rag13_human_evaluation.py --input-dir "Tests/results_g1_rag12/20261013_095027"

Después de completar la columna `evaluacion_humana` en la planilla CSV:
  python Tests/test_g1_rag13_human_evaluation.py --review-csv Tests/results_g1_rag13/evaluacion_humana.csv

Calificaciones admitidas en `evaluacion_humana`: R, P, I
  R = relevante; P = parcialmente relevante; I = irrelevante.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_RESULTS_DIR = Path("Tests/results_g1_rag12")
DEFAULT_OUTPUT_DIR = Path("Tests/results_g1_rag13")
VALID_RATINGS = {"R", "P", "I"}


def newest_run_dir(results_dir: Path) -> Path:
    if not results_dir.exists():
        raise FileNotFoundError(
            f"No existe el directorio de resultados: {results_dir}\n"
            "Indicá la ruta con --input-dir o --results-dir."
        )
    # Accept either a timestamped run folder or a parent folder with run folders.
    if (results_dir / "detalle.csv").exists() and (results_dir / "resumen.csv").exists():
        return results_dir
    candidates = [
        p for p in results_dir.iterdir()
        if p.is_dir() and (p / "detalle.csv").exists() and (p / "resumen.csv").exists()
    ]
    if not candidates:
        raise FileNotFoundError(
            f"No encontré detalle.csv y resumen.csv en {results_dir} ni en sus subdirectorios."
        )
    return max(candidates, key=lambda p: p.stat().st_mtime)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def pick(row: dict[str, str], *keys: str, default: str = "") -> str:
    for key in keys:
        if key in row and row[key] is not None and str(row[key]).strip():
            return str(row[key]).strip()
    return default


def normalize_query_id(row: dict[str, str]) -> str:
    return pick(row, "query_id", "case_id", "id", "consulta_id", default="SIN_ID")


def build_review_rows(
    detail_rows: list[dict[str, str]],
    summary_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    # The G1-RAG-12 detail CSV stores expected_term coverage in the summary CSV.
    summary_by_key = {
        (
            pick(r, "candidate", "document", "version", "corpus", "markdown"),
            normalize_query_id(r),
        ): r
        for r in summary_rows
    }
    result: list[dict[str, str]] = []
    for row in detail_rows:
        qid = normalize_query_id(row)
        candidate = pick(row, "candidate", "document", "version", "corpus", "markdown", default="")
        summary = summary_by_key.get((candidate, qid), {})
        rank = pick(row, "rank", "position", "top_k_rank", default="")
        result.append({
            "query_id": qid,
            "consulta": pick(row, "query", "consulta", "question", "pregunta"),
            "documento": candidate,
            "ranking": rank,
            "puntaje_similitud": pick(row, "score", "similarity", "similarity_score"),
            "objetivo_consulta": pick(summary, "goal", "objetivo"),
            "terminos_esperados": pick(summary, "missing_terms", "expected_terms", "expected", "terminos_esperados"),
            "terminos_encontrados": pick(summary, "found_terms", "expected_terms_found", "matched_terms", "terminos_encontrados"),
            "fuente": pick(row, "source", "source_file", "file", "archivo"),
            "fragmento": pick(row, "text", "chunk_text", "chunk", "fragment", "fragmento"),
            "evaluacion_humana": pick(row, "human_relevance", default=""),
            "motivo_evaluacion": "",
            "respuesta_puede_apoyarse": pick(summary, "answer_supported", default=""),
            "observaciones": "",
        })
    return result


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def summarize(review_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in review_rows:
        key = (row.get("query_id", ""), row.get("documento", ""))
        grouped.setdefault(key, []).append(row)

    output = []
    for (qid, doc), rows in sorted(grouped.items()):
        ratings = [r.get("evaluacion_humana", "").strip().upper() for r in rows]
        ratings = [r for r in ratings if r in VALID_RATINGS]
        output.append({
            "query_id": qid,
            "documento": doc,
            "fragmentos_evaluados": len(ratings),
            "relevantes_R": ratings.count("R"),
            "parciales_P": ratings.count("P"),
            "irrelevantes_I": ratings.count("I"),
            "relevancia_at_5": any(r == "R" for r in ratings),
            "evaluacion_completa": len(ratings) == len(rows) and len(rows) > 0,
            "observaciones": "",
        })
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="G1-RAG-13: evaluación humana de fragmentos.")
    parser.add_argument("--input-dir", type=Path, help="Carpeta de una ejecución específica de G1-RAG-12.")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR,
                        help=f"Carpeta padre de resultados (default: {DEFAULT_RESULTS_DIR}).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                        help=f"Carpeta de salida (default: {DEFAULT_OUTPUT_DIR}).")
    parser.add_argument("--review-csv", type=Path,
                        help="CSV ya calificado; calcula el resumen de evaluación.")
    args = parser.parse_args()

    if args.review_csv:
        review_path = args.review_csv
        if not review_path.exists():
            print(f"ERROR: no existe el archivo calificado: {review_path}", file=sys.stderr)
            return 2
        rows = read_csv(review_path)
        invalid = sorted({
            r.get("evaluacion_humana", "").strip().upper()
            for r in rows
            if r.get("evaluacion_humana", "").strip().upper() not in VALID_RATINGS
        })
        if invalid:
            print(
                "AVISO: hay filas sin calificación válida en evaluacion_humana. "
                "Usá R, P o I. Valores detectados: " + ", ".join(invalid),
                file=sys.stderr,
            )
        summary = summarize(rows)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_path = args.output_dir / f"resumen_evaluacion_{stamp}.csv"
        write_csv(summary_path, summary)
        print(f"Resumen generado: {summary_path}")
        print(f"Filas procesadas: {len(rows)}")
        print("Las filas sin R/P/I no cuentan como fragmentos evaluados.")
        return 0

    try:
        input_dir = args.input_dir if args.input_dir else newest_run_dir(args.results_dir)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print(
            "\nTambién podés indicar directamente los CSV que tengas disponibles, "
            "pero este script espera que estén juntos en una carpeta con nombre "
            "detalle.csv y resumen.csv.",
            file=sys.stderr,
        )
        return 2

    detail_path = input_dir / "detalle.csv"
    summary_path = input_dir / "resumen.csv"
    metadata_path = input_dir / "metadatos.json"
    if not detail_path.exists() or not summary_path.exists():
        print(f"ERROR: faltan detalle.csv o resumen.csv en {input_dir}", file=sys.stderr)
        return 2

    detail_rows = read_csv(detail_path)
    source_summary = read_csv(summary_path)
    review_rows = build_review_rows(detail_rows, source_summary)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_output = args.output_dir / stamp
    run_output.mkdir(parents=True, exist_ok=True)

    review_path = run_output / "evaluacion_humana.csv"
    template_path = run_output / "plantilla_evaluacion_humana.csv"
    initial_summary_path = run_output / "resumen_consultas_original.csv"
    metadata_out = run_output / "metadatos_g1_rag13.json"

    write_csv(review_path, review_rows)
    write_csv(template_path, review_rows)
    write_csv(initial_summary_path, source_summary)

    metadata: dict[str, Any] = {
        "experiment": "G1-RAG-13",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_experiment_directory": str(input_dir.resolve()),
        "source_detail_rows": len(detail_rows),
        "source_summary_rows": len(source_summary),
        "review_scale": {"R": "Relevante", "P": "Parcialmente relevante", "I": "Irrelevante"},
        "instructions": [
            "Abrir evaluacion_humana.csv en Excel o LibreOffice.",
            "Calificar cada fragmento recuperado con R, P o I en evaluacion_humana.",
            "En motivo_evaluacion, anotar brevemente qué evidencia aporta o qué falta.",
            "En respuesta_puede_apoyarse, usar SI, PARCIAL o NO.",
            "Guardar el CSV y ejecutar el script con --review-csv seguido de su ruta.",
            "No cambiar consulta, documento, ranking, puntaje ni fragmento.",
        ],
    }
    if metadata_path.exists():
        try:
            metadata["source_metadata"] = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception as e:
            metadata["source_metadata_read_error"] = str(e)
    metadata_out.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print("G1-RAG-13 — plantilla de evaluación humana creada")
    print(f"Entrada: {input_dir.resolve()}")
    print(f"Fragmentos a evaluar: {len(review_rows)}")
    print(f"Consultas resumidas en el CSV original: {len(source_summary)}")
    print(f"Archivo para calificar: {review_path.resolve()}")
    print(f"Copia de plantilla: {template_path.resolve()}")
    print(f"Metadatos: {metadata_out.resolve()}")
    print("\nCalificá evaluacion_humana con R, P o I y guardá el CSV.")
    print("Luego ejecutá:")
    print(f'  python Tests/test_g1_rag13_human_evaluation.py --review-csv "{review_path}"')
    print("\nNota: no se carga E5 ni se ejecuta recuperación semántica.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
