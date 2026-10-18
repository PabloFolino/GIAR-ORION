# GIAR-ORION — Arquitectura del sistema

**Tipo:** documentación arquitectónica inicial.  
**Estado:** descriptivo; debe contrastarse con el código vigente antes de afirmar detalles exactos.

## 1. Propósito

GIAR-ORION es un agente local de IA orientado a investigación y desarrollo en robótica, con especial interés en aprendizaje por refuerzo (RL), aprendizaje profundo por refuerzo (DRL), Soft Actor-Critic (SAC), Unitree G1 y simulación robótica.

El agente utiliza Ollama para comunicarse con un modelo de lenguaje local. El modelo conocido durante las pruebas es `qwen3:8b`, servido en `http://localhost:11434`.

El agente también dispone de recuperación aumentada por generación (RAG), que recupera fragmentos de una base documental para incorporarlos al contexto de las consultas.

## 2. Componentes conocidos

### 2.1 Aplicación principal: `main.py`

`main.py` es el punto de entrada conversacional conocido. Presenta la interfaz de consola, coordina las consultas y prepara solicitudes a Ollama.

Se han observado los comandos `/salir`, `/limpiar`, `/guardar`, `/sesiones`, `/modo rapido` y `/modo investigacion`. El efecto preciso de cada comando debe comprobarse en la versión vigente de `main.py`.

### 2.2 Modelo de lenguaje: Ollama + Qwen

La configuración conocida utiliza `qwen3:8b` mediante Ollama. La solicitud observada incluye mensajes y parámetros como `think` y `num_predict`; `stream` se configuró como `false` en la versión instrumentada.

`num_predict` es un máximo de tokens nuevos, no una garantía de que la respuesta cubra todos los requisitos de la pregunta.

### 2.3 Recuperación documental: RAG

El recuperador conocido está en `Agent/MultilingualKnowledgeRetriever.py` y usa un modo híbrido con:

- Multilingual E5.
- BGE-M3.

La configuración observada durante las pruebas incluía `mode=hybrid`, `top_k=5`, `device=cpu`, `show_sources=true`, peso E5 de 0,70 y peso BGE-M3 de 0,30. Estos valores deben confirmarse en el `config.json` vigente antes de tratarlos como actuales.

El recuperador selecciona fragmentos; el modelo de lenguaje genera la respuesta. Son etapas distintas y deben evaluarse por separado.

### 2.4 Base de conocimiento: `Knowledge`

`Knowledge` contiene documentación técnica que el RAG puede recuperar, incluidos materiales sobre RL, SAC, Unitree G1 y CoppeliaSim. La respuesta mediante RAG depende de que la información pertinente exista en el corpus y de que se recuperen los fragmentos adecuados.

### 2.5 Caché de embeddings: `Cache`

La caché persistente conocida contiene:

- `e5_embeddings.npy`
- `bge_embeddings.npy`
- `metadata.json`

Su propósito es reutilizar embeddings documentales cuando el corpus, los modelos y los parámetros relevantes coinciden. Esto evita recalcular necesariamente todos los embeddings en cada inicio, pero no implica que los modelos de embeddings nunca deban cargarse.

### 2.6 Configuración: `config.json`

La configuración contiene parámetros del modelo, modos de generación y ajustes del RAG. Se conocen los modos rápido e investigación. Los valores efectivos deben leerse del archivo actual y no inferirse de este documento.

## 3. Flujo lógico general

1. El usuario introduce una consulta.
2. `main.py` coordina el procesamiento.
3. El RAG busca fragmentos en `Knowledge`, cuando la recuperación está habilitada.
4. Los fragmentos se incorporan al contexto de generación según la implementación.
5. La aplicación envía mensajes y parámetros a Ollama.
6. Ollama ejecuta el modelo y devuelve contenido y metadatos.
7. La aplicación presenta la respuesta y, cuando corresponde, fuentes o datos de diagnóstico.

La secuencia exacta de llamadas, condiciones y tratamiento de errores debe verificarse en el código vigente.

## 4. Cómo diagnosticar una respuesta deficiente

- **Problema de recuperación:** la información necesaria no está en los fragmentos recuperados, o estos son irrelevantes, incompletos o redundantes.
- **Problema de generación:** la información está en el contexto, pero el modelo la omite, interpreta mal o no cubre los requisitos.
- **Problema mixto:** se observan deficiencias en ambas etapas.
- **Indeterminado:** no hay evidencia suficiente para atribuir el fallo.

La ausencia de información en `Knowledge` no debe confundirse automáticamente con un fallo del recuperador.

## 5. Fiabilidad y límites

Una respuesta no debe considerarse correcta solo porque esté expresada con seguridad. La fiabilidad depende de la pertinencia de los fragmentos, su interpretación, la configuración efectiva y la cobertura de los requisitos.

Las preguntas sobre la implementación interna deben contrastarse con el código y la configuración vigentes. Si solo se dispone de esta documentación general, la respuesta debe indicar esa limitación.

## 6. Estado de verificación

Este documento resume datos conocidos durante el desarrollo de GIAR-ORION. No sustituye una auditoría del repositorio completo. No se deben inventar nombres de funciones, detalles de implementación ni valores actuales sin verificar las fuentes correspondientes.
