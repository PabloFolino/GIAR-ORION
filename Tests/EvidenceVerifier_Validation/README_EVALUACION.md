# Validación integral EvidenceVerifier 0.2.1

## Alcance
120 casos sintéticos en siete grupos. Se miden por separado:
- NLI aislado: scores de entailment, neutral y contradiction por par.
- EvidenceVerifier completo: clasificación con umbrales, filtro lexical de roles y agregación.

## Distribución
- A_SUPPORT: 20
- B_CONTRADICTION: 20
- C_NEUTRAL: 15
- D_PARAPHRASE: 20
- E_ROLE_DISTINCTION: 15
- F_MULTI_EVIDENCE: 15
- G_ROBUSTNESS: 15

## Instalación
Copiar `EvidenceVerifier_Validation` dentro de `Tests/` del proyecto GIAR-ORION.
El script espera `Agent/EvidenceVerifier.py` en la raíz del proyecto.

## Ejecución (PowerShell)
```powershell
python Tests/EvidenceVerifier_Validation/test_evidence_verifier_validacion_integral.py
```
Opcional: `--device cuda` o `--verifier "ruta\EvidenceVerifier.py"`.

## Salidas
- `resultados_nli.json`: scores de cada par evidencia-afirmación.
- `resultados_verifier.json`: decisión y comparaciones por caso.
- `informe_final.json`: matriz de confusión, precisión/recall, métricas por grupo y discrepancias.

## Criterio
No establecer un porcentaje arbitrario de aprobación antes de observar resultados. Examinar matriz de confusión, precisión/recall por clase, errores por grupo y scores de las discrepancias.

## Limitaciones
El conjunto es sintético y sus etiquetas son hipótesis gold curadas, no una verdad científica ni un benchmark externo. La prueba no evalúa ClaimExtractor, DDGS real ni integración de interfaz. Los resultados son reproducibles para una versión fija de modelo, tokenizer y dependencias.
