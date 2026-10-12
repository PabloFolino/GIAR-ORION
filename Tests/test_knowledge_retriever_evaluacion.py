import sys
from pathlib import Path

# Incorporar la raíz del proyecto a la ruta de búsqueda de Python.
ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Agent.KnowledgeRetriever import KnowledgeRetriever as Original
from Agent.KnowledgeRetriever_revisado import KnowledgeRetriever as Revisado
from Agent.KnowledgeRetriever_experimento import KnowledgeRetriever as Experimental


KNOWLEDGE_DIR = ROOT / "Knowledge"
MAX_RESULTADOS = 10


# ------------------------------------------------------------
# PRUEBA 1: PRECISIÓN DEL RANKING
# ------------------------------------------------------------

CONSULTAS_RANKING = [
    {
        "consulta": "SAC",
        "esperadas": ["algoritmo de aprendizaje por refuerzo"],
    },
    {
        "consulta": "críticos",
        "esperadas": ["los críticos son redes neuronales"],
    },
    {
        "consulta": "actualización de los críticos",
        "esperadas": [
            "la actualización de los críticos consiste en minimizar"
        ],
    },
    {
        "consulta": "temperatura automática",
        "esperadas": [
            "el coeficiente se ajusta mediante un objetivo de entropía"
        ],
    },
    {
        "consulta": "objetivo de Bellman",
        "esperadas": [
            "el objetivo de bellman combina la recompensa inmediata"
        ],
    },
    {
        "consulta": "pérdida del actor",
        "esperadas": [
            "el actor se actualiza para favorecer acciones"
        ],
    },
    {
        "consulta": "referencias bibliográficas",
        "esperadas": ["fuentes primarias correspondientes"],
    },
]


# ------------------------------------------------------------
# PRUEBA 2: CONSULTAS ALTERNATIVAS
#
# Los criterios representan conceptos que deberían aparecer
# en los resultados. No se exige que la consulta y el texto
# utilicen exactamente las mismas palabras.
# ------------------------------------------------------------

CONSULTAS_ALTERNATIVAS = [
    {
        "consulta": "¿Qué función cumple el actor?",
        "criterios": ["política", "acciones"],
    },
    {
        "consulta": "¿Cómo se evita sobreestimar el valor de las acciones?",
        "criterios": ["críticos", "mínimo"],
    },
    {
        "consulta": "¿Cómo aprende el agente a explorar?",
        "criterios": ["entropía", "temperatura"],
    },
    {
        "consulta": "¿Cómo se determina si el entrenamiento funcionó?",
        "criterios": ["recompensa", "estabilidad"],
    },
    {
        "consulta": "¿Qué bibliografía respalda SAC?",
        "criterios": ["fuentes", "referencias"],
    },
]


VERSIONES = [
    ("ORIGINAL", Original),
    ("REVISADA", Revisado),
    ("EXPERIMENTAL", Experimental),
]


def contiene_frase(texto, frases):
    """Comprueba si aparece alguna de las frases esperadas."""
    texto = texto.casefold()
    return any(frase.casefold() in texto for frase in frases)


def evaluar_ranking(resultados, esperadas):
    """
    Devuelve la posición del fragmento esperado.
    None significa que no se encontró entre los resultados.
    """
    for posicion, resultado in enumerate(resultados, start=1):
        if contiene_frase(resultado["text"], esperadas):
            return posicion

    return None


def evaluar_conceptos(resultados, criterios):
    """
    Cuenta cuántos conceptos de evaluación aparecen en los
    textos recuperados.

    Es una medida orientativa: no demuestra por sí sola que
    el resultado responda correctamente la consulta.
    """
    textos = [
        resultado["text"].casefold()
        for resultado in resultados
    ]

    texto_conjunto = " ".join(textos)

    encontrados = [
        criterio
        for criterio in criterios
        if criterio.casefold() in texto_conjunto
    ]

    return encontrados


def crear_recuperadores():
    return {
        nombre: clase(KNOWLEDGE_DIR)
        for nombre, clase in VERSIONES
    }


