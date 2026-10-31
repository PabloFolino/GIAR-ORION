"""Verificador de respuestas GIAR-ORION v3.

La verificación usa el mismo LLM que genera la respuesta: sirve como control
adicional, no como garantía formal. El resultado se marca incompleto si Ollama
indica que el verificador alcanzó su límite de tokens.
"""
from __future__ import annotations
import json
import re
import urllib.error
import urllib.request
from typing import Any

VERIFIER_INSTRUCTIONS = """
Actuás como auditor técnico de una respuesta basada en evidencia documental.
Tu prioridad es detectar y corregir relaciones conceptuales incorrectas, no
reformular por estilo una respuesta que ya está bien.

AUDITORÍA OBLIGATORIA ANTES DE REDACTAR:
1. Para cada relación importante, identifica origen, destino y tipo de relación.
2. Comprueba que la evidencia respalde esa dirección; que dos términos aparezcan
   juntos no demuestra que uno sea entrada, causa, objetivo o salida del otro.
3. Distingue función, dato de entrada, resultado, referencia de entrenamiento y
   función de pérdida. No los intercambies.
4. Si se habla de SAC, comprueba específicamente que el objetivo de Bellman es
   una referencia para calcular la pérdida del crítico; la pérdida actualiza al
   crítico. No afirmes que el actor recibe directamente el objetivo de Bellman o
   la pérdida del crítico salvo que la evidencia lo diga expresamente. Distingue
   la evaluación de acciones que aporta el crítico al actor de la pérdida usada
   para entrenar al crítico.
5. No equipares automáticamente valor Q y ventaja. Usa la denominación exacta
   que sostenga la evidencia.
6. Elimina afirmaciones sobre temperatura, entropía u otros mecanismos si no son
   necesarios para la pregunta o no están respaldados por el contexto entregado.
7. Si la evidencia no permite determinar una relación, dilo explícitamente.

SALIDA:
- Devuelve solo la respuesta final, sin notas sobre tu proceso.
- Sé conciso pero completo. Para una pregunta sobre cuatro componentes, apunta a
  4-6 párrafos breves o viñetas y a no más de unas 400 palabras.
- No repitas la pregunta ni agregues encabezados redundantes.
- No añadas conocimiento externo cuando se suministra evidencia RAG.
""".strip()

# Señales de alto riesgo para la relación actor-crítico-Bellman. No son un
# verificador semántico universal; sirven para no declarar validada esta familia
# de errores cuando la formulación es explícita.
SAC_BAD_RELATIONS = [
    (re.compile(r"\bactor\b.{0,100}\b(recibe|toma como entrada|usa como entrada)\b.{0,80}\b(objetivo de Bellman|pérdida del crítico)\b", re.I | re.S),
     "La respuesta atribuye al actor recibir directamente el objetivo de Bellman o la pérdida del crítico."),
    (re.compile(r"\b(objetivo de Bellman|pérdida del crítico)\b.{0,100}\b(actualiza|entrena|optimiza)\b.{0,80}\b(actor|política del actor)\b", re.I | re.S),
     "La respuesta atribuye al objetivo de Bellman o a la pérdida del crítico la actualización directa del actor."),
    (re.compile(r"\bcrítico\b.{0,100}\b(estima|calcula)\b.{0,40}\b(la ventaja|ventaja)\b.{0,60}\b(o|/)\s*(el valor Q|valor Q)\b", re.I | re.S),
     "La respuesta trata valor Q y ventaja como si fueran necesariamente intercambiables."),
]

def auditar_relaciones_sac(texto: str, pregunta: str) -> list[str]:
    """Detecta algunas formulaciones SAC explícitamente problemáticas."""
    combinado = (pregunta or "") + "\n" + (texto or "")
    if not re.search(r"\b(SAC|actor|crítico|Bellman)\b", combinado, re.I):
        return []
    return [mensaje for patron, mensaje in SAC_BAD_RELATIONS if patron.search(texto or "")]

