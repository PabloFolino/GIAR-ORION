#!/usr/bin/env python3
"""
Evalúa resultados de experimentos NLI de GIAR-ORION.

Acepta:
  - JSON de resultados con "results" (experimentos) o "pairs" (dataset NLI).
  - CSV con columnas: experiment, id, gold, predicted_nli
    y opcionalmente entailment, neutral, contradiction.

La comparación se realiza después de normalizar las etiquetas:
  entailment    -> SUPPORTED
  contradiction -> CONTRADICTED
  neutral       -> INSUFFICIENT

No ejecuta el modelo NLI ni modifica EvidenceVerifier.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

NLI_TO_GOLD = {
    "entailment": "SUPPORTED",
    "contradiction": "CONTRADICTED",
    "neutral": "INSUFFICIENT",
}
CLASSES = ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT")


def normalize_gold(value: str) -> str:
    value = str(value).strip().upper()
    aliases = {
        "SUPPORTED": "SUPPORTED",
        "CONTRADICTED": "CONTRADICTED",
        "INSUFFICIENT": "INSUFFICIENT",
        "ENTAILMENT": "SUPPORTED",
        "CONTRADICTION": "CONTRADICTED",
        "NEUTRAL": "INSUFFICIENT",
    }
    if value not in aliases:
        raise ValueError(f"Etiqueta gold desconocida: {value!r}")
    return aliases[value]


def normalize_prediction(value: str) -> str:
    value = str(value).strip().lower()
    if value in NLI_TO_GOLD:
        return NLI_TO_GOLD[value]
    # También acepta predicciones que ya estén expresadas en etiquetas gold.
    return normalize_gold(value)


def prediction_from_scores(row: dict) -> str:
    scores = {}
    for label in ("entailment", "neutral", "contradiction"):
        raw = row.get(label)
        if raw in (None, ""):
            raise ValueError(f"Falta score {label!r} para {row.get('id', '?')}")
        scores[label] = float(raw)
    best = max(scores, key=scores.get)
    return NLI_TO_GOLD[best]


def load_rows(path: Path) -> list[dict]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            raw_rows = list(csv.DictReader(f))
        rows = []
        for r in raw_rows:
            pred = r.get("predicted_nli") or prediction_from_scores(r)
            rows.append({
                "id": r.get("id", ""),
                "group": r.get("experiment") or r.get("group") or "SIN_GRUPO",
                "gold": normalize_gold(r["gold"]),
                "pred": normalize_prediction(pred),
            })
        return rows

    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        raw_rows = data
    elif isinstance(data, dict):
        raw_rows = data.get("results")
        if raw_rows is None:
            raw_rows = data.get("pairs")
    else:
        raw_rows = None

    if not isinstance(raw_rows, list):
        raise ValueError(
            "El JSON debe contener una lista en 'results' o 'pairs'."
        )

    rows = []
    for r in raw_rows:
        scores = r.get("scores", {})
        score_row = {
            "id": r.get("id", ""),
            "entailment": scores.get("entailment"),
            "neutral": scores.get("neutral"),
            "contradiction": scores.get("contradiction"),
        }
        pred_raw = r.get("predicted_nli") or r.get("prediction")
        pred = normalize_prediction(pred_raw) if pred_raw else prediction_from_scores(score_row)
        rows.append({
            "id": r.get("id", ""),
            "group": r.get("experiment") or r.get("group") or "SIN_GRUPO",
            "gold": normalize_gold(r["gold"]),
            "pred": pred,
        })
    return rows


def metrics(rows: list[dict]) -> dict:
    matrix = {g: {p: 0 for p in CLASSES} for g in CLASSES}
    for r in rows:
        matrix[r["gold"]][r["pred"]] += 1

    n = len(rows)
    correct = sum(matrix[c][c] for c in CLASSES)
    per_class = {}
    f1_values = []
    recalls = []
    for c in CLASSES:
        tp = matrix[c][c]
        fp = sum(matrix[g][c] for g in CLASSES if g != c)
        fn = sum(matrix[c][p] for p in CLASSES if p != c)
        support = sum(matrix[c].values())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[c] = {
            "support": support,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
        if support:
            f1_values.append(f1)
            recalls.append(recall)

    return {
        "n": n,
        "correct": correct,
        "accuracy": correct / n if n else 0.0,
        "macro_f1": sum(f1_values) / len(f1_values) if f1_values else 0.0,
        "balanced_accuracy": sum(recalls) / len(recalls) if recalls else 0.0,
        "confusion_matrix": matrix,
        "per_class": per_class,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Archivo .json o .csv de resultados")
    parser.add_argument("-o", "--output", help="Guardar informe JSON")
    args = parser.parse_args()

    rows = load_rows(Path(args.input))
    if not rows:
        raise SystemExit("No se encontraron casos para evaluar.")

    groups = defaultdict(list)
    for row in rows:
        groups[row["group"]].append(row)

    report = {
        "input": str(Path(args.input)),
        "label_mapping": NLI_TO_GOLD,
        "overall": metrics(rows),
        "groups": {name: metrics(group_rows) for name, group_rows in sorted(groups.items())},
        "note": (
            "Las métricas se calcularon comparando etiquetas normalizadas. "
            "No se utilizó la columna 'correct' del archivo de entrada."
        ),
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.output:
        Path(args.output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nInforme guardado en: {args.output}")


if __name__ == "__main__":
    main()
