# Registro de cambios — KnowledgeRetriever, iteración 2

**Fecha:** 2026-10-11  
**Estado:** versión candidata; no aceptada hasta completar las pruebas.  
**Archivo candidato:** `Agent/KnowledgeRetriever_revisado.py`

## 1. Evidencia de la iteración 1

La comparación sobre cuatro consultas mostró:
- Replay Buffer: regresión de posición 1 a 2.
- Actualización de los críticos: mejora de posición 3 a 1.
- Temperatura automática: sin cambio (posición 1).
- Redes objetivo: sin cambio (posición 1).

La causa identificada para la regresión de Replay Buffer fue que el marcador genérico «durante el entrenamiento» aumentaba la puntuación de un fragmento de uso del búfer por encima de la definición del concepto.

## 2. Cambios de esta iteración

### 2.1 Marcadores explicativos más específicos
Se quitó «durante el entrenamiento» de los marcadores explicativos. Se conservaron marcadores más específicos como «consiste en», «se define como», «se utiliza para» y «su función es».

**Justificación:** una frase que solo ubica temporalmente un proceso no debería recibir automáticamente una bonificación por ser explicativa.

### 2.2 Bonificación y penalización moderadas
El factor explicativo se ajustó a:
- `1.10` para marcadores explicativos sin marcadores de metadiscurso.
- `0.80` para marcadores de metadiscurso sin marcadores explicativos.
- `1.00` si aparecen ambos o ninguno.

En la iteración anterior los factores eran `1.15` y `0.75`. La reducción de su magnitud limita la influencia de esta heurística sobre la puntuación léxica.

### 2.3 Resto del algoritmo
Se conserva la cobertura de términos, el factor de información, la penalización por longitud, la penalización de listas, la bonificación literal, el desempate y la estructura de salida.

## 3. Alcance y limitaciones

Esta sigue siendo una heurística léxica basada en palabras y frases indicadoras; no es una búsqueda semántica. Los marcadores pueden no generalizar a todas las formas de redacción. Cuatro consultas constituyen una prueba inicial pequeña, no una validación general del buscador.

## 4. Validación requerida

1. Sustituir el contenido de `Agent/KnowledgeRetriever_revisado.py` por esta versión candidata.
2. Ejecutar:
   ```powershell
   python .\Tests\test_knowledge_retriever_comparison.py
   ```
3. Revisar las cuatro posiciones y las puntuaciones.
4. Si la comparación es satisfactoria, ejecutar:
   ```powershell
   python .\Tests\test_knowledge_retriever.py
   python .\Tests\test_knowledge_quality.py
   ```
5. Consultar Ollama solo después de verificar las pruebas del recuperador.

## 5. Criterio de decisión

No aceptar la iteración si mantiene la regresión de Replay Buffer o si introduce una regresión nueva. La meta inicial es recuperar la posición 1 para Replay Buffer y mantener la mejora de los críticos, sin degradar las otras dos consultas. Si no se consigue, documentar el resultado y reconsiderar si un factor global por marcadores es apropiado.
