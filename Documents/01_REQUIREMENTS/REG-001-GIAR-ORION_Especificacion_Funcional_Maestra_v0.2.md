# GIAR-ORION --- Especificación funcional maestra

**Código:** GIAR-ORION-DES-001\
**Versión:** 0.2\
**Fecha:** 10/11/2026\
**Estado:** Borrador consolidado para revisión\
**Alcance:** Diseño funcional conceptual de los módulos 1 a 24.

## Control de versiones del documento

| Versión | Fecha | Cambios | Estado |
|---|---|---|---|
| 0.1 | 10/11/2026 | Consolidación inicial de decisiones conversadas para los módulos 1–24; identificación de pendientes y propuestas no aprobadas. | Borrador |
| 0.2 | 10/11/2026 | Desarrollo funcional del Módulo 19 con quince decisiones aprobadas; actualización de pendientes y próxima etapa. | Borrador consolidado para revisión |

## Criterios de lectura

-   **Aprobado funcionalmente:** decisión aceptada; no significa
    implementado ni probado.
-   **Aprobado conceptualmente / pendiente de detalle:** se aceptó
    incorporar el módulo, pero falta especificarlo.
-   **En definición:** hay decisiones pendientes.
-   **Propuesto:** recomendación no aprobada expresamente.
-   **Pendiente:** falta decisión o especificación.

Este documento registra diseño conceptual. No afirma que exista código,
estructura de carpetas o funcionalidad implementada.

# 1. Visión general

GIAR-ORION se concibe como una plataforma local multiagente para
investigación, desarrollo, robótica, software, seguridad, idiomas,
mercado y futuras especialidades. ORION coordina agentes, tareas,
permisos, recursos, proyectos, evidencias y resultados.

## Principios acordados

1.  ORION es el coordinador central y no se deshabilita mediante
    administración ordinaria.
2.  Agentes especializados tienen identidad, configuración, memoria,
    conocimiento, herramientas, logs, avatar y voz propios.
3.  Los servicios comunes se centralizan cuando convenga.
4.  No duplicar innecesariamente instancias del mismo modelo LLM.
5.  Funcionamiento offline como requisito; Internet es opcional.
6.  Compatibilidad Windows 11 y Ubuntu desde el diseño.
7.  Escalabilidad desde una GPU a varias GPU y equipos en red local.
8.  Autonomía configurable, siempre sujeta a objetivos, permisos,
    recursos y límites.
9.  Seguridad por diseño, auditoría y autenticación reforzada para
    operaciones sensibles.
10. Trazabilidad de tareas, archivos, experimentos, cambios, evidencias
    y decisiones.
11. Preservar originales y versiones aprobadas.
12. Medir y probar antes de modificar arquitectura.
13. Separar recuperación RAG, memoria, generación LLM, verificación,
    decisión, aprendizaje y entrenamiento.
14. Los objetivos principales, cambios críticos, acciones destructivas y
    operaciones sensibles requieren autorización.
15. Mantener documentación versionada y una bitácora de trabajo real.

## Agentes iniciales

  -----------------------------------------------------------------------
  Agente                              Responsabilidad
  ----------------------------------- -----------------------------------
  ORION                               Coordinador central, políticas,
                                      asignación, permisos, supervisión y
                                      consolidación.

  ORION-ROBOTICS                      Robótica, simulación, RL,
                                      investigación y desarrollo.

  ORION-SOFTWARE                      Programación e ingeniería de
                                      software.

  ORION-SECURITY                      Seguridad informática y análisis de
                                      amenazas.

  ORION-LANGUAGES                     Traducción, interpretación y
                                      enseñanza de idiomas.

  ORION-MARKETING                     Investigación de mercado,
                                      proveedores, productos,
                                      comparaciones y costos.
  -----------------------------------------------------------------------

Cada agente tiene identidad y contexto propios. La inferencia LLM y
otros servicios compartidos se administran centralmente.

## Modos de interacción

-   **Coordinador:** el usuario conversa con ORION, que deriva tareas.
-   **Agente directo:** el usuario selecciona un agente; ORION sigue
    coordinando internamente permisos y supervisión.
-   **Colaborativo:** varios agentes trabajan juntos bajo coordinación
    de ORION.

Los agentes pueden comunicarse directamente en tareas permitidas. ORION
interviene en asignación, prioridades, permisos, operaciones sensibles,
conflictos y consolidación. Los desacuerdos deben hacerse visibles; no
se convierten opiniones en evidencias.

## Contexto técnico de referencia

  Elemento               Referencia conocida
  ---------------------- --------------------------------------
  SO actual              Windows 11
  SO futuro              Ubuntu
  GPU actual             NVIDIA RTX 5070 Laptop, 8 GB VRAM
  Runtime local          Ollama
  Modelo de referencia   Qwen3:8B
  Conectividad           Local/offline, Internet opcional
  Red local              Puede conectar computadora y celular
  Escalabilidad          Varias GPU en el futuro

Este contexto no limita el diseño a ese hardware.

# 2. Especificación por módulos

Cada módulo incluye historial de versiones al comienzo. La versión 0.1
indica consolidación funcional inicial, no implementación. La columna
"Próximo trabajo" señala la siguiente actividad de diseño o ingeniería.

## MÓDULO 1 --- INTERFAZ PRINCIPAL

  -------------------------------------------------------------------------
  Versión           Cambios realizados  Estado            Próximo trabajo
  ----------------- ------------------- ----------------- -----------------
  0.1               Aprobada línea      Aprobado          Especificar
                    visual profesional  funcionalmente    pantallas,
                    tecnológica +                         navegación,
                    futurista; tema                       componentes y
                    grafito/azul,                         comportamiento
                    acentos                               responsive.
                    cian/violeta; panel                   
                    agentes, chat                         
                    central,                              
                    avatar/actividad,                     
                    barra superior y                      
                    entrada texto/voz.                    

  -------------------------------------------------------------------------

**Objetivo y detalles** - Interfaz principal para usuario, ORION y
agentes. - Panel izquierdo: agentes; centro: conversación; panel
derecho: avatar 3D, identidad y actividad. - Barra superior: navegación,
estado general e indicador móvil. - Seis agentes iniciales visibles y
seleccionables. - Estados: disponible, ocupado, comunicándose,
desconectado, deshabilitado y error. - Accesos: comunicaciones, tareas,
conocimiento, administración, proyectos y reportes. - Niveles de
visualización: - Desarrollo: intervenciones, comunicaciones, resultados
y procesos. - Intermedio: agentes, tareas y avances principales. -
Producción: respuesta final principalmente. - Ocultar informes no
desactiva logs ni auditoría. - Indicador móvil: gris (no habilitado/no
vinculado), verde (conectado), amarillo (habilitado pero desconectado),
rojo (error). Al abrirlo: estado, dispositivo, Wi-Fi, última
comunicación, habilitar/deshabilitar y vincular. - Pendiente:
resolución, accesibilidad, navegación completa y especificación visual
definitiva.

