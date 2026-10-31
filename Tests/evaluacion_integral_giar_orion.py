# -*- coding: utf-8 -*-
"""Evaluación integral no destructiva de GIAR-ORION."""
from __future__ import annotations
import argparse, csv, json, re, sys, time, urllib.request
from pathlib import Path
from datetime import datetime
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CASES = Path(__file__).with_name('casos_evaluacion.json')
OUT = Path(__file__).with_name('resultados')
ABSTAIN = re.compile(r'\b(no se puede|no puedo|no hay|no existe|no encuentro|no está documentad[oa]|no está especificad[oa]|la evidencia no|información insuficiente|no se indica|no se especifica|no cuento con)\b', re.I)
SYSTEM = '''Sos GIAR-ORION, asistente técnico especializado en robótica y aprendizaje por refuerzo. Respondé en español salvo que la consulta esté en inglés. Usá exclusivamente la evidencia suministrada. No inventes valores ni detalles. Si falta evidencia suficiente, decilo expresamente. Diferenciá hechos documentados de inferencias.'''
def readj(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def call_ollama(base, model, messages, params):
    payload={'model':model,'messages':messages,'stream':False,'think':params.get('think',False),'options':{'num_predict':int(params.get('num_predict',1024)),'temperature':0.0,'seed':42}}
    req=urllib.request.Request(base.rstrip('/')+'/api/chat',data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'},method='POST')
    t=time.perf_counter()
    with urllib.request.urlopen(req,timeout=300) as resp: d=json.loads(resp.read().decode())
    m=d.get('message',{})
    return {'answer':m.get('content',''),'elapsed_s':round(time.perf_counter()-t,3),'done_reason':d.get('done_reason'),'eval_count':d.get('eval_count'),'prompt_eval_count':d.get('prompt_eval_count'),'total_duration_ns':d.get('total_duration')}
def norm(x): return re.sub(r'\s+',' ',str(x or '')).casefold()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--modes',default='rapido,investigacion')
    ap.add_argument('--limit',type=int,default=0)
    ap.add_argument('--skip-generation',action='store_true')
    args=ap.parse_args()
    cfg=readj(ROOT/'config.json'); rag=cfg['rag']; llm=cfg['llm']; modes=cfg['generation']['modes']
    selected=[x.strip() for x in args.modes.split(',') if x.strip()]
    for m in selected:
        if m not in modes: raise ValueError(f'Modo inexistente en config.json: {m}')
    cases=readj(CASES); cases=cases[:args.limit] if args.limit else cases
    from Agent.MultilingualKnowledgeRetriever import MultilingualKnowledgeRetriever
    print('Inicializando recuperador con parámetros del proyecto...')
    start=time.perf_counter()
    retriever=MultilingualKnowledgeRetriever(knowledge_dir=ROOT/'Knowledge',mode=rag.get('mode','hybrid'),e5_weight=rag.get('e5_weight',.7),bge_weight=rag.get('bge_weight',.3),cache_dir=ROOT/'Cache',local_files_only=True)
    init_s=round(time.perf_counter()-start,3)
    print(f'Recuperador listo: {init_s}s | fragmentos={len(retriever.chunks)} | consultas={len(cases)}')
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S'); out=OUT/stamp; out.mkdir(parents=True,exist_ok=True); records=[]
    total=len(cases)*(1 if args.skip_generation else len(selected)); count=0
    for c in cases:
        try:
            t=time.perf_counter(); frags=retriever.search(c['query'],top_k=int(rag.get('top_k',5))); rt=round(time.perf_counter()-t,3)
            sources=[str(f.get('source','')) for f in frags]; body=norm(' '.join(sources+[str(f.get('text','')) for f in frags]))
            expected=c.get('expected_source_any',[]); hit=(True if not expected else any(any(x.casefold() in s.casefold() for x in expected) for s in sources))
            terms=c.get('must_terms',[]); coverage=(sum(norm(x) in body for x in terms)/len(terms)) if terms else None
            prompt='CONSULTA:\n'+c['query']+'\n\nEVIDENCIA RECUPERADA:\n'
            for i,f in enumerate(frags,1): prompt+=f"\n--- FRAGMENTO {i} | fuente={f.get('source','')} | score={f.get('score','')} ---\n{f.get('text','')}\n"
            prompt+='\nRespondé exclusivamente con base en la evidencia. Si falta información, señalalo.'
            base={'case_id':c['id'],'category':c['category'],'query':c['query'],'retrieval_seconds':rt,'retrieved_count':len(frags),'expected_source_hit_at_k':hit,'retrieved_sources':sources,'retrieved_scores':[f.get('score') for f in frags],'evidence_term_coverage':coverage,'retrieved_fragments':frags}
            if args.skip_generation:
                records.append(base); count+=1; print(f"[{count}/{total}] {c['id']} RAG_hit={hit} k={len(frags)} {rt}s"); continue
            for mode in selected:
                count+=1
                try:
                    g=call_ollama(llm['base_url'],llm['model'],[{'role':'system','content':SYSTEM},{'role':'user','content':prompt}],modes[mode]); abst=bool(ABSTAIN.search(g['answer'])); expected_abst=bool(c.get('expect_abstention'))
                    row={**base,'mode':mode,**g,'expected_abstention':expected_abst,'detected_abstention':abst,'abstention_match':abst==expected_abst,'nonempty_answer':bool(g['answer'].strip()),'truncated':g.get('done_reason')=='length'}; records.append(row)
                    print(f"[{count}/{total}] {c['id']} {mode}: {g['elapsed_s']}s finish={g['done_reason']} source_hit={hit} abstention_match={row['abstention_match']}")
                except Exception as e: records.append({**base,'mode':mode,'error':f'{type(e).__name__}: {e}'}); print(f'ERROR {c["id"]}/{mode}: {e}')
        except Exception as e: records.append({'case_id':c['id'],'category':c['category'],'query':c['query'],'error':f'{type(e).__name__}: {e}'}); print(f'ERROR RAG {c["id"]}: {e}')
    (out/'resultados_completos.json').write_text(json.dumps({'timestamp':stamp,'root':str(ROOT),'config_snapshot':{'rag':rag,'llm':llm,'modes':{m:modes[m] for m in selected}},'retriever_init_seconds':init_s,'case_count':len(cases),'records':records},ensure_ascii=False,indent=2),encoding='utf-8')
    flat=[]
    for r in records: flat.append({k:(json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v) for k,v in r.items() if k!='retrieved_fragments'})
    keys=sorted({k for r in flat for k in r})
    with (out/'resultados.csv').open('w',encoding='utf-8-sig',newline='') as f: w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(flat)
    ok=[r for r in records if not r.get('error')]; gens=[r for r in ok if 'mode' in r]
    pct=lambda xs: round(100*sum(bool(x) for x in xs)/len(xs),1) if xs else None
    times=[r['elapsed_s'] for r in gens if isinstance(r.get('elapsed_s'),(int,float))]
    summary={'queries':len(cases),'records':len(records),'successful_records':len(ok),'retrieval_expected_source_hit_at_k_pct':pct([r.get('expected_source_hit_at_k') for r in ok]),'mean_retrieval_seconds':round(sum(r['retrieval_seconds'] for r in ok)/len(ok),3) if ok else None,'mean_retrieved_chunks':round(sum(r['retrieved_count'] for r in ok)/len(ok),2) if ok else None,'generation_records':len(gens),'nonempty_answer_pct':pct([r.get('nonempty_answer') for r in gens]),'abstention_match_pct':pct([r.get('abstention_match') for r in gens]),'truncations':sum(bool(r.get('truncated')) for r in gens),'mean_generation_seconds':round(sum(times)/len(times),3) if times else None,'verifier':'No invocado: requiere adaptar llamadas a la interfaz exacta de Agent/ResponseVerifier.py. Usar casos_verificador_controlados.json y registrar TP/TN/FP/FN.'}
    (out/'resumen.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print('\nRESUMEN\n'+json.dumps(summary,ensure_ascii=False,indent=2)+f'\nResultados guardados en: {out}')
    print('Nota: métricas automáticas de fuente/términos/abstención son indicadores de cribado, no una puntuación semántica de verdad.')
if __name__=='__main__': main()
