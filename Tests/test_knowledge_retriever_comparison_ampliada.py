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
MAX_RESULTADOS = 3
LONGITUD_EXTRACTO = 220

CASOS_PRUEBA = [
    {
        "consulta": "críticos",
        "descripcion": "Definición de los críticos",
    },
    {
        "consulta": "objetivo de Bellman",
        "descripcion": "Objetivo de Bellman",
    },
    {
        "consulta": "entropía",
        "descripcion": "Función de la entropía",
    },
    {
        "consulta": "política del actor",
        "descripcion": "Política del actor",
    },
    {
        "consulta": "temperatura",
        "descripcion": "Coeficiente de temperatura",
    },
    {
        "consulta": "Replay Buffer",
        "descripcion": "Función del Replay Buffer",
    },
    {
        "consulta": "redes objetivo",
        "descripcion": "Función de las redes objetivo",
    },
    {
        "consulta": "actualización de los críticos",
        "descripcion": "Actualización de los críticos",
    },
]


def obtener_resultados(buscador, consulta):
    return buscador.buscar(
        consulta,
        max_resultados=MAX_RESULTADOS,
    )


def mostrar_resultados(nombre, resultados):
    print(f"\n  {nombre}")

    if not resultados:
        print("    Sin resultados.")
        return

    for posicion, resultado in enumerate(resultados, start=1):
        texto = " ".join(resultado["text"].split())
        extracto = texto[:LONGITUD_EXTRACTO]

        if len(texto) > LONGITUD_EXTRACTO:
            extracto += "..."

        print(
            f"    {posicion}. "
            f"score={resultado['score']:.4f}"
        )
        print(f"       {extracto}")


def comparar_resultados(originales, revisados):
    if not originales or not revisados:
        return "COMPARACIÓN INCOMPLETA: faltan resultados"

    texto_original = originales[0]["text"].strip()
    texto_revisado = revisados[0]["text"].strip()

    if texto_original == texto_revisado:
        return "MISMO FRAGMENTO EN PRIMERA POSICIÓN"

    return "CAMBIÓ EL FRAGMENTO EN PRIMERA POSICIÓN"


def main():
    original = KnowledgeRetrieverOriginal(KNOWLEDGE_DIR)
    revisado = KnowledgeRetrieverRevisado(KNOWLEDGE_DIR)

    print("=" * 78)
    print("GIAR-ORION - COMPARACIÓN AMPLIADA DEL KNOWLEDGE RETRIEVER")
    print("=" * 78)
    print("Versión original: Agent.KnowledgeRetriever")
    print("Versión revisada: Agent.KnowledgeRetriever_revisado")
    print(f"Consultas evaluadas: {len(CASOS_PRUEBA)}")
    print(f"Resultados mostrados por versión: {MAX_RESULTADOS}")
    print("\nEsta prueba no modifica los módulos ni los tests existentes.")

    resumen = []

    for numero, caso in enumerate(CASOS_PRUEBA, start=1):
        consulta = caso["consulta"]

        resultados_originales = obtener_resultados(
            original,
            consulta,
        )

        resultados_revisados = obtener_resultados(
            revisado,
            consulta,
        )

        comparacion = comparar_resultados(
            resultados_originales,
            resultados_revisados,
        )

        print("\n" + "-" * 78)
        print(f"PRUEBA {numero}: {caso['descripcion']}")
        print(f"Consulta: {consulta}")

        mostrar_resultados(
            "VERSIÓN ORIGINAL",
            resultados_originales,
        )

        mostrar_resultados(
            "VERSIÓN REVISADA",
            resultados_revisados,
        )

        print(f"\n  Comparación: {comparacion}")

        resumen.append(
            {
                "consulta": consulta,
                "original": resultados_originales,
                "revisado": resultados_revisados,
                "comparacion": comparacion,
            }
        )

    print("\n" + "=" * 78)
    print("RESUMEN DE LA COMPARACIÓN AMPLIADA")
    print("=" * 78)

    for caso in resumen:
        originales = caso["original"]
        revisados = caso["revisado"]

        posicion_original = (
            originales[0]["score"]
            if originales
            else None
        )

        posicion_revisada = (
            revisados[0]["score"]
            if revisados
            else None
        )

        print(f"\nConsulta: {caso['consulta']}")
        print(f"  Resultado: {caso['comparacion']}")

        if posicion_original is not None:
            print(
                "  Puntuación del primer resultado original: "
                f"{posicion_original:.4f}"
            )

        if posicion_revisada is not None:
            print(
                "  Puntuación del primer resultado revisado: "
                f"{posicion_revisada:.4f}"
            )

    print("\n" + "=" * 78)
    print("FIN DE LA COMPARACIÓN")
    print("=" * 78)
    print(
        "Nota: una puntuación mayor no demuestra por sí sola "
        "que la respuesta sea más pertinente."
    )
    print(
        "La relevancia debe evaluarse examinando el contenido "
        "y la posición de los fragmentos."
    )


if __name__ == "__main__":
    main()

