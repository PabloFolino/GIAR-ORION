# Unitree G1 — Dossier técnico con fuentes verificables
**Proyecto:** GIAR-ORION  
**Fecha de consulta:** 12 de octubre de 2026  
**Objetivo:** reunir información de fabricante y repositorios de software sobre el humanoide Unitree G1, con foco en simulación, control y aprendizaje por refuerzo.

> **Criterio de confiabilidad.** Se priorizan la página oficial de Unitree, la aplicación/manuales oficiales y repositorios de la organización `unitreerobotics`. Los datos publicados para el producto comercial no siempre coinciden con una configuración EDU, una revisión de hardware o el modelo de simulación. Se identifican explícitamente los valores que no están publicados en las fuentes consultadas; no deben completarse con estimaciones como si fueran especificaciones oficiales.

## 1. Resumen ejecutivo

- El G1 estándar se publica con **1320 × 450 × 200 mm** en posición de pie, **690 × 450 × 300 mm** plegado y aproximadamente **35 kg con batería**.
- La página oficial distingue **G1 (23 grados de libertad)** y **G1 EDU (23–43, según opciones)**. Las configuraciones con manos, muñecas adicionales y cintura de 3 DoF cambian la cantidad de articulaciones.
- El accionamiento se describe como motor síncrono de imanes permanentes (PMSM), rotor interior de baja inercia y alta velocidad, con **doble encoder** y refrigeración local por aire. El par máximo publicado corresponde al mayor motor de la máquina, no a todos los motores: **90 N·m para G1 y 120 N·m para G1 EDU** en la tabla consultada.
- La batería extraíble se especifica como **13 celdas en serie (13S), 9000 mAh**; cargador **54 V, 5 A**; autonomía declarada de aproximadamente **2 horas**. La duración real depende de la tarea y la configuración.
- La página del fabricante enumera cámara de profundidad, LiDAR 3D, matriz de cuatro micrófonos, altavoz de 5 W, Wi-Fi 6 y Bluetooth 5.2. No identifica en esa tabla el fabricante/modelo exacto de cada sensor ni todas sus tasas de muestreo.
- Para control y telemetría hay ejemplos oficiales en `unitree_ros2` y `unitree_sdk2`. El ejemplo ROS 2 de bajo nivel usa `LowCmd` para mandar objetivos de posición/velocidad/par y `LowState` para leer estado de motores e IMU. El ejemplo activa lectura a **500 Hz**; eso es una frecuencia de ejemplo del lazo/lectura, **no una medición del tiempo de respuesta mecánico del motor**.
- Para simulación, `unitree_rl_gym` publica descripciones URDF y MJCF/XML de variantes G1 de 12, 29 DoF y 29 DoF con manos, entre otras. Estos archivos son una fuente técnica valiosa para jerarquía, masas, inercias, ejes, rangos articulares y límites de actuador del modelo concreto.
- Las fuentes públicas consultadas **no permiten confirmar de forma general** la corriente máxima por motor, la curva par-velocidad, el ancho de banda mecánico del actuador, el tiempo de respuesta de cada motor, la temperatura ambiente operativa certificada ni la masa real de cada pieza física de un robot concreto. Para ello se necesita el manual de la revisión exacta, datos del fabricante o medición de laboratorio.

## 2. Especificaciones mecánicas oficiales publicadas

| Parámetro | G1 | G1 EDU | Notas |
|---|---:|---:|---|
| Dimensiones de pie (alto × ancho × espesor) | 1320 × 450 × 200 mm | 1320 × 450 × 200 mm | Página oficial |
| Dimensiones plegado | 690 × 450 × 300 mm | 690 × 450 × 300 mm | Página oficial |
| Masa con batería | ≈ 35 kg | ≈ 35 kg o más | EDU depende de accesorios |
| Grados de libertad totales | 23 | 23–43 | Depende de cintura, muñecas y manos opcionales |
| DoF por pierna | 6 | 6 | 12 en ambas piernas |
| Cintura | 1 DoF | 1 DoF + 2 opcionales | No asumir que toda variante tiene cintura de 3 DoF |
| DoF por brazo | 5 | 5 | En la tabla comercial |
| Mano | No incluida en la configuración base indicada | Opciones de mano dexterous; Dex3-1 puede tener 7 DoF activos | Puede haber opciones adicionales |
| Longitud combinada muslo + pantorrilla | ≈ 0,6 m | ≈ 0,6 m | Dato de catálogo |
| Alcance/ancho de brazos publicado | ≈ 0,45 m | ≈ 0,45 m | La página lo denomina “arm span”; confirmar definición antes de usarlo en CAD |
| Carga máxima de brazo | ≈ 2 kg | ≈ 3 kg | Varía mucho con la postura y extensión del brazo |
| Par máximo de rodilla publicado | 90 N·m | 120 N·m | Especificación de catálogo; no extrapolar a todos los actuadores |
| Rodamientos de salida | Rodamientos de rodillos cruzados industriales | Igual | Página oficial |
| Cableado | Enrutamiento eléctrico hueco por articulaciones | Igual | Página oficial |

