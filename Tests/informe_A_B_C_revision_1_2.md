# Recalculo A/B/C — EvidenceVerifier — Dataset de calibración 1.2

## Alcance y método

- Dataset: revisión 1.2, 80 casos.
- Scores: `resultados_nli(1).json`; 135 pares totales, 80 IDs de calibración seleccionados y 95 pares utilizados.
- Se reutilizaron los scores existentes; **no se ejecutó inferencia NLI**.
- Se aplicó agregación por caso con máximo entailment y máximo contradiction, conforme a EvidenceVerifier 0.2.1.
- Umbral de contradicción: 0,80; margen: 0,15.
- A: entailment 0,80, sin filtro de roles.
- B: entailment 0,70, sin filtro de roles.
- C: entailment 0,80, con filtro de roles de EvidenceVerifier.
- El holdout de 40 casos no se leyó ni se utilizó.

## Resultados globales

| Variante | Configuración | Aciertos | Accuracy | Precisión SUPPORTED | Recall SUPPORTED | FP SUPPORTED | Precisión CONTRADICTED |
|---|---|---:|---:|---:|---:|---:|---:|
| A | E=0.80; filtro roles=no | 56/80 | 70.00% | 100.0% | 57.6% | 0 | 60.7% |
| B | E=0.70; filtro roles=no | 57/80 | 71.25% | 100.0% | 60.6% | 0 | 60.7% |
| C | E=0.80; filtro roles=sí | 58/80 | 72.50% | 100.0% | 57.6% | 0 | 66.7% |

## Matrices de confusión

Orden de filas = etiqueta real; orden de columnas = predicción. Orden: SUPPORTED, CONTRADICTED, INSUFFICIENT, CONFLICTING_EVIDENCE.
### Variante A

```text
19 2 11 1
0 17 1 0
0 9 20 0
0 0 0 0
```

### Variante B

```text
20 2 10 1
0 17 1 0
0 9 20 0
0 0 0 0
```

### Variante C

```text
19 2 11 1
0 16 2 0
0 6 23 0
0 0 0 0
```

## Accuracy por grupo

| Grupo | A | B | C |
|---|---:|---:|---:|
| A_SUPPORT | 12/13 (92.3%) | 12/13 (92.3%) | 12/13 (92.3%) |
| B_CONTRADICTION | 11/13 (84.6%) | 11/13 (84.6%) | 11/13 (84.6%) |
| C_NEUTRAL | 10/10 (100.0%) | 10/10 (100.0%) | 10/10 (100.0%) |
| D_PARAPHRASE | 4/13 (30.8%) | 4/13 (30.8%) | 4/13 (30.8%) |
| E_ROLE_DISTINCTION | 5/10 (50.0%) | 5/10 (50.0%) | 8/10 (80.0%) |
| F_MULTI_EVIDENCE | 8/10 (80.0%) | 8/10 (80.0%) | 8/10 (80.0%) |
| G_ROBUSTNESS | 6/11 (54.5%) | 7/11 (63.6%) | 5/11 (45.5%) |

## Interpretación

- A: 56/80 (70,0%). No produjo falsos positivos SUPPORTED; su precisión SUPPORTED fue 100%, con recall 57,6%.
- B: 57/80 (71,25%). Solo cambia EV-110 de INSUFFICIENT a SUPPORTED; mantiene 0 falsos positivos SUPPORTED y precisión SUPPORTED de 100%.
- C: 58/80 (72,5%). El filtro de roles reduce falsos positivos CONTRADICTED de 11 a 8 y mejora la clasificación de varios casos E_ROLE_DISTINCTION; también cambia EV-114 de CONTRADICTED a INSUFFICIENT.
- C no es mejor en todos los grupos: en G_ROBUSTNESS baja a 5/11 (45,5%), principalmente por el tratamiento de EV-114.
- Las tres variantes mantienen 0 falsos positivos SUPPORTED en estos 80 casos; por tanto, bajar E de 0,80 a 0,70 no perjudica esa métrica en este conjunto, aunque solo añade un acierto.
- Las correcciones de etiquetas 1.2 no cambian la accuracy global frente a las etiquetas previas reconstruidas: EV-036 y EV-058/059 cambian en dirección desfavorable para las predicciones existentes, mientras EV-063 cambia en dirección favorable. Sí cambian la interpretación por clase.

## Decisión provisional

C obtiene la mayor accuracy (72,5%) y mejora la precisión de CONTRADICTED al reducir falsos positivos de contradicción. B añade un acierto frente a A sin generar falsos positivos SUPPORTED. Ninguna configuración debe pasar a producción todavía: el dataset es pequeño, las etiquetas fueron revisadas manualmente y la evaluación es solo de calibración. Congelar una candidata antes de abrir el holdout.

## Archivos de entrada

- `dataset_calibracion_80_revision_1_2_reconstruida.json`
- `resultados_nli(1).json`