## MÓDULO 2 --- CENTRO DE COMUNICACIONES

  -----------------------------------------------------------------------
  Versión           Cambios           Estado            Próximo trabajo
                    realizados                          
  ----------------- ----------------- ----------------- -----------------
  0.1               Centro con lista  Aprobado          Definir
                    de                funcionalmente    protocolo,
                    agentes/grupos,                     estados,
                    conversación y                      persistencia,
                    detalles; tipos                     búsqueda y
                    consulta,                           adjuntos.
                    colaboración,                       
                    transferencia y                     
                    supervisión;                        
                    registro.                           

  -----------------------------------------------------------------------

**Detalles** - Comunicaciones iniciadas por ORION, agente autorizado o
usuario. - Modelo híbrido: comunicación directa permitida entre agentes,
con supervisión central de ORION. - Los archivos compartidos no entran
automáticamente al RAG; pasan por Knowledge Manager. - Registro mínimo:
ID conversación, emisor/receptor, fecha, motivo, mensajes, archivos,
tarea y resultado. - Pendiente: mensajería síncrona/asíncrona, colas,
reintentos, retención y contratos de comunicación.

## MÓDULO 3 --- TASK MANAGER + RESOURCE MANAGER + MODEL MANAGER

  ------------------------------------------------------------------------
  Versión           Cambios realizados Estado            Próximo trabajo
  ----------------- ------------------ ----------------- -----------------
  0.1               Gestión coordinada Aprobado          Definir
                    de tareas,         funcionalmente    contratos, colas,
                    recursos e                           prioridades,
                    inferencia; no                       concurrencia y
                    duplicar                             métricas.
                    innecesariamente                     
                    Qwen3 por agente.                    

  ------------------------------------------------------------------------

**Detalles** - Task Manager: tareas, dependencias, prioridad, progreso,
estado, cancelación, suspensión y reanudación. - Resource Manager: CPU,
RAM, GPU, VRAM, disponibilidad y ejecuciones. - Model Manager: modelos,
instancias/servicios de inferencia, solicitudes, concurrencia y
versiones. - Diferenciar concurrencia de agentes/tareas de concurrencia
de inferencia. - Una GPU inicialmente; varias en el futuro. Los agentes
solicitan recursos a los managers y no dependen de hardware concreto. -
Ante falta de recursos, ordenar prioridades/colas, informar al usuario y
permitir intervención. - Panel: GPU, VRAM, CPU, RAM, modelos activos,
cola y ejecuciones. - Pendiente: planificación, cuotas, límites por
usuario/proyecto y políticas de memoria GPU.

## MÓDULO 4 --- KNOWLEDGE MANAGER

  -----------------------------------------------------------------------
  Versión           Cambios           Estado            Próximo trabajo
                    realizados                          
  ----------------- ----------------- ----------------- -----------------
  0.1               Bibliotecas       Aprobado          Definir esquema,
                    privadas,         funcionalmente    motor vectorial,
                    compartidas y                       pipeline, índices
                    globales;                           y pruebas.
                    permisos                            
                    granulares;                         
                    pipeline                            
                    documental;                         
                    evaluación de                       
                    recuperación.                       

  -----------------------------------------------------------------------

**Detalles** - Bibliotecas privadas por agente, compartidas y
globales. - Acceso libre a biblioteca propia; autorización para
bibliotecas privadas ajenas; permisos en compartidas/globales. -
Permisos: READ, WRITE, UPDATE, DELETE, SHARE; posibilidad de permisos
temporales por proyecto. - Ingesta: validación, extracción,
normalización, chunking, embeddings, indexación, pruebas y validación. -
Estados: pendiente, validando, procesando, indexando, indexado, indexado
con advertencias, error, desactualizado. - Agentes pueden proponer
conocimiento; bandeja de revisión; incorporación permanente autorizada
por usuario o política. - Originales separados de índices; referencias
cuando sea posible. - Pruebas RAG: relevancia, precisión de fragmentos,
cobertura, recuperación crítica, latencia y comparación de versiones. -
Distinguir errores RAG de generación LLM. - UI: bibliotecas, documentos,
procesamiento, validación y propuestas. - Pendiente: búsqueda híbrida,
reranking, metadatos, versionado y métricas.

## MÓDULO 5 --- MEMORY MANAGER

  --------------------------------------------------------------------------
  Versión           Cambios realizados   Estado            Próximo trabajo
  ----------------- -------------------- ----------------- -----------------
  0.1               Modelo híbrido de    Aprobado          Definir ciclo de
                    guardado; cuatro     funcionalmente    vida,
                    tipos de memoria;                      recuperación,
                    memoria                                consolidación,
                    privada/compartida y                   contradicciones y
                    separación de                          permisos.
                    Knowledge.                             

  --------------------------------------------------------------------------

**Detalles** - Working: tarea actual. - Episodic: experiencias. -
Semantic: hechos, relaciones y conclusiones. - Procedural: métodos y
procedimientos. - Memoria privada por agente y compartida. -
`Knowledge/` es biblioteca documental/RAG; `Memory/` es memoria
experiencial/operativa. - Memory Retriever separado de Knowledge
Retriever; pueden combinarse, con fuentes y evaluaciones
diferenciadas. - Estructura conceptual: `Memory/Working`, `Episodic`,
`Semantic`, `Procedural`, `Indexes`; `Knowledge/Documents`,
`Embeddings`, `Indexes`, `Metadata`. - Memoria no modifica
automáticamente pesos del LLM ni equivale a entrenamiento. - Metadatos:
origen, confiabilidad, referencias a tareas/documentos/experimentos;
detectar duplicados/contradicciones, archivar, versionar, buscar y
borrar con permisos. - Guardado automático de recuerdos operativos de
bajo riesgo; conclusiones permanentes, procedimientos y memoria
compartida requieren validación según políticas. - Pendiente: esquema,
confianza, caducidad, consolidación, privacidad y pruebas.

## MÓDULO 6 --- SECURITY & THREAT DETECTION

  --------------------------------------------------------------------------------
  Versión           Cambios realizados         Estado            Próximo trabajo
  ----------------- -------------------------- ----------------- -----------------
  0.1               Arquitectura híbrida con   Aprobado          Definir amenazas,
                    herramientas consolidadas  funcionalmente    adaptadores,
                    y núcleo propio de                           telemetría,
                    supervisión/correlación;                     respuesta y
                    Windows y Ubuntu.                            autorizaciones.

  --------------------------------------------------------------------------------

**Detalles** - Núcleo ORION SECURITY CORE común y adaptadores por SO. -
Windows: Defender/API, firewall, Event Logs (candidatos). - Ubuntu:
ClamAV u otras herramientas, firewall, journald, auditd (candidatos). -
ORION-SECURITY analiza; el núcleo aplica políticas. No delegar toda la
seguridad al agente. - Amenazas: intrusiones, malware, virus,
ransomware, troyanos, spyware, phishing, IP/dominios sospechosos,
escaneo de puertos, ataques de red, procesos/servicios, startup, cambios
de archivos y puertos. - Respuestas: informativo, advertencia, alto,
crítico. - Evitar borrar archivos o detener procesos sin validación;
contención automática solo con políticas explícitas. - Offline: análisis
local y firmas disponibles; inteligencia online opcional. - Perfiles
Normal/Alto/Crítico fueron propuestos, no formalmente aprobados. - No
prometer detección total ni reemplazo del antivirus del SO. - Pendiente:
matriz de riesgo, contención, telemetría, privacidad, pruebas y
perfiles.

