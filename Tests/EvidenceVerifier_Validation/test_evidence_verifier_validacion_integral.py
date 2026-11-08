from __future__ import annotations
import json, sys, time, argparse, importlib.util
from pathlib import Path
from collections import defaultdict
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def load_class(path):
    spec=importlib.util.spec_from_file_location("EvidenceVerifier_tested",path)
    mod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=mod
    spec.loader.exec_module(mod); return mod.EvidenceVerifier
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verifier",default=str(ROOT/"Agent"/"EvidenceVerifier.py"))
    p.add_argument("--device",default=None)
    p.add_argument("--batch-size",type=int,default=8)
    a=p.parse_args()
    data=json.loads((HERE/"dataset_120_casos.json").read_text(encoding="utf-8"))
    EV=load_class(Path(a.verifier)); v=EV(device=a.device); v._load_nli_model()
    import torch
    pairs=[]
    for c in data["cases"]:
        for j,e in enumerate(c["evidence"].split(" || ")):
            pairs.append((c,j,e.strip()))
    raw=[]; t0=time.perf_counter()
    for k in range(0,len(pairs),a.batch_size):
        b=pairs[k:k+a.batch_size]
        enc=v._tokenizer([x[2] for x in b],[x[0]["claim"] for x in b],
          padding=True,truncation=True,max_length=512,return_tensors="pt")
        enc={x:y.to(v.device) for x,y in enc.items()}
        with torch.inference_mode(): probs=torch.softmax(v._nli_model(**enc).logits,dim=-1).cpu().tolist()
        for (c,j,e),s in zip(b,probs):
            ix=v._label_indices
            raw.append({"id":c["id"],"group":c["group"],"pair_index":j,"claim":c["claim"],
             "evidence":e,"gold":c["gold_nli"],"scores":{
             "entailment":float(s[ix["entailment"]]),"neutral":float(s[ix["neutral"]]),
             "contradiction":float(s[ix["contradiction"]])}})
    nli_seconds=time.perf_counter()-t0
    full=[]
    for c in data["cases"]:
        evs=[x.strip() for x in c["evidence"].split(" || ")]
        rag=[{"source":f'{c["id"]}_RAG_{i+1}',"text":e,"score":1.0,"mode":"validation"} for i,e in enumerate(evs)]
        t=time.perf_counter()
        out=v.verify_claims([c["claim"]],rag_results=rag,web_results=[])
        item=out["claims"][0]
        full.append({"id":c["id"],"group":c["group"],"claim":c["claim"],
          "gold":c["gold_verifier"],"predicted":item["status"],
          "best_entailment_score":item.get("best_entailment_score"),
          "best_contradiction_score":item.get("best_contradiction_score"),
          "elapsed_seconds":time.perf_counter()-t,"comparisons":item["comparisons"]})
    def metrics(rows):
        labels=["SUPPORTED","CONTRADICTED","INSUFFICIENT"]
        cm={g:{p:0 for p in labels} for g in labels}
        for x in rows:
            if x["gold"] in cm and x["predicted"] in cm[x["gold"]]: cm[x["gold"]][x["predicted"]]+=1
        n=len(rows); correct=sum(cm[z][z] for z in labels); per={}
        for z in labels:
            tp=cm[z][z]; fp=sum(cm[g][z] for g in labels if g!=z); fn=sum(cm[z][q] for q in labels if q!=z)
            per[z]={"precision":tp/(tp+fp) if tp+fp else None,"recall":tp/(tp+fn) if tp+fn else None,"support":sum(cm[z].values())}
        return {"accuracy":correct/n if n else None,"correct":correct,"total":n,"confusion_matrix_gold_rows_pred_columns":cm,"per_class":per}
    groups=defaultdict(list)
    for x in full: groups[x["group"]].append(x)
    (HERE/"resultados_nli.json").write_text(json.dumps({"model":v.nli_model_name,"device":v.device,"elapsed_seconds":nli_seconds,"pairs":raw},ensure_ascii=False,indent=2),encoding="utf-8")
    (HERE/"resultados_verifier.json").write_text(json.dumps(full,ensure_ascii=False,indent=2),encoding="utf-8")
    report={"dataset":data["dataset"],"cases":len(full),"nli_pairs":len(raw),"model":v.nli_model_name,"device":v.device,
      "thresholds":{"entailment":v.entailment_threshold,"contradiction":v.contradiction_threshold,"decision_margin":v.decision_margin},
      "nli_elapsed_seconds":nli_seconds,"verifier_metrics":metrics(full),
      "group_metrics":{g:metrics(rs) for g,rs in sorted(groups.items())},
      "mismatches":[{k:x[k] for k in ("id","group","gold","predicted","claim","best_entailment_score","best_contradiction_score")} for x in full if x["gold"]!=x["predicted"]],
      "limitations":["Dataset sintético; no es benchmark externo.","Scores NLI no son probabilidades calibradas.","La evaluación no incluye ClaimExtractor ni la interfaz completa.","El verificador recibe evidencias RAG sintéticas; no se evalúa aquí DDGS ni el límite mixto RAG/DDGS."]}
    (HERE/"informe_final.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"cases":len(full),"nli_pairs":len(raw),"accuracy":report["verifier_metrics"]["accuracy"],"mismatches":len(report["mismatches"])},ensure_ascii=False,indent=2))
if __name__=="__main__": main()
