"""
GIAR-ORION - EV-008 NLI benchmark
Compara afirmaciones (hypothesis) con evidencias (premise) usando un modelo NLI.

Uso desde la raíz del proyecto:
    python Tests/test_evidence_nli.py

Este script NO modifica EvidenceVerifier.py ni ningún archivo del agente.
Los casos del JSON son fixtures sintéticos: no validan hechos científicos reales.
"""

import json
import sys
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


MODEL_ID = (
    "MoritzLaurer/"
    "mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
)
DATASET_PATH = Path(__file__).resolve().with_name("evidence_semantic_cases.json")


def normalize_label(label):
    """Normaliza las etiquetas del modelo a entailment/neutral/contradiction."""
    value = str(label).strip().lower()
    if "entail" in value:
        return "entailment"
    if "neutral" in value:
        return "neutral"
    if "contrad" in value:
        return "contradiction"
    return value


def load_dataset():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el dataset: {DATASET_PATH}"
        )

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    cases = dataset.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("El dataset no contiene una lista válida de casos.")

    return dataset, cases


def load_nli_model(device):
    print(f"Modelo: {MODEL_ID}")
    print(f"Dispositivo: {device}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
    model.to(device)
    model.eval()

    id2label = {
        int(index): normalize_label(label)
        for index, label in model.config.id2label.items()
    }

    required = {"entailment", "neutral", "contradiction"}
    available = set(id2label.values())
    if not required.issubset(available):
        raise RuntimeError(
            "Las etiquetas del modelo no son las esperadas. "
            f"Encontradas: {model.config.id2label}"
        )

    return tokenizer, model, id2label


def classify_pair(premise, hypothesis, tokenizer, model, id2label, device):
    """
    premise = evidencia
    hypothesis = afirmación a verificar
    """
    inputs = tokenizer(
        premise,
        hypothesis,
        return_tensors="pt",
        truncation=True,
        max_length=512,
    )
    inputs = {key: value.to(device) for key, value in inputs.items()}

    with torch.inference_mode():
        logits = model(**inputs).logits[0]
        probabilities = torch.softmax(logits, dim=-1).cpu().tolist()

    scores = {
        id2label[index]: float(probability)
        for index, probability in enumerate(probabilities)
    }
    predicted_label = max(scores, key=scores.get)

    mapping = {
        "entailment": "SUPPORTED",
        "neutral": "INSUFFICIENT",
        "contradiction": "CONTRADICTED",
    }

    return mapping[predicted_label], scores


def evaluate_case(case, tokenizer, model, id2label, device):
    claim = case["claim"]
    evidence_list = case["evidence"]

    evidence_results = []
    for evidence in evidence_list:
        prediction, scores = classify_pair(
            premise=evidence,
            hypothesis=claim,
            tokenizer=tokenizer,
            model=model,
            id2label=id2label,
            device=device,
        )
        evidence_results.append(
            {
                "evidence": evidence,
                "prediction": prediction,
                "scores": scores,
            }
        )

    # Agregación conservadora para este benchmark:
    # una evidencia que contradice explícitamente prevalece;
    # si no hay contradicción, una evidencia que implica la afirmación
    # permite clasificarla como respaldada; en los demás casos es insuficiente.
    predictions = [item["prediction"] for item in evidence_results]

    if "CONTRADICTED" in predictions:
        final_prediction = "CONTRADICTED"
    elif "SUPPORTED" in predictions:
        final_prediction = "SUPPORTED"
    else:
        final_prediction = "INSUFFICIENT"

    return final_prediction, evidence_results


def main():
    dataset, cases = load_dataset()

    if not torch.cuda.is_available():
        print("ERROR: CUDA no está disponible. No se ejecutará en CPU.")
        return 2

    device = torch.device("cuda:0")
    print("CUDA disponible:", torch.cuda.is_available())
    print("GPU:", torch.cuda.get_device_name(0))
    print("Casos:", len(cases))
    print()

    tokenizer, model, id2label = load_nli_model(device)

    print("Etiquetas del modelo:", id2label)
    print("\n" + "=" * 78)
    print("RESULTADOS EV-008")
    print("=" * 78)

    results = []
    correct = 0

    for case in cases:
        prediction, evidence_results = evaluate_case(
            case, tokenizer, model, id2label, device
        )
        expected = case["expected"]
        matched = prediction == expected

        if matched:
            correct += 1

        results.append(
            {
                "id": case["id"],
                "claim": case["claim"],
                "expected": expected,
                "predicted": prediction,
                "match": matched,
                "evidence_results": evidence_results,
            }
        )

        print(f"\n{case['id']}")
        print("Afirmación:", case["claim"])
        print("Esperado:", expected)
        print("Predicción:", prediction)
        print("Coincidencia:", "PASS" if matched else "FAIL")

        for index, item in enumerate(evidence_results, start=1):
            scores = item["scores"]
            print(f"  Evidencia {index}: {item['evidence']}")
            print(
                "  NLI: "
                f"entailment={scores.get('entailment', 0.0):.4f} | "
                f"neutral={scores.get('neutral', 0.0):.4f} | "
                f"contradiction={scores.get('contradiction', 0.0):.4f}"
            )

    total = len(cases)
    print("\n" + "=" * 78)
    print(f"RESULTADO GLOBAL: {correct}/{total} coincidencias")
    print("=" * 78)

    report = {
        "suite": dataset.get("suite"),
        "dataset_version": dataset.get("version"),
        "model": MODEL_ID,
        "device": str(device),
        "gpu": torch.cuda.get_device_name(0),
        "correct": correct,
        "total": total,
        "accuracy_on_synthetic_fixtures": correct / total if total else 0.0,
        "results": results,
        "limitations": [
            "Los casos son fixtures sintéticos, no documentación científica real.",
            "Las puntuaciones NLI no son probabilidades calibradas de verdad.",
            "PARTIALLY_SUPPORTED no se infiere con esta prueba de afirmaciones completas.",
            "La agregación es deliberadamente simple y no resuelve conflictos entre múltiples fuentes.",
            "El resultado no constituye todavía una validación del EvidenceVerifier integrado.",
        ],
    }

    report_path = Path(__file__).resolve().with_name("evidence_nli_results.json")
    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    print(f"\nInforme guardado en: {report_path}")
    print("Nota: el porcentaje solo mide coincidencia con estos fixtures sintéticos.")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"\nERROR durante la evaluación: {type(exc).__name__}: {exc}")
        raise