## MÓDULO 7 --- VOICE & AVATAR ENGINE

  -----------------------------------------------------------------------
  Versión           Cambios           Estado            Próximo trabajo
                    realizados                          
  ----------------- ----------------- ----------------- -----------------
  0.1               Avatares 3D       Aprobado          Comparar
                    interactivos;     funcionalmente    tecnologías,
                    STT/TTS; voces                      latencia,
                    por agente;                         calidad, consumo
                    servicios                           y compatibilidad.
                    compartidos y                       
                    estados visuales                    
                    reales.                             

  -----------------------------------------------------------------------

**Detalles** - STT, TTS, push-to-talk, conversación continua, VAD e
interrupción de TTS. - Voz propia por agente. - Avatar humanoide 3D con
lip-sync, parpadeo, cabeza, mirada, expresiones y gestos discretos. - El
avatar refleja estados reales: escuchando, procesando, hablando,
comunicándose y error. - Componentes separados: Agent (lógica), Voice
Engine (STT/TTS), Avatar Engine (visual/animación). - STT/TTS
compartidos cuando sea conveniente. - Candidatos: Whisper, Piper/Kokoro,
Three.js, VAD y WebSocket; aún no seleccionados. - Windows, Ubuntu y
móvil; escritorio completo y versión móvil adaptada. - Resource Manager
controla CPU/GPU. - Pendiente: pruebas de calidad, latencia, consumo,
licencias y offline.

## MÓDULO 8 --- PROJECT & WORKFLOW MANAGER

  -----------------------------------------------------------------------
  Versión           Cambios           Estado            Próximo trabajo
                    realizados                          
  ----------------- ----------------- ----------------- -----------------
  0.1               Modelo híbrido;   Aprobado          Definir ciclo,
                    línea base        funcionalmente    esquema, Git,
                    aprobada; cambios                   aprobaciones y
                    importantes                         flujos.
                    sujetos a                           
                    aprobación;                         
                    tareas,                             
                    dependencias,                       
                    versiones y                         
                    estructura de                       
                    proyecto.                           

  -----------------------------------------------------------------------

**Detalles** - ORION planifica/reorganiza dentro de objetivos y
permisos. - Aprobación necesaria para cambiar objetivos, requisitos
aprobados, eliminar/reemplazar entregables, cambios importantes de
arquitectura, operaciones destructivas y finalizar proyecto. - Línea
base: objetivos, requisitos, alcance, arquitectura, entregables y
restricciones. No se cambia unilateralmente. - Ciclo: inicio, análisis,
planificación, desarrollo, validación, integración, evaluación y
finalización. - Tarea: ID, nombre, descripción, responsable, prioridad,
estado, dependencias, fechas y resultados. - Ejecución paralela
coordinada con Resource Manager. - Git/versionado, identificación de
agente y protección de originales/versiones aprobadas. - Persistencia
integrada con Session Manager. - Estructura conceptual:
`PROJECTS/<proyecto>/config`, `requirements`, `planning`, `tasks`,
`documents`, `experiments`, `results`, `versions`, `reports`. -
Pendiente: plantillas, estados, esquema y reglas de colaboración.

## MÓDULO 9 --- REPORTING & ANALYTICS

  -----------------------------------------------------------------------
  Versión           Cambios           Estado            Próximo trabajo
                    realizados                          
  ----------------- ----------------- ----------------- -----------------
  0.1               Objetivos,        En definición     Resolver
                    evidencias,                         aprobación y
                    referencias,                        completar
                    formatos y                          validación,
                    estados de                          plantillas y
                    informe                             formatos.
                    definidos; falta                    
                    decidir                             
                    aprobación.                         

  -----------------------------------------------------------------------

**Detalles** - Informes técnicos, investigación, experimentos,
comparativas, código, seguridad, rendimiento, mercado, proyectos y
colaboración. - Evidencias: dato verificado, resultado experimental,
conclusión fundamentada, hipótesis, inferencia del modelo e información
no verificada. - Referencias a documentos, RAG, web, archivos, scripts,
experimentos y agentes. - Formatos previstos: Markdown, PDF, DOCX, XLSX,
CSV, HTML, JSON, PPTX. - Historial/versiones; informes aprobados no se
sobrescriben. - Estados: Borrador, Revisado, Validado; validar requiere
criterios explícitos, no solo revisión lingüística. - Pendiente: se
planteó A usuario, B ORION, C híbrido. Se recomendó C (rutinarios con
validación automática; científicos, experimentales, seguridad y
decisiones importantes con aprobación del usuario), pero no está
aceptada expresamente. - File Manager es transversal, no subordinado a
Reporting.

## MÓDULO 10 --- FILE MANAGER

  ------------------------------------------------------------------------------------------
  Versión           Cambios realizados                   Estado            Próximo trabajo
  ----------------- ------------------------------------ ----------------- -----------------
  0.1               Lectura/análisis y                   Aprobado          Seleccionar
                    edición/generación; servicio         funcionalmente    bibliotecas,
                    central; autonomía configurable por                    adaptadores,
                    agente/proyecto/formato/operación.                     límites y pruebas
                                                                           por formato.

  ------------------------------------------------------------------------------------------

**Detalles** - Lee, analiza, crea, edita, convierte, comprime,
descomprime, valida integridad y versiona. - Formatos contemplados: -
Documentos: PDF, DOCX, TXT, MD, ODT, RTF. - Hojas: XLSX, XLS, CSV,
ODS. - Presentaciones: PPTX, PPT, ODP. - Imágenes: PNG, JPG, JPEG, BMP,
TIFF, WEBP, SVG. - Comprimidos: ZIP, 7Z, TAR, GZ. - Código/datos: PY, C,
C++, JS, HTML, CSS, JSON, XML. - Audio: WAV, MP3, FLAC, OGG, M4A. -
Video: MP4, AVI, MKV, MOV, WEBM. - 3D: STL, OBJ, GLTF, GLB, 3DM. -
Comprender contenido requiere adaptadores especializados; abrir un
archivo no implica comprenderlo. - Imagen: OCR, diagramas/gráficos,
comparación, conversión y redimensionamiento. - ZIP: inspección,
extracción, análisis, duplicados, creación/modificación. - Protección:
ZIP bombs, path traversal, archivos maliciosos y límites de tamaño. -
Originales protegidos; edición genera copia/nueva versión;
reemplazo/eliminación según permisos. - Arquitectura propuesta: File
Detector, Reader, Writer, Converter, Archive Manager, Security Manager,
Version Manager y Format Adapters. - Permisos: READ, ANALYZE, CREATE,
WRITE, CONVERT, COMPRESS, DELETE, SHARE. - Niveles: automático,
autorizado por proyecto, requiere autorización, prohibido. - Bibliotecas
candidatas: PyMuPDF/pypdf, python-docx, openpyxl, python-pptx, Pillow,
OpenCV, Tesseract, zipfile, py7zr, FFmpeg, librosa, trimesh, pygltflib,
rhino3dm, BeautifulSoup, lxml y Tree-sitter. No son selección
definitiva. - Servicio transversal a Knowledge, Memory, Project,
Reporting, agentes y Security. - Pendiente: selección técnica y
validación formato por formato.

