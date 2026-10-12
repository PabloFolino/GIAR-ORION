# Registro de cambios — KnowledgeRetriever, iteración 3

**Fecha:** 2026-10-11  
**Estado:** candidata a validación; todavía no aceptada.  
**Base revisada:** `KnowledgeRetriever_revisado(1).py` aportado para comparación.

## 1. Evidencia de la iteración 2

La comparación mostró:
- Replay Buffer: explicación esperada en posición 2 (regresión frente a posición 1 del original).
- Actualización de los críticos: explicación esperada en posición 1 (mejora frente a posición 3).
- Temperatura automática: posición 1, sin cambio.
- Redes objetivo: posición 1, sin cambio.

La revisión del código identificó que la versión candidata había agregado un desempate por longitud:
`-self._contar_palabras(resultado["text"])`.

Cuando dos fragmentos tenían la misma puntuación y la misma cantidad de términos coincidentes, ese criterio favorecía el fragmento más corto. En la consulta «Replay Buffer», esto movió la explicación sobre el uso del búfer delante de su definición. Por lo tanto, la regresión observada no se debió al marcador «durante el entrenamiento» en la versión 2: se debió al nuevo desempate por longitud.

## 2. Cambio de esta iteración

Se elimina el desempate por longitud. El orden vuelve a utilizar:
1. puntuación;
2. cantidad de términos coincidentes.

Cuando ambos valores empatan, el ordenamiento estable de Python conserva el orden en que los fragmentos fueron encontrados en los documentos.

## 3. Qué se conserva

- Los marcadores explicativos y de metadiscurso de la versión 2.
- Los factores de cobertura, información, longitud, lista y coincidencia literal.
- La firma de `buscar()` y las claves de los resultados.
- La estructura del proyecto y las dependencias.

No se modifica `main.py` ni el archivo original `Agent/KnowledgeRetriever.py`.

## 4. Hipótesis comprobable

La hipótesis es que, al eliminar el desempate por longitud, Replay Buffer volverá a la posición 1, mientras que la explicación de actualización de los críticos permanecerá en posición 1 por su puntuación más alta en la versión candidata.

Esto es una predicción, no un resultado medido todavía. Debe comprobarse con la comparación ejecutada en el proyecto local.

## 5. Validación requerida

1. Copiar el contenido de `KnowledgeRetriever_revisado_v3.py` sobre el archivo temporal `Agent/KnowledgeRetriever_revisado.py`.
2. Ejecutar:
   ```powershell
   python .\Tests\test_knowledge_retriever_comparison.py
   ```
3. Si los cuatro casos resultan aceptables, ejecutar:
   ```powershell
   python .\Tests\test_knowledge_retriever.py
   python .\Tests\test_knowledge_quality.py
   ```
4. Ejecutar la prueba con Ollama solo después de validar el ranking.

## 6. Criterio de decisión

No aceptar esta iteración sin observar la salida real. Se espera:
- Replay Buffer: posición 1.
- Actualización de los críticos: posición 1.
- Temperatura automática: posición 1.
- Redes objetivo: posición 1.

Si el resultado difiere, registrar la diferencia y volver a analizar los factores de puntuación antes de cambiar el módulo original.
