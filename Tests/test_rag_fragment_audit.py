from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_ROOT = ROOT / "Tests" / "results_rag_fusion_rrf"


def normalize(text: str) -> str:
    text = (text or "").casefold()
    text = re.sub(r"`+", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s./\\-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def looks_like_toc(text: str) -> bool:
    t = (text or "").casefold()
    toc_signals = [
        "](#", "tabla de contenidos", "índice", "bibliografía",
        "fuentes primarias y técnicas", "https://", "http://"
    ]
    # A fragment with many Markdown links or many numbered section entries is suspicious.
    links = len(re.findall(r"\]\(#", t))
    numbered_sections = len(re.findall(r"(?:^|\s)\d{1,2}\.\s", t))
    url_count = len(re.findall(r"https?://", t))
    return links >= 3 or (numbered_sections >= 7 and len(t) < 3000) or (
        url_count >= 4 and len(t) < 2500
    ) or ("bibliografía" in t and len(t) < 1200)


def is_short_or_generic(text: str) -> bool:
    words = re.findall(r"\w+", text or "", flags=re.UNICODE)
    t = (text or "").casefold()
    generic_markers = [
        "este documento", "fuentes primarias", "conclusiones",
        "objetivo:", "propósito:", "fecha de consulta:"
    ]
    return len(words) < 35 or sum(m in t for m in generic_markers) >= 2


def latest_results_dir(root: Path) -> Path:
    dirs = [p for p in root.iterdir() if p.is_dir()]
    if not dirs:
        raise FileNotFoundError(f"No se encontraron carpetas de resultados en: {root}")
    # Timestamp directory names are sortable; fall back to modification time.
    return sorted(dirs, key=lambda p: (p.name, p.stat().st_mtime))[-1]


def read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audita rankings RRF existentes sin cargar modelos ni modificar recuperadores."
    )
    parser.add_argument("--input", type=Path, default=None,
                        help="Ruta a resultados_detallados.csv. Si se omite, usa la carpeta de resultados más reciente.")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Carpeta de salida. Por defecto crea una subcarpeta audit_<fecha> en Tests.")
    args = parser.parse_args()

    if args.input:
        input_csv = args.input.resolve()
    else:
        result_dir = latest_results_dir(DEFAULT_INPUT_ROOT)
        input_csv = result_dir / "resultados_detallados.csv"

    if not input_csv.exists():
        raise FileNotFoundError(f"No existe el CSV: {input_csv}")

    rows = read_rows(input_csv)
    if not rows:
        raise ValueError("El CSV no contiene filas.")

    out_dir = (args.output_dir.resolve() if args.output_dir else
               ROOT / "Tests" / f"results_rag_fragment_audit_{datetime.now():%Y%m%d_%H%M%S}")
    out_dir.mkdir(parents=True, exist_ok=True)

    by_case_method: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_case_method[(row.get("case_id", ""), row.get("method", ""))].append(row)

    detail_out = []
    summary_out = []
    methods = ["lexical_only", "semantic_only", "rrf_fusion"]

    for (case_id, method), items in sorted(by_case_method.items()):
        items.sort(key=lambda r: int(float(r.get("rank") or 999)))
        for row in items:
            text = row.get("text", "") or ""
            normalized = normalize(text)
            words = re.findall(r"\w+", text, flags=re.UNICODE)
            flags = []
            if looks_like_toc(text):
                flags.append("posible_indice_bibliografia_o_enlaces")
            if is_short_or_generic(text):
                flags.append("fragmento_corto_o_generico")
            detail_out.append({
                "case_id": case_id,
                "method": method,
                "rank": row.get("rank", ""),
                "source": row.get("source", ""),
                "score": row.get("score", ""),
                "rrf_score": row.get("rrf_score", ""),
                "lexical_rank": row.get("lexical_rank", ""),
                "semantic_rank": row.get("semantic_rank", ""),
                "word_count": len(words),
                "normalized_char_count": len(normalized),
                "quality_flags": ";".join(flags),
                "term_coverage": row.get("term_coverage", ""),
                "found_terms": row.get("found_terms", ""),
                "expected_source_found": row.get("expected_source_found", ""),
                "text": text,
            })

        top = items[:5]
        flagged = sum(bool(looks_like_toc(r.get("text", "")) or is_short_or_generic(r.get("text", ""))) for r in top)
        sources = [r.get("source", "") for r in top]
        summary_out.append({
            "case_id": case_id,
            "method": method,
            "top5_flagged_fragments": flagged,
            "top5_distinct_sources": len(set(sources)),
            "top5_sources": " || ".join(sources),
            "top5_mean_term_coverage": round(sum(float(r.get("term_coverage") or 0) for r in top) / max(len(top), 1), 4),
        })

    # Compare normalized text overlap across the three rankings for each query.
    overlap_out = []
    cases = sorted({r.get("case_id", "") for r in rows})
    for case_id in cases:
        method_texts = {}
        for method in methods:
            subset = sorted(by_case_method.get((case_id, method), []),
                            key=lambda r: int(float(r.get("rank") or 999)))[:5]
            method_texts[method] = {normalize(r.get("text", "")) for r in subset if normalize(r.get("text", ""))}
        lex, sem, rrf = (method_texts.get(m, set()) for m in methods)
        overlap_out.append({
            "case_id": case_id,
            "lexical_semantic_exact_overlap": len(lex & sem),
            "lexical_rrf_exact_overlap": len(lex & rrf),
            "semantic_rrf_exact_overlap": len(sem & rrf),
            "lexical_unique_top5": len(lex - sem),
            "semantic_unique_top5": len(sem - lex),
            "note": "Coincidencia exacta normalizada; no detecta fragmentos parcialmente solapados."
        })

    def write_csv(name: str, data: list[dict]) -> None:
        if not data:
            return
        with (out_dir / name).open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            writer.writeheader()
            writer.writerows(data)

    write_csv("auditoria_fragmentos.csv", detail_out)
    write_csv("resumen_calidad_por_consulta.csv", summary_out)
    write_csv("solapamiento_rankings.csv", overlap_out)

    print("GIAR-ORION — Auditoría de fragmentos y rankings")
    print(f"Entrada: {input_csv}")
    print(f"Filas analizadas: {len(rows)}")
    print(f"Salida: {out_dir}")
    print()
    print("Resumen de posibles fragmentos problemáticos en los primeros cinco resultados:")
    for item in summary_out:
        print(f"  {item['case_id']:12} {item['method']:14} "
              f"marcados={item['top5_flagged_fragments']}/5 "
              f"fuentes={item['top5_distinct_sources']} "
              f"cobertura_media={item['top5_mean_term_coverage']}")
    print()
    print("Archivos generados:")
    print(f"  {out_dir / 'auditoria_fragmentos.csv'}")
    print(f"  {out_dir / 'resumen_calidad_por_consulta.csv'}")
    print(f"  {out_dir / 'solapamiento_rankings.csv'}")
    print()
    print("Nota: los indicadores son heurísticos; no sustituyen una evaluación humana de relevancia.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
