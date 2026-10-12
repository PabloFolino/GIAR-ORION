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
]


def normalizar(texto):
    return " ".join(texto.casefold().split())


def evaluar_resultados(resultados, frases_esperadas):
    for posicion, resultado in enumerate(resultados, start=1):
        texto = normalizar(resultado["text"])

        if all(
            normalizar(frase) in texto
            for frase in frases_esperadas
        ):
            return posicion

    return None


def mostrar_resultados(nombre, resultados, frases_esperadas):
    print(f"\n  {nombre}")

    if not resultados:
        print("    No se encontraron resultados.")
        return None

    posicion_esperada = evaluar_resultados(
        resultados,
        frases_esperadas,
    )

    for posicion, resultado in enumerate(resultados, start=1):
        texto = " ".join(resultado["text"].split())

        marca = (
            " <-- FRAGMENTO ESPERADO"
            if all(
                normalizar(frase) in normalizar(texto)
                for frase in frases_esperadas
            )
            else ""
        )

        print(
            f"    {posicion}. "
            f"score={resultado['score']:.4f}{marca}"
        )
        print(f"       {texto}")

    if posicion_esperada is None:
        print("    Evaluación: fragmento esperado no encontrado.")
    else:
        print(
            "    Posición del fragmento esperado: "
            f"{posicion_esperada}"
        )

    return posicion_esperada


def main():
    original = KnowledgeRetrieverOriginal(KNOWLEDGE_DIR)
    revisado = KnowledgeRetrieverRevisado(KNOWLEDGE_DIR)

    print("=" * 78)
    print("GIAR-ORION - EVALUACIÓN DIRIGIDA DE PRECISIÓN")
    print("=" * 78)
    print("Módulos evaluados:")
    print("  - Agent.KnowledgeRetriever")
    print("  - Agent.KnowledgeRetriever_revisado")
    print(f"Posición máxima deseada: 3")
    print("Criterio: coincidencia de todas las frases esperadas")
    print("en un mismo fragmento.")
    print("\nNo se modifica ningún módulo ni test anterior.")

    for numero, caso in enumerate(CASOS_PRUEBA, start=1):
        consulta = caso["consulta"]
        frases = caso["frases_esperadas"]

        resultados_originales = original.buscar(
            consulta,
            max_resultados=MAX_RESULTADOS,
        )

        resultados_revisados = revisado.buscar(
            consulta,
            max_resultados=MAX_RESULTADOS,
        )

        print("\n" + "-" * 78)
        print(f"PRUEBA {numero}: {caso['descripcion']}")
        print(f"Consulta: {consulta}")
        print("Frases esperadas:")
        for frase in frases:
            print(f"  - {frase}")

        posicion_original = mostrar_resultados(
            "VERSIÓN ORIGINAL",
            resultados_originales,
            frases,
        )

        posicion_revisada = mostrar_resultados(
            "VERSIÓN REVISADA",
            resultados_revisados,
            frases,
        )

        print("\n  COMPARACIÓN")

        if posicion_original is None and posicion_revisada is None:
            print("    Ninguna versión encontró el fragmento esperado.")
        elif posicion_original is None:
            print("    El fragmento esperado solo apareció en la revisada.")
        elif posicion_revisada is None:
            print("    El fragmento esperado solo apareció en la original.")
        elif posicion_revisada < posicion_original:
            print(
                "    MEJORA: el fragmento esperado subió de "
                f"{posicion_original} a {posicion_revisada}."
            )
        elif posicion_revisada > posicion_original:
            print(
                "    REGRESIÓN: el fragmento esperado bajó de "
                f"{posicion_original} a {posicion_revisada}."
            )
        else:
            print(
                "    SIN CAMBIO: ambas versiones ubican el fragmento "
                f"en la posición {posicion_original}."
            )

        if (
            posicion_revisada is not None
            and posicion_revisada <= 3
        ):
            print("    Criterio de posición revisada: APROBADO")
        else:
            print("    Criterio de posición revisada: REVISAR")

    print("\n" + "=" * 78)
    print("FIN DE LA EVALUACIÓN DIRIGIDA")
    print("=" * 78)
    print(
        "Nota: la prueba mide la posición de fragmentos específicos; "
        "no demuestra por sí sola la calidad global del recuperador."
    )


if __name__ == "__main__":
    main()
