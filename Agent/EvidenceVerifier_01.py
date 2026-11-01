"""
EvidenceVerifier.py
===================

Módulo independiente de verificación de evidencias para GIAR-ORION.

Versión: 0.1

Alcance de esta primera versión
-------------------------------
1. Recibe los resultados RAG con el formato actual:
   {"source": str, "text": str, "score": float, "mode": str}
2. Recibe los resultados DDGS con el formato actual:
   {"title": str, "url": str, "description": str, "source": str}
3. Comprueba si las URLs y las rutas de fuentes mencionadas en la respuesta
   aparecen en las evidencias recibidas.
4. Detecta URLs duplicadas dentro de las evidencias.
5. Devuelve un informe estructurado.

Limitación deliberada
---------------------
Esta versión NO determina si el contenido de una evidencia demuestra
semánticamente una afirmación. Tampoco descarga páginas web ni consulta
modelos externos. Por lo tanto, una referencia coincidente no equivale a
una afirmación científicamente verificada.

El módulo no modifica RAG, DDGS, Ollama ni la interfaz de GIAR-ORION.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any
from urllib.parse import urlsplit, urlunsplit


class EvidenceVerifierError(ValueError):
    """Error en los datos recibidos por el verificador."""


class EvidenceVerifier:
    """Realiza controles deterministas sobre referencias y evidencias."""

    VERSION = "0.1"

    # Se capturan URLs HTTP(S) escritas en la respuesta.
    URL_PATTERN = re.compile(r"https?://[^\s<>\]\[\"'()]+", re.IGNORECASE)

    def __init__(self) -> None:
        pass

    @staticmethod
    def _normalizar_url(url: str) -> str:
        """
        Normaliza una URL para comparar referencias.
        Conserva ruta, consulta y fragmento; normaliza esquema/host.
        No intenta resolver redirecciones ni equivalencias entre URLs.
        """
        try:
            parsed = urlsplit(url.strip().rstrip(".,;:!?"))
            if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
                return ""

            host = parsed.hostname.lower().rstrip(".")
            port = parsed.port
            netloc = host
            if port is not None and not (
                (parsed.scheme.lower() == "http" and port == 80)
                or (parsed.scheme.lower() == "https" and port == 443)
            ):
                netloc = f"{host}:{port}"

            path = parsed.path or "/"
            return urlunsplit(
                (parsed.scheme.lower(), netloc, path, parsed.query, parsed.fragment)
            )
        except (TypeError, ValueError):
            return ""

    @staticmethod
    def _validar_lista(nombre: str, elementos: Any) -> list[dict[str, Any]]:
        if elementos is None:
            return []
        if not isinstance(elementos, list):
            raise EvidenceVerifierError(f"'{nombre}' debe ser una lista.")

        salida: list[dict[str, Any]] = []
        for indice, item in enumerate(elementos):
            if not isinstance(item, dict):
                raise EvidenceVerifierError(
                    f"El elemento {indice} de '{nombre}' debe ser un diccionario."
                )
            salida.append(item)
        return salida

    @staticmethod
    def _extraer_urls(texto: str) -> list[str]:
        return [
            coincidencia.rstrip(".,;:!?")
            for coincidencia in EvidenceVerifier.URL_PATTERN.findall(texto)
        ]

    def verify(
        self,
        response: str,
        rag_results: list[dict[str, Any]] | None = None,
        web_results: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Verifica la correspondencia de referencias explícitas de la respuesta.

        Parámetros:
            response: texto generado por el LLM.
            rag_results: resultados originales de retriever.search().
            web_results: resultados originales de WebSearch.

        Devuelve un informe JSON-serializable.
        """
        if not isinstance(response, str):
            raise EvidenceVerifierError("'response' debe ser un texto.")

        rag = self._validar_lista("rag_results", rag_results)
        web = self._validar_lista("web_results", web_results)

        # Recolectar rutas locales realmente entregadas por el RAG.
        rag_sources: list[str] = []
        for indice, item in enumerate(rag):
            source = item.get("source")
            text = item.get("text")
            if not isinstance(source, str) or not source.strip():
                raise EvidenceVerifierError(
                    f"rag_results[{indice}] no contiene un 'source' válido."
                )
            if not isinstance(text, str):
                raise EvidenceVerifierError(
                    f"rag_results[{indice}] no contiene un 'text' válido."
                )
            rag_sources.append(source.strip())

        # Recolectar URLs web realmente entregadas por DDGS.
        web_records: list[dict[str, str]] = []
        for indice, item in enumerate(web):
            title = item.get("title")
            url = item.get("url")
            description = item.get("description")
            source = item.get("source")

            if not isinstance(url, str) or not self._normalizar_url(url):
                raise EvidenceVerifierError(
                    f"web_results[{indice}] no contiene una URL HTTP(S) válida."
                )
            if not isinstance(title, str):
                raise EvidenceVerifierError(
                    f"web_results[{indice}] no contiene un 'title' válido."
                )
            if not isinstance(description, str):
                raise EvidenceVerifierError(
                    f"web_results[{indice}] no contiene una 'description' válida."
                )
            if not isinstance(source, str):
                raise EvidenceVerifierError(
                    f"web_results[{indice}] no contiene un 'source' válido."
                )

            web_records.append(
                {
                    "title": title,
                    "url": url,
                    "normalized_url": self._normalizar_url(url),
                    "description": description,
                    "source": source,
                }
            )

        # Detección de URLs duplicadas en el conjunto recuperado.
        url_counts = Counter(record["normalized_url"] for record in web_records)
        duplicate_urls = sorted(
            url for url, count in url_counts.items() if count > 1
        )

        # Comparación de URLs explícitas en la respuesta contra DDGS.
        response_urls = self._extraer_urls(response)
        normalized_available_urls = {
            record["normalized_url"] for record in web_records
        }

        matched_urls: list[str] = []
        unmatched_urls: list[str] = []
        seen_response_urls: set[str] = set()

        for url in response_urls:
            normalized = self._normalizar_url(url)
            if not normalized:
                unmatched_urls.append(url)
                continue
            if normalized in seen_response_urls:
                continue
            seen_response_urls.add(normalized)

            if normalized in normalized_available_urls:
                matched_urls.append(url)
            else:
                unmatched_urls.append(url)

        # Detectar menciones literales de rutas RAG recuperadas y no recuperadas.
        matched_rag_sources = [
            source for source in dict.fromkeys(rag_sources) if source in response
        ]

        # No se puede inferir con seguridad que una cadena parecida a una ruta
        # sea una cita. Solo se informa la coincidencia literal de fuentes RAG.
        report = {
            "verifier": "EvidenceVerifier",
            "version": self.VERSION,
            "checks": {
                "web_url_reference_check": {
                    "status": (
                        "PASS" if not unmatched_urls else "UNVERIFIED"
                    ),
                    "urls_found_in_response": response_urls,
                    "urls_matched_to_search_results": matched_urls,
                    "urls_not_found_in_search_results": unmatched_urls,
                },
                "rag_source_reference_check": {
                    "status": (
                        "PASS"
                        if not rag_sources or matched_rag_sources
                        else "NOT_CITED"
                    ),
                    "retrieved_sources": list(dict.fromkeys(rag_sources)),
                    "sources_mentioned_literally": matched_rag_sources,
                },
                "duplicate_web_reference_check": {
                    "status": "WARNING" if duplicate_urls else "PASS",
                    "duplicate_urls": duplicate_urls,
                },
                "semantic_support_check": {
                    "status": "NOT_PERFORMED",
                    "reason": (
                        "La versión 0.1 no evalúa si el contenido de las evidencias "
                        "respalda semánticamente las afirmaciones."
                    ),
                },
            },
            "evidence_counts": {
                "rag_fragments": len(rag),
                "rag_unique_sources": len(set(rag_sources)),
                "web_results": len(web_records),
                "web_unique_urls": len(normalized_available_urls),
            },
            "overall_status": self._overall_status(
                unmatched_urls=unmatched_urls,
                duplicate_urls=duplicate_urls,
                rag_sources=rag_sources,
                matched_rag_sources=matched_rag_sources,
            ),
            "limitations": [
                "La coincidencia de una URL solo confirma que fue recuperada por DDGS.",
                "DDGS aporta título, URL y fragmento; este módulo no descarga la página.",
                "La coincidencia de una ruta RAG no demuestra que respalde la afirmación.",
                "No se realiza verificación semántica ni comprobación científica.",
                "La ausencia de una cita no demuestra por sí sola que una afirmación sea falsa.",
            ],
        }
        return report

    @staticmethod
    def _overall_status(
        unmatched_urls: list[str],
        duplicate_urls: list[str],
        rag_sources: list[str],
        matched_rag_sources: list[str],
    ) -> str:
        if unmatched_urls:
            return "UNVERIFIED_REFERENCES"
        if duplicate_urls:
            return "WARNING_DUPLICATE_REFERENCES"
        if rag_sources and not matched_rag_sources:
            return "RAG_SOURCES_NOT_CITED"
        return "REFERENCE_CHECKS_PASSED"


