import json
from pathlib import Path
from abstention_eval_v2 import evaluate_records
root=Path(__file__).resolve().parent
records=json.loads((root/'casos_abstencion_controlados_v2.json').read_text(encoding='utf-8'))
result=evaluate_records(records)
(root/'Tests'/'Abstention').mkdir(parents=True, exist_ok=True)
(root/'Tests'/'Abstention'/'resultado_prueba_abstenciones_v2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False,indent=2))
print('Detalle:',root/'Tests'/'Abstention'/'resultado_prueba_abstenciones_v2.json')