**Fuente principal:** [Unitree G1 — página oficial del fabricante](https://www.unitree.com/g1/).

### Rangos articulares comerciales publicados

La página del fabricante presenta los siguientes rangos amplios de movimiento:

- Cintura Z: ±155°.
- Rodilla: 0–165°.
- Cadera: pitch ±154°, roll −30° a +170°, yaw ±158°.
- Muñeca: pitch ±92,5° y yaw ±92,5° en las configuraciones correspondientes.
- G1 EDU puede tener cintura X/Y adicional de ±30° según la opción instalada.

Estos rangos comerciales son descriptivos. Para control, límites de seguridad y simulación se deben usar los límites del **modelo y revisión exactos** (URDF/MJCF), y luego confirmarlos contra la unidad física. Convenciones de eje, signo y cero pueden diferir entre documentos.

## 3. Motores, realimentación y control

### 3.1 Tipo de actuador y sensores articulares

El fabricante describe los motores articulares como **PMSM (Permanent Magnet Synchronous Motor)** de rotor interior, baja inercia y alta velocidad. También publica doble encoder en las articulaciones y refrigeración local por aire.

La doble medición de encoder aporta información de posición/velocidad para el control articular. No debe interpretarse automáticamente como un sensor de par de salida: el conjunto de sensores y estimadores disponibles depende de la versión del actuador y de la interfaz de estado.

### 3.2 Variables de mando y realimentación expuestas por el software

Los ejemplos oficiales de bajo nivel exponen, por articulación, variables equivalentes a:

- **Comando:** `q` (posición objetivo), `dq` (velocidad objetivo), `tau` (par feed-forward), `kp` y `kd` (ganancias del control).
- **Estado:** `q` (posición), `dq` (velocidad), `tau_est`/par estimado y datos de estado/temperatura del motor, según el mensaje y la versión del SDK.
- **IMU:** orientación/ángulos de Euler, velocidad angular del giroscopio y aceleración, según la estructura del mensaje y el ejemplo utilizado.
- **Batería/gestión de potencia:** estado BMS y datos de energía disponibles en las interfaces que los publiquen.
- **Otros:** mando inalámbrico; en determinadas interfaces también fuerzas de pie estimadas/medidas.

Los campos concretos deben comprobarse en las definiciones de mensajes del SDK correspondiente a la familia de hardware (`unitree_hg` para la familia humanoide, no asumir que mensajes `unitree_go` de cuadrúpedos son intercambiables).

### 3.3 Interfaces oficiales relevantes

1. **`unitree_ros2`**: incluye un ejemplo de bajo nivel para G1, publicación de `LowCmd` en `/lowcmd` y suscripción al estado de bajo nivel (`lowstate` o `lf/lowstate`, según el ejemplo/configuración). El ejemplo declara 29 motores y ofrece un modo de lectura de alta frecuencia de 500 Hz.
2. **`unitree_sdk2`**: SDK C++ con ejemplos específicos para G1, incluidos ejemplos de control de articulaciones y lectura de IMU/estado.
3. **Unitree Explore App / manuales oficiales**: configuración inicial, red, calibración de 23/29 DoF, conexión del control remoto, postura/movimiento, batería/cargador y mantenimiento.

Fuentes:
- [Repositorio oficial `unitree_ros2`](https://github.com/unitreerobotics/unitree_ros2)
- [Ejemplo ROS 2 de bajo nivel para G1](https://github.com/unitreerobotics/unitree_ros2/blob/master/example/src/src/g1/lowlevel/g1_low_level_example.cpp)
- [Repositorio oficial `unitree_sdk2`](https://github.com/unitreerobotics/unitree_sdk2)
- [Unitree Explore App y manuales G1](https://www.unitree.com/app/g1/)

**Precaución:** el control de bajo nivel puede mover el robot con fuerza. Primero se debe probar sin carga, con soporte físico apropiado, parada de emergencia y límites conservadores. No enviar comandos de torque/posición a un humanoide real basándose solo en un ejemplo genérico.

### 3.4 Frecuencia y tiempo de respuesta

- El ejemplo ROS 2 usa un temporizador/lazo de **500 Hz** (periodo nominal de 2 ms) para el ejemplo de control y puede suscribirse al estado a alta frecuencia.
- Esto **no demuestra** que el actuador físico tenga un tiempo de respuesta de 2 ms, ni que la red, el firmware y el control interno tengan latencia total de 2 ms.
- No se encontró en las fuentes oficiales públicas consultadas una especificación completa y general de tiempo de subida, retardo, ancho de banda o latencia de cada motor. Esos datos deben obtenerse del fabricante o medirse en un protocolo controlado.

## 4. Límites articulares y límites de esfuerzo

Hay que distinguir tres conceptos:

1. **Límites mecánicos/comerciales:** rangos amplios publicados en la página del producto.
2. **Límites del modelo de simulación:** `range` de cada `joint` y, cuando existe, `actuatorfrcrange` del XML/MJCF. Son parámetros de esa versión del modelo; no necesariamente representan todos los límites de seguridad del hardware real.
3. **Límites de seguridad del controlador/firmware:** límites operativos y de protección del robot real. Deben respetarse aunque el simulador permita más.

El archivo oficial `g1_29dof_with_hand_rev_1_0.xml` incluye, por articulación, nombres, ejes, rangos angulares, masas e inercias de eslabones y límites de fuerza/par del actuador modelado. Por ejemplo, algunas articulaciones de pierna y rodilla tienen límites de esfuerzo de modelo muy superiores a los de muñeca/mano. **No debe usarse un único límite de par para todas las articulaciones.**

Fuente: [MJCF/XML oficial G1 29 DoF con manos](https://github.com/unitreerobotics/unitree_rl_gym/blob/main/resources/robots/g1_description/g1_29dof_with_hand_rev_1_0.xml).

### Corrientes máximas

No se halló una tabla oficial pública y verificable con la corriente continua y pico de cada motor G1, ni su duración permitida. El dato de cargador (54 V, 5 A) **no es** la corriente máxima de los motores; son magnitudes de subsistemas distintos. No estimar corriente de fase del motor a partir de esos dos valores.

### Temperaturas

El SDK contiene funciones de terminación de ejemplo con umbrales de software, por ejemplo temperatura de bobinado >120 °C y carcasa >85 °C. Son **umbrales de protección del código consultado**, no una certificación de rango ambiental ni necesariamente los límites oficiales de todas las revisiones de G1. La temperatura ambiente mínima/máxima de operación no quedó confirmada con fuentes públicas primarias en esta consulta.

Fuente de referencia de código: [terminaciones de seguridad en `unitree_sdk2`](https://github.com/unitreerobotics/unitree_sdk2/blob/main/include/unitree/robot/g1/common/terminations.hpp).

## 5. Alimentación, consumo y autonomía

| Parámetro | Dato publicado |
|---|---|
| Tipo de batería | Litio, 13 celdas en serie (13S) |
| Capacidad nominal | 9000 mAh (9 Ah) |
| Cargador | 54 V, 5 A |
| Autonomía anunciada | Aproximadamente 2 horas |
| Batería | Inteligente y de extracción rápida |

Fuente: [página oficial G1](https://www.unitree.com/g1/).

### Qué puede y qué no puede deducirse

- La capacidad publicada de 9 Ah no basta para calcular con precisión la energía utilizable si no se conoce la tensión nominal exacta del paquete y las condiciones de descarga. Para un cálculo energético formal se necesita la ficha de la batería.
- No se publica en la tabla una curva de consumo en función de marcha, carrera, manipulación, cómputo adicional o temperatura.
- Por eso, **no hay un único consumo en vatios** ni una autonomía garantizada para todas las tareas.
- Para medir consumo real, registrar simultáneamente tensión y corriente de batería/BMS, tarea, masa transportada, duración, estado de batería y temperaturas. Promediar `P(t)=V(t)×I(t)` y reportar Wh por tarea.
- El cargador de 54 V/5 A no implica que el robot consuma 5 A de forma constante.

## 6. Sensores

### 6.1 Sensores indicados en la página oficial

- Cámara de profundidad.
- LiDAR 3D.
- IMU, visible en las interfaces de estado/ejemplos de software.
- Doble encoder por articulación.
- Matriz de cuatro micrófonos.
- Altavoz de 5 W.
- Wi-Fi 6 y Bluetooth 5.2.
- Según la interfaz/configuración de software: estado BMS, temperaturas y estado de articulaciones; algunos mensajes/variantes exponen fuerzas de pie medidas o estimadas.

La tabla comercial no fija en todos los casos fabricante, modelo exacto, rango, resolución, precisión ni frecuencia de cada sensor. Esos datos pueden variar por revisión y lote; deben extraerse del inventario de la unidad o de su manual específico.

### 6.2 Cómo acceder a los datos

**Primera vía recomendada:** usar los ejemplos y mensajes de la versión de SDK/ROS 2 que corresponde al G1 concreto.

- Consultar `LowState` para IMU y estados articulares.
- En el ejemplo oficial ROS 2, inspeccionar los topics disponibles con `ros2 topic list` y examinar el tipo de mensaje con `ros2 topic info`/`ros2 interface show` en el entorno ROS 2 del robot.
- El ejemplo G1 publica comandos en `/lowcmd` y se suscribe a `lowstate` o `lf/lowstate`, según configuración.
- Los datos de cámara y LiDAR pueden usar controladores/topics separados del estado articular; no asumir que están contenidos en `LowState`. Verificar topics, paquetes y nombres reales de la unidad.

Fuente: [documentación y ejemplos `unitree_ros2`](https://github.com/unitreerobotics/unitree_ros2).

**No se debe asumir** que la IMU del torso y una segunda IMU, si existe en cierta revisión, tienen el mismo topic, marco de coordenadas, calibración o frecuencia. Registrar el nombre de topic, tipo de mensaje, frame, unidades y timestamp antes de usarlo en RL.

## 7. Variantes del producto y del modelo de software

### 7.1 Variantes comerciales (familia G1)

- **G1:** configuración de catálogo de 23 DoF, sin algunas opciones de desarrollo/manos descritas para EDU.
- **G1 EDU:** plataforma de desarrollo; catálogo de 23–43 DoF según cintura, muñecas y manos, con desarrollo secundario anunciado.
- **G1 con manos dexterous:** el número de DoF y las interfaces dependen de la mano instalada.
- **G1+:** producto actualizado con cambios de percepción, articulaciones y alimentación/uso continuo. No tratarlo como idéntico al G1 clásico.
- **G1 Comp / G1-Comp:** variante orientada a competición, con configuración específica.
- **G1-D:** plataforma de manipulación móvil distinta; no confundirla con el humanoide G1 bípedo estándar.

Fuentes oficiales:
- [G1](https://www.unitree.com/g1/)
- [G1+](https://www.unitree.com/G1pl/)
- [G1-Comp](https://www.unitree.com/robocup/)
- [G1-D](https://www.unitree.com/mobile/G1-D/)

### 7.2 Variantes en `unitree_rl_gym`

El repositorio incluye descripciones que sirven para diferentes tareas y configuraciones, por ejemplo:

- `g1_12dof.xml` / `g1_12dof.urdf`: modelo simplificado para control de piernas.
- `g1_29dof.xml` y variantes `g1_29dof_lock_waist`: cuerpo con articulaciones de cintura bloqueadas o no, según archivo.
- `g1_29dof_with_hand_rev_1_0.xml`: modelo de 29 DoF con descripciones de manos y límites de articulación específicos.
- URDF correspondientes y mallas visuales/colisión.

Fuente: [directorio oficial de modelos G1 en `unitree_rl_gym`](https://github.com/unitreerobotics/unitree_rl_gym/tree/main/resources/robots/g1_description).

**Importante para GIAR-ORION:** “29 DoF” en el nombre de una descripción no garantiza que todas las articulaciones de manos estén contabilizadas de la misma manera en el controlador o que corresponda al hardware de una unidad determinada. La configuración física y el índice de cada motor se deben verificar contra el firmware/SDK entregado.

## 8. Árbol cinemático/dinámico y simulación

### 8.1 Estructura del modelo

En los modelos MJCF de MuJoCo, la jerarquía se expresa con elementos anidados `<worldbody>`, `<body>`, `<joint>`, `<geom>` e `<inertial>`. El URDF expresa la misma clase de estructura mediante `<link>`, `<joint>`, `<parent>`, `<child>`, `<origin>`, `<axis>`, `<limit>` e `<inertial>`.

El modelo de G1 contiene, según variante:

- pelvis como cuerpo central/base;
- cadenas de pierna izquierda y derecha: cadera pitch/roll/yaw, rodilla y tobillo pitch/roll;
- cintura y torso;
- cadenas de brazo: hombro pitch/roll/yaw, codo y muñeca;
- cabeza y enlaces de sensores/elementos visuales;
- enlaces y articulaciones de mano cuando esa variante los incluye.

Las articulaciones se conectan mediante transformaciones relativas. Cada cuerpo aporta masa, centro de masa e inercia; cada articulación define eje y rango. En MuJoCo, las mallas visuales y las geometrías de colisión pueden ser distintas. Una malla visual no debe confundirse con una colisión físicamente adecuada.

### 8.2 Parámetros a auditar antes de simular

Para el archivo exacto que se vaya a utilizar, extraer y validar:

1. número de cuerpos, articulaciones y actuadores;
2. nombres, orden e índices de motores;
3. padre/hijo de cada articulación;
4. transformaciones relativas y ejes;
5. rangos angulares y límites de esfuerzo por actuador;
6. masa, centro de masa e inercia de cada cuerpo;
7. colisiones, autocolisiones y geometrías respondibles;
8. articulaciones fijas o bloqueadas;
9. marcos de IMU y sensores;
10. convención de unidades (rad, N·m, kg, m) y signos.

No modificar límites físicos solo para evitar inestabilidades sin registrar el cambio. Un archivo de simulación puede incluir simplificaciones o límites de esfuerzo destinados al entrenamiento; no es automáticamente un certificado de equivalencia con el hardware.

### 8.3 Entornos de simulación encontrados en las fuentes oficiales

- **MuJoCo:** MJCF/XML de G1 en `unitree_rl_gym`; útil para dinámica, control y entrenamiento.
- **Isaac Gym / Isaac Lab y el stack de entrenamiento del repositorio:** el soporte exacto depende de la rama/versión del repositorio y sus dependencias; fijar commit y entorno antes de reproducir resultados.
- **CoppeliaSim:** no se identifica en las fuentes consultadas como simulador oficial principal de Unitree. En GIAR-ORION es una integración de terceros/proyecto. La equivalencia depende de cómo se importen las masas, inercias, ejes, actuadores, colisiones y control.
- **ROS 2:** capa de integración/control y telemetría; no es por sí misma un motor de física.

Fuente principal del modelo: [unitreerobotics/unitree_rl_gym](https://github.com/unitreerobotics/unitree_rl_gym).

## 9. Tabla de datos confirmados y pendientes

| Tema solicitado | Estado en fuentes consultadas | Qué usar/qué falta |
|---|---|---|
| Tamaño y masa total | Publicado por Unitree | 1320×450×200 mm, ~35 kg con batería; EDU ~35 kg+ |
| Masa de cada elemento físico | Parcial en URDF/MJCF como masa de eslabón modelado | No equivale necesariamente a masa de pieza real; pedir BOM/CAD oficial |
| Tipo de motor | Publicado de forma general | PMSM de imanes permanentes, rotor interior, baja inercia/alta velocidad |
| Par máximo | Publicado parcialmente | 90 N·m G1 / 120 N·m G1 EDU para rodilla según tabla; no generalizar |
| Límites angulares | Rangos comerciales + rangos por articulación en MJCF/URDF | Usar el archivo de la variante y validar con firmware |
| Doble encoder | Publicado | Posición/velocidad; detalles eléctricos y precisión por confirmar |
| IMU | Interfaz visible en SDK | Modelo físico exacto, ubicación y tasa deben verificarse |
| Cámara de profundidad y LiDAR 3D | Publicado | Modelo, FOV, rango, resolución, frecuencia: revisar lote/manual |
| Fuerza en pies | Algunos mensajes/variantes exponen valores | Confirmar si son sensores físicos o estimaciones en esa versión |
| Batería | 13S, 9000 mAh; cargador 54 V/5 A | Energía Wh y límites de corriente requieren ficha de batería |
| Autonomía | Aproximadamente 2 h | Depende de tarea; no es un consumo constante |
| Corriente máxima por motor | No confirmada públicamente | Solicitar ficha del actuador/driver |
| Tiempo de respuesta del motor | No confirmado como especificación general | 500 Hz es frecuencia de ejemplo, no tiempo de respuesta |
| Temperatura ambiente de operación | No confirmada en fuentes primarias consultadas | Manual de la revisión exacta |
| Umbrales de temperatura del código | Sí, en ejemplo SDK | 120 °C bobinado y 85 °C carcasa en una función de terminación; no confundir con temperatura ambiente |
| Software/control | SDK2, ROS 2, Explore App/manuales | Usar versión compatible con el firmware |
| Simulación | URDF/MJCF oficiales en repo RL | MuJoCo y stack de entrenamiento; CoppeliaSim requiere validación de importación |
| Árbol dinámico | Definido en URDF/MJCF | Extraerlo del archivo exacto y comparar con la unidad física |

## 10. Procedimiento recomendado para GIAR-ORION

1. **Fijar el objetivo físico:** registrar modelo comercial, EDU/no EDU, número de DoF, revisión de hardware/firmware, manos instaladas, módulo de cómputo y sensores.
2. **Fijar el modelo de simulación:** guardar URL, rama, commit y nombre exacto de URDF/MJCF; no mezclar archivos de revisiones distintas.
3. **Generar un inventario del modelo:** tabla de enlaces, masa, centro de masa, inercia, padre, articulación, eje, rango y esfuerzo máximo modelado.
4. **Auditar sensores:** inventariar topics y mensajes; registrar IMU(s), frames, unidades, frecuencia, timestamps, cámara y LiDAR.
5. **Auditar control:** confirmar mapeo índice↔nombre, modo de control, `q/dq/tau/kp/kd`, frecuencia de envío y límites de seguridad.
6. **Solicitar a Unitree/distribuidor los datos no públicos:** corriente continua/pico de cada actuador, curva par-velocidad, tiempo de respuesta, límites térmicos, temperaturas ambientales permitidas, ficha de batería y masa/BOM de cada conjunto.
7. **Validar simulación:** comparar postura de reposo, gravedad, masa total, centros de masa, límites articulares y respuesta a pequeñas órdenes seguras antes de entrenar políticas RL.

## 11. Fuentes primarias y técnicas

1. **Unitree Robotics — G1:** https://www.unitree.com/g1/
2. **Unitree Robotics — G1+ (modelo actualizado):** https://www.unitree.com/G1pl/
3. **Unitree Robotics — G1-Comp:** https://www.unitree.com/robocup/
4. **Unitree Robotics — G1-D:** https://www.unitree.com/mobile/G1-D/
5. **Unitree Explore App y manuales G1:** https://www.unitree.com/app/g1/
6. **`unitreerobotics/unitree_ros2`:** https://github.com/unitreerobotics/unitree_ros2
7. **Ejemplo de control de bajo nivel G1 en ROS 2:** https://github.com/unitreerobotics/unitree_ros2/blob/master/example/src/src/g1/lowlevel/g1_low_level_example.cpp
8. **`unitreerobotics/unitree_sdk2`:** https://github.com/unitreerobotics/unitree_sdk2
9. **Ejemplo de control de tobillo G1 y realimentación:** https://github.com/unitreerobotics/unitree_sdk2/blob/main/example/g1/low_level/g1_ankle_swing_example.cpp
10. **Umbrales de terminación/seguridad en el SDK:** https://github.com/unitreerobotics/unitree_sdk2/blob/main/include/unitree/robot/g1/common/terminations.hpp
11. **`unitreerobotics/unitree_rl_gym`:** https://github.com/unitreerobotics/unitree_rl_gym
12. **MJCF 29 DoF con manos:** https://github.com/unitreerobotics/unitree_rl_gym/blob/main/resources/robots/g1_description/g1_29dof_with_hand_rev_1_0.xml
13. **URDF 12 DoF:** https://github.com/unitreerobotics/unitree_rl_gym/blob/main/resources/robots/g1_description/g1_12dof.urdf
14. **URDF 29 DoF con cintura bloqueada:** https://github.com/unitreerobotics/unitree_rl_gym/blob/main/resources/robots/g1_description/g1_29dof_lock_waist_rev_1_0.urdf

## 12. Limitación de esta revisión

Este documento es un dossier de investigación con fuentes públicas consultadas, no reemplaza el manual suministrado con la unidad, la ficha técnica del actuador, la lista de materiales ni la documentación del firmware concreto. Los repositorios evolucionan; para reproducibilidad, registrar la fecha de consulta y fijar un commit. Cuando una especificación no aparece en una fuente primaria verificable, se deja como pendiente en lugar de inferirla.
