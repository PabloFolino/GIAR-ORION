# GIAR-ORION — Módulos Python

**Tipo:** inventario inicial de módulos y responsabilidades.  
**Estado:** parcial; solo se afirma lo respaldado por la información disponible.

## 1. `main.py`

**Responsabilidad conocida:** punto de entrada conversacional y coordinación de solicitudes al modelo local.

Comportamientos observados durante el desarrollo:

- Presenta la interfaz de consola.
- Ofrece comandos como `/salir`, `/limpiar`, `/guardar`, `/sesiones`, `/modo rapido` y `/modo investigacion`.
- Prepara mensajes para Ollama.
- Obtiene parámetros de generación del modo seleccionado.
- Construye una solicitud a la API de chat de Ollama.
- Recibe el contenido y los metadatos de la respuesta.
- En una versión instrumentada para diagnóstico, muestra datos como duración, cantidad de tokens y `done_reason`.

La función `consultar_ollama` observada construye un payload con el modelo, `messages`, `stream`, `think` y `options.num_predict`.

**Pendiente de verificar:** firmas completas, manejo de excepciones, persistencia de sesiones, construcción exacta del contexto RAG y ubicación de la presentación de fuentes.

## 2. `Agent/MultilingualKnowledgeRetriever.py`

**Responsabilidad conocida:** recuperación de fragmentos de la base documental con embeddings multilingües y modo híbrido.

Elementos conocidos:

- Multilingual E5.
- BGE-M3.
- Combinación híbrida ponderada según configuración.
- Selección de una cantidad limitada de fragmentos por consulta.
- Caché persistente de embeddings documentales.

Archivos de caché conocidos en `Cache`:

- `e5_embeddings.npy`
- `bge_embeddings.npy`
- `metadata.json`

**Pendiente de verificar en el código:** nombres y firmas de todos los métodos, algoritmo exacto de similitud, normalización, estrategia de fragmentación, filtros, tratamiento de documentos nuevos, validación de caché y fórmula exacta de combinación.

La calidad del recuperador debe evaluarse por la pertinencia de los fragmentos, no solo por el número de resultados o el tiempo de ejecución.

## 3. `config.json`

Aunque no es Python, es parte central de la configuración. Contiene parámetros del modelo, modos de generación y ajustes del RAG, como modo, `top_k`, dispositivo, presentación de fuentes y pesos de E5/BGE-M3.

Los valores pueden cambiar. Para conocerlos hay que leer el archivo que está en uso.

## 4. Ollama

Ollama es el servicio local que ejecuta el modelo de lenguaje; no es un módulo Python propio del proyecto.

Datos conocidos:

- Endpoint: `http://localhost:11434`.
- Modelo usado durante las pruebas: `qwen3:8b`.
- La solicitud de chat se construye en `main.py`.

El servicio, el modelo cargado y los parámetros efectivos deben comprobarse en tiempo de ejecución.

## 5. `Knowledge`

Es el directorio de documentos que alimenta la recuperación RAG. No es un módulo Python. Contiene documentación técnica sobre temas como RL, SAC, Unitree G1 y CoppeliaSim. El contenido real puede cambiar con nuevas incorporaciones.

## 6. `Tests`

Contiene scripts y resultados de pruebas. Se han realizado evaluaciones de rankings de recuperación con salidas CSV y JSON.

Una prueba con `generation_enabled=false` permite evaluar la selección de fragmentos, pero no determina si Qwen generaría una respuesta completa o correcta.

Hay que inspeccionar cada script antes de asumir qué mide.

## 7. `Cache`

Contiene la caché persistente de embeddings. No sustituye a `Knowledge`: los documentos fuente siguen siendo la base documental.

## 8. Componentes pendientes de inventariar

La información disponible no permite describir de forma fiable todos los archivos, clases, funciones, dependencias, interfaces ni secuencias de llamadas del proyecto.

En una futura etapa de análisis de código conviene registrar por archivo Python:

- Ruta relativa.
- Propósito.
- Clases y funciones.
- Importaciones propias y externas.
- Entradas y salidas.
- Configuración leída.
- Llamadas a otros módulos.
- Pruebas relacionadas.
- Estado y fecha de verificación.

No deben inventarse nombres de módulos ni responsabilidades sin inspeccionar el código vigente.
