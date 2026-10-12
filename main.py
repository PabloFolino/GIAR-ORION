import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


# ============================================================
# GIAR-ORION - Agente local de IA
# Versión 0.2
# Memoria de conversaciones
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"


def cargar_configuracion() -> dict:
    """Carga y valida la configuración de GIAR-ORION."""

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {CONFIG_FILE}"
        )

    with CONFIG_FILE.open("r", encoding="utf-8") as archivo:
        config = json.load(archivo)

    for campo in ("agent_name", "version", "llm", "paths"):
        if campo not in config:
            raise ValueError(
                f"Falta el campo '{campo}' en config.json."
            )

    llm = config["llm"]

    for campo in (
        "provider",
        "model",
        "base_url",
        "system_prompt",
    ):
        if campo not in llm:
            raise ValueError(
                f"Falta el campo 'llm.{campo}' en config.json."
            )

    if llm["provider"].lower() != "ollama":
        raise ValueError(
            "Esta versión de GIAR-ORION utiliza Ollama."
        )

    if "generation" not in config:
        raise ValueError(
            "Falta la sección 'generation' en config.json."
        )

    generation = config["generation"]

    if "modes" not in generation:
        raise ValueError(
            "Falta 'generation.modes' en config.json."
        )

    modes = generation["modes"]

    if not modes:
        raise ValueError(
            "Debe existir al menos un modo de generación."
        )

    for nombre, parametros in modes.items():
        if (
            "think" not in parametros
            or "num_predict" not in parametros
        ):
            raise ValueError(
                f"El modo '{nombre}' debe definir "
                "'think' y 'num_predict'."
            )

        if not isinstance(parametros["think"], bool):
            raise ValueError(
                f"'think' debe ser booleano en el modo '{nombre}'."
            )

        if (
            not isinstance(parametros["num_predict"], int)
            or parametros["num_predict"] <= 0
        ):
            raise ValueError(
                f"'num_predict' debe ser un entero positivo "
                f"en el modo '{nombre}'."
            )

    modo_inicial = generation.get("default_mode")

    if modo_inicial not in modes:
        raise ValueError(
            f"El modo inicial '{modo_inicial}' no está definido."
        )

    if "memory" not in config["paths"]:
        raise ValueError(
            "Falta 'paths.memory' en config.json."
        )

    return config


def consultar_ollama(
    config: dict,
    mensajes: list[dict],
    modo: str,
) -> tuple[str, dict]:
    """Consulta Ollama con los parámetros del modo seleccionado."""

    llm = config["llm"]
    parametros = config["generation"]["modes"][modo]

    url = f"{llm['base_url'].rstrip('/')}/api/chat"

    payload = {
        "model": llm["model"],
        "messages": mensajes,
        "stream": False,
        "think": parametros["think"],
        "options": {
            "num_predict": parametros["num_predict"]
        },
    }

    datos = json.dumps(payload).encode("utf-8")

    solicitud = urllib.request.Request(
        url,
        data=datos,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            solicitud,
            timeout=300,
        ) as respuesta_http:
            resultado = json.loads(
                respuesta_http.read().decode("utf-8")
            )

    except urllib.error.HTTPError as error:
        detalle = error.read().decode(
            "utf-8",
            errors="replace",
        )
        raise RuntimeError(
            f"Ollama devolvió HTTP {error.code}: {detalle}"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            "No se pudo conectar con Ollama. "
            "Verificá que el servicio esté funcionando."
        ) from error

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Ollama devolvió una respuesta JSON inválida."
        ) from error

    mensaje = resultado.get("message")

    if not isinstance(mensaje, dict) or "content" not in mensaje:
        raise RuntimeError(
            "La respuesta de Ollama no contiene el texto esperado."
        )

    return mensaje["content"], resultado


def obtener_directorio_memoria(config: dict) -> Path:
    """Obtiene la ruta de memoria y crea el directorio si hace falta."""

    directorio = BASE_DIR / config["paths"]["memory"]
    return directorio / "Conversations"


