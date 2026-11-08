# -*- coding: utf-8 -*-
"""
Campaña comparativa EvidenceVerifier 0.2.1 vs 0.2.2 experimental.
Ejecutar desde la raíz de GIAR-ORION:
python Tests/EvidenceVerifier_Validation/run_comparacion_0_2_1_vs_0_2_2.py
"""
from __future__ import annotations

import argparse
import csv
import gc
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEFAULT_DATASET = HERE / "dataset_120_casos.json"
DEFAULT_BASELINE = HERE / "EvidenceVerifier_0_2_1_reference.py"
DEFAULT_EXPERIMENTAL = HERE / "EvidenceVerifier_0_2_2_experimental.py"
OUTPUT_DIR = HERE / "comparacion_0_2_1_vs_0_2_2"


def load_class(module_path: Path, module_name: str):
    if not module_path.is_file():
        raise FileNotFoundError(f"No se encuentra el módulo: {module_path}")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    if not hasattr(module, "EvidenceVerifier"):
        raise RuntimeError(f"{module_path.name} no contiene EvidenceVerifier")
    return module.EvidenceVerifier


def normalize_evidence(text: str) -> list[str]:
    # El delimitador || separa evidencias independientes en los casos F_MULTI_EVIDENCE.
    return [part.strip() for part in text.split("||") if part.strip()]


def make_rag_items(case: dict) -> list[dict]:
    return [
        {
            "source": f"dataset:{case['id']}:evidence:{i+1}",
            "text": fragment,
            "score": 1.0,
            "mode": "validation_dataset",
        }
        for i, fragment in enumerate(normalize_evidence(case["evidence"]))
    ]


def run_version(label: str, module_path: Path, cases: list[dict], output_dir: Path,
                experimental: bool, ollama_url: str, ollama_model: str,
                timeout: int, progress_every: int) -> tuple[list[dict], dict]:
    Verifier = load_class(module_path, f"ev_module_{label}")
    kwargs = {}
    if experimental:
        kwargs.update({
            "normalize_cross_language": True,
            "ollama_url": ollama_url,
            "normalization_model": ollama_model,
            "normalization_timeout": timeout,
        })
    verifier = Verifier(**kwargs)

    records = []
    start_all = time.perf_counter()
    for index, case in enumerate(cases, start=1):
        started = time.perf_counter()
        result = verifier.verify_claims(
            claims=[case["claim"]],
            rag_results=make_rag_items(case),
            web_results=None,
            max_evidence_per_claim=10,
        )
        elapsed = time.perf_counter() - started
        claim_report = result["claims"][0]
        record = {
            "id": case["id"],
            "group": case["group"],
            "claim": case["claim"],
            "evidence": case["evidence"],
            "gold": case.get("gold_verifier", case.get("gold_nli")),
            "predicted": claim_report["status"],
            "correct": claim_report["status"] == case.get("gold_verifier", case.get("gold_nli")),
            "elapsed_seconds": round(elapsed, 4),
            "best_entailment_score": claim_report.get("best_entailment_score"),
            "best_contradiction_score": claim_report.get("best_contradiction_score"),
            "comparisons": claim_report.get("comparisons", []),
            "normalization": result.get("normalization"),
            "device": result.get("device"),
            "model": result.get("model"),
        }
        records.append(record)
        if index == 1 or index % progress_every == 0 or index == len(cases):
            print(f"[{label}] {index}/{len(cases)} casos | último={elapsed:.2f}s | acumulado={time.perf_counter()-start_all:.1f}s",
                  flush=True)

    total = time.perf_counter() - start_all
    summary = summarize(records)
    summary["version_label"] = label
    summary["module_path"] = str(module_path)
    summary["total_seconds"] = round(total, 3)
    summary["mean_case_seconds"] = round(total / len(cases), 3) if cases else None

    # Liberar el modelo antes de cargar la siguiente versión.
    del verifier
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass

    return records, summary


