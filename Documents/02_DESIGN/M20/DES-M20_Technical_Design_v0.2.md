# GIAR-ORION — Technical Design

## DES-M20 — Technical Design

**Código:** DES-M20  
**Versión:** 0.2  
**Fecha:** 11/11/2026  
**Estado:** Borrador técnico integrado para revisión  
**Documento funcional de referencia:** REG-001 — GIAR-ORION, Especificación Funcional Maestra v0.6  
**Alcance de esta versión:** DT-01, DT-02, DT-03, DT-04 y DT-05  
**Ubicación prevista en el repositorio:** `GIAR-ORION/02_DESIGN/M20/`

> **Nota de estado:** este documento consolida decisiones y propuestas de diseño técnico. Las decisiones ARC-001 a ARC-006 indicadas como aprobadas fueron aceptadas expresamente. La aprobación de una decisión o de una especificación funcional no significa que exista una implementación ni que se hayan superado pruebas.

------------------------------------------------------------------------

# Control documental

## Historial de versiones

| Versión | Fecha      | Cambios                                                                                                                                         | Estado                                   |
|:--------|:-----------|:------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------|
| 0.1     | 11/11/2026 | Primera consolidación del diseño técnico: DT-01 a DT-04; incorporación de ARC-001 a ARC-006 y de los criterios aprobados durante la definición. | Borrador técnico integrado para revisión |
| 0.2     | 11/11/2026 | Versión acumulativa: conserva íntegramente DT-01 a DT-04 de v0.1 e incorpora DT-05 — API técnica de Model Manager. Actualiza metadatos, referencias y secuencia de trabajo. | Borrador técnico integrado para revisión |

## Convenciones de estado

- **APROBADA:** decisión aceptada expresamente.
- **PROPUESTA:** solución planteada que todavía requiere aprobación.
- **PENDIENTE:** definición técnica que debe resolverse.
- **BORRADOR:** contenido sujeto a revisión.
- **NO IMPLEMENTADO:** no debe interpretarse como funcionalidad existente.
- **NO PROBADO:** no existen resultados de pruebas que permitan afirmar conformidad.

## Documentos y decisiones de referencia

- `REG-001-GIAR-ORION_Especificacion_Funcional_Maestra_v0.6.md`.
- ORION CORE — especificación funcional, versión 0.1, incorporada en REG-001.
- M20 — Quality & Validation Engine, especificación funcional, versión 0.2, incorporada en REG-001.
- Decisiones arquitectónicas ARC-001 a ARC-006, registradas en este documento.

## Relación entre diseño funcional y diseño técnico

REG-001 define el comportamiento funcional aprobado. Este documento desarrolla propuestas de arquitectura y contratos técnicos para permitir su implementación.

Los contratos funcionales `C20-001` a `C20-012` y `C20-T01` a `C20-T04` pertenecen a M20. No son API, esquemas JSON ni contratos técnicos de ORION CORE. Su formalización técnica corresponde al desarrollo de DT-11 y no debe confundirse con los contratos generales de este documento.

------------------------------------------------------------------------

# Registro de decisiones arquitectónicas

| Código  | Decisión                                                                                                                     | Estado   |
|:--------|:-----------------------------------------------------------------------------------------------------------------------------|:---------|
| ARC-001 | Simplicidad arquitectónica.                                                                                                  | APROBADA |
| ARC-002 | ORION CORE como aplicación modular inicial; agentes ejecutables como procesos independientes cuando se justifique.           | APROBADA |
| ARC-003 | La comunicación entre agentes especializados pasará inicialmente por el Message Broker de ORION CORE.                        | APROBADA |
| ARC-004 | El Broker comenzará con colas en memoria y persistirá selectivamente los mensajes y operaciones que requieran recuperación.  | APROBADA |
| ARC-005 | JSON será el formato común de intercambio de mensajes.                                                                       | APROBADA |
| ARC-006 | Todos los agentes especializados implementarán un contrato común mínimo, manteniendo libertad sobre su arquitectura interna. | APROBADA |

## ARC-001 — Simplicidad arquitectónica

**Estado: APROBADA**

ORION CORE deberá adoptar la arquitectura técnicamente más sencilla que permita satisfacer los requisitos funcionales, de seguridad, disponibilidad, rendimiento y escalabilidad. Toda incorporación de componentes, servicios, procesos o tecnologías adicionales deberá justificarse mediante una necesidad verificable. Se priorizará la modularidad y la posibilidad de evolución progresiva, evitando complejidad prematura.

**Consecuencias:** - No incorporar microservicios, servidores externos o infraestructura adicional por anticipado. - Evitar componentes que dupliquen responsabilidades existentes. - Justificar las tecnologías y procesos independientes por requisitos verificables. - Medir antes de optimizar o distribuir componentes.

## ARC-002 — Modelo inicial de ejecución

**Estado: APROBADA**

ORION CORE se implementará inicialmente como una aplicación modular, con sus componentes separados lógica y funcionalmente. Los agentes especializados podrán ejecutarse como procesos independientes cuando sus necesidades de aislamiento, disponibilidad, recursos o escalabilidad lo justifiquen.

**Consecuencias:** - La separación lógica de componentes no exige separarlos en procesos. - No todos los agentes deben ejecutarse desde el inicio como procesos independientes. - La arquitectura conservará la posibilidad de distribuir agentes progresivamente.

## ARC-003 — Comunicación inicial entre agentes

**Estado: APROBADA**

Inicialmente, la comunicación entre agentes especializados también pasará por el Message Broker de ORION CORE para mantener trazabilidad y control centralizados.

**Consecuencias:** - Se evita establecer canales punto a punto independientes como mecanismo predeterminado. - ORION CORE puede aplicar las políticas de identidad, permisos y trazabilidad. - Una modalidad directa futura requerirá justificación y definición de controles equivalentes.

## ARC-004 — Colas y persistencia del Broker

**Estado: APROBADA**

El Broker comenzará con colas en memoria y persistirá únicamente los mensajes y operaciones que requieran recuperación.

**Consecuencias:** - No se incorpora inicialmente una infraestructura externa de colas. - La persistencia será selectiva y responderá a requisitos de continuidad, recuperación o auditoría. - La pérdida de mensajes en memoria ante una interrupción deberá contemplarse en el análisis de riesgos y en las reglas de reintento. - Los mensajes críticos deberán persistirse antes de depender de ellos para una operación recuperable.

## ARC-005 — Formato común de mensajes

**Estado: APROBADA**

GIAR-ORION utilizará JSON como formato común de intercambio de mensajes entre ORION CORE, los agentes especializados y los módulos del sistema.

**Alcance:** - JSON define la representación de los mensajes. - JSON no determina el protocolo, el transporte ni la topología de red. - Las estructuras se validarán mediante esquemas técnicos que se definirán posteriormente. - La elección del transporte queda pendiente.

## ARC-006 — Contrato común de agentes

**Estado: APROBADA**

Todos los agentes especializados deberán implementar un contrato común mínimo de identidad, registro, capacidades, comunicación, estados y permisos. Sus arquitecturas internas, modelos, herramientas y mecanismos de memoria podrán ser diferentes.

**Consecuencias:** - Un agente de robótica, uno de investigación y uno de visión artificial podrán utilizar modelos y herramientas diferentes. - Todos deberán cumplir las interfaces mínimas de integración. - ORION CORE no deberá depender de la implementación interna de cada agente. - La conformidad con el contrato común será verificable mediante pruebas.

------------------------------------------------------------------------

# DT-01 — Arquitectura técnica general de ORION CORE

**Estado:** Borrador para revisión  
**Versión:** 0.1

## 1. Objetivo

Definir la arquitectura técnica general de ORION CORE, estableciendo sus componentes, responsabilidades, relaciones internas y mecanismos de interacción con agentes especializados y módulos de GIAR-ORION.

El diseño proporciona una base técnica sencilla, modular, extensible y multiplataforma, evitando incorporar complejidad que no esté justificada por requisitos verificables.

