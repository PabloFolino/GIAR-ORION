# -*- coding: utf-8 -*-
"""G1-RAG-08A: prepara una planilla de revisión humana de evidencia.

Ejecutar desde la raíz de GIAR-ORION:
    python Tests\\test_g1_rag08a_human_review.py
Opcional:
    python Tests\\test_g1_rag08a_human_review.py --results-dir Tests\\results_g1_rag07_YYYYMMDD_HHMMSS

No modifica main.py ni los retrievers. Produce revision_humana.csv para completar manualmente.
"""
from __future__ import annotations
import argparse, csv
from pathlib import Path


def read_csv(path):
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    fields = list(rows[0].keys()) if rows else []
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--results-dir', type=Path, default=None,
                   help='Directorio results_g1_rag07_...; por defecto usa el más reciente.')
    p.add_argument('--top-chunks', type=int, default=3,
                   help='Cantidad máxima de fragmentos a incluir por consulta (default: 3).')
    a = p.parse_args()
    root = Path('Tests')
    if a.top_chunks < 1:
        p.error('--top-chunks debe ser >= 1')
    if a.results_dir:
        folder = a.results_dir
    else:
        candidates = sorted(root.glob('results_g1_rag07_*'), key=lambda x: x.stat().st_mtime, reverse=True)
        if not candidates:
            raise SystemExit('ERROR: no encontré Tests/results_g1_rag07_*. Ejecutá primero G1-RAG-07.')
        folder = candidates[0]
    summary_path, detail_path = folder/'resumen.csv', folder/'detalle.csv'
    if not summary_path.exists() or not detail_path.exists():
        raise SystemExit(f'ERROR: faltan resumen.csv o detalle.csv en {folder.resolve()}')
    summary, detail = read_csv(summary_path), read_csv(detail_path)
    by_id = {}
    for d in detail:
        by_id.setdefault(d.get('case_id',''), []).append(d)
    out = []
    for s in summary:
        chunks = sorted(by_id.get(s.get('case_id',''), []), key=lambda x: int(x.get('rank') or 999))[:a.top_chunks]
        if not chunks:
            chunks = [{'rank':'', 'source':'', 'score':'', 'text':'SIN FRAGMENTO RECUPERADO'}]
        for d in chunks:
            out.append({
                'case_id': s.get('case_id',''),
                'query': s.get('query',''),
                'predicted_route': s.get('predicted_route',''),
                'acceptable_routes': s.get('acceptable_routes',''),
                'rank': d.get('rank',''),
                'source': d.get('source',''),
                'retrieval_score': d.get('score',''),
                'retrieved_text': d.get('text',''),
                'relevance_judgment': 'PENDIENTE',
                'answers_query': 'PENDIENTE',
                'evidence_sufficient': 'PENDIENTE',
                'review_notes': '',
            })
    out_path = folder/'revision_humana.csv'
    write_csv(out_path, out)
    print(f'Casos: {len(summary)}')
    print(f'Fragmentos incluidos: {len(out)} (hasta {a.top_chunks} por consulta)')
    print(f'Archivo creado: {out_path.resolve()}')
    print('\nCompletar estas columnas:')
    print('relevance_judgment: RELEVANTE | PARCIAL | IRRELEVANTE')
    print('answers_query: SI | PARCIALMENTE | NO')
    print('evidence_sufficient: SI | NO | NO_APLICA')
    print('No modificar las columnas de consulta, ruta, fuente ni texto recuperado.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
