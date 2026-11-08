# GIAR-ORION-AUDIT-SPEC-001
## Especificación de auditoría integral y relevamiento de arquitectura

| Campo | Valor |
|---|---|
| Proyecto | GIAR-ORION |
| Documento | GIAR-ORION-AUDIT-SPEC-001.md |
| Versión | 0.4 — Relevamiento de la interfaz principal |
| Fecha | 2026-11-08 |
| Estado | En revisión: arquitectura parcialmente relevada |
| Tipo | Especificación de auditoría no intrusiva |

## Índice

- [1. Propósito](#1-propósito)
- [2. Alcance y exclusiones](#2-alcance-y-exclusiones)
  - [2.1 Incluido](#21-incluido)
  - [2.2 Excluido](#22-excluido)
- [3. Sistema GIAR-ORION](#3-sistema-giar-orion)
  - [3.1 Descripción general del sistema](#31-descripción-general-del-sistema)
  - [3.2 Objetivo del sistema](#32-objetivo-del-sistema)
  - [3.3 Arquitectura general](#33-arquitectura-general)
  - [3.4 Estado de relevamiento de la arquitectura](#34-estado-de-relevamiento-de-la-arquitectura)
    - [3.4.1 Consideraciones para interpretar el estado](#341-consideraciones-para-interpretar-el-estado)
    - [3.4.2 Próximo tramo del relevamiento](#342-próximo-tramo-del-relevamiento)
  - [3.5 Relevamiento de componentes](#35-relevamiento-de-componentes)
    - [3.5.1 Interfaz principal: `main_multilinea.py`](#351-interfaz-principal-main_multilineapy)
- [4. Modelo de arquitectura a verificar](#4-modelo-de-arquitectura-a-verificar)
- [5. Relevamiento paso a paso del sistema](#5-relevamiento-paso-a-paso-del-sistema)
- [6. Diseño experimental](#6-diseño-experimental)
- [7. Métricas](#7-métricas)
- [8. Atribución de errores y propagación](#8-atribución-de-errores-y-propagación)
- [9. Ejecución y estados](#9-ejecución-y-estados)
- [10. Estructura de archivos propuesta](#10-estructura-de-archivos-propuesta)
- [11. Reproducibilidad y preservación](#11-reproducibilidad-y-preservación)
- [12. Criterios de aceptación de la auditoría](#12-criterios-de-aceptación-de-la-auditoría)
- [13. Plan de trabajo y avance](#13-plan-de-trabajo-y-avance)
- [14. Próximo paso concreto](#14-próximo-paso-concreto)
- [Anexo A — Verificación del repositorio público](#anexo-a--verificación-del-repositorio-público)

---

## 1. Propósito

Definir una auditoría reproducible que mida, en una única ejecución controlada, el comportamiento de:

1. Recuperación documental RAG.
2. `ClaimExtractor`.
3. `EvidenceVerifier`.
4. Generación de Qwen3.
5. Pipeline integral de GIAR-ORION.

La auditoría debe determinar qué funciona, cuánto funciona, dónde se producen los errores y cómo se propagan entre componentes. No debe modificar el comportamiento del agente evaluado.

**Principio rector:** la auditoría observa y registra. No corrige, reemplaza, ajusta ni reconfigura los componentes de GIAR-ORION durante una ejecución.

## 2. Alcance y exclusiones

### 2.1 Incluido

- Relevamiento de la estructura real del repositorio.
- Identificación de módulos efectivamente importados por la interfaz principal.
- Registro de parámetros y versiones.
- Evaluación aislada de componentes y evaluación integrada.
- Dataset de referencia independiente.
- Métricas, trazabilidad por caso e informes reproducibles.
- Comparación entre ejecuciones sin sobrescribir resultados anteriores.

### 2.2 Excluido

- Modificar `main_multilinea.py` o cualquier módulo original.
- Reemplazar el recuperador RAG.
- Cambiar el modelo, los parámetros de generación o el prompt de producción.
- Modificar umbrales o reglas internas de `EvidenceVerifier`.
- Entrenar o ajustar modelos durante la auditoría.
- Considerar que un módulo funciona correctamente solo porque importa o devuelve una salida.

La auditoría podrá crear archivos propios dentro de `AUDIT/`, pero no escribirá sobre los archivos de producción.

## 3. Sistema GIAR-ORION

### 3.1. Descripción general del sistema

GIAR-ORION es un agente de inteligencia artificial desarrollado como entorno de asistencia para tareas de investigación, análisis y desarrollo tecnológico, con especial orientación hacia la robótica, la inteligencia artificial y los métodos de aprendizaje automático, particularmente el aprendizaje por refuerzo y el aprendizaje profundo por refuerzo.

El sistema combina un modelo de lenguaje de gran tamaño (LLM), mecanismos de recuperación de información documental (RAG), fuentes de información externas y componentes destinados a analizar y verificar las afirmaciones presentes en las respuestas generadas.

La implementación relevada utiliza Ollama como servicio local para ejecutar el modelo de lenguaje Qwen3 (`qwen3:8b`, según la configuración consultada). El componente RAG permite recuperar fragmentos de la base documental del proyecto y aportar ese material como contexto a la generación. La interfaz también contempla modalidades de consulta que incorporan búsqueda web, según la fuente seleccionada por el usuario.

GIAR-ORION no debe entenderse únicamente como un chatbot. Su propósito técnico es integrar recuperación de conocimiento, generación de respuestas y mecanismos de verificación, de modo que las respuestas puedan relacionarse con información documental y evidencias identificables.

Esta descripción resume el diseño y los componentes identificados. No implica que todas las funciones se ejecuten en cada consulta ni que la eficacia de cada componente ya haya sido demostrada. Esas cuestiones forman parte del relevamiento y de la auditoría definidos en este documento.

### 3.2. Objetivo del sistema

El objetivo general de GIAR-ORION es proporcionar un agente de apoyo a la investigación y al desarrollo en robótica e inteligencia artificial que pueda utilizar documentación técnica, analizar problemas, asistir en tareas de programación y experimentación, y elaborar respuestas fundamentadas en las fuentes de información disponibles.

En particular, el sistema busca:

1. **Asistir en la investigación técnica:** ayudar a estudiar algoritmos, arquitecturas, modelos, artículos, documentación y repositorios vinculados con inteligencia artificial y robótica.
2. **Recuperar conocimiento documental:** localizar información relevante en la base de conocimiento del proyecto y utilizarla como contexto para responder consultas.
3. **Integrar fuentes de información:** permitir, de acuerdo con la modalidad seleccionada, el uso de documentación local y de resultados obtenidos mediante búsqueda web.
4. **Analizar y explicar información:** producir respuestas que organicen conceptos, describan procedimientos, comparen alternativas y ayuden a interpretar resultados técnicos.
5. **Asistir en el desarrollo de software:** colaborar en la comprensión, revisión, depuración y desarrollo de programas relacionados con los proyectos de investigación.
6. **Verificar afirmaciones:** identificar afirmaciones factuales en las respuestas y contrastarlas con evidencias, distinguiendo entre información respaldada, contradicha o insuficiente.
7. **Mantener trazabilidad:** facilitar la identificación de las fuentes utilizadas y de los resultados del proceso de verificación, en la medida en que los componentes actuales lo permitan.

Desde el punto de vista de esta auditoría, el objetivo no es determinar si GIAR-ORION cumple idealmente todas esas aspiraciones, sino medir experimentalmente en qué grado las cumple en su versión actual. Por ello, cada capacidad deberá asociarse con pruebas, referencias independientes y métricas específicas.

### 3.3. Arquitectura general

La arquitectura de GIAR-ORION está organizada alrededor de una interfaz principal que coordina la interacción con el usuario y conecta los componentes de recuperación, generación y verificación.

El punto de entrada vigente para las pruebas del proyecto es `main_multilinea.py`. En el relevamiento realizado sobre la rama pública `main` del repositorio se identificó que esta interfaz inicializa el recuperador RAG, el buscador web y una instancia de `ClaimVerificationPipeline`. También se observó que construye un contexto temporal a partir de las fuentes seleccionadas y lo incorpora a los mensajes enviados al servicio Ollama.

A nivel funcional, los componentes identificados cumplen los siguientes roles:

- **Interfaz principal (`main_multilinea.py`):** recibe las consultas, administra la interacción, inicializa los componentes y coordina la preparación de la información que se envía al modelo.
- **Recuperación documental RAG (`Agent/MultilingualKnowledgeRetriever.py`):** busca fragmentos relevantes en la base de conocimiento local y devuelve resultados que pueden utilizarse como evidencia contextual.
- **Búsqueda web (`Agent/WebSearch.py` o módulo efectivamente importado):** obtiene información externa cuando la modalidad de fuentes seleccionada habilita esa búsqueda. Debe analizarse separadamente del RAG local.
- **Construcción del contexto:** reúne la consulta y los fragmentos recuperados para preparar el contenido que recibe el modelo. En la interfaz se identificó la función `construir_contexto_rag(...)`; también existe una construcción diferenciada del contexto web.
- **Servicio de generación (Ollama / Qwen3):** recibe los mensajes y el contexto preparado, y genera la respuesta destinada al usuario.
- **Extracción de afirmaciones (`Agent/ClaimExtractor.py`):** identifica afirmaciones factuales dentro de un texto de respuesta. Su función es extraerlas; no debe confundirse con determinar si son verdaderas.
- **Verificación de evidencias (`Agent/EvidenceVerifier.py`):** contrasta las afirmaciones con las evidencias disponibles y produce una clasificación de respaldo, contradicción o insuficiencia, de acuerdo con la implementación efectiva.
- **Coordinación de la verificación (`Agent/ClaimVerificationPipeline.py`):** organiza el proceso de extracción y verificación. Su secuencia interna, reglas de agregación y contrato de entrada/salida deben confirmarse mediante inspección del código.
- **Presentación de resultados:** la interfaz contiene una función específica para mostrar el informe de verificación. Debe comprobarse qué información del pipeline llega efectivamente a la presentación final.

El esquema siguiente representa los bloques funcionales identificados. Las conexiones entre generación, pipeline y presentación son provisionales hasta completar el seguimiento de las llamadas reales en el código.

```text
                         USUARIO
                            |
                            v
                   main_multilinea.py
                     INTERFAZ PRINCIPAL
                            |
              +-------------+-------------+
              |                           |
              v                           v
       Recuperación RAG              Búsqueda web
       base documental               (según fuente)
              |                           |
              +-------------+-------------+
                            |
                            v
                Construcción del contexto
                            |
                            v
                      Ollama / Qwen3
                            |
                            v
                    Respuesta generada
                            |
                            v
              ClaimVerificationPipeline
                            |
                  +---------+---------+
                  |                   |
                  v                   v
             ClaimExtractor     EvidenceVerifier
                  |                   |
                  +---------+---------+
                            |
                            v
                 Informe de verificación
                            |
                            v
                   Presentación al usuario
```

**Alcance de lo confirmado:** la inspección de `main_multilinea.py` en la rama pública `main` permitió confirmar la importación e inicialización del pipeline, la inicialización del recuperador RAG y del buscador DDGS, la selección de modalidades de fuentes (`local`, `web` y `autorizada`), la construcción del contexto temporal y la existencia de una función para presentar el informe de verificación.

**Aspectos todavía pendientes:** falta completar el seguimiento de la llamada efectiva al método del pipeline, verificar el orden exacto de las operaciones posteriores a la generación, inspeccionar el funcionamiento interno de `ClaimVerificationPipeline.py`, y confirmar los contratos reales de `ClaimExtractor.py` y `EvidenceVerifier.py`. Por ese motivo, el diagrama es una representación funcional provisional y no una secuencia de ejecución completamente certificada.

### 3.4. Estado de relevamiento de la arquitectura

Esta sección registra qué elementos fueron identificados, qué función cumplen dentro del diseño y cuál es el grado de confirmación alcanzado. Se diferencia la existencia o inicialización de un componente de la comprobación de su funcionamiento efectivo.

| Componente / elemento | Archivo o referencia | Función dentro de GIAR-ORION | Estado del relevamiento |
|---|---|---|---|
| Interfaz principal | `main_multilinea.py` | Recibe consultas y coordina la interacción con los componentes. | Identificada como punto de entrada vigente. Se continúa el análisis del flujo completo. |
| Recuperador RAG | `Agent/MultilingualKnowledgeRetriever.py` | Recupera fragmentos de la base documental local. | Inicialización identificada; algoritmo, ranking y contrato de salida pendientes de inspección completa. |
| Construcción del contexto RAG | `construir_contexto_rag(...)` en la interfaz | Prepara el contexto documental que se incorpora a la consulta del LLM. | Función identificada; falta medir qué información recuperada llega efectivamente al prompt. |
| Búsqueda web | `Agent/WebSearch.py` o módulo importado | Obtiene información externa cuando se selecciona una modalidad que la habilita. | Inicialización y modalidades identificadas; falta cerrar el análisis de implementación y fusión de resultados. |
| Servicio de lenguaje | Ollama, endpoint local `/api/chat` | Proporciona el servicio de inferencia del modelo de lenguaje. | Identificado en el código consultado. |
| Modelo LLM | `qwen3:8b` | Genera respuestas a partir de la consulta, instrucciones y contexto recibido. | Modelo observado en la configuración consultada; debe cotejarse con la configuración local efectiva al congelar la auditoría. |
| Extractor de afirmaciones | `Agent/ClaimExtractor.py` | Extrae afirmaciones factuales de la respuesta generada. | Módulo identificado; se observó la versión 0.1.2 en una copia consultada. Falta contrastar con el archivo vigente y completar su evaluación. |
| Verificador de evidencias | `Agent/EvidenceVerifier.py` | Evalúa la relación entre cada afirmación y las evidencias disponibles. | Módulo identificado; implementación, modelos, umbrales y reglas pendientes de inspección completa. |
| Pipeline de verificación | `Agent/ClaimVerificationPipeline.py` | Coordina la extracción y la verificación de afirmaciones. | Importación e inicialización identificadas; invocación efectiva, secuencia interna y agregación pendientes de confirmar. |
| Presentación del informe | `mostrar_informe_verificacion(...)` en la interfaz | Presenta al usuario los resultados de verificación disponibles. | Función identificada; falta comprobar la correspondencia completa entre la salida del pipeline y lo mostrado. |
| `ResponseVerifier.py` | Archivo presente en el repositorio | Posible componente de verificación adicional o variante. | No debe considerarse parte del flujo activo hasta confirmar sus importaciones y llamadas. |

#### 3.4.1. Consideraciones para interpretar el estado

Los estados de la tabla tienen un alcance deliberadamente acotado:

- **Identificado:** se encontró el archivo, símbolo o componente en el repositorio.
- **Inicialización confirmada:** se observó código que crea o prepara el componente.
- **Invocación confirmada:** se verificó que el flujo ejecuta efectivamente el método correspondiente.
- **Funcionamiento evaluado:** existen pruebas con entradas controladas y resultados medidos.
- **Pendiente:** todavía no se dispone de evidencia suficiente para afirmar lo anterior.

Que un módulo esté importado o inicializado no demuestra por sí solo que se ejecute en todas las consultas ni que sus resultados sean correctos. Esa diferencia será mantenida en todo el documento y en los informes de auditoría.

#### 3.4.2. Próximo tramo del relevamiento

El análisis continuará siguiendo el recorrido efectivo de una consulta en este orden:

1. Completar el seguimiento de `main_multilinea.py` desde la preparación de mensajes hasta la respuesta de Ollama, la invocación del pipeline y la presentación del informe.
2. Inspeccionar `Agent/ClaimVerificationPipeline.py`, identificando método público, argumentos, secuencia de ejecución, salidas y manejo de errores.
3. Revisar `Agent/ClaimExtractor.py` y `Agent/EvidenceVerifier.py` en la misma versión del repositorio que se utilizará como referencia.
4. Analizar `Agent/MultilingualKnowledgeRetriever.py` y el módulo de búsqueda web efectivamente importado.
5. Documentar un caso completo de extremo a extremo antes de implementar los instrumentos de medición.

**Regla de trabajo:** primero comprender y documentar el funcionamiento real; después diseñar las pruebas; finalmente medir. No se modificará ningún componente de producción para facilitar la auditoría.


### 3.5. Relevamiento de componentes

En esta sección se documentará cada componente de GIAR-ORION a partir de la inspección de su código fuente. El relevamiento no se limitará a describir la finalidad declarada de cada archivo: deberá reconstruir cómo se ejecuta, qué módulos utiliza, qué datos recibe, qué resultados produce y de qué manera se conecta con los demás componentes.

Cada componente se analizará siguiendo una estructura común:

1. Identificación del archivo y versión examinada.
2. Responsabilidad dentro del sistema.
3. Dependencias e importaciones.
4. Configuración y parámetros utilizados.
5. Funciones y clases principales.
6. Entradas y salidas.
7. Secuencia de ejecución.
8. Manejo de errores y condiciones excepcionales.
9. Archivos, servicios o recursos externos utilizados.
10. Estado de verificación y aspectos pendientes.

El relevamiento se realizará sobre la rama pública `main` del repositorio como referencia inicial. Antes de implementar la auditoría se deberá cotejar esa versión con la copia local que se utiliza para ejecutar GIAR-ORION. La inspección estática del repositorio no equivale a una prueba de ejecución.

#### 3.5.1. Interfaz principal: `main_multilinea.py`

**Identificación y función general**

El archivo `main_multilinea.py` implementa una interfaz conversacional de consola para GIAR-ORION. Su función principal es recibir consultas del usuario —incluidas consultas de varias líneas—, administrar el historial de la sesión, recuperar información documental, incorporar resultados web cuando se selecciona esa modalidad y enviar los mensajes preparados al servicio de lenguaje Ollama.

En el repositorio público consultado, el archivo presenta una cabecera que lo describe como una interfaz conversacional con entrada multilínea. La misma cabecera indica que esta variante permite procesar varias líneas como una única consulta y que conserva el procesamiento de memoria, RAG y Ollama. También contiene una advertencia textual que la identifica como versión de prueba y señala que no reemplaza a `main.py`. Esta declaración deberá contrastarse con la versión local que el usuario ejecuta actualmente y con la decisión de proyecto sobre el punto de entrada vigente.

**Fuente examinada:** repositorio público `PabloFolino/GIAR-ORION`, rama `main`, archivo `main_multilinea.py`.

**Dependencias e importaciones identificadas**

En el código consultado se identifican, entre otras, las siguientes dependencias:

| Dependencia | Uso observado |
|---|---|
| `json` | Lectura de configuración y serialización de conversaciones. |
| `sys` | Incorporación del directorio `Agent` a la ruta de importación cuando corresponde. |
| `urllib.request` y `urllib.error` | Comunicación HTTP con el servicio Ollama y tratamiento de errores de conexión. |
| `datetime` | Generación de marcas temporales para las conversaciones guardadas. |
| `pathlib.Path` | Construcción y administración de rutas del proyecto. |
| `prompt_toolkit.PromptSession` | Recepción de consultas en la consola. |
| `prompt_toolkit.key_binding.KeyBindings` | Definición de atajos para enviar consultas multilínea. |
| `Agent.ClaimVerificationPipeline.ClaimVerificationPipeline` | Importación de la clase que coordina la extracción y verificación de afirmaciones. |
| `MultilingualKnowledgeRetriever` | Recuperador documental importado desde el directorio `Agent` durante la inicialización de RAG. |
| `WebSearch` | Buscador web importado desde `Agent` cuando la búsqueda externa está habilitada. |

La presencia de una importación no demuestra que el componente se ejecute durante cada consulta. En particular, la conexión efectiva del pipeline de verificación se trata como un punto específico de análisis más adelante.

**Organización de rutas y configuración**

El archivo determina la ubicación del proyecto mediante `Path(__file__).resolve().parent` y utiliza esa ruta como `BASE_DIR`. A partir de ella establece:

- `CONFIG_FILE`: ubicación de `config.json`.
- `AGENT_DIR`: ubicación del directorio `Agent`.

La función `cargar_configuracion()` abre el archivo JSON y comprueba la presencia de campos esenciales, entre ellos `agent_name`, `version`, `llm` y `paths`. También valida la configuración del proveedor LLM, los modos de generación, los parámetros `think` y `num_predict`, la configuración RAG y la configuración de búsqueda web.

Entre las validaciones observadas se encuentran:

- El proveedor configurado debe ser `ollama`.
- Deben existir los datos necesarios para identificar el modelo y la URL base del servicio.
- Cada modo de generación debe definir `think` como booleano y `num_predict` como entero positivo.
- El modo inicial debe estar definido entre los modos disponibles.
- Si RAG está habilitado, el modo debe ser `e5`, `bge-m3` o `hybrid`.
- `top_k` debe ser un entero positivo.
- Los pesos de E5 y BGE-M3 deben estar entre 0 y 1; en modo híbrido deben sumar 1.
- Si la búsqueda web está habilitada, el proveedor admitido por esta implementación es `ddgs`; también se valida la cantidad máxima de resultados y la lista de dominios autorizados.

Estas validaciones permiten detectar errores de configuración antes de iniciar la interacción. No demuestran, por sí mismas, que los modelos o servicios estén disponibles ni que sus resultados sean correctos.

**Comunicación con Ollama y generación de respuestas**

La función `consultar_ollama(config, mensajes, modo)` construye una solicitud HTTP dirigida al endpoint `/api/chat` de Ollama. El contenido enviado incluye:

- El identificador del modelo definido en la configuración.
- La lista de mensajes que representa la conversación y el contexto de la consulta.
- `stream=False`, por lo que la respuesta se solicita sin transmisión progresiva.
- El parámetro `think` correspondiente al modo seleccionado.
- `options.num_predict`, tomado de la configuración del modo.

La solicitud utiliza el método HTTP `POST` y establece un timeout de 300 segundos. La función contempla errores HTTP, errores de conexión, JSON inválido y respuestas que no contienen el campo `message.content` esperado. Cuando la respuesta tiene la estructura prevista, devuelve el texto generado y el objeto completo recibido de Ollama.

Este último punto es relevante para la auditoría: la función devuelve tanto el texto como los metadatos de respuesta. Por lo tanto, se deberá comprobar qué información se conserva en el flujo de ejecución y si los metadatos disponibles permiten medir tokens, tiempos y motivo de finalización.

**Memoria e historial de conversaciones**

El archivo administra el historial de la sesión mediante una lista de mensajes con roles `system`, `user` y `assistant`.

Se identifican funciones para:

- Determinar el directorio de conversaciones a partir de `paths.memory`.
- Guardar la conversación en archivos JSON.
- Listar las conversaciones guardadas.
- Recuperar una conversación seleccionada por número.

Al guardar, se conservan únicamente mensajes de usuario y asistente; la instrucción interna del sistema no se incluye en el archivo. El registro incorpora nombre y versión del agente, modelo, fecha de guardado, cantidad de mensajes y contenido de la conversación. También se evita sobrescribir un archivo cuando coincide la marca temporal, agregando un contador al nombre.

La recuperación valida que el archivo contenga una lista de mensajes y conserva solamente entradas con roles `user` o `assistant` y contenido textual.

**Recuperación documental RAG**

La función `crear_recuperador(config)` inicializa el componente RAG cuando la configuración lo habilita. Para ello importa `MultilingualKnowledgeRetriever` desde el directorio `Agent` y lo instancia con:

- Directorio de conocimiento (`knowledge_dir`).
- Modo de recuperación.
- Dispositivo de ejecución.
- Peso de E5.
- Peso de BGE-M3.
- Parámetro `local_files_only`.

La función informa el modo activo y, cuando corresponde, los pesos utilizados en modo híbrido.

La función `construir_contexto_rag(recuperador, pregunta, top_k)` ejecuta `recuperador.search(pregunta, top_k=top_k)`. Si no existe recuperador o no se obtienen resultados, devuelve contexto y listas vacías.

Cuando hay resultados, la función:

1. Extrae las fuentes sin repetirlas.
2. Recorre los fragmentos recuperados.
3. Construye bloques que identifican la fuente y el valor de similitud.
4. Incorpora el texto de cada fragmento.
5. Antecede los bloques con instrucciones que indican al LLM que utilice el material como evidencia, que no invente datos ausentes y que reconozca cuándo el contexto es insuficiente.
6. Devuelve tres elementos: contexto formateado, fuentes y resultados originales.

La devolución de los resultados originales es especialmente importante para la auditoría: permite conservar los fragmentos y sus metadatos para contrastarlos posteriormente con las afirmaciones generadas.

**Búsqueda web y modalidades de fuentes**

La función `crear_buscador_web(config)` inicializa `WebSearch` solamente cuando `web_search.enabled` está habilitado. El código importa `WebSearch` desde el directorio `Agent` y lo instancia con parámetros de región y búsqueda segura.

La función `construir_contexto_web(...)` contempla tres modalidades:

- `local`: no incorpora resultados web; utiliza la recuperación documental local.
- `web`: ejecuta una búsqueda web libre.
- `autorizada`: restringe la búsqueda a los dominios configurados en `authorized_domains`.

Los resultados se convierten en bloques que incluyen título, dominio, URL y descripción. El contexto web se identifica expresamente como información externa y se instruye al modelo para distinguir hechos publicados, inferencias y datos no verificados.

La modalidad inicial observada en la función de inicio es `local`. El usuario puede cambiarla mediante los comandos de la interfaz. Por consiguiente, la búsqueda web no debe considerarse una etapa obligatoria de todas las consultas.

**Entrada multilínea y comandos**

La función `crear_sesion_entrada()` utiliza `PromptSession` y define atajos para enviar una consulta completa. El comportamiento previsto es:

- `Enter`: agrega una nueva línea.
- `Ctrl+S`: intenta enviar la consulta completa.
- `Esc` seguido de `Enter`: permite un envío alternativo.
- `/enviar` en una línea independiente: envía el contenido acumulado.

La función `mostrar_ayuda(...)` informa los comandos disponibles. Entre ellos se encuentran `/help`, `/salir`, `/limpiar`, `/guardar`, `/sesiones`, `/abrir N`, `/modo rapido`, `/modo investigacion` y los comandos `/fuente`.

La función `iniciar_agente(config)` constituye el núcleo de la interfaz. Inicializa la configuración activa, el recuperador RAG, el buscador web y una instancia de `ClaimVerificationPipeline`. Luego crea el historial inicial con el mensaje de sistema y entra en un ciclo de recepción de consultas y comandos.

**Secuencia de procesamiento identificada**

A partir del código consultado, el flujo de una consulta puede describirse, en los tramos visibles, de la siguiente manera:

1. La interfaz recibe el texto completo del usuario.
2. Si el texto está vacío, vuelve a solicitar una entrada.
3. Si corresponde a un comando, ejecuta la operación solicitada y no lo trata como consulta al LLM.
4. Si es una consulta, agrega el mensaje del usuario al historial de la sesión.
5. Ejecuta la recuperación RAG, si está habilitada.
6. Ejecuta la construcción del contexto web según la modalidad seleccionada.
7. Reúne los contextos no vacíos.
8. Copia el historial para preparar los mensajes de la consulta actual.
9. Inserta el contexto recuperado como mensaje de sistema temporal, sin incorporarlo al historial persistente.
10. Prepara los mensajes que se enviarán al modelo.

El comentario del código señala que los contextos RAG y web se agregan solamente a la solicitud actual, mientras que el historial conserva la pregunta y la respuesta. Esta separación debe preservarse en el diseño de auditoría: el contexto realmente enviado al modelo no es necesariamente idéntico al historial guardado.

**Presentación del informe de verificación**

La función `mostrar_informe_verificacion(informe)` está destinada a presentar el resultado producido por `ClaimVerificationPipeline`. No ejecuta verificaciones ni modifica el informe recibido.

Entre los campos que intenta mostrar se encuentran:

- Estado general del pipeline.
- Versiones del pipeline, extractor y verificador.
- Estado y cobertura estructural de la extracción.
- Cantidad de unidades analizadas y clasificadas.
- Cantidad de afirmaciones enviadas a verificación.
- Errores de extracción.
- Estado de la verificación semántica.
- Resultado de cada afirmación.
- Puntajes de entailment y contradiction, cuando están disponibles.
- Evidencias consideradas y sus fuentes.
- Estado de las referencias RAG y web.
- Detección de URLs duplicadas.
- Limitaciones informadas por el pipeline.

La existencia de esta función demuestra que la interfaz contempla una presentación detallada del informe. No demuestra que la función sea invocada efectivamente después de cada respuesta.

**Hallazgo crítico pendiente: conexión efectiva del pipeline**

En el código consultado se confirma que:

1. `ClaimVerificationPipeline` se importa desde `Agent.ClaimVerificationPipeline`.
2. `iniciar_agente()` crea una instancia y le entrega `ollama_base_url` y `ollama_model`.
3. Existe una función `mostrar_informe_verificacion(informe)` preparada para presentar un informe del pipeline.

Sin embargo, en el tramo del archivo que pudo inspeccionarse no se ha podido confirmar todavía la llamada al método que ejecuta la verificación ni la conexión efectiva entre la respuesta generada y el informe presentado. La búsqueda del identificador `pipeline_verificacion` permitió localizar su inicialización, pero no una segunda referencia inequívoca que demuestre su ejecución.

Por lo tanto, **no corresponde afirmar todavía que el pipeline de extracción y verificación se ejecute efectivamente en cada consulta de esta interfaz**. Este es un punto prioritario que debe resolverse inspeccionando el archivo completo y, en particular, el tramo final del ciclo de procesamiento.

También debe verificarse si `consultar_ollama(...)` se invoca en el flujo esperado, cómo se incorpora la respuesta al historial y si existe alguna ruta alternativa que ejecute o evite la verificación.

**Observación de consistencia sobre el punto de entrada**

Existe una diferencia que debe quedar registrada: la decisión de trabajo del proyecto identifica `main_multilinea.py` como la interfaz que se utiliza para las pruebas finales, mientras que la cabecera de la copia pública consultada lo describe como una versión de prueba que no reemplaza a `main.py`.

No se resolverá esta diferencia por inferencia. Antes de conectar la auditoría se deberá confirmar con el usuario qué archivo ejecuta efectivamente en su instalación y cotejar su contenido con la rama pública. La auditoría debe instrumentar el punto de entrada real, no uno supuesto.

**Conclusión del relevamiento de `main_multilinea.py`**

La inspección confirma que el archivo reúne responsabilidades de interfaz, validación de configuración, administración de conversaciones, inicialización de RAG y búsqueda web, preparación del contexto y comunicación con Ollama. También incorpora la importación e inicialización del pipeline de verificación y una función para presentar su informe.

El análisis permite identificar claramente los límites entre recuperación y generación:

- Si el fragmento correcto no aparece entre los resultados de `search`, el problema corresponde a **recuperación RAG**.
- Si el fragmento fue recuperado pero no se incorpora correctamente al mensaje enviado a Ollama, el problema corresponde a **integración del contexto**.
- Si la evidencia llega al modelo y la respuesta la interpreta incorrectamente, la omite o agrega datos no respaldados, el problema corresponde a **generación LLM (Qwen3)**.
- Si la respuesta contiene afirmaciones que deberían verificarse, pero no se ejecuta el pipeline o su resultado no se presenta, el problema corresponde a **integración de la verificación en la interfaz**; no debe atribuirse automáticamente al modelo NLI ni al extractor.

El relevamiento de este archivo queda **parcialmente completado**. La confirmación del flujo final de generación y verificación requiere inspeccionar el tramo restante del archivo y contrastarlo con la copia local vigente.

| Elemento examinado | Resultado del relevamiento |
|---|---|
| Configuración y validaciones | Identificadas |
| Comunicación HTTP con Ollama | Identificada |
| Gestión del historial y archivos de conversación | Identificada |
| Inicialización de RAG | Identificada |
| Construcción del contexto RAG y conservación de resultados originales | Identificada |
| Inicialización de búsqueda web DDGS | Identificada |
| Modalidades local, web y autorizada | Identificadas |
| Preparación de mensajes para el LLM | Identificada parcialmente |
| Importación e inicialización de `ClaimVerificationPipeline` | Confirmadas |
| Invocación efectiva del pipeline en cada consulta | Pendiente de confirmar |
| Correspondencia entre informe generado y presentación al usuario | Pendiente de confirmar |
| Coincidencia entre la rama pública y el archivo local ejecutado | Pendiente de cotejar |

**Referencias de código consultadas:** `main_multilinea.py`, funciones `cargar_configuracion()`, `consultar_ollama()`, `guardar_conversacion()`, `listar_conversaciones()`, `recuperar_conversacion()`, `crear_recuperador()`, `construir_contexto_rag()`, `crear_buscador_web()`, `construir_contexto_web()`, `mostrar_informe_verificacion()`, `crear_sesion_entrada()`, `mostrar_ayuda()` e `iniciar_agente()`.

**Fuente:** [repositorio público GIAR-ORION, rama `main`](https://github.com/PabloFolino/GIAR-ORION), archivo `main_multilinea.py`.

## 4. Modelo de arquitectura a verificar

El esquema representa el flujo de trabajo que se desprende del relevamiento y de las decisiones previas. Es provisional hasta revisar las llamadas reales y sus condiciones de ejecución.

```text
                 USUARIO
                    |
                    v
             main_multilinea.py
                    |
          +---------+----------+
          |                    |
          v                    v
   Memoria/historial       Configuración
          |                    |
          +---------+----------+
                    |
                    v
             Consulta del usuario
                    |
          +---------+----------+
          |                    |
          v                    v
     Recuperación RAG      WebSearch (DDGS)
          |                    |
          +---------+----------+
                    |
                    v
            Construcción del contexto
                    |
                    v
              Ollama / Qwen3
                    |
                    v
             Respuesta generada
                    |
                    v
       ClaimVerificationPipeline
                    |
             +------+------+
             |             |
             v             v
       ClaimExtractor  EvidenceVerifier
             |             |
             +------+------+
                    |
                    v
          Resultado de verificación
                    |
                    v
          Respuesta / informe final
```

No se debe dar por hecho que todos los casos recorren exactamente esta secuencia. Hay que comprobar:
- si la búsqueda web se ejecuta siempre o solo bajo ciertas condiciones;
- cómo se combinan los resultados web y RAG;
- si la verificación se ejecuta en todas las respuestas;
- qué salida del verificador llega al usuario;
- si existen rutas de excepción, abstención o reintento;
- si `ClaimVerificationPipeline` llama a los dos módulos indicados o incorpora lógica adicional.

## 5. Relevamiento paso a paso del sistema

El relevamiento se realizará en este orden. Cada paso deberá producir evidencia concreta: archivo, función, llamada, dato de entrada y dato de salida.

### Paso 0 — Congelar la referencia de auditoría

Registrar:
- ruta del repositorio;
- fecha y hora;
- versión de Python y entorno virtual;
- hash SHA-256 de los archivos examinados;
- estado de Git, si el repositorio está disponible;
- versión de Ollama y etiqueta/digest del modelo;
- copia de solo lectura de la configuración efectiva (con secretos excluidos).

**Criterio de cierre:** poder identificar exactamente qué versión de GIAR-ORION se evaluó.

### Paso 1 — Inventario del repositorio

Identificar los directorios y archivos propios del proyecto, excluyendo del inventario funcional:
- `.venv/`;
- cachés;
- `__pycache__/`;
- pesos de modelos;
- embeddings y archivos generados que no sean código o datos de prueba.

Clasificar cada archivo como:
- punto de entrada;
- módulo de producción;
- configuración;
- datos/Knowledge;
- memoria y logs;
- pruebas;
- experimentos/variantes históricas;
- documentación;
- artefactos generados.

**Criterio de cierre:** inventario que permita distinguir claramente producción, experimentos y archivos obsoletos.

### Paso 2 — Interfaz principal: `main_multilinea.py`

Inspeccionar:
- carga y validación de configuración;
- inicialización de memoria;
- inicialización de RAG;
- inicialización de búsqueda web;
- construcción de mensajes para Ollama;
- llamada HTTP y parámetros enviados;
- ensamblado de contexto;
- llamada a la verificación;
- tratamiento de errores y respuesta final.

Para cada función registrar firma, responsabilidad, dependencias, entradas, salidas y efectos secundarios.

**Criterio de cierre:** diagrama de llamadas real desde la entrada del usuario hasta la respuesta final.

### Paso 3 — RAG: `MultilingualKnowledgeRetriever.py`

Inspeccionar sin alterar:
- modelos de embeddings realmente cargados;
- modo `e5`, `bge-m3` o `hybrid`;
- tokenización y normalización;
- carga y fragmentación de documentos;
- generación o carga de embeddings;
- estrategia de similitud y combinación de puntuaciones;
- ordenamiento y desempate;
- filtros;
- estructura exacta de cada resultado;
- tratamiento de documentos vacíos, duplicados y errores.

Registrar la relación entre `source`, `score` y `text` que la interfaz conserva al construir el contexto.

**Distinción diagnóstica:** un fallo al encontrar o posicionar evidencia es un fallo de **recuperación RAG**, no de generación LLM.

### Paso 4 — Búsqueda web: `WebSearch.py`

Determinar:
- si está conectada a `main_multilinea.py`;
- condiciones de activación;
- consulta enviada;
- proveedor y parámetros efectivos;
- formato de los resultados;
- cómo se fusionan con RAG;
- cómo se identifican las fuentes;
- qué ocurre cuando no hay conexión o resultados.

La búsqueda web se medirá separadamente de RAG. No se atribuirá al recuperador documental una evidencia que provenga de DDGS.

### Paso 5 — Generación: Ollama y Qwen3

Inspeccionar:
- construcción exacta de `messages`;
- system prompt;
- historial incluido;
- contexto RAG/web incorporado;
- modelo y opciones efectivas;
- `think`, `num_predict` y timeout;
- formato de respuesta;
- metadatos de Ollama (`prompt_eval_count`, `eval_count`, duraciones y motivo de finalización, si la API los devuelve);
- manejo de errores y truncamiento.

**Distinción diagnóstica:** si la evidencia correcta fue entregada al modelo pero la respuesta la interpreta mal, la omite o inventa datos, el problema corresponde a **generación LLM**. Si la evidencia nunca llegó al contexto, el origen es recuperación o integración de contexto.

### Paso 6 — `ClaimExtractor.py`

La copia consultada identifica `ClaimExtractor.VERSION = "0.1.2"`. El módulo:
- segmenta la respuesta en unidades textuales;
- solicita a Ollama la extracción de afirmaciones factuales atómicas;
- exige clasificación para cada unidad;
- detecta omisiones, duplicados e inconsistencias estructurales;
- devuelve información serializable como JSON.

La documentación del propio módulo advierte que la cobertura estructural no garantiza exhaustividad semántica y que el extractor no verifica la verdad de las afirmaciones.

Hay que inspeccionar el archivo completo y registrar:
- prompt de extracción;
- modelo y parámetros que recibe;
- reglas de atomización;
- esquema JSON;
- validaciones;
- errores y reintentos;
- correspondencia entre unidades originales y claims extraídos.

**Distinción diagnóstica:** una afirmación factual omitida o fragmentada incorrectamente es un fallo de **ClaimExtractor**, no de EvidenceVerifier.

### Paso 7 — `EvidenceVerifier.py`

Inspeccionar el código vigente para determinar:
- modelos NLI cargados y sus versiones;
- etiquetas y mapeo de clases;
- umbrales efectivos;
- normalización de evidencias;
- selección y agregación de evidencias;
- reglas de `SUPPORTED`, `CONTRADICTED` e `INSUFFICIENT`;
- adjudicación adicional mediante Qwen3, si existe;
- reglas de decisión final;
- tratamiento de contradicciones entre fuentes;
- salida estructurada y trazabilidad.

No se inferirán umbrales ni comportamiento a partir de versiones anteriores o de nombres de archivos. Se leerán del código y la configuración que efectivamente se ejecutan.

**Distinción diagnóstica:** si el claim está bien extraído y la evidencia pertinente fue suministrada, pero el veredicto es incorrecto, el problema corresponde a **EvidenceVerifier**.

### Paso 8 — `ClaimVerificationPipeline.py`

Determinar el flujo real:
- orden de llamadas;
- argumentos entregados al extractor;
- evidencias enviadas al verificador;
- relación entre claims y fuentes;
- agregación de veredictos;
- política ante claims omitidos o errores;
- criterio para producir el estado global;
- si la salida original de Qwen3 se conserva sin alteraciones;
- qué información se presenta al usuario.

**Criterio de cierre:** contrato de entrada/salida y diagrama de secuencia del pipeline.

### Paso 9 — Integración completa

Seguir al menos un caso instrumentado de extremo a extremo, sin cambiar las decisiones del sistema. Registrar el mismo `audit_case_id` en cada etapa:

1. Consulta original.
2. Resultados RAG.
3. Resultados web, si se ejecutan.
4. Contexto efectivamente enviado.
5. Respuesta bruta de Qwen3.
6. Claims extraídos.
7. Evidencias asociadas a cada claim.
8. Salida NLI y adjudicación, si aplica.
9. Veredictos y resultado final.
10. Respuesta efectivamente entregada al usuario.

**Criterio de cierre:** trazabilidad completa que permita localizar el primer punto en que se aparta del resultado esperado.

## 6. Diseño experimental

### 6.1 Dataset

Archivo propuesto: `AUDIT/Dataset/GIAR_ORION_AUDIT_DATASET.json`.

Cada caso deberá contener, como mínimo:

```json
{
  "test_id": "RAG-001",
  "category": "retrieval",
  "language": "es",
  "difficulty": "medium",
  "question": "Pregunta de prueba",
  "source_documents": ["documento_referencia.md"],
  "expected_evidence": [
    {
      "source": "documento_referencia.md",
      "text_or_span": "Fragmento de referencia",
      "relevance": 3
    }
  ],
  "expected_claims": [],
  "expected_verdicts": [],
  "expected_answer": null,
  "required_points": [],
  "forbidden_claims": [],
  "notes": "Justificación y criterio de anotación"
}
```

Los campos podrán ser nulos cuando no correspondan a una etapa. El esquema final deberá validarse antes de iniciar las pruebas.

### 6.2 Independencia de las referencias

- Las respuestas esperadas no se generarán con el mismo Qwen3 que se evalúa.
- Las evidencias esperadas se identificarán directamente en los documentos fuente.
- Los claims y veredictos de referencia se revisarán manualmente.
- Cada caso tendrá una justificación verificable.
- Las versiones del dataset serán inmutables una vez utilizadas en una ejecución publicada.

### 6.3 Tamaño

La distribución inicial de 100 casos queda como objetivo tentativo, no como requisito cerrado. Antes de fijar cantidades se revisarán los casos existentes y su reutilización posible. Un mismo caso puede alimentar varias métricas, pero cada etapa debe tener su propio denominador y criterio de puntuación. No se sumarán los resultados de etapas diferentes como si fueran observaciones independientes.

## 7. Métricas

### 7.1 RAG

Para cada consulta y para el conjunto:
- Precision@K;
- Recall@K;
- F1@K;
- Hit Rate@K;
- MRR;
- NDCG@K.

La relevancia se anotará por fragmento/documento y se definirá de antemano el criterio de correspondencia. Se informará también cobertura por tipo de consulta, idioma y dificultad.

### 7.2 ClaimExtractor

Con correspondencia entre claims esperados y extraídos:
- Precision, Recall y F1;
- omisiones;
- claims espurios;
- duplicados;
- errores de atomización/fragmentación;
- cobertura de unidades textuales.

La comparación semántica no debe depender exclusivamente de igualdad literal. El protocolo de emparejamiento debe quedar fijado y auditable.

### 7.3 EvidenceVerifier

- Accuracy;
- Precision, Recall y F1 por clase;
- macro-F1;
- matriz de confusión;
- tasa de falsos `SUPPORTED`;
- tasa de falsas contradicciones;
- tasa de `INSUFFICIENT`;
- cobertura de casos con evidencia contradictoria.

Se conservarán por separado la salida NLI, la adjudicación LLM y el veredicto final cuando el código exponga esas etapas.

### 7.4 Qwen3

- exactitud factual;
- cobertura de puntos requeridos;
- fidelidad a las fuentes;
- afirmaciones no respaldadas;
- contradicciones;
- omisiones;
- cumplimiento de instrucciones;
- latencia;
- tokens de entrada/salida y velocidad, cuando estén disponibles;
- motivo de finalización y señales de truncamiento.

La evaluación de generación se hará con contexto controlado y referencia externa. Se informará por separado el rendimiento con evidencia correcta y el rendimiento cuando la evidencia recuperada por RAG sea la que realmente recibe.

### 7.5 Pipeline integral

- proporción de consultas con respuesta correcta;
- cobertura de requisitos;
- claims incorrectos que llegan a la salida final;
- claims correctos descartados;
- errores no detectados;
- errores detectados correctamente;
- tasa de abstención adecuada;
- trazabilidad completa;
- latencia total y por etapa.

## 8. Atribución de errores y propagación

Cada error deberá identificar:

1. **Primer punto de divergencia:** primera etapa donde el resultado difiere de la referencia.
2. **Componente de origen:** RAG, WebSearch, integración de contexto, Qwen3, ClaimExtractor, EvidenceVerifier o integración del pipeline.
3. **Efecto posterior:** etapas afectadas por el error inicial.
4. **Detección:** si una etapa posterior lo detectó o lo dejó pasar.
5. **Impacto final:** efecto sobre la respuesta entregada.

Ejemplos:
- Evidencia ausente en top-K: recuperación RAG.
- Evidencia recuperada pero excluida al construir el prompt: integración de contexto.
- Evidencia presente en el prompt y afirmación falsa: generación Qwen3.
- Afirmación falsa presente en la respuesta, pero omitida por el extractor: ClaimExtractor.
- Claim correcto y evidencia suficiente, pero veredicto incorrecto: EvidenceVerifier.
- Componentes individuales correctos pero salida final mal agregada: integración del pipeline.

No se asignará automáticamente todo error final al último módulo que intervino.

## 9. Ejecución y estados

Cada etapa y caso podrá tener uno de estos estados:

- `PASS`: ejecutado y cumple el criterio definido.
- `FAIL`: ejecutado y no cumple.
- `ERROR`: no pudo completarse por una excepción o fallo técnico.
- `SKIPPED`: no correspondía ejecutarlo.
- `NOT_RUN`: no llegó a ejecutarse.
- `INCONCLUSIVE`: se ejecutó, pero la evidencia no permite una conclusión válida.

Un módulo no ejecutado nunca contará como `FAIL` ni como `PASS`.

La ejecución conservará los resultados parciales aunque una etapa posterior falle.

## 10. Estructura de archivos propuesta

```text
GIAR-ORION/
└── AUDIT/
    ├── README.md
    ├── SPEC/
    │   └── GIAR-ORION-AUDIT-SPEC-001.md
    ├── Dataset/
    │   ├── GIAR_ORION_AUDIT_DATASET.json
    │   └── dataset_metadata.json
    ├── Scripts/
    │   ├── GIAR_ORION_AUDIT.py
    │   ├── audit_controller.py
    │   ├── audit_rag.py
    │   ├── audit_claim_extractor.py
    │   ├── audit_evidence_verifier.py
    │   ├── audit_qwen3.py
    │   ├── audit_pipeline.py
    │   └── audit_reporting.py
    ├── Config/
    │   └── audit_config.json
    └── Results/
        └── AUDIT_YYYY-MM-DD_HHMMSS_<RUN_ID>/
            ├── environment.json
            ├── rag_results.json
            ├── claim_extractor_results.json
            ├── evidence_verifier_results.json
            ├── qwen3_results.json
            ├── pipeline_results.json
            ├── metrics.json
            ├── execution_log.txt
            ├── final_report.md
            └── final_report.xlsx
```

La estructura es una propuesta. Los nombres y responsabilidades se confirmarán al diseñar la implementación. Cada ejecución utilizará un directorio nuevo.

## 11. Reproducibilidad y preservación

Por ejecución se guardará:
- identificador único;
- fecha/hora y zona horaria;
- hash del dataset;
- hash de los archivos de código relevantes;
- configuración efectiva saneada;
- versión de Python, librerías, Ollama y modelos;
- identificadores de documentos/fragmentos recuperados;
- entradas y salidas de cada etapa;
- métricas y excepciones;
- duración de cada etapa.

No se sobrescribirán resultados anteriores. Los datos sensibles, credenciales y secretos no se copiarán a los informes.

## 12. Criterios de aceptación de la auditoría

La herramienta de auditoría se considerará técnicamente válida cuando:

1. Ejecute las cinco evaluaciones desde un controlador central.
2. Use los componentes reales del punto de entrada vigente.
3. No modifique el código ni la configuración de producción.
4. Distinga claramente errores de RAG y de generación LLM.
5. Mantenga trazabilidad por caso a través de todas las etapas.
6. Calcule métricas a partir de referencias independientes.
7. Guarde resultados parciales y errores.
8. Diferencie `FAIL`, `ERROR`, `SKIPPED` y `NOT_RUN`.
9. Permita comparar ejecuciones con el mismo dataset y configuración identificada.
10. Genere un informe que permita localizar el primer origen de cada fallo.

No se fijan umbrales globales de aprobación del agente hasta disponer de una línea de base experimental. No se inventará una calificación general combinando métricas incompatibles.

## 13. Plan de trabajo y avance

| Orden | Actividad | Estado |
|---|---|---|
| 0 | Congelar referencia local y registrar hashes | Pendiente |
| 1 | Inventariar estructura y clasificar archivos | Parcial: existe inventario del 01-11 |
| 2 | Revisar `main_multilinea.py` y llamadas reales | Parcial |
| 3 | Revisar `MultilingualKnowledgeRetriever.py` | Pendiente |
| 4 | Revisar `WebSearch.py` y su integración | Pendiente |
| 5 | Revisar llamada a Ollama/Qwen3 | Parcial |
| 6 | Revisar `ClaimExtractor.py` | Parcial: versión 0.1.2 identificada |
| 7 | Revisar `EvidenceVerifier.py` | Pendiente |
| 8 | Revisar `ClaimVerificationPipeline.py` | Pendiente |
| 9 | Trazar un caso integral de extremo a extremo | Pendiente |
| 10 | Cerrar dataset, métricas y protocolo | Pendiente |
| 11 | Implementar controlador y módulos de auditoría | Pendiente |
| 12 | Ejecutar línea de base y generar informes | Pendiente |

## 14. Próximo paso concreto

El siguiente paso es completar el **Paso 0 y el Paso 1 sobre la copia local vigente del repositorio**, y luego cerrar el **Paso 2** inspeccionando `main_multilinea.py` completo. Para hacerlo con precisión se necesita el repositorio actual o, como mínimo, estos archivos de la versión que se ejecuta hoy:

- `main_multilinea.py`
- `config.json`
- `Agent/MultilingualKnowledgeRetriever.py`
- `Agent/WebSearch.py`
- `Agent/ClaimExtractor.py`
- `Agent/EvidenceVerifier.py`
- `Agent/ClaimVerificationPipeline.py`

No hace falta enviar `.venv`, cachés, embeddings ni pesos de modelos para esta primera revisión.

**Regla de avance:** no se implementará el controlador de auditoría hasta haber documentado los contratos reales de los componentes y comprobado el recorrido efectivo de una consulta. Así evitamos construir una auditoría que mida una arquitectura supuesta en lugar de GIAR-ORION.

---

# ANEXO A — Verificación del repositorio público

## Actualización 0.2 — 2026-11-08

### A.1 Fuente inspeccionada

Se inspeccionó el repositorio público:

- Repositorio: https://github.com/PabloFolino/GIAR-ORION
- Rama observada: `main`
- Punto de entrada inspeccionado: `main_multilinea.py`
- Archivo consultado desde GitHub: 1083 líneas (854 líneas de código), 33.9 KB según la vista del repositorio.

Esta inspección corresponde a la rama pública `main` en el momento de la consulta. No equivale a ejecutar el código ni a verificar que el contenido local del equipo sea idéntico.

### A.2 Hallazgo importante: la arquitectura real es más concreta que el esquema inicial

En `main_multilinea.py` se observa que:

1. Se importa directamente `ClaimVerificationPipeline` desde `Agent.ClaimVerificationPipeline`.
2. Durante `iniciar_agente(...)` se inicializan el recuperador RAG, el buscador web y una instancia de `ClaimVerificationPipeline`.
3. El pipeline recibe `ollama_base_url` y `ollama_model` desde la configuración LLM.
4. El modo de fuente comienza como `local`.
5. El usuario puede cambiarlo mediante `/fuente local`, `/fuente web` o `/fuente autorizada`.
6. La recuperación RAG se ejecuta para la consulta y devuelve tres elementos: contexto formateado, fuentes y resultados originales.
7. La búsqueda web se ejecuta según la modalidad elegida. En modo `local` no aporta contexto web; en modo `web` usa búsqueda libre y en modo `autorizada` restringe la búsqueda a dominios configurados.
8. Los contextos RAG y web se agregan a un mensaje de sistema temporal para la solicitud al LLM.
9. El historial de conversación conserva la pregunta y la respuesta, mientras que los contextos recuperados se agregan solo a la solicitud actual.
10. La interfaz incluye una función dedicada a presentar el informe del pipeline, con estado general, versiones, extracción, verificación semántica, referencias y limitaciones.

Referencias de código inspeccionadas:
- `main_multilinea.py`: importación del pipeline y validación de configuración.
- `main_multilinea.py`: `crear_recuperador(...)`, `construir_contexto_rag(...)`.
- `main_multilinea.py`: `crear_buscador_web(...)`, `construir_contexto_web(...)`.
- `main_multilinea.py`: `mostrar_informe_verificacion(...)`.
- `main_multilinea.py`: `iniciar_agente(...)` e inicialización de componentes.

### A.3 Diagrama de flujo actualizado (parcialmente confirmado)

```text
                         USUARIO
                            |
                            v
                    main_multilinea.py
                            |
             +--------------+----------------+
             |              |                |
             v              v                v
        Historial       Recuperador RAG   Buscador DDGS
             |              |                |
             |        contexto + fuentes     |
             |        + resultados crudos    |
             |              |                |
             |              |       modalidad seleccionada
             |              |       local / web / autorizada
             |              |                |
             +--------------+----------------+
                            |
                            v
                Construcción de contexto temporal
                            |
                            v
                    Ollama / modelo configurado
                            |
                            v
                      Respuesta generada
                            |
                            v
                 ClaimVerificationPipeline
                            |
                 [detalle interno pendiente]
                            |
                            v
                   Informe de verificación
                            |
                            v
                     Presentación al usuario
```

**Importante:** la importación, la construcción de la instancia y la función de presentación del informe están comprobadas en el archivo. En esta revisión parcial todavía no se ha confirmado el punto exacto donde se invoca el método de verificación ni todos los argumentos que se le entregan. Tampoco se ha inspeccionado el código interno completo del pipeline. Por lo tanto, el enlace entre la respuesta generada y la ejecución efectiva de la verificación queda pendiente de confirmar.

### A.4 Corrección al documento inicial

El diagrama de la sección 4 de la versión 0.1 era una hipótesis de trabajo. Debe leerse como provisional y no como descripción verificada del flujo. Este anexo reemplaza esa hipótesis en los puntos que ya fueron confirmados.

También se precisa que la búsqueda web no se ejecuta necesariamente en todas las consultas: la interfaz permite seleccionar la modalidad de fuentes y su valor inicial es `local`. RAG local y búsqueda web son fuentes diferenciadas.

### A.5 Próximas inspecciones prioritarias

Para completar el Paso 2 y avanzar al Paso 3, el orden será:

1. Terminar de seguir en `main_multilinea.py` el tramo posterior a la construcción de `mensajes_para_consulta`: llamada a Ollama, incorporación de la respuesta al historial, invocación del pipeline y presentación de su informe.
2. Inspeccionar `Agent/ClaimVerificationPipeline.py`: constructor, método público, secuencia de ejecución, argumentos, salidas y manejo de errores.
3. Inspeccionar `Agent/ClaimExtractor.py` y `Agent/EvidenceVerifier.py` desde la rama pública actual, no desde copias históricas.
4. Inspeccionar `Agent/MultilingualKnowledgeRetriever.py` y `Agent/WebSearch.py`.
5. Contrastar el `config.json` público actual con los valores de configuración observados anteriormente.

### A.6 Estado de la auditoría tras inspeccionar GitHub

| Actividad | Estado actualizado |
|---|---|
| Acceso al repositorio | Confirmado: repositorio público accesible |
| Identificación de rama | `main` |
| Identificación de `main_multilinea.py` | Confirmada |
| Importación e inicialización del pipeline | Confirmadas |
| Inicialización de RAG | Confirmada |
| Inicialización de DDGS | Confirmada |
| Selección de modalidad de fuentes | Confirmada |
| Construcción de contexto temporal | Confirmada |
| Llamada final al LLM y orden exacto de las etapas posteriores | Pendiente de cerrar |
| Contrato interno del pipeline | Pendiente |
| Algoritmo y parámetros efectivos de EvidenceVerifier | Pendiente |
| Auditoría experimental | No iniciada |

**Conclusión de esta actualización:** no hace falta que el usuario envíe un ZIP para comenzar el análisis estático del repositorio público. Se continuará utilizando la rama `main` como referencia y se señalarán expresamente las diferencias que solo puedan resolverse contrastando con la instalación local.
