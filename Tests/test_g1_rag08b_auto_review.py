# -*- coding: utf-8 -*-
"""G1-RAG-08B: evaluación automática preliminar de fragmentos con Ollama.

No modifica main.py, retrievers ni revision_humana.csv.
Ejecutar desde la raíz del proyecto:
  python Tests\\test_g1_rag08b_auto_review.py
Opciones:
  --input "Tests\\results_g1_rag07_20261012_175223\\revision_humana.csv"
  --model qwen3:8b --url http://localhost:11434
Produce revision_automatica.csv y evaluacion_automatica_metadatos.json junto al CSV de entrada.
Las etiquetas son sugerencias que requieren validación humana.
"""
from __future__ import annotations
import argparse, csv, json, time, urllib.request, urllib.error
from pathlib import Path

SYSTEM = """Sos un evaluador técnico de evidencia recuperada para un sistema RAG sobre robótica, Unitree G1, MJCF y aprendizaje por refuerzo. Evaluá SOLO el fragmento proporcionado respecto de la consulta. No uses conocimiento externo para completar lo que el fragmento no dice. No confundas compartir palabras con responder. Si la consulta pide una lista completa y el fragmento contiene solo una parte, marcá parcial. Si la consulta pide datos exactos/orden y el fragmento no demuestra ese dato, no lo supongas.
Respondé exclusivamente un objeto JSON válido con estas claves:
relevance_judgment: uno de RELEVANTE, PARCIAL, IRRELEVANTE.
answers_query: uno de SI, PARCIALMENTE, NO.
evidence_sufficient: uno de SI, NO, NO_APLICA.
confidence: número entre 0 y 1.
review_notes: explicación breve en español, basada solo en el fragmento.
Criterios: RELEVANTE = evidencia directamente relacionada y útil; PARCIAL = relacionada pero incompleta/indirecta; IRRELEVANTE = no aporta evidencia útil. SI = permite contestar la consulta completa con lo que contiene; PARCIALMENTE = responde solo una parte; NO = no la responde. evidence_sufficient SI solo si la evidencia alcanza para fundamentar la respuesta completa; NO si no alcanza; NO_APLICA solo cuando el fragmento claramente no aplica al tipo de consulta."""
VALID = {
    'relevance_judgment': {'RELEVANTE','PARCIAL','IRRELEVANTE'},
    'answers_query': {'SI','PARCIALMENTE','NO'},
    'evidence_sufficient': {'SI','NO','NO_APLICA'},
}

def ollama_eval(url, model, row, timeout):
    user = (f"CONSULTA: {row.get('query','')}\nRUTA: {row.get('predicted_route','')}\n"
            f"FUENTE: {row.get('source','')}\nRANGO: {row.get('rank','')}\n"
            f"FRAGMENTO RECUPERADO:\n{row.get('retrieved_text','')}")
    payload = {'model': model, 'stream': False, 'format': 'json', 'think': False,
               'messages': [{'role':'system','content':SYSTEM}, {'role':'user','content':user}],
               'options': {'temperature': 0}}
    req = urllib.request.Request(url.rstrip('/') + '/api/chat', data=json.dumps(payload).encode('utf-8'),
                                headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    content = data.get('message',{}).get('content','')
    # Tolerar wrappers Markdown de modelos que no respeten format=json.
    content = content.strip()
    if content.startswith('```'):
        content = content.strip('`')
        if content.lower().startswith('json'): content = content[4:].strip()
    result = json.loads(content)
    for key, choices in VALID.items():
        value = str(result.get(key,'')).strip().upper()
        if value not in choices: raise ValueError(f'{key} inválido: {value!r}')
        result[key] = value
    try: result['confidence'] = max(0.0, min(1.0, float(result.get('confidence',0.0))))
    except (TypeError, ValueError): result['confidence'] = 0.0
    result['review_notes'] = str(result.get('review_notes','')).strip()
    return result

def read_csv(path):
    with path.open('r', encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))
def write_csv(path, rows):
    fields = list(rows[0].keys()) if rows else []
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w=csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); w.writeheader(); w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input', type=Path, default=None, help='CSV revision_humana.csv; por defecto busca el más reciente en Tests/results_g1_rag07_*/')
    ap.add_argument('--model', default='qwen3:8b')
    ap.add_argument('--url', default='http://localhost:11434')
    ap.add_argument('--timeout', type=int, default=180)
    ap.add_argument('--limit', type=int, default=0, help='Solo procesar N filas para prueba; 0= todas')
    args=ap.parse_args()
    if args.input:
        src=args.input
    else:
        candidates=sorted(Path('Tests').glob('results_g1_rag07_*/revision_humana.csv'), key=lambda p:p.stat().st_mtime, reverse=True)
        if not candidates: raise SystemExit('ERROR: no encontré revision_humana.csv en Tests/results_g1_rag07_*/')
        src=candidates[0]
    if not src.exists(): raise SystemExit(f'ERROR: no existe el archivo: {src.resolve()}')
    rows=read_csv(src)
    if args.limit>0: rows=rows[:args.limit]
    out=[]; errors=0; start=time.time()
    print(f'Entrada: {src.resolve()}\nModelo: {args.model}\nFilas: {len(rows)}\n')
    for i,row in enumerate(rows,1):
        try:
            ev=ollama_eval(args.url,args.model,row,args.timeout)
            status='REVISAR' if ev['confidence'] < 0.75 or ev['relevance_judgment']=='PARCIAL' or ev['answers_query']=='PARCIALMENTE' else 'VALIDAR'
            err=''
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError, KeyError) as exc:
            errors+=1; ev={'relevance_judgment':'PENDIENTE','answers_query':'PENDIENTE','evidence_sufficient':'PENDIENTE','confidence':0.0,'review_notes':''}
            status='ERROR'; err=f'{type(exc).__name__}: {exc}'
        merged=dict(row)
        merged.update({
            'auto_relevance_judgment':ev['relevance_judgment'],
            'auto_answers_query':ev['answers_query'],
            'auto_evidence_sufficient':ev['evidence_sufficient'],
            'auto_confidence':ev['confidence'],
            'auto_review_notes':ev['review_notes'],
            'human_review_status':status,
            'auto_error':err,
        })
        out.append(merged)
        print(f'[{i}/{len(rows)}] {row.get("case_id", "?")} rank={row.get("rank", "?")}: {status} — {ev["relevance_judgment"]}/{ev["answers_query"]} ({ev["confidence"]:.2f})')
    out_path=src.with_name('revision_automatica.csv')
    write_csv(out_path,out)
    meta={'experiment':'G1-RAG-08B','input':str(src),'model':args.model,'url':args.url,'rows_processed':len(rows),'errors':errors,'elapsed_seconds':round(time.time()-start,2),'output':str(out_path),'warning':'Evaluación automática preliminar; no equivale a revisión humana ni valida por sí sola la respuesta final.'}
    meta_path=src.with_name('evaluacion_automatica_metadatos.json')
    meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'\nCSV: {out_path.resolve()}\nMetadatos: {meta_path.resolve()}\nErrores: {errors}')
    return 0 if errors==0 else 2
if __name__=='__main__': raise SystemExit(main())
