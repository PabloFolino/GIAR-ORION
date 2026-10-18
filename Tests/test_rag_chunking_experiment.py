from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer, util


ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "Knowledge"
OUTPUT_ROOT = ROOT / "Tests"

# Casos prioritarios del experimento RRF. Se incluyen consultas más específicas
# para comprobar si la fragmentación conserva el contenido técnico solicitado.
QUERIES = [
    {
        "case_id": "UNITREE-01",
        "query": "¿Cuáles son las articulaciones principales de las piernas del robot Unitree G1?",
        "terms": ["left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
                  "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",
                  "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
                  "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint"],
        "files": ["Unitree/G1/Unitree_G1_Dossier_Tecnico_GIAR_ORION.md",
                  "CoppeliaSim/CoppeliaSim_Manual_Tecnico_GIAR_ORION.md"],
    },
    {
        "case_id": "SAC-01",
        "query": "¿Cómo funciona SAC y cómo se actualizan los críticos?",
        "terms": ["crítico", "Bellman", "target", "tau", "mínimo", "critic"],
        "files": ["SAC/Fundamentos_de_SAC_GIAR_ORION.md",
                  "RL/Fundamentos_de_Aprendizaje_por_Refuerzo_RL_GIAR_ORION.md"],
    },
    {
        "case_id": "SAC-02",
        "query": "¿Qué función cumple el Replay Buffer durante el entrenamiento de SAC?",
        "terms": ["Replay Buffer", "transiciones", "experiencias", "muestreo"],
        "files": ["SAC/Fundamentos_de_SAC_GIAR_ORION.md"],
    },
    {
        "case_id": "SAC-03",
        "query": "¿Qué relación existe entre la entropía y la política en Soft Actor-Critic?",
        "terms": ["entropía", "política", "temperatura", "exploración"],
        "files": ["SAC/Fundamentos_de_SAC_GIAR_ORION.md"],
    },
    {
        "case_id": "RL-01",
        "query": "¿Qué es el aprendizaje por refuerzo y cómo aprende un agente?",
        "terms": ["agente", "entorno", "recompensa", "estado", "acción"],
        "files": ["RL/Fundamentos_de_Aprendizaje_por_Refuerzo_RL_GIAR_ORION.md"],
    },
    {
        "case_id": "DRL-01",
        "query": "¿Qué diferencia hay entre aprendizaje por refuerzo y aprendizaje profundo por refuerzo?",
        "terms": ["redes neuronales", "representaciones", "aprendizaje por refuerzo", "profundo"],
        "files": ["RL/Fundamentos_de_Aprendizaje_por_Refuerzo_RL_GIAR_ORION.md"],
    },
    {
        "case_id": "COPPELIA-01",
        "query": "¿Cómo se configuran las articulaciones y la dinámica física en CoppeliaSim?",
        "terms": ["articulaciones", "dinámica", "motor físico", "respondible"],
        "files": ["CoppeliaSim/CoppeliaSim_Manual_Tecnico_GIAR_ORION.md"],
    },
    {
        "case_id": "PYTORCH-01",
        "query": "¿Cómo comprobar si PyTorch puede utilizar la GPU NVIDIA mediante CUDA?",
        "terms": ["torch.cuda.is_available", "CUDA", "GPU"],
        "files": [],
    },
    {
        "case_id": "ROBOT-01",
        "query": "¿Cómo se relacionan las observaciones, las acciones y la función de recompensa en el control de un robot?",
        "terms": ["observaciones", "acciones", "recompensa", "política"],
        "files": [],
    },
    {
        "case_id": "AGENT-01",
        "query": "¿Cómo se recuperan documentos de la base de conocimientos de GIAR-ORION?",
        "terms": ["recuperador", "fragmentos", "embeddings", "búsqueda semántica"],
        "files": [],
    },
]