## 2. Alcance

Este documento define: - La arquitectura lógica de ORION CORE. - La organización y responsabilidad de sus componentes. - Las relaciones entre ORION CORE y los agentes especializados. - La comunicación con Model Manager. - La gestión de tareas, estados y eventos. - Los principios generales de seguridad, persistencia y recuperación. - Los criterios generales de despliegue.

No define todavía los esquemas detallados de mensajes, las API definitivas, la implementación interna del Message Broker ni la selección de tecnologías.

## 3. Principios técnicos

1.  **Modularidad:** responsabilidades claramente delimitadas.
2.  **Bajo acoplamiento:** interacción mediante interfaces definidas.
3.  **Responsabilidad única:** evitar duplicar funciones.
4.  **Servicios compartidos:** centralizar servicios comunes cuando resulte conveniente.
5.  **Trazabilidad:** identificar y reconstruir operaciones relevantes.
6.  **Seguridad:** aplicar permisos y autorizaciones antes de operaciones protegidas.
7.  **Resiliencia:** gestionar fallos sin comprometer innecesariamente el funcionamiento general.
8.  **Evolución progresiva:** incorporar capacidades sin rediseñar toda la plataforma.
9.  **Multiplataforma:** contemplar Windows 11 y Ubuntu.
10. **Funcionamiento local:** la operación básica no dependerá obligatoriamente de servicios externos.
11. **Escalabilidad gradual:** conservar la posibilidad de utilizar varias GPU y equipos en red local, sin imponer una arquitectura distribuida desde el inicio.
12. **Medición previa:** justificar cambios de arquitectura con requisitos, métricas o pruebas.

## 4. Modelo arquitectónico

Se adopta una arquitectura modular para ORION CORE. Los componentes estarán separados lógica y funcionalmente, aunque inicialmente podrán ejecutarse dentro de una misma aplicación y proceso.

La separación de componentes en procesos o servicios independientes se realizará cuando exista una necesidad demostrable de aislamiento, disponibilidad, rendimiento, recursos o escalabilidad.

### 4.1. Bloques lógicos

**A. Coordinación central** - Inicialización y cierre. - Registro e identificación de agentes. - Recepción y distribución de solicitudes. - Coordinación de tareas. - Gestión de estados. - Supervisión general.

**B. Comunicación** - Recepción y emisión de mensajes. - Enrutamiento. - Gestión de solicitudes y respuestas. - Identificación y correlación de mensajes. - Gestión de errores de comunicación.

**C. Servicios compartidos** - Comunicación con Model Manager. - Consulta de disponibilidad de modelos. - Solicitud de inferencias. - Gestión de recursos compartidos mediante los módulos responsables.

**D. Seguridad y control** - Identificación de agentes. - Verificación de permisos. - Autorización de operaciones. - Registro de operaciones sensibles.

**E. Persistencia y recuperación** - Registro de eventos. - Persistencia de estados. - Recuperación de sesiones y tareas. - Verificación de integridad.

Estos bloques son agrupaciones lógicas de responsabilidades. No implican crear cinco servicios independientes ni agregar componentes funcionales a los diez ya aprobados.

## 5. Componentes funcionales de ORION CORE

Se conservan los diez componentes definidos en REG-001:

| Código | Componente                              | Responsabilidad principal                                                                   |
|:-------|:----------------------------------------|:--------------------------------------------------------------------------------------------|
| OC-01  | Inicialización y cierre                 | Gestionar el ciclo de vida de ORION CORE y el orden de inicio y cierre.                     |
| OC-02  | Registro e identificación de agentes    | Registrar agentes y administrar sus identidades e información operativa.                    |
| OC-03  | Recepción y distribución de solicitudes | Recibir solicitudes y encaminarlas según especialidad, disponibilidad y condiciones.        |
| OC-04  | Coordinación de tareas                  | Organizar y supervisar tareas, dependencias y colaboración entre agentes.                   |
| OC-05  | Comunicación con Model Manager          | Acceder a los servicios centralizados de modelos e inferencia mediante una interfaz común.  |
| OC-06  | Gestión jerárquica de estados           | Administrar estados de plataforma, agentes y tareas de forma coherente y auditable.         |
| OC-07  | Registro de eventos y errores           | Registrar acontecimientos, incidencias y errores, preservando la auditoría crítica.         |
| OC-08  | Control de permisos                     | Verificar permisos y autorizaciones antes de operaciones protegidas.                        |
| OC-09  | Persistencia                            | Conservar la información necesaria para continuidad y recuperación, verificando integridad. |
| OC-10  | Interfaces con módulos futuros          | Proporcionar interfaces estables para integrar módulos presentes y futuros.                 |

Los bloques lógicos del apartado 4 no constituyen componentes adicionales. La división interna de cada componente se definirá durante el diseño detallado.

## 6. Relación con agentes especializados

ORION CORE coordina la actividad general de los agentes especializados. Cada agente tendrá identidad propia y declarará especialidad, capacidades, versión, herramientas y requisitos operativos.

La arquitectura permitirá: - Registrar agentes disponibles. - Consultar capacidades y estados. - Asignar tareas. - Supervisar la ejecución. - Recibir resultados y errores. - Controlar permisos. - Registrar operaciones relevantes. - Suspender, reanudar o finalizar agentes y tareas según las políticas aplicables.

Los agentes podrán colaborar entre sí. Inicialmente, sus mensajes pasarán por el Message Broker de ORION CORE conforme a ARC-003. ORION conservará autoridad sobre coordinación general, permisos y operaciones que requieran intervención central.

El contrato común de agente se desarrolla en DT-04.

## 7. Relación con Model Manager

ORION CORE no administrará directamente la infraestructura interna de los modelos de inteligencia artificial. La comunicación se realizará mediante Model Manager.

Model Manager será responsable de centralizar, según su especificación: - Registro y disponibilidad de modelos. - Administración de instancias de inferencia. - Asignación de recursos. - Recepción de solicitudes de inferencia. - Devolución de resultados. - Información de disponibilidad y errores.

Se evitará cargar múltiples instancias del mismo modelo cuando puedan compartir un servicio de inferencia. Los agentes accederán a los modelos mediante la interfaz autorizada, sin administrar por separado instancias compartidas.

La API específica se desarrollará en DT-05.

## 8. Comunicación interna

Los componentes utilizarán interfaces desacopladas. El mecanismo de comunicación deberá permitir: - Comunicación entre componentes de ORION CORE. - Comunicación entre ORION CORE y agentes. - Comunicación entre agentes mediante el Broker. - Comunicación con Model Manager. - Comunicación con otros módulos.

Se admitirán modalidades síncronas y asíncronas según la naturaleza de cada operación. La tecnología de transporte no se selecciona en esta versión.

La especificación del Message Broker se desarrolla en DT-02; las estructuras comunes se desarrollan en DT-03.

## 9. Seguridad y permisos

La arquitectura deberá garantizar que: - Cada agente y componente tenga una identidad reconocible. - Las operaciones estén sujetas a permisos. - Las autorizaciones se verifiquen antes de ejecutar operaciones sensibles. - Los componentes no puedan otorgarse permisos a sí mismos. - Las operaciones críticas queden registradas. - Los errores de autorización se traten de manera controlada.

ORION CORE conserva la autoridad transversal sobre permisos y coordinación. La definición técnica detallada corresponde al DT-09.

## 10. Estados y eventos

ORION CORE administrará estados generales de plataforma y permitirá el seguimiento de estados de agentes y tareas. Los cambios relevantes deberán generar eventos registrables.

Se distinguirán, como mínimo: - Estado de plataforma. - Estado de componente o servicio. - Estado de agente. - Estado de tarea. - Estado de sesión.

Las transiciones específicas y sus reglas de consistencia se definirán en los contratos técnicos y en los diseños de los módulos correspondientes. Los estados funcionales propios de M20 no deben confundirse con los estados generales de ORION CORE.