## MÓDULO 11 --- WEB & RESEARCH ENGINE

  -----------------------------------------------------------------------
  Versión           Cambios           Estado            Próximo trabajo
                    realizados                          
  ----------------- ----------------- ----------------- -----------------
  0.1               Investigación     Aprobado          Definir
                    online/offline,   funcionalmente    conectores,
                    fuentes                             límites,
                    múltiples,                          extracción,
                    clasificación de                    evaluación de
                    evidencia y                         fuentes y defensa
                    autonomía                           prompt injection.
                    supervisada.                        

  -----------------------------------------------------------------------

**Detalles** - Fuentes: buscadores, GitHub/GitLab, índices académicos,
documentación oficial, fabricantes y bases técnicas. - Offline:
bibliotecas, repositorios descargados, documentación local, Knowledge y
Memory. Indicar fecha de obtención/última verificación. - Capacidades:
buscar, consultar, analizar páginas/repositorios, descargar documentos
autorizados, extraer, comparar, contrastar, verificar y generar
informes. - Evidencias: verificada, respaldada, contradictoria,
hipótesis, inferencia y no verificada. - Metadatos: URL/ubicación,
título/autor, publicación, consulta, fragmento de respaldo y agente. -
Una respuesta del LLM no es evidencia por sí misma. - Autonomía
aprobada: agentes inician investigación si necesitan información; ORION
supervisa prioridades, consultas, descargas, recursos, permisos, agentes
y consolidación. - Seguridad: páginas/documentos son contenido no
confiable; protección prompt injection; validar descargas; no ejecutar
automáticamente; límites y auditoría. - Pendiente: conectores, APIs,
términos de uso, confiabilidad y caché offline.

## MÓDULO 12 --- LEARNING & ADAPTATION ENGINE

  ---------------------------------------------------------------------------------
  Versión           Cambios realizados          Estado            Próximo trabajo
  ----------------- --------------------------- ----------------- -----------------
  0.1               Aprendizaje integral:       Aprobado          Definir métricas,
                    operativo, optimización de  funcionalmente    ciclo, datasets,
                    agentes y                                     aceptación y
                    entrenamiento/fine-tuning                     límites.
                    justificado.                                  

  ---------------------------------------------------------------------------------

**Detalles** - Categorías: experiencial, procedimental, estratégica,
colaborativa y adaptativa. - Evaluación: precisión, calidad de fuentes,
objetivos, errores, tiempo, recursos, intervención humana, pruebas y
entregables. - Métricas diferentes según especialidad. - Separación: -
Knowledge/RAG: recuperación documental. - Memory: experiencias. -
Learning: evaluación/propuesta de mejora. - LLM:
interpretación/generación. - Training: modificación de pesos. -
Experimentación: hipótesis, diseño, variables, pruebas autorizadas,
registro, comparación, reproducibilidad, resultados negativos y
conclusiones. - Aprendizaje integral aprobado: 1. Operativo. 2.
Optimización de prompts, procedimientos, estrategias y RAG. 3.
Fine-tuning, LoRA, QLoRA y modelos especializados. - Model Training
Manager propuesto: datasets, validación, modelos base, fine-tuning,
LoRA/QLoRA, evaluación antes/después, comparación, versionado,
aprobación y conservación de originales. - Ciclo de mejora: hipótesis,
preparación, prueba, comparación, evaluación, aprobación cuando
corresponda, adopción o descarte. - Hardware actual: RTX 5070 Laptop con
8 GB VRAM; evaluar modelos pequeños, cuantización y técnicas eficientes;
no asumir GPU ilimitada. - Pendiente: métricas, datasets, criterios y
herramientas.

## MÓDULO 13 --- API & INTEGRATION ENGINE

  -----------------------------------------------------------------------
  Versión           Cambios           Estado            Próximo trabajo
                    realizados                          
  ----------------- ----------------- ----------------- -----------------
  0.1               Conectores        Aprobado          Verificar APIs,
                    independientes y  funcionalmente    capacidades,
                    autonomía                           contratos,
                    configurable;                       permisos y
                    agregados Webots                    pruebas.
                    y Solid Edge.                       

  -----------------------------------------------------------------------

**Detalles** - Componentes propuestos: API Manager, Connector Manager,
Device Manager, Data Exchange, Command Executor, Event Manager, Security
Manager. - Robótica/simulación: CoppeliaSim, MuJoCo, Webots, ROS 2. -
CAD: Rhino 3D y Solid Edge. - Desarrollo: VS Code, Git, GitHub; GitLab
posible. - IA: Ollama. - Hardware: Arduino, ESP32, sensores y robots. -
Niveles: consulta, interacción operativa y control físico. - Autonomía
aprobada por agente, aplicación, proyecto, dispositivo, operación y
riesgo. - Simuladores: experimentos, parámetros autorizados, iniciar
simulación y analizar resultados. - Hardware físico: controles
reforzados; permiso de simulación no habilita control real. - Seguridad:
permisos por conector, auditoría, credenciales seguras, aprobación
destructiva y bloqueo/desconexión. - Pendiente: comprobar API real,
autenticación, eventos y límites de cada aplicación.

## MÓDULO 14 --- NOTIFICATION & EVENT MANAGER

  ------------------------------------------------------------------------
  Versión           Cambios realizados Estado            Próximo trabajo
  ----------------- ------------------ ----------------- -----------------
  0.1               Gestión autónoma   Aprobado          Definir esquema,
                    de                 funcionalmente    colas,
                    acontecimientos;                     persistencia,
                    acciones                             deduplicación y
                    correctivas                          reglas.
                    autorizadas,                         
                    coordinación y                       
                    notificación                         
                    PC/móvil.                            

  ------------------------------------------------------------------------

**Detalles** - Categorías: agentes, tareas, investigación, experimentos,
seguridad, recursos, proyectos, autorizaciones y plataforma. -
Prioridades: informativo, normal, importante, alto y crítico. - Centro
de notificaciones: nuevas, historial, filtros por
agente/proyecto/prioridad, marcar leídas, acceder a tarea y ver
detalles. - Móvil por Wi-Fi local sin cloud; almacenar y sincronizar al
reconectar. - Autorizaciones con vencimiento; no ejecutar una
autorización expirada al reconectar. - Autonomía aprobada: ORION
interpreta eventos, inicia acciones permitidas, convoca agentes,
crea/reasigna tareas y pide intervención cuando corresponda. - Ejemplo:
experimento falla, evento registrado, ORION analiza, convoca software,
crea diagnóstico y coordina continuación. - Evitar ciclos infinitos: ID,
límites de reintentos y de convocatorias. - Pendiente: modelo de
eventos, broker/cola y reglas.

