# GIAR-ORION — Evaluación integral no destructiva

Incluye 24 consultas de evaluación y 10 casos controlados para probar el verificador. El ejecutor usa la configuración actual del proyecto, el recuperador híbrido E5/BGE-M3 y Ollama; no modifica `config.json`, `main.py` ni el verificador.

## Instalación
Copiar la carpeta `Tests` dentro de la raíz de `GIAR-ORION`, sin reemplazar archivos existentes. Deben quedar `GIAR-ORION/Tests/evaluacion_integral_giar_orion.py`, `casos_evaluacion.json` y `casos_verificador_controlados.json`.

## Ejecución (PowerShell, desde la raíz del proyecto, con `.venv` activado)

```powershell
python .\Tests\evaluacion_integral_giar_orion.py
```
Ejecuta 24 consultas en modo rápido e investigación: 48 generaciones y recuperación. Solo RAG:

```powershell
python .\Tests\evaluacion_integral_giar_orion.py --skip-generation
```
Prueba corta de 3 consultas:

```powershell
python .\Tests\evaluacion_integral_giar_orion.py --limit 3
```

Usa cachés locales (`local_files_only=True`) y crea `Tests/resultados/<fecha_hora>/` con JSON completo, CSV y resumen. Si el constructor del recuperador o las claves de configuración de la instalación difieren, el script muestra el error; no cambia archivos del agente.

## Qué se cuantifica
- Recuperación: hit@k por fuente esperada, cantidad de fragmentos, scores, cobertura de términos de evidencia y latencia.
- Generación: latencia, respuesta vacía, motivo de finalización, truncamiento y coincidencia de abstención.
- El test de abstención es heurístico por expresiones lingüísticas. Hit@k y cobertura de términos tampoco equivalen a corrección semántica.

## Verificador
`casos_verificador_controlados.json` contiene 10 respuestas correctas, incorrectas, incompletas o no sustentadas. Para cuantificar el `ResponseVerifier.py`, ejecutar esos casos mediante la interfaz real del verificador y registrar su decisión. Con positivos = respuestas que deben rechazarse/alertarse: TP = detecta error; FN = acepta error; TN = acepta respuesta correcta; FP = rechaza respuesta correcta. Calcular precisión=TP/(TP+FP), recall=TP/(TP+FN), especificidad=TN/(TN+FP), F1=2PR/(P+R). No se llama automáticamente al verificador porque su API no se debe adivinar ni alterar.
