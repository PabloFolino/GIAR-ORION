# EvidenceVerifier 0.2.2 experimental

## Propósito

Copia experimental de `EvidenceVerifier.py` 0.2.1. Agrega una etapa de normalización lingüística a inglés mediante Ollama (`qwen3:8b`) antes de ejecutar el mismo modelo NLI.

## No reemplazar el módulo productivo

- No sobrescribir `Agent/EvidenceVerifier.py`.
- No modificar `main_multilinea.py` ni `ClaimVerificationPipeline.py`.
- Ubicar esta copia en `Tests/EvidenceVerifier_Validation/`.
- La versión 0.2.1 permanece como referencia de control.

## Requisitos

- Ollama activo en `http://localhost:11434`.
- Modelo `qwen3:8b` disponible localmente.
- Dependencias ya utilizadas por el verificador: `torch` y `transformers`.
- El modelo NLI actual debe estar disponible localmente o descargarse según la configuración de Hugging Face.

## Uso desde un script de evaluación

```python
from EvidenceVerifier_0_2_2_experimental import EvidenceVerifier

verifier = EvidenceVerifier(
    nli_model_name="MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7",
    entailment_threshold=0.80,
    contradiction_threshold=0.80,
    decision_margin=0.15,
    normalize_cross_language=True,
    ollama_url="http://localhost:11434",
    normalization_model="qwen3:8b",
)

report = verifier.verify_claims(
    claims=["El Critic estima valores Q."],
    rag_results=[{
        "source": "ejemplo",
        "text": "The critic estimates state-action values."
    }],
)
```

Ejecutar desde la carpeta que contiene este archivo o agregar esa carpeta a `sys.path`.

## Comportamiento

1. Cada afirmación y cada evidencia se normaliza a inglés mediante Ollama.
2. Los textos originales y normalizados quedan registrados en `comparisons[].normalization`.
3. Se conserva una caché por texto durante cada llamada a `verify_claims` para no traducir repetidamente una misma cadena.
4. Si Ollama falla o devuelve una salida inválida, se usa el texto original para esa cadena. El informe registra `success=false` y el motivo en la caché interna; el contador `fallback` queda en el resumen.
5. El NLI, sus umbrales, margen, filtro de roles y agregación se mantienen sin cambios funcionales.

## Limitaciones y precauciones

- Esta etapa normaliza todos los textos a inglés; no realiza detección explícita de idioma.
- Qwen puede alterar negaciones, modalidad, cantidades o relaciones técnicas. Por eso se deben inspeccionar los textos normalizados antes de considerar válida una clasificación.
- La normalización agrega latencia: se realiza una solicitud local a Ollama por cada texto único de entrada.
- Si Ollama no está disponible, el verificador continúa con los textos originales. En ese caso no se ha probado realmente la modificación lingüística.
- La salida no es compatible para certificación científica: sigue siendo una estimación NLI.
- La versión experimental no debe conectarse todavía a GIAR-ORION.

## Comparación experimental

Usar el mismo dataset de 120 casos y comparar la versión 0.2.1 contra esta versión, sin cambiar umbrales ni reglas. Registrar exactitud global y por grupo, falsos respaldos, falsas contradicciones, recupero de `SUPPORTED`, fallbacks de Ollama y tiempo total. Revisar especialmente todos los textos normalizados de los casos que cambien de clasificación.
