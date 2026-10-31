import json
from pathlib import Path
from abstention_eval_v3 import evaluate
HERE=Path(__file__).resolve().parent
for src,dst in [('casos_controlados_40_v3.json','resultado_controlados_v3.json'),('casos_reales_48_v3.json','resultado_reales_48_v3.json')]:
 records=json.loads((HERE/src).read_text(encoding='utf-8')); result=evaluate(records); (HERE/dst).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print('\n===',src,'==='); print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False,indent=2)); bad=[r for r in result['rows'] if r['match'] is False]; print('Desacuerdos:',len(bad)); [print('-',r.get('case_id'),r.get('status'),r.get('reason'),(r.get('query') or '')[:100]) for r in bad]
print('Resultados detallados guardados en esta carpeta.')
