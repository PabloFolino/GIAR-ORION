"""
GIAR-ORION - EV-009: evaluación NLI con evidencia técnica del código SAC.

Ejecutar desde la raíz:
    python Tests/test_evidence_nli_ev009.py

Usa el modelo NLI ya descargado y la GPU CUDA.
No modifica el agente ni sus módulos.
"""

import json
import sys
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


MODEL_ID = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"

# Premises redactadas en lenguaje natural a partir del código fuente.
# Se conserva la referencia exacta al archivo y a los elementos examinados.
CASES = [
    {
        "id": "EV-009-A",
        "source": "Networks.py — P_Network.forward() y P_Network.sample_normal()",
        "premise": (
            "En Networks.py, P_Network.forward calcula los parámetros mu y sigma "
            "de una distribución Normal. P_Network.sample_normal construye "
            "Normal(mu, sigma), utiliza rsample() cuando reparameterize=True "
            "y aplica la función tanh a la muestra para restringir la acción."
        ),
        "claim": (
            "La política del actor genera acciones mediante una distribución "
            "Normal, utiliza muestreo reparametrizado cuando está habilitado "
            "y aplica tanh a la acción."
        ),
        "expected": "SUPPORTED",
    },
    {
        "id": "EV-009-B",
        "source": "SAC.py — inicialización de P0-STAND; Networks.py — P_Network.forward()",
        "premise": (
            "En SAC.py, para P0-STAND se establece pref_dim=0 y se construye "
            "P_Network con obs_dim, act_dim y pref_dim. En Networks.py, "
            "P_Network.forward recibe state y pref. Cuando pref_dim es cero, "
            "la primera capa recibe solamente state; no concatena action "
            "como entrada del actor."
        ),
        "claim": (
            "En esta implementación P0-STAND, la red Actor recibe el vector "
            "de estado y el vector de acción como entradas de su primera capa."
        ),
        "expected": "CONTRADICTED",
    },
    {
        "id": "EV-009-C",
        "source": "SAC.py — creación de log_alpha y actualización de Alpha_loss",
        "premise": (
            "En SAC.py, log_alpha se crea como un tensor con requires_grad=True. "
            "El optimizador de temperatura Adam recibe [self.log_alpha]. "
            "La pérdida Alpha_loss se calcula multiplicando self.log_alpha "
            "por el error de entropía desacoplado. La expresión exp(log_alpha) "
            "se utiliza para obtener alpha en otros cálculos, como la pérdida "
            "de la política."
        ),
        "claim": (
            "En esta implementación, el optimizador de temperatura actualiza "
            "directamente alpha igual a exp(log_alpha), en lugar de actualizar "
            "log_alpha."
        ),
        "expected": "CONTRADICTED",
    },
]

LABEL_MAP = {
    "entailment": "SUPPORTED",
    "neutral": "INSUFFICIENT",
    "contradiction": "CONTRADICTED",
}


def normalize_label(label):
    value = str(label).strip().lower()
    if "entail" in value:
        return "entailment"
    if "neutral" in value:
        return "neutral"
    if "contrad" in value:
        return "contradiction"
    return value


def main():
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA no está disponible; la prueba requiere la GPU.")

    device = torch.device("cuda:0")
    print("EV-009 — NLI sobre código SAC")
    print("GPU:", torch.cuda.get_device_name(0))
    print("Modelo:", MODEL_ID)
    print()

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
    model.to(device)
    model.eval()

    id2label = {
        int(index): normalize_label(label)
        for index, label in model.config.id2label.items()
    }

    results = []
    correct = 0

    for case in CASES:
        encoded = tokenizer(
            case["premise"],
            case["claim"],
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        encoded = {key: value.to(device) for key, value in encoded.items()}

        with torch.inference_mode():
            logits = model(**encoded).logits[0]
            probs = torch.softmax(logits, dim=-1).cpu().tolist()

        scores = {
            id2label[index]: float(score)
            for index, score in enumerate(probs)
        }
        nli_label = max(scores, key=scores.get)
        prediction = LABEL_MAP[nli_label]
        passed = prediction == case["expected"]
        correct += int(passed)

        result = {
            **case,
            "predicted": prediction,
            "scores": scores,
            "match": passed,
        }
        results.append(result)

        print("=" * 72)
        print(case["id"])
        print("Fuente:", case["source"])
        print("Afirmación:", case["claim"])
        print("Esperado:", case["expected"])
        print("Obtenido:", prediction, "|", "PASS" if passed else "FAIL")
        print(
            "Scores: "
            f"entailment={scores.get('entailment', 0):.4f} | "
            f"neutral={scores.get('neutral', 0):.4f} | "
            f"contradiction={scores.get('contradiction', 0):.4f}"
        )

    total = len(CASES)
    print("\n" + "=" * 72)
    print(f"EV-009: {correct}/{total} coincidencias")
    print("=" * 72)

    report = {
        "suite": "EV-009",
        "model": MODEL_ID,
        "device": str(device),
        "gpu": torch.cuda.get_device_name(0),
        "correct": correct,
        "total": total,
        "results": results,
        "limitations": [
            "Las premisas son resúmenes en lenguaje natural derivados de los archivos fuente indicados.",
            "La prueba evalúa NLI sobre tres fragmentos técnicos; no valida todo el repositorio.",
            "Los scores NLI no son probabilidades calibradas de verdad.",
            "Una clasificación neutral significa evidencia insuficiente en este par, no que la afirmación sea falsa.",
        ],
    }

    output = Path(__file__).resolve().with_name("evidence_nli_ev009_results.json")
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("Informe:", output)
    return 0 if correct == total else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
        raise
