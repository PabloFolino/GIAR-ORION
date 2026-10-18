#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G1-RAG-15: comparación controlada de respuestas reales de Qwen mediante Ollama.
Lee los fragmentos top-5 ya registrados en el detalle.csv de G1-RAG-12.
No modifica main.py ni el retriever de producción.

Uso desde la raíz GIAR-ORION:
  python Tests/test_g1_rag15_qwen_answer_comparison.py
  python Tests/test_g1_rag15_qwen_answer_comparison.py --input "ruta\\detalle.csv"
  python Tests/test_g1_rag15_qwen_answer_comparison.py --model qwen3:8b --temperature 0

Salidas: Tests/results_g1_rag15/
  respuestas.csv       Una fila por caso y versión, con respuesta completa.
  detalle_evidencia.csv Los cinco fragmentos enviados en cada llamada.
  metadatos.json       Configuración, fuente, estado y tiempos.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "Tests" / "results_g1_rag15"
DEFAULT_INPUT_CANDIDATES = [
    ROOT / "Tests" / "results_g1_rag12" / "detalle.csv",
    ROOT / "Tests" / "results_g1_rag12" / "detalle(7).csv",
    ROOT / "Tests" / "results_g1_rag12" / "detalle(6).csv",
    ROOT / "Tests" / "results_g1_rag12" / "detalle(5).csv",
    ROOT / "Tests" / "results_g1_rag12" / "detalle(4).csv",
    ROOT / "Tests" / "results_g1_rag12" / "detalle(3).csv",
    ROOT / "Tests" / "results_g1_rag12" / "detalle(2).csv",
    ROOT / "Tests" / "results_g1_rag12" / "detalle(1).csv",
]

SYSTEM_PROMPT = """Sos GIAR-ORION, un asistente técnico especializado en robótica y MJCF.
Respondé en español, con precisión y de forma directa.
Usá únicamente la evidencia proporcionada en los fragmentos.
No completes con conocimiento externo ni inventes datos.
Si la evidencia no alcanza para responder una parte, decilo explícitamente.
Diferenciá los hechos explícitos de cualquier inferencia.
No afirmes que consultaste archivos o fuentes fuera de los fragmentos.
No muestres razonamiento interno; entregá una respuesta técnica verificable."""

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="G1-RAG-15: respuestas Qwen old vs new")
    p.add_argument("--input", type=Path, help="CSV detalle.csv de G1-RAG-12 (top-5 ya recuperados)")
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT, help="Directorio de salida")
    p.add_argument("--model", default="qwen3:8b", help="Modelo instalado en Ollama (default: qwen3:8b)")
    p.add_argument("--ollama-url", default="http://localhost:11434", help="Base URL de Ollama")
    p.add_argument("--temperature", type=float, default=0.0, help="Temperatura (default: 0)")
    p.add_argument("--timeout", type=int, default=300, help="Timeout por respuesta en segundos")
    p.add_argument("--limit", type=int, default=0, help="Limitar número de consultas (0 = todas)")
    p.add_argument("--force", action="store_true", help="Volver a ejecutar aunque existan respuestas.csv")
    return p.parse_args()

def locate_input(explicit: Path | None) -> Path:
    if explicit:
        path = explicit.expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"No existe el CSV indicado: {path}")
        return path

    # 1) Preferir las ubicaciones convencionales.
    for candidate in DEFAULT_INPUT_CANDIDATES:
        if candidate.is_file():
            return candidate

    # 2) Buscar recursivamente dentro de Tests. Validar el esquema para no
    # confundirlo con CSV de resumen u otros experimentos.
    tests_dir = ROOT / "Tests"
    required = {"candidate", "case_id", "query", "rank", "source", "score", "text"}
    matches = []
    if tests_dir.is_dir():
        for candidate in tests_dir.rglob("detalle*.csv"):
            try:
                with candidate.open("r", newline="", encoding="utf-8-sig") as f:
                    headers = set(next(csv.reader(f), []))
                if required.issubset(headers):
                    # Preferir rutas que mencionen RAG-12; en empate, el más reciente.
                    rag12_priority = int("rag12" in str(candidate).lower() or "rag-12" in str(candidate).lower())
                    matches.append((rag12_priority, candidate.stat().st_mtime, candidate))
            except (OSError, StopIteration, UnicodeDecodeError):
                continue
    if matches:
        matches.sort(key=lambda item: (item[0], item[1]), reverse=True)
        chosen = matches[0][2]
        if len(matches) > 1:
            print("Se encontraron varios CSV compatibles:")
            for _, _, candidate in matches[:10]:
                print(f"  - {candidate}")
            print(f"Se usará el más probable por ruta/fecha: {chosen}")
        return chosen

    raise FileNotFoundError(
        "No encontré un CSV de detalle compatible dentro de Tests. "
        "Copiá el detalle.csv de G1-RAG-12 a "
        f"{ROOT / 'Tests' / 'results_g1_rag12'} o ejecutá con --input y la ruta completa."
    )

