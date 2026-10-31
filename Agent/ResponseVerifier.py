"""Verificador de respuestas GIAR-ORION v6.

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
- Máximo 180 palabras. Para cuatro componentes, usa cuatro viñetas y una breve
  descripción de las relaciones, solo si están respaldadas por la evidencia.
- No repitas la pregunta ni agregues encabezados redundantes.
- No añadas conocimiento externo cuando se suministra evidencia RAG.
- No afirmes que el actor se alinea directamente con el objetivo de Bellman ni
  que recibe la pérdida del crítico. El objetivo y la pérdida se usan para
  entrenar al crítico; el actor se orienta por la evaluación que proporciona
  el crítico, solo en la medida en que lo establezca la evidencia.
""".strip()

# Señales de alto riesgo para la relación actor-crítico-Bellman. No son un
# verificador semántico universal; sirven para no declarar validada esta familia
# de errores cuando la formulación es explícita.
SAC_BAD_RELATIONS = [
    (re.compile(r"\b(objetivo de Bellman|target de Bellman)\b.{0,70}\b(no se usa|no se utiliza|no se pasa|no sirve|no es referencia|no constituye referencia)\b.{0,90}\b(pérdida del crítico|pérdida\s+del\s+crítico|loss del crítico)\b", re.I),
     "La respuesta niega incorrectamente que el objetivo de Bellman sea referencia para calcular la pérdida del crítico."),
    (re.compile(r"\bactor\b.{0,100}\b(recibe|toma como entrada|usa como entrada)\b.{0,80}\b(objetivo de Bellman|pérdida del crítico)\b", re.I | re.S),
     "La respuesta atribuye al actor recibir directamente el objetivo de Bellman o la pérdida del crítico."),
    (re.compile(r"\b(objetivo de Bellman|pérdida del crítico)\b.{0,100}\b(actualiza|entrena|optimiza)\b.{0,80}\b(actor|política del actor)\b", re.I | re.S),
     "La respuesta atribuye al objetivo de Bellman o a la pérdida del crítico la actualización directa del actor."),
    (re.compile(r"\bcrítico\b.{0,100}\b(estima|calcula)\b.{0,40}\b(la ventaja|ventaja)\b.{0,60}\b(o|/)\s*(el valor Q|valor Q)\b", re.I | re.S),
     "La respuesta trata valor Q y ventaja como si fueran necesariamente intercambiables."),
    (re.compile(r"\bcrítico\b.{0,100}\b(calcula|construye|genera|determina)\b.{0,50}\b(objetivo de Bellman|target de Bellman)\b", re.I | re.S),
     "La respuesta atribuye al crítico el cálculo del objetivo de Bellman; debe comprobarse quién construye ese objetivo según la evidencia."),
    (re.compile(r"\b(objetivo de Bellman|target de Bellman)\b.{0,80}\b(calculado|construido|generado|determinado)\b.{0,40}\bpor el crítico\b", re.I | re.S),
     "La respuesta atribuye al crítico el cálculo del objetivo de Bellman; debe comprobarse esa relación con la evidencia."),
    (re.compile(r"\b(su pérdida|la pérdida del actor)\b.{0,80}\b(actualiza|entrena|optimiza)\b.{0,50}\b(actor|política del actor)\b", re.I | re.S),
     "La respuesta atribuye una pérdida al actor sin distinguirla explícitamente de la pérdida del crítico."),
    # Relaciones positivas directas o indirectas que aparecieron en las pruebas.
    (re.compile(r"\bactor\b.{0,100}\b(se alinea|está alinead[oa]|se modula|es modulad[oa]|se guía|depende)\b.{0,90}\b(objetivo de Bellman|pérdida del crítico|este objetivo|ese objetivo|él|ello)\b", re.I | re.S),
     "La respuesta vincula directamente al actor con el objetivo de Bellman o la pérdida del crítico, incluso mediante pronombres."),
    (re.compile(r"\b(objetivo de Bellman|pérdida del crítico)\b.{0,160}\bactor\b.{0,70}\b(se alinea|está alinead[oa]|se modula|es modulad[oa]|depende)\b", re.I | re.S),
     "La respuesta afirma que el actor se alinea o depende directamente del objetivo de Bellman o de la pérdida del crítico."),
]


