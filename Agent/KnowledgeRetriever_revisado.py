import re
from pathlib import Path


class KnowledgeRetriever:
    """Busca y ordena fragmentos relevantes de Knowledge.

    El ranking es heurístico y léxico; no representa comprensión semántica.
    """

    PALABRAS_IGNORADAS = {
        "a", "al", "de", "del", "el", "en", "la", "las",
        "lo", "los", "o", "para", "por", "que", "se",
        "un", "una", "y", "es", "como", "con", "qué",
        "cual", "cuál",
    }

    # Marcadores de explicación directa. Se excluyen expresiones genéricas
    # como «durante el entrenamiento», que no indican por sí solas una
    # definición o explicación del concepto consultado.
    MARCADORES_EXPLICATIVOS = (
        " es un ", 
        " es una ", 
        " consiste en",
        "se define como",
        "se utiliza para",
        "se usa para",
        "su función es",
        "su objetivo es",
        "sirve para",
        "se calcula",
        "el objetivo combina",
        "la actualización consiste",
    )

    # Marcadores de metadiscurso: señalan qué comprobar, pero no explican
    # necesariamente el concepto. Se penalizan moderadamente.
    MARCADORES_META = (
        "para analizar una implementación",
        "deben verificarse",
        "debe verificarse",
        "conviene verificar",
        "aspectos que deben verificarse",
        "para evaluar una implementación",
    )

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
        """Normaliza mayúsculas/minúsculas para facilitar la comparación."""
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

            # Los encabezados se conservan como contexto, pero no se evalúan
            # como fragmentos independientes.
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
        """Extrae términos únicos y elimina palabras funcionales frecuentes."""
        palabras = set(re.findall(r"\w+", cls._normalizar(texto)))
        return palabras - cls.PALABRAS_IGNORADAS

    @staticmethod
    def _contar_palabras(texto: str) -> int:
        """Cuenta palabras para estimar el tamaño del fragmento."""
        return len(re.findall(r"\w+", texto))

    @classmethod
    def _factor_explicativo(cls, bloque: str) -> float:
        """Ajusta moderadamente la puntuación según el tipo de contenido.

        Solo usa marcadores relativamente específicos. Si el bloque contiene
        a la vez marcadores explicativos y de metadiscurso, no aplica ajuste.
        """
        texto = cls._normalizar(bloque)

        tiene_explicacion = any(
            marcador in texto
            for marcador in cls.MARCADORES_EXPLICATIVOS
        )
        tiene_metadiscurso = any(
            marcador in texto
            for marcador in cls.MARCADORES_META
        )

        if tiene_explicacion and tiene_metadiscurso:
            return 1.0
        if tiene_explicacion:
            return 1.10
        if tiene_metadiscurso:
            return 0.80
        return 1.0

    @staticmethod
    def _es_lista_de_parametros(bloque: str) -> bool:
        """Detecta listas Markdown sencillas que suelen enumerar elementos."""
        return bloque.count("- ") >= 2

    def buscar(
        self,
        consulta: str,
        max_resultados: int = 5,
    ) -> list[dict]:
        """Busca fragmentos y los ordena por relevancia textual heurística."""
        if not consulta.strip():
            return []

        if max_resultados < 1:
            return []

        palabras_consulta = self._extraer_palabras(consulta)
        if not palabras_consulta:
            return []

        resultados = []
        consulta_normalizada = self._normalizar(consulta).strip()
        archivos = sorted(self.knowledge_dir.rglob("*.md"))

        for archivo in archivos:
            try:
                texto = archivo.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue

            for bloque in self._dividir_documento(texto):
                palabras_bloque = self._extraer_palabras(bloque)
                coincidencias = palabras_consulta & palabras_bloque

                if not coincidencias:
                    continue

                # 1. Cobertura: proporción de términos de consulta presentes.
                cobertura = len(coincidencias) / len(palabras_consulta)
                factor_cobertura = cobertura ** 2

                # 2. Información: longitud acotada para no premiar bloques
                # indefinidamente por ser más extensos.
                cantidad_palabras = self._contar_palabras(bloque)
                factor_informacion = min(cantidad_palabras / 30, 1.0)

                # 3. Longitud: penalización moderada para bloques extensos.
                factor_longitud = 0.75 if cantidad_palabras > 45 else 1.0

                # 4. Listas: penalización moderada para listas de parámetros.
                factor_lista = (
                    0.70 if self._es_lista_de_parametros(bloque) else 1.0
                )

                # 5. Coincidencia literal: bonificación pequeña.
                bloque_normalizado = self._normalizar(bloque)
                factor_coincidencia = (
                    1.10
                    if consulta_normalizada in bloque_normalizado
                    else 1.0
                )

                # 6. Ajuste moderado por tipo de contenido.
                factor_explicativo = self._factor_explicativo(bloque)

                puntuacion = (
                    factor_cobertura
                    * (0.7 + 0.3 * factor_informacion)
                    * factor_longitud
                    * factor_lista
                    * factor_coincidencia
                    * factor_explicativo
                )

                resultados.append({
                    "source": str(archivo.relative_to(self.knowledge_dir)),
                    "text": bloque,
                    "score": round(puntuacion, 4),
                    "matched_terms": sorted(coincidencias),
                })

        # Orden principal por puntuación. Desempates: más términos coincidentes
        # y luego el fragmento más breve.
        resultados.sort(
            key=lambda resultado: (
                resultado["score"],
                len(resultado["matched_terms"]),
                -self._contar_palabras(resultado["text"]),
            ),
            reverse=True,
        )

        # Evitar devolver exactamente el mismo fragmento dos veces.
        resultados_unicos = []
        fragmentos_vistos = set()

        for resultado in resultados:
            clave = (resultado["source"], resultado["text"])
            if clave in fragmentos_vistos:
                continue

            fragmentos_vistos.add(clave)
            resultados_unicos.append(resultado)

            if len(resultados_unicos) >= max_resultados:
                break

        return resultados_unicos
