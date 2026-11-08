# GIAR-ORION-AUDIT-SPEC-001
## Especificación de auditoría integral y relevamiento de arquitectura

| Campo | Valor |
|---|---|
| Proyecto | GIAR-ORION |
| Documento | GIAR-ORION-AUDIT-SPEC-001.md |
| Versión | 0.5 — Flujo integral de consulta y verificación |
| Fecha | 2026-11-08 |
| Estado | En revisión: flujo principal de consulta y ejecución del pipeline documentados; eficacia pendiente de evaluación |
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
   - [3.5.2 Ciclo completo de una consulta: desde el ingreso hasta la verificación](#352-ciclo-completo-de-una-consulta-desde-el-ingreso-hasta-la-verificación)
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

La arquitectura de GIAR-ORION está organizada alrededor de una interfaz principal que coordina la interacción con el usuario y conecta los componentes de recuperación, generación y verificación. En la revisión que da origen a esta versión 0.5 se incorpora como confirmado que, después de obtener la respuesta de Qwen3, la interfaz invoca el pipeline de verificación y procesa su informe. La ejecución de esa etapa no debe confundirse con una validación de su eficacia ni con una corrección automática de la respuesta.

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

El esquema siguiente representa el flujo funcional actualizado. La conexión desde la respuesta generada hacia el pipeline y la presentación del informe se consideran confirmadas según el seguimiento comunicado para esta revisión. La secuencia interna del pipeline y la eficacia de sus veredictos siguen sujetas a inspección y medición.

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

**Alcance de lo confirmado en esta versión:** además de la importación e inicialización, se da por confirmado que el flujo de consulta llega a la invocación efectiva de `ClaimVerificationPipeline` después de la generación de Qwen3 y que el informe resultante se presenta desde la interfaz. La búsqueda web continúa siendo condicional a la modalidad seleccionada; RAG se ejecuta cuando está habilitado.

**Aspectos todavía pendientes:** inspeccionar los contratos y la secuencia interna de `ClaimVerificationPipeline.py`, `ClaimExtractor.py` y `EvidenceVerifier.py`; determinar las reglas exactas de asociación de evidencias y agregación; medir la calidad de extracción y verificación; y comprobar si existen condiciones de excepción o consultas en las que el pipeline no se ejecuta. La ejecución confirmada no demuestra que los veredictos sean correctos ni que la respuesta original se modifique.

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

1. Conservar el recorrido de `main_multilinea.py` desde la entrada hasta la generación, la invocación del pipeline y la presentación del informe como flujo funcional de referencia.
2. Inspeccionar `Agent/ClaimVerificationPipeline.py`, identificando método público, argumentos, secuencia interna, salidas y manejo de errores.
3. Revisar `Agent/ClaimExtractor.py` y `Agent/EvidenceVerifier.py` en la misma versión del repositorio que se utilizará como referencia.
4. Analizar `Agent/MultilingualKnowledgeRetriever.py` y el módulo de búsqueda web efectivamente importado.
5. Registrar un caso completo de extremo a extremo con entradas y salidas de cada etapa, antes de implementar los instrumentos de medición.

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

**Hallazgo actualizado: ejecución efectiva del pipeline**

Para esta versión 0.5 se incorpora el resultado del seguimiento posterior de la interfaz: el pipeline no queda solamente importado e inicializado. En el recorrido de consulta examinado, después de que Ollama/Qwen3 devuelve la respuesta, se invoca `ClaimVerificationPipeline.run()` con la respuesta generada y las evidencias disponibles; luego, la interfaz utiliza el informe producido para presentar los resultados de verificación.

La secuencia funcional confirmada queda, por lo tanto, establecida así:

1. La interfaz prepara los mensajes y solicita la generación a Ollama/Qwen3.
2. Recibe el texto de respuesta generado.
3. Conserva/incorpora la respuesta en el flujo conversacional de la interfaz.
4. Ejecuta `ClaimVerificationPipeline.run()` sobre la respuesta y las evidencias disponibles.
5. Recibe el informe de verificación.
6. Presenta el informe mediante la función de visualización correspondiente.

**Límite de esta confirmación:** se confirma que la etapa de verificación se ejecuta después de la generación y que existe una salida de informe presentada por la interfaz. Esto no demuestra que la extracción sea exhaustiva, que los veredictos semánticos sean correctos ni que el sistema corrija o regenere automáticamente la respuesta cuando detecta afirmaciones no respaldadas. En esta especificación, la respuesta generada y el informe de verificación se consideran productos diferenciados, salvo que una inspección posterior del código demuestre una modificación explícita de la respuesta.

Queda pendiente inspeccionar el interior de `ClaimVerificationPipeline.py` y verificar con una traza instrumentada los argumentos exactos, las evidencias asociadas a cada afirmación, las salidas parciales, las rutas de error y la correspondencia entre el informe devuelto y lo que finalmente ve el usuario.

**Observación de consistencia sobre el punto de entrada**

Existe una diferencia que debe quedar registrada: la decisión de trabajo del proyecto identifica `main_multilinea.py` como la interfaz que se utiliza para las pruebas finales, mientras que la cabecera de la copia pública consultada lo describe como una versión de prueba que no reemplaza a `main.py`.

No se resolverá esta diferencia por inferencia. Antes de conectar la auditoría se deberá confirmar con el usuario qué archivo ejecuta efectivamente en su instalación y cotejar su contenido con la rama pública. La auditoría debe instrumentar el punto de entrada real, no uno supuesto.

**Conclusión del relevamiento de `main_multilinea.py`**

La inspección confirma que el archivo reúne responsabilidades de interfaz, validación de configuración, administración de conversaciones, inicialización y uso de RAG, búsqueda web condicional, preparación del contexto y comunicación con Ollama. Para esta versión también se considera confirmado el recorrido posterior a la generación: invocación efectiva del pipeline de verificación y presentación de su informe.

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
| Invocación efectiva del pipeline después de la generación | Confirmada en el recorrido examinado; falta verificar condiciones de excepción y cobertura de todas las rutas |
| Presentación del informe producido por el pipeline | Confirmada; falta auditar correspondencia campo por campo y exactitud de los resultados |
| Coincidencia entre la rama pública y el archivo local ejecutado | Pendiente de cotejar |

**Referencias de código consultadas:** `main_multilinea.py`, funciones `cargar_configuracion()`, `consultar_ollama()`, `guardar_conversacion()`, `listar_conversaciones()`, `recuperar_conversacion()`, `crear_recuperador()`, `construir_contexto_rag()`, `crear_buscador_web()`, `construir_contexto_web()`, `mostrar_informe_verificacion()`, `crear_sesion_entrada()`, `mostrar_ayuda()` e `iniciar_agente()`.

**Fuente:** [repositorio público GIAR-ORION, rama `main`](https://github.com/PabloFolino/GIAR-ORION), archivo `main_multilinea.py`.


#### 3.5.2. Ciclo completo de una consulta: desde el ingreso hasta la verificación

Esta sección documenta el recorrido de una consulta nueva desde que el usuario la ingresa hasta que recibe la respuesta y el informe de verificación. El objetivo es dejar explícita la secuencia de procesamiento y distinguir las operaciones obligatorias de aquellas que dependen de la configuración o de la modalidad seleccionada.

**A. Preparación de la sesión (una vez al iniciar la interfaz)**

1. `main_multilinea.py` carga y valida `config.json`.
2. Inicializa el historial de conversación y prepara el mensaje de sistema.
3. Inicializa el recuperador RAG si la configuración lo habilita.
4. Inicializa el buscador web si la búsqueda web está habilitada.
5. Crea la instancia de `ClaimVerificationPipeline` con los parámetros de conexión a Ollama y el modelo configurado.
6. Inicializa la modalidad de fuentes (el relevamiento de la interfaz identifica `local` como modalidad inicial) y entra en el ciclo de recepción de entradas.

La inicialización de un componente no implica que todas sus funciones se ejecuten en cada consulta. Por ejemplo, la búsqueda web depende de la modalidad de fuentes.

**B. Ingreso y clasificación de la entrada**

1. El usuario escribe una consulta, que puede ocupar varias líneas.
2. La interfaz reúne las líneas y procesa el envío como una única entrada.
3. Si la entrada está vacía, no inicia el procesamiento y vuelve a solicitar texto.
4. Si la entrada es un comando de la interfaz (`/salir`, `/limpiar`, `/guardar`, `/sesiones`, `/modo` o `/fuente`, entre otros), ejecuta la operación correspondiente. Los comandos no siguen el recorrido de generación de una consulta ordinaria.
5. Si es una consulta nueva, la agrega al historial conversacional con el rol `user`.

**C. Recuperación de información y preparación del contexto**

6. Si RAG está habilitado, la interfaz llama al recuperador documental con la pregunta y el valor `top_k` configurado.
7. El recuperador devuelve los fragmentos encontrados. La función de construcción de contexto prepara bloques con fuente, similitud y texto, y conserva también los resultados originales para su trazabilidad.
8. La interfaz prepara la búsqueda web de acuerdo con la modalidad de fuentes:
   - `local`: no agrega resultados web.
   - `web`: ejecuta búsqueda web libre.
   - `autorizada`: limita la búsqueda a los dominios configurados.
9. Si hay resultados web, los transforma en bloques de contexto con los datos de identificación de la fuente.
10. La interfaz reúne los contextos disponibles (RAG y, cuando corresponda, web). Si una fuente no está habilitada o no devuelve resultados, no debe suponerse que aporta evidencia.
11. Copia/prepara los mensajes de la conversación para la solicitud actual e incorpora el contexto recuperado como información temporal de esa solicitud. El contexto temporal no debe confundirse con el historial persistente de usuario y asistente.

**D. Generación de la respuesta**

12. La interfaz envía a Ollama una solicitud HTTP `POST` al endpoint `/api/chat`.
13. La solicitud contiene el modelo configurado, los mensajes preparados y las opciones del modo de generación, entre ellas `think` y `num_predict`; el relevamiento identifica `stream=False` y un timeout de 300 segundos.
14. Ollama ejecuta Qwen3 (o el modelo que indique la configuración efectiva) y devuelve el objeto de respuesta.
15. La interfaz extrae el texto de `message.content` y trata los errores HTTP, de conexión, JSON o de estructura de respuesta.
16. La respuesta generada se incorpora al flujo/historial conversacional y queda disponible para su presentación.

**E. Extracción y verificación posterior a la generación**

17. Una vez obtenida la respuesta, la interfaz invoca `ClaimVerificationPipeline.run()` con la respuesta generada y las evidencias disponibles para la verificación.
18. El pipeline coordina la extracción de afirmaciones y su contraste con las evidencias. En términos funcionales, intervienen `ClaimExtractor` y `EvidenceVerifier`; el orden interno, los argumentos exactos, las reglas de asociación y la agregación deben documentarse a partir de la inspección de sus implementaciones vigentes.
19. `ClaimExtractor` identifica las unidades/afirmaciones factuales que serán evaluadas. La extracción no determina por sí misma la verdad de una afirmación.
20. `EvidenceVerifier` contrasta las afirmaciones extraídas con las evidencias disponibles y produce resultados de verificación conforme a sus modelos y reglas efectivas.
21. El pipeline reúne los resultados y devuelve un informe estructurado a la interfaz.
22. La interfaz presenta el informe mediante `mostrar_informe_verificacion(...)`, incluyendo los campos que estén disponibles: estado, cobertura, cantidades, resultados por afirmación, puntajes, evidencias, fuentes y limitaciones.

**F. Resultado que recibe el usuario**

23. El usuario recibe la respuesta generada por Qwen3 y la información del informe de verificación presentada por la interfaz.
24. La verificación ocurre después de la generación. No debe afirmarse que el pipeline modifica, corrige, elimina o regenera automáticamente la respuesta, salvo que el código vigente demuestre expresamente ese comportamiento.
25. Una afirmación clasificada como no respaldada o contradictoria en el informe no implica, por sí sola, que haya sido retirada de la respuesta ya generada. La auditoría deberá comprobar qué contenido se muestra y si existe alguna acción posterior sobre la respuesta original.

**Resumen del loop**

```text
USUARIO
  |
  v
Ingreso de consulta multilínea
  |
  v
¿Es comando?
  |-- Sí --> Ejecutar comando --> volver a esperar entrada
  |
  `-- No
       |
       v
Agregar pregunta al historial
       |
       v
Recuperar evidencia local (RAG, si está habilitado)
       |
       v
Buscar en web según modalidad
(local / web / autorizada)
       |
       v
Construir contexto temporal
(RAG + web disponible)
       |
       v
Preparar mensajes + historial
       |
       v
POST /api/chat --> Ollama / Qwen3
       |
       v
Recibir respuesta generada
       |
       +------> Incorporar respuesta al historial
       |
       v
ClaimVerificationPipeline.run()
       |
       v
ClaimExtractor: extraer afirmaciones
       |
       v
EvidenceVerifier: contrastar con evidencias
       |
       v
Construir informe de verificación
       |
       v
Mostrar respuesta e informe al usuario
```

**Puntos de control de la auditoría**

| Punto | Dato que debe registrarse | Atribución inicial si falla |
|---|---|---|
| Entrada | Consulta original, modo y modalidad de fuente | Interfaz / entrada |
| Recuperación local | Fragmentos, fuentes, scores y orden | Recuperación RAG |
| Búsqueda externa | Consulta, resultados, dominios y errores | WebSearch |
| Contexto | Texto exacto incorporado a `messages` | Integración de contexto |
| Generación | Modelo, parámetros, mensajes, respuesta y metadatos | Ollama / generación LLM |
| Extracción | Unidades, claims, omisiones y errores | ClaimExtractor |
| Verificación | Evidencias por claim, puntajes y veredictos | EvidenceVerifier |
| Orquestación | Entrada/salida de `run()`, agregación y excepciones | ClaimVerificationPipeline |
| Presentación | Respuesta e informe efectivamente mostrados | Interfaz / presentación |

**Límites de conocimiento y confirmaciones pendientes**

El recorrido anterior documenta el flujo funcional confirmado para esta revisión. No reemplaza la inspección de los archivos internos ni una traza de ejecución con identificadores correlacionados. En particular, deben verificarse: si RAG se ejecuta en todas las consultas cuando está habilitado; el comportamiento exacto ante cero resultados; si el pipeline se ejecuta en todas las rutas de respuesta o solo en la ruta ordinaria; la forma exacta en que se entregan las evidencias; el tratamiento de errores del pipeline; y si el informe se presenta siempre o bajo alguna condición.

La eficacia se evaluará por separado. La auditoría debe medir al menos la cobertura de extracción, la precisión de los veredictos y la proporción de afirmaciones no respaldadas que llegan al usuario. No se considerará que el loop es correcto simplemente porque todas sus etapas hayan sido invocadas.

## 4. Modelo de arquitectura a verificar

El esquema representa el flujo de consulta actualizado. La respuesta de Qwen3 se obtiene primero; posteriormente se ejecuta el pipeline de verificación y se presenta su informe. La auditoría deberá determinar si la interfaz presenta ambos resultados por separado y confirmar todas las rutas de excepción.

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
                            |                |
                       Evidencias       según modalidad:
                       documentales     local/web/autorizada
             |              |                |
             +--------------+----------------+
                            |
                            v
                Construcción de contexto
                   temporal de consulta
                            |
                            v
                  Preparación de mensajes
                            |
                            v
                     Ollama / Qwen3
                            |
                            v
                  Respuesta generada
                     |             |
                     |             v
                     |    ClaimVerificationPipeline.run()
                     |             |
                     |       +-----+------+
                     |       |            |
                     |       v            v
                     |  ClaimExtractor  EvidenceVerifier
                     |       |            ^
                     |       +------------+
                     |             |
                     |             v
                     |     Informe estructurado
                     |             |
                     +-------------+
                            |
                            v
               Presentación al usuario:
                respuesta + informe
```

La representación no implica que el pipeline corrija la respuesta. La respuesta generada se produce antes de la verificación. La relación entre el informe y la respuesta final deberá verificarse en el código y en una ejecución instrumentada.

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

**Criterio de cierre:** diagrama de llamadas desde la entrada del usuario hasta la generación, invocación del pipeline y presentación del informe. El recorrido funcional se documenta en 3.5.2; queda pendiente una traza instrumentada que registre argumentos y salidas reales.

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

Seguir al menos un caso instrumentado de extremo a extremo, sin cambiar las decisiones del sistema. El loop funcional ya está documentado en 3.5.2; esta etapa debe producir una traza observada, no solo una descripción. Registrar el mismo `audit_case_id` en cada etapa:

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
11. Informe de verificación efectivamente presentado y relación (si existe) con la respuesta mostrada.

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
- claims no respaldados detectados por el pipeline pero que permanecen en la respuesta presentada;
- evidencia de cualquier corrección o regeneración posterior, si la implementación la contempla;
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
| 2 | Revisar `main_multilinea.py` y llamadas reales | Parcial: recorrido funcional hasta `ClaimVerificationPipeline.run()` y presentación del informe documentado; falta traza instrumentada y cotejo local |
| 3 | Revisar `MultilingualKnowledgeRetriever.py` | Pendiente |
| 4 | Revisar `WebSearch.py` y su integración | Pendiente |
| 5 | Revisar llamada a Ollama/Qwen3 | Parcial |
| 6 | Revisar `ClaimExtractor.py` | Parcial: versión 0.1.2 identificada |
| 7 | Revisar `EvidenceVerifier.py` | Pendiente |
| 8 | Revisar `ClaimVerificationPipeline.py` | Pendiente: ejecución desde la interfaz confirmada; contrato interno y agregación sin auditar |
| 9 | Trazar un caso integral de extremo a extremo | Pendiente: el loop está documentado; falta registrar una ejecución con entradas y salidas reales por etapa |
| 10 | Cerrar dataset, métricas y protocolo | Pendiente |
| 11 | Implementar controlador y módulos de auditoría | Pendiente |
| 12 | Ejecutar línea de base y generar informes | Pendiente |

## 14. Próximo paso concreto

El siguiente paso es completar el **Paso 0 y el Paso 1 sobre la copia local vigente del repositorio**, y realizar la traza instrumentada del **Paso 9**. El recorrido funcional de la interfaz hasta la invocación del pipeline ya quedó documentado; ahora corresponde inspeccionar el contrato interno de los componentes y medir una ejecución real. Para cotejar la versión local se necesitan estos archivos:

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


### A.7 Actualización 0.5 — Confirmación del recorrido de verificación

En la revisión que da origen a la versión 0.5 se incorpora la confirmación de que la verificación no queda limitada a la importación e inicialización del pipeline. El flujo examinado llega a la invocación efectiva de `ClaimVerificationPipeline.run()` después de recibir la respuesta de Ollama/Qwen3 y utiliza el informe devuelto para su presentación desde la interfaz.

El recorrido de una consulta nueva queda documentado en detalle en la sección 3.5.2. En síntesis:

1. La interfaz recibe la consulta y distingue comandos de consultas ordinarias.
2. Agrega la pregunta al historial.
3. Ejecuta RAG cuando está habilitado.
4. Ejecuta búsqueda web únicamente según la modalidad seleccionada.
5. Construye el contexto temporal y prepara los mensajes.
6. Solicita la generación a Ollama/Qwen3.
7. Recibe la respuesta y la incorpora al flujo conversacional.
8. Invoca el pipeline con la respuesta y las evidencias disponibles.
9. El pipeline coordina extracción y verificación.
10. La interfaz presenta el informe de verificación junto con el resultado de la consulta.

**Alcance:** esta actualización confirma la conexión funcional entre generación, ejecución del pipeline y presentación del informe. No certifica la corrección de los claims, la calidad de los veredictos, la exhaustividad de la extracción ni la existencia de un mecanismo automático de corrección o regeneración de la respuesta.

La confirmación debe completarse con una traza instrumentada que registre los argumentos exactos de `run()`, las evidencias asociadas a cada afirmación, los resultados de cada subcomponente y el contenido que efectivamente se presenta al usuario. La auditoría experimental todavía no se ha iniciado.

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
| Llamada al LLM, ejecución posterior del pipeline y presentación del informe | Flujo funcional confirmado; orden interno y trazabilidad fina pendientes |
| Contrato interno del pipeline | Pendiente |
| Algoritmo y parámetros efectivos de EvidenceVerifier | Pendiente |
| Auditoría experimental | No iniciada |

**Conclusión de esta actualización:** no hace falta que el usuario envíe un ZIP para comenzar el análisis estático del repositorio público. Se continuará utilizando la rama `main` como referencia y se señalarán expresamente las diferencias que solo puedan resolverse contrastando con la instalación local.
