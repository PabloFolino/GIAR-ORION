"""
GIAR-ORION - Runner de experimentos controlados de paráfrasis P1-P4.
No modifica EvidenceVerifier, umbrales, datasets de calibración ni holdout.
Requiere: pip install transformers torch
Ejecutar desde el entorno GIAR-ORION:
    python run_paraphrase_experiments.py
"""
import json
import csv
import time
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
HERE = Path(__file__).resolve().parent
DATASET_PATH = HERE / "paraphrase_experiments.json"
JSON_OUT = HERE / "paraphrase_experiment_results.json"
CSV_OUT = HERE / "paraphrase_experiment_results.csv"
BATCH_SIZE = 16
MAX_LENGTH = 256

def normalize_label(label):
    label = str(label).lower()
    if "entail" in label:
        return "entailment"
    if "contrad" in label:
        return "contradiction"
    if "neutral" in label:
        return "neutral"
    return label

def main():
    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Modelo: {MODEL_NAME}")
    print(f"Dispositivo: {device}")
    start = time.time()

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.to(device)
    model.eval()

    id2label = {int(k): normalize_label(v) for k, v in model.config.id2label.items()}
    all_cases = []
    for exp in data["experiments"]:
        for case in exp["cases"]:
            item = dict(case)
            item["experiment"] = exp["id"]
            all_cases.append(item)

    results = []
    with torch.inference_mode():
        for offset in range(0, len(all_cases), BATCH_SIZE):
            batch = all_cases[offset:offset+BATCH_SIZE]
            # Premise=evidence, hypothesis=claim: ¿la evidencia respalda el claim?
            encoded = tokenizer(
                [x["evidence"] for x in batch],
                [x["claim"] for x in batch],
                padding=True,
                truncation=True,
                max_length=MAX_LENGTH,
                return_tensors="pt"
            ).to(device)
            logits = model(**encoded).logits
            probs = torch.softmax(logits, dim=-1).detach().cpu().tolist()
            for item, row in zip(batch, probs):
                scores = {id2label[i]: float(row[i]) for i in range(len(row))}
                predicted = max(scores, key=scores.get)
                results.append({
                    **item,
                    "scores": scores,
                    "predicted_nli": predicted,
                    "correct": predicted == item["gold"].lower()
                })
            print(f"Procesados {min(offset+BATCH_SIZE, len(all_cases))}/{len(all_cases)}")

    summary = {}
    for exp in data["experiments"]:
        subset = [r for r in results if r["experiment"] == exp["id"]]
        summary[exp["id"]] = {
            "n": len(subset),
            "accuracy_argmax": sum(r["correct"] for r in subset) / len(subset),
            "supported_n": sum(r["gold"] == "SUPPORTED" for r in subset),
            "supported_mean_entailment": sum(r["scores"].get("entailment", 0) for r in subset if r["gold"] == "SUPPORTED") /
                max(1, sum(r["gold"] == "SUPPORTED" for r in subset)),
            "contradicted_n": sum(r["gold"] == "CONTRADICTED" for r in subset),
            "insufficient_n": sum(r["gold"] == "INSUFFICIENT" for r in subset)
        }

    output = {
        "model": MODEL_NAME,
        "device": str(device),
        "elapsed_seconds": time.time() - start,
        "n_cases": len(results),
        "summary": summary,
        "results": results
    }
    JSON_OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    columns = ["experiment", "id", "gold", "predicted_nli", "correct",
               "entailment", "neutral", "contradiction", "claim", "evidence"]
    with CSV_OUT.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for r in results:
            row = {k:r.get(k, "") for k in columns if k not in ("entailment","neutral","contradiction")}
            for k in ("entailment","neutral","contradiction"):
                row[k] = r["scores"].get(k, "")
            writer.writerow(row)

    print("\nResumen por experimento:")
    for key, value in summary.items():
        print(key, value)
    print(f"\nResultados: {JSON_OUT}")
    print(f"CSV: {CSV_OUT}")
    print(f"Tiempo total: {output['elapsed_seconds']:.2f} s")

if __name__ == "__main__":
    main()