def verificar_y_corregir_respuesta(
    *, base_url: str, modelo: str, pregunta: str, respuesta_inicial: str,
    contexto_evidencia: str, system_prompt: str, parametros: dict[str, Any],
    timeout: int = 300, initial_done_reason: str | None = None,
) -> tuple[str, dict[str, Any]]:
    evidencia = contexto_evidencia.strip() or (
        "No se proporcionó contexto RAG. No afirmes que una frase está respaldada "
        "por documentación recuperada."
    )
    alertas_iniciales = auditar_relaciones_sac(respuesta_inicial, pregunta)
    aviso_truncamiento = (
        "IMPORTANTE: la generación inicial terminó con done_reason=length; la "
        "respuesta inicial puede estar incompleta. Reconstruye una respuesta "
        "completa y concisa desde la evidencia, sin continuar una frase truncada.\n\n"
        if initial_done_reason == "length" else ""
    )
    alertas = ""
    if alertas_iniciales:
        alertas = "ALERTAS DE RELACIÓN DETECTADAS EN LA RESPUESTA INICIAL:\n- " + "\n- ".join(alertas_iniciales) + "\nCorrige obligatoriamente esas relaciones si la evidencia no las respalda.\n\n"
    contenido_usuario = (
        aviso_truncamiento + alertas +
        "PREGUNTA ORIGINAL:\n" + pregunta.strip() +
        "\n\nEVIDENCIA DOCUMENTAL DISPONIBLE:\n" + evidencia +
        "\n\nRESPUESTA INICIAL:\n" + respuesta_inicial.strip() +
        "\n\nAudita las relaciones y funciones contra la evidencia. Corrige errores, "
        "elimina afirmaciones no respaldadas y conserva lo correcto. Entrega una "
        "respuesta final completa y concisa, sin notas de auditoría."
    )
    payload = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": VERIFIER_INSTRUCTIONS},
            {"role": "user", "content": contenido_usuario},
        ],
        "stream": False,
        "think": False,
        "options": {"num_predict": 640, "temperature": 0.0, "seed": 42},
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
        message = result.get("message", {})
        texto = message.get("content", "")
        reason = result.get("done_reason")
        tokens = result.get("eval_count")
        if not isinstance(texto, str) or not texto.strip():
            return respuesta_inicial, {
                "changed": False, "status": "incomplete_empty_response",
                "error": "El verificador devolvió contenido vacío.",
                "verification_tokens": tokens, "done_reason": reason,
                "initial_done_reason": initial_done_reason,
                "relation_alerts_initial": alertas_iniciales,
            }
        texto = texto.strip()
        # Nunca se acepta una salida del verificador cortada como respuesta final.
        if reason == "length":
            return respuesta_inicial, {
                "changed": False, "status": "incomplete_verifier_limit",
                "error": "El verificador alcanzó el límite de tokens; su salida parcial fue descartada.",
                "verification_tokens": tokens, "done_reason": reason,
                "initial_done_reason": initial_done_reason,
                "relation_alerts_initial": alertas_iniciales,
            }
        alertas_finales = auditar_relaciones_sac(texto, pregunta)
        if alertas_finales:
            return texto, {
                "changed": texto != respuesta_inicial.strip(),
                "status": "failed_relation_audit",
                "error": "Persisten formulaciones relacionales de alto riesgo.",
                "verification_tokens": tokens, "done_reason": reason,
                "initial_done_reason": initial_done_reason,
                "relation_alerts_initial": alertas_iniciales,
                "relation_alerts_final": alertas_finales,
            }
        return texto, {
            "changed": texto != respuesta_inicial.strip(),
            "status": "ok_unverified_formally",
            "verification_tokens": tokens, "done_reason": reason,
            "initial_done_reason": initial_done_reason,
            "relation_alerts_initial": alertas_iniciales,
            "relation_alerts_final": [],
        }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            json.JSONDecodeError, OSError) as error:
        return respuesta_inicial, {
            "changed": False, "status": "fallback_initial_answer",
            "error": f"Falló la verificación: {type(error).__name__}: {error}",
            "verification_tokens": None, "initial_done_reason": initial_done_reason,
            "relation_alerts_initial": alertas_iniciales,
        }
