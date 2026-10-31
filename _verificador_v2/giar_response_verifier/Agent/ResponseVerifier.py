"""Verificación predeterminada de calidad conceptual para GIAR-ORION.

La verificación usa una segunda llamada al mismo modelo local. No es una prueba
formal de verdad: es una revisión guiada por evidencia y criterios explícitos.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


VERIFIER_INSTRUCTIONS = """
Actuás como revisor de calidad conceptual de una respuesta técnica.
Tu tarea es entregar una versión final corregida, no describir tu proceso de revisión.

AUDITORÍA OBLIGATORIA DE RELACIONES (NO OMITIR):
Antes de redactar la respuesta final, contrasta cada relación importante de la
respuesta con la evidencia. Revisa expresamente sujeto, acción, objeto, fuente de
información y finalidad. Detecta relaciones invertidas, atribución de una función
al componente equivocado y conceptos que aparecen juntos pero cuya relación no
está documentada. No basta con que la respuesta suene coherente.

Ejemplo de criterio: si la evidencia dice que un objetivo es referencia para
entrenar al crítico y que el crítico proporciona estimaciones al actor, no afirmes
que el actor recibe como entrada el objetivo ni la pérdida del crítico, salvo que
la evidencia lo diga explícitamente.

OBJETIVOS OBLIGATORIOS:
1. COMPLETITUD: conservar todos los elementos esenciales de la respuesta y de la
   evidencia que sean necesarios para responder la pregunta.
2. RELACIONES: preservar quién hace qué, sobre qué componente, con qué información,
   bajo qué condición y con qué finalidad, cuando la información lo establezca.
3. DISTINCIÓN DE FUNCIONES: no atribuir a un componente la función de otro.
4. FIDELIDAD: no inventar mecanismos, relaciones causales, garantías ni detalles.
5. COHERENCIA: resolver contradicciones y eliminar repeticiones que no aporten.
6. CLARIDAD: explicar el mecanismo de forma completa y directa, sin reducirlo a una
   lista de definiciones desconectadas.

Cuando se proporciona evidencia documental, esta limita las afirmaciones sobre lo
que dice la documentación. No conviertas conceptos co-ocurrentes en una relación
causal si la evidencia no la establece. Si falta información para explicar una parte
necesaria, indicalo de manera concreta en la respuesta final.

Cuando no se proporciona evidencia documental, revisa completitud estructural,
coherencia y relaciones internas, pero no afirmes que verificaste los hechos contra
fuentes que no recibiste.

La respuesta inicial puede estar truncada. Si se informa que la generación terminó
por límite de tokens, reconstruye una respuesta completa y autocontenida a partir
de la evidencia; no continúes desde una frase cortada ni conserves un final roto.
Si la evidencia no permite completar un punto, dilo expresamente. No inventes.

Devuelve ÚNICAMENTE la respuesta final revisada. No incluyas puntuaciones, notas al
revisor, etiquetas de auditoría ni explicaciones sobre los cambios.
""".strip()


def verificar_y_corregir_respuesta(
    *,
    base_url: str,
    modelo: str,
    pregunta: str,
    respuesta_inicial: str,
    contexto_evidencia: str,
    system_prompt: str,
    parametros: dict[str, Any],
    respuesta_truncada: bool = False,
    timeout: int = 300,
) -> tuple[str, dict[str, Any]]:
    """Revisa una respuesta y devuelve (respuesta_final, métricas del verificador).

    Si la llamada de verificación falla, conserva la respuesta inicial para que un
    fallo secundario no impida usar el agente; el error queda registrado.
    """
    evidencia = contexto_evidencia.strip() or (
        "No se proporcionó contexto RAG para esta consulta. No afirmes que una frase "
        "está respaldada por documentación recuperada."
    )
    contenido_usuario = (
        "PREGUNTA ORIGINAL:\n" + pregunta.strip() + "\n\n"
        "EVIDENCIA DISPONIBLE:\n" + evidencia + "\n\n"
        "RESPUESTA INICIAL QUE DEBES REVISAR:\n" + respuesta_inicial.strip() + "\n\n"
        "ESTADO DE GENERACIÓN: " + ("TRUNCADA: Ollama terminó por límite de tokens. Debes reconstruir una respuesta completa." if respuesta_truncada else "Ollama no informó truncamiento por límite de tokens.") + "\n\n"
        "Revisa la respuesta inicial según los criterios. Conserva lo correcto, corrige "
        "confusiones entre funciones, recupera relaciones o elementos esenciales "
        "omitidos cuando estén respaldados y elimina afirmaciones no justificadas. "
        "No amplíes la respuesta con conocimiento externo si se proporcionó evidencia. "
        "Entrega solamente la respuesta final."
    )
    payload = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": VERIFIER_INSTRUCTIONS},
            {"role": "user", "content": contenido_usuario},
        ],
        "stream": False,
        "think": parametros.get("think", False),
        "options": {
            # La verificación debe ser breve: audita y corrige, no repite un ensayo.
            "num_predict": min(max(parametros.get("num_predict", 512), 512), 768),
            "temperature": 0.0,
            "seed": 42,
        },
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
        message = result.get("message", {})
        texto = message.get("content", "")
        if not isinstance(texto, str) or not texto.strip():
            return respuesta_inicial, {
                "changed": False,
                "status": "fallback_empty_response",
                "input_truncated": respuesta_truncada,
                "verification_complete": False,
                "error": "El verificador devolvió contenido vacío.",
                "verification_tokens": result.get("eval_count"),
            }
        texto = texto.strip()
        return texto, {
            "changed": texto != respuesta_inicial.strip(),
            "status": "reviewed_truncated_input" if respuesta_truncada else "ok",
            "input_truncated": respuesta_truncada,
            "verification_complete": not (result.get("done_reason") == "length"),
            "verification_tokens": result.get("eval_count"),
            "done_reason": result.get("done_reason"),
            "prompt_tokens": result.get("prompt_eval_count"),
        }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError) as error:
        return respuesta_inicial, {
            "changed": False,
            "status": "fallback_initial_answer",
            "input_truncated": respuesta_truncada,
            "verification_complete": False,
            "error": f"Falló la verificación: {type(error).__name__}: {error}",
            "verification_tokens": None,
        }