def summarize(records: list[dict]) -> dict:
    total = len(records)
    correct = sum(bool(r["correct"]) for r in records)
    labels = ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT"]
    confusion = {g: {p: 0 for p in labels + ["CONFLICTING_EVIDENCE"]} for g in labels}
    for r in records:
        gold, pred = r["gold"], r["predicted"]
        confusion.setdefault(gold, {p: 0 for p in labels + ["CONFLICTING_EVIDENCE"]})
        confusion[gold][pred] = confusion[gold].get(pred, 0) + 1

    group_counts = defaultdict(lambda: {"cases": 0, "correct": 0, "accuracy_pct": 0.0})
    for r in records:
        g = group_counts[r["group"]]
        g["cases"] += 1
        g["correct"] += int(bool(r["correct"]))
    for g in group_counts.values():
        g["accuracy_pct"] = round(100 * g["correct"] / g["cases"], 2) if g["cases"] else 0

    return {
        "cases": total,
        "correct": correct,
        "accuracy_pct": round(100 * correct / total, 2) if total else 0,
        "prediction_counts": dict(Counter(r["predicted"] for r in records)),
        "gold_counts": dict(Counter(r["gold"] for r in records)),
        "confusion_matrix_rows_gold_columns_prediction": confusion,
        "by_group": dict(group_counts),
        "mean_case_seconds": round(sum(r["elapsed_seconds"] for r in records) / total, 3) if total else None,
    }