## MÓDULO 15 --- BACKUP & RECOVERY MANAGER

  ----------------------------------------------------------------------------
  Versión           Cambios realizados     Estado            Próximo trabajo
  ----------------- ---------------------- ----------------- -----------------
  0.1               Sistema híbrido,       Aprobado          Definir
                    estrategia 3-2-1 de    funcionalmente    herramientas,
                    referencia,                              cifrado,
                    frecuencia/retención                     retención,
                    inteligentes y                           restauración y
                    verificación.                            pruebas.

  ----------------------------------------------------------------------------

**Detalles** - Destinos: disco local, externo, NAS, otra computadora LAN
y remoto opcional. - Offline sin dependencia cloud. - Referencia 3-2-1:
tres copias, dos medios, una externa al equipo. - Modalidades: completa,
incremental, diferencial y por evento. - Eventos: cambios críticos,
actualizaciones, modelos, procedimientos, administración y proyectos. -
Proteger configuración, agentes, memoria, bibliotecas, proyectos,
experimentos, modelos según disponibilidad, código y logs. - Índices RAG
pueden reconstruirse; no necesariamente duplicarlos en cada backup. -
Recuperación de cierre inesperado, error de agente, corrupción, fallo de
plataforma y fallo de equipo. - Verificación: SHA-256, integridad,
fecha/versión, componentes, detección de copias incompletas y pruebas de
restauración. - Migración Windows/Ubuntu con validación de
dependencias. - Frecuencia/retención inteligente según criticidad,
cambios, actividad, riesgo, espacio y última copia. Respetar límites del
usuario; no borrar copias necesarias por falta de espacio. - Panel:
último/próximo backup, integridad, espacio, destinos, versiones, alertas
y restauraciones. - Pendiente: cifrado, inmutabilidad, herramientas y
restauración completa.

## MÓDULO 16 --- ADMINISTRATION & CONFIGURATION MANAGER

  -----------------------------------------------------------------------
  Versión           Cambios           Estado            Próximo trabajo
                    realizados                          
  ----------------- ----------------- ----------------- -----------------
  0.1               Administración    Aprobado          Definir esquema
                    centralizada y    funcionalmente    de configuración,
                    autonomía                           roles, secretos y
                    configurable con                    aprobaciones.
                    auditoría y                         
                    aprobación                          
                    reforzada para                      
                    cambios críticos.                   

  -----------------------------------------------------------------------

**Detalles** - Administra agentes, modelos, recursos, permisos,
seguridad, integraciones, conocimiento/memoria, dispositivos,
configuración y actualizaciones. - Agentes: crear, configurar, asignar
herramientas/permisos, habilitar/deshabilitar, actualizar y consultar
actividad. - ORION no se deshabilita desde administración ordinaria. -
Modelos: registrar, configurar Ollama/proveedores, asignar modelos,
versiones/parámetros, modelos entrenados y recursos. - Permisos por
agente, usuario, proyecto, aplicación, dispositivo, archivo, operación y
riesgo; permisos temporales. - Auditoría: ID, responsable, fecha,
parámetro, valor anterior/nuevo, motivo, autorización y resultado. -
Autonomía C aprobada: ajustes rutinarios y optimizaciones autorizadas
autónomas; cambios importantes requieren aprobación; cambios críticos,
permisos y operaciones destructivas requieren autorización reforzada. -
ORION no cambia unilateralmente arquitectura o seguridad ni elimina
agentes fundamentales. - Pendiente: esquema, secretos, roles, validación
y reversión.

## MÓDULO 17 --- MULTI-USER & IDENTITY MANAGER

  -----------------------------------------------------------------------
  Versión           Cambios           Estado            Próximo trabajo
                    realizados                          
  ----------------- ----------------- ----------------- -----------------
  0.1               Modelo            Aprobado          Definir
                    multiusuario      funcionalmente    autenticación,
                    avanzado con                        aislamiento, MFA,
                    identidad,                          roles y sesiones.
                    sesiones,                           
                    memoria,                            
                    preferencias,                       
                    permisos y                          
                    proyectos.                          

  -----------------------------------------------------------------------

**Detalles** - Roles iniciales propuestos: administrador principal,
administrador, investigador, desarrollador, operador e invitado;
configurables. - Identidad: ID, perfil, credenciales, roles, permisos,
preferencias, sesiones, dispositivos y proyectos. -
Memoria/conversaciones privadas no se comparten automáticamente. -
Sesiones simultáneas; servicios centrales compartidos y contextos
aislados. - Proyectos colaborativos con permisos consultar, crear,
modificar, experimentar, aprobar y administrar participantes. -
Auditoría de cambios por usuario y agente. - Seguridad: hash de
contraseñas, autenticación reforzada, bloqueo, vencimiento/revocación de
sesiones y dispositivos. - Pendiente: autenticación local, MFA,
separación de datos y recuperación de cuenta.

## MÓDULO 18 --- SCHEDULER & AUTONOMOUS OPERATIONS

  -----------------------------------------------------------------------
  Versión           Cambios           Estado            Próximo trabajo
                    realizados                          
  ----------------- ----------------- ----------------- -----------------
  0.1               Autonomía         Aprobado          Definir
                    integral          funcionalmente    scheduler,
                    configurable para                   triggers,
                    planificar,                         persistencia,
                    programar,                          reintentos y
                    iniciar, detener,                   límites.
                    reorganizar y                       
                    reanudar tareas.                    

  -----------------------------------------------------------------------

**Detalles** - Modalidades: inmediata, programada, recurrente,
condicional y autónoma. - Estados: pendiente, programada, preparando,
ejecutando, en espera, suspendida, recuperándose, finalizada, fallida y
cancelada. - Tareas largas conservan estado, progreso, resultados
parciales y logs. - Recuperación desde último punto válido; estado no
confiable requiere reinicio o intervención. - Distinguir cerrar
interfaz, cerrar sesión, cerrar GIAR-ORION y apagar equipo. - Puede
seguir trabajando sin usuario conectado mientras servicios estén
activos. - Resource Manager controla concurrencia, prioridad,
suspensión/reanudación, CPU/GPU/RAM/VRAM y límites
térmicos/energéticos. - Autonomía C aprobada sujeta a objetivos,
permisos, recursos, seguridad y autorizaciones sensibles. - Pendiente:
motor, watchdog, persistencia, reintentos y apagado.

## MÓDULO 19 --- DECISION & REASONING ENGINE

| Versión | Cambios realizados | Estado | Próximo trabajo |
|---|---|---|---|
| 0.1 | Incorporación inicial del motor de razonamiento compartido, análisis de alternativas y resolución de conflictos entre agentes. | Aprobado conceptualmente | Completar definición funcional. |
| 0.2 | Especificación funcional ampliada: quince decisiones aprobadas sobre arquitectura, hipótesis, confiabilidad, desacuerdos, trazabilidad, aprendizaje, experimentación, métodos, suficiencia, revisión, recuperación, comparación de soluciones e intervención humana. | Aprobado funcionalmente en el alcance definido; implementación pendiente | Definir criterios medibles, algoritmos, contratos con módulos relacionados, métricas y pruebas. |

