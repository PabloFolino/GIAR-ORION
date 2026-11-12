"""GIAR-ORION - Búsqueda externa mediante DDGS.

Dependencia: python -m pip install -U ddgs

Devuelve título, URL y fragmento; no descarga páginas ni utiliza Ollama.
Prueba los motores configurados en orden, con reintentos por motor, y termina
cuando dos motores distintos aportaron resultados válidos.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen


class WebSearchError(RuntimeError):
    """Error controlado durante una búsqueda web."""


class WebSearch:
    """Búsqueda web libre o restringida a dominios autorizados."""

    # Backends de búsqueda de texto documentados por DDGS.
    DEFAULT_BACKENDS = (
        "google", "bing", "brave", "duckduckgo", "grokipedia",
        "mojeek", "startpage", "yandex", "yahoo", "wikipedia",
    )

    def __init__(
        self,
        safesearch: str = "moderate",
        region: str = "wt-wt",
        retries: int = 2,
        backends: tuple[str, ...] = DEFAULT_BACKENDS,
        successful_engines_required: int = 2,
    ):
        self.safesearch = safesearch
        self.region = region

        if isinstance(retries, bool) or not isinstance(retries, int) or retries < 0:
            raise ValueError("retries debe ser un entero mayor o igual que cero.")
        if not backends or not all(isinstance(b, str) and b.strip() for b in backends):
            raise ValueError("Debe indicarse al menos un backend válido.")
        if (isinstance(successful_engines_required, bool)
                or not isinstance(successful_engines_required, int)
                or successful_engines_required < 1):
            raise ValueError("successful_engines_required debe ser un entero positivo.")

        # retries=2 significa: intento inicial + hasta dos reintentos.
        self.retries = retries
        self.backends = tuple(dict.fromkeys(b.strip().lower() for b in backends))
        self.successful_engines_required = successful_engines_required
        self.last_status = "not_run"
        self.last_message = ""
        try:
            from ddgs import DDGS
        except ImportError as error:
            raise WebSearchError(
                "DDGS no está instalado. Ejecutá: python -m pip install -U ddgs"
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
    def _normalizar_resultado(resultado: dict[str, Any]) -> dict[str, str] | None:
        titulo = str(resultado.get("title") or "").strip()
        url = str(resultado.get("href") or resultado.get("url") or "").strip()
        descripcion = str(resultado.get("body") or resultado.get("description") or "").strip()
        dominio = WebSearch._dominio_de_url(url)
        if not url or not dominio:
            return None
        return {
            "title": titulo or "Sin título",
            "url": url,
            "description": descripcion,
            "source": dominio,
        }

    @staticmethod
    def _hay_conexion_internet(timeout: float = 5.0) -> bool:
        """Comprueba HTTPS con dos destinos; no depende de un motor de búsqueda."""
        for url in ("https://www.google.com/generate_204", "https://www.cloudflare.com/"):
            try:
                with urlopen(url, timeout=timeout) as respuesta:
                    if 200 <= getattr(respuesta, "status", 200) < 500:
                        return True
            except Exception:
                continue
        return False

    def _buscar(self, consulta: str, max_results: int) -> list[dict[str, str]]:
        if not isinstance(consulta, str) or not consulta.strip():
            raise ValueError("La consulta de búsqueda no puede estar vacía.")
        if isinstance(max_results, bool) or not isinstance(max_results, int):
            raise ValueError("max_results debe ser un entero.")
        if not 1 <= max_results <= 20:
            raise ValueError("max_results debe estar entre 1 y 20.")

        self.last_status = "searching"
        self.last_message = ""
        errores: list[str] = []
        motores_con_resultados: list[str] = []
        salida: list[dict[str, str]] = []
        vistos: set[str] = set()

        for backend in self.backends:
            motor_aporto_resultados = False
            for intento in range(self.retries + 1):
                try:
                    with self._ddgs_class() as ddgs:
                        resultados = list(ddgs.text(
                            consulta.strip(),
                            region=self.region,
                            safesearch=self.safesearch,
                            max_results=max_results,
                            backend=backend,
                        ) or [])

                    # Respuesta vacía: el motor contestó, pero no encontró resultados.
                    items_motor = []
                    vistos_motor: set[str] = set()
                    for resultado in resultados:
                        item = self._normalizar_resultado(resultado)
                        if item is None:
                            continue
                        clave = item["url"].rstrip("/").lower()
                        if clave not in vistos_motor:
                            vistos_motor.add(clave)
                            items_motor.append(item)

                    if items_motor:
                        motor_aporto_resultados = True
                        motores_con_resultados.append(backend)
                        for item in items_motor:
                            clave = item["url"].rstrip("/").lower()
                            if clave not in vistos:
                                vistos.add(clave)
                                salida.append(item)
                        break  # Este motor ya cumplió; pasar al siguiente.
                    break  # Respuesta válida sin resultados: no es un fallo de conexión.

                except Exception as error:
                    errores.append(
                        f"{backend}, intento {intento + 1}/{self.retries + 1}: "
                        f"{type(error).__name__}: {error}"
                    )
                    # Reintentar el mismo motor; agotados los intentos, pasar al siguiente.

            if motor_aporto_resultados and len(motores_con_resultados) >= self.successful_engines_required:
                break

        if salida:
            self.last_status = (
                "success" if len(motores_con_resultados) >= self.successful_engines_required
                else "partial_success"
            )
            if self.last_status == "success":
                self.last_message = (
                    f"Búsqueda completada: {len(motores_con_resultados)} motores aportaron resultados "
                    f"({', '.join(motores_con_resultados)})."
                )
            else:
                self.last_message = (
                    f"Búsqueda parcial: solo {len(motores_con_resultados)} motor(es) aportaron resultados "
                    f"({', '.join(motores_con_resultados)}). Se devuelven los resultados disponibles."
                )
            return salida[:max_results]

        if self._hay_conexion_internet():
            self.last_status = "no_search_results_internet_available"
            self.last_message = (
                "Los motores de búsqueda no encontraron información para esta consulta, "
                "pero la conexión a Internet funciona correctamente."
            )
        else:
            self.last_status = "internet_connection_unavailable"
            self.last_message = (
                "No se obtuvieron resultados y tampoco se pudo confirmar la conexión a Internet."
            )

        if errores:
            self.last_message += " Detalles técnicos: " + " | ".join(errores[-5:])
        return []

    def search_web(self, query: str, max_results: int = 5) -> list[dict[str, str]]:
        """Realiza una búsqueda libre en Internet."""
        return self._buscar(query, max_results)

    def search_authorized(
        self, query: str, authorized_domains: list[str], max_results: int = 5
    ) -> list[dict[str, str]]:
        """Busca dentro de dominios autorizados y valida localmente cada URL."""
        if not isinstance(query, str) or not query.strip():
            raise ValueError("La consulta de búsqueda no puede estar vacía.")
        if not authorized_domains:
            raise ValueError("Debe indicarse al menos un dominio autorizado.")
        if isinstance(max_results, bool) or not isinstance(max_results, int):
            raise ValueError("max_results debe ser un entero.")
        if not 1 <= max_results <= 20:
            raise ValueError("max_results debe estar entre 1 y 20.")

        dominios = list(dict.fromkeys(self._normalizar_dominio(d) for d in authorized_domains))
        resultados_finales: list[dict[str, str]] = []
        vistos: set[str] = set()
        por_dominio = max(1, (max_results + len(dominios) - 1) // len(dominios))

        for dominio in dominios:
            consulta_restringida = f"site:{dominio} {query.strip()}"
            for item in self._buscar(consulta_restringida, por_dominio):
                host = self._dominio_de_url(item["url"])
                if not any(self._pertenece_al_dominio(host, permitido) for permitido in dominios):
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
    buscador = WebSearch()
    consulta = "Soft Actor Critic reinforcement learning"

    print("PRUEBA 1 - Búsqueda libre")
    resultados = buscador.search_web(consulta, max_results=5)
    print(f"Estado: {buscador.last_status}")
    print(f"Diagnóstico: {buscador.last_message}")
    for resultado in resultados:
        print(f"\n{resultado['title']}\n{resultado['url']}\n{resultado['description']}")

    print("\nPRUEBA 2 - Dominios autorizados")
    resultados = buscador.search_authorized(
        consulta, authorized_domains=["arxiv.org", "openai.com"], max_results=5
    )
    print(f"Estado: {buscador.last_status}")
    print(f"Diagnóstico: {buscador.last_message}")
    for resultado in resultados:
        print(f"\n{resultado['title']}\n{resultado['url']}\n{resultado['description']}")
