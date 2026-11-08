# GIAR-ORION — Experimentos controlados de paráfrasis

Incluye cuatro grupos ejecutables en una sola carga del modelo:

- P1: equivalencias terminológicas.
- P2: equivalencias funcionales.
- P3: paráfrasis conceptuales.
- P4: relaciones que requieren conocimiento de SAC/RL.

Cada grupo contiene 6 casos SUPPORTED, 1 CONTRADICTED y 1 INSUFFICIENT.
Total: 32 pares. La evidencia se usa como premisa y la afirmación como hipótesis.

## Ejecución

Copiar la carpeta al equipo donde está GIAR-ORION y ejecutar dentro del entorno que ya tiene PyTorch:

```powershell
python .\run_paraphrase_experiments.py
```

Si falta Transformers:

```powershell
pip install transformers
```

El script carga mDeBERTa una sola vez y procesa los 32 pares por lotes. No modifica el verificador ni los umbrales. Genera JSON y CSV con scores y predicción NLI.

## Precauciones

- No usa el holdout independiente de 40 casos.
- No recalibra umbrales.
- No altera EvidenceVerifier ni la configuración de producción.
- Los resultados son exploratorios: las etiquetas gold de cada caso deben revisarse técnicamente antes de usarlos para cualquier decisión de arquitectura.
