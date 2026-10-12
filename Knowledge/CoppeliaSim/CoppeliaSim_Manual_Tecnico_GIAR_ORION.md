# CoppeliaSim: manual técnico de referencia para GIAR-ORION

**Fecha de elaboración:** 12 de octubre de 2026  
**Versión de referencia de la documentación:** CoppeliaSim V4.10.0 (la documentación oficial consultada muestra V4.10).  
**Plataformas de interés:** Windows 11 y Ubuntu Linux.  
**Aplicación principal en GIAR-ORION:** simulación física y cinemática de robots, en particular Unitree G1, control externo con Python, experimentación con aprendizaje por refuerzo y auditoría de modelos importados.

> **Alcance y criterio documental.** Este documento organiza los conceptos y procedimientos principales del [CoppeliaSim User Manual](https://manual.coppeliarobotics.com/index.html), apoyándose en las páginas oficiales relevantes enlazadas en cada sección. El manual es una documentación web extensa, con páginas de referencia de API, tutoriales, propiedades de objetos y detalles por motor físico; este dossier es una guía técnica amplia y no una reproducción literal de todas sus páginas. Cuando una función o compatibilidad depende de la revisión, el sistema operativo, un plugin o el motor físico, se indica que debe comprobarse en la instalación concreta.

---

## Índice

1. [Qué es CoppeliaSim](#1-qué-es-coppeliasim)
2. [Ediciones y versiones: evaluación](#2-ediciones-y-versiones-evaluación)
3. [Instalación en Windows](#3-instalación-en-windows)
4. [Instalación en Ubuntu](#4-instalación-en-ubuntu)
5. [Arquitectura de una escena y objetos](#5-arquitectura-de-una-escena-y-objetos)
6. [Cinemática: jerarquía y árbol del robot](#6-cinemática-jerarquía-y-árbol-del-robot)
7. [Dinámica: cómo construir correctamente el árbol físico](#7-dinámica-cómo-construir-correctamente-el-árbol-físico)
8. [Articulaciones y control de motores](#8-articulaciones-y-control-de-motores)
9. [Motores físicos: MuJoCo, Bullet, ODE, Vortex y Newton](#9-motores-físicos-mujoco-bullet-ode-vortex-y-newton)
10. [Sensores y adquisición de datos](#10-sensores-y-adquisición-de-datos)
11. [Formas de programar y conectarse](#11-formas-de-programar-y-conectarse)
12. [Python: ejemplos con ZeroMQ Remote API](#12-python-ejemplos-con-zeromq-remote-api)
13. [Python: ROS 2 y otras alternativas](#13-python-ros-2-y-otras-alternativas)
14. [Lua dentro de CoppeliaSim](#14-lua-dentro-de-coppeliasim)
15. [Comparación de interfaces de conexión](#15-comparación-de-interfaces-de-conexión)
16. [Ejecución sincronizada, pasos y rendimiento](#16-ejecución-sincronizada-pasos-y-rendimiento)
17. [Buenas prácticas para un robot humanoide](#17-buenas-prácticas-para-un-robot-humanoide)
18. [Diagnóstico de errores comunes](#18-diagnóstico-de-errores-comunes)
19. [Recomendación para GIAR-ORION y Unitree G1](#19-recomendación-para-giar-orion-y-unitree-g1)
20. [Bibliografía y enlaces oficiales](#20-bibliografía-y-enlaces-oficiales)

---

# 1. Qué es CoppeliaSim

[CoppeliaSim](https://www.coppeliarobotics.com/) es un simulador robótico multiplataforma con entorno gráfico, motor de simulación, API, scripts, plugins y herramientas de cinemática, sensores y planificación. Su arquitectura distribuida permite que distintas partes de una escena sean controladas por scripts embebidos, plugins, nodos ROS/ROS 2 o aplicaciones externas.

La documentación oficial lo presenta como útil para automatización industrial, monitorización remota, control de hardware, prototipado, verificación y desarrollo de algoritmos robóticos. Puede ejecutarse como aplicación independiente o integrarse como biblioteca en una aplicación propia.

Fuentes:
- [Manual oficial — Welcome](https://manual.coppeliarobotics.com/en/welcome.htm)
- [Características principales](https://manual.coppeliarobotics.com/en/coppeliaSimFeatures.htm)

## 1.1 Capacidades principales

- Construcción de escenas y jerarquías de objetos.
- Cinemática directa e inversa (FK/IK).
- Dinámica de cuerpos rígidos y respuesta a colisiones.
- Sensores de visión, proximidad y fuerza, entre otros.
- Planificación de movimiento y cálculo de distancias/interferencias.
- Programación mediante Lua y Python embebido, API remota, plugins y ROS.
- Control sincronizado paso a paso, útil para entrenamiento y experimentación.
- Registro y visualización de variables.
- Importación de modelos y mallas, creación de geometrías de colisión y configuración de propiedades físicas.

La existencia de estas capacidades no garantiza que todos los sensores, plugins o funciones estén disponibles con idéntica configuración en cada versión, sistema operativo o paquete.

## 1.2 Conceptos que no deben confundirse

- **Escena (`.ttt`):** archivo que contiene el mundo de simulación y sus objetos.
- **Modelo (`.ttm`):** conjunto reutilizable de objetos y, según el caso, scripts y comportamiento.
- **Objeto de escena:** shape, joint, sensor, dummy, cámara, luz, script, etc.
- **Malla visual:** geometría destinada a mostrar el objeto.
- **Geometría de colisión/dinámica:** representación utilizada para contactos y cálculos físicos.
- **Cinemática:** relación geométrica entre articulaciones, enlaces y transformaciones.
- **Dinámica:** relación entre fuerzas/torques, masa, inercia, contactos y movimiento.
- **API regular:** funciones `sim.*` que pueden usarse desde scripts y, mediante interfaces compatibles, desde programas externos.
- **Remote API:** interfaz de comunicación entre procesos; no es el motor físico.
- **ROS 2:** middleware de comunicación entre nodos; no reemplaza el motor físico de CoppeliaSim.

---

# 2. Ediciones y versiones: evaluación

## 2.1 Ediciones de producto

La página oficial de producto presenta las ediciones Edu, Pro y Lite. Las condiciones de licencia son decisivas: no se debe elegir una edición solamente por sus funciones técnicas.

| Edición | Propósito general | Uso típico | Evaluación |
|---|---|---|---|
| **Edu** | Uso educativo bajo su licencia específica | Docencia, aprendizaje y proyectos de estudiantes/profesores de escuelas y universidades | Opción natural para trabajo educativo cuando la entidad y el uso cumplen la licencia |
| **Pro** | Uso comercial profesional | Empresas, integraciones comerciales y proyectos que requieren licencia comercial | Consultar precio y condiciones al proveedor |
| **Lite** | Runtime comercial para integrarse y distribuirse dentro de una aplicación propia | Productos que incorporan CoppeliaSim y se entregan a terceros | Adecuada para distribución embebida; solicitar condiciones al proveedor |

**Advertencia importante sobre Edu:** la licencia publicada establece condiciones restrictivas: está destinada exclusivamente a estudiantes, docentes y profesores de escuelas y universidades, y no autoriza el uso por empresas, instituciones de investigación, organizaciones sin fines de lucro, fundaciones ni uso comercial. Antes de distribuir un sistema o utilizarlo fuera de un contexto educativo, revisar la licencia vigente.

Fuentes:
- [Licencias oficiales](https://manual.coppeliarobotics.com/en/licensing.htm)
- [Página oficial de CoppeliaSim y ediciones](https://www.coppeliarobotics.com/)

## 2.2 Versiones de software

La documentación utiliza el formato `Vx.y.z (rev. w)`:
- `x`: versión principal.
- `y.z`: versión regular.
- `rev. w`: revisión, principalmente para correcciones.

La página de historial consultada registra **CoppeliaSim V4.10.0, 14 de mayo de 2025**. El sitio oficial de descarga consultado indica V4.10.0 rev.0 como versión disponible. Verificar siempre la versión actual en el sitio oficial antes de instalar; no asumir que un número de versión leído en un tutorial es el último.

Fuentes:
- [Historial de versiones](https://manual.coppeliarobotics.com/en/versionInfo.htm)
- [Versiones anteriores y paquetes de descarga](https://coppeliarobotics.com/previousVersions)

## 2.3 ¿Conviene actualizar una instalación existente?

| Criterio | Actualizar | Mantener una versión fijada |
|---|---|---|
| Correcciones de errores | Ventaja | Puede conservar errores ya corregidos |
| Nuevas funciones/API | Ventaja | API más estable para reproducir experimentos |
| Compatibilidad de plugins | Hay que volver a comprobar | Menor riesgo si todo se compiló para esa versión |
| Reproducibilidad de RL | Requiere revalidación | Ventaja para comparar entrenamientos |
| Escenas antiguas | Puede requerir ajustes | Menos cambios de comportamiento |
| Trabajo colaborativo | Todos deben usar una versión acordada | Facilita reproducibilidad si se registra la versión |

**Recomendación:** no actualizar en mitad de una campaña de entrenamiento. Registrar versión y revisión, motor físico, timestep, substeps, plugins, parámetros de articulaciones y commit de los scripts. Probar una actualización en una copia del proyecto y ejecutar pruebas de regresión antes de adoptarla.

## 2.4 Cambios de motor físico entre versiones

El historial oficial de V4.10.0 documenta, entre otros cambios, un ajuste del valor por defecto de `armature` en MuJoCo para evitar confusiones. El historial también señala que el usuario debe ajustar ese parámetro de manera apropiada para la estabilidad de la simulación. Esto ilustra por qué una escena puede comportarse de forma distinta tras cambiar de versión aun cuando el archivo no se haya editado explícitamente.

Fuente: [Historial oficial de versiones](https://manual.coppeliarobotics.com/en/versionInfo.htm).

---

# 3. Instalación en Windows

## 3.1 Obtener el paquete

1. Abrir la página oficial: [CoppeliaSim](https://www.coppeliarobotics.com/).
2. Seleccionar la edición adecuada y aceptar/revisar la licencia.
3. Descargar el paquete de Windows correspondiente.
4. Si se necesita una versión anterior, usar [Previous versions](https://coppeliarobotics.com/previousVersions).
5. Comprobar que la descarga corresponde a la arquitectura y versión deseadas.

El sitio distribuye paquetes de Windows que pueden variar entre instalador y paquete binario. Seguir las instrucciones específicas del archivo descargado, en lugar de aplicar pasos de un paquete distinto.

## 3.2 Instalación inicial

1. Ejecutar el instalador si se descargó un instalador, o extraer el paquete si se descargó un archivo comprimido.
2. Elegir una ruta de instalación corta y sin caracteres problemáticos, por ejemplo:
   `C:\Program Files\CoppeliaRobotics\CoppeliaSimEdu`
3. Iniciar CoppeliaSim desde el ejecutable.
4. Revisar la consola de inicio: muestra información sobre plugins y errores de carga.
5. Abrir una escena de ejemplo y ejecutar una simulación breve.
6. Confirmar que el motor físico elegido está disponible y que la escena no presenta errores.

La ruta anterior es un ejemplo de organización, no una ruta obligatoria.

## 3.3 Comprobar versión y funcionamiento

- Revisar **Help/About** o la información de versión de la aplicación.
- Abrir una escena de ejemplo incluida en la instalación.
- Ejecutar, pausar y detener la simulación.
- Comprobar que los objetos dinámicos muestran el estado dinámico esperado.
- Abrir la consola y verificar que los plugins necesarios se cargaron.

Si un plugin no se carga, comprobar compatibilidad de versión, dependencias, arquitectura y rutas. No copiar DLL arbitrarias de otra versión.

## 3.4 Python en Windows

Se recomienda utilizar un entorno virtual para el código externo:

```text
cd C:\ruta\de\tu\proyecto
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install coppeliasim-zmqremoteapi-client
```

El número de versión de Python debe ser compatible con los paquetes que use el proyecto; el cliente ZeroMQ oficial se instala con `pip`. Para usar la API remota ZeroMQ no es necesario incrustar la biblioteca principal de CoppeliaSim dentro de Python: se conecta a la instancia que se ejecuta por separado.

Si PowerShell bloquea la activación del entorno, revisar la política local de ejecución con las normas de seguridad de la máquina. No hace falta cambiarla globalmente sin necesidad; también puede invocarse el ejecutable de Python del entorno directamente.

## 3.5 ROS 2 en Windows

Para una integración de robótica que dependa de ROS 2, Ubuntu suele ser el camino más directo con la documentación del plugin ROS 2 de CoppeliaSim. En Windows, la compatibilidad depende de la distribución de ROS 2, los binarios disponibles y el plugin correspondiente. No asumir que el plugin compilado para Ubuntu funciona en Windows.

---

# 4. Instalación en Ubuntu

## 4.1 Seleccionar el paquete

El sitio oficial de versiones anteriores publica paquetes específicos para distintas versiones de Ubuntu, incluyendo en el historial consultado paquetes para Ubuntu 20.04, 22.04 y 24.04. La disponibilidad depende de la versión de CoppeliaSim. Elegir un paquete que coincida con la versión de Ubuntu y la arquitectura del equipo.

Fuentes:
- [Descargas y versiones anteriores](https://coppeliarobotics.com/previousVersions)
- [Manual oficial](https://manual.coppeliarobotics.com/index.html)

## 4.2 Instalación desde un paquete comprimido

Procedimiento general para un paquete binario Linux:

1. Descargar el paquete oficial apropiado.
2. Extraerlo en una carpeta de usuario, por ejemplo `~/Applications/CoppeliaSim`.
3. Abrir una terminal en la carpeta extraída.
4. Ejecutar el binario de CoppeliaSim desde la terminal.
5. Leer la salida de consola para identificar plugins que no se cargaron o bibliotecas faltantes.
6. Abrir una escena de ejemplo y probar la simulación.

Los nombres exactos del archivo y del ejecutable dependen del paquete descargado. No se debe asumir un nombre de archivo fijo para todas las versiones.

## 4.3 Ejecutar desde terminal

Ejecutar desde terminal es especialmente útil en Linux porque la consola permanece visible y muestra los mensajes de inicialización y carga de plugins. Si se inicia desde un lanzador gráfico y hay problemas, volver a ejecutar desde terminal para ver el error real.

La documentación explica que el terminal de Linux muestra mensajes de plugins y que conviene mantenerlo visible durante la sesión.

Fuente: [Interfaz de usuario](https://manual.coppeliarobotics.com/en/userInterface.htm).

## 4.4 Python en Ubuntu

Crear un entorno virtual e instalar el cliente ZeroMQ:

```text
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install coppeliasim-zmqremoteapi-client
```

Después, iniciar CoppeliaSim y ejecutar el cliente Python. El cliente debe apuntar al puerto/servidor ZeroMQ que esté activo en la instancia. Si el programa corre en otro equipo, configurar la conexión de red y las reglas de firewall de forma deliberada.

## 4.5 ROS 2 en Ubuntu

El manual oficial indica que el entorno de ROS 2 debe estar inicializado antes de ejecutar CoppeliaSim. La interfaz usa un plugin `libsimROS2` y, según el paquete, puede ser necesario copiarlo a la carpeta principal de CoppeliaSim o compilarlo si no existe una versión compatible para el sistema.

Procedimiento general:

1. Instalar una distribución de ROS 2 compatible con la versión de Ubuntu.
2. Seguir la documentación oficial de ROS 2 para preparar el entorno.
3. Ejecutar `source` del entorno de ROS 2 antes de iniciar CoppeliaSim.
4. Comprobar la consola para verificar que `simROS2` se carga.
5. Si no se carga, revisar dependencias, ABI, versión y compatibilidad del plugin; compilar desde la fuente oficial solo si es necesario.

Fuente: [Tutorial oficial ROS 2](https://manual.coppeliarobotics.com/en/ros2Tutorial.htm).

## 4.6 Ubuntu en WSL

WSL puede servir para determinadas tareas de Python o desarrollo, pero la visualización 3D, los drivers gráficos, la integración ROS y la física en tiempo real pueden requerir configuración adicional. Para una instalación de simulación robusta, especialmente con sensores visuales y entrenamiento prolongado, preferir Ubuntu instalado nativamente o una configuración de escritorio Linux probada. La compatibilidad concreta debe validarse en el hardware utilizado.

---

# 5. Arquitectura de una escena y objetos

CoppeliaSim representa la escena como una jerarquía de objetos. La jerarquía expresa relaciones padre-hijo y transformaciones relativas; no determina por sí sola que un objeto sea dinámico.

Tipos de objeto frecuentes:
- **Shape:** malla rígida triangular, visual y/o de colisión.
- **Joint:** unión articulada con uno o tres grados de libertad, según el tipo.
- **Force sensor:** mide la fuerza/par transmitidos en una conexión, dentro de los límites del modelo.
- **Dummy:** punto con posición y orientación; puede utilizarse para marcos, objetivos y restricciones.
- **Vision sensor:** genera imágenes/salidas de percepción simulada.
- **Proximity sensor:** detecta objetos dentro de una geometría de detección.
- **Camera/light/graph/point cloud/octree:** objetos para visualización, sensores o datos.
- **Script:** comportamiento asociado a escena/modelo o comportamiento global.

Fuente: [Objetos de escena](https://manual.coppeliarobotics.com/en/objects.htm).

## 5.1 Convenciones de nombres

Para robots articulados, conviene que cada objeto tenga un alias único y estable, por ejemplo:

```text
/G1
/G1/pelvis
/G1/left_hip_pitch_joint
/G1/left_thigh
/G1/left_knee_joint
/G1/left_shank
/G1/left_ankle_pitch_joint
/G1/left_foot
```

Estos nombres son ilustrativos. Si el modelo oficial usa otros nombres, preservar los nombres originales cuando forman parte del pipeline de control, entrenamiento o auditoría.

En la API se suelen obtener handles mediante `sim.getObject('/ruta/al/objeto')`. Usar rutas completas evita ambigüedad cuando hay varios objetos con el mismo alias.

Fuente: [Acceso programático a objetos de escena](https://manual.coppeliarobotics.com/en/accessingSceneObjects.htm).

## 5.2 Transformaciones

Cada objeto tiene un marco local y una pose respecto de su padre. Una transformación rígida representa posición y orientación. Los errores de transformaciones padre-hijo provocan:
- enlaces que aparecen desplazados;
- ejes articulares incorrectos;
- objetos visuales que no coinciden con las colisiones;
- errores de posición en sensores;
- geometría aparentemente correcta en reposo pero movimiento incorrecto al rotar una articulación.

Para importar robots desde URDF/MJCF/CAD, validar por separado:
1. pose de cada enlace en configuración cero;
2. posición y orientación de cada eje;
3. transformación entre marcos;
4. unidades y convención de coordenadas;
5. posición de los sensores respecto del cuerpo al que están unidos.

---

# 6. Cinemática: jerarquía y árbol del robot

## 6.1 Árbol cinemático

Un árbol cinemático describe cómo los enlaces se conectan por articulaciones. En un robot serial típico, cada articulación conecta un enlace padre con uno hijo. Un humanoide es una estructura ramificada: la pelvis o base conecta las dos piernas y la cadena superior del torso/brazos.

Ejemplo conceptual:

```text
world
└── G1_base / pelvis
    ├── left_hip_yaw_joint
    │   └── left_hip_roll_joint
    │       └── left_hip_pitch_joint
    │           └── left_thigh
    │               └── left_knee_joint
    │                   └── left_shank
    │                       └── left_ankle_pitch_joint
    │                           └── left_foot
    ├── right_leg_chain
    └── waist_joint
        └── torso
            ├── left_arm_chain
            ├── right_arm_chain
            ├── head
            └── sensors
```

Este diagrama ilustra la topología; el orden real de las articulaciones debe tomarse del URDF/MJCF de la variante. No usarlo como una definición exacta del árbol del G1.

## 6.2 Reglas cinemáticas

- Cada articulación debe tener el tipo correcto: revoluta, prismática, esférica o fija según el mecanismo.
- El eje debe expresarse en el marco correcto.
- Los valores de cero y los offsets deben ser coherentes.
- Las articulaciones deben conectar los cuerpos que realmente corresponden.
- No debe haber enlaces desconectados ni ciclos accidentales en una cadena que se pretende modelar como árbol.
- Los mecanismos cerrados requieren modelado y resolución adecuados; no deben convertirse arbitrariamente en un árbol abierto sin considerar las restricciones.
- Los sensores deben tener marcos bien definidos y estar conectados al cuerpo correcto.
- La jerarquía visual debe conservar la semántica necesaria para scripts y control.

## 6.3 Cinemática directa e inversa

- **FK (forward kinematics):** a partir de las posiciones articulares calcula la pose del efector final.
- **IK (inverse kinematics):** busca posiciones articulares que alcancen una pose objetivo.
- **Jacobiano:** relaciona velocidades articulares con velocidades del efector.
- **Redundancia:** un mecanismo tiene más grados de libertad que las restricciones de la tarea; pueden existir múltiples soluciones.
- **Singularidad:** configuración donde ciertas direcciones de movimiento pierden capacidad o la solución se vuelve mal condicionada.

CoppeliaSim ofrece un sistema de IK/FK basado en grupos y elementos IK, con métodos como pseudoinversa del Jacobiano, mínimos cuadrados amortiguados y proyección en el espacio nulo.

Fuentes:
- [Cinemática](https://manual.coppeliarobotics.com/en/kinematics.htm)
- [Tutorial de cinemática inversa](https://manual.coppeliarobotics.com/en/inverseKinematicsTutorial.htm)

## 6.4 Cuándo usar un modelo cinemático no dinámico

Un modelo puramente cinemático puede ser suficiente para:
- visualizar poses;
- resolver IK;
- probar trayectorias geométricas;
- verificar marcos y límites.

No es suficiente para estudiar:
- caída de un humanoide;
- contacto pie-suelo;
- fuerzas de impacto;
- estabilidad dinámica;
- torque requerido para caminar;
- transferencia de carga o respuesta a colisiones.

Para esos objetivos se necesita una configuración dinámica válida.

---

# 7. Dinámica: cómo construir correctamente el árbol físico

**La jerarquía cinemática y la validez dinámica están relacionadas, pero no son equivalentes.** Un modelo puede verse perfectamente en la escena y aun así no formar una estructura física válida.

Fuentes principales:
- [Diseño de simulaciones dinámicas](https://manual.coppeliarobotics.com/en/designingDynamicSimulations.htm)
- [Módulo de dinámica](https://manual.coppeliarobotics.com/en/dynamicsModule.htm)
- [Propiedades dinámicas de articulaciones](https://manual.coppeliarobotics.com/en/jointDynamicsProperties.htm)

## 7.1 Qué objetos participan en la dinámica

El manual explica que el conjunto dinámico se basa principalmente en shapes, joints y force sensors. La participación efectiva depende de la jerarquía, el modo de articulación, las propiedades de los shapes y el motor físico.

Para un robot articulado, normalmente se requiere:
- cuerpos rígidos no estáticos con masa e inercia válidas;
- articulaciones dinámicas que conecten cuerpos;
- geometrías de colisión válidas;
- una base fijada al mundo o un cuerpo libre, según el objetivo;
- contactos y máscaras de colisión configurados apropiadamente;
- parámetros de motor/actuador y control compatibles con el motor físico elegido.

## 7.2 Static, non-static, respondable y non-respondable

Estas propiedades son diferentes:

- **Static:** el shape no es desplazado por la dinámica; puede representar el suelo o una estructura fija.
- **Non-static:** el shape puede ser afectado por gravedad, fuerzas y restricciones.
- **Respondable:** participa en respuesta física a colisiones, sujeto a las máscaras de colisión.
- **Non-respondable:** puede estar presente para visualización o detección, pero no produce la respuesta de contacto correspondiente.

Dos shapes respondables pueden generar reacción de colisión si sus máscaras de colisión son compatibles. Una forma visual no tiene por qué ser la geometría de colisión más adecuada.

No convertir todos los cuerpos del robot en estáticos para evitar que caiga. Eso puede producir un modelo visualmente plausible pero físicamente incorrecto.

## 7.3 Árbol dinámico correcto: reglas prácticas

### A. Un enlace físico por cuerpo rígido coherente

Cada eslabón que debe moverse como un cuerpo rígido debe tener una representación dinámica coherente. Si el eslabón tiene varios objetos visuales, se puede organizar una estructura donde las mallas visuales estén asociadas al cuerpo físico, sin crear cuerpos dinámicos duplicados involuntariamente.

### B. Masa e inercia

Cada cuerpo dinámico debe tener:
- masa positiva y físicamente plausible;
- centro de masa coherente;
- tensor de inercia válido y positivo;
- orientación del marco de inercia correcta.

No asignar masas arbitrarias iguales a todos los enlaces. Las inercias incorrectas afectan la aceleración, los contactos, la estabilidad y el aprendizaje por refuerzo.

### C. Geometrías de colisión

Usar geometrías simples y estables cuando sea posible:
- cápsulas/cilindros para extremidades;
- cajas o formas convexas para torso/pelvis;
- geometría más detallada solo cuando la tarea lo necesite.

Las mallas visuales muy complejas o no convexas pueden elevar el coste y provocar problemas según el motor. Es frecuente mantener una malla visual detallada y una geometría de colisión simplificada.

### D. Articulaciones

Cada articulación dinámica debe:
- estar conectada a los cuerpos correctos;
- tener el eje correcto;
- tener límites coherentes;
- tener modo y control adecuados;
- no duplicar accidentalmente una restricción;
- tener parámetros específicos del motor revisados.

### E. Base y contacto con el mundo

Para estudiar un robot libre como un humanoide, la pelvis/base no debe quedar fijada al mundo salvo que el experimento lo requiera. El suelo normalmente es estático y respondable. Los pies deben tener geometrías de contacto que representen razonablemente la superficie de apoyo.

### F. Sensores de fuerza

Un sensor de fuerza puede modelar una conexión y reportar cargas transmitidas. No debe insertarse en cualquier punto sin comprender cómo modifica la estructura dinámica. Si solo se necesita una estimación de fuerza de contacto, evaluar si el sensor disponible corresponde a la medición que se quiere representar.

## 7.4 Orden recomendado para construir un humanoide dinámico

1. Crear la pelvis/base y comprobar masa, centro de masa e inercia.
2. Añadir una sola cadena de pierna y validar el movimiento de cada articulación.
3. Añadir la segunda pierna y revisar simetría y nombres.
4. Añadir torso/cintura y después brazos/cabeza.
5. Revisar todos los límites articulares y ejes.
6. Revisar colisiones internas y máscaras para evitar contactos espurios.
7. Comprobar la validez dinámica de cada cuerpo/articulación.
8. Ejecutar una prueba de caída sin control.
9. Ejecutar una prueba de soporte/contacto.
10. Añadir el controlador de articulaciones.
11. Solo después integrar el lazo de RL.

La prueba de caída es importante: si el robot no está sujeto y la gravedad está activa, el modelo debe responder físicamente a la gravedad. Si queda suspendido sin explicación, investigar cuerpos estáticos, articulaciones no dinámicas, restricciones, colisiones y modo de simulación.

## 7.5 Cómo inspeccionar la validez dinámica

El manual indica que los objetos dinámicos se identifican en la jerarquía durante la simulación. Si un objeto debería ser dinámico pero no puede serlo, CoppeliaSim muestra un indicador de advertencia. Durante el diagnóstico, abrir la información dinámica del objeto y revisar la razón del fallo.

No basta con que el robot no muestre mensajes de error: comprobar que cada cuerpo, articulación y contacto se comporta como se espera.

## 7.6 Restricciones y jerarquía

Las restricciones entre shapes pueden establecerse mediante:
- articulaciones dinámicas;
- sensores de fuerza dinámicos;
- restricciones dinámicas dummy-dummy.

Las restricciones deben formar la estructura mecánica prevista. Evitar restricciones duplicadas entre dos cuerpos, porque pueden sobrerrestringir el sistema y causar inestabilidad.

## 7.7 Dinámica vs. cinemática en una articulación

CoppeliaSim distingue tres modos de articulación:
- **Kinematic:** la articulación no es manejada por el módulo de dinámica y puede posicionarse directamente o seguir perfiles de movimiento.
- **Dependent:** depende de otra articulación mediante una relación lineal.
- **Dynamic:** la articulación la maneja el módulo de dinámica si la configuración conectada es válida.

Un robot configurado con articulaciones cinemáticas puede animarse, pero no reproduce automáticamente la respuesta física de un motor real.

Fuente: [Modos de articulación](https://manual.coppeliarobotics.com/en/jointModes.htm).

---

# 8. Articulaciones y control de motores

## 8.1 Modos de control dinámico

El cuadro de propiedades dinámicas de una articulación admite varias modalidades:

| Modo | Comportamiento | Uso habitual |
|---|---|---|
| Free / sin control | Articulación libre, sin motor activo | Pruebas pasivas o articulaciones sin accionamiento |
| Force/torque | Aplica fuerza/torque solicitado | Control de esfuerzo, control de bajo nivel |
| Velocity | Aplica fuerza/torque para alcanzar velocidad objetivo | Motores de velocidad |
| Position | Aplica fuerza/torque para alcanzar posición objetivo | Servocontrol articular |
| Spring-damper | Control tipo resorte-amortiguador | Comportamiento elástico simplificado |
| Custom | Llama a una función callback de articulación | Controlador personalizado |

Fuente: [Propiedades dinámicas de articulaciones](https://manual.coppeliarobotics.com/en/jointDynamicsProperties.htm).

## 8.2 API habitual

Las funciones de alto nivel incluyen, según el modo y tipo de articulación:
- `sim.setJointTargetPosition`
- `sim.setJointTargetVelocity`
- `sim.setJointTargetForce`
- `sim.getJointPosition`
- `sim.getJointVelocity`
- funciones de lectura de estado y parámetros.

Consultar la referencia exacta para las firmas, unidades y restricciones de cada función: [API de CoppeliaSim](https://manual.coppeliarobotics.com/en/apiFunctions.htm).

## 8.3 Fuerza máxima no es lo mismo que objetivo

Un objetivo de posición es una consigna. La fuerza/torque máximo es un límite del actuador simulado. Aumentar la fuerza máxima puede cambiar la respuesta y ocultar problemas de control; no debe usarse como arreglo universal para que el robot se mueva.

## 8.4 Control personalizado

En modo Custom, una callback de articulación permite calcular esfuerzo y/o velocidad en el paso dinámico. La callback puede ejecutarse con mayor frecuencia que el paso de simulación global, dependiendo del motor y los substeps. Debe evitarse asumir que cada callback equivale exactamente a un frame gráfico.

Fuente: [Callbacks de articulación](https://manual.coppeliarobotics.com/en/jointCallbackFunctions.htm).

---

# 9. Motores físicos: MuJoCo, Bullet, ODE, Vortex y Newton

CoppeliaSim ofrece cinco motores físicos en la documentación consultada:
- MuJoCo
- Bullet
- ODE (Open Dynamics Engine)
- Vortex
- Newton Dynamics

Fuente: [Módulo de dinámica](https://manual.coppeliarobotics.com/en/dynamicsModule.htm).

## 9.1 Comparación cualitativa

| Motor | Perfil general | Ventajas posibles | Precauciones |
|---|---|---|---|
| **MuJoCo** | Dinámica de cuerpos articulados, contactos y control | Muy relevante para robótica y RL; parámetros de articulaciones y contactos configurables | Los resultados dependen de timestep, solver, armature, fricción y parámetros del modelo |
| **Bullet** | Motor de física general de código abierto | Amplio uso, integración conocida y buen soporte de colisiones | No asumir que sus parámetros o resultados coinciden con MuJoCo |
| **ODE** | Dinámica rígida y detección de colisiones | Motor clásico y conocido | El ajuste de contactos y estabilidad requiere pruebas |
| **Vortex** | Motor de dinámica comercial con herramientas especializadas | Puede ser útil en escenarios industriales específicos | Disponibilidad/licencia y funciones dependen de la distribución |
| **Newton** | Motor de dinámica integrado en las versiones actuales | Alternativa para comparar comportamiento físico | Comprobar madurez, características y resultados para la escena concreta |

Esta tabla es una guía de evaluación, no una clasificación universal de precisión. La calidad depende del mecanismo, contacto, parámetros, paso de simulación y objetivo de la prueba.

## 9.2 Cómo comparar motores correctamente

Para un robot humanoide:
1. Mantener igual la geometría, masa, inercia, gravedad y control.
2. Documentar timestep y substeps por motor.
3. Registrar fricción, restitución y parámetros de contacto.
4. Ejecutar una prueba de caída y reposo.
5. Ejecutar una prueba de una articulación aislada.
6. Comparar posición, velocidad, esfuerzo, penetración de contacto y tiempo de cómputo.
7. Repetir con la misma semilla y condiciones iniciales si el experimento incluye aleatoriedad.

No comparar dos motores con parámetros predeterminados distintos y atribuir toda diferencia al motor en sí.

## 9.3 MuJoCo en un proyecto de RL

Para entrenar locomoción, el motor debe producir contactos razonables y comportamiento estable con un paso de integración compatible con el controlador. Registrar al menos:
- motor y versión;
- timestep de simulación;
- paso del motor físico/substeps;
- solver y parámetros de contacto;
- masas/inercia;
- fricción de suelo y pies;
- límites articulares;
- parámetros del controlador;
- versiones de CoppeliaSim y Python.

---

# 10. Sensores y adquisición de datos

## 10.1 Sensores comunes

CoppeliaSim permite simular, entre otros:
- sensores de visión/cámaras;
- sensores de proximidad;
- sensores de fuerza;
- sensores de contacto y datos derivados del contacto, según modelo;
- sensores externos representados mediante scripts o interfaces de hardware.

Los sensores simulados no son automáticamente equivalentes a los sensores reales. Deben modelarse resolución, ruido, latencia, frecuencia y marcos si esos factores son relevantes para el controlador.

## 10.2 Visión

Un sensor de visión produce imágenes que pueden leerse con la API. Es posible publicar imágenes a un nodo ROS 2 o enviarlas a un cliente externo. El coste de transferencia puede ser significativo para imágenes grandes o frecuencias elevadas.

Fuente: [Interfaz ROS 2 y ejemplo de publicación de imagen](https://manual.coppeliarobotics.com/en/rosInterfaces.htm).

## 10.3 Sensores de proximidad

La detección depende de la geometría de detección, los objetos elegibles y la configuración. Un sensor de proximidad no equivale a una cámara de profundidad o LiDAR completo, salvo que se configure o construya una simulación que produzca el tipo de dato requerido.

## 10.4 Sensores de fuerza

Un sensor de fuerza mide la carga transmitida a través de una conexión modelada. Hay que definir correctamente su ubicación, orientación y relación con los cuerpos. No interpretar cualquier valor de fuerza como fuerza de suelo sin comprobar el marco y el montaje.

## 10.5 Datos para RL

Un entorno RL suele requerir:
- observación de articulaciones: posición y velocidad;
- IMU o orientación/velocidad angular;
- estado de contacto de pies;
- estado de la base;
- objetivo de movimiento;
- acción articular;
- recompensa;
- señal de terminación;
- información de depuración.

Separar explícitamente:
- observación física del simulador;
- normalización de la observación;
- acción de la política;
- conversión de acción a comandos articulares;
- recompensa;
- terminación/reset.

---

# 11. Formas de programar y conectarse

La documentación presenta distintas vías de personalización que pueden combinarse. Las principales son scripts embebidos, add-ons, plugins, interfaces ROS/ROS 2, Remote API y uso de CoppeliaSim como biblioteca.

Fuente: [Scripts](https://manual.coppeliarobotics.com/en/scripts.htm) y [características principales](https://manual.coppeliarobotics.com/en/coppeliaSimFeatures.htm).

## 11.1 Scripts Lua embebidos

El código se ejecuta dentro de CoppeliaSim y puede responder a callbacks del ciclo de simulación. Es la vía directa para comportamiento asociado a un objeto/modelo.

Ventajas:
- acceso directo a objetos y API;
- baja complejidad de conexión;
- comportamiento guardado con la escena/modelo;
- ideal para prototipos, sensores y lógica local.

Desventajas:
- la lógica queda ligada a la escena;
- la gestión de dependencias y pruebas unitarias puede ser menos cómoda que en un paquete Python externo;
- no es la opción ideal para alojar todo un pipeline de entrenamiento de RL de gran tamaño.

## 11.2 Scripts Python dentro de CoppeliaSim

El manual incluye soporte para scripting Python y describe scripts con callbacks similares a los de Lua, con diferencias específicas.

Ventajas:
- bibliotecas Python en el mismo entorno de simulación;
- útil para lógica que requiere procesamiento Python;
- mantiene el acceso directo a la API.

Desventajas:
- depende del intérprete/configuración y de los paquetes compatibles con esa instalación;
- mezclar el ciclo del simulador con bibliotecas de ML puede complicar dependencias y rendimiento;
- no es lo mismo que ejecutar un proceso Python externo por Remote API.

Fuente: [Scripting](https://manual.coppeliarobotics.com/en/scripts.htm).

## 11.3 ZeroMQ Remote API

La aplicación CoppeliaSim se ejecuta como proceso separado. Un programa Python/C++/Java/etc. se conecta mediante ZeroMQ y puede llamar a funciones de la API regular y de plugins habilitados.

Es la opción recomendada por el manual frente a la Legacy Remote API para nuevas integraciones generales.

Ventajas:
- proceso Python independiente;
- fácil integrar PyTorch, NumPy y lógica de RL;
- funciona localmente o a través de red;
- admite stepping sincronizado;
- no requiere compilar CoppeliaSim como biblioteca dentro de Python.

Desventajas:
- hay latencia y serialización entre procesos;
- transferir imágenes o grandes volúmenes de datos tiene coste;
- hay que gestionar conexión, puertos y ciclo de vida del simulador;
- el rendimiento del RL puede estar limitado por llamadas remotas frecuentes.

Fuentes:
- [Remote API](https://manual.coppeliarobotics.com/en/remoteApiOverview.htm)
- [ZeroMQ Remote API](https://manual.coppeliarobotics.com/en/zmqRemoteApiOverview.htm)

## 11.4 WebSocket Remote API

La documentación presenta una Remote API basada en WebSocket, orientada a clientes JavaScript.

Ventaja:
- apropiada para aplicaciones web o herramientas JavaScript.

Desventaja:
- no suele ser la primera opción para un entorno de entrenamiento Python/PyTorch cuando ZeroMQ ya cubre el caso.

Fuente: [Remote API](https://manual.coppeliarobotics.com/en/remoteApiOverview.htm).

## 11.5 ROS y ROS 2

CoppeliaSim puede actuar como un nodo ROS/ROS 2 y publicar/suscribirse a topics, servicios y acciones mediante plugins.

Ventajas:
- arquitectura distribuida y desacoplada;
- integración con controladores y herramientas de robótica;
- mensajes estándar;
- apropiado para probar pipelines que también se usarán con hardware real.

Desventajas:
- configuración adicional de ROS y plugins;
- compatibilidad de distribución, sistema operativo y ABI;
- depuración de red/topics puede agregar complejidad;
- para un experimento RL simple, puede haber más infraestructura que la necesaria.

Fuentes:
- [ROS Interface](https://manual.coppeliarobotics.com/en/rosInterf.htm)
- [ROS 2 Interface](https://manual.coppeliarobotics.com/en/ros2Interface.htm)
- [Tutorial ROS 2](https://manual.coppeliarobotics.com/en/ros2Tutorial.htm)

## 11.6 Legacy Remote API

La Legacy Remote API está **deprecada desde CoppeliaSim V4.4** en favor de ZeroMQ Remote API.

Ventaja:
- puede ser necesaria para mantener proyectos antiguos que ya dependen de ella.

Desventajas:
- interfaz obsoleta;
- dependencia de bindings y plugin heredados;
- no es la opción recomendada para comenzar un proyecto nuevo.

Fuente: [Legacy Remote API](https://manual.coppeliarobotics.com/en/legacyRemoteApiOverview.htm).

## 11.7 BØ-based Remote API

La interfaz basada en BlueZero también está marcada como obsoleta en favor de ZeroMQ Remote API. Solo se recomienda mantenerla cuando existe una dependencia heredada que no se puede migrar de inmediato.

Fuente: [BØ-based Remote API](https://manual.coppeliarobotics.com/en/b0RemoteApiOverview.htm).

## 11.8 CoppeliaSim como biblioteca

CoppeliaSim también puede cargarse como biblioteca desde una aplicación propia. El manual documenta `coppeliaSim.dll` en Windows y `libcoppeliaSim.so` en Linux, así como una biblioteca headless. La aplicación debe gestionar la inicialización, el hilo de simulación, el bucle y la desinicialización.

Ventajas:
- integración profunda en una aplicación propia;
- control preciso del ciclo de simulación;
- puede evitar la comunicación por red/proceso separado.

Desventajas:
- integración técnica más compleja;
- gestión de hilos y ciclo de vida;
- dependencias y despliegue más delicados;
- no es el camino más sencillo para comenzar un agente de RL.

Fuentes:
- [CoppeliaSim Library](https://manual.coppeliarobotics.com/en/coppeliaSimLibrary.htm)
- [Cliente Python de la biblioteca](https://manual.coppeliarobotics.com/en/pythonClient.htm)

## 11.9 Plugins nativos

Los plugins extienden el simulador con funciones nativas, normalmente C/C++ u otras integraciones compiladas. Son útiles para extender la API o integrar bibliotecas específicas.

Ventajas:
- alto control y potencial rendimiento;
- integración directa con funciones del simulador.

Desventajas:
- compilación, ABI y dependencias por sistema operativo;
- mayor coste de mantenimiento;
- plugin y CoppeliaSim deben ser compatibles en versión.

Fuente: [Plugins](https://manual.coppeliarobotics.com/en/plugins.htm).

---

# 12. Python: ejemplos con ZeroMQ Remote API

Los siguientes ejemplos usan la interfaz recomendada para una aplicación Python externa.

## 12.1 Instalar el cliente

```text
python -m pip install coppeliasim-zmqremoteapi-client
```

La documentación oficial indica que el cliente instala sus dependencias ZeroMQ y CBOR mediante pip.

Fuente: [ZeroMQ Remote API — Python](https://manual.coppeliarobotics.com/en/zmqRemoteApiOverview.htm).

## 12.2 Ejemplo mínimo: conectar, iniciar y avanzar paso a paso

Requisito: CoppeliaSim debe estar ejecutándose con el servicio/add-on ZeroMQ Remote API disponible.

```python
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

client = RemoteAPIClient()
sim = client.require("sim")

sim.setStepping(True)
sim.startSimulation()

try:
    while sim.getSimulationTime() < 3.0:
        sim.step()
        print(f"t = {sim.getSimulationTime():.3f} s")
finally:
    sim.stopSimulation()
```

`setStepping(True)` hace que el cliente avance la simulación de forma sincronizada mediante `sim.step()`. Esto facilita que un algoritmo lea el estado, calcule una acción y avance el siguiente paso.

## 12.3 Obtener un objeto por ruta y leer su posición

```python
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

client = RemoteAPIClient()
sim = client.require("sim")

robot = sim.getObject("/Robot")
position = sim.getObjectPosition(robot, sim.handle_world)
orientation = sim.getObjectOrientation(robot, sim.handle_world)

print("Posición:", position)
print("Orientación Euler:", orientation)
```

Cambiar `/Robot` por el alias/ruta real de la escena. Las orientaciones devueltas por esta función son ángulos de Euler según la API; para cálculos robustos de orientación, conocer la convención y considerar cuaterniones cuando corresponda.

Fuente: [Acceso programático a objetos](https://manual.coppeliarobotics.com/en/accessingSceneObjects.htm).

## 12.4 Leer y mandar posición articular

```python
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

client = RemoteAPIClient()
sim = client.require("sim")

joint = sim.getObject("/Robot/joint")

# Leer posición actual:
q = sim.getJointPosition(joint)
print("q actual:", q)

# Solicitar una posición objetivo:
sim.setJointTargetPosition(joint, 0.25)
```

Este ejemplo presupone que la articulación está configurada en un modo compatible con un objetivo de posición. Si está en modo cinemático o en otro modo de control, el comportamiento será distinto. Para una articulación dinámica, configurar motor, control, límites y parámetros dinámicos en la escena.

## 12.5 Leer estado de varios motores

```python
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

client = RemoteAPIClient()
sim = client.require("sim")

joint_paths = [
    "/Robot/left_hip_pitch_joint",
    "/Robot/left_knee_joint",
    "/Robot/left_ankle_pitch_joint",
]

joints = [sim.getObject(path) for path in joint_paths]

for path, handle in zip(joint_paths, joints):
    print(path, sim.getJointPosition(handle), sim.getJointVelocity(handle))
```

Los nombres deben coincidir exactamente con los objetos de la escena. Para robots con muchos motores, construir el mapeo nombre↔handle una sola vez y conservar un orden explícito.

## 12.6 Control en lazo cerrado: ejemplo didáctico

Este ejemplo demuestra la estructura de un lazo de posición; no es un controlador recomendado para un humanoide completo.

```python
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

client = RemoteAPIClient()
sim = client.require("sim")

joint = sim.getObject("/Robot/joint")
target = 0.25

sim.setStepping(True)
sim.startSimulation()

try:
    for _ in range(500):
        q = sim.getJointPosition(joint)
        error = target - q

        # La articulación debe estar configurada para control de posición.
        sim.setJointTargetPosition(joint, target)

        sim.step()

        if abs(error) < 0.01:
            break
finally:
    sim.stopSimulation()
```

En un controlador real, la acción puede provenir de PID, una política RL o un controlador de torque. Hay que verificar límites, frecuencia, saturación, modos articulares y estabilidad.

## 12.7 Obtener imagen de un sensor de visión

```python
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

client = RemoteAPIClient()
sim = client.require("sim")

sensor = sim.getObject("/VisionSensor")
image, resolution = sim.getVisionSensorImg(sensor)

print("Resolución:", resolution)
print("Bytes/píxeles recibidos:", len(image))
```

Para visualizar la imagen, convertir el buffer según el formato y la resolución que devuelve la API. Confirmar si el dato está codificado como RGB/RGBA y si requiere reordenamiento de filas/bytes antes de pasarlo a OpenCV o NumPy.

## 12.8 Ejecutar el simulador en modo stepping para RL

Esquema recomendado:

```text
iniciar simulación
para cada paso de control:
    leer estado
    construir observación
    política RL -> acción
    aplicar acción
    avanzar simulación exactamente un paso
    leer nuevo estado
    calcular recompensa
    comprobar terminación
al terminar episodio:
    detener o reiniciar el entorno
```

Para entrenamiento eficiente, reducir las llamadas remotas innecesarias. Si cada acción requiere docenas de llamadas de ida y vuelta, la latencia de comunicación puede dominar el tiempo de entrenamiento. Evaluar agrupar lecturas/escrituras, ejecutar parte de la lógica dentro del simulador o utilizar una integración de nivel más bajo si el cuello de botella lo justifica.

---

# 13. Python: ROS 2 y otras alternativas

## 13.1 ROS 2: cuándo elegirlo

ROS 2 es apropiado cuando el experimento necesita una arquitectura distribuida con nodos separados para percepción, planificación, control y logging, o cuando se busca mantener una interfaz cercana a la que se utilizará con el robot real.

Ejemplo conceptual de topics:
- `/joint_states`: estado articular, si el sistema lo publica con ese nombre/tipo.
- `/cmd_vel`: velocidad base en robots móviles, cuando el controlador la soporta.
- topics de imágenes, nubes de puntos o IMU según el modelo y los nodos.
- servicios/actions para operaciones específicas.

Estos nombres son convenciones frecuentes, no garantías de que una escena CoppeliaSim los publique automáticamente. El proyecto debe definir los mensajes, topics y tipos reales.

## 13.2 Ejemplo de publicación de imagen desde un script

La documentación oficial muestra cómo crear un publisher ROS 2 desde un script de CoppeliaSim, leer la imagen de un sensor y publicar un mensaje `sensor_msgs/msg/Image`. La implementación exacta depende de la API y versión del plugin.

Referencia y ejemplo oficial:
[ROS Interfaces — ejemplo de imagen](https://manual.coppeliarobotics.com/en/rosInterfaces.htm).

## 13.3 API remota versus ROS 2

Para un experimento local de RL que ya está implementado en Python/PyTorch, ZeroMQ suele ser más simple. ROS 2 es más atractivo cuando la arquitectura requiere nodos independientes, mensajes estándar y conexión con otros componentes robóticos.

## 13.4 Legacy API: migración

Si un proyecto usa `simxStart`, `simxGetObjectHandle` y funciones `simx*`, probablemente depende de la Legacy Remote API. Para un proyecto nuevo, usar ZeroMQ. Para migrar, probar en una copia y mapear cada llamada antigua a la API regular equivalente; revisar cambios de sincronización, streaming y valores de retorno.

---

# 14. Lua dentro de CoppeliaSim

CoppeliaSim integra Lua y amplía el lenguaje con funciones de API que suelen comenzar por `sim.`. Los scripts usan callbacks del ciclo de simulación. Hay scripts embebidos, scripts principales, scripts de simulación, scripts de personalización, sandbox y add-ons.

Fuentes:
- [Scripting](https://manual.coppeliarobotics.com/en/scripts.htm)
- [Script objects](https://manual.coppeliarobotics.com/en/scriptObjects.htm)
- [API functions](https://manual.coppeliarobotics.com/en/apiFunctions.htm)

## 14.1 Estructura básica de un script de simulación

```lua
function sysCall_init()
    sim = require('sim')
    joint = sim.getObject('/Robot/joint')
    target = 0.25
end

function sysCall_actuation()
    sim.setJointTargetPosition(joint, target)
end

function sysCall_sensing()
    local q = sim.getJointPosition(joint)
    print('Posición articular: ' .. q)
end

function sysCall_cleanup()
    print('Fin de la simulación')
end
```

- `sysCall_init`: inicialización al comenzar la simulación.
- `sysCall_actuation`: aplicar consignas/acciones.
- `sysCall_sensing`: leer y procesar datos.
- `sysCall_cleanup`: liberar recursos o informar al terminar.

La selección de callback debe corresponder al orden del ciclo de simulación y a la tarea concreta.

## 14.2 Leer varias articulaciones

```lua
function sysCall_init()
    sim = require('sim')
    jointPaths = {
        '/Robot/left_hip_pitch_joint',
        '/Robot/left_knee_joint',
        '/Robot/left_ankle_pitch_joint'
    }

    joints = {}
    for i, path in ipairs(jointPaths) do
        joints[i] = sim.getObject(path)
    end
end

function sysCall_sensing()
    for i, joint in ipairs(joints) do
        local q = sim.getJointPosition(joint)
        local dq = sim.getJointVelocity(joint)
        print(string.format('%d: q=%.4f dq=%.4f', i, q, dq))
    end
end
```

## 14.3 Aplicar una consigna a un conjunto de articulaciones

```lua
function sysCall_init()
    sim = require('sim')

    jointPaths = {
        '/Robot/left_hip_pitch_joint',
        '/Robot/left_knee_joint'
    }

    targetPositions = {0.1, 0.3}
    joints = {}

    for i, path in ipairs(jointPaths) do
        joints[i] = sim.getObject(path)
    end
end

function sysCall_actuation()
    for i, joint in ipairs(joints) do
        sim.setJointTargetPosition(joint, targetPositions[i])
    end
end
```

Este ejemplo requiere que las articulaciones estén configuradas de forma compatible con control de posición. No garantiza un perfil de movimiento ni límites seguros por sí solo.

## 14.4 Obtener la pose de un objeto

```lua
function sysCall_init()
    sim = require('sim')
    robot = sim.getObject('/Robot')
end

function sysCall_sensing()
    local p = sim.getObjectPosition(robot, sim.handle_world)
    local e = sim.getObjectOrientation(robot, sim.handle_world)

    print(string.format(
        'p=(%.3f, %.3f, %.3f), euler=(%.3f, %.3f, %.3f)',
        p[1], p[2], p[3], e[1], e[2], e[3]
    ))
end
```

## 14.5 Control de fuerza/torque

La función para fijar la fuerza objetivo se usa en un contexto compatible con el modo de control de la articulación. El modo, los límites y las unidades deben revisarse en la documentación de la articulación y del motor.

```lua
function sysCall_init()
    sim = require('sim')
    joint = sim.getObject('/Robot/joint')
end

function sysCall_actuation()
    -- Ejemplo didáctico: torque/fuerza de consigna.
    -- La articulación debe estar configurada en modo dinámico
    -- y en un modo de control compatible.
    sim.setJointTargetForce(joint, 1.0)
end
```

No usar valores arbitrarios de torque sobre un humanoide completo. Comenzar con una articulación aislada, límites bajos y una escena de prueba.

## 14.6 Callback de articulación personalizada

CoppeliaSim permite implementar control personalizado mediante callbacks de articulación cuando la articulación está en modo dinámico y el control personalizado está activado. Esto puede servir para controladores de bajo nivel, pero la callback y el motor físico deben configurarse de acuerdo con el manual.

Fuente: [Joint callback functions](https://manual.coppeliarobotics.com/en/jointCallbackFunctions.htm).

## 14.7 Lua frente a Python

| Criterio | Lua embebido | Python externo |
|---|---|---|
| Acceso a objetos | Directo | Mediante API remota |
| Dependencias de ML | Limitadas frente al ecosistema Python | Excelente ecosistema de NumPy/PyTorch |
| Latencia de llamadas | No hay ida y vuelta entre procesos | Hay comunicación y serialización |
| Ciclo de simulación | Integrado | Coordinado por API remota |
| Depuración de la escena | Cómoda | Depende de cliente y servidor |
| Entrenamiento RL grande | Útil para lógica local | Generalmente más conveniente |
| Portabilidad de lógica | Ligada a la escena/API | Código externo separable |
| Uso recomendado | Automatización local y comportamiento de objetos | Entrenamiento, análisis y orquestación del experimento |

---

# 15. Comparación de interfaces de conexión

| Método | Arquitectura | Ventajas principales | Desventajas principales | Recomendación |
|---|---|---|---|---|
| Lua embebido | Dentro de CoppeliaSim | Acceso directo y baja latencia | Lógica acoplada a la escena; ecosistema ML menos cómodo | Scripts locales y control de escena |
| Python embebido | Dentro de CoppeliaSim | Python junto al simulador | Dependencias/intérprete; acoplamiento al proceso | Procesamiento local específico |
| ZeroMQ Remote API | Python externo ↔ CoppeliaSim | Simple, multiplataforma, stepping, API extensa | Latencia y coste de llamadas remotas | **Primera elección para GIAR-ORION** |
| ROS 2 | Nodos distribuidos | Estándares, módulos desacoplados, integración robótica | Configuración y depuración más complejas | Cuando se necesita arquitectura ROS |
| WebSocket Remote API | Cliente JavaScript ↔ simulador | Integración web | Menos natural para RL Python | Interfaces web |
| Legacy Remote API | Cliente externo heredado | Mantiene proyectos antiguos | Deprecada desde V4.4 | Solo mantenimiento/migración |
| BØ Remote API | Cliente externo heredado | Puede sostener sistemas antiguos | Obsoleta frente a ZeroMQ | Solo legado |
| CoppeliaSim como biblioteca | Embebido en aplicación | Control fino del ciclo, integración profunda | Complejidad de hilos/ABI/despliegue | Fase avanzada o requisito de integración |
| Plugin C/C++ | Dentro del proceso | Extensión nativa y rendimiento | Compilación y mantenimiento por versión/OS | Solo si se necesita una extensión nativa |

## 15.1 Recomendación práctica

Para un proyecto nuevo en Python/PyTorch:
1. Comenzar con **ZeroMQ Remote API**.
2. Activar stepping para que cada acción se aplique a un paso controlado.
3. Medir rendimiento y coste de comunicación.
4. Si el entrenamiento necesita ROS, integrar ROS 2 en una fase posterior.
5. Considerar biblioteca embebida o lógica local solo si hay una necesidad demostrada de rendimiento o integración.

---

# 16. Ejecución sincronizada, pasos y rendimiento

## 16.1 Simulación libre frente a stepping

- **No sincronizada:** el simulador avanza a su propio ritmo; el cliente consulta y envía órdenes cuando puede.
- **Stepping:** el cliente solicita explícitamente avanzar un paso. Facilita el control determinista del orden de observación, acción y avance de simulación.

Para RL, el stepping permite organizar de manera clara la transición:
`observación_t → acción_t → avance → observación_(t+1) → recompensa_t`.

## 16.2 Timestep y substeps

No confundir:
- paso de simulación;
- paso interno del motor físico;
- frecuencia del controlador;
- frecuencia de lectura de sensores;
- frecuencia de renderizado;
- frecuencia de llamadas del cliente remoto.

Los valores deben elegirse de acuerdo con la dinámica y el controlador. Un paso demasiado grande puede empeorar la estabilidad del contacto; uno demasiado pequeño aumenta el coste computacional.

## 16.3 Rendimiento

Los principales factores incluyen:
- número de cuerpos y articulaciones;
- complejidad de colisiones;
- número de contactos simultáneos;
- motor y parámetros;
- timestep/substeps;
- sensores de visión y resolución;
- transferencia de datos a través de Remote API;
- frecuencia de logging;
- renderizado gráfico.

Para medir el rendimiento de RL, separar:
1. tiempo que consume el motor físico;
2. tiempo de la política/neural network;
3. tiempo de comunicación;
4. tiempo de procesamiento de recompensa/observación;
5. tiempo de visualización y logging.

---

# 17. Buenas prácticas para un robot humanoide

## 17.1 Separar los componentes

Mantener módulos diferenciados para:
- modelo mecánico;
- observación;
- controlador;
- interfaz CoppeliaSim;
- recompensa;
- terminación/reset;
- entrenamiento;
- evaluación;
- logging/auditoría.

Esto permite cambiar el controlador o el modelo sin rehacer todo el sistema.

## 17.2 Preservar nombres y mapeos

No renombrar articulaciones una vez que los scripts, el modelo de política y los archivos de configuración dependen de esos nombres. Mantener un archivo de mapeo explícito:

| Índice de control | Nombre de articulación | Handle | Unidad | Límite inferior | Límite superior |
|---:|---|---|---|---:|---:|
| 0 | nombre real | resuelto en ejecución | rad | del modelo | del modelo |
| 1 | nombre real | resuelto en ejecución | rad | del modelo | del modelo |

Los valores deben extraerse del modelo exacto; no rellenar con ejemplos.

## 17.3 Auditar masas e inercias

Antes de entrenar, comprobar:
- masa total;
- masa por enlace;
- centro de masa;
- tensores de inercia;
- ejes articulares;
- rangos;
- límites de esfuerzo;
- cuerpos dinámicos habilitados;
- geometrías respondables;
- colisiones internas;
- contacto pie-suelo.

## 17.4 Validación escalonada

1. Inspección visual sin dinámica.
2. Validación cinemática con una articulación a la vez.
3. Caída libre y gravedad.
4. Contacto con suelo.
5. Control articular aislado.
6. Control de postura.
7. Perturbaciones suaves.
8. Entrenamiento RL.

No comenzar por un entrenamiento de cientos de episodios si la dinámica base no está validada.

## 17.5 Sim-to-real

Para transferir políticas a un robot real, tener en cuenta:
- diferencias entre simulador y hardware;
- latencia y jitter;
- límites reales de actuadores;
- saturación;
- ruido y sesgo de sensores;
- frecuencia de control;
- contactos y fricción;
- variación de masa/carga;
- seguridad y parada de emergencia.

Un modelo que “camina” en la simulación no prueba por sí solo que la política sea segura en un robot físico.

---

# 18. Diagnóstico de errores comunes

| Síntoma | Causas posibles | Comprobación recomendada |
|---|---|---|
| El robot queda suspendido | Cuerpos estáticos, articulaciones cinemáticas, restricciones, base fijada | Revisar propiedades dinámicas y topología |
| El robot atraviesa el suelo | Shapes no respondables, máscaras de colisión, geometría de colisión incorrecta | Revisar suelo/pies y máscaras |
| El robot explota o se desestabiliza | Inercias, masas, timestep, contactos, restricciones duplicadas | Simplificar escena y validar una cadena |
| Articulaciones en gris/no activas | Modo, conexión dinámica o configuración de motor incorrecta | Revisar joint mode y estado dinámico |
| No se obtiene un handle | Ruta/alias incorrecto o escena diferente | Usar ruta absoluta y listar/inspeccionar jerarquía |
| ZeroMQ no conecta | Instancia no activa, add-on/plugin, puerto, firewall o cliente incompatible | Revisar consola y configuración del servidor |
| ROS 2 no aparece | Entorno no cargado, plugin no compatible o dependencias ausentes | Ejecutar desde terminal y revisar carga del plugin |
| Python no encuentra el paquete | Entorno virtual equivocado | Comprobar el intérprete y `python -m pip show ...` |
| Cambia la dinámica al actualizar | Cambios de versión o parámetros por defecto | Fijar versión y comparar propiedades físicas |
| Entrenamiento muy lento | Demasiadas llamadas remotas, sensores costosos, logging o timestep pequeño | Perfilar cada etapa y reducir datos innecesarios |

---

# 19. Recomendación para GIAR-ORION y Unitree G1

Dado que GIAR-ORION trabaja con Python, PyTorch, aprendizaje por refuerzo y modelos del Unitree G1, la arquitectura inicial recomendada es:

```text
GIAR-ORION / Python
    ├── Environment.py
    ├── RewardEngine.py
    ├── SAC.py / política RL
    ├── ReplayBuffer.py
    └── CoppeliaSimAdapter.py
              │
              │ ZeroMQ Remote API
              ▼
         CoppeliaSim
              ├── modelo G1 (.ttm)
              ├── articulaciones y cuerpos dinámicos
              ├── sensores
              ├── motor físico seleccionado
              └── scripts Lua auxiliares
```

Este diagrama es una propuesta de arquitectura; los nombres de módulos deben ajustarse a la estructura real del repositorio.

## 19.1 Qué dejar en Python externo

- entrenamiento SAC/PPO u otro algoritmo;
- redes neuronales y optimizadores;
- Replay Buffer;
- configuración y experimentos;
- logging, métricas y checkpoints;
- evaluación de políticas;
- generación de informes.

## 19.2 Qué dejar en CoppeliaSim/Lua

- lógica local de la escena que deba ejecutarse cerca del ciclo de simulación;
- inicialización de objetos y sensores;
- controladores auxiliares locales;
- callbacks de articulaciones cuando se requieran;
- operaciones que reduzcan muchas llamadas remotas si se ha medido que la comunicación es el cuello de botella.

No duplicar la misma lógica de control en Lua y Python sin definir cuál es la autoridad. Debe quedar claro dónde se calcula la acción y dónde se ejecuta.

## 19.3 Plan de implementación

**Etapa 1 — Congelar el entorno**
- registrar versión/revisión de CoppeliaSim;
- registrar motor físico y parámetros;
- conservar una copia de la escena original;
- fijar versión del cliente ZeroMQ.

**Etapa 2 — Auditoría del modelo**
- inventariar cuerpos y articulaciones;
- validar nombres, orden, ejes, límites;
- validar masas e inercias;
- comprobar colisiones y caída libre.

**Etapa 3 — Adaptador Python**
- implementar conexión;
- resolver handles una sola vez;
- leer estado;
- aplicar acciones;
- avanzar con stepping;
- reiniciar episodios de manera reproducible.

**Etapa 4 — Pruebas**
- lectura de estado;
- control de una articulación;
- control de varias articulaciones;
- prueba de caída/contacto;
- prueba de reset;
- medición de rendimiento.

**Etapa 5 — Entrenamiento**
- integrar observaciones, acciones, recompensas y terminaciones;
- validar unidades y normalizaciones;
- ejecutar pocos episodios de diagnóstico;
- aumentar el entrenamiento solo después de verificar que las transiciones son correctas.

---

# 20. Bibliografía y enlaces oficiales

## Manual general y versiones
1. [CoppeliaSim User Manual](https://manual.coppeliarobotics.com/index.html)
2. [Welcome](https://manual.coppeliarobotics.com/en/welcome.htm)
3. [Características principales](https://manual.coppeliarobotics.com/en/coppeliaSimFeatures.htm)
4. [Historial de versiones](https://manual.coppeliarobotics.com/en/versionInfo.htm)
5. [Versiones anteriores](https://coppeliarobotics.com/previousVersions)
6. [Licencias](https://manual.coppeliarobotics.com/en/licensing.htm)

## Objetos, cinemática y dinámica
7. [Objetos de escena](https://manual.coppeliarobotics.com/en/objects.htm)
8. [Acceso programático a objetos](https://manual.coppeliarobotics.com/en/accessingSceneObjects.htm)
9. [Cinemática](https://manual.coppeliarobotics.com/en/kinematics.htm)
10. [Tutorial IK](https://manual.coppeliarobotics.com/en/inverseKinematicsTutorial.htm)
11. [Diseño de simulaciones dinámicas](https://manual.coppeliarobotics.com/en/designingDynamicSimulations.htm)
12. [Módulo de dinámica](https://manual.coppeliarobotics.com/en/dynamicsModule.htm)
13. [Modos de articulación](https://manual.coppeliarobotics.com/en/jointModes.htm)
14. [Propiedades dinámicas de articulaciones](https://manual.coppeliarobotics.com/en/jointDynamicsProperties.htm)
15. [Callbacks de articulación](https://manual.coppeliarobotics.com/en/jointCallbackFunctions.htm)

## Programación y conexiones
16. [Scripting](https://manual.coppeliarobotics.com/en/scripts.htm)
17. [Script objects](https://manual.coppeliarobotics.com/en/scriptObjects.htm)
18. [Remote API](https://manual.coppeliarobotics.com/en/remoteApiOverview.htm)
19. [ZeroMQ Remote API](https://manual.coppeliarobotics.com/en/zmqRemoteApiOverview.htm)
20. [Legacy Remote API](https://manual.coppeliarobotics.com/en/legacyRemoteApiOverview.htm)
21. [BØ Remote API](https://manual.coppeliarobotics.com/en/b0RemoteApiOverview.htm)
22. [ROS Interface](https://manual.coppeliarobotics.com/en/rosInterf.htm)
23. [ROS 2 Interface](https://manual.coppeliarobotics.com/en/ros2Interface.htm)
24. [Tutorial ROS 2](https://manual.coppeliarobotics.com/en/ros2Tutorial.htm)
25. [CoppeliaSim Library](https://manual.coppeliarobotics.com/en/coppeliaSimLibrary.htm)
26. [Cliente Python de CoppeliaSim Library](https://manual.coppeliarobotics.com/en/pythonClient.htm)
27. [Plugins](https://manual.coppeliarobotics.com/en/plugins.htm)
28. [API functions](https://manual.coppeliarobotics.com/en/apiFunctions.htm)

---

## Nota final

Este dossier sirve como guía de trabajo y como índice técnico de fuentes oficiales. Para decisiones de producción, compatibilidad de versiones, licencias, parámetros de motor y funciones específicas, consultar la página oficial correspondiente a la versión instalada. Antes de modificar el modelo del G1 o iniciar entrenamiento de RL, registrar el archivo exacto de escena/modelo, la versión de CoppeliaSim, el motor físico y los parámetros relevantes.
