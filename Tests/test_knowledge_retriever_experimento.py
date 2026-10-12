import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from Agent.KnowledgeRetriever import (
    KnowledgeRetriever as KnowledgeRetrieverOriginal,
)

from Agent.KnowledgeRetriever_revisado import (
    KnowledgeRetriever as KnowledgeRetrieverRevisado,
)


KNOWLEDGE_DIR = BASE_DIR / "Knowledge"
MAX_RESULTADOS = 10


# Cada caso contiene la consulta y una frase que identifica
# el fragmento que esperamos recuperar en una posición alta.
CASOS_PRUEBA = [
    {
        "consulta": "críticos",
        "descripcion": "Definición de los críticos",
        "frases_esperadas": [
            "los críticos son redes neuronales",
            "función de valor de acción q",
        ],
    },
    {
        "consulta": "actualización de los críticos",
        "descripcion": "Actualización de los críticos",
        "frases_esperadas": [
            "minimizar una función de pérdida",
            "objetivo temporal de bellman",
        ],
    },
    {
        "consulta": "temperatura",
        "descripcion": "Función del coeficiente de temperatura",
        "frases_esperadas": [
            "coeficiente de temperatura",
            "término de entropía",
        ],
    },
    {
        "consulta": "temperatura automática",
        "descripcion": "Ajuste automático de temperatura",
        "frases_esperadas": [
            "coeficiente se ajusta",
            "objetivo de entropía",
        ],
    },
    {
        "consulta": "Replay Buffer",
        "descripcion": "Definición del Replay Buffer",
        "frases_esperadas": [
            "replay buffer es",
        ],
    },
    {
        "consulta": "objetivo de Bellman",
        "descripcion": "Objetivo de Bellman",
        "frases_esperadas": [
            "el objetivo de bellman",
        ],
    },
    {
        "consulta": "entropía",
        "descripcion": "Función de la entropía",
        "frases_esperadas": [
            "entropía",
        ],
    },
    {
        "consulta": "política del actor",
        "descripcion": "Política del actor",
        "frases_esperadas": [
            "el actor representa la política",
        ],
    },
    {
        "consulta": "redes objetivo",
        "descripcion": "Función de las redes objetivo",
        "frases_esperadas": [
            "redes objetivo",
        ],
    },
]


def buscar_resultados(buscador, consulta):
    return buscador.buscar(
        consulta,
        max_resultados=MAX_RESULTADOS,
    )


def localizar_fragmento(resultados, frases_esperadas):
    """
    Busca el primer fragmento que contenga todas las frases esperadas.

    Devuelve su posición y puntuación.
    Si no se encuentra, devuelve None.
    """
    frases = [
        frase.casefold()
        for frase in frases_esperadas
    ]

    for posicion, resultado in enumerate(resultados, start=1):
        texto = resultado["text"].casefold()

        if all(frase in texto for frase in frases):
            return {
                "posicion": posicion,
                "score": resultado["score"],
                "texto": resultado["text"],
            }

    return None


def mostrar_resultado(nombre, resultado):
    print(f"\n  {nombre}")

    if resultado is None:
        print("    Fragmento esperado: NO ENCONTRADO")
        return

    print(f"    Posición: {resultado['posicion']}")
    print(f"    Score: {resultado['score']:.4f}")
    print(f"    Fragmento: {resultado['texto']}")


def evaluar_caso(original, revisado, caso):
    consulta = caso["consulta"]
    frases = caso["frases_esperadas"]

    resultados_originales = buscar_resultados(
        original,
        consulta,
    )

    resultados_revisados = buscar_resultados(
        revisado,
        consulta,
    )

    esperado_original = localizar_fragmento(
        resultados_originales,
        frases,
    )

    esperado_revisado = localizar_fragmento(
        resultados_revisados,
        frases,
    )

    print("\n" + "=" * 78)
    print(f"CONSULTA: {consulta}")
    print(f"Objetivo: {caso['descripcion']}")
    print("=" * 78)

    mostrar_resultado(
        "VERSIÓN ORIGINAL",
        esperado_original,
    )

    mostrar_resultado(
        "VERSIÓN REVISADA",
        esperado_revisado,
    )

    if esperado_original is None or esperado_revisado is None:
        comparacion = "INCOMPLETA: falta el fragmento esperado"

    elif (
        esperado_original["posicion"]
        == esperado_revisado["posicion"]
    ):
        comparacion = "SIN CAMBIO DE POSICIÓN"

    elif (
        esperado_revisado["posicion"]
        < esperado_original["posicion"]
    ):
        comparacion = "MEJORA DE POSICIÓN"

    else:
        comparacion = "REGRESIÓN DE POSICIÓN"

    print(f"\n  Comparación: {comparacion}")

    return {
        "consulta": consulta,
        "original": esperado_original,
        "revisado": esperado_revisado,
        "comparacion": comparacion,
    }


def main():
    original = KnowledgeRetrieverOriginal(KNOWLEDGE_DIR)
    revisado = KnowledgeRetrieverRevisado(KNOWLEDGE_DIR)

    print("=" * 78)
    print("GIAR-ORION - EXPERIMENTO DE PRECISIÓN DEL KNOWLEDGE RETRIEVER")
    print("=" * 78)

    print(f"Directorio de conocimiento: {KNOWLEDGE_DIR}")
    print(f"Casos evaluados: {len(CASOS_PRUEBA)}")
    print(f"Máximo de resultados examinados: {MAX_RESULTADOS}")

    print("\nNo se modifica ningún recuperador ni test anterior.")

    resumen = []

    for caso in CASOS_PRUEBA:
        resultado = evaluar_caso(
            original,
            revisado,
            caso,
        )

        resumen.append(resultado)

    mejoras = sum(
        resultado["comparacion"] == "MEJORA DE POSICIÓN"
        for resultado in resumen
    )

    regresiones = sum(
        resultado["comparacion"] == "REGRESIÓN DE POSICIÓN"
        for resultado in resumen
    )

    sin_cambios = sum(
        resultado["comparacion"] == "SIN CAMBIO DE POSICIÓN"
        for resultado in resumen
    )

    incompletas = sum(
        resultado["comparacion"].startswith("INCOMPLETA")
        for resultado in resumen
    )

    print("\n" + "=" * 78)
    print("RESUMEN DEL EXPERIMENTO")
    print("=" * 78)

    print(f"Mejoras de posición: {mejoras}")
    print(f"Regresiones de posición: {regresiones}")
    print(f"Sin cambios de posición: {sin_cambios}")
    print(f"Evaluaciones incompletas: {incompletas}")

    print("\nDetalle por consulta:")

    for resultado in resumen:
        original_resultado = resultado["original"]
        revisado_resultado = resultado["revisado"]

        posicion_original = (
            original_resultado["posicion"]
            if original_resultado
            else "N/E"
        )

        posicion_revisada = (
            revisado_resultado["posicion"]
            if revisado_resultado
            else "N/E"
        )

        print(
            f"  {resultado['consulta']}: "
            f"{posicion_original} -> {posicion_revisada} | "
            f"{resultado['comparacion']}"
        )

    print("\n" + "=" * 78)
    print("FIN DEL EXPERIMENTO")
    print("=" * 78)

    print(
        "Nota: una mejor posición del fragmento esperado "
        "no garantiza por sí sola una mejor calidad global."
    )


if __name__ == "__main__":
    main()