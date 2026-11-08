#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Evalúa las 16 paráfrasis controladas de P2 con el modelo NLI de GIAR-ORION.
No modifica EvidenceVerifier, RAG, umbrales ni arquitectura.

Uso:
    python test_P2_parafrasis.py
    python test_P2_parafrasis.py ruta/al/archivo.json
"""

import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"

# Orden de etiquetas del checkpoint XNLI si la configuración devuelve LABEL_0...
FALLBACK_ID2LABEL = {
    0: "contradiction",
    1: "neutral",
    2: "entailment",
}

NLI_TO_GOLD = {
    "entailment": "SUPPORTED",
    "contradiction": "CONTRADICTED",
    "neutral": "INSUFFICIENT",
}


def normalize_label(label):
    """Normaliza etiquetas de Hugging Face a las tres clases NLI."""
    value = str(label).strip().lower()
    value = value.replace(" ", "_")
    if "entail" in value:
        return "entailment"
    if "contrad" in value:
        return "contradiction"
    if "neutral" in value:
        return "neutral"
    return None


def get_id2label(model):
    """Obtiene las etiquetas del modelo y valida que sean las tres clases."""
    raw = getattr(model.config, "id2label", {}) or {}
    mapped = {}

    for key, value in raw.items():
        try:
            index = int(key)
        except (TypeError, ValueError):
            continue
        normalized = normalize_label(value)
        if normalized:
            mapped[index] = normalized

    if set(mapped.values()) != set(NLI_TO_GOLD):
        mapped = FALLBACK_ID2LABEL.copy()

    if set(mapped.values()) != set(NLI_TO_GOLD):
        raise RuntimeError(
            f"No se pudieron identificar las etiquetas NLI. id2label={raw}"
        )

    return mapped


def main():
    parser = argparse.ArgumentParser(
        description="Evalúa las paráfrasis controladas de P2."
    )
    parser.add_argument(
        "input_json",
        nargs="?",
        default=str(Path(__file__).with_name("P2_parafrasis_controladas.json")),
        help="JSON de entrada. Por defecto, junto a este script.",
    )
    args = parser.parse_args()

    input_path = Path(args.input_json).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(
            f"No se encontró el archivo de entrada:\n{input_path}\n"
            "Ubicá P2_parafrasis_controladas.json junto al script "
            "o indicá su ruta como argumento."
        )

    with input_path.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    pairs = dataset.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        raise ValueError(
            "El JSON no contiene una lista 'pairs' válida y no vacía."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Modelo: {MODEL_NAME}")
    print(f"Dispositivo: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    print("\nCargando tokenizer y modelo...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.to(device)
    model.eval()

    id2label = get_id2label(model)
    print(f"Etiquetas detectadas: {id2label}")
    print(f"Pares a evaluar: {len(pairs)}\n")

    results = []
    start = time.perf_counter()

    for number, pair in enumerate(pairs, start=1):
        required = ("id", "source_id", "variant", "gold", "claim", "evidence")
        missing = [key for key in required if key not in pair]
        if missing:
            raise ValueError(
                f"El par {number} no contiene los campos requeridos: {missing}"
            )

        # NLI: premise = evidence; hypothesis = claim.
        inputs = tokenizer(
            pair["evidence"],
            pair["claim"],
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        inputs = {key: value.to(device) for key, value in inputs.items()}

        with torch.inference_mode():
            logits = model(**inputs).logits[0]
            probabilities = torch.softmax(logits, dim=-1).detach().cpu()

        scores = {
            id2label[index]: float(probabilities[index])
            for index in range(len(probabilities))
        }
        predicted_nli = max(scores, key=scores.get)
        predicted_gold = NLI_TO_GOLD[predicted_nli]
        gold = str(pair["gold"]).upper()

        result = {
            "id": pair["id"],
            "source_id": pair["source_id"],
            "variant": pair["variant"],
            "gold": gold,
            "predicted_nli": predicted_nli,
            "predicted": predicted_gold,
            "correct": predicted_gold == gold,
            "scores": scores,
            "claim": pair["claim"],
            "evidence": pair["evidence"],
        }
        results.append(result)

        status = "OK" if result["correct"] else "ERROR"
        print(
            f"[{number:02d}/{len(pairs)}] {pair['id']} | "
            f"{pair['variant']} | gold={gold} | "
            f"pred={predicted_gold} | {status}"
        )

    elapsed = time.perf_counter() - start

    # Métricas globales y por caso de origen.
    total = len(results)
    correct = sum(item["correct"] for item in results)
    accuracy = correct / total if total else 0.0

    per_case = defaultdict(list)
    for item in results:
        per_case[item["source_id"]].append(item)

    summary_by_case = {}
    for source_id, items in sorted(per_case.items()):
        case_correct = sum(item["correct"] for item in items)
        summary_by_case[source_id] = {
            "n": len(items),
            "correct": case_correct,
            "accuracy": case_correct / len(items),
            "predictions": dict(Counter(item["predicted"] for item in items)),
        }

    summary = {
        "n_cases": total,
        "correct": correct,
        "incorrect": total - correct,
        "accuracy": accuracy,
        "predictions": dict(Counter(item["predicted"] for item in results)),
        "by_source_id": summary_by_case,
    }

    output = {
        "model": MODEL_NAME,
        "device": str(device),
        "elapsed_seconds": elapsed,
        "input_file": str(input_path),
        "label_mapping": NLI_TO_GOLD,
        "summary": summary,
        "results": results,
    }

    output_json = input_path.with_name("P2_resultados_nli.json")
    output_csv = input_path.with_name("P2_resultados_nli.csv")

    with output_json.open("w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    csv_fields = [
        "id", "source_id", "variant", "gold", "predicted",
        "predicted_nli", "correct", "entailment", "neutral",
        "contradiction", "claim", "evidence",
    ]
    with output_csv.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=csv_fields)
        writer.writeheader()
        for item in results:
            row = {key: item.get(key, "") for key in csv_fields}
            row.update(item["scores"])
            writer.writerow(row)

    print("\n========== RESUMEN ==========")
    print(f"Total: {total}")
    print(f"Correctos: {correct}")
    print(f"Incorrectos: {total - correct}")
    print(f"Accuracy: {accuracy:.2%}")
    print("\nResultados por caso:")
    for source_id, metrics in summary_by_case.items():
        print(
            f"  {source_id}: {metrics['correct']}/{metrics['n']} "
            f"({metrics['accuracy']:.1%})"
        )

    print("\nArchivos generados:")
    print(f"  JSON: {output_json}")
    print(f"  CSV:  {output_csv}")
    print(f"Tiempo de inferencia: {elapsed:.2f} s")


if __name__ == "__main__":
    main()
