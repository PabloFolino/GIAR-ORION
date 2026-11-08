import json, csv, time, argparse
from collections import defaultdict
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_DEFAULT = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
LABEL_MAP = {"entailment":"SUPPORTED","contradiction":"CONTRADICTED","neutral":"INSUFFICIENT"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default="GIAR_ORION_NLI_test_controlado.json")
    ap.add_argument("--output",default="GIAR_ORION_NLI_test_resultados")
    ap.add_argument("--model",default=MODEL_DEFAULT)
    args=ap.parse_args()

    with open(args.input,encoding="utf-8") as f:
        data=json.load(f)
    device="cuda" if torch.cuda.is_available() else "cpu"
    tok=AutoTokenizer.from_pretrained(args.model)
    model=AutoModelForSequenceClassification.from_pretrained(args.model).to(device)
    model.eval()

    # Resolve label indices from the model configuration, avoiding assumed order.
    id2label={int(k):str(v).lower() for k,v in model.config.id2label.items()}
    label_ids={}
    for idx,name in id2label.items():
        for key in LABEL_MAP:
            if key in name:
                label_ids[key]=idx
    if set(label_ids)!=set(LABEL_MAP):
        raise RuntimeError(f"No se pudieron resolver las etiquetas NLI: {id2label}")

    results=[]
    start=time.time()
    for item in data["cases"]:
        inputs=tok(item["claim"],item["evidence"],return_tensors="pt",
                   truncation=True,max_length=512).to(device)
        with torch.no_grad():
            logits=model(**inputs).logits[0]
            probs=torch.softmax(logits,dim=-1).cpu().tolist()
        scores={k:float(probs[v]) for k,v in label_ids.items()}
        pred=max(scores,key=scores.get)
        results.append({**item,"predicted_nli":pred,"predicted":LABEL_MAP[pred],
                        "correct":LABEL_MAP[pred]==item["gold"],
                        "scores":scores})

    elapsed=time.time()-start
    grouped=defaultdict(list)
    for r in results:
        grouped[r["factor"]].append(r)
    summary={}
    for factor,items in grouped.items():
        summary[factor]={
            "n":len(items),
            "correct":sum(x["correct"] for x in items),
            "accuracy":sum(x["correct"] for x in items)/len(items),
            "confusion":{}
        }
        for gold in LABEL_MAP.values():
            subset=[x for x in items if x["gold"]==gold]
            if subset:
                summary[factor]["confusion"][gold]={
                    pred:sum(x["predicted"]==pred for x in subset)
                    for pred in LABEL_MAP.values()
                }

    output={"model":args.model,"device":device,"elapsed_seconds":elapsed,
            "n_cases":len(results),"summary":summary,"results":results}
    with open(args.output+".json","w",encoding="utf-8") as f:
        json.dump(output,f,ensure_ascii=False,indent=2)
    with open(args.output+".csv","w",encoding="utf-8-sig",newline="") as f:
        fields=["id","case_id","factor","level","language","gold","predicted",
                "correct","entailment","neutral","contradiction","claim","evidence"]
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow({**r,**r["scores"]})
    print(f"Casos: {len(results)} | dispositivo: {device} | tiempo: {elapsed:.2f}s")
    print("\\nAccuracy por factor:")
    for factor,s in summary.items():
        print(f"  {factor:22s} {s['correct']:2d}/{s['n']:2d} = {s['accuracy']:.1%}")
    print(f"\\nArchivos: {args.output}.json y {args.output}.csv")

if __name__=="__main__":
    main()
