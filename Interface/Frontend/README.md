# GIAR-ORION — Prototipo Frontend

Prototipo navegable de la interfaz multiagente basado en la referencia visual aportada.

## Ejecutar
1. Descomprimir la carpeta.
2. Abrir `index.html` en un navegador, o abrir la carpeta en Visual Studio Code.
3. Para desarrollo, se puede utilizar la extensión Live Server de VS Code.

## Archivos
- `index.html`: estructura de la interfaz.
- `css/styles.css`: estilos y adaptación responsive.
- `js/app.js`: interacciones de demostración.

## Interacciones incluidas
- Selección de los seis agentes.
- Cambio del modo de conversación.
- Envío de mensajes con respuesta simulada.
- Acciones rápidas que completan el campo de mensaje.
- Creación de conversaciones.
- Navegación superior con respuestas informativas de demostración.

## Límites de esta versión
Es únicamente el frontend de demostración. No incluye API, persistencia, conexión a Ollama ni integración con `main_multilinea.py`. Los avatares son representaciones gráficas temporales; podrán sustituirse por los recursos visuales definitivos.


## Adaptación responsive (v0.2)
La interfaz utiliza el tamaño disponible del navegador (`100dvh`, anchos flexibles,
`clamp()` y puntos de adaptación por anchura y altura). En pantallas medianas
se oculta el panel contextual derecho; en móviles se compacta la lista de agentes
y se prioriza la conversación. No se fija una resolución de 1440 × 900.

La hoja de estilos no depende de una fuente descargada de Internet. Los controles
de voz, adjuntos y navegación siguen siendo demostrativos.