def guardar_conversacion(
    config: dict,
    mensajes: list[dict],
) -> Path | None:
    """Guarda una conversación en un archivo JSON local."""

    # No guardar la instrucción interna del sistema.
    conversacion = [
        mensaje
        for mensaje in mensajes
        if mensaje.get("role") in ("user", "assistant")
    ]

    if not conversacion:
        print(
            "GIAR-ORION: No hay mensajes para guardar."
        )
        return None

    directorio = obtener_directorio_memoria(config)
    directorio.mkdir(parents=True, exist_ok=True)

    fecha = datetime.now().astimezone()
    marca_tiempo = fecha.strftime("%Y%m%d_%H%M%S")

    nombre_archivo = f"conversacion_{marca_tiempo}.json"
    ruta_archivo = directorio / nombre_archivo

    # Evitar sobrescribir una sesión si coinciden los nombres.
    contador = 1

    while ruta_archivo.exists():
        nombre_archivo = (
            f"conversacion_{marca_tiempo}_{contador}.json"
        )
        ruta_archivo = directorio / nombre_archivo
        contador += 1

    datos = {
        "agent_name": config["agent_name"],
        "agent_version": config["version"],
        "model": config["llm"]["model"],
        "saved_at": fecha.isoformat(timespec="seconds"),
        "message_count": len(conversacion),
        "messages": conversacion,
    }

    with ruta_archivo.open("w", encoding="utf-8") as archivo:
        json.dump(
            datos,
            archivo,
            ensure_ascii=False,
            indent=4,
        )
        archivo.write("\n")

    print("\nGIAR-ORION: Conversación guardada correctamente.")
    print(f"Archivo: {ruta_archivo}")
    print(f"Mensajes guardados: {len(conversacion)}")

    return ruta_archivo


def listar_conversaciones(config: dict) -> None:
    """Muestra las conversaciones guardadas."""

    directorio = obtener_directorio_memoria(config)

    if not directorio.exists():
        print(
            "\nGIAR-ORION: Todavía no hay conversaciones guardadas."
        )
        return

    archivos = sorted(
        directorio.glob("conversacion_*.json"),
        reverse=True,
    )

    if not archivos:
        print(
            "\nGIAR-ORION: Todavía no hay conversaciones guardadas."
        )
        return

    print("\nCONVERSACIONES GUARDADAS")
    print("-" * 60)

    for indice, archivo in enumerate(archivos, start=1):
        try:
            with archivo.open("r", encoding="utf-8") as entrada:
                datos = json.load(entrada)

            fecha = datos.get("saved_at", "Fecha desconocida")
            cantidad = datos.get("message_count", 0)

            print(f"{indice}. {archivo.name}")
            print(f"   Fecha: {fecha}")
            print(f"   Mensajes: {cantidad}")

        except (OSError, json.JSONDecodeError):
            print(f"{indice}. {archivo.name} [No se pudo leer]")

    print("-" * 60)
    print(f"Total de conversaciones: {len(archivos)}")

def recuperar_conversacion(
    config: dict,
    numero: int,
) -> list[dict] | None:
    """Recupera los mensajes de una conversación guardada."""

    directorio = obtener_directorio_memoria(config)

    if not directorio.exists():
        print("GIAR-ORION: No hay conversaciones guardadas.")
        return None

    archivos = sorted(
        directorio.glob("conversacion_*.json"),
        reverse=True,
    )

    if numero < 1 or numero > len(archivos):
        print(
            f"GIAR-ORION: Número de sesión inválido. "
            f"Hay {len(archivos)} conversaciones disponibles."
        )
        return None

    ruta = archivos[numero - 1]

    try:
        with ruta.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

    except (OSError, json.JSONDecodeError) as error:
        print(f"GIAR-ORION: No se pudo recuperar la sesión: {error}")
        return None

    mensajes = datos.get("messages")

    if not isinstance(mensajes, list):
        print("GIAR-ORION: El archivo no contiene una conversación válida.")
        return None

    mensajes_validos = []

    for mensaje in mensajes:
        if (
            isinstance(mensaje, dict)
            and mensaje.get("role") in ("user", "assistant")
            and isinstance(mensaje.get("content"), str)
        ):
            mensajes_validos.append({
                "role": mensaje["role"],
                "content": mensaje["content"],
            })

    if not mensajes_validos:
        print("GIAR-ORION: La conversación no contiene mensajes válidos.")
        return None

    print("\nGIAR-ORION: Conversación recuperada.")
    print(f"Archivo: {ruta.name}")
    print(f"Mensajes cargados: {len(mensajes_validos)}")

    return mensajes_validos

