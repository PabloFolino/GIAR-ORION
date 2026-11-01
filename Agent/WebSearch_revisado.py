"""
GIAR-ORION - Búsqueda externa mediante DDGS.

Dependencia:
    python -m pip install -U ddgs

Este módulo devuelve resultados del buscador (título, URL y fragmento).
No descarga el contenido completo de las páginas ni utiliza Ollama.

Ante fallos de conexión, reintenta la consulta y prueba otros motores DDGS.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


class WebSearchError(RuntimeError):
    """Error controlado durante una búsqueda web."""


class WebSearch:
    """Búsqueda web libre o restringida a dominios autorizados."""

    def __init__(
        self,
        safesearch: str = "moderate",
        region: str = "wt-wt",
        retries: int = 1,
        backends: tuple[str, ...] = ("auto", "bing", "brave", "duckduckgo"),
    ):
        self.safesearch = safesearch
        self.region = region

        if isinstance(retries, bool) or not isinstance(retries, int) or retries < 0:
            raise ValueError("retries debe ser un entero mayor o igual que cero.")
        if not backends or not all(isinstance(b, str) and b.strip() for b in backends):
            raise ValueError("Debe indicarse al menos un backend válido.")

        # retries=1 significa un intento inicial y un reintento por motor.
        self.retries = retries
        self.backends = tuple(dict.fromkeys(b.strip().lower() for b in backends))
        try:
            from ddgs import DDGS
        except ImportError as error:
            raise WebSearchError(
                "DDGS no está instalado. Ejecutá: "
                "python -m pip install -U ddgs"
            ) from error
        self._ddgs_class = DDGS

    @staticmethod
    def _normalizar_dominio(dominio: str) -> str:
        dominio = dominio.strip().lower()
        if not dominio:
            raise ValueError("La lista contiene un dominio vacío.")
        if "://" in dominio:
            dominio = urlparse(dominio).hostname or ""
        dominio = dominio.rstrip(".")
        if not dominio or "/" in dominio or "@" in dominio:
            raise ValueError(f"Dominio no válido: {dominio!r}")
        return dominio

    @staticmethod
    def _dominio_de_url(url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return ""
        return parsed.hostname.lower().rstrip(".")

    @staticmethod
    def _pertenece_al_dominio(host: str, dominio: str) -> bool:
        return host == dominio or host.endswith("." + dominio)

    @staticmethod
    def _normalizar_resultado(
        resultado: dict[str, Any],
    ) -> dict[str, str] | None:
        titulo = str(resultado.get("title") or "").strip()
        url = str(resultado.get("href") or resultado.get("url") or "").strip()
        descripcion = str(
            resultado.get("body") or resultado.get("description") or ""
        ).strip()
        dominio = WebSearch._dominio_de_url(url)
        if not url or not dominio:
            return None
        return {
            "title": titulo or "Sin título",
            "url": url,
            "description": descripcion,
            "source": dominio,
        }

    def _buscar(self, consulta: str, max_results: int) -> list[dict[str, str]]:
        if not isinstance(consulta, str) or not consulta.strip():
            raise ValueError("La consulta de búsqueda no puede estar vacía.")
        if isinstance(max_results, bool) or not isinstance(max_results, int):
            raise ValueError("max_results debe ser un entero.")
        if not 1 <= max_results <= 20:
            raise ValueError("max_results debe estar entre 1 y 20.")

        errores: list[str] = []
        hubo_respuesta = False

        # Ante un fallo se reintenta el motor actual y luego se prueba otro.
        # Materializamos los resultados dentro del contexto para capturar
        # también errores que aparezcan al consumir el generador.
        for backend in self.backends:
            for intento in range(self.retries + 1):
                try:
                    with self._ddgs_class() as ddgs:
                        resultados = list(
                            ddgs.text(
                                consulta.strip(),
                                region=self.region,
                                safesearch=self.safesearch,
                                max_results=max_results,
                                backend=backend,
                            ) or []
                        )

                    hubo_respuesta = True
                    if not resultados:
                        break

                    salida: list[dict[str, str]] = []
                    vistos: set[str] = set()
                    for resultado in resultados:
                        item = self._normalizar_resultado(resultado)
                        if item is None:
                            continue
                        clave = item["url"].rstrip("/").lower()
                        if clave not in vistos:
                            vistos.add(clave)
                            salida.append(item)

                    if salida:
                        return salida
                    break

                except TypeError as error:
                    # Compatibilidad con versiones de ddgs sin parámetro backend.
                    if "backend" not in str(error).lower():
                        errores.append(f"{backend}: {error}")
                        break
                    try:
                        with self._ddgs_class() as ddgs:
                            resultados = list(
                                ddgs.text(
                                    consulta.strip(),
                                    region=self.region,
                                    safesearch=self.safesearch,
                                    max_results=max_results,
                                ) or []
                            )
                        hubo_respuesta = True
                        salida = []
                        vistos = set()
                        for resultado in resultados:
                            item = self._normalizar_resultado(resultado)
                            if item is None:
                                continue
                            clave = item["url"].rstrip("/").lower()
                            if clave not in vistos:
                                vistos.add(clave)
                                salida.append(item)
                        if salida:
                            return salida
                        break
                    except Exception as compat_error:
                        errores.append(f"{backend} (compatibilidad): {compat_error}")
                        break

                except Exception as error:
                    errores.append(
                        f"{backend}, intento {intento + 1}/{self.retries + 1}: {error}"
                    )

        if hubo_respuesta:
            return []

        detalle = " | ".join(errores[-4:]) or "No hubo respuesta de los motores."
        raise WebSearchError(
            "No se pudo completar la búsqueda DDGS después de probar "
            f"los motores configurados. Detalles: {detalle}"
        )

    def search_web(
        self, query: str, max_results: int = 5
    ) -> list[dict[str, str]]:
        """Realiza una búsqueda libre en Internet."""
        return self._buscar(query, max_results)

    def search_authorized(
        self,
        query: str,
        authorized_domains: list[str],
        max_results: int = 5,
    ) -> list[dict[str, str]]:
        """
        Busca dentro de dominios autorizados.

        Se agrega site:dominio a la consulta y se valida cada URL recibida.
        La validación local impide devolver resultados de dominios ajenos,
        incluso si el motor no respeta el operador site:.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("La consulta de búsqueda no puede estar vacía.")
        if not authorized_domains:
            raise ValueError("Debe indicarse al menos un dominio autorizado.")
        if isinstance(max_results, bool) or not isinstance(max_results, int):
            raise ValueError("max_results debe ser un entero.")
        if not 1 <= max_results <= 20:
            raise ValueError("max_results debe estar entre 1 y 20.")

        dominios = list(dict.fromkeys(
            self._normalizar_dominio(d) for d in authorized_domains
        ))
        resultados_finales: list[dict[str, str]] = []
        vistos: set[str] = set()
        por_dominio = max(
            1, (max_results + len(dominios) - 1) // len(dominios)
        )

        for dominio in dominios:
            consulta_restringida = f"site:{dominio} {query.strip()}"
            for item in self._buscar(consulta_restringida, por_dominio):
                host = self._dominio_de_url(item["url"])
                if not any(
                    self._pertenece_al_dominio(host, permitido)
                    for permitido in dominios
                ):
                    continue
                clave = item["url"].rstrip("/").lower()
                if clave in vistos:
                    continue
                vistos.add(clave)
                resultados_finales.append(item)
                if len(resultados_finales) >= max_results:
                    return resultados_finales

        return resultados_finales


if __name__ == "__main__":
    # Prueba independiente: python WebSearch.py
    buscador = WebSearch()
    consulta = "Soft Actor Critic reinforcement learning"

    print("PRUEBA 1 - Búsqueda libre")
    for resultado in buscador.search_web(consulta, max_results=3):
        print(
            f"\n{resultado['title']}\n{resultado['url']}"
            f"\n{resultado['description']}"
        )

    print("\nPRUEBA 2 - Dominios autorizados")
    for resultado in buscador.search_authorized(
        consulta,
        authorized_domains=["arxiv.org", "openai.com"],
        max_results=3,
    ):
        print(
            f"\n{resultado['title']}\n{resultado['url']}"
            f"\n{resultado['description']}"
        )
