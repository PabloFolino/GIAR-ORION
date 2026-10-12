# Aprendizaje por Refuerzo (Reinforcement Learning, RL)

## Fundamentos, formulación matemática, algoritmos, historia, aplicaciones en robótica y ejemplos en Python

**Documento técnico para GIAR-ORION**\
**Versión:** 1.0\
**Fecha:** 12 de octubre de 2026\
**Idioma:** español\
**Objetivo:** ofrecer una referencia de estudio profunda y trazable
sobre aprendizaje por refuerzo (RL), desde las definiciones esenciales
hasta los algoritmos modernos de Deep RL, con especial atención al
control de robots.

------------------------------------------------------------------------

## 0. Cómo leer este documento y de dónde proviene la información

Este documento es una síntesis técnica construida a partir de
bibliografía académica y documentación técnica identificable. No es una
transcripción de una única fuente. Para facilitar la trazabilidad, las
ideas principales se agrupan según su origen:

  -----------------------------------------------------------------------
  Etiqueta                Tipo de fuente          Uso en este documento
  ----------------------- ----------------------- -----------------------
  **\[SB\]**              Sutton y Barto,         Fundamentos, procesos
                          *Reinforcement          de decisión de Markov,
                          Learning: An            retorno, funciones de
                          Introduction*, 2.ª      valor, programación
                          edición (2018)          dinámica, Monte Carlo,
                                                  TD, elegibilidad y
                                                  evolución histórica.

  **\[Spinning Up\]**     OpenAI, *Spinning Up in Terminología moderna,
                          Deep RL*                retorno, políticas,
                                                  trayectorias, familias
                                                  de algoritmos y
                                                  conexión entre teoría y
                                                  código.

  **\[Watkins\]**         Watkins (1989), tesis   Desarrollo histórico y
                          sobre Q-learning        fundamento de
                                                  Q-learning.

  **\[Williams\]**        Williams (1992),        Fundamentos de
                          artículo sobre          gradientes de política.
                          REINFORCE               

  **\[DQN\]**             Mnih et al. (2015),     Hito de Deep RL con
                          *Nature*                redes profundas y
                                                  juegos Atari.

  **\[AlphaGo\]**         Silver et al. (2016),   Redes de política y
                          *Nature*                valor, búsqueda y
                                                  aprendizaje por
                                                  autojuego.

  **\[PPO\]**             Schulman et al. (2017), Optimización de
                          artículo sobre Proximal políticas y
                          Policy Optimization     entrenamiento estable
                                                  por lotes.

  **\[SAC\]**             Haarnoja et al. (2018), Máxima entropía y
                          artículos de Soft       control continuo
                          Actor-Critic            off-policy.
  -----------------------------------------------------------------------

Las referencias completas y enlaces están en la sección 19. Los ejemplos
de código, escenarios de robot y recomendaciones operativas son
**material didáctico elaborado para este documento**; no se atribuyen
literalmente a una fuente externa. Cuando se da una regla práctica o un
ejemplo numérico, se presenta como ilustración y no como resultado
experimental universal.

------------------------------------------------------------------------

# PARTE I. CONCEPTOS FUNDAMENTALES

## 1. ¿Qué es el aprendizaje por refuerzo?

El **aprendizaje por refuerzo** (*Reinforcement Learning*, RL) es un
área del aprendizaje automático en la que un agente aprende a tomar
decisiones mediante la interacción con un entorno. El agente ejecuta
acciones, observa sus consecuencias y recibe una señal de recompensa. El
objetivo es aprender una conducta que maximice la recompensa acumulada a
lo largo del tiempo. \[SB, Spinning Up\]

La diferencia fundamental respecto del aprendizaje supervisado es que
normalmente no se proporciona una etiqueta correcta para cada decisión.
El agente debe descubrir qué acciones conducen a mejores resultados, y
las consecuencias de una acción pueden aparecer muchos pasos después.

### Ejemplo sencillo

Un robot móvil debe llegar a una posición objetivo sin chocar:

-   Si avanza en la dirección correcta, puede recibir una recompensa
    positiva.
-   Si se aleja del objetivo, la recompensa puede ser menor.
-   Si choca, puede recibir una penalización y finalizar el episodio.
-   Si llega al destino, recibe una recompensa de éxito.

El algoritmo no recibe necesariamente una demostración de cada
movimiento correcto. Aprende a partir de la experiencia.

### Qué aprende y qué no aprende automáticamente

RL puede aprender una política de decisión, pero **no define por sí
mismo qué significa el éxito**. La tarea, las observaciones, las
acciones, las recompensas, las condiciones de terminación y los límites
físicos deben diseñarse correctamente.

Una recompensa mal formulada puede enseñar un comportamiento que
maximiza la cifra registrada y, aun así, incumple la intención del
diseñador. Por eso la validación del entorno y de la recompensa es parte
central del trabajo.

## 2. Componentes del problema de RL

### 2.1 Agente

El **agente** es el sistema que decide qué acción ejecutar. Puede ser un
programa sencillo, una tabla de valores o una red neuronal.

En robótica, el agente puede contener una política neuronal que
convierte el estado estimado del robot en consignas de posición,
velocidad o torque.

### 2.2 Entorno

El **entorno** es aquello con lo que interactúa el agente. Puede ser un
simulador, un videojuego, un banco experimental o un robot real.

El entorno recibe la acción y devuelve una nueva observación, una
recompensa y señales que indican si el episodio terminó.

### 2.3 Estado y observación

El **estado** (s_t) es una descripción suficiente de la situación del
entorno para modelar su evolución. La **observación** (o_t) es la
información que el agente realmente recibe. \[SB, Spinning Up\]

Si el agente conoce todo el estado relevante, el problema puede
modelarse como totalmente observado. Si sólo recibe una parte ---por
ejemplo, una cámara sin profundidad o sensores ruidosos---, el problema
es parcialmente observado.

En un humanoide, un vector de observación podría incluir:

-   orientación y velocidad angular del torso;
-   velocidad lineal estimada;
-   posiciones y velocidades de las articulaciones;
-   contactos de los pies;
-   altura del torso;
-   objetivo de movimiento;
-   acciones anteriores.

El estado y la observación no deben confundirse en un sistema real. A
veces la documentación usa (s) por simplicidad aunque el agente sólo
tenga acceso a (o).

### 2.4 Acción

La **acción** (a_t) es la decisión del agente en el instante (t).

Ejemplos: - mover un robot móvil hacia adelante; - elegir izquierda o
derecha en un entorno discreto; - ordenar una posición articular; -
enviar un vector de torques; - seleccionar una velocidad objetivo.

El conjunto de acciones posibles se denota (`\mathcal `{=tex}A). Puede
ser discreto o continuo.

### 2.5 Recompensa

La **recompensa** (r_t) es una señal numérica que evalúa el resultado
inmediato de una transición. En la formulación estándar, es un escalar:

\[ r_t `\in `{=tex}`\mathbb `{=tex}R \]

Puede ser positiva, negativa o cero. No es necesariamente dinero,
puntuación ni una medida física: es una señal diseñada para orientar el
aprendizaje.

### 2.6 Política

La **política** (`\pi`{=tex}) especifica cómo el agente elige acciones.

Para una política determinista:

\[ a_t=`\pi`{=tex}(s_t) \]

Para una política estocástica:

\[ a_t`\sim`{=tex}`\pi`{=tex}(`\cdot`{=tex}`\mid `{=tex}s_t) \]

La política puede ser una tabla, una regla programada o una red
neuronal. Aprender RL significa, en términos generales, mejorar esta
política a partir de experiencia.

### 2.7 Transición y dinámica

La dinámica describe cómo cambia el entorno después de una acción.

En un entorno determinista:

\[ s\_{t+1}=f(s_t,a_t) \]

En uno estocástico:

\[ s\_{t+1}`\sim `{=tex}P(`\cdot`{=tex}`\mid `{=tex}s_t,a_t) \]

En simulación física, la dinámica puede estar definida por un motor de
física y por modelos de sensores y actuadores.

### 2.8 Episodio y trayectoria

Un **episodio** es una secuencia de interacción desde un estado inicial
hasta una condición de finalización o un límite de tiempo.

Una **trayectoria** puede escribirse:

\[ `\tau`{=tex}=(s_0,a_0,r_0,s_1,a_1,r_1,`\ldots`{=tex},s_T) \]

En documentación técnica también se usan los términos *rollout* y
*trajectory*.

### 2.9 Retorno

El **retorno** (G_t) es la suma de las recompensas futuras, normalmente
descontadas:

\[ G_t=`\sum`{=tex}*{k=0}^{T-t-1}`\gamma`{=tex}^k r*{t+k} \]

El parámetro (`\gamma`{=tex}) es el **factor de descuento**, con
(0`\leq`{=tex}`\gamma`{=tex}`\leq1`{=tex}). Si el horizonte es infinito,
se suele exigir (`\gamma`{=tex}\<1) para que el retorno esté bien
definido bajo condiciones habituales.

-   Un (`\gamma`{=tex}) menor enfatiza más las recompensas próximas.
-   Un (`\gamma`{=tex}) cercano a 1 da más importancia a recompensas
    lejanas.
-   En episodios finitos, el tratamiento del final debe ser coherente
    con la definición de la tarea.

### 2.10 Exploración y explotación

El agente debe equilibrar dos objetivos:

-   **Exploración:** probar acciones para aprender qué sucede.
-   **Explotación:** elegir acciones que, según lo aprendido, parecen
    mejores.

Si sólo explota desde el principio, puede quedarse con una política
mediocre. Si explora indefinidamente, puede no consolidar una conducta
útil.

La forma de resolver este compromiso depende del algoritmo: exploración
(`\epsilon`{=tex})-greedy, políticas estocásticas, ruido de acción,
entropía, modelos de incertidumbre u otros métodos.

------------------------------------------------------------------------

## 3. Formulación matemática: proceso de decisión de Markov

Muchos problemas de RL se modelan como un **Proceso de Decisión de
Markov** (*Markov Decision Process*, MDP). Una notación común es:

\[
`\mathcal `{=tex}M=(`\mathcal `{=tex}S,`\mathcal `{=tex}A,P,R,`\gamma`{=tex},`\rho`{=tex}\_0)
\]

donde:

-   (`\mathcal `{=tex}S): espacio de estados;
-   (`\mathcal `{=tex}A): espacio de acciones;
-   (P(s'`\mid `{=tex}s,a)): probabilidad de transición;
-   (R(s,a,s')): recompensa;
-   (`\gamma`{=tex}): factor de descuento;
-   (`\rho`{=tex}\_0): distribución de estados iniciales.

La propiedad de Markov expresa que, si el estado está definido de manera
adecuada, la distribución del siguiente estado depende del estado actual
y de la acción actual, no de toda la historia:

\[ P(s\_{t+1}`\mid `{=tex}s_t,a_t,s\_{t-1},a\_{t-1},`\ldots`{=tex})
=P(s\_{t+1}`\mid `{=tex}s_t,a_t) \]

Esto no significa que el mundo no tenga historia física. Significa que
el estado debe incluir la información necesaria para resumirla.

### 3.1 Qué ocurre si el estado no es Markoviano

Si la observación omite variables importantes ---por ejemplo, velocidad
cuando sólo se registra posición---, dos observaciones iguales pueden
conducir a evoluciones distintas. Algunas soluciones son añadir
variables, utilizar una ventana temporal o incorporar una red
recurrente. Estas alternativas no garantizan por sí solas resolver toda
observación parcial.

### 3.2 MDP frente a POMDP

Un **Proceso de Decisión de Markov Parcialmente Observable** (*POMDP*)
modela explícitamente que el agente no conoce el estado real y recibe
observaciones con una distribución condicionada al estado.

En un POMDP se puede razonar sobre una creencia (b_t(s)), una
distribución sobre los estados posibles. En la práctica, un agente puede
aproximar esa información mediante filtros, estimadores de estado,
historial de observaciones o redes recurrentes.

------------------------------------------------------------------------

# PARTE II. OBJETIVOS Y FUNCIONES DE VALOR

## 4. ¿Qué optimiza RL?

La meta habitual es maximizar el retorno esperado de la política:

\[
J(`\pi`{=tex})=`\mathbb `{=tex}E\_{`\tau`{=tex}`\sim`{=tex}`\pi`{=tex}}\[G_0\]
=`\mathbb `{=tex}E\_{`\tau`{=tex}`\sim`{=tex}`\pi`{=tex}}`\left[\sum_{t=0}^{T-1}\gamma^t r_t\right]`{=tex}\]

La expectativa aparece porque puede haber aleatoriedad en los estados
iniciales, las transiciones o las acciones.

El objetivo no es necesariamente obtener la mayor recompensa en un paso.
Una acción con recompensa inmediata baja puede ser conveniente si
permite alcanzar una situación que genere más recompensa en el futuro.

## 5. Función de valor de estado

La función (V\^`\pi`{=tex}(s)) representa el retorno esperado si el
agente empieza en (s) y luego sigue la política (`\pi`{=tex}):

\[ V\^`\pi`{=tex}(s)=`\mathbb `{=tex}E\_`\pi[G_t\mid s_t=s]`{=tex}\]

La ecuación de Bellman para una política es:

\[ V\^`\pi`{=tex}(s)=`\sum`{=tex}*a`\pi`{=tex}(a`\mid `{=tex}s)
`\sum`{=tex}*{s'}P(s'`\mid `{=tex}s,a)
`\left[R(s,a,s')+\gamma V^\pi(s')\right]`{=tex}\]

Para espacios continuos, las sumas se sustituyen por integrales cuando
corresponde.

## 6. Función de valor de acción

La función (Q\^`\pi`{=tex}(s,a)) representa el retorno esperado al
ejecutar primero (a) en (s) y luego seguir (`\pi`{=tex}):

\[ Q\^`\pi`{=tex}(s,a)=
`\mathbb `{=tex}E\_`\pi[G_t\mid s_t=s,a_t=a]`{=tex}\]

La relación entre (V) y (Q) es:

\[
V\^`\pi`{=tex}(s)=`\sum`{=tex}\_a`\pi`{=tex}(a`\mid `{=tex}s)Q\^`\pi`{=tex}(s,a)
\]

En espacios de acción continuos, la suma se convierte en una integral.

La función (Q) ayuda a comparar acciones en una situación. No es una
probabilidad ni una recompensa inmediata: es una estimación del retorno
futuro.

## 7. Función de ventaja

La ventaja indica cuánto mejor o peor es una acción respecto del valor
habitual de ese estado:

\[ A^`\pi`{=tex}(s,a)=Q^`\pi`{=tex}(s,a)-V\^`\pi`{=tex}(s) \]

-   (A\^`\pi`{=tex}(s,a)\>0): la acción es mejor que el promedio
    esperado bajo la política.
-   (A\^`\pi`{=tex}(s,a)\<0): es peor que ese promedio.
-   (A\^`\pi`{=tex}(s,a)`\approx0`{=tex}): su valor estimado está cerca
    del promedio.

Las ventajas se utilizan en muchos algoritmos de gradiente de política,
entre ellos PPO.

## 8. Ecuación de Bellman óptima

La función de valor óptima satisface:

\[ V\^\*(s)=`\max`{=tex}*a`\sum`{=tex}*{s'}P(s'`\mid `{=tex}s,a)
`\left[R(s,a,s')+\gamma V^*(s')\right]`{=tex}\]

Para el valor de acción:

\[ Q\^\*(s,a)=`\sum`{=tex}\_{s'}P(s'`\mid `{=tex}s,a)
`\left[R(s,a,s')+\gamma\max_{a'}Q^*(s',a')\right]`{=tex}\]

Estas ecuaciones expresan una idea central: el valor de una decisión
depende de su recompensa inmediata y del valor futuro que permite
alcanzar.

En muchos entornos reales, la dinámica y los espacios son demasiado
grandes para calcular exactamente estas funciones. Por eso se usan
métodos de aproximación, muestreo y redes neuronales.

------------------------------------------------------------------------

# PARTE III. FAMILIAS DE ALGORITMOS

## 9. Programación dinámica, Monte Carlo y aprendizaje temporal

Sutton y Barto presentan estas familias como partes fundamentales de la
historia y la estructura conceptual de RL. \[SB\]

### 9.1 Programación dinámica (DP)

Los métodos de programación dinámica utilizan un modelo conocido de las
transiciones y recompensas. Ejemplos: evaluación iterativa de políticas
e iteración de valor.

Ventaja: pueden resolver MDP pequeños de forma sistemática.\
Limitación: suelen requerir un modelo del entorno y operaciones sobre
estados, lo que resulta inviable en espacios enormes o continuos.

### 9.2 Monte Carlo (MC)

Los métodos Monte Carlo estiman retornos a partir de episodios completos
o segmentos adecuados. Por ejemplo, después de observar el retorno
(G_t), se actualiza una estimación de valor hacia ese retorno.

Una forma simple es:

\[
V(s_t)`\leftarrow `{=tex}V(s_t)+`\alpha`{=tex}\_{`\text{lr}`{=tex}}\[G_t-V(s_t)\]
\]

donde (`\alpha`{=tex}\_{`\text{lr}`{=tex}}) es la tasa de aprendizaje,
distinta conceptualmente del factor de descuento (`\gamma`{=tex}).

Ventaja: no requiere conocer las probabilidades de transición.\
Limitación: para el retorno completo puede necesitar esperar al final
del episodio y tener alta varianza.

### 9.3 Temporal-Difference (TD)

Los métodos TD actualizan una estimación usando otra estimación
aprendida, sin esperar necesariamente al final del episodio. Una
actualización TD(0) para el valor es:

\[ V(s_t)`\leftarrow `{=tex}V(s_t)+`\alpha`{=tex}\_{`\text{lr}`{=tex}}
`\left[r_t+\gamma V(s_{t+1})-V(s_t)\right]`{=tex}\]

El término entre corchetes es el **error TD**:

\[ `\delta`{=tex}*t=r_t+`\gamma `{=tex}V(s*{t+1})-V(s_t) \]

La idea se denomina *bootstrapping*: una estimación se actualiza usando
otra estimación.

### 9.4 Diferencia intuitiva

-   DP: aprende o calcula usando un modelo explícito.
-   MC: aprende de retornos observados en trayectorias.
-   TD: combina recompensa observada con estimaciones de valor futuras.

Son conceptos fundamentales que reaparecen dentro de muchos algoritmos
modernos.

## 10. Q-learning

Q-learning es un algoritmo TD off-policy que aprende una función de
valor de acción óptima sin requerir que la política de comportamiento
sea la misma política que se evalúa. \[Watkins, SB\]

La actualización tabular es:

\[
Q(s_t,a_t)`\leftarrow `{=tex}Q(s_t,a_t)+`\alpha`{=tex}\_{`\text{lr}`{=tex}}
`\left[
r_t+\gamma\max_{a'}Q(s_{t+1},a')-Q(s_t,a_t)
\right]`{=tex}\]

La expresión objetivo es:

\[ y_t=r_t+`\gamma`{=tex}(1-d_t)`\max`{=tex}*{a'}Q(s*{t+1},a') \]

donde (d_t=1) si la transición termina realmente el episodio. La máscara
debe adaptarse a la semántica del entorno.

### 10.1 ¿Qué significa off-policy?

La acción que genera los datos puede proceder de una política
exploratoria, mientras que el objetivo usa la acción futura con mayor Q
estimado. Por ejemplo, el agente explora con (`\epsilon`{=tex})-greedy,
pero el objetivo de Q-learning usa el máximo sobre las acciones
siguientes.

### 10.2 SARSA

SARSA es un método TD on-policy. Su actualización utiliza la siguiente
acción realmente elegida por la política de comportamiento:

\[
Q(s_t,a_t)`\leftarrow `{=tex}Q(s_t,a_t)+`\alpha`{=tex}\_{`\text{lr}`{=tex}}
`\left[
r_t+\gamma Q(s_{t+1},a_{t+1})-Q(s_t,a_t)
\right]`{=tex}\]

La diferencia principal frente a Q-learning es el término futuro: SARSA
usa (Q(s\_{t+1},a\_{t+1})), mientras que Q-learning usa
(`\max`{=tex}*{a'}Q(s*{t+1},a')).

### 10.3 Ejemplo de Q-learning tabular en Python

El ejemplo siguiente resuelve un entorno de cuadrícula pequeño creado
para fines didácticos. No utiliza librerías externas ni representa un
robot físico.

``` python
import numpy as np
import random

# Cuadrícula 5x5. Inicio (0,0), objetivo (4,4).
N = 5
N_STATES = N * N
ACTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # arriba, abajo, izq., der.
N_ACTIONS = len(ACTIONS)

def state_id(pos):
    return pos[0] * N + pos[1]

def step(pos, action_idx):
    dr, dc = ACTIONS[action_idx]
    r = min(max(pos[0] + dr, 0), N - 1)
    c = min(max(pos[1] + dc, 0), N - 1)
    next_pos = (r, c)

    reached_goal = next_pos == (N - 1, N - 1)
    reward = 10.0 if reached_goal else -1.0
    return next_pos, reward, reached_goal

Q = np.zeros((N_STATES, N_ACTIONS), dtype=np.float32)

learning_rate = 0.1
gamma = 0.95
epsilon = 1.0
epsilon_min = 0.05
epsilon_decay = 0.995
episodes = 3000
max_steps = 100

for episode in range(episodes):
    pos = (0, 0)

    for _ in range(max_steps):
        s = state_id(pos)

        if random.random() < epsilon:
            action = random.randrange(N_ACTIONS)
        else:
            action = int(np.argmax(Q[s]))

        next_pos, reward, terminated = step(pos, action)
        ns = state_id(next_pos)

        # En el objetivo no se suma valor futuro.
        next_value = 0.0 if terminated else np.max(Q[ns])
        target = reward + gamma * next_value

        Q[s, action] += learning_rate * (target - Q[s, action])
        pos = next_pos

        if terminated:
            break

    epsilon = max(epsilon_min, epsilon * epsilon_decay)

print("Valores Q aprendidos para el estado inicial:")
print(Q[state_id((0, 0))])
```

**Qué enseña el ejemplo:** - el agente explora al principio y luego
reduce la exploración; - la tabla Q almacena un valor por estado y
acción; - el objetivo combina recompensa inmediata y mejor valor futuro
estimado; - la recompensa de llegada es escalar.

No debe confundirse este ejemplo tabular con Deep RL: no hay red
neuronal ni Replay Buffer.

## 11. Deep Reinforcement Learning (Deep RL)

Deep RL combina algoritmos de RL con redes neuronales profundas para
representar políticas o funciones de valor en espacios grandes.
\[Spinning Up\]

En RL tabular, cada estado o par estado-acción puede tener una entrada
separada. En un robot complejo hay demasiados estados posibles para
guardar una tabla. Una red neuronal puede aproximar una función:

\[ Q\_`\phi`{=tex}(s,a)`\approx `{=tex}Q\^\*(s,a) \]

o una política:

\[ `\pi`{=tex}\_`\theta`{=tex}(a`\mid `{=tex}s) \]

Los parámetros (`\phi`{=tex}) o (`\theta`{=tex}) se ajustan mediante
optimización basada en gradientes.

### 11.1 Qué aporta una red neuronal

-   Generalización entre estados parecidos.
-   Capacidad de procesar vectores de sensores, imágenes u otras
    entradas.
-   Representación de políticas y valores no lineales.

### 11.2 Qué complica

-   Entrenamiento más inestable que una tabla pequeña.
-   Mayor demanda de cómputo y memoria.
-   Sensibilidad a escalas, hiperparámetros y calidad de datos.
-   Necesidad de evaluación con varias semillas y condiciones.
-   Posibilidad de sobreajuste al simulador o a la distribución de
    entrenamiento.

### 11.3 DQN

Deep Q-Network (DQN) combina Q-learning con una red neuronal y
popularizó el uso de RL profundo en videojuegos Atari. El trabajo de
Mnih et al. publicado en *Nature* en 2015 mostró que un mismo enfoque
podía aprender a jugar numerosos juegos a partir de píxeles. \[DQN\]

DQN suele usar: - una red Q online; - una red Q objetivo; - un Replay
Buffer; - exploración (`\epsilon`{=tex})-greedy.

Es especialmente natural para acciones discretas. No es la elección
directa más habitual para controlar un vector continuo de torques.

### 11.4 Gradientes de política

Los métodos de gradiente de política optimizan directamente los
parámetros de una política estocástica. Una forma general del gradiente
es:

\[ `\nabla`{=tex}*`\theta `{=tex}J(`\theta`{=tex})=
`\mathbb `{=tex}E*{`\tau`{=tex}`\sim`{=tex}`\pi`{=tex}\_`\theta`{=tex}}
`\left[
\sum_t \nabla_\theta\log\pi_\theta(a_t\mid s_t)\,G_t
\right]`{=tex}\]

La idea de REINFORCE fue desarrollada formalmente por Williams (1992).
\[Williams\]

Una desventaja básica es la varianza: las estimaciones del gradiente
pueden fluctuar mucho. Los baselines y los críticos ayudan a reducirla.

### 11.5 Actor-crítico

Los métodos actor-crítico combinan: - un actor, que aprende la
política; - un crítico, que estima valor o ventaja para orientar la
actualización del actor.

El crítico puede disminuir la varianza respecto de usar directamente el
retorno completo. Sin embargo, un crítico incorrecto también puede
introducir sesgo o desestabilizar el aprendizaje.

------------------------------------------------------------------------

# PARTE IV. TAXONOMÍA Y ALGORITMOS MODERNOS

## 12. Cómo clasificar algoritmos de RL

No existe una sola clasificación. Los siguientes ejes son independientes
y ayudan a entender las diferencias.

### 12.1 Basado en modelo vs. libre de modelo

**Model-based RL:** utiliza o aprende un modelo de la dinámica para
planificar o generar datos.

**Model-free RL:** aprende políticas o valores sin depender de un modelo
explícito de transición durante la toma de decisiones.

Un simulador físico puede ser un modelo del mundo usado para generar
experiencia, pero eso no convierte automáticamente al algoritmo de
aprendizaje en model-based RL. Hay que distinguir el simulador del
modelo aprendido que utiliza el agente para planificar.

### 12.2 Basado en valor vs. basado en política

**Value-based:** aprende valores de estados o acciones y deriva una
política de ellos. Q-learning y DQN son ejemplos.

**Policy-based:** optimiza directamente los parámetros de la política.
REINFORCE es un ejemplo.

**Actor-crítico:** combina política y valor. SAC, PPO en su formulación
actor-crítico y muchos métodos continuos pertenecen a esta familia, con
diferencias importantes en cómo aprenden y actualizan sus componentes.

### 12.3 On-policy vs. off-policy

**On-policy:** aprende principalmente con datos generados por la
política que se está optimizando o una versión muy próxima. PPO es un
ejemplo típico.

**Off-policy:** puede aprender con datos de una política de
comportamiento distinta y reutilizar experiencias pasadas. Q-learning,
DQN y SAC son ejemplos habituales.

La clasificación práctica depende de la formulación exacta. Las
variantes y las implementaciones pueden tener detalles adicionales.

### 12.4 Acciones discretas vs. continuas

-   **Discretas:** elegir una de un conjunto finito, como
    izquierda/derecha.
-   **Continuas:** elegir valores reales, como velocidades o torques.
-   **Híbridas:** combinación de decisiones discretas y parámetros
    continuos.

Para un humanoide con decenas de articulaciones, el espacio de acción
suele ser continuo y multidimensional. SAC, TD3 o PPO continuo son
familias comunes que se evalúan para ese tipo de problema, pero la
elección depende del entorno.

### 12.5 Online RL, offline RL y aprendizaje por demostración

-   **Online RL:** el agente interactúa con el entorno durante el
    entrenamiento.
-   **Offline RL:** aprende de un conjunto fijo de datos, sin obtener
    nuevas transiciones durante el aprendizaje.
-   **Imitation learning:** aprende a reproducir acciones de
    demostraciones; puede combinarse con RL.
-   **RL desde demostraciones:** usa datos de expertos para inicializar
    o complementar el aprendizaje por recompensa.

Offline RL no es simplemente ejecutar SAC con el entorno desconectado.
Reutilizar un dataset fijo requiere considerar el desajuste entre las
acciones presentes en los datos y las acciones que el agente quiere
evaluar.

### 12.6 RL de un agente y multiagente

En RL de un agente se modela un decisor principal. En RL multiagente
varios agentes toman decisiones e interactúan, y la recompensa puede ser
individual o compartida. La interacción entre políticas hace que el
problema pueda cambiar durante el entrenamiento.

------------------------------------------------------------------------

## 13. PPO, DDPG, TD3 y SAC: comparación conceptual

  ------------------------------------------------------------------------------------
  Algoritmo      Familia / datos  Uso típico      Idea principal     Precaución
  -------------- ---------------- --------------- ------------------ -----------------
  Q-learning     Basado en valor, Estados y       Actualización TD   La tabla no
                 off-policy,      acciones        con máximo futuro  escala a estados
                 tabla            discretas                          enormes.
                                  pequeños                           

  DQN            Basado en valor, Acciones        Red Q + buffer +   No controla
                 off-policy, Deep discretas con   red objetivo       directamente
                 RL               observaciones                      acciones
                                  complejas                          continuas sin
                                                                     adaptar el
                                                                     problema.

  REINFORCE      Gradiente de     Enseñanza de    Gradiente de       Alta varianza en
                 política,        políticas       log-probabilidad   las estimaciones.
                 normalmente      estocásticas    ponderado por      
                 on-policy                        retorno            

  PPO            Actor-crítico,   Amplia gama de  Limita cambios de  Suele necesitar
                 normalmente      tareas,         política mediante  datos nuevos de
                 on-policy        incluido        un objetivo        la política y
                                  control         recortado          descarta
                                  continuo                           reutilización
                                                                     amplia del
                                                                     buffer.

  DDPG           Actor-crítico    Acciones        Actor determinista Sensibilidad a
                 determinista,    continuas       y crítico Q        hiperparámetros y
                 off-policy                                          exploración.

  TD3            Actor-crítico    Acciones        Dos críticos,      No elimina la
                 determinista,    continuas       actualización      necesidad de
                 off-policy                       retardada del      diseñar bien
                                                  actor y suavizado  recompensa y
                                                  del objetivo       escalas.

  SAC            Actor-crítico    Acciones        Maximiza           Temperatura,
                 estocástico,     continuas       recompensa más     escalado y
                 off-policy                       entropía; usa dos  estimaciones Q
                                                  críticos en su     requieren
                                                  versión moderna    vigilancia.
  ------------------------------------------------------------------------------------

No existe un ganador universal. La comparación debe hacerse con la misma
tarea, presupuesto de interacción, semillas, métricas y condiciones de
evaluación. La facilidad de entrenamiento y la calidad final pueden
diferir según el entorno.

------------------------------------------------------------------------

# PARTE V. RECOMPENSAS Y DISEÑO DE TAREAS

## 14. Cómo se diseña una recompensa

Una recompensa debe traducir la tarea en una señal numérica que permita
distinguir resultados mejores y peores. En robótica, suele ser una
combinación de términos.

Ejemplo conceptual para un robot que debe seguir una velocidad objetivo:

\[ r_t=w_v r\_{`\text{velocidad}`{=tex}} -w_f p\_{`\text{caída}`{=tex}}
-w_e p\_{`\text{energía}`{=tex}} -w_s p\_{`\text{suavidad}`{=tex}} \]

donde cada término representa una métrica diferente y los pesos expresan
prioridades.

### 14.1 Recompensa escalar y multiobjetivo

En RL estándar, la recompensa por transición suele ser un escalar. Se
pueden combinar varios objetivos:

\[ r_t=`\sum`{=tex}*{i=1}\^{m}w_i r*{i,t} \]

Esto se denomina escalarización. Los pesos deben elegirse de forma que
la escala de cada término sea comprensible y que un componente no domine
accidentalmente.

Una recompensa vectorial real:

\[ `\mathbf `{=tex}r_t=(r\_{1,t},r\_{2,t},`\ldots`{=tex},r\_{m,t}) \]

representa un problema multiobjetivo. Un algoritmo estándar que espera
un escalar no resuelve automáticamente todos los objetivos
independientes; hay que definir una escalarización, preferencias
condicionantes o un método multiobjetivo específico.

### 14.2 Ejemplo de recompensa para control robótico

El ejemplo es ilustrativo y requiere adaptar nombres, unidades y pesos
al simulador real:

``` python
import numpy as np

def reward_robot(vx, target_vx, roll, pitch,
                 torque, joint_velocity, fallen, weights):
    tracking_error = vx - target_vx
    r_tracking = np.exp(-(tracking_error ** 2) / 0.25)

    p_tilt = roll**2 + pitch**2
    p_energy = np.sum(np.abs(np.asarray(torque) *
                             np.asarray(joint_velocity)))
    p_fall = 1.0 if fallen else 0.0

    reward = (
        weights["tracking"] * r_tracking
        - weights["tilt"] * p_tilt
        - weights["energy"] * p_energy
        - weights["fall"] * p_fall
    )

    if not np.isfinite(reward):
        raise ValueError("La recompensa no es finita.")
    return float(reward)
```

El ejemplo: - premia el seguimiento de velocidad; - penaliza
inclinación; - penaliza un proxy de potencia mecánica; - penaliza la
caída; - comprueba que la recompensa sea finita.

No garantiza que el robot aprenda a caminar. Debe evaluarse la escala,
el signo y el efecto de cada término mediante episodios controlados.

### 14.3 Errores frecuentes en la recompensa

1.  Penalizar demasiado el movimiento y aprender a quedarse quieto.
2.  Premiar velocidad sin penalizar inestabilidad.
3.  Dar una recompensa de éxito demasiado rara y no ofrecer señal útil
    al principio.
4.  Escalar mal términos con unidades diferentes.
5.  Definir caídas con un umbral que se dispara incorrectamente.
6.  No distinguir entre éxito, caída, estado inválido y límite de
    tiempo.
7.  No registrar los términos individuales.
8.  Introducir señales que el agente puede explotar de una manera no
    prevista.

### 14.4 Reward shaping

El *reward shaping* agrega señales intermedias para facilitar el
aprendizaje. Puede ayudar, pero también cambiar el objetivo que se
optimiza. En ciertas formulaciones existe shaping potencialmente
invariante a la política óptima; no toda recompensa adicional tiene esa
propiedad.

Una regla práctica es justificar cada término y medir si mejora la
conducta objetivo, no sólo la recompensa agregada.

------------------------------------------------------------------------

# PARTE VI. ENTRENAMIENTO, TIEMPO, MEMORIA Y EVALUACIÓN

## 15. Qué significa entrenar un agente RL

Un ciclo típico de entrenamiento incluye:

1.  Inicializar el entorno y las redes o tablas.
2.  Obtener una observación inicial.
3.  Elegir una acción según la política actual y su estrategia de
    exploración.
4.  Ejecutar la acción en el entorno.
5.  Recibir la siguiente observación, recompensa y banderas de
    terminación.
6.  Guardar la transición, si el algoritmo usa un buffer.
7.  Actualizar los parámetros según el algoritmo.
8.  Registrar métricas.
9.  Repetir durante muchos pasos y evaluar periódicamente.

La interacción con el entorno y las actualizaciones de parámetros son
operaciones diferentes. En algunos algoritmos, una actualización usa
varios datos; en otros, se agrupan muchas transiciones antes de
optimizar.

## 16. Episodios, pasos y actualizaciones

No basta con decir "entrené 300 episodios". Hay que registrar:

-   número de episodios;
-   pasos de entorno totales;
-   longitud media del episodio;
-   actualizaciones de gradiente;
-   tamaño de lote;
-   frecuencia de evaluación;
-   tiempo real de entrenamiento.

Si un episodio tiene 200 pasos, 300 episodios representan 60.000 pasos.
Si tiene 5.000 pasos, representan 1.500.000. La diferencia es de 25
veces.

## 17. Estimar tiempo de entrenamiento

Una aproximación de planificación es:

\[ T\_{`\text{total}`{=tex}}`\approx`{=tex}
N\_{`\text{env}`{=tex}}t\_{`\text{env}`{=tex}}
+N\_{`\text{updates}`{=tex}}t\_{`\text{update}`{=tex}}
+T\_{`\text{eval}`{=tex}}+T\_{`\text{overhead}`{=tex}} \]

donde: - (N\_{`\text{env}`{=tex}}): cantidad de pasos de entorno; -
(t\_{`\text{env}`{=tex}}): tiempo medio por paso; -
(N\_{`\text{updates}`{=tex}}): actualizaciones; -
(t\_{`\text{update}`{=tex}}): tiempo por actualización; -
(T\_{`\text{eval}`{=tex}}): evaluaciones; -
(T\_{`\text{overhead}`{=tex}}): inicialización, guardado, registro y
comunicación.

### Ejemplo ilustrativo

Con 500.000 pasos, 10 ms por paso de entorno y 4 ms por actualización,
suponiendo una actualización por paso:

-   interacción: 5.000 s;
-   actualizaciones: 2.000 s;
-   total aproximado: 7.000 s (1,94 h), sin contar sobrecostes.

Si el entorno tarda 50 ms por paso, la interacción por sí sola suma
25.000 s (casi 6,95 h).

**Estos números no son una predicción universal ni una medición de
GIAR-ORION.** Hay que medir el entorno real y extrapolar.

### 17.1 Código para medir velocidad del entorno

``` python
import time

def benchmark_env(env, action, steps=1000):
    start = time.perf_counter()
    completed = 0

    for _ in range(steps):
        # Adaptar a la API: algunos entornos devuelven 4 valores,
        # otros 5 (observation, reward, terminated, truncated, info).
        result = env.step(action)
        completed += 1

    elapsed = time.perf_counter() - start
    return {
        "steps": completed,
        "elapsed_seconds": elapsed,
        "seconds_per_step": elapsed / max(completed, 1),
        "steps_per_second": completed / max(elapsed, 1e-12),
    }
```

Debe adaptarse al API del entorno y a la lógica de reset. En una API
remota, el tiempo de comunicación puede dominar el costo de la red
neuronal.

## 18. Memoria y hardware

No existe un requisito de memoria único para RL. El consumo depende del
algoritmo, las dimensiones, el tamaño de red, el Replay Buffer, la
cantidad de entornos y el tipo de observación.

### 18.1 RAM

La RAM puede alojar: - simulador y geometría; - Replay Buffer; -
observaciones y transiciones; - registros y datos de evaluación; -
procesos auxiliares y múltiples entornos.

Para un Replay Buffer que almacena observación actual, siguiente
observación, acción, recompensa y bandera de terminación como `float32`,
una aproximación es:

\[
M\_{`\text{buffer}`{=tex}}`\approx `{=tex}N(2d_s+d_a+2)`\times4`{=tex} `\text{bytes}`{=tex}
\]

con capacidad (N), dimensión de observación (d_s) y dimensión de acción
(d_a). Es una estimación de los arreglos numéricos principales, sin
sobrecarga de Python ni estructuras auxiliares.

Ejemplo: (N=10\^6), (d_s=200), (d_a=29):

\[ M`\approx10`{=tex}\^6(400+29+2)`\times4`{=tex}
=1.724`\times10`{=tex}\^9 `\text{bytes}`{=tex} \]

Aproximadamente 1,724 GB decimales (alrededor de 1,61 GiB).

### 18.2 VRAM

La VRAM puede alojar: - parámetros de redes; - gradientes; - estados del
optimizador; - activaciones y tensores de lote; - datos transferidos a
GPU.

Una política MLP con observaciones vectoriales suele ser mucho más
ligera que una red que procesa imágenes, pero la cifra exacta debe
medirse. La capacidad de VRAM no determina por sí sola la velocidad: el
simulador puede ser el cuello de botella.

### 18.3 Código para estimar Replay Buffer

``` python
def estimate_buffer_gb(obs_dim, act_dim, capacity, bytes_per_value=4):
    elements = capacity * (2 * obs_dim + act_dim + 2)
    return elements * bytes_per_value / 1e9

print(estimate_buffer_gb(obs_dim=200, act_dim=29,
                         capacity=1_000_000))
```

### 18.4 Qué medir en la máquina real

-   RAM del proceso y del simulador;
-   VRAM asignada y pico de VRAM;
-   utilización de CPU y GPU;
-   pasos por segundo;
-   actualizaciones por segundo;
-   tiempo de reset;
-   tamaño del buffer;
-   número de entornos paralelos.

No se debe estimar memoria sólo a partir del tamaño del archivo del
modelo. Las activaciones, gradientes, optimizadores y buffers pueden
requerir bastante memoria adicional.

## 19. Límites y dificultades de RL

### 19.1 No garantiza encontrar una política óptima

El aprendizaje depende de exploración, datos, representación, recompensa
y optimización. Una red puede converger a una solución mediocre, oscilar
o fallar.

### 19.2 Eficiencia de muestras

Muchos problemas de control necesitan numerosas interacciones. En
robótica real, cada ensayo puede consumir tiempo, energía o hardware.
Por eso se suele entrenar en simulación, aprovechar demostraciones o
diseñar métodos que reutilicen datos.

### 19.3 Sensibilidad a hiperparámetros

La tasa de aprendizaje, el factor de descuento, el tamaño de lote, la
escala de recompensa y la frecuencia de actualización pueden cambiar el
resultado de forma importante.

### 19.4 Seguridad

La recompensa no es un mecanismo de seguridad suficiente. Para un robot
real se necesitan límites físicos, supervisión, parada de emergencia y
pruebas controladas.

### 19.5 Brecha entre simulación y realidad

La política puede depender de una fricción, masa, latencia o ruido
específicos del simulador. La transferencia sim-to-real puede requerir
aleatorización de parámetros, calibración, estimación robusta y
validación progresiva.

### 19.6 Reproducibilidad

Resultados pueden variar entre semillas, versiones de bibliotecas y
hardware. Deben guardarse configuraciones, versiones, semillas,
checkpoints y métricas.

### 19.7 Recompensa mal especificada

Una recompensa es un proxy del objetivo. Si el proxy no representa el
objetivo real, el agente puede maximizarlo de manera no deseada. La
evaluación debe incluir métricas independientes de la recompensa
entrenada.

### 19.8 Episodios truncados y terminaciones

Los entornos modernos suelen distinguir: - `terminated`: la tarea
terminó de forma terminal; - `truncated`: el episodio se cortó por un
límite externo, como un máximo de pasos.

No siempre deben tratarse de la misma manera en el objetivo de Bellman.
El tratamiento depende del algoritmo y de la definición del proceso.

## 20. Evaluar un agente correctamente

No basta con observar una recompensa alta o una pérdida baja. Un
protocolo razonable incluye:

-   recompensa media y dispersión;
-   tasa de éxito;
-   frecuencia de caída o fallo;
-   duración de episodios;
-   error de seguimiento;
-   energía o esfuerzo;
-   suavidad de acciones;
-   resultados con varias semillas;
-   pruebas con estados iniciales distintos;
-   evaluación sin exploración adicional, cuando corresponda;
-   validación de seguridad separada.

La métrica principal debe representar la tarea real. Si la tarea es
caminar estable, la recompensa total no sustituye a la tasa de caída, el
error de velocidad y la estabilidad física.

------------------------------------------------------------------------

# PARTE VII. HISTORIA DEL APRENDIZAJE POR REFUERZO

## 21. Una historia con varias raíces

La historia de RL no empieza con las redes neuronales profundas. Surgió
de la convergencia gradual de varias tradiciones: aprendizaje por ensayo
y error, control óptimo, programación dinámica, teoría de decisiones,
aprendizaje de máquinas y modelos computacionales inspirados en el
comportamiento. Sutton y Barto dedican parte de su libro a reconstruir
estas raíces. \[SB\]

Las fechas siguientes señalan hitos influyentes, no una lista exhaustiva
ni una atribución exclusiva del campo a una sola persona.

## 22. Cronología de hitos

### 1898--1911: aprendizaje por ensayo y error

Los estudios de Edward Thorndike sobre aprendizaje animal y su
formulación de la "ley del efecto" (1911) son antecedentes conceptuales
importantes: las consecuencias de una conducta influyen en la
probabilidad de que se repita. Es un antecedente psicológico, no un
algoritmo moderno de RL.

### Décadas de 1940--1950: cibernética, control y aprendizaje en máquinas

La investigación sobre control adaptativo, automatización, teoría de
decisiones y sistemas que ajustan su conducta contribuyó a crear el
contexto del aprendizaje por refuerzo. Alan Turing exploró ideas
tempranas de máquinas que modifican su comportamiento a partir de
señales de éxito y fracaso. Estas líneas históricas son diversas y no
equivalen todavía a la formulación moderna de un MDP.

### 1950--1960: programación dinámica y decisiones secuenciales

Richard Bellman desarrolló la programación dinámica y las ecuaciones de
Bellman, que se convirtieron en bases matemáticas para problemas de
decisión secuencial y control óptimo. Las ecuaciones expresan cómo
descomponer un problema de largo plazo en recompensa inmediata y valor
futuro.

En paralelo, los estudios de aprendizaje por refuerzo en máquinas y los
trabajos sobre juegos ayudaron a formular métodos de aprendizaje
mediante interacción.

### 1960--1970: control adaptativo y fundamentos computacionales

Se desarrollaron métodos de control adaptativo, estimación y aprendizaje
que influyeron en las ideas de aprendizaje a partir de consecuencias.
Los límites de cómputo y la falta de datos de gran escala condicionaban
los experimentos.

### Década de 1980: TD y algoritmos de aprendizaje por refuerzo modernos

El aprendizaje por diferencia temporal (*Temporal-Difference Learning*)
se consolidó como una idea central: actualizar estimaciones usando
errores entre predicciones sucesivas. Los trabajos de Richard Sutton y
colaboradores ayudaron a establecer sus fundamentos.

Chris Watkins desarrolló Q-learning, formalizado en su tesis doctoral de
1989 y publicado posteriormente. Q-learning permitió aprender valores
óptimos de acción a partir de experiencia sin requerir un modelo
conocido de transición. \[Watkins\]

### 1992: REINFORCE y gradientes de política

Ronald J. Williams publicó "Simple Statistical Gradient-Following
Algorithms for Connectionist Reinforcement Learning", donde presentó la
familia REINFORCE. Este trabajo es un hito en métodos que ajustan
directamente políticas estocásticas usando gradientes de la recompensa
esperada. \[Williams\]

### Década de 1990: consolidación teórica y aplicaciones

Se consolidaron formulaciones que conectaban métodos de Monte Carlo, TD,
aproximación de funciones y control. El libro de Sutton y Barto de 1998
ayudó a organizar el campo y ofrecer una presentación unificada de sus
fundamentos. \[SB, edición 1998\]

### 1990--2000: TD-Gammon y juegos

TD-Gammon, desarrollado por Gerald Tesauro, mostró que aprendizaje por
diferencia temporal y redes neuronales podían aprender estrategias
fuertes para backgammon a partir del autojuego. Fue un ejemplo
influyente de aprendizaje desde experiencia en un entorno con resultados
diferidos.

### 2000--2010: aproximación de funciones y control continuo

El campo avanzó en algoritmos actor-crítico, gradientes de política,
métodos con aproximadores no lineales y aprendizaje en control continuo.
Sin embargo, la combinación de redes profundas con RL seguía siendo
difícil de estabilizar y costosa en cómputo.

### 2013--2015: resurgimiento del Deep RL

Los avances en GPU, redes profundas, grandes conjuntos de experiencias y
técnicas de estabilización permitieron entrenar agentes desde entradas
de alta dimensión.

En 2015, Mnih et al. publicaron en *Nature* "Human-level control through
deep reinforcement learning". Su trabajo mostró un agente DQN capaz de
aprender a jugar múltiples juegos Atari directamente desde píxeles,
combinando redes profundas con Q-learning y mecanismos de
estabilización. \[DQN\]

### 2016: AlphaGo

Silver et al. publicaron "Mastering the game of Go with deep neural
networks and tree search". AlphaGo combinó redes de política y valor,
aprendizaje supervisado a partir de partidas humanas, aprendizaje por
autojuego y búsqueda de árbol Monte Carlo. En 2016 venció al campeón
europeo Fan Hui por 5--0, un hito de la IA aplicada a juegos complejos.
\[AlphaGo\]

AlphaGo no fue simplemente "un algoritmo de RL": fue un sistema híbrido
que combinó aprendizaje supervisado, aprendizaje por refuerzo y
búsqueda.

### 2015--2018: algoritmos modernos para control continuo

Se desarrollaron y popularizaron métodos como DDPG, TRPO, PPO, TD3 y
SAC. Estas familias abordaron diferentes compromisos entre estabilidad,
eficiencia de muestras, exploración y control de acciones continuas.

### 2017: PPO

Proximal Policy Optimization se difundió como una familia de algoritmos
de optimización de política relativamente simple de implementar, que
limita el cambio de política mediante un objetivo recortado en una de
sus formulaciones principales. \[PPO\]

### 2018: Soft Actor-Critic

Haarnoja y colaboradores desarrollaron SAC como un algoritmo off-policy
de actor-crítico que optimiza una recompensa aumentada por entropía. La
formulación favorece exploración y ha sido influyente para tareas de
control continuo. \[SAC\]

### 2018 en adelante: expansión de aplicaciones

RL se extendió en investigación hacia robótica simulada y física,
manipulación, locomoción, juegos, sistemas de recomendación, asignación
de recursos, optimización y control. El desempeño real depende del
entorno y de cómo se evalúe; un resultado espectacular en un benchmark
no implica una solución general para cualquier tarea.

### Década de 2020: datos, simulación, RL offline y sistemas híbridos

Las líneas activas incluyen RL offline, aprendizaje desde
demostraciones, métodos model-based, aprendizaje multiagente, políticas
condicionadas por objetivos, entrenamiento masivamente paralelo y
combinación con modelos fundacionales. Las técnicas no son
intercambiables: cada una introduce supuestos distintos sobre datos,
exploración y distribución de entrenamiento.

## 23. Qué enseña la historia

1.  RL se desarrolló a partir de varias disciplinas, no de un único
    descubrimiento.
2.  Las ecuaciones de valor y los métodos TD preceden a Deep RL.
3.  Las redes profundas ampliaron la capacidad de representación, pero
    también aumentaron los desafíos de estabilidad y cómputo.
4.  DQN y AlphaGo fueron hitos distintos: DQN enfatizó aprendizaje desde
    píxeles en juegos Atari; AlphaGo combinó redes, autojuego y búsqueda
    para Go.
5.  PPO, TD3 y SAC reflejan decisiones de diseño diferentes, no una
    progresión en la que cada algoritmo sea siempre superior al
    anterior.
6.  En robótica, la simulación y la evaluación de seguridad son tan
    importantes como la optimización de la red.

------------------------------------------------------------------------

# PARTE VIII. EJEMPLOS DE CÓMO RAZONAR SOBRE RL

## 24. Ejemplo conceptual: un robot que aprende a avanzar

Supongamos que un robot debe avanzar a una velocidad objetivo (v\^\*).

### Estado u observación

\[
o_t=\[v_t,`\theta`{=tex}\_t,`\dot`{=tex}`\theta`{=tex}\_t,q_t,`\dot `{=tex}q_t,`\ldots`{=tex}\]
\]

Podría incluir velocidad del torso, orientación, velocidades articulares
y otras variables.

### Acción

\[ a_t`\in[-1,1]`{=tex}\^{d_a} \]

Cada componente se escala a la consigna física del actuador
correspondiente.

### Recompensa

\[
r_t=w_v`\exp`{=tex}`\left`{=tex}(-`\frac{(v_t-v^*)^2}{\sigma^2}`{=tex}`\right`{=tex})
-w_f`\mathbf 1`{=tex}\_{`\text{caída}`{=tex}} -w_e E_t \]

La recompensa favorece el seguimiento de velocidad y penaliza caídas y
energía. Los pesos y el término de energía requieren definición y
validación.

### Fin del episodio

El episodio puede terminar si: - se detecta una caída; - se alcanza el
objetivo; - aparece un estado numéricamente inválido; - se alcanza un
límite de duración.

Cada condición debe distinguirse en los registros para diagnosticar el
entrenamiento.

### Evaluación

Además de la recompensa: - medir error de velocidad; - medir tasa de
caída; - comprobar estabilidad; - registrar acciones saturadas; -
evaluar diferentes estados iniciales.

## 25. Ejemplo de estructura de un entorno

Este pseudocódigo ilustra la interfaz conceptual. No es un entorno
completo de CoppeliaSim ni un sustituto de la API del simulador.

``` python
class RobotTask:
    def reset(self):
        # Reiniciar simulador y devolver observación inicial.
        obs = self.read_observation()
        return obs

    def step(self, action):
        # 1. Validar y limitar la acción.
        action = self.safety_clip(action)

        # 2. Aplicar la acción durante el intervalo de control.
        self.apply_action(action)
        self.advance_simulation()

        # 3. Leer estado/observación y calcular recompensa.
        obs = self.read_observation()
        reward = self.compute_reward(obs, action)

        # 4. Determinar terminación real y truncamiento temporal.
        terminated = self.is_terminal_failure(obs) or self.goal_reached(obs)
        truncated = self.time_limit_reached()

        info = {
            "goal_reached": self.goal_reached(obs),
            "fallen": self.is_terminal_failure(obs),
        }
        return obs, float(reward), terminated, truncated, info
```

El detalle importante es la separación entre: - dinámica y sensores; -
política que elige acciones; - recompensa; - terminación; - límites de
seguridad.

## 26. Lista de control para empezar un proyecto de RL

### Definición de tarea

-   [ ] El objetivo se puede medir.
-   [ ] Se definieron éxito y fracaso.
-   [ ] Se especificó la duración del episodio.
-   [ ] Se separaron terminación y truncamiento.

### Observación

-   [ ] Dimensiones y orden documentados.
-   [ ] Unidades y rangos conocidos.
-   [ ] No hay valores `NaN` ni `Inf`.
-   [ ] Las variables necesarias para la dinámica están presentes o se
    estima el estado.

### Acciones

-   [ ] Dimensión y orden verificados.
-   [ ] Tipo de control definido: posición, velocidad, torque u otro.
-   [ ] Escalas y límites físicos definidos.
-   [ ] Acciones saturadas registradas.
-   [ ] Existe una capa de seguridad independiente.

### Recompensa

-   [ ] Cada término tiene una justificación.
-   [ ] Se registran los componentes por separado.
-   [ ] Escalas y signos comprobados.
-   [ ] Se prueba si el agente puede explotar el diseño.
-   [ ] La métrica final es independiente de la recompensa cuando sea
    posible.

### Entrenamiento

-   [ ] Algoritmo y variante documentados.
-   [ ] Semillas registradas.
-   [ ] Hiperparámetros guardados.
-   [ ] Se registran pasos y actualizaciones, no sólo episodios.
-   [ ] Checkpoints y logs se guardan.
-   [ ] Se mide tiempo y memoria.

### Evaluación

-   [ ] Se evalúa periódicamente sin exploración extra, si corresponde.
-   [ ] Se prueban varias semillas.
-   [ ] Se prueban condiciones iniciales distintas.
-   [ ] Se registran éxito, fallos y estabilidad.
-   [ ] La política se valida antes de usar hardware real.

------------------------------------------------------------------------

# PARTE IX. GLOSARIO

## 27. Definiciones para consulta rápida

-   **Acción ((a)):** decisión ejecutada por el agente.
-   **Agente:** sistema que aprende a decidir.
-   **Aprendizaje por refuerzo (RL):** aprendizaje de decisiones
    mediante interacción y recompensas.
-   **Aprendizaje profundo por refuerzo (Deep RL):** RL que utiliza
    redes neuronales profundas para aproximar políticas, valores o
    modelos.
-   **Bootstrapping:** actualizar una estimación usando otra estimación
    aprendida.
-   **Crítico:** estimador de valor usado para evaluar estados o
    acciones.
-   **Descuento ((`\gamma`{=tex})):** factor que pondera recompensas
    futuras.
-   **Entorno:** sistema con el que interactúa el agente.
-   **Episodio:** secuencia de interacción hasta la terminación o el
    límite definido.
-   **Estado ((s)):** descripción suficiente del entorno para la
    formulación.
-   **Exploración:** probar acciones para obtener información.
-   **Explotación:** elegir acciones que parecen mejores según lo
    aprendido.
-   **Función de ventaja ((A)):** diferencia entre valor de una acción y
    valor del estado.
-   **Función de valor ((V)):** retorno esperado desde un estado.
-   **Función Q ((Q)):** retorno esperado al ejecutar una acción en un
    estado y continuar con una política.
-   **Gradiente de política:** derivada del objetivo esperado respecto
    de los parámetros de la política.
-   **MDP:** proceso de decisión de Markov.
-   **Modelo:** representación de la dinámica o de la recompensa del
    entorno.
-   **Off-policy:** aprende de datos generados por una política
    diferente o anterior.
-   **On-policy:** aprende usando datos de la política que se optimiza o
    una versión próxima.
-   **Observación ((o)):** información disponible para el agente.
-   **Política ((`\pi`{=tex})):** regla que especifica cómo elegir
    acciones.
-   **POMDP:** proceso de decisión de Markov parcialmente observable.
-   **Recompensa ((r)):** señal inmediata que evalúa una transición.
-   **Replay Buffer:** memoria de transiciones reutilizadas por ciertos
    algoritmos.
-   **Retorno ((G)):** suma descontada de recompensas futuras.
-   **TD:** aprendizaje por diferencia temporal.
-   **Transición:** relación entre estado, acción, recompensa y
    siguiente estado.
-   **Trayectoria / rollout:** secuencia de estados, acciones y
    recompensas.
-   **Terminación (`terminated`):** final real definido por la tarea.
-   **Truncamiento (`truncated`):** corte externo del episodio, por
    ejemplo por un límite temporal.
-   **Sim-to-real:** transferencia de políticas desde simulación a
    hardware físico.
-   **Escalarización:** combinación de varios objetivos en una
    recompensa escalar.

------------------------------------------------------------------------

# 28. Bibliografía y fuentes de referencia

Las siguientes fuentes son las principales referencias utilizadas para
construir el contenido técnico e histórico. Los enlaces permiten
consultar las fuentes originales o sus páginas editoriales.

## 28.1 Libros y textos de referencia

**\[SB1\]** Sutton, R. S., & Barto, A. G. (2018). *Reinforcement
Learning: An Introduction* (2nd ed.). MIT Press.\
Página editorial:
https://mitpress.mit.edu/9780262039246/reinforcement-learning/\
Edición abierta de los autores:
http://incompleteideas.net/book/the-book-2nd.html

Referencia central para MDP, retorno, políticas, funciones de valor,
programación dinámica, Monte Carlo, TD, Q-learning, SARSA, aproximación
de funciones y contexto histórico.

**\[SB2\]** Sutton, R. S., & Barto, A. G. (1998). *Reinforcement
Learning: An Introduction*. MIT Press.\
Página editorial:
https://mitpress.mit.edu/9780262193986/reinforcement-learning/

Edición histórica que contribuyó a consolidar la presentación moderna
del campo.

## 28.2 Documentación técnica y material educativo

**\[Spinning Up\]** Achiam, J. (2018). *Spinning Up in Deep
Reinforcement Learning*. OpenAI.\
Introducción a conceptos:
https://spinningup.openai.com/en/latest/spinningup/rl_intro.html\
Portal: https://spinningup.openai.com/en/latest/

Fuente utilizada para definiciones de agente, entorno, estado, acción,
política, trayectoria, retorno y panorama de Deep RL.

## 28.3 Artículos y trabajos históricos

**\[Watkins\]** Watkins, C. J. C. H. (1989). *Learning from Delayed
Rewards*. PhD thesis, University of Cambridge.\
Registro y materiales bibliográficos:
https://www.cs.rhul.ac.uk/\~chrisw/new_thesis.pdf

Trabajo asociado al desarrollo de Q-learning y al aprendizaje a partir
de recompensas diferidas.

**\[Williams\]** Williams, R. J. (1992). "Simple Statistical
Gradient-Following Algorithms for Connectionist Reinforcement Learning."
*Machine Learning*, 8, 229--256.\
DOI: https://doi.org/10.1007/BF00992696

Referencia clásica para la familia REINFORCE y gradientes de política.

**\[DQN\]** Mnih, V., Kavukcuoglu, K., Silver, D., et al. (2015).
"Human-level control through deep reinforcement learning." *Nature*,
518, 529--533.\
DOI: https://doi.org/10.1038/nature14236

Hito de Deep RL aplicado a juegos Atari a partir de píxeles.

**\[AlphaGo\]** Silver, D., Huang, A., Maddison, C. J., et al. (2016).
"Mastering the game of Go with deep neural networks and tree search."
*Nature*, 529, 484--489.\
DOI: https://doi.org/10.1038/nature16961

Referencia para la combinación de redes de política y valor, autojuego y
búsqueda Monte Carlo en AlphaGo.

**\[PPO\]** Schulman, J., Wolski, F., Dhariwal, P., Radford, A., &
Klimov, O. (2017). "Proximal Policy Optimization Algorithms."\
arXiv: https://arxiv.org/abs/1707.06347

Referencia para PPO y la optimización de políticas mediante un objetivo
recortado.

**\[SAC1\]** Haarnoja, T., Zhou, A., Abbeel, P., & Levine, S. (2018).
"Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement
Learning with a Stochastic Actor."\
arXiv: https://arxiv.org/abs/1801.01290

Referencia para SAC y la formulación de máxima entropía.

**\[SAC2\]** Haarnoja, T., Zhou, A., Hartikainen, K., et al. (2018).
"Soft Actor-Critic Algorithms and Applications."\
arXiv: https://arxiv.org/abs/1812.05905

Desarrollo de SAC y aplicaciones, incluida la formulación con ajuste
automático de temperatura.

## 28.4 Cómo citar y ampliar esta guía

Para un informe académico o institucional: 1. citar el libro de Sutton y
Barto para fundamentos generales; 2. citar el artículo original
correspondiente al algoritmo estudiado; 3. citar la versión concreta del
código o repositorio analizado; 4. registrar fecha de consulta de
documentación web que pueda cambiar; 5. separar afirmaciones teóricas,
resultados publicados y resultados experimentales propios.

La bibliografía no implica que cada ejemplo de código de este documento
haya sido copiado de esas fuentes. Los fragmentos de Python son ejemplos
originales de carácter didáctico y deben adaptarse y probarse antes de
usarlos en un proyecto.

------------------------------------------------------------------------

# 29. Conclusiones

El aprendizaje por refuerzo estudia cómo aprender decisiones a partir de
interacción y recompensas acumuladas. Su formulación utiliza estados,
acciones, políticas, transiciones, retornos y funciones de valor. Las
ecuaciones de Bellman expresan la relación entre la recompensa inmediata
y el valor futuro; los métodos MC, TD, Q-learning y gradientes de
política ofrecen distintas formas de estimar o maximizar ese retorno.

Deep RL extiende estos métodos mediante redes neuronales, haciendo
posible trabajar con observaciones y espacios de acción grandes, pero
introduciendo dificultades de estabilidad, consumo de recursos,
sensibilidad a hiperparámetros y reproducibilidad.

La historia del campo muestra una evolución desde el aprendizaje por
ensayo y error, el control óptimo y la programación dinámica hasta TD,
Q-learning, gradientes de política y algoritmos modernos como DQN, PPO y
SAC. Los avances de Deep RL ampliaron el alcance de los sistemas
aprendidos, pero no eliminaron la necesidad de diseñar correctamente el
entorno y evaluar los resultados.

Para robótica, la calidad de la tarea, la observación, las acciones, la
recompensa, la dinámica del simulador y los mecanismos de seguridad es
tan importante como el algoritmo. Un agente no debe considerarse exitoso
sólo porque la recompensa aumente: debe cumplir métricas físicas y
funcionales independientes y demostrar estabilidad en condiciones
variadas.

**Principio rector para GIAR-ORION:** toda afirmación sobre un
entrenamiento concreto debe poder rastrearse a la configuración, el
código, los datos y los registros del experimento. Esta guía establece
los fundamentos generales; la implementación real debe auditarse por
separado.