def write_csv(path: Path, rows: list[dict]):
    fields = [
        "id", "group", "claim", "evidence", "gold",
        "predicted_0_2_1", "predicted_0_2_2",
        "correct_0_2_1", "correct_0_2_2", "change",
        "seconds_0_2_1", "seconds_0_2_2",
        "entailment_0_2_1", "contradiction_0_2_1",
        "entailment_0_2_2", "contradiction_0_2_2",
        "normalization_requested", "normalization_succeeded", "normalization_fallback",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Comparación integral 0.2.1 vs 0.2.2 experimental")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--experimental", type=Path, default=DEFAULT_EXPERIMENTAL)
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--ollama-model", default="qwen3:8b")
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--progress-every", type=int, default=5)
    args = parser.parse_args()

    for p in (args.dataset, args.baseline, args.experimental):
        if not p.is_file():
            raise FileNotFoundError(f"Falta archivo requerido: {p}")

    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    cases = dataset.get("cases")
    if not isinstance(cases, list) or len(cases) != 120:
        raise ValueError(f"Se esperaban 120 casos y se encontraron {len(cases) if isinstance(cases, list) else 'datos inválidos'}")
    ids = [c.get("id") for c in cases]
    if len(set(ids)) != 120:
        raise ValueError("El dataset contiene IDs duplicados.")
    for c in cases:
        for key in ("id", "group", "claim", "evidence"):
            if not isinstance(c.get(key), str) or not c[key].strip():
                raise ValueError(f"Caso inválido {c.get('id')}: campo {key!r} ausente.")
        if c.get("gold_verifier", c.get("gold_nli")) not in {
            "SUPPORTED", "CONTRADICTED", "INSUFFICIENT", "CONFLICTING_EVIDENCE"
        }:
            raise ValueError(f"Etiqueta gold inválida en {c['id']}.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== CAMPAÑA COMPARATIVA EVIDENCEVERIFIER ===")
    print(f"Casos: {len(cases)} | Dataset: {args.dataset}")
    print(f"Referencia: {args.baseline}")
    print(f"Experimental: {args.experimental}")
    print("Se ejecutan secuencialmente para no mantener dos modelos NLI en memoria.")
    print("\n--- Ejecutando 0.2.1 ---", flush=True)
    records_021, summary_021 = run_version(
        "0.2.1", args.baseline, cases, OUTPUT_DIR, False,
        args.ollama_url, args.ollama_model, args.timeout, args.progress_every
    )

    print("\n--- Ejecutando 0.2.2 experimental (normalización Qwen activada) ---", flush=True)
    records_022, summary_022 = run_version(
        "0.2.2", args.experimental, cases, OUTPUT_DIR, True,
        args.ollama_url, args.ollama_model, args.timeout, args.progress_every
    )

    by_id_021 = {r["id"]: r for r in records_021}
    by_id_022 = {r["id"]: r for r in records_022}
    comparison_rows = []
    transitions = Counter()
    improved, worsened, unchanged = [], [], []
    norm_totals = Counter()

    for case in cases:
        a, b = by_id_021[case["id"]], by_id_022[case["id"]]
        change = f"{a['predicted']} -> {b['predicted']}"
        transitions[change] += 1
        if not a["correct"] and b["correct"]:
            improved.append(case["id"])
        elif a["correct"] and not b["correct"]:
            worsened.append(case["id"])
        else:
            unchanged.append(case["id"])

        norm = b.get("normalization") or {}
        for k in ("requested", "succeeded", "fallback"):
            norm_totals[k] += int(norm.get(k, 0) or 0)

        comparison_rows.append({
            "id": case["id"],
            "group": case["group"],
            "claim": case["claim"],
            "evidence": case["evidence"],
            "gold": a["gold"],
            "predicted_0_2_1": a["predicted"],
            "predicted_0_2_2": b["predicted"],
            "correct_0_2_1": a["correct"],
            "correct_0_2_2": b["correct"],
            "change": change,
            "seconds_0_2_1": a["elapsed_seconds"],
            "seconds_0_2_2": b["elapsed_seconds"],
            "entailment_0_2_1": a["best_entailment_score"],
            "contradiction_0_2_1": a["best_contradiction_score"],
            "entailment_0_2_2": b["best_entailment_score"],
            "contradiction_0_2_2": b["best_contradiction_score"],
            "normalization_requested": norm.get("requested", 0),
            "normalization_succeeded": norm.get("succeeded", 0),
            "normalization_fallback": norm.get("fallback", 0),
        })

    summary = {
        "evaluation": "EvidenceVerifier 0.2.1 vs 0.2.2 experimental",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "dataset": str(args.dataset),
        "dataset_name": dataset.get("dataset"),
        "total_cases": len(cases),
        "method": {
            "same_cases_and_order": True,
            "same_claims_and_evidence": True,
            "evidence_split_delimiter": "||",
            "max_evidence_per_claim": 10,
            "nli_model": "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7",
            "thresholds": {"entailment": 0.80, "contradiction": 0.80, "decision_margin": 0.15},
            "experimental_normalization": f"Ollama {args.ollama_model}",
            "execution_order": ["0.2.1", "0.2.2"],
            "gold_label_field": "gold_verifier (fallback gold_nli)",
        },
        "version_0_2_1": summary_021,
        "version_0_2_2": summary_022,
        "delta_accuracy_percentage_points": round(summary_022["accuracy_pct"] - summary_021["accuracy_pct"], 2),
        "improved_cases": improved,
        "worsened_cases": worsened,
        "unchanged_correctness_cases": unchanged,
        "prediction_transitions": dict(transitions),
        "normalization_totals_0_2_2": dict(norm_totals),
        "limitations": [
            "Dataset sintético curado; no equivale a un benchmark externo.",
            "La evaluación mide clasificación de pares afirmación-evidencia, no calidad de extracción de claims ni RAG real.",
            "Los textos separados por || se entregan como evidencias RAG independientes.",
            "La normalización con Qwen puede alterar negaciones, modalidad, cantidades o relaciones; auditar textos originales y normalizados en el JSON.",
            "Los scores NLI no son probabilidades calibradas.",
            "La latencia de 0.2.2 incluye llamadas a Ollama; la de 0.2.1 no.",
        ],
    }

    (OUTPUT_DIR / "informe_comparativo.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "resultados_0_2_1_detallados.json").write_text(
        json.dumps(records_021, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "resultados_0_2_2_detallados.json").write_text(
        json.dumps(records_022, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_csv(OUTPUT_DIR / "comparacion_por_caso.csv", comparison_rows)

    print("\n=== RESULTADO ===")
    print(f"0.2.1: {summary_021['correct']}/{summary_021['cases']} = {summary_021['accuracy_pct']}%")
    print(f"0.2.2: {summary_022['correct']}/{summary_022['cases']} = {summary_022['accuracy_pct']}%")
    print(f"Diferencia: {summary['delta_accuracy_percentage_points']:+.2f} puntos porcentuales")
    print(f"Mejoraron: {len(improved)} | Empeoraron: {len(worsened)} | Sin cambio en acierto: {len(unchanged)}")
    print(f"Normalizaciones: {dict(norm_totals)}")
    print(f"Informes guardados en: {OUTPUT_DIR}")
    print("Revisar especialmente resultados_0_2_2_detallados.json para auditar cada normalización.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