### Objetivo

Proporcionar un motor de razonamiento compartido por toda la plataforma. ORION administra las solicitudes, coordina análisis colaborativos y consolida decisiones de los agentes. El motor recomienda y fundamenta; la ejecución de acciones queda sujeta a permisos, políticas, recursos y autorizaciones.

### Decisiones funcionales aprobadas

**19.1 — Motor de razonamiento compartido**

El motor será un servicio común de GIAR-ORION. ORION administra las solicitudes, coordina análisis entre agentes y consolida resultados. Los agentes especializados aportan conocimiento de sus respectivos dominios. La recomendación del motor no equivale por sí misma a autorización para ejecutar acciones.

**19.2 — Arquitectura híbrida de razonamiento**

El razonamiento combinará componentes con responsabilidades diferenciadas:

- LLM: interpretación del problema, formulación de hipótesis y propuesta de soluciones.
- Algoritmos y métodos matemáticos: cálculos y análisis cuantitativos.
- Reglas lógicas: restricciones, consistencia y comprobaciones formales.
- Knowledge Manager: recuperación y consulta de evidencias documentales.
- Memory Manager: experiencias y procedimientos previos.
- Quality & Validation Engine: verificación de respuestas, métodos y resultados.
- ORION: coordinación, adjudicación y consolidación.

La salida del LLM no será considerada evidencia por sí misma.

**19.3 — Razonamiento adaptativo**

La profundidad del análisis se ajustará según complejidad, criticidad, especialidad, evidencias disponibles, precisión requerida y recursos. Se contemplan niveles directo, intermedio y profundo. Los límites de iteraciones, tiempo y recursos serán configurables.

**19.4 — Hipótesis competitivas y colaborativas**

El motor podrá generar varias hipótesis y contrastarlas. Para cada una deberá buscar evidencias favorables y contrarias, evaluar consistencia, identificar información faltante, convocar agentes especializados, detectar contradicciones y descartar hipótesis solo cuando existan fundamentos suficientes. Si la información no alcanza, conservará las hipótesis abiertas y podrá proponer experimentos discriminantes.

La coincidencia entre varios agentes no constituye por sí sola evidencia.

**19.5 — Evaluación híbrida de confiabilidad**

Cada hipótesis y conclusión podrá incluir:

- Puntuación cuantitativa basada en criterios definidos.
- Clasificación cualitativa: alta, media o baja confiabilidad.
- Evidencias favorables y contrarias.
- Incertidumbres e información faltante.
- Condiciones o nuevas evidencias que podrían modificar la evaluación.

Una puntuación generada por el LLM no se interpretará como probabilidad estadística. Las probabilidades requerirán métodos apropiados y calibrados.

**19.6 — Resolución de desacuerdos mediante evidencia y evaluación técnica**

Ante desacuerdos, cada agente presentará su conclusión y fundamentos. El motor identificará coincidencias y discrepancias, podrá solicitar argumentos o análisis adicionales y contrastará las posiciones mediante evidencias, reglas, cálculos, documentación o pruebas. ORION consolidará el resultado. Si no existe fundamento suficiente para resolver el desacuerdo, conservará las posiciones discrepantes e informará al usuario.

La cantidad de agentes que respalda una conclusión no determina su veracidad; la evidencia y la consistencia técnica tienen prioridad. La votación, si se utiliza, será complementaria y no decisoria.

**19.7 — Registro estructurado y configurable**

El proceso de razonamiento tendrá un registro auditable que incluya problema y objetivo, agentes participantes, hipótesis, evidencias a favor y en contra, métodos utilizados, desacuerdos, evaluaciones, conclusiones, confiabilidad, incertidumbres, información faltante, decisión final, fecha, duración y recursos.

El nivel de detalle será configurable: resumido, intermedio o completo. El registro deberá permitir reconstruir y auditar el proceso cuando sea posible, sin almacenar indiscriminadamente todo intercambio interno.

**19.8 — Aprendizaje controlado y evaluado**

El motor registrará decisiones y resultados, identificará errores, aciertos y patrones, y propondrá mejoras en sus métodos. Las mejoras se evaluarán mediante pruebas comparativas y métricas. Solo se incorporarán si cumplen los criterios de calidad establecidos. Se conservarán versiones anteriores y capacidad de reversión.

Integración: Memory Manager conserva experiencias; Learning & Adaptation Engine administra el ciclo de aprendizaje; Quality & Validation Engine verifica las mejoras. El motor no modificará autónomamente sus criterios sin evaluación y control.

**19.9 — Ejecución autónoma de pruebas con límites y permisos**

El motor podrá diseñar y ejecutar experimentos para comprobar hipótesis en entornos autorizados, incluidos simuladores integrados. Deberá respetar límites de tiempo, recursos y cantidad de experimentos; registrar parámetros, condiciones, procedimientos y resultados; y proteger archivos originales y configuraciones aprobadas.

La autorización para simulación no habilita control de hardware físico. El control real requiere permisos específicos y controles reforzados. Las acciones sensibles requieren aprobación. Los resultados deberán contrastarse con las hipótesis iniciales.

Integración: Project & Workflow Manager, API & Integration Engine, Scheduler & Autonomous Operations, Quality & Validation Engine y Data & Experiment Manager.

**19.10 — Selección adaptativa y combinada de métodos**

El motor analizará el problema y seleccionará uno o varios métodos adecuados. Podrá combinarlos y cambiar de estrategia si los resultados son insuficientes. Registrará qué métodos utilizó y por qué. La selección considerará tipo y complejidad del problema, especialidad, criticidad, evidencias, precisión requerida y recursos disponibles.

Entre los métodos posibles se encuentran razonamiento lógico, análisis matemático, diagnóstico causal, generación y contraste de hipótesis, simulación, análisis estadístico e investigación documental. Esta lista describe capacidades, no una selección tecnológica definitiva.

**19.11 — Criterios adaptativos de suficiencia de información**

El motor definirá qué información necesita según el problema y evaluará calidad, cantidad y confiabilidad de evidencias, contradicciones, criticidad y precisión requerida. Determinará si necesita investigar, consultar agentes o ejecutar experimentos. Podrá declarar insuficiencia de información y deberá exponer limitaciones e incertidumbres.

No confundirá la capacidad de generar una respuesta con disponer de evidencia suficiente para fundamentarla.

**19.12 — Revisión crítica independiente y multicapa**

Antes de presentar una conclusión como fundamentada, se revisará su coherencia con el problema, el respaldo de evidencias, la validez lógica, los cálculos cuando corresponda y el alcance de las afirmaciones. Podrá solicitar revisión de agentes especializados y devolver el análisis para corrección.

La revisión deberá distinguir, como mínimo, errores de recuperación RAG, extracción documental, generación LLM, razonamiento, cálculos, verificación de evidencias y adjudicación entre agentes. Una respuesta bien redactada no equivale a una respuesta técnicamente correcta.

**19.13 — Recuperación inteligente ante errores**