## 11. Persistencia y recuperación

La arquitectura contemplará la conservación de: - Identidades y registros de agentes. - Configuraciones necesarias. - Estados de tareas y sesiones. - Eventos relevantes. - Registros de errores. - Información necesaria para recuperación.

La persistencia deberá permitir verificar integridad y detectar inconsistencias. La recuperación de información histórica no implica recuperar automáticamente permisos o autorizaciones anteriores.

El diseño detallado se desarrollará en DT-08. La persistencia selectiva de mensajes del Broker se rige además por ARC-004.

## 12. Despliegue

La arquitectura deberá poder ejecutarse en Windows 11 y Ubuntu, priorizando tecnologías multiplataforma y de código abierto.

El despliegue inicial será local y sencillo. Se conservará la posibilidad de ejecutar agentes en procesos independientes y, posteriormente, en otros equipos de la red local, cuando los requisitos lo justifiquen.

El procedimiento de instalación y despliegue se desarrollará en DT-10.

## 13. Integración con M20

M20 — Quality & Validation Engine se integrará a GIAR-ORION como módulo especializado. ORION CORE proporcionará los servicios generales que M20 necesite: - Identidad y registro de agentes. - Comunicación. - Coordinación de tareas. - Acceso a Model Manager. - Gestión de permisos. - Estados y eventos. - Persistencia y trazabilidad.

M20 conserva sus responsabilidades específicas de validación, evaluación de calidad, decisión, corrección y gestión de evidencias.

Los contratos `C20-001` a `C20-012` y `C20-T01` a `C20-T04` pertenecen a las interacciones internas de M20. No son contratos generales de ORION CORE.

La especificación técnica de M20 corresponde a DT-11.

## 14. Aspectos pendientes

1.  Estructura interna de paquetes y módulos.
2.  Alcance técnico definitivo del Message Broker.
3.  Protocolo y transporte de comunicación.
4.  Esquemas técnicos de mensajes.
5.  Contrato técnico completo de agentes.
6.  Interfaces técnicas con Model Manager.
7.  Mecanismos de persistencia y almacenamiento.
8.  Autenticación y autorización.
9.  Estrategia multiproceso y distribuida.
10. Requisitos cuantitativos de rendimiento y escalabilidad.

## 15. Criterios de aceptación

DT-01 podrá considerarse consolidado cuando: - La arquitectura lógica esté definida. - Las responsabilidades de los componentes estén delimitadas. - Las relaciones entre ORION CORE, agentes y servicios compartidos estén establecidas. - Las decisiones arquitectónicas estén identificadas y justificadas. - Las dependencias con otros módulos estén documentadas. - No existan contradicciones con REG-001. - Los aspectos pendientes estén identificados y asignados.

------------------------------------------------------------------------

# DT-02 — Especificación técnica del Message Broker

**Estado:** Borrador para revisión  
**Versión:** 0.1

## 1. Objetivo

Definir el diseño técnico del mecanismo de comunicación de GIAR-ORION, responsable de transportar mensajes entre ORION CORE, agentes especializados y módulos del sistema.

El diseño prioriza simplicidad, trazabilidad, confiabilidad y evolución progresiva.

## 2. Alcance

Este documento establece: - Responsabilidades del Message Broker. - Modelo general de comunicación. - Tipos de mensajes. - Enrutamiento. - Identificación y correlación. - Comunicación síncrona y asíncrona. - Gestión de errores y reintentos. - Tratamiento de duplicados. - Seguridad y trazabilidad. - Criterios de persistencia y recuperación.

No selecciona todavía una tecnología concreta ni define la implementación definitiva.

## 3. Responsabilidades del Broker

El Message Broker deberá: 1. Recibir mensajes de componentes autorizados. 2. Identificar emisor y destinatario. 3. Validar la estructura básica del mensaje. 4. Determinar el destino indicado. 5. Entregar el mensaje. 6. Gestionar respuestas y confirmaciones cuando correspondan. 7. Controlar errores de comunicación. 8. Facilitar trazabilidad. 9. Aplicar políticas de reintentos. 10. Permitir detectar mensajes duplicados cuando corresponda.

El Broker no será responsable de: - Decidir qué agente debe resolver una tarea. - Ejecutar inferencias. - Validar la calidad del contenido de una respuesta. - Conceder permisos. - Administrar memoria de agentes. - Resolver conflictos funcionales entre agentes.

Estas responsabilidades corresponden a otros componentes.

## 4. Modelo arquitectónico

### 4.1. Implementación inicial

El Message Broker será inicialmente un componente lógico integrado a ORION CORE. No se requiere de inicio un servidor independiente, clúster de mensajería, infraestructura distribuida ni base de datos exclusiva para mensajes.

Su interfaz deberá permitir una eventual separación en otro proceso sin modificar innecesariamente los contratos de comunicación.

### 4.2. Modalidades de comunicación

- **Interna:** entre componentes de ORION CORE.
- **Con agentes:** entre ORION CORE y agentes especializados.
- **Entre agentes:** entre agentes especializados, pasando inicialmente por el Broker conforme a ARC-003.
- **Con módulos:** intercambio con Model Manager y otros módulos registrados, de acuerdo con sus interfaces.

## 5. Tipos de mensajes

Se contemplan inicialmente estas categorías:

| Tipo       | Descripción                                                   |
|:-----------|:--------------------------------------------------------------|
| `REQUEST`  | Solicitud de ejecución o información.                         |
| `RESPONSE` | Respuesta a una solicitud.                                    |
| `COMMAND`  | Instrucción dirigida a un componente o agente.                |
| `EVENT`    | Notificación de un acontecimiento.                            |
| `STATUS`   | Información sobre el estado de un componente, agente o tarea. |
| `ERROR`    | Notificación de un error.                                     |
| `CONTROL`  | Mensajes de coordinación y administración.                    |

La clasificación y los esquemas definitivos se establecerán en DT-03.

## 6. Identificación de mensajes

Todo mensaje deberá disponer de un identificador único. La estructura común prevista incluye: - `message_id`: identificador único del mensaje. - `correlation_id`: identificador que relaciona mensajes de una misma operación. - `sender_id`: identidad del emisor. - `recipient_id`: identidad del destinatario. - `message_type`: tipo de mensaje. - `timestamp`: fecha y hora de creación. - `version`: versión del contrato. - `payload`: contenido específico.

Los formatos definitivos y las reglas de validación se especificarán en DT-03.

## 7. Enrutamiento

El Broker determinará el destino utilizando la identificación del destinatario. Los destinos podrán ser: - Un componente de ORION CORE. - Un agente especializado. - Model Manager. - Otro módulo registrado. - Un conjunto de destinatarios autorizados, cuando corresponda.

El Broker no seleccionará agentes según especialidad, prioridad o disponibilidad. Esa decisión corresponde al componente de coordinación de tareas.

## 8. Comunicación síncrona y asíncrona

Se admitirán ambas modalidades.

### 8.1. Síncrona

Se utilizará cuando el emisor necesite una respuesta antes de continuar. Deberá contemplar tiempo máximo de espera, respuesta satisfactoria, respuesta de error y expiración.

### 8.2. Asíncrona

Se utilizará cuando el emisor pueda continuar sin esperar una respuesta inmediata. Deberá contemplar recepción, confirmación cuando corresponda, notificación de finalización y seguimiento mediante `correlation_id`.

La modalidad se elegirá según la operación. No se impondrá asincronía a todos los intercambios.

## 9. Colas y procesamiento

Conforme a ARC-004, la implementación inicial utilizará colas en memoria. El Broker deberá gestionar mensajes pendientes de entrega o procesamiento.

La persistencia se aplicará selectivamente a los mensajes y operaciones que requieran recuperación, continuidad o auditoría. La política deberá identificar qué mensajes son críticos y en qué momento deben persistirse.

