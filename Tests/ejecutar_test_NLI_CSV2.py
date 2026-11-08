#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GIAR-ORION - Ejecutor de pruebas NLI desde CSV
Modelo: MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7

Entrada: CSV con columnas claim, evidence y expected.
Procesa Evidence como premise y Claim como hypothesis.
Genera un CSV de resultados con scores y un resumen por factor.
"""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"

REQUIRED_COLUMNS = {"claim", "evidence", "expected"}


def normalize_label(label):
    """Convierte nombres habituales de etiquetas NLI a etiquetas internas."""
    value = str(label).strip().lower().replace("-", "_").replace(" ", "_")

    if "entail" in value or "support" in value:
        return "entailment"
    if "contrad" in value:
        return "contradiction"
    if "neutral" in value:
        return "neutral"
    return None


def get_label_mapping(model):
    """Obtiene el mapeo NLI desde la configuración del checkpoint."""
    mapping = {}
    id2label = getattr(model.config, "id2label", {}) or {}

    for index, label in id2label.items():
        try:
            idx = int(index)
        except (TypeError, ValueError):
            continue
        normalized = normalize_label(label)
        if normalized:
            mapping[idx] = normalized

    expected = {"entailment", "neutral", "contradiction"}
    if len(mapping) == 3 and set(mapping.values()) == expected:
        return mapping

    if model.config.num_labels == 3:
        print(
            "AVISO: la configuración no expone etiquetas reconocibles. "
            "Se utiliza el mapeo del checkpoint mDeBERTa XNLI: "
            "0=contradiction, 1=entailment, 2=neutral.",
            file=sys.stderr,
        )
        return {0: "contradiction", 1: "entailment", 2: "neutral"}

    raise RuntimeError("No se pudo determinar el mapeo de etiquetas NLI.")


def detect_separator(file_path):
    """Detecta separador punto y coma o coma."""
    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        first_line = file.readline()
    return ";" if first_line.count(";") >= first_line.count(",") else ","


def load_input(file_path):
    separator = detect_separator(file_path)
    data = pd.read_csv(file_path, sep=separator, encoding="utf-8-sig")
    data.columns = [str(column).strip().lower() for column in data.columns]

    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(
            "Faltan columnas obligatorias: "
            + ", ".join(sorted(missing))
            + ". Se requieren claim, evidence y expected."
        )

    for column in ("claim", "evidence", "expected"):
        data[column] = data[column].fillna("").astype(str).str.strip()

    empty_rows = data[(data["claim"] == "") | (data["evidence"] == "")]
    if not empty_rows.empty:
        indexes = ", ".join(str(i + 2) for i in empty_rows.index.tolist())
        raise ValueError(f"Hay Claim o Evidence vacíos en las filas: {indexes}")

    return data


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta el test NLI de GIAR-ORION sobre un CSV."
    )
    parser.add_argument("--input", required=True, help="CSV de entrada.")
    parser.add_argument(
        "--output",
        default=None,
        help="CSV de salida. Por defecto agrega _resultados al nombre.",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cuda", "cpu"),
        default="auto",
        help="Dispositivo de inferencia. Por defecto: auto.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Pares por lote. Por defecto: 8.",
    )
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {input_path}")
    if args.batch_size < 1:
        raise ValueError("--batch-size debe ser mayor que cero.")

    data = load_input(input_path)

    if args.device == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("Se solicitó CUDA, pero CUDA no está disponible.")
        device = torch.device("cuda")
    elif args.device == "cpu":
        device = torch.device("cpu")
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("=" * 68)
    print("GIAR-ORION - TEST NLI CSV")
    print("=" * 68)
    print(f"Modelo: {MODEL_NAME}")
    print(f"Dispositivo: {device}")
    print(f"Archivo: {input_path}")
    print(f"Pares: {len(data)}")
    print("Premise = Evidence | Hypothesis = Claim")
    print("-" * 68)

    start_time = time.time()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.to(device)
    model.eval()

    label_mapping = get_label_mapping(model)
    print(f"Mapeo de etiquetas: {label_mapping}")

    all_scores = []

    for start in range(0, len(data), args.batch_size):
        batch = data.iloc[start : start + args.batch_size]
        encoded = tokenizer(
            batch["evidence"].tolist(),
            batch["claim"].tolist(),
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        encoded = {key: value.to(device) for key, value in encoded.items()}

        with torch.inference_mode():
            logits = model(**encoded).logits
            probabilities = torch.softmax(logits, dim=-1).cpu()

        for probability in probabilities:
            all_scores.append({
                label_mapping[index]: float(probability[index])
                for index in range(len(probability))
            })

        print(f"Procesados: {min(start + len(batch), len(data))}/{len(data)}")

    results = data.copy()
    results["predicted_nli"] = [
        max(scores, key=scores.get) for scores in all_scores
    ]
    label_conversion = {
        "entailment": "SUPPORTED",
        "neutral": "INSUFFICIENT",
        "contradiction": "CONTRADICTED",
    }
    results["prediction"] = results["predicted_nli"].map(label_conversion)
    results["entailment"] = [scores["entailment"] for scores in all_scores]
    results["neutral"] = [scores["neutral"] for scores in all_scores]
    results["contradiction"] = [scores["contradiction"] for scores in all_scores]

    results["expected"] = results["expected"].str.upper().str.strip()
    valid_labels = {"SUPPORTED", "INSUFFICIENT", "CONTRADICTED"}
    invalid = sorted(set(results["expected"]) - valid_labels)
    if invalid:
        raise ValueError(
            "Etiquetas esperadas no reconocidas: "
            + ", ".join(invalid)
            + ". Use SUPPORTED, INSUFFICIENT o CONTRADICTED."
        )

    results["correct"] = results["prediction"] == results["expected"]

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else input_path.with_name(input_path.stem + "_resultados.csv")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(
        output_path,
        sep=";",
        index=False,
        encoding="utf-8-sig",
        float_format="%.8f",
    )

    elapsed = time.time() - start_time
    accuracy = results["correct"].mean() * 100.0

    print("\n" + "=" * 68)
    print("RESULTADO GENERAL")
    print("=" * 68)
    print(f"Casos: {len(results)}")
    print(f"Aciertos: {int(results['correct'].sum())}")
    print(f"Errores: {int((~results['correct']).sum())}")
    print(f"Accuracy: {accuracy:.2f}%")
    print(f"Tiempo total: {elapsed:.2f} segundos")

    group_column = next(
        (column for column in ("factor", "group") if column in results.columns),
        None,
    )
    if group_column:
        summary = results.groupby(group_column, dropna=False).agg(
            casos=("correct", "size"),
            aciertos=("correct", "sum"),
            accuracy=("correct", "mean"),
        )
        summary["accuracy"] = (summary["accuracy"] * 100).round(2)
        print(f"\nRESULTADOS POR {group_column.upper()}")
        print(summary.to_string())

    print("\nMATRIZ DE CONFUSIÓN")
    confusion = pd.crosstab(
        results["expected"],
        results["prediction"],
        rownames=["Esperado"],
        colnames=["Predicción"],
        dropna=False,
    )
    print(confusion.to_string())

    print(f"\nArchivo generado: {output_path}")
    print("Este test evalúa únicamente NLI; no ejecuta RAG, ClaimExtractor ni Qwen3.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nERROR: {error}", file=sys.stderr)
        sys.exit(1)
