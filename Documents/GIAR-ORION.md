# GIAR-ORION

## Índice

1. [¿Qué queremos que pueda hacer GIAR-ORION?](#1-qué-queremos-que-pueda-hacer-giar-orion)
2. [Arquitectura general](#2-arquitectura-general)
3. [¿Cómo funcionará en tu computadora?](#3-cómo-funcionará-en-tu-computadora)
4. [Plan de desarrollo](#4-plan-de-desarrollo)
5. [¿Qué hará que GIAR-ORION sea diferente de un chatbot?](#5-qué-hará-que-giar-orion-sea-diferente-de-un-chatbot)
6. [Instalación y configuración de Ollama](#6-instalación-y-configuración-de-ollama)

### *Inteligencia artificial para investigación y desarrollo en robótica autónoma.*

GIAR-ORION será un agente de IA local, diseñado para trabajar como **investigador, ingeniero de software y especialista en aprendizaje por refuerzo aplicado a la robótica**.

La idea es que no se limite a responder preguntas: queremos que pueda analizar programas, estudiar documentación, ejecutar pruebas controladas, interpretar resultados y ayudarnos a mejorar los sistemas robóticos.

## 1. ¿Qué queremos que pueda hacer GIAR-ORION?

Dividiremos sus capacidades en seis áreas.

| Área | Capacidades previstas |
| --- | --- |
| 🧠 Inteligencia artificial | Comprender instrucciones, razonar sobre problemas técnicos y elaborar planes de trabajo. |
| 🤖 RL y DRL | Asistir en algoritmos SAC, PPO y otros métodos de aprendizaje por refuerzo. |
| 💻 Ingeniería de software | Analizar código Python, detectar errores, proponer cambios y ejecutar pruebas controladas. |
| 🔬 Investigación experimental | Examinar recompensas, pérdidas, políticas, métricas y resultados de entrenamiento. |
| 📚 Conocimiento técnico | Consultar documentación especializada de PyTorch, Unitree, MuJoCo y CoppeliaSim. |
| 🗣️ Voz y memoria | Mantener conversaciones por voz y registrar conocimientos, decisiones y experimentos relevantes. |

Estas son capacidades que desarrollaremos progresivamente, no funciones que Ollama proporcione automáticamente.

## 2. Arquitectura general

Propongo organizar GIAR-ORION en módulos independientes.

```text
                    GIAR-ORION
                         │
             ┌───────────┴───────────┐
             │                       │
       INTERFAZ HUMANA          ORQUESTADOR
             │                       │
       ┌─────┴─────┐       ┌─────────┼─────────┐
       │           │       │         │         │
      Voz        Texto   Memoria   Planificación Herramientas
                               │         │         │
                               └─────────┼─────────┘
                                         │
                                  MOTOR DE IA
                                      Ollama
                                         │
                                  Modelo de lenguaje
                                         │
                       ┌─────────────────┼────────────────┐
                       │                 │                │
                  Conocimiento       Análisis         Experimentos
                   especializado     de código        y resultados
                       │                 │                │
                       └─────────────────┼────────────────┘
                                         │
                               ENTORNOS DE ROBÓTICA
                                         │
                             ┌───────────┴───────────┐
                             │                       │
                         CoppeliaSim              MuJoCo
                             │                       │
                             └───────────┬───────────┘
                                         │
                                   Unitree G1
```

Este esquema representa la arquitectura objetivo. La conexión con los simuladores y el robot se incorporará cuando los módulos correspondientes estén implementados y validados.

**Una decisión de diseño importante:** GIAR-ORION será independiente del motor de lenguaje. Comenzaremos con Ollama, pero podremos sustituirlo por otra solución local sin reconstruir toda la arquitectura.

Además, el agente que razona y analiza los experimentos estará separado del controlador que ejecuta la política de movimiento del robot. Así evitaremos confundir las respuestas de un modelo de lenguaje con el control robótico en tiempo real.

---

## 3. ¿Cómo funcionará en tu computadora?

Tomaremos como referencia tu entorno actual:

- Windows 11.
- NVIDIA RTX 5070 Laptop con 8 GB de VRAM.
- 16 GB de RAM.
- Python y PyTorch.
- CoppeliaSim.
- Entorno de entrenamiento del Unitree G1.

La primera versión funcionará localmente.

Una vez descargados los modelos, las dependencias y la documentación necesaria, podremos trabajar sin conexión a Internet en las funciones que hayamos preparado para ese modo.

No necesitamos entrenar un modelo de lenguaje desde cero. Utilizaremos uno existente y construiremos alrededor de él los componentes que le darán sus capacidades especializadas.

### Una consideración sobre los recursos

Los 8 GB de VRAM y los 16 GB de RAM permiten comenzar con modelos cuantizados de tamaño moderado, aunque tendremos que verificar el consumo real.

También tendremos que evitar que el modelo de lenguaje consuma tanta memoria que perjudique los experimentos de PyTorch o CoppeliaSim.

Por eso, **la primera etapa será instalar el motor y validar el funcionamiento del modelo antes de construir el resto del agente**.

---

## 4. Plan de desarrollo

Propongo avanzar en siete etapas.

| Etapa | Desarrollo | Resultado esperado |
| --- | --- | --- |
| 1 | Instalación del motor local | Modelo de IA funcionando en Windows. |
| 2 | Agente básico en Python | Interfaz propia para conversar con el modelo. |
| 3 | Memoria y conocimientos | Consulta de documentación especializada y registro de información útil. |
| 4 | Herramientas de ingeniería | Lectura de código, análisis de errores y ejecución controlada de pruebas. |
| 5 | Especialización en RL y DRL | Asistencia técnica sobre algoritmos, entrenamiento y evaluación. |
| 6 | Integración con robótica | Herramientas para trabajar con CoppeliaSim, MuJoCo y Unitree G1. |
| 7 | Interfaz de voz | Reconocimiento de voz y respuestas habladas mediante componentes locales. |

Cada etapa tendrá pruebas de aceptación. No avanzaremos simplemente porque el programa se ejecute: comprobaremos que las funciones implementadas realmente trabajen como esperamos.

---

## 5. ¿Qué hará que GIAR-ORION sea diferente de un chatbot?

Pensemos en un problema concreto de tu entrenamiento SAC.

Supongamos que el robot no mejora su recompensa después de numerosos episodios.

Un chatbot podría explicar las posibles causas.

GIAR-ORION, cuando hayamos implementado y autorizado las herramientas necesarias, podría seguir un procedimiento más completo:

1. Examinar los registros de entrenamiento.
2. Analizar las curvas de recompensa y las pérdidas del actor y los críticos.
3. Revisar los parámetros de configuración de SAC.
4. Contrastar los resultados con el código del entorno y la función de recompensa.
5. Formular hipótesis sobre las causas de la falta de convergencia.
6. Proponer experimentos para comprobar esas hipótesis.
7. Ejecutar pruebas controladas y analizar sus resultados.
8. Registrar los resultados para comparar futuras ejecuciones.

No supondrá que una hipótesis es correcta simplemente porque parezca razonable. Deberá contrastarla con los datos y distinguir entre los problemas confirmados y las posibilidades que todavía necesitan pruebas.

Las modificaciones importantes de código y los experimentos que puedan afectar a tus archivos o entrenamientos requerirán controles y autorización.

Ese es el salto que buscamos: pasar de un sistema que responde preguntas a uno que **participa de manera estructurada en el proceso de investigación y desarrollo**.

---

## 6. Instalación y configuración de Ollama

No intentaremos desarrollar todo GIAR-ORION de una sola vez.

El primer hito será:

**GIAR-ORION 0.1 — Motor local operativo.**

Esta versión inicial deberá cumplir tres condiciones:

- Ollama instalado y funcionando en Windows.
- Un modelo de lenguaje seleccionado y probado con tu hardware.
- Capacidad para responder preguntas técnicas sin depender de una conexión a Internet, una vez preparado el entorno.

Después construiremos el agente en Python, manteniendo separados el motor de lenguaje, la memoria, el conocimiento especializado y las herramientas.