No se incorpora inicialmente un sistema externo de colas. La pérdida de mensajes no persistidos ante una interrupción deberá tratarse mediante límites explícitos, confirmaciones, reintentos o reconstrucción de la operación, según corresponda.

## 10. Reintentos y errores

Se deberán contemplar: - Destinatario no disponible. - Tiempo de espera agotado. - Error de transmisión. - Mensaje inválido. - Destinatario inexistente. - Rechazo por falta de autorización. - Error durante el procesamiento.

Los reintentos serán controlados y limitados. No se repetirán automáticamente operaciones con efectos secundarios sin verificar previamente que la repetición sea segura.

Los errores definitivos deberán registrarse y notificarse al componente responsable.

## 11. Duplicación e idempotencia

El sistema contemplará que un mensaje pueda recibirse más de una vez.

- Cada mensaje tendrá un identificador único.
- Los componentes podrán reconocer mensajes ya procesados cuando corresponda.
- Las operaciones sensibles deberán protegerse contra ejecuciones duplicadas.
- Los reintentos no deberán producir efectos secundarios no deseados.

No se garantizará entrega exactamente una vez en todos los escenarios. Se priorizará entrega confiable, detección de duplicados e idempotencia en las operaciones que lo requieran.

## 12. Seguridad

El Broker deberá verificar la identidad del emisor mediante mecanismos definidos por Security Core, la existencia del destinatario, la estructura del mensaje y las reglas de comunicación aplicables.

La autorización de una operación protegida corresponderá al sistema de seguridad y permisos; el Broker no podrá conceder permisos ni sustituir esa autoridad.

Los mensajes no autorizados o inválidos deberán rechazarse y registrarse sin exponer información sensible.

## 13. Trazabilidad

Los mensajes deberán poder relacionarse con: - Solicitud original. - Tarea correspondiente. - Agente emisor y destinatario. - Respuesta. - Eventos y errores asociados.

Se utilizarán identificadores de mensaje y correlación para reconstruir el recorrido de una operación. El registro respetará políticas de privacidad, seguridad y retención.

## 14. Persistencia y recuperación

Se distinguirán: - Mensajes temporales en memoria. - Mensajes pendientes. - Mensajes procesados. - Mensajes fallidos. - Registros de auditoría asociados.

La persistencia no deberá duplicar innecesariamente el almacenamiento general de GIAR-ORION. Las reglas de persistencia y recuperación se coordinarán con DT-08.

## 15. Evolución

El Broker deberá permitir: 1. Comenzar integrado a ORION CORE. 2. Atender agentes ejecutados en procesos independientes. 3. Incorporar comunicación entre equipos de una red local. 4. Separarse en un servicio independiente si necesidades verificables lo justifican.

La evolución deberá preservar los contratos de comunicación siempre que sea técnicamente posible.

## 16. Aspectos pendientes

1.  Tecnología de comunicación.
2.  Protocolo de transporte.
3.  Implementación de colas.
4.  Esquemas técnicos definitivos.
5.  Política de reintentos y tiempos máximos.
6.  Política de persistencia selectiva.
7.  Comunicación entre equipos.
8.  Retención de mensajes.
9.  Pruebas de rendimiento, concurrencia y recuperación.

## 17. Criterios de aceptación

DT-02 podrá considerarse consolidado cuando las responsabilidades, modalidades, enrutamiento, identificación, correlación, tratamiento de errores, duplicados, seguridad y trazabilidad estén definidos y sean coherentes con ARC-001 a ARC-005, DT-01 y REG-001.

------------------------------------------------------------------------

# DT-03 — Contratos técnicos de ORION CORE

**Estado:** Borrador para revisión  
**Versión:** 0.1

## 1. Objetivo

Definir los contratos técnicos que regulan la comunicación y la interacción entre componentes de ORION CORE, agentes especializados, Model Manager y módulos del sistema.

Los contratos establecerán estructuras de datos, responsabilidades, condiciones de intercambio, respuestas y mecanismos de control para permitir que los componentes evolucionen sin perder compatibilidad.

## 2. Alcance

Se definen: - Convenciones generales de comunicación. - Estructura común de mensajes. - Contratos de solicitudes, respuestas, comandos y eventos. - Contratos de estados y errores. - Identidad, correlación y trazabilidad. - Permisos y autorización. - Comunicación con agentes y Model Manager. - Versionado y compatibilidad.

No se define la implementación interna de cada componente ni se selecciona una tecnología de transporte.

## 3. Principios

1.  Cada mensaje tendrá una estructura identificable.
2.  Los componentes conocerán solamente las interfaces necesarias.
3.  Los mensajes tendrán identificadores únicos.
4.  Los mensajes relacionados compartirán un identificador de correlación.
5.  Los errores utilizarán estructuras comunes.
6.  Los contratos tendrán versiones.
7.  Las operaciones sensibles requerirán autorización.
8.  Los cambios preservarán compatibilidad cuando sea posible.
9.  No se transmitirán datos innecesarios.
10. Los contratos serán independientes del transporte.

## 4. Formato común

Conforme a ARC-005, JSON será el formato común de representación e intercambio de mensajes. Esta decisión no determina si el transporte será local, HTTP, WebSocket, RPC u otro mecanismo; esa selección queda pendiente.

### 4.1. Campos comunes propuestos

| Campo            | Descripción                                | Obligatorio |
|:-----------------|:-------------------------------------------|:------------|
| `message_id`     | Identificador único del mensaje.           | Sí          |
| `correlation_id` | Identificador de la operación relacionada. | Sí          |
| `sender_id`      | Identidad declarada del emisor.            | Sí          |
| `recipient_id`   | Identidad del destinatario.                | Sí          |
| `message_type`   | Tipo de mensaje.                           | Sí          |
| `timestamp`      | Fecha y hora de creación.                  | Sí          |
| `version`        | Versión del contrato.                      | Sí          |
| `payload`        | Contenido específico del mensaje.          | Sí          |

La obligatoriedad y el formato definitivo de cada campo deberán verificarse al construir los esquemas JSON. Los mensajes de difusión o eventos sin respuesta deberán definir una regla explícita para `recipient_id` y `correlation_id`, evitando valores ambiguos.

### 4.2. Ejemplo conceptual

``` json
{
  "message_id": "msg-000001",
  "correlation_id": "task-000001",
  "sender_id": "orion_core",
  "recipient_id": "agent_research",
  "message_type": "REQUEST",
  "timestamp": "2026-11-11T15:00:00Z",
  "version": "1.0",
  "payload": {
    "operation": "research",
    "parameters": {}
  }
}
```

Este ejemplo ilustra la estructura, no constituye todavía un esquema normativo ni fija el formato definitivo de los identificadores o fechas.

## 5. Contrato de solicitudes (`REQUEST`)

Las solicitudes representan pedidos de ejecución o información dirigidos a un componente o agente. Deberán permitir identificar: - Operación solicitada. - Destinatario. - Contexto necesario. - Parámetros de ejecución. - Prioridad, cuando corresponda. - Tiempo máximo de espera, cuando corresponda.

La solicitud deberá poder relacionarse con su respuesta mediante `correlation_id`.

## 6. Contrato de respuestas (`RESPONSE`)

Las respuestas identificarán la solicitud original, emisor, resultado, datos devueltos, condición de finalización y errores u observaciones.

Se distinguirá entre: - Respuesta satisfactoria. - Respuesta satisfactoria con observaciones. - Respuesta fallida. - Respuesta incompleta. - Respuesta no disponible.

Una respuesta satisfactoria no implica que M20 haya validado el resultado.

## 7. Contrato de comandos (`COMMAND`)

Los comandos representan instrucciones dirigidas a un componente o agente. Ejemplos: iniciar, suspender, reanudar o cancelar una tarea; actualizar un estado; ejecutar una acción autorizada.

Los comandos deberán identificar la operación solicitada y verificar los permisos correspondientes antes de ejecutarse.

## 8. Contrato de eventos (`EVENT`)

