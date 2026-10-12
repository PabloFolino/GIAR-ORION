import sys
from pathlib import Path


# Obtener la raíz del proyecto GIAR-ORION.
BASE_DIR = Path(__file__).resolve().parent.parent

# Incorporar la raíz del proyecto a las rutas de importación.
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from Agent.KnowledgeRetriever import KnowledgeRetriever


KNOWLEDGE_DIR = BASE_DIR / "Knowledge"


def main():
    buscador = KnowledgeRetriever(KNOWLEDGE_DIR)

    consultas = [
        "entropía",
        "críticos",
        "Replay Buffer",
    ]

    for consulta in consultas:
        print("\n" + "=" * 60)
        print(f"CONSULTA: {consulta}")
        print("=" * 60)

        resultados = buscador.buscar(
            consulta,
            max_resultados=3,
        )

        if not resultados:
            print("No se encontraron coincidencias.")
            continue

        for indice, resultado in enumerate(resultados, start=1):
            print(f"\nResultado {indice}")
            print(f"Fuente: {resultado['source']}")
            print(f"Puntuación: {resultado['score']:.2f}")
            print(
                "Coincidencias: "
                f"{', '.join(resultado['matched_terms'])}"
            )
            print(f"Texto: {resultado['text']}")


if __name__ == "__main__":
    main()