Ante un error, el motor identificará su origen y alcance, analizará qué etapas y resultados quedaron afectados, conservará los resultados todavía válidos y repetirá únicamente las etapas comprometidas. Podrá convocar agentes, verificará la corrección y registrará causa y solución. Si no puede resolverlo, informará al usuario y no presentará el resultado como validado.

No deberá descartar todo el análisis por un error localizado ni conservar resultados cuya validez dependa de una etapa defectuosa.

**19.14 — Evaluación comparativa multicriterio de soluciones**

El motor generará alternativas, comprobará su viabilidad y comparará ventajas, desventajas, limitaciones, precisión, complejidad, costo, tiempo, recursos, riesgos y compatibilidad con los requisitos del proyecto. Asignará ponderaciones según objetivos y prioridades, presentará una clasificación fundamentada y explicará la recomendación. Informará si ninguna alternativa satisface adecuadamente los requisitos.

La solución más conveniente no será necesariamente la más rápida ni la de mayor precisión aislada; dependerá de los objetivos y restricciones.

**19.15 — Intervención humana según riesgo, incertidumbre e impacto**

El motor solicitará intervención humana cuando existan consecuencias importantes, evidencias insuficientes o contradictorias, confiabilidad inadecuada, desacuerdos irresueltos, cambios importantes de arquitectura, impacto posible sobre hardware o sistemas externos, permisos insuficientes o riesgo para proyectos y datos.

En tareas rutinarias y de bajo riesgo podrá continuar dentro de sus permisos. La intervención dependerá del riesgo real de la decisión, no solamente de la dificultad del problema.

### Decisión pendiente: 19.16

Se planteó definir cómo debe explicar ORION el proceso que conduce a una conclusión. Se presentaron tres alternativas: explicación resumida, detallada o adaptativa/configurable (resumida, técnica, completa e interactiva). Se recomendó la alternativa C, pero **no fue aprobada expresamente**. Por lo tanto, permanece pendiente y no forma parte de las decisiones aprobadas del módulo.

### Integración y límites de responsabilidad

El motor se integra principalmente con:

- Módulo 3 — Task, Resource & Model Manager: disponibilidad y límites de recursos.
- Módulo 4 — Knowledge Manager: evidencias documentales y recuperación RAG.
- Módulo 5 — Memory Manager: experiencias y procedimientos.
- Módulo 8 — Project & Workflow Manager: objetivos, requisitos y línea base de proyectos.
- Módulo 11 — Web & Research Engine: investigación y fuentes externas.
- Módulo 12 — Learning & Adaptation Engine: evaluación y adopción de mejoras.
- Módulo 13 — API & Integration Engine: herramientas, simuladores y dispositivos.
- Módulo 18 — Scheduler & Autonomous Operations: ejecución y programación de tareas.
- Módulo 20 — Quality & Validation Engine: validación independiente.
- Módulo 22 — Data & Experiment Manager: datasets y resultados experimentales.

El Módulo 19 coordina el razonamiento y la toma de decisiones, pero no reemplaza a los módulos especializados. La recuperación documental sigue siendo responsabilidad de Knowledge/RAG; la generación, del LLM; la validación, del módulo 20; la ejecución, de los gestores y conectores correspondientes; y la autorización, de las políticas de ORION.

### Pendientes de ingeniería

- Definir métricas operativas y umbrales por especialidad.
- Precisar algoritmos y métodos de evaluación para confiabilidad y suficiencia.
- Definir formatos de hipótesis, evidencias, decisiones y registros.
- Establecer límites de iteraciones, tiempo y recursos por nivel de razonamiento.
- Definir contratos e interfaces con los módulos relacionados.
- Diseñar pruebas de calidad, reproducibilidad y calibración.
- Resolver la decisión 19.16.

## MÓDULO 20 --- QUALITY & VALIDATION ENGINE

  ------------------------------------------------------------------------
  Versión           Cambios           Estado             Próximo trabajo
                    realizados                           
  ----------------- ----------------- ------------------ -----------------
  0.1               Aceptada          Aprobado           Definir
                    incorporación     conceptualmente;   criterios,
                    para validar      detalle pendiente  métricas, pruebas
                    respuestas,                          y umbrales.
                    código,                              
                    experimentos,                        
                    investigaciones e                    
                    informes.                            

  ------------------------------------------------------------------------

**Alcance propuesto** - Evaluar respuestas. - Validar código. - Ejecutar
pruebas. - Comprobar resultados experimentales. - Evaluar
investigaciones e informes. - Detectar inconsistencias. - Comparar
versiones. - Calidad lingüística no equivale a validez técnica.

## MÓDULO 21 --- KNOWLEDGE GRAPH ENGINE

  ------------------------------------------------------------------------
  Versión           Cambios           Estado             Próximo trabajo
                    realizados                           
  ----------------- ----------------- ------------------ -----------------
  0.1               Aceptada          Aprobado           Definir
                    incorporación de  conceptualmente;   ontología, nodos,
                    relaciones        detalle pendiente  relaciones,
                    explícitas entre                     almacenamiento y
                    conceptos,                           consultas.
                    documentos,                          
                    proyectos,                           
                    agentes,                             
                    experimentos y                       
                    resultados.                          

  ------------------------------------------------------------------------

**Alcance propuesto** - Entidades: conceptos, documentos,
investigaciones, experimentos, proyectos, agentes, modelos,
procedimientos, resultados y conclusiones. - Complementa RAG mediante
relaciones explícitas; no lo reemplaza. - Pendiente: ontología, base de
datos, procedencia, contradicciones y evaluación.

## MÓDULO 22 --- DATA & EXPERIMENT MANAGER

  --------------------------------------------------------------------------
  Versión           Cambios           Estado             Próximo trabajo
                    realizados                           
  ----------------- ----------------- ------------------ -------------------
  0.1               Aceptada          Aprobado           Definir catálogo,
                    incorporación     conceptualmente;   esquemas,
                    para datasets,    detalle pendiente  versionado, linaje
                    datos                                y reproducibilidad.
                    experimentales,                      
                    entrenamiento y                      
                    resultados.                          

  --------------------------------------------------------------------------

**Alcance propuesto** - Administrar datasets y preparar datos. -
Versionar conjuntos. - Registrar experimentos, variables y parámetros. -
Almacenar/comparar resultados. - Gestionar entrenamiento, validación y
prueba. - Evaluar reproducibilidad. - Pendiente: formatos, metadatos,
almacenamiento, privacidad y retención.

## MÓDULO 23 --- PLUGIN & EXTENSION MANAGER

  ------------------------------------------------------------------------
  Versión           Cambios           Estado             Próximo trabajo
                    realizados                           
  ----------------- ----------------- ------------------ -----------------
  0.1               Aceptada          Aprobado           Definir API,
                    incorporación     conceptualmente;   manifiesto, ciclo
                    para              detalle pendiente  de vida,
                    herramientas,                        aislamiento y
                    conectores y                         firma.
                    extensiones de                       
                    terceros o                           
                    desarrolladas por                    
                    agentes.                             

  ------------------------------------------------------------------------

