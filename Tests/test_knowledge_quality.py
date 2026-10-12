import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from Agent.KnowledgeRetriever import KnowledgeRetriever


KNOWLEDGE_DIR = BASE_DIR / "Knowledge"

# Posición máxima aceptable del fragmento explicativo.
POSICION_MAXIMA = 3


CASOS_PRUEBA = [
    {
        "consulta": "Replay Buffer",
        "frases_esperadas": [
            "almacena las transiciones",
            "estado, la acción, la recompensa",
        ],
        "descripcion": "Función del Replay Buffer",
    },
    {
        "consulta": "actualización de los críticos",
        "frases_esperadas": [
            "minimizar una función de pérdida",
            "objetivo temporal de Bellman",
        ],
        "descripcion": "Actualización de los críticos",
    },
    {
        "consulta": "temperatura automática",
        "frases_esperadas": [
            "coeficiente se ajusta",
            "objetivo de entropía",
        ],
        "descripcion": "Ajuste automático de temperatura",
    },
    {
        "consulta": "redes objetivo",
        "frases_esperadas": [
            "redes objetivo",
            "estimaciones más estables",
        ],
        "descripcion": "Función de las redes objetivo",
    },
]


def normalizar(texto: str) -> str:
    return " ".join(texto.casefold().split())


def main():
    buscador = KnowledgeRetriever(KNOWLEDGE_DIR)

    aprobados = 0
    total = len(CASOS_PRUEBA)

    print("=" * 70)
    print("GIAR-ORION - EVALUACIÓN DE CALIDAD DE RECUPERACIÓN")
    print("=" * 70)
    print(f"Posición máxima aceptable: {POSICION_MAXIMA}")
    print("Criterio: todas las frases esperadas deben aparecer")
    print("en un mismo fragmento recuperado.")

    for caso in CASOS_PRUEBA:
        consulta = caso["consulta"]
        frases_esperadas = caso["frases_esperadas"]

        resultados = buscador.buscar(
            consulta,
            max_resultados=10,
        )

        posicion_relevante = None
        frases_encontradas = []

        # Buscar un único fragmento que contenga todas
        # las frases necesarias para explicar el concepto.
        for indice, resultado in enumerate(resultados, start=1):
            texto = normalizar(resultado["text"])

            encontradas = [
                frase
                for frase in frases_esperadas
                if normalizar(frase) in texto
            ]

            if len(encontradas) == len(frases_esperadas):
                posicion_relevante = indice
                frases_encontradas = encontradas
                break

        contenido_aprobado = posicion_relevante is not None

        posicion_aprobada = (
            posicion_relevante is not None
            and posicion_relevante <= POSICION_MAXIMA
        )

        aprobado = contenido_aprobado and posicion_aprobada

        if aprobado:
            aprobados += 1

        print("\n" + "-" * 70)
        print(f"Prueba: {caso['descripcion']}")
        print(f"Consulta: {consulta}")

        print(
            "Contenido explicativo: "
            f"{'APROBADO' if contenido_aprobado else 'REVISAR'}"
        )

        print(
            "Frases encontradas: "
            f"{len(frases_encontradas)}/{len(frases_esperadas)}"
        )

        if posicion_relevante is None:
            print("Posición del fragmento explicativo: no encontrado")
        else:
            print(
                "Posición del fragmento explicativo: "
                f"{posicion_relevante}"
            )

        print(
            "Posición: "
            f"{'APROBADA' if posicion_aprobada else 'REVISAR'}"
        )

        print(f"Estado general: {'APROBADA' if aprobado else 'REVISAR'}")

        if resultados:
            for indice, resultado in enumerate(resultados, start=1):
                texto = normalizar(resultado["text"])

                contiene_todas = all(
                    normalizar(frase) in texto
                    for frase in frases_esperadas
                )

                marca = (
                    " <-- EXPLICACION ESPERADA"
                    if contiene_todas
                    else ""
                )

                print(f"\n  Resultado {indice}{marca}")
                print(f"  Puntuación: {resultado['score']:.4f}")
                print(f"  Texto: {resultado['text']}")
        else:
            print("No se encontraron resultados.")

    print("\n" + "=" * 70)
    print(f"RESULTADO: {aprobados}/{total} pruebas aprobadas")
    print("=" * 70)


if __name__ == "__main__":
    main()