def iniciar_agente(config: dict) -> None:
    """Ejecuta la interfaz conversacional."""

    nombre = config["agent_name"]
    version = config["version"]
    modelo = config["llm"]["model"]
    modos = config["generation"]["modes"]

    modo = config["generation"]["default_mode"]

    mensajes = [
        {
            "role": "system",
            "content": config["llm"]["system_prompt"],
        }
    ]

    print()
    print("=" * 60)
    print(f"{nombre} - Versión {version}")
    print("Inteligencia artificial para investigación y desarrollo")
    print("en robótica autónoma")
    print("=" * 60)

    print(f"Proveedor: {config['llm']['provider']}")
    print(f"Modelo: {modelo}")
    print(f"Modo inicial: {modo}")
    print(f"Servicio: {config['llm']['base_url']}")
    print()
    print("Comandos disponibles:")
    print("  /salir                 Finalizar la sesión")
    print("  /limpiar               Borrar el historial de la sesión")
    print("  /guardar               Guardar la conversación actual")
    print("  /sesiones              Listar conversaciones guardadas")
    print("  /modo rapido           Activar el modo rápido")
    print("  /modo investigacion    Activar el modo de investigación")
    print("-" * 60)

    while True:
        try:
            pregunta = input("\nVos: ").strip()

        except (EOFError, KeyboardInterrupt):
            print(f"\n\n{nombre}: Sesión finalizada.")
            break

        if not pregunta:
            continue

        comando = pregunta.lower()

        if comando == "/salir":
            print(f"\n{nombre}: Hasta la próxima.")
            break

        if comando == "/sesiones":
            listar_conversaciones(config)
            continue

        if comando.startswith("/abrir"): 
            partes = comando.split() 
            if len(partes) != 2 or not partes[1].isdigit(): 
                print("Uso correcto: /abrir N") 
                continue 
            numero = int(partes[1]) 
            mensajes_recuperados = recuperar_conversacion( config, numero, ) 
            if mensajes_recuperados is not None: 
                mensajes = [ mensajes[0:0] ]  if False else mensajes[:1] 
                mensajes.extend(mensajes_recuperados) 
            continue


        if comando == "/limpiar":
            mensajes = mensajes[:1]
            print(
                f"{nombre}: Se borró el historial de esta sesión. "
                "Las conversaciones guardadas no se modificaron."
            )
            continue

        if comando == "/guardar":
            try:
                guardar_conversacion(config, mensajes)
            except OSError as error:
                print(f"Error al guardar la conversación: {error}")
            continue

        if comando == "/sesiones":
            listar_conversaciones(config)
            continue

        if comando.startswith("/modo"):
            partes = comando.split(maxsplit=1)

            if len(partes) != 2:
                print(f"Modos disponibles: {', '.join(modos)}")
                continue

            nuevo_modo = partes[1]

            if nuevo_modo not in modos:
                print(
                    f"Modo desconocido: {nuevo_modo}. "
                    f"Disponibles: {', '.join(modos)}"
                )
                continue

            modo = nuevo_modo
            print(f"{nombre}: Modo cambiado a '{modo}'.")
            continue

        mensajes.append({
            "role": "user",
            "content": pregunta,
        })

        print(f"\n{nombre} [{modo}]: pensando...\n")

        try:
            respuesta, resultado = consultar_ollama(
                config,
                mensajes,
                modo,
            )

        except RuntimeError as error:
            mensajes.pop()
            print(f"Error: {error}")
            continue

        mensajes.append({
            "role": "assistant",
            "content": respuesta,
        })

        print(respuesta)

        if "total_duration" in resultado:
            segundos = (
                resultado["total_duration"] / 1_000_000_000
            )
            print(f"\n[Tiempo total: {segundos:.2f} s]")

        if "eval_count" in resultado:
            print(
                f"[Tokens generados: {resultado['eval_count']}]"
            )


def main() -> None:
    """Punto de entrada de GIAR-ORION."""

    try:
        config = cargar_configuracion()
        iniciar_agente(config)

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
    ) as error:
        print(f"Error de configuración: {error}")


if __name__ == "__main__":
    main()

