# Prueba comparativa del recuperador de conocimiento

## Propósito
Comparar el módulo original y la versión revisada usando las mismas cuatro consultas de `Tests/test_knowledge_quality.py`. La prueba no modifica el módulo original ni los tests existentes.

## Preparación
1. Mantener `Agent/KnowledgeRetriever.py` sin cambios.
2. Copiar el archivo descargado `KnowledgeRetriever_revisado.py` dentro de `Agent/`, conservando exactamente ese nombre.
3. Guardar este script como `Tests/test_knowledge_retriever_comparison.py`.

La estructura temporal esperada es:

```text
GIAR-ORION/
├── Agent/
│   ├── KnowledgeRetriever.py
│   └── KnowledgeRetriever_revisado.py
└── Tests/
    └── test_knowledge_retriever_comparison.py
```

## Ejecución
Desde la raíz del proyecto, con `.venv` activado:

```powershell
python .\\Tests\\test_knowledge_retriever_comparison.py
```

## Qué mide
Para cada una de las cuatro consultas:
- encuentra la posición del fragmento que contiene todas las frases esperadas;
- muestra las puntuaciones y los tres primeros fragmentos de ambas versiones;
- informa si la posición mejora, empeora o queda igual.

## Límites
Esta prueba compara ranking para cuatro casos conocidos. No demuestra calidad general ni comprensión semántica. El cambio solo debe aceptarse después de revisar los resultados y ejecutar también los tests existentes.