Los eventos informarán que ocurrió una situación relevante, por ejemplo: - Agente registrado o disponible. - Agente desconectado. - Tarea iniciada o finalizada. - Error detectado. - Recurso no disponible. - Cambio de estado.

Los eventos no implican necesariamente una solicitud de respuesta.

## 9. Contrato de estados (`STATUS`)

Los componentes podrán informar su estado operativo, incluyendo identidad, estado actual, fecha de actualización, disponibilidad e información complementaria.

Se distinguirán los estados de plataforma, componentes, agentes, tareas, sesiones y servicios compartidos. Los estados específicos deberán respetar REG-001 y los documentos de cada módulo.

## 10. Contrato de errores (`ERROR`)

Se propone la siguiente estructura común:

| Campo            | Descripción                                            |
|:-----------------|:-------------------------------------------------------|
| `error_code`     | Código identificador del error.                        |
| `error_type`     | Categoría del error.                                   |
| `message`        | Descripción breve.                                     |
| `source_id`      | Componente que informa el error.                       |
| `correlation_id` | Operación relacionada.                                 |
| `timestamp`      | Fecha y hora.                                          |
| `recoverable`    | Indica si admite recuperación.                         |
| `details`        | Información técnica complementaria, sujeta a permisos. |

Categorías iniciales: - Comunicación. - Validación. - Autorización. - Ejecución. - Recursos. - Persistencia. - Error interno.

Los mensajes de error no deberán exponer información sensible. El catálogo definitivo de códigos queda pendiente.

## 11. Identidad y trazabilidad

Todo componente participante deberá disponer de una identidad reconocible. Los mensajes permitirán reconstruir quién inició una operación, qué componentes participaron, qué mensajes se intercambiaron, qué resultado se obtuvo y qué errores ocurrieron.

`message_id` identifica el mensaje y `correlation_id` relaciona los mensajes de una operación. La identidad declarada dentro del JSON no sustituye la autenticación del emisor.

## 12. Permisos y autorización

Los contratos deberán proporcionar información suficiente para identificar la operación y verificar si el emisor está autorizado.

Reglas: 1. La capacidad técnica no implica autorización. 2. Los permisos se verifican antes de operaciones protegidas. 3. Los agentes no pueden concederse permisos a sí mismos. 4. El Broker no reemplaza al sistema de seguridad. 5. Las operaciones sensibles deben quedar registradas.

La definición técnica detallada corresponde a DT-09.

## 13. Contrato con Model Manager

ORION CORE y los agentes autorizados accederán a modelos mediante Model Manager. El intercambio deberá contemplar: - Identidad del solicitante. - Identificación del modelo solicitado. - Tipo de operación. - Parámetros de inferencia. - Datos de entrada. - Resultado. - Errores. - Información de consumo y recursos, cuando esté disponible.

Model Manager administrará disponibilidad y ejecución de modelos. Los agentes no deberán administrar directamente instancias compartidas de inferencia. La API específica se desarrollará en DT-05.

## 14. Contratos transversales

Se mantienen los cuatro contratos transversales funcionales de ORION CORE:

| Código     | Contrato                     | Responsabilidad                            |
|:-----------|:-----------------------------|:-------------------------------------------|
| C-CORE-T01 | Identity & Traceability      | Identidad, correlación y trazabilidad.     |
| C-CORE-T02 | Permission & Authorization   | Verificación de permisos y autorizaciones. |
| C-CORE-T03 | State & Event Management     | Gestión de estados y eventos.              |
| C-CORE-T04 | Error & Exception Management | Gestión uniforme de errores y excepciones. |

Estos contratos son transversales; no representan componentes independientes. Sus esquemas técnicos deberán especificarse en el desarrollo posterior.

## 15. Versionado y compatibilidad

Se propone evaluar versionado semántico: - **MAJOR:** cambios incompatibles. - **MINOR:** incorporación compatible de funcionalidades. - **PATCH:** correcciones que no modifican la estructura contractual.

Esta convención es una propuesta técnica y queda pendiente de aprobación. Los componentes deberán validar compatibilidad antes de intercambiar información. Los cambios incompatibles deberán documentarse y contar con un procedimiento de transición.

## 16. Validación de contratos

Antes de procesar un mensaje, el receptor deberá verificar: 1. Presencia de campos obligatorios. 2. Tipo de mensaje reconocido. 3. Versión compatible. 4. Identidad autenticada del emisor. 5. Destinatario válido. 6. Estructura del contenido. 7. Permisos requeridos.

Los mensajes inválidos deberán rechazarse y generar un registro de error.

## 17. Aspectos pendientes

1.  Esquemas JSON definitivos.
2.  Tipos de datos y restricciones.
3.  Catálogo de códigos de error.
4.  Catálogo de operaciones y comandos.
5.  Estructuras específicas por tipo de mensaje.
6.  Mecanismos técnicos de autenticación.
7.  Formatos definitivos de fechas e identificadores.
8.  Herramientas de validación automática.
9.  Convención de versionado y compatibilidad.

## 18. Criterios de aceptación

DT-03 podrá considerarse consolidado cuando exista una estructura común de mensajes, estén definidos los tipos de intercambio, la correlación y trazabilidad, los errores tengan estructura común, los contratos transversales estén especificados y la comunicación con agentes y Model Manager sea coherente con DT-02, DT-04 y REG-001.

------------------------------------------------------------------------

# DT-04 — Contrato técnico de agente especializado

**Estado:** Borrador para revisión  
**Versión:** 0.1

## 1. Objetivo

Definir el contrato técnico que deberán cumplir los agentes especializados para integrarse a GIAR-ORION y operar bajo la coordinación de ORION CORE.

El contrato establece una estructura común de identidad, capacidades, comunicación, estados y permisos, permitiendo incorporar, actualizar o reemplazar agentes sin modificar innecesariamente la arquitectura general.

## 2. Alcance

Este documento define: - Identidad y registro. - Especialidad y capacidades. - Comunicación con ORION CORE y otros agentes. - Acceso a Model Manager. - Gestión de tareas. - Estados y ciclo de vida. - Permisos y seguridad. - Memoria, conocimiento y herramientas. - Registro de actividad, monitoreo y recuperación. - Ejecución, despliegue y versionado.

No define la arquitectura interna de cada agente ni obliga a utilizar un modelo de inteligencia artificial determinado.

## 3. Principios generales

1.  Cada agente tendrá identidad única dentro de GIAR-ORION.
2.  Declarará especialidad y capacidades.
3.  Informará su estado operativo.
4.  Recibirá tareas mediante mecanismos autorizados.
5.  Respetará las políticas de seguridad.
6.  Utilizará Model Manager para acceder a modelos compartidos.
7.  Registrará operaciones relevantes.
8.  Mantendrá delimitadas sus responsabilidades.
9.  Podrá actualizarse o reemplazarse respetando contratos.
10. No asumirá la coordinación general propia de ORION CORE.

## 4. Contrato común mínimo

Conforme a ARC-006, todos los agentes deberán implementar como mínimo:

| Área         | Obligación del agente                                        |
|:-------------|:-------------------------------------------------------------|
| Identidad    | Exponer un identificador estable y datos de identificación.  |
| Registro     | Poder registrarse y actualizar su información operativa.     |
| Capacidades  | Declarar especialidades, capacidades y limitaciones.         |
| Comunicación | Intercambiar mensajes compatibles con DT-02 y DT-03.         |
| Estados      | Informar estados operativos y cambios relevantes.            |
| Permisos     | Respetar permisos y autorizaciones aplicables.               |
| Tareas       | Aceptar, rechazar, ejecutar e informar resultados de tareas. |
| Errores      | Informar fallos mediante estructuras comunes.                |
| Trazabilidad | Relacionar actividad con mensajes y tareas.                  |
| Versionado   | Informar versión y compatibilidad contractual.               |

Este contrato mínimo no obliga a que los agentes compartan el mismo modelo, arquitectura interna, herramientas, memoria o tecnología de ejecución.

## 5. Identidad del agente