@dataclass
class Chunk:
    source: str
    heading: str
    text: str
    strategy: str


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def markdown_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def parse_markdown(path: Path, root: Path) -> list[tuple[str, str]]:
    """Return (heading path, body block) pairs, keeping the active Markdown heading."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    heading_stack: list[tuple[int, str]] = []
    blocks: list[tuple[str, str]] = []
    current: list[str] = []

    def heading_path() -> str:
        return " > ".join(label for _, label in heading_stack)

    def flush() -> None:
        nonlocal current
        body = "\n".join(current).strip()
        body = re.sub(r"\n{3,}", "\n\n", body)
        if body:
            blocks.append((heading_path(), body))
        current = []

    for line in text.splitlines():
        match = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match:
            flush()
            level = len(match.group(1))
            label = match.group(2).strip()
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, label))
        else:
            current.append(line)
    flush()
    return blocks


def is_navigation_or_references(text: str, heading: str) -> bool:
    combined = f"{heading}\n{text}".casefold()
    link_count = len(re.findall(r"\]\(", text))
    url_count = len(re.findall(r"https?://", text, flags=re.I))
    reference_heading = any(x in heading.casefold() for x in
                            ("bibliografía", "fuentes primarias", "referencias", "índice", "tabla de contenidos"))
    toc_like = link_count >= 3 or url_count >= 4
    # Do not drop these from the corpus; mark them down-weighted/excluded only
    # for this experimental retrieval to avoid navigation-only chunks dominating.
    return reference_heading or toc_like


def split_legacy(path: Path, root: Path, chunk_chars: int = 1100,
                 overlap_chars: int = 150) -> list[Chunk]:
    """Approximate the current paragraph-based chunking described in the project notes."""
    chunks: list[Chunk] = []
    rel = path.relative_to(root).as_posix()
    for heading, body in parse_markdown(path, root):
        # Approximate current behavior: heading-prefixed paragraph blocks, then
        # character windows with overlap when a block exceeds the configured size.
        paragraphs = [normalize(p) for p in re.split(r"\n\s*\n", body) if normalize(p)]
        for paragraph in paragraphs:
            full = f"{heading}\n{paragraph}" if heading else paragraph
            if len(full) <= chunk_chars:
                chunks.append(Chunk(rel, heading, full, "legacy_approx"))
                continue
            start = 0
            while start < len(full):
                end = min(start + chunk_chars, len(full))
                piece = full[start:end].strip()
                if piece:
                    chunks.append(Chunk(rel, heading, piece, "legacy_approx"))
                if end >= len(full):
                    break
                start = max(start + 1, end - overlap_chars)
    return chunks


def split_heading_aware(path: Path, root: Path, chunk_chars: int = 1400,
                        overlap_chars: int = 180) -> list[Chunk]:
    """Keep heading context and paragraph boundaries; split only oversized paragraphs."""
    chunks: list[Chunk] = []
    rel = path.relative_to(root).as_posix()
    for heading, body in parse_markdown(path, root):
        if is_navigation_or_references(body, heading):
            # Retain in output/corpus inventory, but don't let navigation dominate retrieval.
            continue
        prefix = f"Sección: {heading}\n" if heading else ""
        paragraphs = [normalize(p) for p in re.split(r"\n\s*\n", body) if normalize(p)]
        # parse_markdown normalizes newlines, so markdown list/table blocks remain together.
        if not paragraphs:
            paragraphs = [body]
        current = prefix
        for paragraph in paragraphs:
            candidate = (current + "\n" + paragraph).strip() if current.strip() else paragraph
            if len(candidate) <= chunk_chars:
                current = candidate
                continue
            if current.strip() and len(current.strip()) > len(prefix.strip()):
                chunks.append(Chunk(rel, heading, current.strip(), "heading_aware"))
                current = prefix
            if len(paragraph) <= chunk_chars:
                current = (prefix + "\n" + paragraph).strip() if prefix else paragraph
            else:
                start = 0
                while start < len(paragraph):
                    end = min(start + chunk_chars, len(paragraph))
                    piece = paragraph[start:end].strip()
                    if piece:
                        chunks.append(Chunk(rel, heading, (prefix + "\n" + piece).strip(), "heading_aware"))
                    if end >= len(paragraph):
                        break
                    start = max(start + 1, end - overlap_chars)
                current = prefix
        if current.strip() and len(current.strip()) > len(prefix.strip()):
            chunks.append(Chunk(rel, heading, current.strip(), "heading_aware"))
    return chunks


def coverage(text: str, terms: list[str]) -> tuple[int, int, str]:
    t = text.casefold()
    found = [term for term in terms if term.casefold() in t]
    return len(found), len(terms), ";".join(found)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compara fragmentación Markdown aproximada actual frente a una estrategia consciente de encabezados."
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--model", default="intfloat/multilingual-e5-base")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--offline", action="store_true",
                        help="Exige que el modelo ya esté en la caché local.")
    args = parser.parse_args()

    if not KNOWLEDGE_DIR.exists():
        raise FileNotFoundError(f"No existe la base de conocimientos: {KNOWLEDGE_DIR}")

    files = markdown_files(KNOWLEDGE_DIR)
    if not files:
        raise FileNotFoundError(f"No hay archivos Markdown en: {KNOWLEDGE_DIR}")

    legacy_chunks: list[Chunk] = []
    new_chunks: list[Chunk] = []
    for path in files:
        legacy_chunks.extend(split_legacy(path, KNOWLEDGE_DIR))
        new_chunks.extend(split_heading_aware(path, KNOWLEDGE_DIR))

    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("Se solicitó CUDA, pero torch.cuda.is_available() es False.")
    device = ("cuda" if torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device

    print("GIAR-ORION — Experimento de fragmentación Markdown")
    print(f"Documentos Markdown: {len(files)}")
    print(f"Fragmentos baseline aproximado: {len(legacy_chunks)}")
    print(f"Fragmentos nuevos: {len(new_chunks)}")
    print(f"Modelo: {args.model} | dispositivo: {device}")
    print("Nota: el baseline reproduce la descripción conocida del fragmentador actual, no importa ni modifica su implementación original.")

    model_kwargs = {"device": device}
    if args.offline:
        model_kwargs["local_files_only"] = True
    model = SentenceTransformer(args.model, **model_kwargs)

    query_texts = ["query: " + q["query"] for q in QUERIES]
    query_embeddings = model.encode(query_texts, convert_to_tensor=True,
                                    normalize_embeddings=True, show_progress_bar=True)

    all_rows: list[dict] = []
    summary_rows: list[dict] = []
    for strategy, chunks in (("legacy_approx", legacy_chunks), ("heading_aware", new_chunks)):
        if not chunks:
            continue
        passage_texts = ["passage: " + c.text for c in chunks]
        embeddings = model.encode(passage_texts, batch_size=16, convert_to_tensor=True,
                                  normalize_embeddings=True, show_progress_bar=True)
        scores = util.cos_sim(query_embeddings, embeddings)
        for qi, q in enumerate(QUERIES):
            # A query may nominate a few likely source files, but scoring still considers all chunks.
            ranked = torch.argsort(scores[qi], descending=True).tolist()
            selected = []
            for idx in ranked:
                c = chunks[idx]
                score = float(scores[qi][idx].item())
                nav = is_navigation_or_references(c.text, c.heading)
                # New strategy excludes nav/reference chunks at construction; legacy is left untouched.
                selected.append((idx, c, score, nav))
                if len(selected) >= args.top_k:
                    break
            found_terms_all = set()
            top_coverage_sum = 0
            for rank, (idx, chunk, score, nav) in enumerate(selected, start=1):
                found_n, total_n, found_terms = coverage(chunk.text, q["terms"])
                found_terms_all.update(x for x in q["terms"] if x.casefold() in chunk.text.casefold())
                top_coverage_sum += (found_n / total_n) if total_n else 0.0
                all_rows.append({
                    "case_id": q["case_id"],
                    "strategy": strategy,
                    "rank": rank,
                    "score": round(score, 6),
                    "source": chunk.source,
                    "heading": chunk.heading,
                    "char_count": len(chunk.text),
                    "word_count": len(re.findall(r"\w+", chunk.text)),
                    "navigation_or_reference_flag": nav,
                    "expected_terms_found_in_chunk": found_terms,
                    "expected_term_coverage_in_chunk": round(found_n / total_n, 4) if total_n else 0,
                    "text": chunk.text,
                })
            summary_rows.append({
                "case_id": q["case_id"],
                "strategy": strategy,
                "top_k": args.top_k,
                "mean_top_k_term_coverage": round(top_coverage_sum / max(len(selected), 1), 4),
                "distinct_sources_top_k": len({c.source for _, c, _, _ in selected}),
                "navigation_or_reference_chunks_top_k": sum(1 for _, _, _, nav in selected if nav),
                "expected_terms_found_anywhere_top_k": ";".join(sorted(found_terms_all, key=str.casefold)),
                "expected_terms_coverage_anywhere_top_k": round(len(found_terms_all) / max(len(q["terms"]), 1), 4),
            })
        del embeddings
        if device == "cuda":
            torch.cuda.empty_cache()

    out_dir = OUTPUT_ROOT / f"results_chunking_experiment_{datetime.now():%Y%m%d_%H%M%S}"
    out_dir.mkdir(parents=True, exist_ok=True)

    def write_csv(name: str, rows: list[dict]) -> None:
        if not rows:
            return
        with (out_dir / name).open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    write_csv("ranking_comparativo.csv", all_rows)
    write_csv("resumen_comparativo.csv", summary_rows)

    # Save exact configuration and counts.
    with (out_dir / "metadatos.txt").open("w", encoding="utf-8") as f:
        f.write(f"model={args.model}\n")
        f.write(f"device={device}\n")
        f.write(f"documents={len(files)}\n")
        f.write(f"legacy_approx_chunks={len(legacy_chunks)}\n")
        f.write(f"heading_aware_chunks={len(new_chunks)}\n")
        f.write(f"top_k={args.top_k}\n")
        f.write("baseline_note=Approximation of the documented existing chunking; not a direct invocation of the production retriever.\n")

    print(f"\nExperimento finalizado. Salida: {out_dir}")
    print(f"Resumen: {out_dir / 'resumen_comparativo.csv'}")
    print(f"Rankings: {out_dir / 'ranking_comparativo.csv'}")
    print(f"Metadatos: {out_dir / 'metadatos.txt'}")
    print("\nResumen por consulta:")
    for r in summary_rows:
        print(f"  {r['case_id']:12} {r['strategy']:16} "
              f"cobertura={r['expected_terms_coverage_anywhere_top_k']:.3f} "
              f"fuentes={r['distinct_sources_top_k']} "
              f"índice/enlaces={r['navigation_or_reference_chunks_top_k']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
