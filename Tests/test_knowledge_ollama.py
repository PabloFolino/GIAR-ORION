import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from Agent.KnowledgeRetriever import KnowledgeRetriever


KNOWLEDGE_DIR = BASE_DIR / "Knowledge"
CONFIG_FILE = BASE_DIR / "config.json"


def cargar_configuracion():
    with open(CONFIG_FILE, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def consultar_ollama(config, consulta, contexto):
    llm = config["llm"]

    mensajes = [
        {
            "role": "system",
            "content": (
                "Sos GIAR-ORION, un asistente especializado en "
                "aprendizaje por refuerzo y robótica. "
                "Respondé utilizando prioritariamente el contexto "
                "proporcionado. No inventes información ni atribuyas "
                "al documento afirmaciones que no aparecen en él. "
                "Si el contexto no alcanza para responder, indicá "
                "qué información falta. Diferenciá los datos del "
                "contexto de cualquier explicación adicional."
            ),
        },
        {
            "role": "user",
            "content": (
                f"CONSULTA:\n{consulta}\n\n"
                f"CONTEXTO RECUPERADO:\n{contexto}\n\n"
                "Respondé la consulta de manera técnica y clara. "
                "Explicá qué indica el contexto sobre la actualización "
                "de los críticos y el objetivo temporal de Bellman."
            ),
        },
    ]

    payload = {
        "model": llm["model"],
        "messages": mensajes,
        "stream": False,
        "think": False,
        "options": {
            "num_predict": 500,
        },
    }

    url = llm["base_url"].rstrip("/") + "/api/chat"

    solicitud = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(solicitud, timeout=180) as respuesta:
        resultado = json.loads(respuesta.read().decode("utf-8"))

    mensaje = resultado.get("message", {})
    contenido = mensaje.get("content", "")

    return contenido, resultado


def main():
    print("=" * 70)
    print("GIAR-ORION - PRUEBA DE RECUPERACIÓN Y CONSULTA A OLLAMA")
    print("=" * 70)

    try:
        config = cargar_configuracion()

        buscador = KnowledgeRetriever(KNOWLEDGE_DIR)

        consulta = (
            "¿Cómo se actualizan los críticos en SAC "
            "y qué función cumple el objetivo de Bellman?"
        )

        print("\nConsulta:")
        print(consulta)

        resultados = buscador.buscar(
            consulta,
            max_resultados=3,
        )

        if not resultados:
            print("\nERROR: no se recuperó ningún fragmento.")
            return

        print("\nFragmentos recuperados:")

        for indice, resultado in enumerate(resultados, start=1):
            print(f"\n[{indice}] {resultado['source']}")
            print(f"Puntuación: {resultado['score']:.4f}")
            print(resultado["text"])

        contexto = "\n\n".join(
            f"[Fuente: {resultado['source']}]\n{resultado['text']}"
            for resultado in resultados
        )

        print("\n" + "=" * 70)
        print("CONSULTANDO A OLLAMA")
        print("=" * 70)
        print(f"Modelo: {config['llm']['model']}")
        print("Esperá a que termine la generación...")

        respuesta, datos = consultar_ollama(
            config,
            consulta,
            contexto,
        )

        if not respuesta.strip():
            print("\nADVERTENCIA: Ollama no devolvió texto.")
            print("Revisá la respuesta del modelo y su configuración.")
            return

        print("\n" + "=" * 70)
        print("RESPUESTA DE GIAR-ORION")
        print("=" * 70)
        print(respuesta)

        print("\n" + "=" * 70)
        print("MÉTRICAS DE OLLAMA")
        print("=" * 70)

        if "eval_count" in datos:
            print(f"Tokens generados: {datos['eval_count']}")

        if "prompt_eval_count" in datos:
            print(f"Tokens de entrada: {datos['prompt_eval_count']}")

        print("\nRESULTADO: recuperación y consulta completadas.")
        print("La calidad de la respuesta debe evaluarse por separado.")
        print("=" * 70)

    except FileNotFoundError as error:
        print(f"\nERROR: no se encontró un archivo: {error}")

    except KeyError as error:
        print(f"\nERROR: falta una clave en la configuración: {error}")

    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", errors="replace")
        print(f"\nERROR HTTP de Ollama: {error.code}")
        print(detalle)

    except urllib.error.URLError as error:
        print("\nERROR: no se pudo conectar con Ollama.")
        print(f"Detalle: {error.reason}")
        print("Verificá que Ollama esté ejecutándose.")

    except TimeoutError:
        print("\nERROR: se agotó el tiempo de espera de Ollama.")

    except json.JSONDecodeError as error:
        print(f"\nERROR al interpretar una respuesta JSON: {error}")

    except Exception as error:
        print(f"\nERROR inesperado: {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()