Cada agente tendrá una identidad única. La información inicial propuesta es:

| Campo               | Descripción                         |
|:--------------------|:------------------------------------|
| `agent_id`          | Identificador único y estable.      |
| `agent_name`        | Nombre del agente.                  |
| `agent_version`     | Versión de la implementación.       |
| `agent_type`        | Categoría o especialidad principal. |
| `description`       | Descripción de sus funciones.       |
| `registration_date` | Fecha de registro.                  |
| `status`            | Estado operativo.                   |

La actualización de versión no generará una nueva identidad, salvo que se trate de un agente distinto. El formato definitivo del registro se especificará mediante un esquema JSON.

## 6. Registro del agente

Todo agente deberá registrarse en ORION CORE antes de recibir tareas.

El registro permitirá: - Identificar al agente. - Conocer su especialidad y capacidades. - Consultar su versión. - Identificar herramientas disponibles. - Conocer requisitos de recursos. - Verificar compatibilidad. - Determinar permisos aplicables.

ORION CORE aceptará o rechazará el registro según las políticas vigentes. La declaración de capacidades no implica que esas capacidades estén autorizadas.

## 7. Especialidad y capacidades

Cada agente declarará las funciones que puede realizar. La descripción permitirá evaluar su adecuación a una tarea.

Ejemplos de especialidades: - Investigación científica y técnica. - Programación e ingeniería de software. - Aprendizaje por refuerzo. - Robótica. - Simulación. - Visión artificial. - Procesamiento de audio. - Análisis de datos. - Gestión documental. - Validación y verificación.

La lista es ilustrativa y no cerrada. Cada capacidad deberá describir identificador, nombre, descripción, tipo de operación, requisitos y limitaciones conocidas.

## 8. Comunicación

Los agentes utilizarán JSON conforme a ARC-005 y las estructuras comunes de DT-03.

El modelo inicial de comunicación será: 1. Agente emisor → Message Broker. 2. Message Broker → ORION CORE o agente destinatario. 3. Agente destinatario → Message Broker. 4. Message Broker → agente solicitante.

La comunicación entre agentes pasará inicialmente por el Broker. Los mensajes deberán incluir identificadores y campos comunes. El agente no podrá eludir controles de identidad, permisos o trazabilidad.

## 9. Ejecución de tareas

Un agente deberá poder: 1. Recibir una solicitud. 2. Verificar que corresponde a sus capacidades. 3. Comprobar requisitos de ejecución. 4. Verificar permisos. 5. Aceptar o rechazar la tarea. 6. Ejecutar la operación. 7. Informar cambios de estado. 8. Devolver resultados. 9. Comunicar errores u observaciones.

El agente no podrá modificar unilateralmente la asignación de una tarea ni asumir atribuciones de ORION CORE. La suspensión, reanudación o cancelación se regirá por las políticas del sistema.

## 10. Acceso a Model Manager

Los agentes utilizarán Model Manager para acceder a modelos compartidos. Deberán poder solicitar un modelo, informar parámetros, enviar entradas, recibir resultados y comunicar errores o requisitos de recursos.

No deberán crear instancias redundantes de modelos compartidos cuando estén administrados por Model Manager.

Podrá admitirse la utilización de modelos locales propios cuando esté justificada y autorizada. La arquitectura y los modelos internos del agente no quedan uniformados por este contrato.

## 11. Memoria y conocimiento

Cada agente podrá disponer de mecanismos propios de: - Memoria de trabajo. - Memoria de sesión. - Memoria persistente. - Base de conocimiento. - Recuperación RAG.

La gestión será responsabilidad del agente o del módulo especializado correspondiente y respetará las políticas generales de GIAR-ORION.

La información compartida entre agentes estará sujeta a permisos. La memoria de un agente no se confundirá con el registro central de eventos ni con la persistencia de ORION CORE.

## 12. Herramientas

Cada agente podrá disponer de herramientas específicas, por ejemplo: - Intérpretes y entornos de ejecución. - Herramientas de análisis de código. - Simuladores. - Sistemas de visión artificial. - Sistemas de procesamiento de audio. - Herramientas de investigación. - Acceso a archivos y documentos.

El agente declarará las herramientas disponibles y sus requisitos. La disponibilidad de una herramienta no implica autorización para utilizarla. Las operaciones que modifiquen archivos, ejecuten código o interactúen con sistemas externos respetarán las políticas de seguridad.

## 13. Estados del agente

Se propone el siguiente conjunto inicial de estados operativos:

| Estado         | Descripción                       |
|:---------------|:----------------------------------|
| `REGISTERED`   | Agente registrado.                |
| `INITIALIZING` | Preparando su entorno.            |
| `READY`        | Disponible para recibir tareas.   |
| `BUSY`         | Ejecutando una tarea.             |
| `WAITING`      | Esperando recursos o información. |
| `SUSPENDED`    | Ejecución suspendida.             |
| `ERROR`        | Presenta un error operativo.      |
| `OFFLINE`      | No se encuentra disponible.       |
| `TERMINATING`  | Finalizando su ejecución.         |
| `TERMINATED`   | Ejecución finalizada.             |

Este catálogo es una propuesta técnica inicial. Las transiciones permitidas, estados adicionales y condiciones deberán validarse contra el modelo jerárquico de REG-001 y las pruebas de integración.

## 14. Ciclo de vida

El ciclo de vida general comprenderá: 1. Creación o incorporación. 2. Registro. 3. Validación de identidad y capacidades. 4. Inicialización. 5. Disponibilidad. 6. Asignación de tareas. 7. Ejecución. 8. Suspensión o recuperación, cuando corresponda. 9. Finalización. 10. Desactivación o eliminación del registro según las políticas aplicables.

ORION CORE deberá poder conocer la situación operativa del agente.

## 15. Permisos y seguridad

Los agentes operarán bajo permisos explícitamente autorizados. Se contemplan permisos relacionados con: - Comunicación. - Acceso a archivos. - Acceso a conocimiento. - Utilización de modelos. - Ejecución de herramientas. - Modificación de información. - Acceso a otros agentes. - Operaciones administrativas.

Reglas: 1. Un agente no podrá concederse permisos a sí mismo. 2. Las capacidades declaradas no implican autorización. 3. Los permisos se verificarán antes de operaciones protegidas. 4. Las operaciones sensibles quedarán registradas. 5. Se respetarán restricciones de acceso a información.

ORION CORE conservará la autoridad transversal sobre coordinación y permisos. La definición técnica detallada corresponde a DT-09.

## 16. Registro de actividad

Cada agente proporcionará información suficiente para reconstruir sus operaciones relevantes. Se registrarán, según corresponda: - Inicio y finalización de tareas. - Solicitudes recibidas. - Respuestas emitidas. - Cambios de estado. - Utilización de herramientas. - Solicitudes a Model Manager. - Errores. - Operaciones sensibles.

Los registros se relacionarán con identificadores de mensaje y tarea. Su detalle y retención respetarán las políticas del sistema.

## 17. Monitoreo y recuperación

ORION CORE deberá poder conocer la disponibilidad de los agentes. Se contemplan mecanismos para: - Consultar estados. - Detectar falta de respuesta. - Identificar errores e interrupciones. - Solicitar suspensión o finalización. - Recuperar tareas cuando corresponda. - Reasignar tareas a otros agentes si está permitido.

La recuperación deberá considerar si repetir una tarea es seguro y si sus efectos secundarios pueden evitarse. No se deberá declarar recuperada una operación sin verificar su estado.

## 18. Ejecución y despliegue

Los agentes podrán ejecutarse: - Dentro del mismo proceso de ORION CORE cuando resulte apropiado. - Como procesos independientes. - En otros equipos de la red local cuando la arquitectura y la seguridad lo permitan.

La modalidad dependerá de requisitos de recursos, aislamiento, disponibilidad y escalabilidad. No se exigirá que todos los agentes utilicen la misma tecnología o modelo.

