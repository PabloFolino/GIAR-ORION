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

from Agent.KnowledgeRetriever_experimento import (
    KnowledgeRetriever as KnowledgeRetrieverExperimento,
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


def localizar_fragmento(resultados, frases_esperadas):
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


def buscar_y_evaluar(buscador, consulta, frases_esperadas):
    resultados = buscador.buscar(
        consulta,
        max_resultados=MAX_RESULTADOS,
    )

    fragmento_esperado = localizar_fragmento(
        resultados,
        frases_esperadas,
    )

    primer_resultado = resultados[0] if resultados else None

    return {
        "resultados": resultados,
        "esperado": fragmento_esperado,
        "primero": primer_resultado,
    }


def mostrar_version(nombre, evaluacion):
    print(f"\n  {nombre}")

    esperado = evaluacion["esperado"]
    primero = evaluacion["primero"]

    if esperado is None:
        print("    Fragmento esperado: NO ENCONTRADO")
    else:
        print(
            f"    Posición esperada: {esperado['posicion']}"
        )
        print(
            f"    Score esperado: {esperado['score']:.4f}"
        )

    if primero is None:
        print("    Primer resultado: SIN RESULTADOS")
    else:
        print(
            f"    Score del primer resultado: "
            f"{primero['score']:.4f}"
        )
        print(
            f"    Primer fragmento: "
            f"{' '.join(primero['text'].split())}"
        )


def comparar_fragmento_esperado(base, nuevo):
    if base is None or nuevo is None:
        return "INCOMPLETA: no se encontró el fragmento esperado"

    posicion_base = base["posicion"]
    posicion_nueva = nuevo["posicion"]

    if posicion_nueva < posicion_base:
        return "MEJORA DE POSICIÓN"

    if posicion_nueva > posicion_base:
        return "REGRESIÓN DE POSICIÓN"

    return "SIN CAMBIO DE POSICIÓN"


def comparar_primer_fragmento(base, nuevo):
    if base is None or nuevo is None:
        return "COMPARACIÓN INCOMPLETA"

    if base["text"].strip() == nuevo["text"].strip():
        return "MISMO FRAGMENTO"

    return "CAMBIÓ EL FRAGMENTO"


def main():
    versiones = {
        "ORIGINAL": KnowledgeRetrieverOriginal(KNOWLEDGE_DIR),
        "REVISADA": KnowledgeRetrieverRevisado(KNOWLEDGE_DIR),
        "EXPERIMENTAL": KnowledgeRetrieverExperimento(KNOWLEDGE_DIR),
    }

    print("=" * 88)
    print("GIAR-ORION - COMPARACIÓN DE TRES KNOWLEDGE RETRIEVERS")
    print("=" * 88)
    print(f"Consultas evaluadas: {len(CASOS_PRUEBA)}")
    print(f"Máximo de resultados examinados: {MAX_RESULTADOS}")
    print("No se modifican los recuperadores durante la ejecución.")

    resumen = []

    for caso in CASOS_PRUEBA:
        consulta = caso["consulta"]
        frases = caso["frases_esperadas"]

        evaluaciones = {
            nombre: buscar_y_evaluar(
                buscador,
                consulta,
                frases,
            )
            for nombre, buscador in versiones.items()
        }

        print("\n" + "=" * 88)
        print(f"CONSULTA: {consulta}")
        print(f"Objetivo: {caso['descripcion']}")
        print("=" * 88)

        for nombre, evaluacion in evaluaciones.items():
            mostrar_version(nombre, evaluacion)

        revisada = evaluaciones["REVISADA"]
        experimental = evaluaciones["EXPERIMENTAL"]
        original = evaluaciones["ORIGINAL"]

        print("\n  COMPARACIONES")

        print(
            "    Fragmento esperado, revisada -> experimental: "
            + comparar_fragmento_esperado(
                revisada["esperado"],
                experimental["esperado"],
            )
        )

        print(
            "    Primer fragmento, revisada -> experimental: "
            + comparar_primer_fragmento(
                revisada["primero"],
                experimental["primero"],
            )
        )

        print(
            "    Fragmento esperado, original -> experimental: "
            + comparar_fragmento_esperado(
                original["esperado"],
                experimental["esperado"],
            )
        )

        resumen.append({
            "consulta": consulta,
            "original": original,
            "revisada": revisada,
            "experimental": experimental,
        })

    print("\n" + "=" * 88)
    print("RESUMEN FINAL")
    print("=" * 88)

    for caso in resumen:
        consulta = caso["consulta"]

        posiciones = []
        for nombre in ("ORIGINAL", "REVISADA", "EXPERIMENTAL"):
            esperado = caso[nombre.lower()]["esperado"]
            posicion = (
                esperado["posicion"]
                if esperado is not None
                else "N/E"
            )
            posiciones.append(f"{nombre}={posicion}")

        print(f"{consulta}: " + " | ".join(posiciones))

    print("\n" + "=" * 88)
    print("FIN DEL EXPERIMENTO")
    print("=" * 88)
    print(
        "Interpretación: las posiciones y puntuaciones son indicadores "
        "heurísticos; la pertinencia requiere revisar el contenido."
    )


if __name__ == "__main__":
    main()