def verify_response(
    response: str,
    rag_results: list[dict[str, Any]] | None = None,
    web_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Función de conveniencia para ejecutar una verificación."""
    return EvidenceVerifier().verify(
        response=response,
        rag_results=rag_results,
        web_results=web_results,
    )


if __name__ == "__main__":
    # Prueba autocontenida con datos sintéticos.
    # No consulta Internet, Ollama ni la base documental real.
    rag_demo = [
        {
            "source": "Fundamentos_de_SAC_GIAR_ORION.md",
            "text": "SAC es un algoritmo de aprendizaje por refuerzo off-policy.",
            "score": 0.82,
            "mode": "hybrid",
        }
    ]

    web_demo = [
        {
            "title": "Soft Actor-Critic",
            "url": "https://spinningup.openai.com/en/latest/algorithms/sac.html",
            "description": "Documentación de referencia sobre Soft Actor-Critic.",
            "source": "spinningup.openai.com",
        }
    ]

    response_demo = (
        "Según Fundamentos_de_SAC_GIAR_ORION.md, SAC es off-policy. "
        "Referencia: https://spinningup.openai.com/en/latest/algorithms/sac.html"
    )

    resultado = verify_response(
        response=response_demo,
        rag_results=rag_demo,
        web_results=web_demo,
    )

    import json

    print(json.dumps(resultado, ensure_ascii=False, indent=2))