def ollama_chat(base_url: str, model: str, system_prompt: str, user_prompt: str,
                temperature: float, timeout: int) -> dict[str, Any]:
    payload = {
        "model": model,
        "stream": False,
        "think": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {"temperature": temperature, "seed": 42},
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/api/chat",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
        data = json.loads(raw)
        message = data.get("message", {}) or {}
        return {
            "status": "OK",
            "answer": message.get("content", "") or "",
            "thinking": message.get("thinking", "") or "",
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "prompt_eval_count": data.get("prompt_eval_count"),
            "eval_count": data.get("eval_count"),
            "error": "",
        }
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return {"status": "ERROR", "answer": "", "thinking": "",
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "prompt_eval_count": None, "eval_count": None,
                "error": f"HTTP {exc.code}: {detail[:1500]}"}
    except Exception as exc:
        return {"status": "ERROR", "answer": "", "thinking": "",
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "prompt_eval_count": None, "eval_count": None,
                "error": f"{type(exc).__name__}: {exc}"}

def make_user_prompt(query: str, chunks: list[dict[str, Any]]) -> str:
    parts = [
        "CONSULTA DEL USUARIO:",
        query,
        "",
        "EVIDENCIA RECUPERADA (fragmentos ordenados por ranking; no son necesariamente completos):",
    ]
    for c in chunks:
        parts.extend([
            "",
            f"--- FRAGMENTO {c['rank']} | archivo={c['source']} | score={c['score']} ---",
            c["text"],
            f"--- FIN FRAGMENTO {c['rank']} ---",
        ])
    parts.extend([
        "",
        "Respondé la consulta basándote exclusivamente en estos fragmentos. "
        "Si hay una distinción o dato que no aparece en la evidencia, señalá la limitación.",
    ])
    return "\n".join(parts)

def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def main() -> int:
    args = parse_args()
    input_path = locate_input(args.input)
    outdir = args.output_dir.expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    answers_path = outdir / "respuestas.csv"
    evidence_path = outdir / "detalle_evidencia.csv"
    metadata_path = outdir / "metadatos.json"

    if answers_path.exists() and not args.force:
        print(f"Ya existe {answers_path}")
        print("Para evitar repetir llamadas y sobreescribir resultados, el programa se detiene.")
        print("Usá --force para ejecutar de nuevo.")
        return 2

    with input_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        columns = reader.fieldnames or []

    required = {"candidate", "case_id", "query", "rank", "source", "score", "text"}
    missing = required - set(columns)
    if missing:
        print(f"CSV incompatible. Faltan columnas: {', '.join(sorted(missing))}")
        print(f"Columnas encontradas: {columns}")
        return 2

    normalized = []
    for row in rows:
        try:
            rank = int(float(row.get("rank", "0")))
        except (ValueError, TypeError):
            continue
        if rank < 1 or rank > 5:
            continue
        candidate = (row.get("candidate") or "").strip().lower()
        if candidate not in {"old", "new"}:
            continue
        normalized.append({**row, "rank": rank, "candidate": candidate})

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in normalized:
        grouped.setdefault((row["case_id"], row["candidate"]), []).append(row)
    case_queries: dict[str, str] = {}
    for row in normalized:
        case_queries.setdefault(row["case_id"], row["query"])
    case_ids = sorted(case_queries)
    if args.limit > 0:
        case_ids = case_ids[:args.limit]

    # Confirm the local Ollama service/model before processing all 10 calls.
    try:
        req = urllib.request.Request(args.ollama_url.rstrip("/") + "/api/tags")
        with urllib.request.urlopen(req, timeout=10) as response:
            tags = json.loads(response.read().decode("utf-8"))
        installed_models = [m.get("name", "") for m in tags.get("models", [])]
        if not any(m == args.model or m.split(":")[0] == args.model.split(":")[0]
                   for m in installed_models):
            print(f"Advertencia: no veo '{args.model}' en los modelos de Ollama.")
            print("Modelos detectados:", ", ".join(installed_models) or "(ninguno)")
            print("Se intentará ejecutar; Ollama podría descargar el modelo si corresponde.")
    except Exception as exc:
        print(f"No se pudo consultar Ollama en {args.ollama_url}: {exc}")
        print("Verificá que Ollama esté iniciado. No se generaron respuestas.")
        return 3

    answer_rows: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    expected_calls = len(case_ids) * 2
    completed = 0
    print(f"G1-RAG-15 | modelo={args.model} | consultas={len(case_ids)} | llamadas previstas={expected_calls}")
    print(f"Entrada: {input_path}")
    print(f"Salida:  {outdir}")

    for case_id in case_ids:
        for candidate in ("old", "new"):
            chunks = sorted(grouped.get((case_id, candidate), []), key=lambda x: x["rank"])
            if not chunks:
                answer_rows.append({
                    "case_id": case_id, "candidate": candidate, "query": case_queries[case_id],
                    "model": args.model, "temperature": args.temperature, "status": "ERROR",
                    "answer": "", "thinking": "", "elapsed_seconds": "", "prompt_eval_count": "",
                    "eval_count": "", "chunk_count": 0, "source_file": str(input_path),
                    "error": "No se encontraron fragmentos para esta consulta y versión.",
                    "technical_accuracy_review": "PENDIENTE",
                    "evidence_coverage_review": "PENDIENTE",
                    "unsupported_claims_review": "PENDIENTE",
                    "review_notes": "",
                })
                continue
            if len(chunks) != 5:
                print(f"Advertencia: {case_id}/{candidate} tiene {len(chunks)} fragmentos (se esperaban 5).")
            for c in chunks:
                evidence_rows.append({
                    "case_id": case_id, "candidate": candidate, "rank": c["rank"],
                    "source": c["source"], "score": c["score"],
                    "expected_terms_found": c.get("expected_terms_found", ""),
                    "text": c["text"],
                })
            prompt = make_user_prompt(case_queries[case_id], chunks)
            print(f"[{completed+1}/{expected_calls}] {case_id} | {candidate} ...", flush=True)
            result = ollama_chat(args.ollama_url, args.model, SYSTEM_PROMPT, prompt,
                                 args.temperature, args.timeout)
            completed += 1
            answer_rows.append({
                "case_id": case_id, "candidate": candidate, "query": case_queries[case_id],
                "model": args.model, "temperature": args.temperature, "status": result["status"],
                "answer": result["answer"], "thinking": result["thinking"],
                "elapsed_seconds": result["elapsed_seconds"],
                "prompt_eval_count": result["prompt_eval_count"], "eval_count": result["eval_count"],
                "chunk_count": len(chunks), "source_file": str(input_path), "error": result["error"],
                "technical_accuracy_review": "PENDIENTE",
                "evidence_coverage_review": "PENDIENTE",
                "unsupported_claims_review": "PENDIENTE",
                "review_notes": "",
            })
            print(f"    estado={result['status']} tiempo={result['elapsed_seconds']} s")
            if result["error"]:
                print(f"    error={result['error'][:250]}")

    write_csv(answers_path, answer_rows)
    write_csv(evidence_path, evidence_rows)
    metadata = {
        "experiment": "G1-RAG-15",
        "description": "Comparación controlada de respuestas reales de Qwen con los top-5 fragmentos ya recuperados por G1-RAG-12.",
        "created_at_local": datetime.now().astimezone().isoformat(),
        "input_csv": str(input_path),
        "output_dir": str(outdir),
        "ollama_url": args.ollama_url,
        "model": args.model,
        "temperature": args.temperature,
        "seed": 42,
        "system_prompt": SYSTEM_PROMPT,
        "method": "Cada consulta se envía dos veces: una con los cinco fragmentos old y otra con los cinco fragmentos new. Mismo modelo, system prompt, temperatura y seed.",
        "case_ids": case_ids,
        "expected_calls": expected_calls,
        "completed_calls": completed,
        "success_count": sum(1 for r in answer_rows if r["status"] == "OK"),
        "error_count": sum(1 for r in answer_rows if r["status"] != "OK"),
        "notes": [
            "No se recalcula la recuperación: se reutilizan los fragmentos del CSV de G1-RAG-12.",
            "No se modifica main.py ni Agent/MultilingualKnowledgeRetriever.py.",
            "Los campos de revisión quedan PENDIENTE para evaluación técnica posterior.",
            "El parámetro think=false puede ser ignorado por versiones antiguas de Ollama; se conserva cualquier campo thinking que la API devuelva.",
            "La misma semilla y temperatura reducen variabilidad, pero no garantizan identidad determinista en todos los entornos.",
        ],
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nExperimento finalizado.")
    print(f"Respuestas: {answers_path}")
    print(f"Evidencia:  {evidence_path}")
    print(f"Metadatos:  {metadata_path}")
    print(f"Éxitos: {metadata['success_count']} | Errores: {metadata['error_count']}")
    if metadata["error_count"]:
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
