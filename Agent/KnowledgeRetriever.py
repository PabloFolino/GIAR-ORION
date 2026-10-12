import re
from pathlib import Path


class KnowledgeRetriever:
    """Busca y ordena fragmentos relevantes de Knowledge."""

    PALABRAS_IGNORADAS = {
        "a", "al", "de", "del", "el", "en", "la", "las",
        "lo", "los", "o", "para", "por", "que", "se",
        "un", "una", "y", "es", "como", "con", "qué",
        "cual", "cuál", "los", "las",
    }

    def __init__(self, knowledge_dir: Path):
        self.knowledge_dir = Path(knowledge_dir)

        if not self.knowledge_dir.exists():
            raise FileNotFoundError(
                f"No existe el directorio de conocimiento: "
                f"{self.knowledge_dir}"
            )

        if not self.knowledge_dir.is_dir():
            raise NotADirectoryError(
                f"La ruta no es un directorio: {self.knowledge_dir}"
            )

    @staticmethod
    def _normalizar(texto: str) -> str:
        """Normaliza texto para facilitar la comparación."""
        return texto.casefold()

    @staticmethod
    def _dividir_documento(texto: str) -> list[str]:
        """Divide el documento en fragmentos sin perder sus párrafos."""

        bloques = []
        bloque_actual = []

        for linea in texto.splitlines():
            linea = linea.strip()

            if not linea:
                if bloque_actual:
                    bloques.append(" ".join(bloque_actual))
                    bloque_actual = []
                continue

            # Los encabezados se conservan como contexto,
            # pero no se evalúan como fragmentos independientes.
            if linea.startswith("#"):
                if bloque_actual:
                    bloques.append(" ".join(bloque_actual))
                    bloque_actual = []

                continue

            bloque_actual.append(linea)

        if bloque_actual:
            bloques.append(" ".join(bloque_actual))

        return [
            bloque.strip()
            for bloque in bloques
            if bloque.strip()
        ]

    @classmethod
    def _extraer_palabras(cls, texto: str) -> set[str]:
        """Extrae términos significativos del texto."""

        palabras = set(
            re.findall(r"\w+", cls._normalizar(texto))
        )

        return palabras - cls.PALABRAS_IGNORADAS

    def buscar(
        self,
        consulta: str,
        max_resultados: int = 5,
    ) -> list[dict]:
        """Busca fragmentos y los ordena por relevancia textual."""

        if not consulta.strip():
            return []

        if max_resultados < 1:
            return []

        palabras_consulta = self._extraer_palabras(consulta)

        if not palabras_consulta:
            return []

        resultados = []

        archivos = sorted(
            self.knowledge_dir.rglob("*.md")
        )

        for archivo in archivos:
            try:
                texto = archivo.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue

            for bloque in self._dividir_documento(texto):
                palabras_bloque = self._extraer_palabras(bloque)

                coincidencias = (
                    palabras_consulta & palabras_bloque
                )

                if not coincidencias:
                    continue

                # Proporción de términos de la consulta encontrados.
                cobertura = (
                    len(coincidencias) / len(palabras_consulta)
                )

                # Favorecer la coincidencia con todos los términos.
                factor_cobertura = cobertura ** 2

                cantidad_palabras = len(
                    re.findall(r"\w+", bloque)
                )

                # Evitar que los fragmentos largos obtengan ventaja
                # únicamente por su cantidad de palabras.
                factor_informacion = min(
                    cantidad_palabras / 30,
                    1.0,
                )

                factor_longitud = 1.0

                if cantidad_palabras > 45:
                    factor_longitud = 0.75

                # Penalizar listas de parámetros frente a explicaciones.
                es_lista = bloque.count("- ") >= 2
                factor_lista = 0.70 if es_lista else 1.0

                # Coincidencia textual exacta con la consulta normalizada.
                consulta_normalizada = self._normalizar(consulta).strip()
                bloque_normalizado = self._normalizar(bloque)

                factor_coincidencia = 1.0

                if consulta_normalizada in bloque_normalizado:
                    factor_coincidencia = 1.10

                puntuacion = (
                    factor_cobertura
                    * (0.7 + 0.3 * factor_informacion)
                    * factor_longitud
                    * factor_lista
                    * factor_coincidencia
                )

                resultados.append({
                    "source": str(
                        archivo.relative_to(self.knowledge_dir)
                    ),
                    "text": bloque,
                    "score": round(puntuacion, 4),
                    "matched_terms": sorted(coincidencias),
                })

        # Ordenar por puntuación y, en caso de empate,
        # favorecer los fragmentos con más términos coincidentes.
        resultados.sort(
            key=lambda resultado: (
                resultado["score"],
                len(resultado["matched_terms"]),
            ),
            reverse=True,
        )

        # Evitar devolver exactamente el mismo fragmento dos veces.
        resultados_unicos = []
        fragmentos_vistos = set()

        for resultado in resultados:
            clave = (
                resultado["source"],
                resultado["text"],
            )

            if clave in fragmentos_vistos:
                continue

            fragmentos_vistos.add(clave)
            resultados_unicos.append(resultado)

            if len(resultados_unicos) >= max_resultados:
                break

        return resultados_unicos
