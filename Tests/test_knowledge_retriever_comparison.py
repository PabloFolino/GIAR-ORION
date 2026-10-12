import importlib.util
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
AGENT_DIR = BASE_DIR / "Agent"
KNOWLEDGE_DIR = BASE_DIR / "Knowledge"

ARCHIVO_ORIGINAL = AGENT_DIR / "KnowledgeRetriever.py"
ARCHIVO_REVISADO = AGENT_DIR / "KnowledgeRetriever_revisado.py"

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


def cargar_clase(archivo, nombre_modulo):
    if not archivo.is_file():
        raise FileNotFoundError(
            f"No se encontró {archivo}\n"
            "Copiá KnowledgeRetriever_revisado.py dentro de Agent "
            "sin reemplazar KnowledgeRetriever.py."
        )

    spec = importlib.util.spec_from_file_location(nombre_modulo, archivo)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar el módulo: {archivo}")

    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre_modulo] = modulo
    spec.loader.exec_module(modulo)
    return modulo.KnowledgeRetriever


def normalizar(texto):
    return " ".join(texto.casefold().split())


def evaluar_resultados(resultados, frases_esperadas):
    frases = [normalizar(frase) for frase in frases_esperadas]

    for posicion, resultado in enumerate(resultados, start=1):
        texto = normalizar(resultado["text"])
        if all(frase in texto for frase in frases):
            return posicion, resultado

    return None, None


def imprimir_resultados(etiqueta, resultados, frases_esperadas):
    posicion_objetivo, fragmento_objetivo = evaluar_resultados(
        resultados, frases_esperadas
    )

    print(f"\n{etiqueta}:")
    if posicion_objetivo is None:
        print("  No se encontró un fragmento con todas las frases esperadas.")
    else:
        print(
            f"  Posición de la explicación esperada: {posicion_objetivo}"
            f" | puntuación: {fragmento_objetivo['score']:.4f}"
        )

    print("  Primeros 3 resultados:")
    for indice, resultado in enumerate(resultados[:3], start=1):
        texto = resultado["text"]
        if len(texto) > 230:
            texto = texto[:227] + "..."
        print(
            f"    {indice}. score={resultado['score']:.4f} | {texto}"
        )

    return posicion_objetivo, fragmento_objetivo


def main():
    print("=" * 78)
    print("GIAR-ORION - COMPARACIÓN CONTROLADA DEL KNOWLEDGE RETRIEVER")
    print("=" * 78)
    print("La prueba no modifica el módulo original ni los tests existentes.")
    print(f"Conocimiento evaluado: {KNOWLEDGE_DIR}")

    if not KNOWLEDGE_DIR.is_dir():
        print(f"\nERROR: no existe el directorio: {KNOWLEDGE_DIR}")
        return

    try:
        ClaseOriginal = cargar_clase(
            ARCHIVO_ORIGINAL, "retriever_original_comparacion"
        )
        ClaseRevisada = cargar_clase(
            ARCHIVO_REVISADO, "retriever_revisado_comparacion"
        )
        original = ClaseOriginal(KNOWLEDGE_DIR)
        revisado = ClaseRevisada(KNOWLEDGE_DIR)
    except (FileNotFoundError, ImportError, OSError) as error:
        print(f"\nERROR: {error}")
        return

    resumen = []

    for numero, caso in enumerate(CASOS_PRUEBA, start=1):
        print("\n" + "-" * 78)
        print(f"PRUEBA {numero}: {caso['descripcion']}")
        print(f"Consulta: {caso['consulta']}")

        resultados_originales = original.buscar(
            caso["consulta"], max_resultados=10
        )
        resultados_revisados = revisado.buscar(
            caso["consulta"], max_resultados=10
        )

        pos_original, frag_original = imprimir_resultados(
            "VERSIÓN ORIGINAL",
            resultados_originales,
            caso["frases_esperadas"],
        )
        pos_revisado, frag_revisado = imprimir_resultados(
            "VERSIÓN REVISADA",
            resultados_revisados,
            caso["frases_esperadas"],
        )

        if pos_original is None or pos_revisado is None:
            cambio = "NO COMPARABLE: falta la explicación esperada"
        elif pos_revisado < pos_original:
            cambio = f"MEJORA: sube de posición {pos_original} a {pos_revisado}"
        elif pos_revisado > pos_original:
            cambio = f"REGRESIÓN: baja de posición {pos_original} a {pos_revisado}"
        else:
            cambio = f"SIN CAMBIO DE POSICIÓN: permanece en {pos_revisado}"

        print(f"\n  COMPARACIÓN: {cambio}")
        resumen.append((caso["descripcion"], pos_original, pos_revisado, cambio))

    print("\n" + "=" * 78)
    print("RESUMEN COMPARATIVO")
    print("=" * 78)
    for descripcion, original_pos, revisado_pos, cambio in resumen:
        print(
            f"- {descripcion}: original={original_pos}, "
            f"revisado={revisado_pos} -> {cambio}"
        )

    mejoras = sum(
        1 for _, original_pos, revisado_pos, _ in resumen
        if original_pos is not None
        and revisado_pos is not None
        and revisado_pos < original_pos
    )
    regresiones = sum(
        1 for _, original_pos, revisado_pos, _ in resumen
        if original_pos is not None
        and revisado_pos is not None
        and revisado_pos > original_pos
    )

    print(f"\nMejoras de posición: {mejoras}")
    print(f"Regresiones de posición: {regresiones}")
    print("No se acepta ni rechaza el cambio automáticamente.")
    print("La decisión requiere revisar este resultado y ejecutar los tests.")
    print("=" * 78)


if __name__ == "__main__":
    main()
