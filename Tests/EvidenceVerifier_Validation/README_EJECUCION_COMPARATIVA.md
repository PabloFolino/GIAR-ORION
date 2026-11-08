# Campaña comparativa EvidenceVerifier 0.2.1 vs 0.2.2

## Objetivo
Comparar el verificador de referencia 0.2.1 con la copia experimental 0.2.2, usando exactamente los mismos 120 casos, afirmaciones y evidencias.

## Instalación
Copiar estos tres archivos dentro de:

`GIAR-ORION/Tests/EvidenceVerifier_Validation/`

- `EvidenceVerifier_0_2_1_reference.py`
- `EvidenceVerifier_0_2_2_experimental.py`
- `run_comparacion_0_2_1_vs_0_2_2.py`

No reemplazar `Agent/EvidenceVerifier.py`, `main_multilinea.py` ni `ClaimVerificationPipeline.py`.
El dataset `dataset_120_casos.json` ya debe estar en ese directorio.

## Requisitos previos
1. Activar el entorno virtual `.venv`.
2. Tener instalados `torch` y `transformers` (ya utilizados en la campaña anterior).
3. Tener Ollama iniciado.
4. Confirmar `qwen3:8b` con `ollama list`.

## Ejecución
Desde la raíz del proyecto `GIAR-ORION`, ejecutar:

```powershell
python Tests/EvidenceVerifier_Validation/run_comparacion_0_2_1_vs_0_2_2.py
```

No ejecutar desde dentro de `Tests` y no ejecutar el módulo `EvidenceVerifier` directamente.

## Archivos generados
Se crea `Tests/EvidenceVerifier_Validation/comparacion_0_2_1_vs_0_2_2/` con:

- `informe_comparativo.json`: métricas globales, por grupo, matriz de confusión, diferencias y conteo de normalizaciones.
- `comparacion_por_caso.csv`: comparación directa de cada uno de los 120 casos.
- `resultados_0_2_1_detallados.json`: scores y predicciones de la versión 0.2.1.
- `resultados_0_2_2_detallados.json`: scores, predicciones y textos originales/normalizados de la 0.2.2.

## Metodología
- Se usa `gold_verifier` como etiqueta de referencia (fallback: `gold_nli`).
- El separador `||` divide evidencias múltiples en fragmentos independientes.
- Se conservan los umbrales 0.80 / 0.80 y margen 0.15.
- Las versiones se ejecutan secuencialmente para evitar cargar dos modelos NLI en GPU al mismo tiempo.
- La normalización solo está activada en 0.2.2.

## Importante
La ejecución 0.2.2 puede tardar considerablemente porque Qwen normaliza cada afirmación y cada evidencia antes del NLI. La latencia de 0.2.2 incluye Ollama; no debe compararse directamente con la latencia de 0.2.1 como si ambas hicieran el mismo trabajo.

No se modifica ningún módulo productivo. El benchmark es sintético y sus etiquetas deben interpretarse con cautela. Antes de considerar una mejora real, hay que auditar las traducciones/normalizaciones, especialmente negaciones, cuantificadores, cantidades y relaciones entre Actor, Critic y Replay Buffer.
