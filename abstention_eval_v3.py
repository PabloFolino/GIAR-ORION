"""Evaluador heurístico v3: pregunta + respuesta; abstención separada de suficiencia."""
import re
ABSTENTION_PATTERNS=[r'\bno hay información suficiente\b',r'\bno (?:se )?(?:puede|es posible) determinar\b',r'\bno (?:se )?(?:menciona|indica|especifica|proporciona|incluye|dispone)\b',r'\bno especifica\b',r'\bno permite establecer\b',r'\bla evidencia (?:proporcionada|disponible|recuperada) no\b',r'\bno está (?:especificado|documentado|confirmado)\b',r'\bno puedo confirmar\b',r'\bno puedo afirmar\b',r'\bno es posible confirmar\b',r'\bno se puede confirmar\b',r'\bno hay datos suficientes\b',r'\bno figura en (?:la )?documentación\b',r'\bno se dispone de datos\b',r'\bno puedo determinar\b',r'\bno se puede verificar\b']
EXACT_REQUEST=[r'\bvalor exacto\b',r'\bvalor configurado\b',r'\bvalor activo\b',r'\bqué valor\b',r'\bcuánto\b',r'\bcuántos\b',r'\bcuál es la cifra\b']
PROJECT_SCOPE=[r'\b(?:en el proyecto|actual|real|última ejecución|configuración efectiva|archivo cargado|desplegada)\b']
CONCEPT=[r'\b(?:es|representa|controla|pondera|regula|permite|se utiliza|consiste en)\b',r'\b(?:factor de descuento|término de entropía|política|actor|crítico|recompensa|valor futuro)\b']
VALUE=[r'\b(?:gamma|alpha|tau|learning rate|tasa de aprendizaje|recompensa media|episodios|latencia|umbral)\b.{0,70}\b(?:es|=|de|fue|sería)\s*[-+]?\d+(?:[.,]\d+)?',r'\b[-+]?\d+(?:[.,]\d+)?\s*(?:episodios|ms|milisegundos|segundos)\b']
def hits(patterns,text): return [p for p in patterns if re.search(p,text,re.I|re.S)]
def classify(query,answer):
 q=(query or '').lower(); a=re.sub(r'\s+',' ',(answer or '').strip()); al=a.lower()
 if not a: return dict(status='abstention',abstention_detected=True,sufficiency='insufficient',reason='empty_answer',confidence='high',signals=[])
 abst=hits(ABSTENTION_PATTERNS,al); exact=bool(hits(EXACT_REQUEST,q)); project=bool(hits(PROJECT_SCOPE,q)); concept=hits(CONCEPT,al); value=hits(VALUE,al)
 if exact and abst and not value:
  return dict(status='partial' if concept else 'abstention',abstention_detected=True,sufficiency='insufficient',reason='requested_exact_value_not_provided',confidence='medium',signals=abst+concept)
 if abst:
  if concept and len(a.split())>12: return dict(status='partial',abstention_detected=True,sufficiency='query_dependent_review',reason='uncertainty_plus_context',confidence='medium',signals=abst+concept)
  return dict(status='abstention',abstention_detected=True,sufficiency='insufficient',reason='explicit_lack_of_evidence',confidence='medium',signals=abst)
 if project and value: return dict(status='answer',abstention_detected=False,sufficiency='grounding_review_required',reason='specific_claim_requires_evidence_check',confidence='low',signals=value)
 return dict(status='answer',abstention_detected=False,sufficiency='not_assessed_by_heuristic',reason='no_explicit_abstention_cue',confidence='medium',signals=[])
def evaluate(records):
 rows=[]; tp=tn=fp=fn=partial=0
 for r in records:
  z=classify(r.get('query',''),r.get('answer','')); expected=r.get('expected_abstention'); pred=z['abstention_detected']; match=None if expected is None else bool(expected)==pred
  if expected is not None:
   if expected and pred: tp+=1
   elif not expected and not pred: tn+=1
   elif not expected and pred: fp+=1
   else: fn+=1
  partial+=z['status']=='partial'; rows.append({**{k:r.get(k) for k in ('case_id','mode','category','query','expected_abstention')},**z,'match':match,'answer':r.get('answer','')})
 n=sum(r.get('expected_abstention') is not None for r in rows); precision=tp/(tp+fp) if tp+fp else 0.; recall=tp/(tp+fn) if tp+fn else 0.; specificity=tn/(tn+fp) if tn+fp else 0.; f1=2*precision*recall/(precision+recall) if precision+recall else 0.
 return dict(n=len(rows),n_with_labels=n,TP=tp,TN=tn,FP=fp,FN=fn,partial=partial,accuracy=(tp+tn)/n if n else None,precision=precision,recall=recall,specificity=specificity,f1=f1,sufficiency_warning='La suficiencia y la fundamentación no quedan validadas por esta clasificación heurística.',rows=rows)