## 19. Versionado y compatibilidad

Cada agente informará su versión. Los cambios deberán contemplar: - Compatibilidad con contratos vigentes. - Identificación de cambios incompatibles. - Actualización de capacidades declaradas. - Compatibilidad con versiones de GIAR-ORION. - Posibilidad de reemplazo o reversión.

Una actualización no modificará silenciosamente los contratos de comunicación. La convención técnica de versionado queda pendiente de consolidación en DT-03.

## 20. Aspectos pendientes

1.  Esquema JSON definitivo del registro.
2.  Esquema JSON de declaración de capacidades.
3.  Estructura de solicitudes y respuestas de tareas.
4.  Catálogo definitivo de estados y transiciones.
5.  Mecanismo de identificación y autenticación.
6.  Modelo detallado de permisos.
7.  Interfaz de monitoreo.
8.  Política de recuperación de tareas.
9.  Requisitos de compatibilidad entre versiones.
10. Pruebas de conformidad de agentes.

## 21. Criterios de aceptación

DT-04 podrá considerarse consolidado cuando: - La identidad de los agentes esté definida. - El registro tenga una estructura común. - Las capacidades puedan declararse y verificarse. - La comunicación respete DT-02 y DT-03. - La interacción con Model Manager esté definida. - Los estados y el ciclo de vida sean consistentes. - Los permisos estén delimitados. - Existan mecanismos de monitoreo y recuperación. - Se pueda incorporar un nuevo agente sin modificar innecesariamente ORION CORE. - No existan contradicciones con REG-001.

------------------------------------------------------------------------

# DT-05 — API técnica de Model Manager

## 1. Objetivo

Definir la interfaz técnica mediante la cual los agentes especializados y los componentes autorizados de ORION CORE solicitan servicios de inferencia, sin depender directamente del proveedor que ejecuta los modelos.

DT-05 desarrolla la responsabilidad de Model Manager definida en REG-001 y las referencias establecidas en DT-01 y DT-04. No define la implementación interna del proveedor ni selecciona una tecnología de inferencia definitiva.

## 2. Alcance

DT-05 comprende:

- La interfaz interna de acceso a modelos.
- La identificación lógica de modelos y su resolución hacia modelos físicos y proveedores.
- La administración lógica del catálogo de modelos, proveedores e instancias.
- La recepción y gestión de solicitudes de inferencia.
- Las modalidades síncrona y asíncrona.
- La interacción con Resource Manager para conocer o coordinar la disponibilidad de recursos.
- La devolución de resultados y la información operativa necesaria para su seguimiento.

No comprende la arquitectura interna de los modelos, su entrenamiento, la implementación específica de cada proveedor ni las políticas completas de planificación y cuotas de recursos.

## 3. Principios de diseño

1. **Independencia del proveedor:** los consumidores utilizarán una interfaz interna de GIAR-ORION y no dependerán directamente de Ollama ni de otro proveedor.
2. **Identificadores lógicos:** los consumidores solicitarán modelos mediante identificadores lógicos; Model Manager resolverá su correspondencia física.
3. **Gestión centralizada:** Model Manager coordinará el acceso a los servicios de inferencia y evitará duplicaciones innecesarias de instancias cuando un servicio compartido resulte adecuado.
4. **Separación de responsabilidades:** Model Manager gestionará el acceso a modelos; Resource Manager conservará la responsabilidad de gestión de recursos; ORION CORE conservará la autoridad transversal sobre identidad y permisos.
5. **Evolución progresiva:** la solución deberá respetar ARC-001 y ARC-002. Las responsabilidades descritas no implican procesos o servicios independientes.
6. **Modalidades de ejecución:** la API ofrecerá inferencia síncrona y asíncrona, sin imponer una modalidad única a todos los agentes.

## 4. Decisiones técnicas registradas

### DT05-DEC-001 — Independencia respecto del proveedor

**Estado: APROBADA**

Model Manager deberá proporcionar una interfaz interna independiente del proveedor de inferencia utilizado. Los agentes solicitarán modelos mediante identificadores lógicos, sin depender directamente de Ollama ni de la tecnología que ejecute el modelo. La resolución de cada solicitud corresponderá a Model Manager, que determinará el modelo físico, la versión, la configuración y el proveedor asociado.

### DT05-DEC-002 — Modalidades de inferencia síncrona y asíncrona

**Estado: APROBADA**

La API de Model Manager admitirá ambas modalidades:

- **Síncrona:** el consumidor solicita una inferencia y espera la devolución del resultado en la misma interacción. Es adecuada para consultas breves y respuestas que puedan resolverse dentro del tiempo de espera admitido.
- **Asíncrona:** el consumidor presenta una solicitud, recibe un identificador de solicitud y consulta u obtiene posteriormente el resultado. Es adecuada para procesamientos prolongados, multimodales o sometidos a cargas elevadas.

Ambas modalidades estarán disponibles. Ningún agente estará obligado a utilizar exclusivamente una de ellas.

## 5. Responsabilidades lógicas

Se identifican las siguientes responsabilidades funcionales. Esta separación es lógica y no determina que deban implementarse como módulos desplegables o procesos independientes.

| Responsabilidad | Función |
|:----------------|:--------|
| Model Registry | Mantener el catálogo de modelos y sus identificadores lógicos, junto con la información necesaria para su resolución. |
| Provider Manager | Registrar y administrar la información de los proveedores de inferencia y sus características de conexión. |
| Model Instance Manager | Conocer y administrar las instancias o servicios de modelos disponibles, su estado y su asociación con modelos físicos y proveedores. |
| Inference Gateway | Recibir solicitudes, resolver el modelo requerido, coordinar la ejecución y devolver resultados o información de seguimiento. |
| Resource Interface | Interactuar con Resource Manager para consultar o coordinar la disponibilidad de recursos necesaria para una inferencia. |

## 6. Identificación de modelos y servicios

El diseño distingue los siguientes conceptos:

- **Modelo lógico:** identificador estable utilizado por los agentes y consumidores de la API.
- **Modelo físico:** modelo concreto que ejecuta el proveedor, incluida su variante o versión.
- **Proveedor:** tecnología o servicio que proporciona la ejecución de inferencia.
- **Instancia:** servicio o instancia operativa concreta a través de la cual se atienden solicitudes.

Ejemplos ilustrativos —no constituyen nombres ni identificadores aprobados—:

| Concepto | Ejemplo |
|:---------|:--------|
| Modelo lógico | `orion.general` |
| Modelo físico | `qwen3:8b` |
| Proveedor | `ollama.local` |
| Instancia | `instance-001` |

La correspondencia entre identificadores lógicos y recursos físicos será responsabilidad de Model Manager. Los agentes no deberán inferir ni construir esa correspondencia por su cuenta.

## 7. Flujo general de una solicitud

El siguiente flujo representa una propuesta de funcionamiento de alto nivel:

1. Un agente o componente autorizado solicita una inferencia mediante la API.
2. ORION CORE aplica las verificaciones de identidad y permisos que correspondan.
3. Model Manager recibe la solicitud y determina la modalidad de ejecución.
4. Inference Gateway resuelve el identificador lógico solicitado.
5. Model Instance Manager identifica una instancia o servicio disponible compatible con la resolución.
6. Cuando sea necesario, Resource Interface consulta o coordina con Resource Manager la disponibilidad de recursos.
7. El proveedor asociado ejecuta la inferencia.
8. Model Manager devuelve el resultado directamente en modalidad síncrona o habilita su obtención posterior en modalidad asíncrona.
9. Se registran los datos operativos necesarios para la trazabilidad y el diagnóstico.

Este flujo no define todavía el protocolo de transporte, los esquemas definitivos de solicitud y respuesta ni una estrategia de planificación.

## 8. Modalidad síncrona

En modalidad síncrona, la operación comprende una solicitud y una respuesta dentro de una misma interacción lógica.

