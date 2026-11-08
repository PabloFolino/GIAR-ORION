# GIAR-ORION-AUDIT-SPEC-001

## Especificación de auditoría integral y relevamiento de arquitectura

| Campo     | Valor                                                                                                                  |
|:----------|:-----------------------------------------------------------------------------------------------------------------------|
| Proyecto  | GIAR-ORION                                                                                                             |
| Documento | GIAR-ORION-AUDIT-SPEC-001.md                                                                                           |
| Versión   | 0.6 — Relevamiento del pipeline, ClaimExtractor y EvidenceVerifier                                                     |
| Fecha     | 2026-11-08                                                                                                             |
| Estado    | En revisión: flujo de consulta y método `run()` relevados estáticamente; eficacia pendiente de evaluación experimental |
| Tipo      | Especificación de auditoría no intrusiva                                                                               |

## Índice

- [1. Propósito](#1-propósito)
- [2. Alcance y exclusiones](#2-alcance-y-exclusiones)
  - [2.1 Incluido](#21-incluido)
  - [2.2 Excluido](#22-excluido)
- [3. Sistema GIAR-ORION](#3-sistema-giar-orion)
  - [3.1 Descripción general del
    sistema](#31-descripción-general-del-sistema)
  - [3.2 Objetivo del sistema](#32-objetivo-del-sistema)
  - [3.3 Arquitectura general](#33-arquitectura-general)
  - [3.4 Estado de relevamiento de la
    arquitectura](#34-estado-de-relevamiento-de-la-arquitectura)
    - [3.4.1 Consideraciones para interpretar el
      estado](#341-consideraciones-para-interpretar-el-estado)
    - [3.4.2 Próximo tramo del
      relevamiento](#342-próximo-tramo-del-relevamiento)
  - [3.5 Relevamiento de componentes](#35-relevamiento-de-componentes)
    - [3.5.1 Interfaz principal:
      `main_multilinea.py`](#351-interfaz-principal-main_multilineapy)
  - [3.5.2 Ciclo completo de una consulta: desde el ingreso hasta la
    verificación](#352-ciclo-completo-de-una-consulta-desde-el-ingreso-hasta-la-verificación)
  - [3.5.3 Pipeline de verificación:
    `ClaimVerificationPipeline.run()`](#353-pipeline-de-verificación-claimverificationpipelinerun)
- [3.5.4 ClaimExtractor](#354-claimextractor)
- [3.5.6 EvidenceVerifier](#356-evidenceverifier)
- [4. Modelo de arquitectura a
  verificar](#4-modelo-de-arquitectura-a-verificar)
- [5. Relevamiento paso a paso del
  sistema](#5-relevamiento-paso-a-paso-del-sistema)
- [6. Diseño experimental](#6-diseño-experimental)
- [7. Métricas](#7-métricas)
- [8. Atribución de errores y
  propagación](#8-atribución-de-errores-y-propagación)
- [9. Ejecución y estados](#9-ejecución-y-estados)
- [10. Estructura de archivos
  propuesta](#10-estructura-de-archivos-propuesta)
- [11. Reproducibilidad y
  preservación](#11-reproducibilidad-y-preservación)
- [12. Criterios de aceptación de la
  auditoría](#12-criterios-de-aceptación-de-la-auditoría)
- [13. Plan de trabajo y avance](#13-plan-de-trabajo-y-avance)
- [14. Próximo paso concreto](#14-próximo-paso-concreto)
- [Anexo A — Verificación del repositorio
  público](#anexo-a--verificación-del-repositorio-público)

------------------------------------------------------------------------

## 1. Propósito

Definir una auditoría reproducible que mida, en una única ejecución
controlada, el comportamiento de:

1.  Recuperación documental RAG.
2.  `ClaimExtractor`.
3.  `EvidenceVerifier`.
4.  Generación de Qwen3.
5.  Pipeline integral de GIAR-ORION.

La auditoría debe determinar qué funciona, cuánto funciona, dónde se
producen los errores y cómo se propagan entre componentes. No debe
modificar el comportamiento del agente evaluado.

**Principio rector:** la auditoría observa y registra. No corrige,
reemplaza, ajusta ni reconfigura los componentes de GIAR-ORION durante
una ejecución.

## 2. Alcance y exclusiones

### 2.1 Incluido

- Relevamiento de la estructura real del repositorio.
- Identificación de módulos efectivamente importados por la interfaz
  principal.
- Registro de parámetros y versiones.
- Evaluación aislada de componentes y evaluación integrada.
- Dataset de referencia independiente.
- Métricas, trazabilidad por caso e informes reproducibles.
- Comparación entre ejecuciones sin sobrescribir resultados anteriores.

### 2.2 Excluido

- Modificar `main_multilinea.py` o cualquier módulo original.
- Reemplazar el recuperador RAG.
- Cambiar el modelo, los parámetros de generación o el prompt de
  producción.
- Modificar umbrales o reglas internas de `EvidenceVerifier`.
- Entrenar o ajustar modelos durante la auditoría.
- Considerar que un módulo funciona correctamente solo porque importa o
  devuelve una salida.

La auditoría podrá crear archivos propios dentro de `AUDIT/`, pero no
escribirá sobre los archivos de producción.

## 3. Sistema GIAR-ORION

### 3.1. Descripción general del sistema

GIAR-ORION es un agente de inteligencia artificial desarrollado como
entorno de asistencia para tareas de investigación, análisis y
desarrollo tecnológico, con especial orientación hacia la robótica, la
inteligencia artificial y los métodos de aprendizaje automático,
particularmente el aprendizaje por refuerzo y el aprendizaje profundo
por refuerzo.

El sistema combina un modelo de lenguaje de gran tamaño (LLM),
mecanismos de recuperación de información documental (RAG), fuentes de
información externas y componentes destinados a analizar y verificar las
afirmaciones presentes en las respuestas generadas.

La implementación relevada utiliza Ollama como servicio local para
ejecutar el modelo de lenguaje Qwen3 (`qwen3:8b`, según la configuración
consultada). El componente RAG permite recuperar fragmentos de la base
documental del proyecto y aportar ese material como contexto a la
generación. La interfaz también contempla modalidades de consulta que
incorporan búsqueda web, según la fuente seleccionada por el usuario.

GIAR-ORION no debe entenderse únicamente como un chatbot. Su propósito
técnico es integrar recuperación de conocimiento, generación de
respuestas y mecanismos de verificación, de modo que las respuestas
puedan relacionarse con información documental y evidencias
identificables.

Esta descripción resume el diseño y los componentes identificados. No
implica que todas las funciones se ejecuten en cada consulta ni que la
eficacia de cada componente ya haya sido demostrada. Esas cuestiones
forman parte del relevamiento y de la auditoría definidos en este
documento.

### 3.2. Objetivo del sistema

El objetivo general de GIAR-ORION es proporcionar un agente de apoyo a
la investigación y al desarrollo en robótica e inteligencia artificial
que pueda utilizar documentación técnica, analizar problemas, asistir en
tareas de programación y experimentación, y elaborar respuestas
fundamentadas en las fuentes de información disponibles.

En particular, el sistema busca:

1.  **Asistir en la investigación técnica:** ayudar a estudiar
    algoritmos, arquitecturas, modelos, artículos, documentación y
    repositorios vinculados con inteligencia artificial y robótica.
2.  **Recuperar conocimiento documental:** localizar información
    relevante en la base de conocimiento del proyecto y utilizarla como
    contexto para responder consultas.
3.  **Integrar fuentes de información:** permitir, de acuerdo con la
    modalidad seleccionada, el uso de documentación local y de
    resultados obtenidos mediante búsqueda web.
4.  **Analizar y explicar información:** producir respuestas que
    organicen conceptos, describan procedimientos, comparen alternativas
    y ayuden a interpretar resultados técnicos.
5.  **Asistir en el desarrollo de software:** colaborar en la
    comprensión, revisión, depuración y desarrollo de programas
    relacionados con los proyectos de investigación.
6.  **Verificar afirmaciones:** identificar afirmaciones factuales en
    las respuestas y contrastarlas con evidencias, distinguiendo entre
    información respaldada, contradicha o insuficiente.
7.  **Mantener trazabilidad:** facilitar la identificación de las
    fuentes utilizadas y de los resultados del proceso de verificación,
    en la medida en que los componentes actuales lo permitan.

Desde el punto de vista de esta auditoría, el objetivo no es determinar
si GIAR-ORION cumple idealmente todas esas aspiraciones, sino medir
experimentalmente en qué grado las cumple en su versión actual. Por
ello, cada capacidad deberá asociarse con pruebas, referencias
independientes y métricas específicas.

### 3.3. Arquitectura general

La arquitectura de GIAR-ORION está organizada alrededor de una interfaz
principal que coordina la interacción con el usuario y conecta los
componentes de recuperación, generación y verificación. En la revisión
que da origen a esta versión 0.5 se incorpora como confirmado que,
después de obtener la respuesta de Qwen3, la interfaz invoca el pipeline
de verificación y procesa su informe. La ejecución de esa etapa no debe
confundirse con una validación de su eficacia ni con una corrección
automática de la respuesta.

El punto de entrada vigente para las pruebas del proyecto es
`main_multilinea.py`. En el relevamiento realizado sobre la rama pública
`main` del repositorio se identificó que esta interfaz inicializa el
recuperador RAG, el buscador web y una instancia de
`ClaimVerificationPipeline`. También se observó que construye un
contexto temporal a partir de las fuentes seleccionadas y lo incorpora a
los mensajes enviados al servicio Ollama.

A nivel funcional, los componentes identificados cumplen los siguientes
roles:

- **Interfaz principal (`main_multilinea.py`):** recibe las consultas,
  administra la interacción, inicializa los componentes y coordina la
  preparación de la información que se envía al modelo.
- **Recuperación documental RAG
  (`Agent/MultilingualKnowledgeRetriever.py`):** busca fragmentos
  relevantes en la base de conocimiento local y devuelve resultados que
  pueden utilizarse como evidencia contextual.
- **Búsqueda web (`Agent/WebSearch.py` o módulo efectivamente
  importado):** obtiene información externa cuando la modalidad de
  fuentes seleccionada habilita esa búsqueda. Debe analizarse
  separadamente del RAG local.
- **Construcción del contexto:** reúne la consulta y los fragmentos
  recuperados para preparar el contenido que recibe el modelo. En la
  interfaz se identificó la función `construir_contexto_rag(...)`;
  también existe una construcción diferenciada del contexto web.
- **Servicio de generación (Ollama / Qwen3):** recibe los mensajes y el
  contexto preparado, y genera la respuesta destinada al usuario.
- **Extracción de afirmaciones (`Agent/ClaimExtractor.py`):** identifica
  afirmaciones factuales dentro de un texto de respuesta. Su función es
  extraerlas; no debe confundirse con determinar si son verdaderas.
- **Verificación de evidencias (`Agent/EvidenceVerifier.py`):**
  contrasta las afirmaciones con las evidencias disponibles y produce
  una clasificación de respaldo, contradicción o insuficiencia, de
  acuerdo con la implementación efectiva.
- **Coordinación de la verificación
  (`Agent/ClaimVerificationPipeline.py`):** organiza el proceso de
  extracción y verificación. Su secuencia interna, reglas de agregación
  y contrato de entrada/salida deben confirmarse mediante inspección del
  código.
- **Presentación de resultados:** la interfaz contiene una función
  específica para mostrar el informe de verificación. Debe comprobarse
  qué información del pipeline llega efectivamente a la presentación
  final.

El esquema siguiente representa el flujo funcional actualizado. La
conexión desde la respuesta generada hacia el pipeline y la presentación
del informe se consideran confirmadas según el seguimiento comunicado
para esta revisión. La secuencia interna del pipeline y la eficacia de
sus veredictos siguen sujetas a inspección y medición.

``` text
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

**Alcance de lo confirmado en esta versión:** además de la importación e
inicialización, se da por confirmado que el flujo de consulta llega a la
invocación efectiva de `ClaimVerificationPipeline` después de la
generación de Qwen3 y que el informe resultante se presenta desde la
interfaz. La búsqueda web continúa siendo condicional a la modalidad
seleccionada; RAG se ejecuta cuando está habilitado.

**Aspectos todavía pendientes:** inspeccionar los contratos y la
secuencia interna de `ClaimVerificationPipeline.py`, `ClaimExtractor.py`
y `EvidenceVerifier.py`; determinar las reglas exactas de asociación de
evidencias y agregación; medir la calidad de extracción y verificación;
y comprobar si existen condiciones de excepción o consultas en las que
el pipeline no se ejecuta. La ejecución confirmada no demuestra que los
veredictos sean correctos ni que la respuesta original se modifique.

### 3.4. Estado de relevamiento de la arquitectura

Esta sección registra qué elementos fueron identificados, qué función
cumplen dentro del diseño y cuál es el grado de confirmación alcanzado.
Se diferencia la existencia o inicialización de un componente de la
comprobación de su funcionamiento efectivo.

| Componente / elemento         | Archivo o referencia                               | Función dentro de GIAR-ORION                                                    | Estado del relevamiento                                                                                                                      |
|:------------------------------|:---------------------------------------------------|:--------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------|
| Interfaz principal            | `main_multilinea.py`                               | Recibe consultas y coordina la interacción con los componentes.                 | Identificada como punto de entrada vigente. Se continúa el análisis del flujo completo.                                                      |
| Recuperador RAG               | `Agent/MultilingualKnowledgeRetriever.py`          | Recupera fragmentos de la base documental local.                                | Inicialización identificada; algoritmo, ranking y contrato de salida pendientes de inspección completa.                                      |
| Construcción del contexto RAG | `construir_contexto_rag(...)` en la interfaz       | Prepara el contexto documental que se incorpora a la consulta del LLM.          | Función identificada; falta medir qué información recuperada llega efectivamente al prompt.                                                  |
| Búsqueda web                  | `Agent/WebSearch.py` o módulo importado            | Obtiene información externa cuando se selecciona una modalidad que la habilita. | Inicialización y modalidades identificadas; falta cerrar el análisis de implementación y fusión de resultados.                               |
| Servicio de lenguaje          | Ollama, endpoint local `/api/chat`                 | Proporciona el servicio de inferencia del modelo de lenguaje.                   | Identificado en el código consultado.                                                                                                        |
| Modelo LLM                    | `qwen3:8b`                                         | Genera respuestas a partir de la consulta, instrucciones y contexto recibido.   | Modelo observado en la configuración consultada; debe cotejarse con la configuración local efectiva al congelar la auditoría.                |
| Extractor de afirmaciones     | `Agent/ClaimExtractor.py`                          | Extrae afirmaciones factuales de la respuesta generada.                         | Módulo identificado; se observó la versión 0.1.2 en una copia consultada. Falta contrastar con el archivo vigente y completar su evaluación. |
| Verificador de evidencias     | `Agent/EvidenceVerifier.py`                        | Evalúa la relación entre cada afirmación y las evidencias disponibles.          | Módulo identificado; implementación, modelos, umbrales y reglas pendientes de inspección completa.                                           |
| Pipeline de verificación      | `Agent/ClaimVerificationPipeline.py`               | Coordina la extracción y la verificación de afirmaciones.                       | Importación e inicialización identificadas; invocación efectiva, secuencia interna y agregación pendientes de confirmar.                     |
| Presentación del informe      | `mostrar_informe_verificacion(...)` en la interfaz | Presenta al usuario los resultados de verificación disponibles.                 | Función identificada; falta comprobar la correspondencia completa entre la salida del pipeline y lo mostrado.                                |
| `ResponseVerifier.py`         | Archivo presente en el repositorio                 | Posible componente de verificación adicional o variante.                        | No debe considerarse parte del flujo activo hasta confirmar sus importaciones y llamadas.                                                    |

#### 3.4.1. Consideraciones para interpretar el estado

Los estados de la tabla tienen un alcance deliberadamente acotado:

- **Identificado:** se encontró el archivo, símbolo o componente en el
  repositorio.
- **Inicialización confirmada:** se observó código que crea o prepara el
  componente.
- **Invocación confirmada:** se verificó que el flujo ejecuta
  efectivamente el método correspondiente.
- **Funcionamiento evaluado:** existen pruebas con entradas controladas
  y resultados medidos.
- **Pendiente:** todavía no se dispone de evidencia suficiente para
  afirmar lo anterior.

Que un módulo esté importado o inicializado no demuestra por sí solo que
se ejecute en todas las consultas ni que sus resultados sean correctos.
Esa diferencia será mantenida en todo el documento y en los informes de
auditoría.

#### 3.4.2. Próximo tramo del relevamiento

El análisis continuará siguiendo el recorrido efectivo de una consulta
en este orden:

1.  Conservar el recorrido de `main_multilinea.py` desde la entrada
    hasta la generación, la invocación del pipeline y la presentación
    del informe como flujo funcional de referencia.
2.  Inspeccionar `Agent/ClaimVerificationPipeline.py`, identificando
    método público, argumentos, secuencia interna, salidas y manejo de
    errores.
3.  Revisar `Agent/ClaimExtractor.py` y `Agent/EvidenceVerifier.py` en
    la misma versión del repositorio que se utilizará como referencia.
4.  Analizar `Agent/MultilingualKnowledgeRetriever.py` y el módulo de
    búsqueda web efectivamente importado.
5.  Registrar un caso completo de extremo a extremo con entradas y
    salidas de cada etapa, antes de implementar los instrumentos de
    medición.

**Regla de trabajo:** primero comprender y documentar el funcionamiento
real; después diseñar las pruebas; finalmente medir. No se modificará
ningún componente de producción para facilitar la auditoría.

### 3.5. Relevamiento de componentes

En esta sección se documentará cada componente de GIAR-ORION a partir de
la inspección de su código fuente. El relevamiento no se limitará a
describir la finalidad declarada de cada archivo: deberá reconstruir
cómo se ejecuta, qué módulos utiliza, qué datos recibe, qué resultados
produce y de qué manera se conecta con los demás componentes.

Cada componente se analizará siguiendo una estructura común:

1.  Identificación del archivo y versión examinada.
2.  Responsabilidad dentro del sistema.
3.  Dependencias e importaciones.
4.  Configuración y parámetros utilizados.
5.  Funciones y clases principales.
6.  Entradas y salidas.
7.  Secuencia de ejecución.
8.  Manejo de errores y condiciones excepcionales.
9.  Archivos, servicios o recursos externos utilizados.
10. Estado de verificación y aspectos pendientes.

El relevamiento se realizará sobre la rama pública `main` del
repositorio como referencia inicial. Antes de implementar la auditoría
se deberá cotejar esa versión con la copia local que se utiliza para
ejecutar GIAR-ORION. La inspección estática del repositorio no equivale
a una prueba de ejecución.

#### 3.5.1. Interfaz principal: `main_multilinea.py`

**Identificación y función general**

El archivo `main_multilinea.py` implementa una interfaz conversacional
de consola para GIAR-ORION. Su función principal es recibir consultas
del usuario —incluidas consultas de varias líneas—, administrar el
historial de la sesión, recuperar información documental, incorporar
resultados web cuando se selecciona esa modalidad y enviar los mensajes
preparados al servicio de lenguaje Ollama.

En el repositorio público consultado, el archivo presenta una cabecera
que lo describe como una interfaz conversacional con entrada multilínea.
La misma cabecera indica que esta variante permite procesar varias
líneas como una única consulta y que conserva el procesamiento de
memoria, RAG y Ollama. También contiene una advertencia textual que la
identifica como versión de prueba y señala que no reemplaza a `main.py`.
Esta declaración deberá contrastarse con la versión local que el usuario
ejecuta actualmente y con la decisión de proyecto sobre el punto de
entrada vigente.

**Fuente examinada:** repositorio público `PabloFolino/GIAR-ORION`, rama
`main`, archivo `main_multilinea.py`.

**Dependencias e importaciones identificadas**

En el código consultado se identifican, entre otras, las siguientes
dependencias:

| Dependencia                                                 | Uso observado                                                                                  |
|:------------------------------------------------------------|:-----------------------------------------------------------------------------------------------|
| `json`                                                      | Lectura de configuración y serialización de conversaciones.                                    |
| `sys`                                                       | Incorporación del directorio `Agent` a la ruta de importación cuando corresponde.              |
| `urllib.request` y `urllib.error`                           | Comunicación HTTP con el servicio Ollama y tratamiento de errores de conexión.                 |
| `datetime`                                                  | Generación de marcas temporales para las conversaciones guardadas.                             |
| `pathlib.Path`                                              | Construcción y administración de rutas del proyecto.                                           |
| `prompt_toolkit.PromptSession`                              | Recepción de consultas en la consola.                                                          |
| `prompt_toolkit.key_binding.KeyBindings`                    | Definición de atajos para enviar consultas multilínea.                                         |
| `Agent.ClaimVerificationPipeline.ClaimVerificationPipeline` | Importación de la clase que coordina la extracción y verificación de afirmaciones.             |
| `MultilingualKnowledgeRetriever`                            | Recuperador documental importado desde el directorio `Agent` durante la inicialización de RAG. |
| `WebSearch`                                                 | Buscador web importado desde `Agent` cuando la búsqueda externa está habilitada.               |

La presencia de una importación no demuestra que el componente se
ejecute durante cada consulta. En particular, la conexión efectiva del
pipeline de verificación se trata como un punto específico de análisis
más adelante.

**Organización de rutas y configuración**

El archivo determina la ubicación del proyecto mediante
`Path(__file__).resolve().parent` y utiliza esa ruta como `BASE_DIR`. A
partir de ella establece:

- `CONFIG_FILE`: ubicación de `config.json`.
- `AGENT_DIR`: ubicación del directorio `Agent`.

La función `cargar_configuracion()` abre el archivo JSON y comprueba la
presencia de campos esenciales, entre ellos `agent_name`, `version`,
`llm` y `paths`. También valida la configuración del proveedor LLM, los
modos de generación, los parámetros `think` y `num_predict`, la
configuración RAG y la configuración de búsqueda web.

Entre las validaciones observadas se encuentran:

- El proveedor configurado debe ser `ollama`.
- Deben existir los datos necesarios para identificar el modelo y la URL
  base del servicio.
- Cada modo de generación debe definir `think` como booleano y
  `num_predict` como entero positivo.
- El modo inicial debe estar definido entre los modos disponibles.
- Si RAG está habilitado, el modo debe ser `e5`, `bge-m3` o `hybrid`.
- `top_k` debe ser un entero positivo.
- Los pesos de E5 y BGE-M3 deben estar entre 0 y 1; en modo híbrido
  deben sumar 1.
- Si la búsqueda web está habilitada, el proveedor admitido por esta
  implementación es `ddgs`; también se valida la cantidad máxima de
  resultados y la lista de dominios autorizados.

Estas validaciones permiten detectar errores de configuración antes de
iniciar la interacción. No demuestran, por sí mismas, que los modelos o
servicios estén disponibles ni que sus resultados sean correctos.

**Comunicación con Ollama y generación de respuestas**

La función `consultar_ollama(config, mensajes, modo)` construye una
solicitud HTTP dirigida al endpoint `/api/chat` de Ollama. El contenido
enviado incluye:

- El identificador del modelo definido en la configuración.
- La lista de mensajes que representa la conversación y el contexto de
  la consulta.
- `stream=False`, por lo que la respuesta se solicita sin transmisión
  progresiva.
- El parámetro `think` correspondiente al modo seleccionado.
- `options.num_predict`, tomado de la configuración del modo.

La solicitud utiliza el método HTTP `POST` y establece un timeout de 300
segundos. La función contempla errores HTTP, errores de conexión, JSON
inválido y respuestas que no contienen el campo `message.content`
esperado. Cuando la respuesta tiene la estructura prevista, devuelve el
texto generado y el objeto completo recibido de Ollama.

Este último punto es relevante para la auditoría: la función devuelve
tanto el texto como los metadatos de respuesta. Por lo tanto, se deberá
comprobar qué información se conserva en el flujo de ejecución y si los
metadatos disponibles permiten medir tokens, tiempos y motivo de
finalización.

**Memoria e historial de conversaciones**

El archivo administra el historial de la sesión mediante una lista de
mensajes con roles `system`, `user` y `assistant`.

Se identifican funciones para:

- Determinar el directorio de conversaciones a partir de `paths.memory`.
- Guardar la conversación en archivos JSON.
- Listar las conversaciones guardadas.
- Recuperar una conversación seleccionada por número.

Al guardar, se conservan únicamente mensajes de usuario y asistente; la
instrucción interna del sistema no se incluye en el archivo. El registro
incorpora nombre y versión del agente, modelo, fecha de guardado,
cantidad de mensajes y contenido de la conversación. También se evita
sobrescribir un archivo cuando coincide la marca temporal, agregando un
contador al nombre.

La recuperación valida que el archivo contenga una lista de mensajes y
conserva solamente entradas con roles `user` o `assistant` y contenido
textual.

**Recuperación documental RAG**

La función `crear_recuperador(config)` inicializa el componente RAG
cuando la configuración lo habilita. Para ello importa
`MultilingualKnowledgeRetriever` desde el directorio `Agent` y lo
instancia con:

- Directorio de conocimiento (`knowledge_dir`).
- Modo de recuperación.
- Dispositivo de ejecución.
- Peso de E5.
- Peso de BGE-M3.
- Parámetro `local_files_only`.

La función informa el modo activo y, cuando corresponde, los pesos
utilizados en modo híbrido.

La función `construir_contexto_rag(recuperador, pregunta, top_k)`
ejecuta `recuperador.search(pregunta, top_k=top_k)`. Si no existe
recuperador o no se obtienen resultados, devuelve contexto y listas
vacías.

Cuando hay resultados, la función:

1.  Extrae las fuentes sin repetirlas.
2.  Recorre los fragmentos recuperados.
3.  Construye bloques que identifican la fuente y el valor de similitud.
4.  Incorpora el texto de cada fragmento.
5.  Antecede los bloques con instrucciones que indican al LLM que
    utilice el material como evidencia, que no invente datos ausentes y
    que reconozca cuándo el contexto es insuficiente.
6.  Devuelve tres elementos: contexto formateado, fuentes y resultados
    originales.

La devolución de los resultados originales es especialmente importante
para la auditoría: permite conservar los fragmentos y sus metadatos para
contrastarlos posteriormente con las afirmaciones generadas.

**Búsqueda web y modalidades de fuentes**

La función `crear_buscador_web(config)` inicializa `WebSearch` solamente
cuando `web_search.enabled` está habilitado. El código importa
`WebSearch` desde el directorio `Agent` y lo instancia con parámetros de
región y búsqueda segura.

La función `construir_contexto_web(...)` contempla tres modalidades:

- `local`: no incorpora resultados web; utiliza la recuperación
  documental local.
- `web`: ejecuta una búsqueda web libre.
- `autorizada`: restringe la búsqueda a los dominios configurados en
  `authorized_domains`.

Los resultados se convierten en bloques que incluyen título, dominio,
URL y descripción. El contexto web se identifica expresamente como
información externa y se instruye al modelo para distinguir hechos
publicados, inferencias y datos no verificados.

La modalidad inicial observada en la función de inicio es `local`. El
usuario puede cambiarla mediante los comandos de la interfaz. Por
consiguiente, la búsqueda web no debe considerarse una etapa obligatoria
de todas las consultas.

**Entrada multilínea y comandos**

La función `crear_sesion_entrada()` utiliza `PromptSession` y define
atajos para enviar una consulta completa. El comportamiento previsto es:

- `Enter`: agrega una nueva línea.
- `Ctrl+S`: intenta enviar la consulta completa.
- `Esc` seguido de `Enter`: permite un envío alternativo.
- `/enviar` en una línea independiente: envía el contenido acumulado.

La función `mostrar_ayuda(...)` informa los comandos disponibles. Entre
ellos se encuentran `/help`, `/salir`, `/limpiar`, `/guardar`,
`/sesiones`, `/abrir N`, `/modo rapido`, `/modo investigacion` y los
comandos `/fuente`.

La función `iniciar_agente(config)` constituye el núcleo de la interfaz.
Inicializa la configuración activa, el recuperador RAG, el buscador web
y una instancia de `ClaimVerificationPipeline`. Luego crea el historial
inicial con el mensaje de sistema y entra en un ciclo de recepción de
consultas y comandos.

**Secuencia de procesamiento identificada**

A partir del código consultado, el flujo de una consulta puede
describirse, en los tramos visibles, de la siguiente manera:

1.  La interfaz recibe el texto completo del usuario.
2.  Si el texto está vacío, vuelve a solicitar una entrada.
3.  Si corresponde a un comando, ejecuta la operación solicitada y no lo
    trata como consulta al LLM.
4.  Si es una consulta, agrega el mensaje del usuario al historial de la
    sesión.
5.  Ejecuta la recuperación RAG, si está habilitada.
6.  Ejecuta la construcción del contexto web según la modalidad
    seleccionada.
7.  Reúne los contextos no vacíos.
8.  Copia el historial para preparar los mensajes de la consulta actual.
9.  Inserta el contexto recuperado como mensaje de sistema temporal, sin
    incorporarlo al historial persistente.
10. Prepara los mensajes que se enviarán al modelo.

El comentario del código señala que los contextos RAG y web se agregan
solamente a la solicitud actual, mientras que el historial conserva la
pregunta y la respuesta. Esta separación debe preservarse en el diseño
de auditoría: el contexto realmente enviado al modelo no es
necesariamente idéntico al historial guardado.

**Presentación del informe de verificación**

La función `mostrar_informe_verificacion(informe)` está destinada a
presentar el resultado producido por `ClaimVerificationPipeline`. No
ejecuta verificaciones ni modifica el informe recibido.

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

La existencia de esta función demuestra que la interfaz contempla una
presentación detallada del informe. No demuestra que la función sea
invocada efectivamente después de cada respuesta.

**Hallazgo actualizado: ejecución efectiva del pipeline**

Para esta versión 0.5 se incorpora el resultado del seguimiento
posterior de la interfaz: el pipeline no queda solamente importado e
inicializado. En el recorrido de consulta examinado, después de que
Ollama/Qwen3 devuelve la respuesta, se invoca
`ClaimVerificationPipeline.run()` con la respuesta generada y las
evidencias disponibles; luego, la interfaz utiliza el informe producido
para presentar los resultados de verificación.

La secuencia funcional confirmada queda, por lo tanto, establecida así:

1.  La interfaz prepara los mensajes y solicita la generación a
    Ollama/Qwen3.
2.  Recibe el texto de respuesta generado.
3.  Conserva/incorpora la respuesta en el flujo conversacional de la
    interfaz.
4.  Ejecuta `ClaimVerificationPipeline.run()` sobre la respuesta y las
    evidencias disponibles.
5.  Recibe el informe de verificación.
6.  Presenta el informe mediante la función de visualización
    correspondiente.

**Límite de esta confirmación:** se confirma que la etapa de
verificación se ejecuta después de la generación y que existe una salida
de informe presentada por la interfaz. Esto no demuestra que la
extracción sea exhaustiva, que los veredictos semánticos sean correctos
ni que el sistema corrija o regenere automáticamente la respuesta cuando
detecta afirmaciones no respaldadas. En esta especificación, la
respuesta generada y el informe de verificación se consideran productos
diferenciados, salvo que una inspección posterior del código demuestre
una modificación explícita de la respuesta.

Queda pendiente inspeccionar el interior de
`ClaimVerificationPipeline.py` y verificar con una traza instrumentada
los argumentos exactos, las evidencias asociadas a cada afirmación, las
salidas parciales, las rutas de error y la correspondencia entre el
informe devuelto y lo que finalmente ve el usuario.

**Observación de consistencia sobre el punto de entrada**

Existe una diferencia que debe quedar registrada: la decisión de trabajo
del proyecto identifica `main_multilinea.py` como la interfaz que se
utiliza para las pruebas finales, mientras que la cabecera de la copia
pública consultada lo describe como una versión de prueba que no
reemplaza a `main.py`.

No se resolverá esta diferencia por inferencia. Antes de conectar la
auditoría se deberá confirmar con el usuario qué archivo ejecuta
efectivamente en su instalación y cotejar su contenido con la rama
pública. La auditoría debe instrumentar el punto de entrada real, no uno
supuesto.

**Conclusión del relevamiento de `main_multilinea.py`**

La inspección confirma que el archivo reúne responsabilidades de
interfaz, validación de configuración, administración de conversaciones,
inicialización y uso de RAG, búsqueda web condicional, preparación del
contexto y comunicación con Ollama. Para esta versión también se
considera confirmado el recorrido posterior a la generación: invocación
efectiva del pipeline de verificación y presentación de su informe.

El análisis permite identificar claramente los límites entre
recuperación y generación:

- Si el fragmento correcto no aparece entre los resultados de `search`,
  el problema corresponde a **recuperación RAG**.
- Si el fragmento fue recuperado pero no se incorpora correctamente al
  mensaje enviado a Ollama, el problema corresponde a **integración del
  contexto**.
- Si la evidencia llega al modelo y la respuesta la interpreta
  incorrectamente, la omite o agrega datos no respaldados, el problema
  corresponde a **generación LLM (Qwen3)**.
- Si la respuesta contiene afirmaciones que deberían verificarse, pero
  no se ejecuta el pipeline o su resultado no se presenta, el problema
  corresponde a **integración de la verificación en la interfaz**; no
  debe atribuirse automáticamente al modelo NLI ni al extractor.

El relevamiento de este archivo queda **parcialmente completado**. La
confirmación del flujo final de generación y verificación requiere
inspeccionar el tramo restante del archivo y contrastarlo con la copia
local vigente.

| Elemento examinado                                                    | Resultado del relevamiento                                                                                    |
|:----------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------|
| Configuración y validaciones                                          | Identificadas                                                                                                 |
| Comunicación HTTP con Ollama                                          | Identificada                                                                                                  |
| Gestión del historial y archivos de conversación                      | Identificada                                                                                                  |
| Inicialización de RAG                                                 | Identificada                                                                                                  |
| Construcción del contexto RAG y conservación de resultados originales | Identificada                                                                                                  |
| Inicialización de búsqueda web DDGS                                   | Identificada                                                                                                  |
| Modalidades local, web y autorizada                                   | Identificadas                                                                                                 |
| Preparación de mensajes para el LLM                                   | Identificada parcialmente                                                                                     |
| Importación e inicialización de `ClaimVerificationPipeline`           | Confirmadas                                                                                                   |
| Invocación efectiva del pipeline después de la generación             | Confirmada en el recorrido examinado; falta verificar condiciones de excepción y cobertura de todas las rutas |
| Presentación del informe producido por el pipeline                    | Confirmada; falta auditar correspondencia campo por campo y exactitud de los resultados                       |
| Coincidencia entre la rama pública y el archivo local ejecutado       | Pendiente de cotejar                                                                                          |

**Referencias de código consultadas:** `main_multilinea.py`, funciones
`cargar_configuracion()`, `consultar_ollama()`,
`guardar_conversacion()`, `listar_conversaciones()`,
`recuperar_conversacion()`, `crear_recuperador()`,
`construir_contexto_rag()`, `crear_buscador_web()`,
`construir_contexto_web()`, `mostrar_informe_verificacion()`,
`crear_sesion_entrada()`, `mostrar_ayuda()` e `iniciar_agente()`.

**Fuente:** [repositorio público GIAR-ORION, rama
`main`](https://github.com/PabloFolino/GIAR-ORION), archivo
`main_multilinea.py`.

#### 3.5.2. Ciclo completo de una consulta: desde el ingreso hasta la verificación

Esta sección documenta el recorrido de una consulta nueva desde que el
usuario la ingresa hasta que recibe la respuesta y el informe de
verificación. El objetivo es dejar explícita la secuencia de
procesamiento y distinguir las operaciones obligatorias de aquellas que
dependen de la configuración o de la modalidad seleccionada.

**A. Preparación de la sesión (una vez al iniciar la interfaz)**

1.  `main_multilinea.py` carga y valida `config.json`.
2.  Inicializa el historial de conversación y prepara el mensaje de
    sistema.
3.  Inicializa el recuperador RAG si la configuración lo habilita.
4.  Inicializa el buscador web si la búsqueda web está habilitada.
5.  Crea la instancia de `ClaimVerificationPipeline` con los parámetros
    de conexión a Ollama y el modelo configurado.
6.  Inicializa la modalidad de fuentes (el relevamiento de la interfaz
    identifica `local` como modalidad inicial) y entra en el ciclo de
    recepción de entradas.

La inicialización de un componente no implica que todas sus funciones se
ejecuten en cada consulta. Por ejemplo, la búsqueda web depende de la
modalidad de fuentes.

**B. Ingreso y clasificación de la entrada**

1.  El usuario escribe una consulta, que puede ocupar varias líneas.
2.  La interfaz reúne las líneas y procesa el envío como una única
    entrada.
3.  Si la entrada está vacía, no inicia el procesamiento y vuelve a
    solicitar texto.
4.  Si la entrada es un comando de la interfaz (`/salir`, `/limpiar`,
    `/guardar`, `/sesiones`, `/modo` o `/fuente`, entre otros), ejecuta
    la operación correspondiente. Los comandos no siguen el recorrido de
    generación de una consulta ordinaria.
5.  Si es una consulta nueva, la agrega al historial conversacional con
    el rol `user`.

**C. Recuperación de información y preparación del contexto**

6.  Si RAG está habilitado, la interfaz llama al recuperador documental
    con la pregunta y el valor `top_k` configurado.
7.  El recuperador devuelve los fragmentos encontrados. La función de
    construcción de contexto prepara bloques con fuente, similitud y
    texto, y conserva también los resultados originales para su
    trazabilidad.
8.  La interfaz prepara la búsqueda web de acuerdo con la modalidad de
    fuentes:
    - `local`: no agrega resultados web.
    - `web`: ejecuta búsqueda web libre.
    - `autorizada`: limita la búsqueda a los dominios configurados.
9.  Si hay resultados web, los transforma en bloques de contexto con los
    datos de identificación de la fuente.
10. La interfaz reúne los contextos disponibles (RAG y, cuando
    corresponda, web). Si una fuente no está habilitada o no devuelve
    resultados, no debe suponerse que aporta evidencia.
11. Copia/prepara los mensajes de la conversación para la solicitud
    actual e incorpora el contexto recuperado como información temporal
    de esa solicitud. El contexto temporal no debe confundirse con el
    historial persistente de usuario y asistente.

**D. Generación de la respuesta**

12. La interfaz envía a Ollama una solicitud HTTP `POST` al endpoint
    `/api/chat`.
13. La solicitud contiene el modelo configurado, los mensajes preparados
    y las opciones del modo de generación, entre ellas `think` y
    `num_predict`; el relevamiento identifica `stream=False` y un
    timeout de 300 segundos.
14. Ollama ejecuta Qwen3 (o el modelo que indique la configuración
    efectiva) y devuelve el objeto de respuesta.
15. La interfaz extrae el texto de `message.content` y trata los errores
    HTTP, de conexión, JSON o de estructura de respuesta.
16. La respuesta generada se incorpora al flujo/historial conversacional
    y queda disponible para su presentación.

**E. Extracción y verificación posterior a la generación**

17. Una vez obtenida la respuesta, la interfaz invoca
    `ClaimVerificationPipeline.run()` con la respuesta generada y las
    evidencias disponibles para la verificación.
18. El pipeline coordina la extracción de afirmaciones y su contraste
    con las evidencias. En términos funcionales, intervienen
    `ClaimExtractor` y `EvidenceVerifier`; el orden interno, los
    argumentos exactos, las reglas de asociación y la agregación deben
    documentarse a partir de la inspección de sus implementaciones
    vigentes.
19. `ClaimExtractor` identifica las unidades/afirmaciones factuales que
    serán evaluadas. La extracción no determina por sí misma la verdad
    de una afirmación.
20. `EvidenceVerifier` contrasta las afirmaciones extraídas con las
    evidencias disponibles y produce resultados de verificación conforme
    a sus modelos y reglas efectivas.
21. El pipeline reúne los resultados y devuelve un informe estructurado
    a la interfaz.
22. La interfaz presenta el informe mediante
    `mostrar_informe_verificacion(...)`, incluyendo los campos que estén
    disponibles: estado, cobertura, cantidades, resultados por
    afirmación, puntajes, evidencias, fuentes y limitaciones.

**F. Resultado que recibe el usuario**

23. El usuario recibe la respuesta generada por Qwen3 y la información
    del informe de verificación presentada por la interfaz.
24. La verificación ocurre después de la generación. No debe afirmarse
    que el pipeline modifica, corrige, elimina o regenera
    automáticamente la respuesta, salvo que el código vigente demuestre
    expresamente ese comportamiento.
25. Una afirmación clasificada como no respaldada o contradictoria en el
    informe no implica, por sí sola, que haya sido retirada de la
    respuesta ya generada. La auditoría deberá comprobar qué contenido
    se muestra y si existe alguna acción posterior sobre la respuesta
    original.

**Resumen del loop**

``` text
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

| Punto              | Dato que debe registrarse                           | Atribución inicial si falla |
|:-------------------|:----------------------------------------------------|-----------------------------|
| Entrada            | Consulta original, modo y modalidad de fuente       | Interfaz / entrada          |
| Recuperación local | Fragmentos, fuentes, scores y orden                 | Recuperación RAG            |
| Búsqueda externa   | Consulta, resultados, dominios y errores            | WebSearch                   |
| Contexto           | Texto exacto incorporado a `messages`               | Integración de contexto     |
| Generación         | Modelo, parámetros, mensajes, respuesta y metadatos | Ollama / generación LLM     |
| Extracción         | Unidades, claims, omisiones y errores               | ClaimExtractor              |
| Verificación       | Evidencias por claim, puntajes y veredictos         | EvidenceVerifier            |
| Orquestación       | Entrada/salida de `run()`, agregación y excepciones | ClaimVerificationPipeline   |
| Presentación       | Respuesta e informe efectivamente mostrados         | Interfaz / presentación     |

**Límites de conocimiento y confirmaciones pendientes**

El recorrido anterior documenta el flujo funcional confirmado para esta
revisión. No reemplaza la inspección de los archivos internos ni una
traza de ejecución con identificadores correlacionados. En particular,
deben verificarse: si RAG se ejecuta en todas las consultas cuando está
habilitado; el comportamiento exacto ante cero resultados; si el
pipeline se ejecuta en todas las rutas de respuesta o solo en la ruta
ordinaria; la forma exacta en que se entregan las evidencias; el
tratamiento de errores del pipeline; y si el informe se presenta siempre
o bajo alguna condición.

La eficacia se evaluará por separado. La auditoría debe medir al menos
la cobertura de extracción, la precisión de los veredictos y la
proporción de afirmaciones no respaldadas que llegan al usuario. No se
considerará que el loop es correcto simplemente porque todas sus etapas
hayan sido invocadas.

#### 3.5.3. Pipeline de verificación: `ClaimVerificationPipeline.run()`

**Identificación y fuente examinada**

Se inspeccionó el archivo `Agent/ClaimVerificationPipeline.py` de la
rama pública `main` del repositorio GIAR-ORION. El archivo declara que
su responsabilidad es orquestar `ClaimExtractor` y `EvidenceVerifier`
sin modificar esos componentes.

- Clase: `ClaimVerificationPipeline`.
- Versión declarada: `0.1.0`.
- Método principal: `run(response, rag_results=None, web_results=None)`.
- Método alternativo: `verify(...)`, que delega en `run(...)`.
- Función auxiliar: `run_pipeline(...)`, que crea una instancia y
  ejecuta `run(...)`.
- Fuente: [`Agent/ClaimVerificationPipeline.py`, rama
  `main`](https://raw.githubusercontent.com/PabloFolino/GIAR-ORION/main/Agent/ClaimVerificationPipeline.py).

El análisis que sigue describe el código fuente consultado. Antes de
considerar estos datos como configuración definitiva de la instalación
utilizada para las pruebas, habrá que cotejar el archivo local y
registrar su hash.

**Responsabilidad del método `run()`**

`run()` recibe una respuesta textual ya generada y coordina dos
operaciones principales:

1.  Extraer afirmaciones factuales mediante `ClaimExtractor`.
2.  Contrastar esas afirmaciones con las evidencias disponibles mediante
    `EvidenceVerifier`.

El método devuelve un diccionario con el estado del proceso, los
resultados de extracción y verificación, versiones de los componentes y
limitaciones conocidas. No genera una respuesta nueva ni contiene, en el
código inspeccionado, una operación que reescriba la respuesta original.

**Firma y argumentos**

``` python
def run(
    self,
    response: str,
    rag_results: Optional[list] = None,
    web_results: Optional[list] = None,
) -> dict:
```

| Argumento     | Tipo declarado   | Función                                                       |
|:--------------|:-----------------|:--------------------------------------------------------------|
| `response`    | `str`            | Texto de respuesta generado que se analizará.                 |
| `rag_results` | `Optional[list]` | Resultados RAG que se entregan al verificador como evidencia. |
| `web_results` | `Optional[list]` | Resultados web que se entregan al verificador como evidencia. |

El método exige que `response` sea una cadena no vacía. Si no se cumple
esa condición, lanza `ValueError` antes de iniciar la extracción. Los
argumentos `rag_results` y `web_results` son opcionales y, si no se
suministran, su valor predeterminado es `None`.

**Preparación de los componentes: constructor `__init__()`**

Aunque el foco de esta sección es `run()`, su comportamiento depende de
cómo se construyen los componentes:

- Si no se proporciona `claim_extractor`, el constructor importa
  `ClaimExtractor` y lo instancia.
- A ese constructor le pasa `base_url` y `model`, cuyos valores
  predeterminados se obtienen de `ollama_base_url` y `ollama_model`.
- Si no se proporciona `evidence_verifier`, importa e instancia
  `EvidenceVerifier`.
- El constructor permite inyectar instancias alternativas, por ejemplo
  mocks para pruebas independientes.
- Si ocurre una excepción durante la inicialización, la envuelve en
  `ClaimVerificationPipelineError`.

La versión declarada por el pipeline es `0.1.0`. Las versiones del
extractor y del verificador se obtienen dinámicamente mediante el
atributo `VERSION` de cada instancia, si existe.

**Secuencia interna de ejecución de `run()`**

El método sigue el orden que se detalla a continuación.

**1. Validación de la respuesta**

Comprueba que `response` sea un `str` y que no esté vacío ni contenga
únicamente espacios. Si la validación falla, lanza una excepción
`ValueError`. Esta validación no se registra como uno de los estados
estructurados del diccionario: la excepción se propaga al código que
llamó a `run()`.

**2. Creación del informe inicial**

Antes de ejecutar los componentes, crea un diccionario con los
siguientes campos:

| Campo                      | Valor inicial o significado                                                               |
|:---------------------------|:------------------------------------------------------------------------------------------|
| `pipeline`                 | Nombre `ClaimVerificationPipeline`.                                                       |
| `pipeline_version`         | Versión declarada por la clase.                                                           |
| `status`                   | Inicialmente `None`; luego refleja el resultado o la condición de detención.              |
| `can_present_as_supported` | Inicialmente `False`; solo cambia a `True` para estado semántico exactamente `SUPPORTED`. |
| `claims_submitted`         | Inicialmente `0`; luego contiene la cantidad de afirmaciones enviadas al verificador.     |
| `extractor_version`        | Versión del extractor, si está declarada.                                                 |
| `verifier_version`         | Versión del verificador, si está declarada.                                               |
| `extraction`               | Resultado de extracción, inicialmente `None`.                                             |
| `verification`             | Resultado de verificación, inicialmente `None`.                                           |
| `reference_status`         | Estado global de referencias informado por el verificador, si está disponible.            |
| `semantic_status`          | Estado del análisis de respaldo semántico, si está disponible.                            |
| `limitations`              | Lista inicial de limitaciones conocidas.                                                  |

El código incorpora cuatro limitaciones iniciales:

- La cobertura estructural del extractor no demuestra exhaustividad
  semántica.
- Los puntajes NLI no son probabilidades calibradas.
- El respaldo semántico no equivale a una verificación científica
  definitiva.
- Los resultados DDGS contienen título y fragmento, no necesariamente el
  contenido completo de la página.

**3. Extracción de afirmaciones**

El pipeline ejecuta:

``` python
extraction = self.claim_extractor.extract(response)
```

Si la llamada produce una excepción, el método:

- establece `status = EXTRACTION_ERROR`;
- registra el tipo y el mensaje de la excepción en `error`;
- devuelve inmediatamente el informe.

Si el extractor no devuelve un diccionario, también establece
`EXTRACTION_ERROR`, registra el motivo y detiene el proceso.

**4. Control de cobertura estructural**

El método exige que el resultado de extracción contenga `complete` con
valor booleano `True`.

Si `extraction.get("complete") is not True`:

- establece `status = EXTRACTION_INCOMPLETE`;
- copia los errores informados por el extractor en `extraction_errors`;
- agrega una limitación indicando que la verificación semántica se
  detuvo;
- devuelve el informe sin llamar a la verificación semántica de claims.

Esta condición es importante: en esta implementación, la verificación
semántica de las afirmaciones no continúa cuando la extracción no
alcanza la cobertura estructural exigida.

El propio docstring del pipeline aclara que `complete=True` indica
cobertura estructural, no exhaustividad semántica. Por lo tanto, no
demuestra que se hayan identificado todas las afirmaciones factuales
presentes en la respuesta.

**5. Validación y normalización de las afirmaciones**

Cuando la extracción está marcada como completa, el método auxiliar
`_extract_claim_texts(extraction)`:

- exige que `extraction["claims"]` sea una lista;
- exige que cada elemento sea un diccionario;
- exige que cada elemento contenga un campo `claim` de tipo cadena y no
  vacío;
- elimina espacios al principio y al final del texto;
- construye una lista de cadenas con las afirmaciones.

Si la estructura no cumple el contrato esperado, `run()` establece
`EXTRACTION_ERROR`, registra el error y devuelve el informe.

Luego asigna a `claims_submitted` la cantidad de afirmaciones extraídas
y validadas.

**6. Rama especial: no se detectaron afirmaciones**

Si la lista de afirmaciones queda vacía, el pipeline no llama al
verificador con `claims=[]`. En cambio, ejecuta:

``` python
verification = self.evidence_verifier.verify(
    response,
    rag_results=rag_results,
    web_results=web_results,
    claims=None,
)
```

Si la llamada falla, establece `VERIFICATION_ERROR`, registra la
excepción y devuelve el informe.

Si la llamada finaliza correctamente:

- guarda el resultado en `verification`;
- obtiene `reference_status` a partir de
  `verification["overall_status"]`, si el resultado es un diccionario;
- establece `status = NO_FACTUAL_CLAIMS`;
- establece `semantic_status = "NOT_PERFORMED"`;
- agrega una limitación que indica que no se detectaron afirmaciones
  factuales y que no se realizó verificación semántica;
- devuelve el informe.

Por consiguiente, `NO_FACTUAL_CLAIMS` no significa que el texto haya
sido declarado verdadero. Significa que el extractor no produjo
afirmaciones factuales para la etapa semántica. El verificador recibe la
respuesta completa con `claims=None`, pero el pipeline marca
expresamente la verificación semántica como no realizada.

**7. Rama ordinaria: verificación de afirmaciones**

Cuando existe al menos una afirmación validada, el pipeline llama:

``` python
verification = self.evidence_verifier.verify(
    response,
    rag_results=rag_results,
    web_results=web_results,
    claims=claim_texts,
)
```

Por lo tanto, el verificador recibe simultáneamente:

- la respuesta completa;
- los resultados RAG;
- los resultados web;
- la lista de afirmaciones extraídas.

Si la llamada produce una excepción, el pipeline establece
`VERIFICATION_ERROR`, registra el tipo y el mensaje de la excepción y
devuelve el informe.

Si la llamada finaliza correctamente:

- guarda el diccionario de salida en `verification`;
- obtiene `reference_status` desde el campo `overall_status` del
  resultado, cuando este campo existe.

**8. Comprobación del informe semántico**

El pipeline no utiliza cualquier campo del resultado del verificador
como estado semántico. Busca específicamente:

``` text
verification
  └── checks
       └── semantic_support_check
```

El método auxiliar `_semantic_report(...)` devuelve ese objeto solamente
cuando las estructuras intermedias son diccionarios y el informe
semántico también es un diccionario.

Si ese informe no existe o no tiene la estructura esperada:

- establece `status = SEMANTIC_VERIFICATION_NOT_PERFORMED`;
- establece `semantic_status = "NOT_PERFORMED"`;
- agrega una limitación indicando que el verificador no devolvió el
  informe esperado;
- devuelve el resultado.

**9. Validación del estado semántico**

Cuando el informe semántico existe, el pipeline lee su campo
`overall_status`. Reconoce los siguientes valores:

- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `MIXED_EVIDENCE`
- `CONTRADICTED`
- `INSUFFICIENT`
- `CONFLICTING_EVIDENCE`

Si el valor no pertenece a esa lista, el pipeline establece
`SEMANTIC_VERIFICATION_NOT_PERFORMED`, agrega una limitación y devuelve
el informe.

Si el valor es reconocido:

- copia ese valor a `semantic_status`;
- lo copia también a `status`;
- establece `can_present_as_supported = True` únicamente cuando el valor
  es exactamente `SUPPORTED`.

El código indica expresamente que el estado principal del pipeline
procede del análisis semántico, no del estado global de referencias del
`EvidenceVerifier`. Por ello, `reference_status` y `semantic_status` son
campos diferentes y no deben confundirse.

**10. Devolución del informe**

Cuando se alcanza una salida normal, el método devuelve el diccionario
estructurado. Según la rama ejecutada, puede contener resultados
completos, resultados parciales o una condición de detención. No todas
las salidas significan que se haya realizado verificación semántica.

**Diagrama de decisión de `run()`**

``` text
run(response, rag_results, web_results)
             |
             v
¿response es string no vacío?
       | No
       +----> ValueError (se propaga)
       |
      Sí
       |
       v
Crear informe inicial
       |
       v
ClaimExtractor.extract(response)
       |
       +---- excepción / salida no dict
       |           |
       |           v
       |     EXTRACTION_ERROR
       |           |
       |           v
       |        devolver
       |
       v
¿extraction.complete es True?
       | No
       +----> EXTRACTION_INCOMPLETE
       |       detener verificación semántica
       |       devolver
       |
      Sí
       |
       v
Validar y extraer textos de claims
       |
       +---- estructura inválida
       |           |
       |           v
       |     EXTRACTION_ERROR
       |           |
       |           v
       |        devolver
       |
       v
¿Hay claims?
   | No                         | Sí
   v                            v
EvidenceVerifier.verify(     EvidenceVerifier.verify(
 claims=None)                 claims=claim_texts)
   |                            |
   v                            v
NO_FACTUAL_CLAIMS          ¿Excepción?
semantic NOT_PERFORMED       | Sí
   |                         v
   |                   VERIFICATION_ERROR
   |                         |
   |                         v
   |                      devolver
   |                            |
   |                           No
   |                            |
   |                            v
   |                   ¿Existe semantic_support_check?
   |                      | No
   |                      v
   |              SEMANTIC_VERIFICATION_NOT_PERFORMED
   |                      |
   |                      v
   |                   devolver
   |                      |
   |                     Sí
   |                      |
   |                      v
   |              ¿Estado reconocido?
   |                 | No
   |                 v
   |        SEMANTIC_VERIFICATION_NOT_PERFORMED
   |                 |
   |                 v
   |              devolver
   |                 |
   |                Sí
   |                 |
   |                 v
   |       status = semantic_status
   |       can_present_as_supported =
   |          (status == SUPPORTED)
   |                 |
   +-----------------+
             |
             v
       devolver informe
```

**Estados y condiciones de salida definidos en el código**

| Estado                                | Condición que lo produce                                                        | ¿Se realizó verificación semántica de claims?                                    |
|:--------------------------------------|:--------------------------------------------------------------------------------|:---------------------------------------------------------------------------------|
| `NO_FACTUAL_CLAIMS`                   | Extracción estructural completa, pero lista de claims vacía.                    | No. El verificador recibe `claims=None`, pero el pipeline marca `NOT_PERFORMED`. |
| `EXTRACTION_INCOMPLETE`               | El extractor no devuelve `complete is True`.                                    | No; el pipeline se detiene antes de verificar.                                   |
| `EXTRACTION_ERROR`                    | Excepción del extractor, salida no diccionario o estructura de claims inválida. | No.                                                                              |
| `VERIFICATION_ERROR`                  | Excepción durante la llamada a `EvidenceVerifier.verify(...)`.                  | No se obtiene un resultado válido de esa llamada.                                |
| `SEMANTIC_VERIFICATION_NOT_PERFORMED` | No existe el informe semántico esperado o su estado no es reconocido.           | No se dispone de un estado semántico válido.                                     |
| `SUPPORTED`                           | Estado semántico reconocido y exactamente igual a `SUPPORTED`.                  | Sí, según el resultado informado por el verificador.                             |
| `PARTIALLY_SUPPORTED`                 | Estado semántico reconocido.                                                    | Sí.                                                                              |
| `MIXED_EVIDENCE`                      | Estado semántico reconocido.                                                    | Sí.                                                                              |
| `CONTRADICTED`                        | Estado semántico reconocido.                                                    | Sí.                                                                              |
| `INSUFFICIENT`                        | Estado semántico reconocido.                                                    | Sí.                                                                              |
| `CONFLICTING_EVIDENCE`                | Estado semántico reconocido.                                                    | Sí.                                                                              |

La tabla describe las ramas y etiquetas del código; no expresa una
valoración de la precisión real de esos resultados.

**Contrato de salida**

El diccionario devuelto contiene, como estructura base:

``` json
{
  "pipeline": "ClaimVerificationPipeline",
  "pipeline_version": "0.1.0",
  "status": null,
  "can_present_as_supported": false,
  "claims_submitted": 0,
  "extractor_version": null,
  "verifier_version": null,
  "extraction": null,
  "verification": null,
  "reference_status": null,
  "semantic_status": null,
  "limitations": []
}
```

Según la rama de ejecución, se agregan campos como `error` o
`extraction_errors`, y se completan los resultados de extracción y
verificación. Los valores `null` del ejemplo son valores iniciales
ilustrativos; no representan una salida única ni garantizada.

**Qué hace y qué no hace `run()`**

De acuerdo con el código inspeccionado, `run()`:

- recibe una respuesta ya generada;
- solicita la extracción de afirmaciones;
- controla la integridad estructural declarada por el extractor;
- valida el formato de los claims;
- entrega respuesta, claims y evidencias al verificador;
- interpreta el informe semántico devuelto;
- construye un estado global del pipeline;
- informa limitaciones y errores.

En cambio, el método no muestra operaciones para:

- modificar el texto original de la respuesta;
- eliminar afirmaciones no respaldadas;
- redactar una respuesta sustitutiva;
- volver a llamar a Qwen3 para corregir la respuesta;
- incorporar automáticamente las conclusiones del informe al historial
  como una respuesta corregida.

Por lo tanto, **la verificación es posterior y evaluativa; no
constituye, en el código de `run()` inspeccionado, un mecanismo de
autocorrección de la respuesta**.

**Distinciones necesarias para la auditoría**

1.  `complete=True` significa cobertura estructural según el extractor,
    no que todos los claims semánticamente relevantes hayan sido
    encontrados.
2.  `NO_FACTUAL_CLAIMS` no equivale a `SUPPORTED`.
3.  `reference_status` y `semantic_status` representan información
    distinta.
4.  `can_present_as_supported` solo es verdadero para el estado exacto
    `SUPPORTED`; no lo es para `PARTIALLY_SUPPORTED`.
5.  Los estados semánticos son resultados informados por
    `EvidenceVerifier`; su calidad debe medirse con datos de referencia
    independientes.
6.  Un estado `SUPPORTED` no constituye certificación científica
    definitiva, tal como advierte el propio pipeline.
7.  La captura de excepciones dentro de `run()` permite devolver ciertos
    errores como estados estructurados, pero la validación inicial de
    `response` puede lanzar `ValueError` hacia el llamador.

**Conclusión del relevamiento**

La inspección estática de `ClaimVerificationPipeline.py` permite
reconstruir el flujo de control de `run()` y sus principales contratos.
El método actúa como orquestador: no decide directamente la verdad de
una afirmación mediante una regla propia, sino que utiliza la extracción
de `ClaimExtractor` y la salida de `EvidenceVerifier`.

Se identifica una política de detención conservadora cuando la
extracción no alcanza `complete=True`, y una rama especial cuando no se
detectan afirmaciones factuales. También se observa que el estado final
del pipeline se deriva del informe `semantic_support_check` cuando este
existe y contiene una etiqueta reconocida.

**Estado:** relevamiento estático de `run()` completado sobre la rama
pública consultada. Quedan pendientes el cotejo con la copia local, la
inspección detallada de `ClaimExtractor` y `EvidenceVerifier`, y las
pruebas controladas que permitan medir la calidad de las decisiones. No
se considera evaluada la eficacia del pipeline por el solo hecho de
haber reconstruido su lógica.

**Referencias de código**

- `ClaimVerificationPipeline.py`, líneas 12–46: clase, versión y
  constructor.
- Líneas 47–76: lectura de versiones, extracción del estado de
  referencia, localización del informe semántico y validación de claims.
- Líneas 77–108: firma, validación de entrada y creación del informe.
- Líneas 109–127: extracción y control de cobertura estructural.
- Líneas 128–156: validación de claims y rama sin afirmaciones
  factuales.
- Líneas 157–195: verificación semántica, interpretación de estados y
  devolución.
- Líneas 196–205: alias `verify()` y función auxiliar `run_pipeline()`.

### 3.5.4. Extractor de afirmaciones: `ClaimExtractor`

**Identificación y fuente examinada**

Se inspeccionó `Agent/ClaimExtractor.py` de la rama pública `main` del
repositorio GIAR-ORION.

- Clase: `ClaimExtractor`.
- Versión declarada: `0.1.2`.
- Método principal: `extract(response)`.
- Servicio de inferencia: Ollama, endpoint `/api/chat`.
- Modelo: el que recibe el constructor; en la integración del pipeline
  se toma por defecto de `ollama_model` (configuración de GIAR-ORION).
- Fuente examinada:
  `https://raw.githubusercontent.com/PabloFolino/GIAR-ORION/main/Agent/ClaimExtractor.py`.

La descripción del propio módulo delimita su responsabilidad: segmentar
la respuesta, solicitar a Ollama la extracción de afirmaciones factuales
atómicas, exigir una clasificación para cada unidad y detectar omisiones
o inconsistencias estructurales. El módulo no verifica la verdad de las
afirmaciones; esa tarea corresponde a `EvidenceVerifier`.

**Constructor y parámetros**

``` python
ClaimExtractor(
    base_url: str,
    model: str,
    think: bool = False,
    num_predict: int = 2048,
    timeout: int = 180,
)
```

| Parámetro     | Valor predeterminado / validación | Función                                              |
|---------------|-----------------------------------|------------------------------------------------------|
| `base_url`    | Obligatorio, texto no vacío       | URL base de Ollama.                                  |
| `model`       | Obligatorio, texto no vacío       | Modelo que realiza la extracción.                    |
| `think`       | `False`, debe ser booleano        | Valor enviado a la API de Ollama.                    |
| `num_predict` | `2048`, entero positivo           | Límite de generación configurado para la extracción. |
| `timeout`     | `180` segundos, entero positivo   | Tiempo máximo de espera de la solicitud HTTP.        |

El constructor elimina la barra final de `base_url` y conserva los
parámetros en la instancia. El código valida tipos y valores positivos
para los parámetros numéricos.

En la integración documentada en 3.5.3, el pipeline crea el extractor
con `base_url` y `model` derivados de `ollama_base_url` y
`ollama_model`, salvo que se inyecte una instancia o se proporcionen
opciones específicas.

**Etapa 1: segmentación de la respuesta**

El método estático `_split_units(response)`:

1.  Divide el texto por saltos de línea.
2.  Elimina espacios al principio y al final de cada línea.
3.  Descarta líneas vacías.
4.  Divide cada línea cuando detecta puntuación terminal (`.`, `!`, `?`)
    seguida de espacios y de un comienzo probable de oración.
5.  Devuelve una lista de unidades textuales.

La expresión regular utiliza como comienzo probable una letra mayúscula,
un dígito o determinados signos de apertura seguidos de esos caracteres.
El propio código califica esta segmentación como sencilla y heurística,
y aclara que no constituye un análisis lingüístico completo.

**Implicación para la auditoría:** una unidad puede contener más de una
afirmación, por lo que el modelo debe descomponerla; pero una
segmentación incorrecta puede dificultar la cobertura. Abreviaturas,
decimales, puntuación interna, nombres propios y comienzos en minúscula
son casos que deben probarse. Esta es una hipótesis de riesgo derivada
de la regla de segmentación, no un fallo experimental ya demostrado.

**Etapa 2: construcción del prompt**

`_build_prompt(units)` asigna un identificador entero a cada unidad,
comenzando en 1, y solicita al modelo:

- analizar la respuesta unidad por unidad;
- identificar todas las afirmaciones factuales explícitas;
- dividir las oraciones con varias afirmaciones en claims atómicos;
- no agregar información ni completar datos implícitos;
- no corregir el contenido original;
- no convertir preguntas, opiniones, títulos o instrucciones en
  afirmaciones factuales;
- devolver exactamente una entrada de `coverage` por unidad;
- clasificar cada unidad como `FACTUAL` o `NON_FACTUAL`;
- incluir uno o más claims para una unidad `FACTUAL`;
- devolver una lista vacía de claims para una unidad `NON_FACTUAL`.

El formato solicitado es JSON con `coverage` y `notes`. Cada elemento de
`coverage` debe incluir `unit_id`, `status` y `claims`.

**Etapa 3: llamada a Ollama**

`_call_ollama(prompt)` envía una solicitud HTTP `POST` a `/api/chat`
con:

- el modelo configurado;
- un mensaje `system` que ordena actuar como extractor, no evaluar la
  verdad y no agregar conocimiento;
- el prompt de extracción como mensaje `user`;
- `stream=False`;
- `think` según el constructor;
- `format="json"`;
- `options.num_predict` según el constructor;
- `options.temperature=0`.

La solicitud utiliza el timeout configurado. El método contempla errores
HTTP, errores de conexión y respuestas JSON inválidas. También exige que
Ollama devuelva `message.content` como texto. Los errores de esta etapa
se expresan mediante `ClaimExtractorError`.

**Etapa 4: decodificación del JSON**

`_extract_json(text)`:

1.  Elimina espacios externos.
2.  Tolera cercas Markdown externas del tipo \`\`\`json.
3.  Intenta decodificar el texto completo como JSON.
4.  Si falla, busca el primer `{` y el último `}` e intenta decodificar
    ese segmento.
5.  Exige que el resultado sea un objeto/diccionario.

Si no puede obtener un objeto válido, lanza `ClaimExtractorError`. La
tolerancia a texto externo no elimina la necesidad de validar después la
estructura del objeto.

**Etapa 5: validación estructural y cálculo de `complete`**

`_validate_extraction(units, data, model)` comprueba el contenido de
`coverage`:

- `coverage` debe ser una lista.
- Cada elemento debe ser un diccionario.
- `unit_id` debe ser un entero y no puede ser booleano.
- El identificador debe corresponder a una unidad existente.
- `status` debe ser `FACTUAL` o `NON_FACTUAL`.
- `claims` debe ser una lista.
- Cada claim debe ser una cadena no vacía.
- Una unidad `FACTUAL` debe tener al menos un claim.
- Una unidad `NON_FACTUAL` no debe contener claims.
- No debe haber identificadores duplicados.
- No debe faltar ningún identificador esperado.
- No deben aparecer identificadores adicionales.
- `notes` debe ser una lista; si no lo es, se registra un error y se
  normaliza a una lista vacía.

Por cada claim aceptado se crea un objeto con:

| Campo         | Significado                                            |
|---------------|--------------------------------------------------------|
| `claim`       | Texto de la afirmación atómica, sin espacios externos. |
| `unit_id`     | Identificador de la unidad de origen.                  |
| `source_unit` | Texto original de la unidad de la que se extrajo.      |

El campo `complete` se calcula como `not errors`. Por lo tanto, expresa
que la estructura y la cobertura de unidades superaron las validaciones
implementadas. **No mide si el modelo encontró semánticamente todas las
afirmaciones verdaderas o verificables del texto.**

El resultado incluye `extractor`, `version`, `model`, `complete`,
`unit_count`, `classified_unit_count`, `claim_count`, `claims`,
`coverage`, `errors`, `notes` y `limitations`.

**Etapa 6: método público `extract(response)`**

La secuencia efectiva es:

1.  Valida que `response` sea una cadena no vacía.
2.  Ejecuta `_split_units(response)`.
3.  Si no hay unidades, lanza `ClaimExtractorError`.
4.  Construye el prompt mediante `_build_prompt(units)`.
5.  Llama a Ollama mediante `_call_ollama(prompt)`.
6.  Decodifica la respuesta con `_extract_json(raw_output)`.
7.  Valida estructura y cobertura mediante `_validate_extraction(...)`.
8.  Devuelve el diccionario serializable.

El método no recibe resultados RAG ni web y no consulta fuentes externas
para contrastar los claims. Trabaja sobre el texto de respuesta que
recibe.

**Diagrama de ejecución**

``` text
Respuesta de Qwen3
        |
        v
Validar texto no vacío
        |
        v
_split_units(response)
        |
        v
Asignar unit_id a cada unidad
        |
        v
_build_prompt(units)
        |
        v
Ollama /api/chat
(modelo configurado, temperature=0, format=json)
        |
        v
_extract_json(raw_output)
        |
        v
_validate_extraction(units, data, model)
        |
        +---- errores estructurales ----> complete=False
        |                                  |
        |                                  v
        |                         Pipeline detiene verificación
        |
        +---- sin errores --------------> complete=True
                                           |
                                           v
                                  claims + coverage + notes
                                           |
                                           v
                                  ClaimVerificationPipeline
```

**Limitaciones declaradas por el propio módulo**

El resultado incluye expresamente estas limitaciones:

1.  La cobertura estructural no garantiza exhaustividad semántica.
2.  El modelo puede omitir afirmaciones o clasificarlas incorrectamente.
3.  La extracción no verifica la verdad ni el respaldo de las
    afirmaciones.
4.  Si `complete` es `False`, la respuesta no debe considerarse
    verificada.

**Análisis técnico y riesgos que deben medirse**

| Riesgo                                                      | Por qué importa                                                                                             | Prueba necesaria                                                                           |
|-------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| Omisión semántica                                           | Una unidad puede estar clasificada correctamente, pero contener un claim que el modelo no extrajo.          | Comparar contra claims de referencia anotados independientemente.                          |
| Atomización incorrecta                                      | Una oración con varios hechos puede quedar como un único claim o dividirse de forma inadecuada.             | Casos con conjunciones, relaciones causales, fechas, cantidades y condiciones.             |
| Segmentación heurística                                     | La expresión regular puede separar o mantener juntas unidades de manera no lingüísticamente ideal.          | Casos con abreviaturas, decimales, listas, títulos y oraciones que comienzan en minúscula. |
| Clasificación incorrecta                                    | Una opinión, instrucción o pregunta puede marcarse como factual, o viceversa.                               | Dataset equilibrado con unidades factuales y no factuales.                                 |
| JSON estructuralmente válido pero semánticamente incompleto | `complete=True` podría coexistir con claims omitidos o mal interpretados.                                   | Medir Recall y F1 semánticos, no solo `complete`.                                          |
| Truncamiento de generación                                  | `num_predict=2048` limita la salida y una respuesta extensa podría no producir toda la estructura esperada. | Registrar metadatos de Ollama y probar respuestas de longitud creciente.                   |
| Dependencia de Qwen/Ollama                                  | La extracción requiere que el servicio local esté disponible y responda con el esquema esperado.            | Medir latencia, tasa de errores y reproducibilidad por modelo/configuración.               |

Estas filas describen riesgos a evaluar, no resultados de pruebas ya
ejecutadas.

**Métricas específicas para `ClaimExtractor`**

La evaluación deberá usar una respuesta de entrada fija y un conjunto de
claims esperados anotado manualmente. Se medirán:

- Precision, Recall y F1 de claims extraídos.
- Tasa de omisión de afirmaciones.
- Tasa de claims espurios.
- Exactitud de atomización.
- Exactitud de clasificación `FACTUAL` / `NON_FACTUAL`.
- Cobertura estructural (`complete`).
- Correspondencia correcta entre `claim`, `unit_id` y `source_unit`.
- Latencia, errores y longitud de la respuesta de Ollama.

La cobertura estructural se informará separada del Recall semántico. No
se aceptará `complete=True` como sustituto de una extracción correcta.

**Atribución de errores**

- Si el texto original contiene una afirmación factual y el extractor no
  la devuelve, el fallo corresponde a **ClaimExtractor**.
- Si el extractor devuelve una afirmación que no está en el texto
  original, corresponde a **ClaimExtractor**.
- Si la afirmación fue extraída correctamente pero `EvidenceVerifier` la
  clasifica mal, corresponde al **EvidenceVerifier**.
- Si el extractor falla por indisponibilidad o respuesta inválida de
  Ollama, se registrará como error técnico de extracción, no como error
  factual de Qwen3 en la respuesta original.

**Conclusión del relevamiento**

La implementación de `ClaimExtractor` es un extractor basado en un LLM
local, precedido por una segmentación heurística y seguido por
validaciones estructurales estrictas. Su principal aporte al pipeline es
producir claims y comprobar que todas las unidades recibieron una
clasificación estructuralmente válida.

El punto crítico es que `complete=True` no certifica que se hayan
extraído todas las afirmaciones. El valor debe interpretarse
exclusivamente como integridad estructural. La calidad semántica
requiere medir omisiones, falsos claims y atomización contra referencias
independientes.

**Estado:** inspección estática de la versión `0.1.2` completada sobre
la rama pública consultada. Falta cotejar el archivo local y ejecutar
pruebas controladas.

**Referencias de código:** `ClaimExtractor.py`, líneas 28–65 (clase y
constructor); 67–92 (segmentación); 94–128 (JSON); 130–196 (Ollama);
198–232 (prompt); 233–360 (validación); 361–386 (método `extract`).

### 3.5.5. Numeración reservada

La numeración 3.5.5 se conserva sin asignar hasta definir el siguiente
componente o aspecto del relevamiento. No se introduce contenido
supuesto para completar la secuencia.

### 3.5.6. Verificador de evidencias: `EvidenceVerifier`

**Identificación y fuente examinada**

Se inspeccionó `Agent/EvidenceVerifier.py` de la rama pública `main` del
repositorio GIAR-ORION.

- Clase: `EvidenceVerifier`.
- Versión declarada: `0.3.0`.
- Método principal de integración:
  `verify(response, rag_results=None, web_results=None, claims=None)`.
- Método de verificación semántica:
  `verify_claims(claims, rag_results=None, web_results=None, max_evidence_per_claim=10)`.
- Modelo NLI predeterminado:
  `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`.
- Modelo de adjudicación local predeterminado: `qwen3:8b`.
- Fuente examinada:
  `https://raw.githubusercontent.com/PabloFolino/GIAR-ORION/main/Agent/EvidenceVerifier.py`.

**Hallazgo central: el verificador combina dos mecanismos diferentes**

La implementación actual no utiliza mDeBERTa como autoridad final del
veredicto. Ejecuta dos niveles:

1.  **NLI con mDeBERTa:** calcula puntajes de entailment, neutral y
    contradiction para cada par evidencia-afirmación. Los conserva como
    información diagnóstica.
2.  **Adjudicación semántica con Qwen3 mediante Ollama:** recibe la
    afirmación y los fragmentos de evidencia y asigna a cada evidencia
    una etiqueta `SUPPORTED`, `CONTRADICTED` o `INSUFFICIENT`. Esta
    adjudicación es la que gobierna el estado final.

El docstring inicial del archivo todavía contiene una descripción de una
versión limitada que dice que no determina respaldo semántico y no
consulta modelos externos. Sin embargo, el cuerpo actual de la clase, su
constructor y sus métodos sí implementan carga NLI y adjudicación local
con Ollama. Esta inconsistencia documental debe quedar registrada: para
describir el comportamiento ejecutable se toma como referencia el código
de los métodos, no solamente el texto introductorio del módulo.

**Constructor y parámetros**

``` python
EvidenceVerifier(
    nli_model_name=DEFAULT_NLI_MODEL,
    entailment_threshold=0.80,
    contradiction_threshold=0.80,
    decision_margin=0.15,
    device=None,
    ollama_url="http://localhost:11434",
    adjudication_model="qwen3:8b",
    adjudication_timeout=90,
    use_ollama_adjudication=True,
)
```

| Parámetro                 |                                        Valor predeterminado | Función observada                                                                                   |
|---------------------------|------------------------------------------------------------:|-----------------------------------------------------------------------------------------------------|
| `nli_model_name`          | `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` | Modelo NLI cargado mediante Transformers.                                                           |
| `entailment_threshold`    |                                                      `0.80` | Se conserva en configuración y en el informe; no gobierna el veredicto final en esta versión.       |
| `contradiction_threshold` |                                                      `0.80` | Se conserva en configuración y en el informe; no gobierna el veredicto final en esta versión.       |
| `decision_margin`         |                                                      `0.15` | Se conserva en configuración y en el informe; no gobierna el veredicto final en esta versión.       |
| `device`                  |                                                      `None` | Si no se indica, selecciona `cuda` cuando PyTorch informa disponibilidad; en caso contrario, `cpu`. |
| `ollama_url`              |                                    `http://localhost:11434` | URL base del servicio de adjudicación.                                                              |
| `adjudication_model`      |                                                  `qwen3:8b` | Modelo LLM que decide las etiquetas semánticas por evidencia.                                       |
| `adjudication_timeout`    |                                               `90` segundos | Timeout de la llamada de adjudicación a Ollama.                                                     |
| `use_ollama_adjudication` |                                                      `True` | Habilita la adjudicación local con Qwen3.                                                           |

El constructor valida que los tres parámetros numéricos de umbral/margen
estén entre 0 y 1. Inicializa las referencias internas del tokenizer y
del modelo NLI sin cargarlos todavía. La carga se realiza de forma
diferida cuando se ejecuta la verificación semántica y existen
evidencias.

**Etapa 1: validación de entradas**

`verify(response, rag_results, web_results, claims)` exige que
`response` sea una cadena. Valida que RAG y web sean listas de
diccionarios o `None`.

Para RAG exige que cada resultado contenga:

- `source`: ruta o referencia textual no vacía.
- `text`: contenido textual.

Para web exige:

- `url`: URL HTTP(S) válida.
- `title`: cadena.
- `description`: cadena.
- `source`: cadena.

Los errores de contrato se comunican mediante `EvidenceVerifierError`.

**Etapa 2: controles de referencias**

El método `verify()` realiza controles deterministas separados del
análisis semántico:

- Extrae URLs HTTP(S) escritas explícitamente en la respuesta.
- Normaliza esquema y host, elimina puertos estándar y conserva ruta,
  query y fragmento.
- Compara las URLs de la respuesta con las URLs recibidas desde DDGS.
- Detecta URLs duplicadas en los resultados web recibidos.
- Comprueba coincidencias literales entre las rutas `source` de RAG y el
  texto de la respuesta.

Los estados de esos controles son:

- `PASS` o `UNVERIFIED` para URLs.
- `PASS` o `NOT_CITED` para referencias RAG.
- `PASS` o `WARNING` para URLs duplicadas.

Una coincidencia literal de una ruta RAG no demuestra que el fragmento
respalde el contenido de la afirmación. Del mismo modo, una URL
coincidente confirma que apareció en los resultados DDGS, no que el
contenido de la página haya sido leído o validado.

**Etapa 3: construcción del conjunto de evidencias semánticas**

En `verify_claims(...)`:

- Cada resultado RAG se transforma en una evidencia con
  `evidence_type="RAG"`, su `source` y el texto recuperado.
- Cada resultado web se transforma en una evidencia `DDGS_SNIPPET`,
  usando como texto la concatenación de `title` y `description`, y como
  fuente la URL.
- No se descarga el artículo completo.
- El código toma los primeros elementos de la lista combinada mediante
  `selected = evidence[:max_evidence_per_claim]`.

**Observación importante sobre el límite de evidencias:** aunque el
argumento se llama `max_evidence_per_claim`, la selección se realiza una
sola vez sobre la lista combinada, antes del bucle de afirmaciones. Por
lo tanto, en esta implementación el mismo conjunto inicial de evidencias
se reutiliza para cada claim; no se observa una recuperación o selección
individual por afirmación. Esto debe evaluarse como una limitación
funcional potencial, especialmente cuando hay muchos claims o las
evidencias relevantes aparecen después de las primeras posiciones.

Si no hay evidencias seleccionadas, el método devuelve `INSUFFICIENT`
para cada claim, con `comparisons=[]`, sin cargar el modelo NLI ni
ejecutar la adjudicación Qwen.

**Etapa 4: carga y ejecución NLI con mDeBERTa**

Cuando existen evidencias:

1.  `_load_nli_model()` importa PyTorch y Transformers.
2.  Selecciona dispositivo CUDA o CPU, salvo que se haya indicado uno.
3.  Carga tokenizer y `AutoModelForSequenceClassification` desde
    `nli_model_name`.
4.  Pone el modelo en el dispositivo y activa `eval()`.
5.  Lee `id2label` y exige identificar exactamente una etiqueta para
    `entailment`, `neutral` y `contradiction`.
6.  Construye pares con el texto de evidencia como premisa y el claim
    como hipótesis.
7.  Tokeniza con padding, truncamiento y `max_length=512`.
8.  Ejecuta inferencia en lotes de 8, bajo `torch.inference_mode()`.
9.  Aplica softmax y conserva los tres puntajes.

Para cada comparación se guarda `evidence_id`, `evidence_type`,
`source`, texto de evidencia, puntajes NLI y un indicador
`role_mismatch`.

**Importante:** los puntajes NLI no se usan para determinar directamente
el estado final. Los umbrales `0.80` y el margen `0.15` se incluyen en
el informe como parámetros de diagnóstico/compatibilidad; el propio
resultado los identifica como valores que no gobiernan la decisión
final.

**Etapa 5: salvaguarda de roles técnicos**

El código incluye `_roles_in_text()` y `_role_mismatch()` para reconocer
algunos roles técnicos explícitos, por ejemplo `actor`, `critic`,
`replay_buffer`, `environment`, `robot`, `policy` y `value_function`.

La función marca incompatibilidad cuando ambos textos identifican roles
y no comparten ninguno. El indicador se incorpora a cada comparación. En
la implementación observada no actúa como una regla determinista
independiente que cambie el veredicto: se registra como dato auxiliar,
mientras que la adjudicación semántica recibe los textos de evidencia y
el claim.

**Etapa 6: adjudicación semántica con Qwen3**

Para cada claim, `_ollama_adjudicate(claim, evidence_items)` envía a
Ollama una solicitud `/api/chat` con:

- modelo `adjudication_model`;
- mensaje que contiene el claim y las evidencias numeradas;
- `stream=False`;
- `format="json"`;
- `temperature=0`;
- `num_predict=700`;
- timeout `adjudication_timeout`.

El prompt impone reglas conservadoras:

- `SUPPORTED`: la evidencia expresa directamente o implica claramente la
  totalidad del claim.
- `CONTRADICTED`: la evidencia afirma un hecho incompatible sobre el
  mismo sujeto, propiedad y condiciones.
- `INSUFFICIENT`: evidencia relacionada pero parcial, sobre otro
  aspecto/componente o insuficiente para decidir.
- La ausencia de mención no debe considerarse contradicción.
- Se permiten equivalencias terminológicas entre español e inglés solo
  cuando el significado sea realmente equivalente.
- Se exige JSON con una clasificación por cada identificador de
  evidencia.

La función valida que la salida contenga una lista `items`, que los
identificadores sean válidos y que las etiquetas pertenezcan al conjunto
permitido. También exige que se haya clasificado cada evidencia
exactamente una vez. Si la salida no cumple, lanza una excepción.

**Etapa 7: decisión por claim**

Si la adjudicación se completa correctamente, el código agrega las
etiquetas recibidas para las evidencias del claim:

| Condición                                                    | Estado del claim       |
|--------------------------------------------------------------|------------------------|
| Hay al menos una evidencia `SUPPORTED` y otra `CONTRADICTED` | `CONFLICTING_EVIDENCE` |
| Existe al menos una `SUPPORTED` y ninguna `CONTRADICTED`     | `SUPPORTED`            |
| No hay `SUPPORTED`, pero existe `CONTRADICTED`               | `CONTRADICTED`         |
| No existe respaldo ni contradicción directa                  | `INSUFFICIENT`         |
| La adjudicación no está disponible o falla                   | `INSUFFICIENT`         |

Los puntajes NLI máximos de entailment y contradiction se incluyen en el
reporte como diagnóstico. Si Qwen no produce una clasificación válida,
el método registra el error y adopta `INSUFFICIENT` para ese claim: es
un comportamiento *fail-closed* y evita que el NLI acepte
automáticamente la afirmación.

**Etapa 8: agregación global de claims**

El campo `overall_status` de la verificación semántica se calcula con
estas reglas:

| Condición entre los estados de todos los claims                    | Estado global          |
|--------------------------------------------------------------------|------------------------|
| Al menos un claim `CONFLICTING_EVIDENCE`                           | `CONFLICTING_EVIDENCE` |
| Todos los claims `SUPPORTED`                                       | `SUPPORTED`            |
| Hay `SUPPORTED`, pero no `CONTRADICTED` y no todos son `SUPPORTED` | `PARTIALLY_SUPPORTED`  |
| Hay `SUPPORTED` y también `CONTRADICTED`                           | `MIXED_EVIDENCE`       |
| No hay `SUPPORTED`, pero existe `CONTRADICTED`                     | `CONTRADICTED`         |
| Ninguna condición anterior                                         | `INSUFFICIENT`         |

El resultado contiene modelo NLI, modelo de adjudicación, proveedor,
indicador de adjudicación habilitada, errores de adjudicación,
dispositivo, parámetros diagnósticos, resultados por claim,
`overall_status` y limitaciones.

**Etapa 9: informe integral de `verify()`**

Cuando `claims` es una lista, `verify()` incorpora el informe semántico
bajo:

``` text
checks
  └── semantic_support_check
```

Cuando `claims=None`, el control semántico se marca como
`NOT_PERFORMED`; el módulo no extrae claims automáticamente. La
extracción pertenece a `ClaimExtractor` y es coordinada por
`ClaimVerificationPipeline`.

El informe superior también incluye:

- `web_url_reference_check`;
- `rag_source_reference_check`;
- `duplicate_web_reference_check`;
- `semantic_support_check`;
- conteos de fragmentos RAG, fuentes RAG únicas, resultados web y URLs
  únicas;
- `overall_status` de controles de referencias;
- limitaciones.

**Distinción crítica entre dos estados globales**

`EvidenceVerifier` produce dos niveles que no deben confundirse:

1.  `report["overall_status"]`: resume controles de referencias URL/RAG
    y duplicados.
2.  `report["checks"]["semantic_support_check"]["overall_status"]`:
    resume la verificación semántica de los claims.

`ClaimVerificationPipeline` toma el segundo para establecer su
`semantic_status` y su `status` principal. El primero queda registrado
como `reference_status`. Un estado `REFERENCE_CHECKS_PASSED` no
significa que las afirmaciones estén respaldadas; y un estado semántico
`SUPPORTED` no significa que todas las referencias URL hayan pasado los
controles.

**Diagrama de ejecución**

``` text
Claim(s) + respuesta + resultados RAG/web
                    |
                    v
              EvidenceVerifier.verify()
                    |
          +---------+----------+
          |                    |
          v                    v
  Controles de referencias   ¿claims suministrados?
  URL / RAG / duplicados       | No
          |                    +----> semantic NOT_PERFORMED
          |                    |
          |                   Sí
          |                    |
          |                    v
          |             verify_claims(claims)
          |                    |
          |                    v
          |            Construir evidencias
          |            RAG + snippets DDGS
          |                    |
          |                    v
          |             Seleccionar primeros N
          |                    |
          |                    v
          |             ¿hay evidencias?
          |                | No
          |                +----> INSUFFICIENT
          |                |
          |               Sí
          |                |
          |                v
          |       mDeBERTa NLI (diagnóstico)
          |                |
          |                v
          |       Qwen3 / Ollama por claim
          |                |
          |                v
          |       Etiqueta por evidencia
          |                |
          |                v
          |       Agregación por claim
          |                |
          |                v
          |       Agregación global semántica
          |                |
          +----------------+
                    |
                    v
             Informe estructurado
                    |
                    v
       ClaimVerificationPipeline.run()
```

**Limitaciones y riesgos técnicos**

| Observación                                                                                 | Consecuencia posible                                                                                                              | Estado                                                                                     |
|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| Los primeros N elementos se seleccionan una sola vez para todos los claims.                 | Una evidencia relevante ubicada más adelante puede no ser considerada; un claim recibe evidencia que solo trata otro claim.       | Hallazgo estático confirmado; impacto pendiente de medir.                                  |
| DDGS aporta `title` y `description`, no el contenido completo.                              | El veredicto puede basarse en un fragmento incompleto o descontextualizado.                                                       | Limitación declarada en el código.                                                         |
| Los umbrales NLI no gobiernan el resultado final.                                           | Modificar esos umbrales no cambiaría por sí solo las etiquetas semánticas de esta versión.                                        | Confirmado por el flujo de decisión inspeccionado.                                         |
| La decisión final depende de Qwen3.                                                         | Puede haber variabilidad o errores de adjudicación del LLM aunque NLI entregue puntajes diagnósticos altos.                       | Riesgo a medir.                                                                            |
| Si Qwen falla, el estado pasa a `INSUFFICIENT`.                                             | Se evita una aceptación automática, pero puede aumentar la abstención/falta de decisión.                                          | Comportamiento fail-closed confirmado.                                                     |
| El modelo NLI requiere PyTorch, Transformers y pesos disponibles localmente o descargables. | La primera carga puede necesitar acceso a caché o red y memoria de GPU/CPU.                                                       | Dependencia de implementación.                                                             |
| El docstring inicial contradice la implementación actual.                                   | Puede inducir a documentar incorrectamente la capacidad semántica del módulo.                                                     | Inconsistencia documental confirmada.                                                      |
| `use_ollama_adjudication=False` deja `judge_ok=False` en el flujo observado.                | Las comparaciones NLI se calculan, pero el resultado de cada claim termina en `INSUFFICIENT`; NLI no pasa a ser juez alternativo. | Consecuencia del código; requiere prueba unitaria para confirmar comportamiento ejecutado. |
| `_role_mismatch` se registra, pero no funciona como filtro determinista del veredicto.      | No debe interpretarse como una garantía de que los roles distintos no influyan en la adjudicación.                                | Hallazgo estático confirmado.                                                              |

**Métricas específicas para `EvidenceVerifier`**

La evaluación deberá separar tres dimensiones:

1.  **Controles de referencias**
    - precisión de detección de URLs presentes y ausentes;
    - detección de duplicados;
    - detección de menciones literales de fuentes RAG;
    - falsos `PASS`, falsos `UNVERIFIED` y falsos `NOT_CITED`.
2.  **NLI diagnóstico**
    - distribución de entailment, neutral y contradiction;
    - accuracy y macro-F1 de la etiqueta NLI de mayor puntaje frente a
      referencias;
    - calibración, solo si se define un protocolo adecuado;
    - análisis de errores por idioma, longitud y tipo de relación.
3.  **Adjudicación semántica y agregación**
    - accuracy, precision, recall y F1 por `SUPPORTED`, `CONTRADICTED` e
      `INSUFFICIENT`;
    - macro-F1;
    - tasa de falsos `SUPPORTED` (métrica crítica);
    - tasa de abstención `INSUFFICIENT`;
    - tasa de errores o salidas JSON inválidas de Qwen;
    - exactitud de agregación por claim y global;
    - latencia separada de NLI y de adjudicación;
    - sensibilidad al orden y cantidad de evidencias.

Las referencias deberán ser anotadas independientemente y cada claim
deberá tener evidencia de apoyo, contradicción o insuficiencia
claramente identificada. Se mantendrán separados el resultado NLI, el
resultado Qwen y el veredicto agregado.

**Atribución de errores**

- Evidencia correcta no recuperada por RAG: **recuperación RAG**.
- Evidencia recuperada pero no entregada a `EvidenceVerifier`:
  **integración de contexto/interfaz**.
- Claim omitido o mal atomizado antes de llegar al verificador:
  **ClaimExtractor**.
- Claim correcto y evidencia pertinente entregados, pero etiqueta
  semántica incorrecta: **adjudicación Qwen dentro de
  EvidenceVerifier**.
- Puntajes NLI incorrectos, aun cuando Qwen decida correctamente:
  **señal diagnóstica NLI**.
- Etiquetas individuales correctas pero `overall_status` incorrecto:
  **agregación de EvidenceVerifier**.
- Estado semántico correcto pero interpretado mal por el pipeline o
  presentado mal por la interfaz: **integración del pipeline/interfaz**.

**Conclusión del relevamiento**

`EvidenceVerifier` v0.3.0 no es solamente un comparador de URLs ni un
clasificador NLI. En el código actual combina controles deterministas de
referencias, una etapa NLI con mDeBERTa cuyos puntajes son diagnósticos
y una adjudicación semántica local con Qwen3 que determina las etiquetas
finales por evidencia.

El resultado final depende, por tanto, de dos modelos con funciones
diferentes: mDeBERTa aporta señales NLI y Qwen3 adjudica el respaldo
semántico usando los fragmentos recibidos. No corresponde decir que
mDeBERTa decide el veredicto final.

Se detectaron dos puntos que merecen pruebas prioritarias: la selección
de los primeros N elementos se aplica una sola vez a todos los claims, y
la opción `use_ollama_adjudication=False` no activa una decisión final
alternativa basada en NLI. Además, el docstring inicial no refleja el
comportamiento semántico implementado en el cuerpo del archivo.

**Estado:** inspección estática de `EvidenceVerifier.py` v0.3.0
completada sobre la rama pública consultada. Falta cotejar el archivo
local, ejecutar pruebas controladas y medir el rendimiento real. No se
ha modificado el componente de producción.

**Referencias de código:** `EvidenceVerifier.py`, líneas 34–81 (clase y
constructor); 82–113 (carga NLI); 114–149 (roles); 150–224 (adjudicación
Qwen); 225–406 (verificación semántica); 408–447 (normalización y
validación); 449–614 (verificación de referencias e informe); 616–628
(estado global).

## 4. Modelo de arquitectura a verificar

El esquema representa el flujo de consulta actualizado. La respuesta de
Qwen3 se obtiene primero; posteriormente se ejecuta el pipeline de
verificación y se presenta su informe. La auditoría deberá determinar si
la interfaz presenta ambos resultados por separado y confirmar todas las
rutas de excepción.

``` text
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

La representación no implica que el pipeline corrija la respuesta. La
respuesta generada se produce antes de la verificación. La relación
entre el informe y la respuesta final deberá verificarse en el código y
en una ejecución instrumentada.

## 5. Relevamiento paso a paso del sistema

El relevamiento se realizará en este orden. Cada paso deberá producir
evidencia concreta: archivo, función, llamada, dato de entrada y dato de
salida.

### Paso 0 — Congelar la referencia de auditoría

Registrar: - ruta del repositorio; - fecha y hora; - versión de Python y
entorno virtual; - hash SHA-256 de los archivos examinados; - estado de
Git, si el repositorio está disponible; - versión de Ollama y
etiqueta/digest del modelo; - copia de solo lectura de la configuración
efectiva (con secretos excluidos).

**Criterio de cierre:** poder identificar exactamente qué versión de
GIAR-ORION se evaluó.

### Paso 1 — Inventario del repositorio

Identificar los directorios y archivos propios del proyecto, excluyendo
del inventario funcional: - `.venv/`; - cachés; - `__pycache__/`; -
pesos de modelos; - embeddings y archivos generados que no sean código o
datos de prueba.

Clasificar cada archivo como: - punto de entrada; - módulo de
producción; - configuración; - datos/Knowledge; - memoria y logs; -
pruebas; - experimentos/variantes históricas; - documentación; -
artefactos generados.

**Criterio de cierre:** inventario que permita distinguir claramente
producción, experimentos y archivos obsoletos.

### Paso 2 — Interfaz principal: `main_multilinea.py`

Inspeccionar: - carga y validación de configuración; - inicialización de
memoria; - inicialización de RAG; - inicialización de búsqueda web; -
construcción de mensajes para Ollama; - llamada HTTP y parámetros
enviados; - ensamblado de contexto; - llamada a la verificación; -
tratamiento de errores y respuesta final.

Para cada función registrar firma, responsabilidad, dependencias,
entradas, salidas y efectos secundarios.

**Criterio de cierre:** diagrama de llamadas desde la entrada del
usuario hasta la generación, invocación del pipeline y presentación del
informe. El recorrido funcional se documenta en 3.5.2; queda pendiente
una traza instrumentada que registre argumentos y salidas reales.

### Paso 3 — RAG: `MultilingualKnowledgeRetriever.py`

Inspeccionar sin alterar: - modelos de embeddings realmente cargados; -
modo `e5`, `bge-m3` o `hybrid`; - tokenización y normalización; - carga
y fragmentación de documentos; - generación o carga de embeddings; -
estrategia de similitud y combinación de puntuaciones; - ordenamiento y
desempate; - filtros; - estructura exacta de cada resultado; -
tratamiento de documentos vacíos, duplicados y errores.

Registrar la relación entre `source`, `score` y `text` que la interfaz
conserva al construir el contexto.

**Distinción diagnóstica:** un fallo al encontrar o posicionar evidencia
es un fallo de **recuperación RAG**, no de generación LLM.

### Paso 4 — Búsqueda web: `WebSearch.py`

Determinar: - si está conectada a `main_multilinea.py`; - condiciones de
activación; - consulta enviada; - proveedor y parámetros efectivos; -
formato de los resultados; - cómo se fusionan con RAG; - cómo se
identifican las fuentes; - qué ocurre cuando no hay conexión o
resultados.

La búsqueda web se medirá separadamente de RAG. No se atribuirá al
recuperador documental una evidencia que provenga de DDGS.

### Paso 5 — Generación: Ollama y Qwen3

Inspeccionar: - construcción exacta de `messages`; - system prompt; -
historial incluido; - contexto RAG/web incorporado; - modelo y opciones
efectivas; - `think`, `num_predict` y timeout; - formato de respuesta; -
metadatos de Ollama (`prompt_eval_count`, `eval_count`, duraciones y
motivo de finalización, si la API los devuelve); - manejo de errores y
truncamiento.

**Distinción diagnóstica:** si la evidencia correcta fue entregada al
modelo pero la respuesta la interpreta mal, la omite o inventa datos, el
problema corresponde a **generación LLM**. Si la evidencia nunca llegó
al contexto, el origen es recuperación o integración de contexto.

### Paso 6 — `ClaimExtractor.py`

La copia consultada identifica `ClaimExtractor.VERSION = "0.1.2"`. El
módulo: - segmenta la respuesta en unidades textuales; - solicita a
Ollama la extracción de afirmaciones factuales atómicas; - exige
clasificación para cada unidad; - detecta omisiones, duplicados e
inconsistencias estructurales; - devuelve información serializable como
JSON.

La documentación del propio módulo advierte que la cobertura estructural
no garantiza exhaustividad semántica y que el extractor no verifica la
verdad de las afirmaciones.

Hay que inspeccionar el archivo completo y registrar: - prompt de
extracción; - modelo y parámetros que recibe; - reglas de atomización; -
esquema JSON; - validaciones; - errores y reintentos; - correspondencia
entre unidades originales y claims extraídos.

**Distinción diagnóstica:** una afirmación factual omitida o fragmentada
incorrectamente es un fallo de **ClaimExtractor**, no de
EvidenceVerifier.

### Paso 7 — `EvidenceVerifier.py`

Inspeccionar el código vigente para determinar: - modelos NLI cargados y
sus versiones; - etiquetas y mapeo de clases; - umbrales efectivos; -
normalización de evidencias; - selección y agregación de evidencias; -
reglas de `SUPPORTED`, `CONTRADICTED` e `INSUFFICIENT`; - adjudicación
adicional mediante Qwen3, si existe; - reglas de decisión final; -
tratamiento de contradicciones entre fuentes; - salida estructurada y
trazabilidad.

No se inferirán umbrales ni comportamiento a partir de versiones
anteriores o de nombres de archivos. Se leerán del código y la
configuración que efectivamente se ejecutan.

**Distinción diagnóstica:** si el claim está bien extraído y la
evidencia pertinente fue suministrada, pero el veredicto es incorrecto,
el problema corresponde a **EvidenceVerifier**.

### Paso 8 — `ClaimVerificationPipeline.py`

Determinar el flujo real: - orden de llamadas; - argumentos entregados
al extractor; - evidencias enviadas al verificador; - relación entre
claims y fuentes; - agregación de veredictos; - política ante claims
omitidos o errores; - criterio para producir el estado global; - si la
salida original de Qwen3 se conserva sin alteraciones; - qué información
se presenta al usuario.

**Criterio de cierre:** contrato de entrada/salida y diagrama de
secuencia del pipeline.

### Paso 9 — Integración completa

Seguir al menos un caso instrumentado de extremo a extremo, sin cambiar
las decisiones del sistema. El loop funcional ya está documentado en
3.5.2; esta etapa debe producir una traza observada, no solo una
descripción. Registrar el mismo `audit_case_id` en cada etapa:

1.  Consulta original.
2.  Resultados RAG.
3.  Resultados web, si se ejecutan.
4.  Contexto efectivamente enviado.
5.  Respuesta bruta de Qwen3.
6.  Claims extraídos.
7.  Evidencias asociadas a cada claim.
8.  Salida NLI y adjudicación, si aplica.
9.  Veredictos y resultado final.
10. Respuesta efectivamente entregada al usuario.
11. Informe de verificación efectivamente presentado y relación (si
    existe) con la respuesta mostrada.

**Criterio de cierre:** trazabilidad completa que permita localizar el
primer punto en que se aparta del resultado esperado.

## 6. Diseño experimental

### 6.1 Dataset

Archivo propuesto: `AUDIT/Dataset/GIAR_ORION_AUDIT_DATASET.json`.

Cada caso deberá contener, como mínimo:

``` json
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

Los campos podrán ser nulos cuando no correspondan a una etapa. El
esquema final deberá validarse antes de iniciar las pruebas.

### 6.2 Independencia de las referencias

- Las respuestas esperadas no se generarán con el mismo Qwen3 que se
  evalúa.
- Las evidencias esperadas se identificarán directamente en los
  documentos fuente.
- Los claims y veredictos de referencia se revisarán manualmente.
- Cada caso tendrá una justificación verificable.
- Las versiones del dataset serán inmutables una vez utilizadas en una
  ejecución publicada.

### 6.3 Tamaño

La distribución inicial de 100 casos queda como objetivo tentativo, no
como requisito cerrado. Antes de fijar cantidades se revisarán los casos
existentes y su reutilización posible. Un mismo caso puede alimentar
varias métricas, pero cada etapa debe tener su propio denominador y
criterio de puntuación. No se sumarán los resultados de etapas
diferentes como si fueran observaciones independientes.

## 7. Métricas

### 7.1 RAG

Para cada consulta y para el conjunto: - Precision@K; - Recall@K; -
F1@K; - Hit Rate@K; - MRR; - NDCG@K.

La relevancia se anotará por fragmento/documento y se definirá de
antemano el criterio de correspondencia. Se informará también cobertura
por tipo de consulta, idioma y dificultad.

### 7.2 ClaimExtractor

Con correspondencia entre claims esperados y extraídos: - Precision,
Recall y F1; - omisiones; - claims espurios; - duplicados; - errores de
atomización/fragmentación; - cobertura de unidades textuales.

La comparación semántica no debe depender exclusivamente de igualdad
literal. El protocolo de emparejamiento debe quedar fijado y auditable.

### 7.3 EvidenceVerifier

- Accuracy;
- Precision, Recall y F1 por clase;
- macro-F1;
- matriz de confusión;
- tasa de falsos `SUPPORTED`;
- tasa de falsas contradicciones;
- tasa de `INSUFFICIENT`;
- cobertura de casos con evidencia contradictoria.

Se conservarán por separado la salida NLI, la adjudicación LLM y el
veredicto final cuando el código exponga esas etapas.

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

La evaluación de generación se hará con contexto controlado y referencia
externa. Se informará por separado el rendimiento con evidencia correcta
y el rendimiento cuando la evidencia recuperada por RAG sea la que
realmente recibe.

### 7.5 Pipeline integral

- proporción de consultas con respuesta correcta;
- cobertura de requisitos;
- claims incorrectos que llegan a la salida final;
- claims no respaldados detectados por el pipeline pero que permanecen
  en la respuesta presentada;
- evidencia de cualquier corrección o regeneración posterior, si la
  implementación la contempla;
- claims correctos descartados;
- errores no detectados;
- errores detectados correctamente;
- tasa de abstención adecuada;
- trazabilidad completa;
- latencia total y por etapa.

## 8. Atribución de errores y propagación

Cada error deberá identificar:

1.  **Primer punto de divergencia:** primera etapa donde el resultado
    difiere de la referencia.
2.  **Componente de origen:** RAG, WebSearch, integración de contexto,
    Qwen3, ClaimExtractor, EvidenceVerifier o integración del pipeline.
3.  **Efecto posterior:** etapas afectadas por el error inicial.
4.  **Detección:** si una etapa posterior lo detectó o lo dejó pasar.
5.  **Impacto final:** efecto sobre la respuesta entregada.

Ejemplos: - Evidencia ausente en top-K: recuperación RAG. - Evidencia
recuperada pero excluida al construir el prompt: integración de
contexto. - Evidencia presente en el prompt y afirmación falsa:
generación Qwen3. - Afirmación falsa presente en la respuesta, pero
omitida por el extractor: ClaimExtractor. - Claim correcto y evidencia
suficiente, pero veredicto incorrecto: EvidenceVerifier. - Componentes
individuales correctos pero salida final mal agregada: integración del
pipeline.

No se asignará automáticamente todo error final al último módulo que
intervino.

## 9. Ejecución y estados

Cada etapa y caso podrá tener uno de estos estados:

- `PASS`: ejecutado y cumple el criterio definido.
- `FAIL`: ejecutado y no cumple.
- `ERROR`: no pudo completarse por una excepción o fallo técnico.
- `SKIPPED`: no correspondía ejecutarlo.
- `NOT_RUN`: no llegó a ejecutarse.
- `INCONCLUSIVE`: se ejecutó, pero la evidencia no permite una
  conclusión válida.

Un módulo no ejecutado nunca contará como `FAIL` ni como `PASS`.

La ejecución conservará los resultados parciales aunque una etapa
posterior falle.

## 10. Estructura de archivos propuesta

``` text
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

La estructura es una propuesta. Los nombres y responsabilidades se
confirmarán al diseñar la implementación. Cada ejecución utilizará un
directorio nuevo.

## 11. Reproducibilidad y preservación

Por ejecución se guardará: - identificador único; - fecha/hora y zona
horaria; - hash del dataset; - hash de los archivos de código
relevantes; - configuración efectiva saneada; - versión de Python,
librerías, Ollama y modelos; - identificadores de documentos/fragmentos
recuperados; - entradas y salidas de cada etapa; - métricas y
excepciones; - duración de cada etapa.

No se sobrescribirán resultados anteriores. Los datos sensibles,
credenciales y secretos no se copiarán a los informes.

## 12. Criterios de aceptación de la auditoría

La herramienta de auditoría se considerará técnicamente válida cuando:

1.  Ejecute las cinco evaluaciones desde un controlador central.
2.  Use los componentes reales del punto de entrada vigente.
3.  No modifique el código ni la configuración de producción.
4.  Distinga claramente errores de RAG y de generación LLM.
5.  Mantenga trazabilidad por caso a través de todas las etapas.
6.  Calcule métricas a partir de referencias independientes.
7.  Guarde resultados parciales y errores.
8.  Diferencie `FAIL`, `ERROR`, `SKIPPED` y `NOT_RUN`.
9.  Permita comparar ejecuciones con el mismo dataset y configuración
    identificada.
10. Genere un informe que permita localizar el primer origen de cada
    fallo.

No se fijan umbrales globales de aprobación del agente hasta disponer de
una línea de base experimental. No se inventará una calificación general
combinando métricas incompatibles.

## 13. Plan de trabajo y avance

| Orden | Actividad                                      | Estado                                                                                                                                                |
|:------|:-----------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0     | Congelar referencia local y registrar hashes   | Pendiente                                                                                                                                             |
| 1     | Inventariar estructura y clasificar archivos   | Parcial: existe inventario del 01-11                                                                                                                  |
| 2     | Revisar `main_multilinea.py` y llamadas reales | Parcial: recorrido funcional hasta `ClaimVerificationPipeline.run()` y presentación del informe documentado; falta traza instrumentada y cotejo local |
| 3     | Revisar `MultilingualKnowledgeRetriever.py`    | Pendiente                                                                                                                                             |
| 4     | Revisar `WebSearch.py` y su integración        | Pendiente                                                                                                                                             |
| 5     | Revisar llamada a Ollama/Qwen3                 | Parcial                                                                                                                                               |
| 6     | Revisar `ClaimExtractor.py`                    | Parcial: versión 0.1.2 identificada                                                                                                                   |
| 7     | Revisar `EvidenceVerifier.py`                  | Pendiente                                                                                                                                             |
| 8     | Revisar `ClaimVerificationPipeline.py`         | Parcial: método `run()` relevado estáticamente en 3.5.3; falta cotejo local y prueba controlada                                                       |
| 9     | Trazar un caso integral de extremo a extremo   | Pendiente: el loop está documentado; falta registrar una ejecución con entradas y salidas reales por etapa                                            |
| 10    | Cerrar dataset, métricas y protocolo           | Pendiente                                                                                                                                             |
| 11    | Implementar controlador y módulos de auditoría | Pendiente                                                                                                                                             |
| 12    | Ejecutar línea de base y generar informes      | Pendiente                                                                                                                                             |

## 14. Próximo paso concreto

El siguiente paso es cotejar `ClaimVerificationPipeline.py` con la copia
local y continuar con el relevamiento de `ClaimExtractor.py` y
`EvidenceVerifier.py`. Después se realizará una traza instrumentada del
**Paso 9** para medir una ejecución real. Para cerrar el cotejo de
versiones se necesitan estos archivos:

- `main_multilinea.py`
- `config.json`
- `Agent/MultilingualKnowledgeRetriever.py`
- `Agent/WebSearch.py`
- `Agent/ClaimExtractor.py`
- `Agent/EvidenceVerifier.py`
- `Agent/ClaimVerificationPipeline.py`

No hace falta enviar `.venv`, cachés, embeddings ni pesos de modelos
para esta primera revisión.

**Regla de avance:** no se implementará el controlador de auditoría
hasta haber documentado los contratos reales de los componentes y
comprobado el recorrido efectivo de una consulta. Así evitamos construir
una auditoría que mida una arquitectura supuesta en lugar de GIAR-ORION.

------------------------------------------------------------------------

# ANEXO A — Verificación del repositorio público

## Actualización 0.2 — 2026-11-08

### A.1 Fuente inspeccionada

Se inspeccionó el repositorio público:

- Repositorio: https://github.com/PabloFolino/GIAR-ORION
- Rama observada: `main`
- Punto de entrada inspeccionado: `main_multilinea.py`
- Archivo consultado desde GitHub: 1083 líneas (854 líneas de código),
  33.9 KB según la vista del repositorio.

Esta inspección corresponde a la rama pública `main` en el momento de la
consulta. No equivale a ejecutar el código ni a verificar que el
contenido local del equipo sea idéntico.

### A.2 Hallazgo importante: la arquitectura real es más concreta que el esquema inicial

En `main_multilinea.py` se observa que:

1.  Se importa directamente `ClaimVerificationPipeline` desde
    `Agent.ClaimVerificationPipeline`.
2.  Durante `iniciar_agente(...)` se inicializan el recuperador RAG, el
    buscador web y una instancia de `ClaimVerificationPipeline`.
3.  El pipeline recibe `ollama_base_url` y `ollama_model` desde la
    configuración LLM.
4.  El modo de fuente comienza como `local`.
5.  El usuario puede cambiarlo mediante `/fuente local`, `/fuente web` o
    `/fuente autorizada`.
6.  La recuperación RAG se ejecuta para la consulta y devuelve tres
    elementos: contexto formateado, fuentes y resultados originales.
7.  La búsqueda web se ejecuta según la modalidad elegida. En modo
    `local` no aporta contexto web; en modo `web` usa búsqueda libre y
    en modo `autorizada` restringe la búsqueda a dominios configurados.
8.  Los contextos RAG y web se agregan a un mensaje de sistema temporal
    para la solicitud al LLM.
9.  El historial de conversación conserva la pregunta y la respuesta,
    mientras que los contextos recuperados se agregan solo a la
    solicitud actual.
10. La interfaz incluye una función dedicada a presentar el informe del
    pipeline, con estado general, versiones, extracción, verificación
    semántica, referencias y limitaciones.

Referencias de código inspeccionadas: - `main_multilinea.py`:
importación del pipeline y validación de configuración. -
`main_multilinea.py`: `crear_recuperador(...)`,
`construir_contexto_rag(...)`. - `main_multilinea.py`:
`crear_buscador_web(...)`, `construir_contexto_web(...)`. -
`main_multilinea.py`: `mostrar_informe_verificacion(...)`. -
`main_multilinea.py`: `iniciar_agente(...)` e inicialización de
componentes.

### A.3 Diagrama de flujo actualizado (parcialmente confirmado)

``` text
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

**Importante:** la importación, la construcción de la instancia y la
función de presentación del informe están comprobadas en el archivo. En
esta revisión parcial todavía no se ha confirmado el punto exacto donde
se invoca el método de verificación ni todos los argumentos que se le
entregan. Tampoco se ha inspeccionado el código interno completo del
pipeline. Por lo tanto, el enlace entre la respuesta generada y la
ejecución efectiva de la verificación queda pendiente de confirmar.

### A.4 Corrección al documento inicial

El diagrama de la sección 4 de la versión 0.1 era una hipótesis de
trabajo. Debe leerse como provisional y no como descripción verificada
del flujo. Este anexo reemplaza esa hipótesis en los puntos que ya
fueron confirmados.

También se precisa que la búsqueda web no se ejecuta necesariamente en
todas las consultas: la interfaz permite seleccionar la modalidad de
fuentes y su valor inicial es `local`. RAG local y búsqueda web son
fuentes diferenciadas.

### A.5 Próximas inspecciones prioritarias

Para completar el Paso 2 y avanzar al Paso 3, el orden será:

1.  Terminar de seguir en `main_multilinea.py` el tramo posterior a la
    construcción de `mensajes_para_consulta`: llamada a Ollama,
    incorporación de la respuesta al historial, invocación del pipeline
    y presentación de su informe.
2.  Inspeccionar `Agent/ClaimVerificationPipeline.py`: constructor,
    método público, secuencia de ejecución, argumentos, salidas y manejo
    de errores.
3.  Inspeccionar `Agent/ClaimExtractor.py` y `Agent/EvidenceVerifier.py`
    desde la rama pública actual, no desde copias históricas.
4.  Inspeccionar `Agent/MultilingualKnowledgeRetriever.py` y
    `Agent/WebSearch.py`.
5.  Contrastar el `config.json` público actual con los valores de
    configuración observados anteriormente.

### A.8 Actualización 0.6 — Inspección estática de `ClaimVerificationPipeline.run()`

Se examinó el archivo `Agent/ClaimVerificationPipeline.py` de la rama
pública `main`. La clase declara la versión `0.1.0` y el método `run()`
recibe la respuesta generada junto con resultados RAG y web opcionales.
El método coordina `ClaimExtractor.extract()` y
`EvidenceVerifier.verify()`, construye un informe estructurado y
reconoce estados semánticos específicos.

El relevamiento detallado, incluyendo las ramas de error, la condición
`complete`, el caso sin afirmaciones factuales y la interpretación de
`semantic_support_check`, se incorpora en la sección 3.5.3.

Esta inspección es estática y corresponde al archivo público consultado.
No sustituye el cotejo con el archivo local ni las pruebas
experimentales. La eficacia de extracción y verificación permanece sin
medir.

### A.7 Actualización 0.5 — Confirmación del recorrido de verificación

En la revisión que da origen a la versión 0.5 se incorpora la
confirmación de que la verificación no queda limitada a la importación e
inicialización del pipeline. El flujo examinado llega a la invocación
efectiva de `ClaimVerificationPipeline.run()` después de recibir la
respuesta de Ollama/Qwen3 y utiliza el informe devuelto para su
presentación desde la interfaz.

El recorrido de una consulta nueva queda documentado en detalle en la
sección 3.5.2. En síntesis:

1.  La interfaz recibe la consulta y distingue comandos de consultas
    ordinarias.
2.  Agrega la pregunta al historial.
3.  Ejecuta RAG cuando está habilitado.
4.  Ejecuta búsqueda web únicamente según la modalidad seleccionada.
5.  Construye el contexto temporal y prepara los mensajes.
6.  Solicita la generación a Ollama/Qwen3.
7.  Recibe la respuesta y la incorpora al flujo conversacional.
8.  Invoca el pipeline con la respuesta y las evidencias disponibles.
9.  El pipeline coordina extracción y verificación.
10. La interfaz presenta el informe de verificación junto con el
    resultado de la consulta.

**Alcance:** esta actualización confirma la conexión funcional entre
generación, ejecución del pipeline y presentación del informe. No
certifica la corrección de los claims, la calidad de los veredictos, la
exhaustividad de la extracción ni la existencia de un mecanismo
automático de corrección o regeneración de la respuesta.

La confirmación debe completarse con una traza instrumentada que
registre los argumentos exactos de `run()`, las evidencias asociadas a
cada afirmación, los resultados de cada subcomponente y el contenido que
efectivamente se presenta al usuario. La auditoría experimental todavía
no se ha iniciado.

### A.6 Estado de la auditoría tras inspeccionar GitHub

| Actividad                                                                   | Estado actualizado                                                       |
|:----------------------------------------------------------------------------|:-------------------------------------------------------------------------|
| Acceso al repositorio                                                       | Confirmado: repositorio público accesible                                |
| Identificación de rama                                                      | `main`                                                                   |
| Identificación de `main_multilinea.py`                                      | Confirmada                                                               |
| Importación e inicialización del pipeline                                   | Confirmadas                                                              |
| Inicialización de RAG                                                       | Confirmada                                                               |
| Inicialización de DDGS                                                      | Confirmada                                                               |
| Selección de modalidad de fuentes                                           | Confirmada                                                               |
| Construcción de contexto temporal                                           | Confirmada                                                               |
| Llamada al LLM, ejecución posterior del pipeline y presentación del informe | Flujo funcional confirmado; orden interno y trazabilidad fina pendientes |
| Contrato interno del pipeline                                               | Pendiente                                                                |
| Algoritmo y parámetros efectivos de EvidenceVerifier                        | Pendiente                                                                |
| Auditoría experimental                                                      | No iniciada                                                              |

**Conclusión de esta actualización:** no hace falta que el usuario envíe
un ZIP para comenzar el análisis estático del repositorio público. Se
continuará utilizando la rama `main` como referencia y se señalarán
expresamente las diferencias que solo puedan resolverse contrastando con
la instalación local.