def ejecutar_ranking(recuperadores):
    print("\n" + "=" * 90)
    print("PRUEBA 1: PRECISIÓN DEL RANKING")
    print("=" * 90)

    resumen = {
        nombre: {"top1": 0, "top10": 0, "sin_resultado": 0}
        for nombre, _ in VERSIONES
    }

    for caso in CONSULTAS_RANKING:
        consulta = caso["consulta"]
        esperadas = caso["esperadas"]

        print(f"\nConsulta: {consulta}")
        print(f"Fragmento esperado: {esperadas[0]}")

        for nombre, _ in VERSIONES:
            resultados = recuperadores[nombre].buscar(
                consulta,
                max_resultados=MAX_RESULTADOS,
            )

            posicion = evaluar_ranking(resultados, esperadas)

            if posicion == 1:
                resumen[nombre]["top1"] += 1

            if posicion is not None:
                resumen[nombre]["top10"] += 1
                estado = f"posición {posicion}"
            else:
                resumen[nombre]["sin_resultado"] += 1
                estado = "no encontrado en Top-10"

            print(f"  {nombre}: {estado}")

            if resultados:
                print(f"    Primer resultado: {resultados[0]['text']}")

    print("\nResumen del ranking:")

    for nombre, _ in VERSIONES:
        datos = resumen[nombre]
        total = len(CONSULTAS_RANKING)

        print(
            f"  {nombre}: "
            f"Top-1={datos['top1']}/{total}; "
            f"Top-10={datos['top10']}/{total}; "
            f"sin resultado esperado={datos['sin_resultado']}/{total}"
        )

    return resumen


def ejecutar_consultas_alternativas(recuperadores):
    print("\n" + "=" * 90)
    print("PRUEBA 2: CONSULTAS ALTERNATIVAS")
    print("=" * 90)

    resumen = {
        nombre: {"criterios_encontrados": 0, "criterios_totales": 0}
        for nombre, _ in VERSIONES
    }

    for caso in CONSULTAS_ALTERNATIVAS:
        consulta = caso["consulta"]
        criterios = caso["criterios"]

        print(f"\nConsulta: {consulta}")
        print(f"Conceptos buscados: {criterios}")

        for nombre, _ in VERSIONES:
            resultados = recuperadores[nombre].buscar(
                consulta,
                max_resultados=MAX_RESULTADOS,
            )

            encontrados = evaluar_conceptos(resultados, criterios)

            resumen[nombre]["criterios_encontrados"] += len(encontrados)
            resumen[nombre]["criterios_totales"] += len(criterios)

            print(
                f"  {nombre}: "
                f"{len(encontrados)}/{len(criterios)} conceptos encontrados"
            )

            if encontrados:
                print(f"    Conceptos: {encontrados}")

            if resultados:
                print(f"    Primer resultado: {resultados[0]['text']}")
            else:
                print("    Sin resultados.")

    print("\nResumen de consultas alternativas:")

    for nombre, _ in VERSIONES:
        datos = resumen[nombre]
        encontrados = datos["criterios_encontrados"]
        total = datos["criterios_totales"]

        porcentaje = encontrados / total * 100 if total else 0

        print(
            f"  {nombre}: {encontrados}/{total} "
            f"coincidencias de conceptos ({porcentaje:.1f} %)"
        )

    return resumen


def main():
    print("=" * 90)
    print("GIAR-ORION - EVALUACIÓN INDEPENDIENTE DE KNOWLEDGE RETRIEVER")
    print("=" * 90)
    print(f"Directorio de conocimiento: {KNOWLEDGE_DIR}")
    print("Se comparan los recuperadores original, revisado y experimental.")
    print("No se modifican los recuperadores ni los documentos de conocimiento.")

    recuperadores = crear_recuperadores()

    ejecutar_ranking(recuperadores)
    ejecutar_consultas_alternativas(recuperadores)

    print("\n" + "=" * 90)
    print("FIN DE LA EVALUACIÓN")
    print("=" * 90)
    print("Los resultados de conceptos son orientativos y requieren revisión.")


if __name__ == "__main__":
    main()