El consumidor deberá proporcionar la información requerida para identificar el modelo lógico y los datos de entrada de la inferencia. Model Manager resolverá el modelo y coordinará su ejecución. Si la operación finaliza dentro del tiempo admitido, devolverá el resultado; si no puede completarse, deberá comunicar la condición correspondiente de forma explícita.

Quedan pendientes la definición del tiempo máximo de espera, la semántica de cancelación, el tratamiento de reintentos y el catálogo definitivo de errores.

## 9. Modalidad asíncrona

En modalidad asíncrona, la API permitirá presentar una solicitud sin mantener al consumidor bloqueado hasta que finalice la inferencia.

Como comportamiento mínimo propuesto:

1. El consumidor presenta la solicitud.
2. Model Manager registra o admite la solicitud y devuelve un identificador que permita referenciarla.
3. La ejecución continúa bajo la gestión de Model Manager.
4. El consumidor podrá obtener posteriormente el estado y, cuando esté disponible, el resultado mediante la interfaz que se defina.

La notificación activa al consumidor, los mecanismos de consulta, la persistencia de solicitudes, la retención de resultados y las reglas de recuperación quedan pendientes de especificación. La existencia de un identificador no implica por sí sola que la solicitud tenga persistencia duradera.

## 10. Interacción con Resource Manager

Model Manager no sustituye a Resource Manager ni asume la administración directa del hardware. La coordinación deberá permitir considerar, cuando corresponda:

- Disponibilidad de CPU y memoria RAM.
- Disponibilidad de GPU y memoria VRAM.
- Estado y carga de las instancias de modelos.
- Capacidad para admitir nuevas solicitudes.
- Necesidad de esperar, rechazar o diferir una solicitud por falta de recursos.

Las políticas de prioridad, cuotas, límites por usuario o proyecto, planificación y gestión de memoria GPU no quedan definidas en esta versión. Deberán especificarse de forma coordinada con el diseño de Resource Manager y Task Manager.

## 11. Administración del catálogo y de las instancias

El diseño contempla que Model Manager mantenga información suficiente para:

- Identificar modelos lógicos disponibles.
- Asociar cada modelo lógico con uno o más modelos físicos y sus versiones.
- Identificar el proveedor correspondiente.
- Conocer las instancias o servicios disponibles y su estado operativo.
- Determinar qué instancia puede atender una solicitud compatible.

La estructura persistente del catálogo, el mecanismo de actualización, la detección de cambios externos y las operaciones administrativas concretas quedan pendientes de definición.

## 12. Errores y condiciones operativas

La API deberá permitir distinguir, como mínimo conceptual, entre solicitudes inválidas, modelo lógico no resuelto, proveedor no disponible, instancia no disponible, recursos insuficientes y fallo durante la inferencia.

Este listado es orientativo y no constituye un catálogo definitivo de códigos de error. La taxonomía, la estructura de error, la posibilidad de reintento y la propagación de errores del proveedor se definirán en una revisión posterior.

## 13. Seguridad y permisos

Model Manager no otorgará permisos por sí mismo. Las solicitudes deberán estar sujetas a la identidad y autorización gestionadas por ORION CORE.

La autorización deberá contemplar, según el modelo de permisos que se defina, qué consumidor puede solicitar qué modelos y qué operaciones administrativas puede realizar. Las capacidades de un agente no equivalen a permisos. Las operaciones sensibles deberán quedar registradas conforme a las políticas generales del sistema.

La definición completa de autenticación, autorización, credenciales de proveedores y protección de secretos corresponde también a DT-09.

## 14. Trazabilidad y observabilidad

Para facilitar el seguimiento operativo, se considera necesario relacionar las solicitudes con identificadores que permitan correlacionar, cuando existan, el agente solicitante, la tarea, la solicitud de inferencia, la instancia utilizada y el resultado.

Se deberán poder analizar estados, duración, errores y utilización de recursos sin registrar innecesariamente el contenido sensible de las entradas o salidas. El esquema de eventos, los campos obligatorios, la retención y las políticas de redacción de datos quedan pendientes.

## 15. Aspectos pendientes de definición

1. Esquemas definitivos de solicitud y respuesta para ambas modalidades.
2. Formato y alcance del identificador de solicitud asíncrona.
3. API para consultar estados y recuperar resultados asíncronos.
4. Mecanismo de notificación, si corresponde.
5. Catálogo definitivo de estados y errores.
6. Tiempos máximos de espera y reglas de cancelación.
7. Reintentos, idempotencia y tratamiento de solicitudes duplicadas.
8. Persistencia, recuperación y retención de solicitudes y resultados.
9. Política de concurrencia de inferencia y límites de admisión.
10. Coordinación detallada con Task Manager y Resource Manager.
11. Administración, actualización y versionado del catálogo.
12. Seguridad de las conexiones con proveedores y gestión de credenciales.
13. Contratos de observabilidad, auditoría y protección de datos.
14. Selección del transporte y protocolo de la API interna.

## 16. Criterios de aceptación

DT-05 podrá considerarse técnicamente consolidado cuando:

- La interfaz interna sea independiente del proveedor.
- Los identificadores lógicos y su resolución estén especificados.
- Se encuentren definidos los contratos de inferencia síncrona y asíncrona.
- La solicitud asíncrona permita identificar y recuperar el resultado de manera inequívoca.
- La interacción con Resource Manager y Task Manager esté delimitada.
- Los estados, errores, cancelación y reintentos estén definidos.
- Los requisitos de identidad, permisos y trazabilidad sean consistentes con ORION CORE.
- Los contratos no contradigan REG-001 ni las decisiones ARC-001 a ARC-006.
- Existan pruebas de conformidad para ambas modalidades y para los escenarios de error.

## 17. Estado de DT-05

DT-05 se incorpora como borrador técnico. DT05-DEC-001 y DT05-DEC-002 están aprobadas. Las responsabilidades lógicas, los flujos generales y los comportamientos descritos como propuestas no deben interpretarse como contratos definitivos ni como decisiones aprobadas. Los puntos enumerados en la sección 15 requieren definición antes del cierre técnico.

------------------------------------------------------------------------

# Consolidación de DT-01 a DT-05

## Estado de los documentos

| Documento | Tema | Estado |
|:----------|:-----|:-------|
| DT-01 | Arquitectura técnica general de ORION CORE | Borrador para revisión |
| DT-02 | Especificación técnica del Message Broker | Borrador para revisión |
| DT-03 | Contratos técnicos de ORION CORE | Borrador para revisión |
| DT-04 | Contrato técnico de agente especializado | Borrador para revisión |
| DT-05 | API técnica de Model Manager | Borrador para revisión |

Las decisiones ARC-001 a ARC-006 están aprobadas. En DT-05, DT05-DEC-001 y DT05-DEC-002 están aprobadas. Esto no significa que los documentos estén cerrados en su totalidad: contienen definiciones pendientes, esquemas no formalizados y aspectos que requieren pruebas.

## Próxima secuencia de trabajo

1. Revisar y consolidar DT-01 a DT-05.
2. Completar los esquemas JSON y contratos técnicos pendientes de DT-01 a DT-05.
3. Desarrollar DT-06 — Arquitectura de interfaces multimodales.
4. Desarrollar DT-07 — Pipeline de voz y avatar.
5. Desarrollar DT-08 — Persistencia y recuperación de sesiones.
6. Desarrollar DT-09 — Arquitectura de seguridad y permisos.
7. Desarrollar DT-10 — Despliegue Windows/Ubuntu.
8. Desarrollar DT-11 — Especificación técnica de M20, formalizando los contratos C20-001 a C20-012 y sus contratos transversales.
9. Elaborar DT-12 — Matriz de pruebas e integración.

## Regla de control

Ninguna tecnología, biblioteca, protocolo, servicio externo, esquema definitivo o mecanismo de persistencia se considerará seleccionado por aparecer mencionado como ejemplo o alternativa. La selección requerirá una decisión documentada y justificada.

**Fin de DES-M20_Technical_Design_v0.2.**
