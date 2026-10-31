"""Evaluación de abstenciones para GIAR-ORION: clasificador heurístico de tres estados."""
from __future__ import annotations
import re
from typing import Any

ABSTENTION_PATTERNS = [
 r"\bno hay información suficiente\b", r"\bno (?:se )?(?:puede|es posible) determinar\b",
 r"\bno (?:se )?(?:menciona|indica|especifica|proporciona|incluye|dispone)\b", r"\bno especifica\b", r"\bno permite establecer\b",
 r"\bno cuento con (?:la )?información\b", r"\bla evidencia (?:proporcionada|disponible|recuperada) no\b",
 r"\bno está (?:especificado|documentado|confirmado)\b", r"\bno puedo confirmar\b", r"\bno puedo afirmar\b",
 r"\bno es posible confirmar\b", r"\bno se puede confirmar\b", r"\bno hay datos suficientes\b",
 r"\bno figura en (?:la )?documentación\b", r"\bno se dispone de datos\b",
]
CONTINUATION = [r"\bsin embargo\b", r"\bno obstante\b", r"\bpero\b", r"\baunque\b", r"\bpor ejemplo\b", r"\bse puede inferir\b", r"\bcabe inferir\b", r"\bprobablemente\b", r"\bpodría ser\b", r"\bcomo valor estándar\b", r"\bgeneralmente\b", r"\bpor lo general\b", r"\ben términos generales\b", r"\bla respuesta es\b", r"\bse recomienda\b", r"\bdebe\b", r"\bsí explica\b", r"\ben sac\b", r"\bpara evaluarla\b", r";\s*(?:sí|el|la|los|las|gamma|alpha|tau|en|para)\b"]
CONCRETE = [r"\b(?:es|son|cumple|consiste|representa|permite|calcula|utiliza|combina)\b", r"\b(?:actor|crítico|política|recompensa|estado|acción|gamma|alpha|tau)\b", r"\b\d+(?:[.,]\d+)?\b", r"```", r"\$\$?", r"^\s*\d+[\.)]\s+"]
CLOSURE = [r"\bpor lo tanto\b.{0,100}\bno hay información suficiente\b", r"\bpor tanto\b.{0,100}\bno (?:se puede|es posible) determinar\b", r"\bno se proporciona\b.{0,100}\bvalor\b", r"\bno se menciona\b.{0,100}\b(?:ningún|ningun|un) valor\b", r"\bno puedo confirmar\b", r"\bno hay datos suficientes\b"]

def classify_abstention(answer: str) -> dict[str, Any]:
    if not isinstance(answer, str) or not answer.strip():
        return {"status":"abstention","is_abstention":True,"confidence":1.0,"reason":"empty_answer","signals":[]}
    text = re.sub(r"\s+", " ", answer.lower()).strip()
    abst = [p for p in ABSTENTION_PATTERNS if re.search(p,text,re.I)]
    if not abst:
        return {"status":"answer","is_abstention":False,"confidence":0.85,"reason":"no_abstention_cue","signals":[]}
    continuation = [p for p in CONTINUATION if re.search(p,text,re.I)]
    concrete = [p for p in CONCRETE if re.search(p,text,re.I)]
    closure = any(re.search(p,text,re.I) for p in CLOSURE)
    # Un conector que introduce una respuesta general/inferencia tras la cautela
    # indica respuesta mixta. La mera presencia de términos técnicos o números no basta.
    if continuation:
        return {"status":"partial","is_abstention":False,"confidence":0.70,"reason":"uncertainty_plus_substantive_content","signals":abst+continuation}
    # Si la frase de incertidumbre es el único acto comunicativo, clasificar como abstención,
    # aunque mencione el parámetro solicitado (p. ej. gamma o episodios).
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if closure or len(sentences) <= 2:
        return {"status":"abstention","is_abstention":True,"confidence":0.85 if closure else 0.70,"reason":"explicit_lack_of_evidence_without_answer","signals":abst}
    if len(text.split()) < 45 and not concrete:
        return {"status":"abstention","is_abstention":True,"confidence":0.65,"reason":"short_uncertainty_only","signals":abst}
    return {"status":"partial","is_abstention":False,"confidence":0.55,"reason":"ambiguous_uncertainty","signals":abst}

def evaluate_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    tp=tn=fp=fn=partial=0; rows=[]
    for rec in records:
        expected=bool(rec["expected_abstention"]); answer=rec.get("answer",""); result=classify_abstention(answer); pred=result["is_abstention"]
        if result["status"]=="partial": partial+=1
        if expected and pred: tp+=1
        elif not expected and not pred: tn+=1
        elif not expected and pred: fp+=1
        else: fn+=1
        rows.append({"case_id":rec.get("case_id"),"expected_abstention":expected,"predicted_status":result["status"],"predicted_abstention":pred,"match":expected==pred,"reason":result["reason"],"answer":answer})
    n=len(rows); precision=tp/(tp+fp) if tp+fp else 0.; recall=tp/(tp+fn) if tp+fn else 0.; specificity=tn/(tn+fp) if tn+fp else 0.; f1=2*precision*recall/(precision+recall) if precision+recall else 0.
    return {"n":n,"TP":tp,"TN":tn,"FP":fp,"FN":fn,"partial":partial,"accuracy":(tp+tn)/n if n else 0.,"precision":precision,"recall":recall,"specificity":specificity,"f1":f1,"rows":rows}
