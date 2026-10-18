#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Inspección independiente de la fragmentación de la sección de articulaciones G1.
No modifica el recuperador ni ningún documento. Solo lee Markdown y muestra cómo
se comportan dos estrategias de fragmentación para la sección 6.3.

Ejecutar desde la raíz de GIAR-ORION:
  python Tests\inspect_g1_chunking.py
  python Tests\inspect_g1_chunking.py --md "Knowledge\Unitree\G1\Unitree_G1_Dossier_Tecnico_GIAR_ORION.md"
"""
import argparse
import csv
import re
from datetime import datetime
from pathlib import Path

QUERIES = {
    "G1-01": {
        "query": "articulaciones de la pierna izquierda",
        "terms": ["left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
                  "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint"],
    },
    "G1-02": {
        "query": "articulaciones de la cintura",
        "terms": ["waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint"],
    },
    "G1-05": {
        "query": "articulaciones de la mano derecha",
        "terms": ["right_hand_thumb_0_joint", "right_hand_thumb_1_joint",
                  "right_hand_thumb_2_joint", "right_hand_index_0_joint",
                  "right_hand_index_1_joint", "right_hand_middle_0_joint",
                  "right_hand_middle_1_joint"],
    },
}

def default_markdown():
    candidates = [
        Path("Knowledge/Unitree/G1/Unitree_G1_Dossier_Tecnico_GIAR_ORION.md"),
        Path("Knowledge/Unitree/G1/Unitree_G1_Dossier_Tecnico_GIAR_ORION(3).md"),
        Path("Knowledge/Unitree/G1/Unitree_G1_Dossier_Tecnico_GIAR_ORION_actualizado.md"),
    ]
    return next((p for p in candidates if p.is_file()), None)

def extract_section(text):
    marker = "### 6.3 Inventario nominal de las 43 articulaciones actuadas"
    parts = text.split(marker, 1)
    if len(parts) != 2:
        return None
    tail = parts[1]
    end = re.search(r"\n## \d+\.", tail)
    section = tail[:end.start()] if end else tail
    return marker + section

def chunk_by_chars(text, size=1100, overlap=150):
    # Approximation for comparison only; not the production implementation.
    result = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        piece = text[start:end].strip()
        if piece:
            result.append(piece)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return result

def chunk_by_heading_groups(text, max_chars=1000):
    # Preserve each named group heading and its list together where possible.
    lines = text.splitlines()
    groups = []
    current = []
    for line in lines:
        if line.startswith("**") and ("—" in line or ":" in line):
            if current:
                groups.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        groups.append("\n".join(current).strip())

    chunks = []
    buffer = ""
    for group in groups:
        if not group:
            continue
        if len(group) > max_chars:
            if buffer:
                chunks.append(buffer.strip())
                buffer = ""
            chunks.extend(chunk_by_chars(group, max_chars, 120))
        elif not buffer:
            buffer = group
        elif len(buffer) + 2 + len(group) <= max_chars:
            buffer += "\n\n" + group
        else:
            chunks.append(buffer.strip())
            buffer = group
    if buffer:
        chunks.append(buffer.strip())
    return chunks

def term_coverage(chunk, terms):
    found = [term for term in terms if term in chunk]
    return len(found), len(terms), found

def main():
    parser = argparse.ArgumentParser(description="Inspecciona fragmentos de la sección 6.3 del dossier G1.")
    parser.add_argument("--md", type=Path, help="Ruta al dossier Markdown.")
    parser.add_argument("--out", type=Path, default=Path("Tests"), help="Carpeta de salida.")
    parser.add_argument("--show-all", action="store_true", help="Mostrar el texto completo de cada fragmento.")
    args = parser.parse_args()

    md_path = args.md or default_markdown()
    if not md_path or not md_path.is_file():
        print("ERROR: no se encontró el Markdown. Indicá su ruta con --md.")
        return 2

    full_text = md_path.read_text(encoding="utf-8-sig")
    section = extract_section(full_text)
    if section is None:
        print("ERROR: no se encontró el encabezado de la sección 6.3 esperado.")
        print("Encabezado esperado: ### 6.3 Inventario nominal de las 43 articulaciones actuadas")
        return 2

    strategies = {
        "char_1100_overlap_150": chunk_by_chars(section, 1100, 150),
        "grouped_by_heading": chunk_by_heading_groups(section, 1000),
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = args.out / f"results_g1_chunk_inspection_{stamp}"
    outdir.mkdir(parents=True, exist_ok=True)
    rows = []
    report = [
        "INSPECCIÓN DE FRAGMENTACIÓN — DOSSIER UNITREE G1",
        "=" * 72,
        f"Markdown: {md_path.resolve()}",
        f"Longitud de la sección 6.3: {len(section)} caracteres",
        "",
        "IMPORTANTE: char_1100_overlap_150 es una aproximación de ventana de caracteres,",
        "no una llamada al fragmentador real de producción.",
    ]

    for method, chunks in strategies.items():
        report += ["", "#" * 72, f"MÉTODO: {method}", f"Cantidad de fragmentos: {len(chunks)}"]
        for i, chunk in enumerate(chunks, 1):
            report += ["", f"FRAGMENTO {i} | caracteres={len(chunk)}"]
            for qid, data in QUERIES.items():
                found_count, total, found = term_coverage(chunk, data["terms"])
                if found_count:
                    report.append(f"  Coincide con {qid} ({data['query']}): {found_count}/{total}: {', '.join(found)}")
            report.append("  TEXTO:")
            report.append(chunk if args.show_all else (chunk if len(chunk) <= 1800 else chunk[:1800] + "\n...[TRUNCADO EN EL INFORME]..."))
            rows.append({
                "method": method, "chunk_id": i, "characters": len(chunk),
                "contains_left_leg_terms": sum(t in chunk for t in QUERIES["G1-01"]["terms"]),
                "contains_waist_terms": sum(t in chunk for t in QUERIES["G1-02"]["terms"]),
                "contains_right_hand_terms": sum(t in chunk for t in QUERIES["G1-05"]["terms"]),
                "text": chunk,
            })

    report_path = outdir / "informe_fragmentos.txt"
    report_path.write_text("\n".join(report), encoding="utf-8")
    csv_path = outdir / "fragmentos.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Inspección finalizada.")
    print("Archivo Markdown:", md_path.resolve())
    print("Longitud de sección 6.3:", len(section), "caracteres")
    for method, chunks in strategies.items():
        print(f"{method}: {len(chunks)} fragmentos")
        for qid, data in QUERIES.items():
            best = max((term_coverage(chunk, data["terms"])[0] for chunk in chunks), default=0)
            print(f"  {qid}: mejor fragmento {best}/{len(data['terms'])} términos esperados")
    print("Informe:", report_path.resolve())
    print("CSV:", csv_path.resolve())
    print("No se modificó ningún archivo de producción.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