**Alcance propuesto** - Incorporar, instalar, versionar, validar,
habilitar/deshabilitar extensiones. - Controlar compatibilidad,
dependencias y permisos. - Extensiones aisladas; no modificar libremente
el núcleo. - Pendiente: formato, sandbox, firma, actualización, rollback
y repositorio offline.

## MÓDULO 24 --- DIAGNOSTICS & SELF-MONITORING

  -------------------------------------------------------------------------
  Versión           Cambios           Estado             Próximo trabajo
                    realizados                           
  ----------------- ----------------- ------------------ ------------------
  0.1               Aceptada          Aprobado           Definir métricas,
                    incorporación     conceptualmente;   health checks,
                    para salud de     detalle pendiente  telemetría y
                    plataforma,                          límites de
                    fallos,                              auto-reparación.
                    degradaciones y                      
                    diagnóstico.                         

  -------------------------------------------------------------------------

**Alcance propuesto** - Supervisar módulos. - Detectar
errores/degradaciones. - Controlar recursos. - Detectar fallos de
comunicación. - Analizar logs. - Detectar conflictos. - Proponer
soluciones y verificar correcciones. - Diagnóstico autónomo permitido;
cambios críticos requieren autorización. - Pendiente: métricas,
umbrales, trazas, aislamiento y auto-reparación.

# 3. Políticas transversales

## Autonomía y permisos

Los permisos se podrán definir por agente, usuario, proyecto,
aplicación, conector, dispositivo, formato, operación, riesgo y
duración. Niveles usados conceptualmente: automático, supervisado,
requiere autorización y prohibido. La semántica común se unificará en
arquitectura técnica.

## Autorización móvil

-   Opcional para uso normal.
-   Wi-Fi local; sin cloud.
-   El móvil aprueba solicitudes concretas, no tiene administración
    general.
-   Solicitud identificada, vencimiento, un solo uso y protección contra
    replay.
-   Comunicación cifrada, dispositivo vinculado y auditoría.
-   Si se pierde conexión, no se ejecuta una operación que exige
    confirmación móvil.
-   Una autorización vencida no se ejecuta al reconectar.

## Autenticación administrativa

La clave administrativa no se almacena en texto plano ni en
código/configuración. Se propuso hash Argon2id con sal, límite de
intentos y bloqueo. No usar cifrado reversible para almacenar la clave.

## RESET

1.  Reiniciar sesión: limpiar conversaciones/contexto operativo.
2.  Reiniciar plataforma: reiniciar agentes/servicios y estados
    operativos, conservando bibliotecas/config/logs.
3.  Restablecimiento de fábrica: valores iniciales y eliminación de
    personalizaciones con autorización. No borrar documentos/bibliotecas
    sin autorización expresa.

Antes de RESET: gestionar tareas, informar pérdidas, backup,
confirmación, ejecución y verificación.

## Sesiones y recuperación

Al iniciar, preguntar continuar sesión anterior o comenzar nueva. Al
continuar, restaurar, verificar integridad y recuperar tareas. Reanudar
desde punto válido si confiable; reiniciar si corrupto/no confiable;
consultar si faltan datos o autorización. Nunca marcar una tarea
interrumpida como finalizada.

## Evidencias

Separar dato verificado, resultado experimental, conclusión
fundamentada, hipótesis, inferencia del modelo e información no
verificada.

## Archivos originales

Lectura no modifica; edición crea copia/versión; reemplazo/eliminación
sujetos a permisos y autorización; versiones aprobadas protegidas.

## Diagnóstico de problemas

Distinguir errores de recuperación RAG, extracción documental,
generación LLM, verificación NLI/evidencia, adjudicación/decisión,
herramienta/conector, planificación/ejecución e infraestructura. No
modificar arquitectura antes de medir.

# 4. Estructura documental propuesta

La estructura siguiente es una propuesta lógica; no se afirma que ya
esté creada en el equipo.

``` text
GIAR-ORION/
├── Agents/
│   ├── ORION/{Core,Configuration,Memory,Knowledge,Tools,Logs}/
│   ├── ORION-ROBOTICS/
│   ├── ORION-SOFTWARE/
│   ├── ORION-SECURITY/
│   ├── ORION-LANGUAGES/
│   └── ORION-MARKETING/
├── Interface/{UI,Avatars}/
├── LLM/{Models,Configuration,Services}/
├── Projects/
├── Documents/
│   ├── INDEX.md
│   ├── 00_Governance/
│   ├── 01_Functional_Specification/
│   ├── 02_Work_Log/
│   ├── 03_Architecture/
│   ├── 04_Requirements/
│   ├── 05_Design/
│   ├── 06_Implementation/
│   ├── 07_Testing/
│   ├── 08_Changes/
│   └── 09_Reports/
├── Data/
├── Backups/
├── Logs/
└── Tools/
```

**Ubicación de los dos documentos maestros:** -
`GIAR-ORION/Documents/01_Functional_Specification/GIAR-ORION_Especificacion_Funcional_Maestra.md` -
`GIAR-ORION/Documents/02_Work_Log/GIAR-ORION_Bitacora_de_Trabajo.md`

Son documentos de todo el proyecto, por eso van en `Documents/`, no
dentro de un agente.

# 5. Convención documental

Identificadores: - DOC: documento general. - REQ: requerimiento. - DES:
diseño. - IMP: implementación. - TEST: prueba. - CHANGE: cambio.

Estados: - DRAFT. - REVIEW. - APPROVED. - IN_PROGRESS. - TESTING. -
COMPLETED. - BLOCKED.

Al comienzo de cada módulo se mantiene tabla de versiones con versión,
fecha, cambios, estado y próximo trabajo. Una aprobación conceptual no
cambia el estado a implementado.

# 6. Pendientes explícitos

1.  Módulo 9: falta aprobar modelo de aprobación de informes. Se
    recomendó opción híbrida C, pero no fue aceptada expresamente.
2.  Módulo 6: perfiles Normal/Alto/Crítico propuestos, no formalizados.
3.  Módulo 19: quince decisiones funcionales aprobadas; queda pendiente
    la decisión 19.16 y el detalle de ingeniería. Módulos 20--24:
    incorporación aceptada; falta especificación funcional detallada.
4.  Tecnologías nombradas: candidatas, no selección final, salvo que se
    indique expresamente.
5.  Estructura de carpetas: propuesta, no confirmada como creada.
6.  No hay módulos que deban considerarse implementados por su
    aprobación conceptual.

# 7. Próxima etapa

Completar la decisión pendiente 19.16 y continuar las especificaciones
funcionales de los módulos 20 Quality & Validation, 21 Knowledge Graph,
22 Data & Experiment, 23 Plugin & Extension y 24 Diagnostics &
Self-Monitoring.

Después realizar auditoría integral de los 24 módulos:
responsabilidades, duplicaciones, dependencias, interfaces, servicios
compartidos, conflictos, riesgos y pendientes. Luego arquitectura
técnica, contratos, estructura real, plan de implementación y pruebas
incrementales.

**Fin --- Especificación funcional maestra v0.2.**