def auditar_relaciones_sac(texto: str, pregunta: str) -> list[str]:
    """Audita relaciones SAC dentro de cada oración para evitar falsos cruces.

    Las reglas son deliberadamente acotadas: detectan algunas relaciones de alto
    riesgo, pero no sustituyen una evaluación semántica ni la evidencia RAG.
    """
    combinado = (pregunta or "") + "\n" + (texto or "")
    if not re.search(r"\b(SAC|actor|crítico|Bellman)\b", combinado, re.I):
        return []

    resultado: list[str] = []
    # No permitir que una expresión relacione sujetos de oraciones distintas.
    oraciones = [x.strip() for x in re.split(r"(?<=[.!?;])\s+|[\r\n]+", texto or "") if x.strip()]
    for oracion in oraciones:
        for patron, mensaje in SAC_BAD_RELATIONS:
            coincidencia = patron.search(oracion)
            if not coincidencia:
                continue
            tramo = coincidencia.group(0).lower()
            # Excluir negaciones explícitas de las relaciones que se prohíben.
            # La regla específica sobre negar el uso del objetivo para la pérdida
            # no se excluye: esa negación es precisamente el error detectado.
            es_regla_negacion_objetivo = mensaje.startswith(
                "La respuesta niega incorrectamente que el objetivo de Bellman"
            )
            if not es_regla_negacion_objetivo:
                negacion = re.search(
                    r"\b(no|nunca|jamás|sin)\b.{0,45}\b(" 
                    r"recibe|recibir|usa|usar|se alinea|está alinead[oa]|"
                    r"se modula|es modulad[oa]|depende|calcula|construye|"
                    r"genera|determina|actualiza|entrena|optimiza)\b",
                    tramo,
                )
                if negacion:
                    continue
            if mensaje not in resultado:
                resultado.append(mensaje)
    return resultado

def _reparar_relaciones(
    *, base_url: str, modelo: str, pregunta: str, respuesta: str,
    evidencia: str, alertas: list[str], system_prompt: str, timeout: int,
) -> tuple[str, dict[str, Any]]:
    """Realiza un único intento de reparación dirigido por alertas deterministas."""
    instrucciones = (
        "Repara la respuesta usando exclusivamente la evidencia suministrada. "
        "Corrige cada alerta relacional, sin explicar el proceso. Distingue con "
        "precisión quién calcula el objetivo de Bellman, quién estima Q, qué "
        "pérdida entrena al crítico y cómo el crítico informa al actor. No afirmes "
        "que el crítico calcula el objetivo de Bellman salvo que la evidencia lo "
        "diga explícitamente. Si una relación no está documentada, omítela o "
        "declara que la evidencia no permite establecerla. Responde en español, "
        "en no más de 160 palabras."
    )
    contenido = (
        "PREGUNTA:\n" + pregunta +
        "\n\nEVIDENCIA:\n" + evidencia +
        "\n\nALERTAS QUE DEBEN CORREGIRSE:\n- " + "\n- ".join(alertas) +
        "\n\nRESPUESTA QUE DEBE REPARARSE:\n" + respuesta
    )
    payload = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": instrucciones},
            {"role": "user", "content": contenido},
        ],
        "stream": False,
        "think": False,
        "options": {"num_predict": 384, "temperature": 0.0, "seed": 42},
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response_http:
            result = json.loads(response_http.read().decode("utf-8"))
        return result.get("message", {}).get("content", ""), {
            "done_reason": result.get("done_reason"),
            "verification_tokens": result.get("eval_count"),
        }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            json.JSONDecodeError, OSError) as error:
        return "", {"done_reason": "error", "error": str(error), "verification_tokens": None}


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
        "options": {"num_predict": 512, "temperature": 0.0, "seed": 42},
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
                "initial_answer_truncated": initial_done_reason == "length",
                "relation_alerts_initial": alertas_iniciales,
            }
        alertas_finales = auditar_relaciones_sac(texto, pregunta)
        tokens_totales = tokens or 0
        # Si el primer verificador conserva una relación problemática, hacer una
        # única reparación dirigida. No repetir indefinidamente ni aceptar una
        # salida parcial como validada.
        if alertas_finales:
            texto_reparacion, diagnostico_reparacion = _reparar_relaciones(
                base_url=base_url,
                modelo=modelo,
                pregunta=pregunta,
                respuesta=texto,
                evidencia=evidencia,
                alertas=alertas_finales,
                system_prompt=system_prompt,
                timeout=timeout,
            )
            tokens_totales += diagnostico_reparacion.get("verification_tokens") or 0
            if diagnostico_reparacion.get("done_reason") != "length" and texto_reparacion.strip():
                alertas_reparacion = auditar_relaciones_sac(texto_reparacion, pregunta)
                if not alertas_reparacion:
                    return texto_reparacion.strip(), {
                        "changed": texto_reparacion.strip() != respuesta_inicial.strip(),
                        "status": "ok_repaired_relation_audit",
                        "verification_tokens": tokens_totales,
                        "done_reason": reason,
                        "repair_done_reason": diagnostico_reparacion.get("done_reason"),
                        "initial_done_reason": initial_done_reason,
                        "relation_alerts_initial": alertas_iniciales,
                        "relation_alerts_final": [],
                        "repair_attempted": True,
                    }
                alertas_finales = alertas_reparacion
            return texto_reparacion.strip() or texto, {
                "changed": (texto_reparacion.strip() or texto) != respuesta_inicial.strip(),
                "status": "failed_relation_audit",
                "error": "Persisten formulaciones relacionales de alto riesgo tras un intento de reparación.",
                "verification_tokens": tokens_totales,
                "done_reason": reason,
                "repair_done_reason": diagnostico_reparacion.get("done_reason"),
                "initial_done_reason": initial_done_reason,
                "relation_alerts_initial": alertas_iniciales,
                "relation_alerts_final": alertas_finales,
                "repair_attempted": True,
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
