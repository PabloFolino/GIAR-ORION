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

CONSULTAS = [
    {
        "consulta": "SAC",
        "esperadas": ["algoritmo de aprendizaje por refuerzo"],
    },
    {
        "consulta": "actor",
        "esperadas": ["el actor representa la política del agente"],
    },
    {
        "consulta": "críticos",
        "esperadas": ["los críticos son redes neuronales"],
    },
    {
        "consulta": "redes objetivo",
        "esperadas": ["las redes objetivo proporcionan estimaciones"],
    },
    {
        "consulta": "Replay Buffer",
        "esperadas": ["es un búfer de reproducción de experiencias"],
    },
    {
        "consulta": "entropía",
        "esperadas": ["la entropía representa la aleatoriedad de la política"],
    },
    {
        "consulta": "temperatura",
        "esperadas": ["coeficiente controla la importancia relativa"],
    },
    {
        "consulta": "temperatura automática",
        "esperadas": ["el coeficiente se ajusta mediante un objetivo de entropía"],
    },
    {
        "consulta": "actualización de los críticos",
        "esperadas": ["la actualización de los críticos consiste en minimizar"],
    },
    {
        "consulta": "objetivo de Bellman",
        "esperadas": ["el objetivo de bellman combina la recompensa inmediata"],
    },
    {
        "consulta": "pérdida del actor",
        "esperadas": ["el actor se actualiza para favorecer acciones"],
    },
    {
        "consulta": "lotes de entrenamiento",
        "esperadas": ["selecciona lotes de transiciones del replay buffer"],
    },
    {
        "consulta": "recompensa del entorno",
        "esperadas": ["definición de la recompensa del entorno"],
    },
    {
        "consulta": "evaluar un entrenamiento",
        "esperadas": ["no basta con observar una recompensa aislada"],
    },
    {
        "consulta": "referencias bibliográficas",
        "esperadas": ["fuentes primarias correspondientes"],
    },
]


VERSIONES = [
    ("ORIGINAL", Original),
    ("REVISADA", Revisado),
    ("EXPERIMENTAL", Experimental),
]


def buscar_fragmento(retriever, consulta, esperadas):
    resultados = retriever.buscar(consulta, max_resultados=10)

    for posicion, resultado in enumerate(resultados, start=1):
        texto = resultado["text"].casefold()

        if all(frase.casefold() in texto for frase in esperadas):
            return posicion, resultado

    return None, None


def main():
    print("=" * 90)
    print("GIAR-ORION - COMPARACIÓN AMPLIADA DE KNOWLEDGE RETRIEVERS")
    print("=" * 90)
    print(f"Consultas evaluadas: {len(CONSULTAS)}")
    print("Máximo de resultados examinados por consulta: 10")
    print("No se modifican los recuperadores ni los documentos de conocimiento.")

    recuperadores = {
        nombre: clase(KNOWLEDGE_DIR)
        for nombre, clase in VERSIONES
    }

    resumen = {nombre: 0 for nombre, _ in VERSIONES}
    total_con_respuesta = {nombre: 0 for nombre, _ in VERSIONES}

    for numero, caso in enumerate(CONSULTAS, start=1):
        consulta = caso["consulta"]
        esperadas = caso["esperadas"]

        print("\n" + "-" * 90)
        print(f"PRUEBA {numero}/{len(CONSULTAS)}: {consulta}")
        print(f"Fragmento esperado: {esperadas[0]}")
        print("-" * 90)

        for nombre, _ in VERSIONES:
            retriever = recuperadores[nombre]
            resultados = retriever.buscar(consulta, max_resultados=10)

            posicion, resultado = buscar_fragmento(
                retriever,
                consulta,
                esperadas,
            )

            if resultados:
                total_con_respuesta[nombre] += 1

            if posicion is not None:
                resumen[nombre] += 1
                print(
                    f"\n{nombre}: RESPUESTA ESPERADA EN POSICIÓN "
                    f"{posicion}"
                )
                print(f"Score: {resultado['score']}")
                print(f"Texto: {resultado['text']}")
            else:
                print(f"\n{nombre}: NO SE ENCONTRÓ EL FRAGMENTO ESPERADO")

                if resultados:
                    primero = resultados[0]
                    print(f"Primer score: {primero['score']}")
                    print(f"Primer texto: {primero['text']}")
                else:
                    print("No se recuperaron resultados.")

    print("\n" + "=" * 90)
    print("RESUMEN FINAL")
    print("=" * 90)

    for nombre, _ in VERSIONES:
        aciertos = resumen[nombre]
        total = len(CONSULTAS)
        porcentaje = aciertos / total * 100

        print(
            f"{nombre}: {aciertos}/{total} respuestas esperadas encontradas "
            f"({porcentaje:.1f} %)"
        )
        print(
            f"  Consultas con resultados recuperados: "
            f"{total_con_respuesta[nombre]}/{total}"
        )

    print("\nFin de la prueba. No se modificó ningún recuperador.")


if __name__ == "__main__":
    main()

