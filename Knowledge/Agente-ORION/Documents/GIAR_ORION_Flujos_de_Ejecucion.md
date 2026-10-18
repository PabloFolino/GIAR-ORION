# GIAR-ORION — Flujos de ejecución

**Tipo:** descripción de flujos conocidos.  
**Estado:** conceptual; debe contrastarse con la implementación vigente.

## 1. Flujo conversacional general

1. El usuario escribe una consulta.
2. `main.py` recibe la consulta y coordina el procesamiento.
3. Si la recuperación está habilitada, el RAG busca fragmentos en la base documental.
4. Los fragmentos seleccionados se utilizan como contexto según la implementación.
5. `main.py` construye una solicitud para la API de chat de Ollama.
6. Ollama ejecuta el modelo configurado, conocido durante las pruebas como `qwen3:8b`.
7. La aplicación recibe la respuesta y sus metadatos.
8. La aplicación muestra el texto y, cuando está instrumentada, datos de diagnóstico.

Esta es una descripción lógica. El orden exacto y las ramas condicionales deben comprobarse en el código vigente.

## 2. Flujo de recuperación RAG

1. El recuperador recibe la consulta.
2. La consulta se transforma para la búsqueda.
3. El sistema compara la consulta con fragmentos del corpus indexado.
4. En el modo híbrido conocido intervienen Multilingual E5 y BGE-M3.
5. Los resultados se combinan según la configuración vigente.
6. Se seleccionan hasta `top_k` fragmentos.
7. Los fragmentos se devuelven al componente que prepara el contexto de generación.

El algoritmo exacto, la normalización de puntuaciones, los filtros y la combinación deben verificarse en `Agent/MultilingualKnowledgeRetriever.py`.

### Señales de un posible problema de recuperación

- Los fragmentos no contienen los datos necesarios.
- Los resultados tratan temas diferentes al consultado.
- Aparecen índices, bibliografías o texto genérico en posiciones altas.
- Hay fragmentos repetidos o con poco contenido útil.
- Una fuente pertinente existe en `Knowledge`, pero no aparece entre los resultados.

La ausencia de una fuente esperada solo puede interpretarse si la prueba definió correctamente esa fuente y si la información existe realmente en el corpus.

## 3. Flujo de generación con Ollama

1. La aplicación prepara los mensajes y el contexto disponible.
2. Selecciona los parámetros correspondientes al modo de generación.
3. Construye una solicitud a la API de chat de Ollama.
4. La solicitud observada incluye el modelo, los mensajes, `think` y `options.num_predict`, entre otros campos.
5. Ollama genera una respuesta.
6. La aplicación recibe el contenido y los metadatos.
7. La respuesta se presenta al usuario.

`num_predict` limita la cantidad de tokens nuevos; no garantiza que se cubran todos los requisitos. Si está disponible, debe registrarse `done_reason`, por ejemplo `stop` o `length`.

## 4. Inicialización y caché

El sistema puede cargar embeddings documentales previamente guardados en `Cache`:

- `e5_embeddings.npy`
- `bge_embeddings.npy`
- `metadata.json`

Si la caché coincide con el corpus, los modelos y los parámetros relevantes, puede reutilizarse. Si no coincide o no es válida, puede ser necesario reconstruirla.

La caché no evita necesariamente que los modelos de embeddings se carguen al iniciar. Las condiciones exactas de validación deben confirmarse en el código actual.

## 5. Diagnóstico: separar recuperación y generación

### Paso A — Definir requisitos

Enumerar los puntos que una respuesta correcta debe cubrir. Esta lista es la referencia para evaluar la integridad.

### Paso B — Inspeccionar la recuperación

Comprobar si los fragmentos recuperados contienen información suficiente.

- Si la información falta, investigar el corpus, la fragmentación, el recuperador y la configuración.
- Si está presente, pasar a evaluar la generación.

### Paso C — Inspeccionar la generación

Comparar la respuesta con los fragmentos y los requisitos.

- Si omite datos disponibles, puede haber un problema de generación.
- Si contradice el contexto, revisar la interpretación y las instrucciones.
- Si incorpora datos no respaldados, registrar una posible alucinación.
- Si responde solo algunos requisitos, medir la cobertura de la respuesta.

### Paso D — Inspeccionar longitud y finalización

Registrar, cuando estén disponibles:

- Tokens generados.
- Límite `num_predict`.
- Duración total.
- `done_reason`.

No diagnosticar truncamiento únicamente por la longitud. Una respuesta puede estar incompleta y terminar con `stop`; también puede alcanzar el límite después de haber cubierto los requisitos esenciales.

### Paso E — Clasificar

- **Recuperación:** falta información necesaria en los fragmentos.
- **Generación:** la información está disponible, pero no se utiliza adecuadamente.
- **Mixto:** se observan ambos problemas.
- **Indeterminado:** falta evidencia suficiente.

## 6. Estrategias de generación para evaluar posteriormente

1. Planificar la respuesta según los requisitos explícitos.
2. Cubrir primero todos los puntos esenciales y luego añadir detalles.
3. Reducir redundancias e introducciones innecesarias.
4. Generar por etapas cuando la respuesta sea extensa.
5. Detectar respuestas incompletas y continuar desde los puntos pendientes.
6. Verificar cobertura, coherencia y repeticiones al finalizar.

Estas estrategias deben compararse mediante preguntas de referencia. Ninguna instrucción garantiza por sí sola integridad absoluta; una continuación sin control puede repetir o contradecir contenido previo.

## 7. Alcance

Estos flujos describen el comportamiento lógico conocido, no una traza exhaustiva de cada llamada. Las preguntas sobre orden real de ejecución, condiciones o tratamiento de errores deben resolverse inspeccionando el código fuente vigente.
