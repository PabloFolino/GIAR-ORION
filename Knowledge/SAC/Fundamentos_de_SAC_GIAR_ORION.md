# Soft Actor-Critic (SAC): fundamentos matemáticos, implementación y aplicación a robótica

**Documento técnico para GIAR-ORION**\
**Versión:** 2.0\
**Fecha:** 12 de octubre de 2026\
**Propósito:** explicar SAC desde sus fundamentos hasta las decisiones
prácticas de implementación, con fórmulas, ejemplos en Python, criterios
de diagnóstico y estimaciones de tiempo y memoria.

> **Alcance y trazabilidad.** Este documento amplía el archivo
> introductorio *Fundamentos de Soft Actor-Critic.md*. La formulación
> matemática se contrasta con el artículo original de SAC y la
> documentación técnica de OpenAI Spinning Up. Los ejemplos de
> recompensa y de control se presentan como diseños ilustrativos, no
> como la configuración confirmada de un proyecto particular. Para
> afirmar qué parámetros, recompensas o límites utiliza un entrenamiento
> concreto, hay que inspeccionar sus archivos de configuración y su
> código.

------------------------------------------------------------------------

## 1. Resumen ejecutivo

**Soft Actor-Critic (SAC)** es un algoritmo de aprendizaje por refuerzo
profundo (*Deep Reinforcement Learning*, DRL), de tipo
**actor-crítico**, **estocástico** y **off-policy**. Se usa
especialmente para problemas de control con acciones continuas, como
regular el par de motores, la velocidad de articulaciones o las
consignas de un robot.

SAC aprende simultáneamente:

1.  **Actor o política** (`\pi`{=tex}\_`\theta`{=tex}(a`\mid `{=tex}s)):
    dada una observación (s), produce una distribución de probabilidad
    sobre acciones posibles.
2.  **Dos críticos** (Q\_{`\phi`{=tex}*1}(s,a)) y
    (Q*{`\phi`{=tex}\_2}(s,a)): estiman el retorno esperado de ejecutar
    la acción (a) en el estado (s).
3.  **Dos críticos objetivo** (Q\_{`\bar`{=tex}`\phi`{=tex}*1}) y
    (Q*{`\bar`{=tex}`\phi`{=tex}\_2}): copias lentas de los críticos
    principales que estabilizan el objetivo de aprendizaje.
4.  **Replay Buffer** (`\mathcal `{=tex}D): almacena transiciones
    anteriores para volver a utilizarlas durante el aprendizaje.
5.  **Temperatura** (`\alpha`{=tex}): pondera la entropía de la política
    frente a la recompensa. Puede ser fija o ajustarse automáticamente.

La característica distintiva de SAC es que intenta maximizar tanto la
recompensa acumulada como la entropía de la política. En términos
prácticos, no busca solamente obtener una buena acción: durante el
aprendizaje también procura conservar suficiente exploración.

SAC **no garantiza** que el robot aprenda a caminar, que converja en una
cantidad determinada de episodios ni que encuentre una política segura.
El resultado depende de la definición del estado, las acciones, la
recompensa, el simulador, la arquitectura de las redes, la cantidad de
datos y los hiperparámetros.

------------------------------------------------------------------------

## 2. Qué problema resuelve el aprendizaje por refuerzo

Un entorno de aprendizaje por refuerzo se puede representar como un
proceso de decisión de Markov:

\[
`\mathcal `{=tex}M=(`\mathcal `{=tex}S,`\mathcal `{=tex}A,P,R,`\gamma`{=tex})
\]

donde:

-   (`\mathcal `{=tex}S): conjunto de estados u observaciones posibles.
-   (`\mathcal `{=tex}A): conjunto de acciones posibles.
-   (P(s'`\mid `{=tex}s,a)): dinámica de transición; describe la
    probabilidad de llegar al siguiente estado (s').
-   (R(s,a,s')): recompensa inmediata que asigna el entorno.
-   (`\gamma`{=tex}`\in`{=tex}\[0,1)): factor de descuento de
    recompensas futuras.

En cada paso (t), el agente observa (s_t), elige (a_t), el entorno
ejecuta la acción y devuelve (r_t), (s\_{t+1}) y señales de terminación.

La secuencia es:

\[ s_t `\rightarrow `{=tex}a_t `\rightarrow `{=tex}(r_t,s\_{t+1},d_t) \]

El objetivo no es maximizar solamente la recompensa inmediata, sino la
suma descontada a lo largo del tiempo:

\[
J_R(`\pi`{=tex})=`\mathbb `{=tex}E\_{`\tau`{=tex}`\sim`{=tex}`\pi`{=tex}}`\left[\sum_{t=0}^{T-1}\gamma^t r_t\right]`{=tex}\]

Aquí (`\tau`{=tex}) representa una trayectoria completa generada al
interactuar con el entorno.

### 2.1 Por qué se necesita una función de recompensa

La recompensa define qué significa "hacerlo bien". El algoritmo no
conoce por sí mismo conceptos como caminar estable, no caerse, ahorrar
energía o seguir una velocidad objetivo. Esos objetivos deben expresarse
en señales numéricas.

Una recompensa mal diseñada puede provocar que el agente maximice una
conducta no deseada. Por ejemplo, premiar únicamente el desplazamiento
hacia adelante puede hacer que el robot se desplace de manera brusca,
ignore el equilibrio o encuentre una solución artificial del simulador.

### 2.2 Estado y observación no siempre son lo mismo

En teoría, el estado contiene toda la información necesaria para
predecir la dinámica. En la práctica, el agente suele recibir una
observación parcial:

\[ o_t = h(s_t) \]

En un robot humanoide, una observación podría incluir:

-   orientación del torso o cuaternión de IMU;
-   velocidad angular y aceleración;
-   velocidades lineales estimadas;
-   posiciones y velocidades articulares;
-   altura y orientación del torso;
-   contactos de los pies;
-   velocidad objetivo;
-   acciones anteriores.

No conviene incorporar variables sin normalizarlas ni mezclar unidades
sin revisar sus escalas. Un ángulo en radianes, una velocidad en rad/s y
una posición en metros pueden tener rangos muy distintos.

------------------------------------------------------------------------

## 3. ¿Qué significa que SAC sea actor-crítico?

### 3.1 Actor

El actor parametriza la política:

\[ a_t`\sim`{=tex}`\pi`{=tex}\_`\theta`{=tex}(a`\mid `{=tex}s_t) \]

En SAC para acciones continuas, normalmente una red neuronal calcula la
media (`\mu`{=tex}*`\theta`{=tex}(s)) y la desviación estándar
(`\sigma`{=tex}*`\theta`{=tex}(s)) de una distribución gaussiana.
Después se toma una muestra y se limita al rango de acción permitido.

El actor no tiene por qué producir siempre exactamente la misma acción
para una observación. Esa aleatoriedad favorece la exploración durante
el entrenamiento.

### 3.2 Crítico

Un crítico aproxima la función de valor de acción:

\[ Q\^`\pi`{=tex}(s,a)
=`\mathbb `{=tex}E\_`\pi`{=tex}`\left[\sum_{k=0}^{\infty}\gamma^k r_{t+k}
\mid s_t=s,a_t=a\right]`{=tex}\]

Intuitivamente, (Q(s,a)) estima qué tan conveniente sería ejecutar (a)
en (s) y continuar después con la política. No es una recompensa
observada directamente ni una probabilidad: es una estimación aprendida
del retorno futuro.

### 3.3 ¿Por qué dos críticos?

SAC suele aprender dos estimadores independientes y usa el mínimo:

\[
Q\_{`\min`{=tex}}(s,a)=`\min`{=tex}(Q\_{`\phi`{=tex}*1}(s,a),Q*{`\phi`{=tex}\_2}(s,a))
\]

Las redes pueden cometer errores diferentes. Si se usara siempre el
valor mayor, el aprendizaje podría sobrevalorar acciones por error. Usar
el mínimo reduce ese riesgo, aunque no elimina todos los errores de
estimación.

### 3.4 Redes objetivo

Los críticos objetivo se actualizan lentamente:

\[
`\bar`{=tex}`\phi`{=tex}\_i`\leftarrow `{=tex}`\tau`{=tex}`\phi`{=tex}\_i+(1-`\tau`{=tex})`\bar`{=tex}`\phi`{=tex}\_i
\]

En esta convención, (`\tau`{=tex}) es pequeño, por ejemplo 0.005.
Algunas bibliotecas usan el parámetro complementario
(`\rho=1`{=tex}-`\tau`{=tex}), cercano a 1. Por eso hay que comprobar
qué convención utiliza el código antes de copiar un valor.

Las redes objetivo no son otra política independiente: son copias lentas
de los críticos que se usan para construir objetivos de entrenamiento
más estables.

------------------------------------------------------------------------

## 4. Entropía y máxima entropía

La entropía mide la dispersión de una distribución de probabilidad. Para
una política continua con densidad (`\pi`{=tex}(a`\mid `{=tex}s)):

\[ `\mathcal `{=tex}H(`\pi`{=tex}(`\cdot`{=tex}`\mid `{=tex}s))
=`\mathbb `{=tex}E\_{a`\sim`{=tex}`\pi`{=tex}}`\left[-\log\pi(a\mid s)\right]`{=tex}\]

El objetivo de máxima entropía de SAC se expresa como:

\[ J(`\pi`{=tex})=
`\mathbb `{=tex}E\_{`\tau`{=tex}`\sim`{=tex}`\pi`{=tex}}`\left[
\sum_{t=0}^{T-1}\gamma^t
\left(r_t+\alpha\mathcal H(\pi(\cdot\mid s_t))\right)
\right]`{=tex}\]

Equivalentemente, usando una muestra de acción:

\[ J(`\pi`{=tex})= `\mathbb `{=tex}E`\left[
\sum_t\gamma^t
\left(r_t-\alpha\log\pi(a_t\mid s_t)\right)
\right]`{=tex}\]

-   Si (`\alpha`{=tex}) aumenta, la entropía tiene más peso: se
    incentiva una política más dispersa.
-   Si (`\alpha`{=tex}) disminuye, domina más la recompensa.
-   Si (`\alpha`{=tex}) es demasiado alta, la política puede continuar
    explorando y no consolidar el comportamiento.
-   Si (`\alpha`{=tex}) es demasiado baja, puede reducir la exploración
    prematuramente.

La entropía no equivale a ruido añadido sin control: es una propiedad de
la distribución aprendida por el actor y aparece explícitamente en las
funciones objetivo.

### 4.1 Temperatura fija y automática

**Temperatura fija:** (`\alpha`{=tex}) se configura manualmente y no
cambia durante el entrenamiento.

**Temperatura automática:** se define una entropía objetivo y se aprende
(`\alpha`{=tex}), normalmente optimizando (`\log`{=tex}`\alpha`{=tex})
para garantizar que (`\alpha`{=tex}\>0).

Una forma habitual de la pérdida de temperatura es:

\[ L(`\alpha`{=tex})=
`\mathbb `{=tex}E\_{a_t`\sim`{=tex}`\pi`{=tex}\_`\theta`{=tex}}
`\left[-\log\alpha\,
(\log\pi_\theta(a_t\mid s_t)+\mathcal H_{\text{obj}})\right]`{=tex}\]

La forma exacta y el signo dependen de la convención usada para definir
la entropía objetivo y la pérdida. La implementación debe verificarse
junto con el signo del gradiente. No se debe copiar una ecuación aislada
sin comprobarla contra el código.

Para acciones continuas de dimensión (d_a), una inicialización frecuente
es:

\[ `\mathcal `{=tex}H\_{`\text{obj}`{=tex}}`\approx `{=tex}-d_a \]

Es una heurística habitual, no una ley universal. En un robot de muchas
articulaciones, el objetivo de entropía y el escalado de las acciones
requieren especial atención.

------------------------------------------------------------------------

## 5. Las ecuaciones centrales de SAC moderno

Esta sección presenta la variante moderna de SAC sin una red (V(s))
separada. Versiones anteriores incluían una red de valor adicional, por
lo que las ecuaciones y el número de redes pueden diferir entre
implementaciones.

### 5.1 Objetivo de Bellman suavizado

Se toma una transición del buffer:

\[ (s,a,r,s',d)`\sim`{=tex}`\mathcal `{=tex}D \]

Se muestrea una nueva acción del actor actual para el estado siguiente:

\[
a'`\sim`{=tex}`\pi`{=tex}\_`\theta`{=tex}(`\cdot`{=tex}`\mid `{=tex}s')
\]

El objetivo de los críticos es:

\[ y=r+`\gamma`{=tex}(1-d) `\left[
\min_{i\in\{1,2\}}Q_{\bar\phi_i}(s',a')
-\alpha\log\pi_\theta(a'\mid s')
\right]`{=tex}\]

Interpretación:

-   (r): recompensa inmediata guardada en el buffer.
-   (`\gamma`{=tex}): cuánto importa el futuro.
-   (d): indicador de terminación verdadera del episodio.
-   (Q\_{`\bar`{=tex}`\phi`{=tex}\_i}): críticos objetivo.
-   (`\min`{=tex}*i Q*{`\bar`{=tex}`\phi`{=tex}\_i}): estimación
    conservadora del valor futuro.
-   (-`\alpha`{=tex}`\log`{=tex}`\pi`{=tex}(a'`\mid `{=tex}s')):
    contribución de entropía.
-   (1-d): anula el valor futuro cuando la transición termina realmente
    el episodio.

**Importante:** en entornos con límite artificial de duración, hay que
distinguir "terminó el episodio por éxito/fallo" de "se agotó el tiempo
límite". Confundir `terminated` y `truncated` puede sesgar el objetivo
de Bellman.

### 5.2 Pérdida de cada crítico

Cada crítico minimiza el error cuadrático medio entre su predicción y el
objetivo:

\[ L\_{Q_i}(`\phi`{=tex}*i)=
`\mathbb `{=tex}E*{(s,a,r,s',d)`\sim`{=tex}`\mathcal `{=tex}D} `\left[
\left(Q_{\phi_i}(s,a)-y\right)^2
\right]`{=tex}\]

La pérdida conjunta suele ser:

\[ L_Q=L\_{Q_1}+L\_{Q_2} \]

El objetivo (y) se calcula sin propagar gradientes hacia el actor ni
hacia las redes objetivo. En PyTorch esto suele hacerse dentro de
`torch.no_grad()`.

### 5.3 Pérdida del actor

El actor intenta encontrar acciones con alto valor Q sin perder la
regularización entrópica:

\[ J\_`\pi`{=tex}(`\theta`{=tex})=
`\mathbb `{=tex}E\_{s`\sim`{=tex}`\mathcal `{=tex}D,,a`\sim`{=tex}`\pi`{=tex}\_`\theta`{=tex}}
`\left[
\min_i Q_{\phi_i}(s,a)
-\alpha\log\pi_\theta(a\mid s)
\right]`{=tex}\]

Como los optimizadores habituales minimizan una pérdida, se implementa
el negativo:

\[ L\_`\pi`{=tex}(`\theta`{=tex})= `\mathbb `{=tex}E`\left[
\alpha\log\pi_\theta(a\mid s)
-\min_i Q_{\phi_i}(s,a)
\right]`{=tex}\]

Las acciones usadas para actualizar el actor se vuelven a muestrear de
la política actual. No se usa directamente la acción antigua del buffer
como acción del actor.

### 5.4 Actualización de redes objetivo

Con la convención (`\tau`{=tex}) pequeño:

\[
`\bar`{=tex}`\phi`{=tex}\_i`\leftarrow`{=tex}`\tau`{=tex}`\phi`{=tex}\_i+(1-`\tau`{=tex})`\bar`{=tex}`\phi`{=tex}\_i
\]

Ejemplo: si (`\tau=0.005`{=tex}), cada actualización mueve lentamente la
red objetivo un 0.5 % hacia los parámetros actuales. El valor concreto
debe validarse para la frecuencia de actualización utilizada.

### 5.5 Resumen de una actualización

En cada lote de entrenamiento, el ciclo típico es:

1.  Extraer un lote del Replay Buffer.
2.  Muestrear acciones siguientes con el actor actual.
3.  Calcular (y) usando los críticos objetivo y la entropía.
4.  Actualizar los dos críticos.
5.  Muestrear acciones actuales y actualizar el actor.
6.  Si corresponde, actualizar (`\alpha`{=tex}).
7.  Actualizar las redes objetivo mediante promedio móvil.

Las implementaciones pueden variar en el orden exacto, la frecuencia
relativa de los pasos y el uso de ajuste automático de temperatura.

------------------------------------------------------------------------

## 6. Política gaussiana, reparametrización y límites de acción

### 6.1 Muestreo reparametrizado

Para que el gradiente del actor pueda atravesar el muestreo de la
acción, se usa la reparametrización:

\[
u=`\mu`{=tex}*`\theta`{=tex}(s)+`\sigma`{=tex}*`\theta`{=tex}(s)`\odot`{=tex}`\epsilon`{=tex},
`\qquad `{=tex}`\epsilon`{=tex}`\sim`{=tex}`\mathcal `{=tex}N(0,I) \]

Luego se transforma la acción:

\[ a=`\tanh`{=tex}(u) \]

La función `tanh` limita cada componente a ((-1,1)). Para un actuador
con límites físicos diferentes, se escala:

\[ a\_{`\text{físico}`{=tex}}=b+c`\odot `{=tex}a \]

donde (b=(a\_{`\max`{=tex}}+a\_{`\min`{=tex}})/2) y
(c=(a\_{`\max`{=tex}}-a\_{`\min`{=tex}})/2), componente a componente.

### 6.2 Corrección de la log-probabilidad

Al aplicar `tanh`, la distribución cambia. Por ello, la log-probabilidad
debe corregirse con el jacobiano de la transformación:

\[ `\log`{=tex}`\pi`{=tex}(a`\mid `{=tex}s)= `\sum`{=tex}\_j`\left[
\log\mathcal N(u_j;\mu_j,\sigma_j)
-\log(1-\tanh^2(u_j)+\varepsilon)
\right]`{=tex}\]

Si además se escala la acción por un rango distinto de 1, también debe
considerarse el término del cambio de escala al calcular la densidad en
el espacio de acciones físicas. Muchas implementaciones calculan la
política en el espacio normalizado y aplican la escala al enviar
acciones al entorno; la convención debe ser consistente.

Un error frecuente es omitir la corrección `tanh`: la entropía calculada
queda mal y eso afecta el entrenamiento del actor y el ajuste de
temperatura.

### 6.3 Ejemplo de actor gaussiano en PyTorch

El siguiente fragmento es didáctico. Muestra el cálculo de una acción
normalizada y su log-probabilidad; no es un entrenador completo ni una
política lista para accionar un robot real.

``` python
import torch
import torch.nn as nn
from torch.distributions import Normal

LOG_STD_MIN = -20
LOG_STD_MAX = 2

class GaussianActor(nn.Module):
    def __init__(self, obs_dim, act_dim, hidden=256):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(obs_dim, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
        )
        self.mu = nn.Linear(hidden, act_dim)
        self.log_std = nn.Linear(hidden, act_dim)

    def forward(self, obs):
        h = self.backbone(obs)
        mu = self.mu(h)
        log_std = self.log_std(h).clamp(LOG_STD_MIN, LOG_STD_MAX)
        std = log_std.exp()

        dist = Normal(mu, std)
        u = dist.rsample()            # reparametrización
        action = torch.tanh(u)        # acción normalizada en (-1, 1)

        log_prob = dist.log_prob(u)
        correction = torch.log(1 - action.pow(2) + 1e-6)
        log_prob = (log_prob - correction).sum(dim=-1, keepdim=True)

        deterministic_action = torch.tanh(mu)
        return action, log_prob, deterministic_action
```

En evaluación, puede utilizarse `deterministic_action` para reducir la
variabilidad. En entrenamiento se suele usar la muestra estocástica.

------------------------------------------------------------------------

## 7. Recompensa: ¿es escalar, multivaluada o multiobjetivo?

Esta distinción es importante en robótica.

### 7.1 SAC estándar recibe una recompensa escalar

La formulación habitual de SAC usa:

\[ r_t`\in`{=tex}`\mathbb `{=tex}R \]

Es decir, **una sola cantidad numérica por transición**. Esa cantidad
puede calcularse combinando muchas métricas: velocidad, equilibrio,
energía, caídas, seguimiento de consigna, etc.

Que la recompensa tenga varios términos no significa que SAC esté
recibiendo una recompensa vectorial. Por ejemplo:

\[ r_t=w_v r\_{`\text{velocidad}`{=tex}} +w_b
r\_{`\text{equilibrio}`{=tex}} +w_e r\_{`\text{energía}`{=tex}} +w_c
r\_{`\text{contacto}`{=tex}} -r\_{`\text{penalizaciones}`{=tex}} \]

Los pesos (w_i) determinan el compromiso entre objetivos. Sus magnitudes
importan: si un término vale cientos y otro centésimas, el primero puede
dominar el aprendizaje.

### 7.2 Ejemplo de recompensa para caminar

Una recompensa ilustrativa para un humanoide podría ser:

\[ r_t = w_v e\^{-`\frac{(v_x-v_x^*)^2}{\sigma_v^2}`{=tex}} +w_y
e\^{-`\frac{(v_y-v_y^*)^2}{\sigma_y^2}`{=tex}}
+w\_`\omega `{=tex}e\^{-`\frac{(\omega_z-\omega_z^*)^2}{\sigma_\omega^2}`{=tex}}
-w\_{`\text{tilt}`{=tex}}(`\theta`{=tex}*{`\text{roll}`{=tex}}\^2+`\theta`{=tex}*{`\text{pitch}`{=tex}}\^2)
-w\_{`\text{energy}`{=tex}}\|
`\tau`{=tex}*t`\odot`{=tex}`\dot `{=tex}q_t\|*1
-w*{`\text{action}`{=tex}}\|a_t-a*{t-1}\|\^2
-r\_{`\text{fall}`{=tex}}`\mathbf1`{=tex}\_{`\text{caída}`{=tex}} \]

Donde:

-   (v_x,v_y): velocidades medidas del torso.
-   (v_x\^*,v_y\^*): velocidades objetivo.
-   (`\omega`{=tex}\_z,`\omega`{=tex}\_z\^\*): velocidad angular de
    guiñada real y deseada.
-   (`\theta`{=tex}*{`\text{roll}`{=tex}},`\theta`{=tex}*{`\text{pitch}`{=tex}}):
    inclinación del torso.
-   (`\tau`{=tex}\_t): pares articulares.
-   (`\dot `{=tex}q_t): velocidades articulares.
-   (a_t-a\_{t-1}): variación de la acción.
-   (`\mathbf1`{=tex}\_{`\text{caída}`{=tex}}): vale 1 si se detectó una
    caída.

Los términos exponenciales ofrecen una recompensa alta cuando el error
es pequeño y disminuyen suavemente con el error. Las penalizaciones
buscan evitar inclinaciones excesivas, gasto energético, cambios bruscos
y caídas.

**Esto es un ejemplo de diseño, no una recomendación de copiar los pesos
sin pruebas.** Los términos deben normalizarse, verificarse con
trayectorias reales y ajustarse según la tarea. También hay que
comprobar si el simulador permite medir torque, contactos y velocidades
con las unidades esperadas.

### 7.3 Implementación de recompensa escalar

``` python
import numpy as np

def walking_reward(obs, action, prev_action, torque, joint_velocity,
                   target_vx, target_vy, fallen, weights):
    # Ejemplo de claves esperadas en obs; adaptar a la estructura real.
    vx = float(obs["torso_vx"])
    vy = float(obs["torso_vy"])
    roll = float(obs["roll"])
    pitch = float(obs["pitch"])

    r_velocity = np.exp(-((vx - target_vx) ** 2) / 0.25)
    r_lateral = np.exp(-((vy - target_vy) ** 2) / 0.25)
    p_tilt = roll**2 + pitch**2
    p_energy = np.sum(np.abs(torque * joint_velocity))
    p_smooth = np.sum((action - prev_action) ** 2)
    p_fall = 1.0 if fallen else 0.0

    reward = (
        weights["velocity"] * r_velocity
        + weights["lateral"] * r_lateral
        - weights["tilt"] * p_tilt
        - weights["energy"] * p_energy
        - weights["smooth"] * p_smooth
        - weights["fall"] * p_fall
    )
    return float(reward)
```

La función debe devolver un escalar finito. Conviene registrar cada
componente por separado, además de la recompensa total. Si sólo se
guarda la suma, será difícil descubrir qué término está dominando.

### 7.4 ¿Qué pasa si realmente se necesita recompensa vectorial?

Si el entorno devuelve algo como:

\[
`\mathbf `{=tex}r_t=(r\_{`\text{velocidad}`{=tex}},r\_{`\text{equilibrio}`{=tex}},r\_{`\text{energía}`{=tex}})
\]

eso es una recompensa vectorial o un problema multiobjetivo. El SAC
estándar descrito aquí no resuelve directamente una optimización
vectorial con preferencias independientes. Las opciones incluyen:

1.  **Escalarizar:** combinar los componentes con pesos y entrenar el
    SAC estándar.
2.  **Condicionar la política a preferencias:** pasar pesos u objetivos
    como parte de la observación y entrenar para varias preferencias.
3.  **Usar métodos multiobjetivo específicos:** si se requiere conservar
    explícitamente el frente de Pareto en lugar de fijar un compromiso
    único.

La opción más simple suele ser la primera, pero los pesos deben ser
explícitos y la recompensa debe reflejar las prioridades reales de la
tarea.

### 7.5 Buenas prácticas para recompensas

-   Registrar por separado cada término y su distribución.
-   Comprobar que todas las magnitudes son finitas (`NaN` e `Inf` deben
    detenerse o registrarse como error).
-   Vigilar el rango de cada componente.
-   Evitar recompensas que sólo se obtengan por explotar un error del
    simulador.
-   Penalizar caídas con un criterio verificable, no sólo con una
    inclinación arbitraria.
-   No premiar la velocidad si el robot está fuera de control.
-   Evaluar también estabilidad, tasa de éxito, energía, suavidad y
    generalización.
-   Separar las recompensas de entrenamiento de las métricas de
    evaluación cuando sea conveniente.

------------------------------------------------------------------------

## 8. Acciones continuas, discretas y "multivaluadas"

SAC se asocia principalmente con acciones continuas, como consignas
articulares normalizadas entre -1 y 1. La variante habitual usa una
política gaussiana transformada por `tanh`.

Existen variantes de SAC para acciones discretas, en las que la política
produce probabilidades sobre un conjunto finito de acciones. No se debe
asumir que una implementación de SAC para acciones continuas admite
acciones discretas sin cambios.

La palabra **multivaluada** puede referirse a conceptos distintos:

-   **Acción multidimensional:** una acción es un vector, por ejemplo 29
    consignas articulares. Sigue siendo una acción continua vectorial y
    es compatible con SAC continuo.
-   **Recompensa con varios componentes:** varias métricas se combinan
    en una recompensa escalar; es compatible con SAC estándar.
-   **Recompensa vectorial real:** cada transición devuelve varios
    objetivos independientes; requiere una estrategia multiobjetivo o
    escalarización antes de usar SAC estándar.
-   **Acción discreta:** se elige entre alternativas categóricas;
    necesita una variante compatible con acciones discretas.

Por lo tanto, hay que identificar cuál de estos sentidos aplica al
entorno concreto.

------------------------------------------------------------------------

## 9. Replay Buffer y aprendizaje off-policy

El Replay Buffer almacena transiciones:

\[ (s_t,a_t,r_t,s\_{t+1},d_t) \]

Durante la actualización se selecciona aleatoriamente un lote de tamaño
(B). El agente puede reutilizar una experiencia muchas veces y aprender
de datos generados por políticas anteriores. Esa es la ventaja principal
de ser *off-policy*.

### 9.1 Tamaño del buffer

Un buffer más grande permite conservar más experiencias, pero consume
más RAM y puede incluir datos antiguos poco representativos de la
política actual. Uno muy pequeño puede perder diversidad.

Una estimación sencilla para matrices `float32` que guardan
observaciones actuales y siguientes, acciones, recompensas y
terminaciones es:

\[ M\_{`\text{buffer}`{=tex}}`\approx`{=tex}
N(2d_s+d_a+2)`\times4`{=tex} `\text{bytes}`{=tex} \]

donde:

-   (N): capacidad de transiciones;
-   (d_s): dimensión de la observación;
-   (d_a): dimensión de la acción;
-   el término `+2` es una aproximación para recompensa y bandera de
    terminación, ambas representadas como `float32`.

No incluye sobrecarga de Python, índices, alineación ni estructuras
auxiliares. Si las observaciones se guardan en `float64`, la parte
numérica ocupa aproximadamente el doble.

**Ejemplo 1:** (d_s=100), (d_a=29), (N=10\^6):

\[ M`\approx10`{=tex}\^6(200+29+2)`\cdot4`{=tex}
=924,000,000`\text{ bytes}`{=tex} \]

Aproximadamente 0.92 GB decimales (0.86 GiB) para los arrays numéricos
principales.

**Ejemplo 2:** (d_s=200), (d_a=29), (N=10\^6):

\[ M`\approx10`{=tex}\^6(400+29+2)`\cdot4`{=tex}
=1.724`\text{ GB}`{=tex} \]

Por eso el tamaño del buffer debe elegirse con la RAM disponible y las
dimensiones reales, no sólo con una cifra de referencia.

### 9.2 Ejemplo de cálculo de memoria

``` python
def estimate_replay_buffer_gb(obs_dim, act_dim, capacity, bytes_per_value=4):
    # Aproximación: obs, next_obs, action, reward y done.
    values = capacity * (2 * obs_dim + act_dim + 2)
    bytes_total = values * bytes_per_value
    return bytes_total / 1e9

print(estimate_replay_buffer_gb(obs_dim=200, act_dim=29,
                                capacity=1_000_000))
# Aproximadamente 1.724 GB decimales
```

Antes de reservar un millón de transiciones, conviene comenzar con una
capacidad menor, medir la memoria del proceso y aumentar sólo si los
experimentos lo justifican.

------------------------------------------------------------------------

## 10. Hiperparámetros principales y sus efectos

Los valores siguientes son rangos ilustrativos de uso frecuente, no una
receta universal. La configuración válida depende de la escala de
recompensa, la dimensión de estado/acción, la frecuencia de control y la
implementación.

  ---------------------------------------------------------------------------
  Parámetro                    Símbolo  Ejemplos frecuentes Efecto /
                                                            advertencia
  --------------- -------------------- -------------------- -----------------
  Factor de           (`\gamma`{=tex})          0.99--0.999 Mayor valor
  descuento                                                 considera un
                                                            horizonte más
                                                            largo y puede
                                                            dificultar la
                                                            estimación.

  Tamaño de lote                 \(B\)             128--512 Lotes grandes
                                                            consumen más
                                                            memoria y cómputo
                                                            por
                                                            actualización.

  Capacidad de                   \(N\)    100 mil--1 millón Aumenta la
  Replay Buffer                                             diversidad
                                                            almacenada y el
                                                            uso de RAM.

  Tasa de               (`\eta`{=tex})      3e-4 como punto Demasiado alta
  aprendizaje                              inicial habitual puede
                                                            desestabilizar;
                                                            demasiado baja
                                                            puede ralentizar.

  Actualización         (`\tau`{=tex})   0.005 como ejemplo En esta
  objetivo                                            común convención,
                                                            valores pequeños
                                                            hacen el
                                                            movimiento más
                                                            lento.

  Temperatura         (`\alpha`{=tex})    fija o automática Controla el peso
                                                            de la entropía;
                                                            depende de
                                                            escalas y
                                                            dimensión.

  Ancho de red                     ---       2 capas de 256 Redes mayores
                                         unidades como base elevan cómputo y
                                                  frecuente memoria; no
                                                            garantizan mejor
                                                            aprendizaje.

  Inicio                           ---     según el entorno Puede aumentar
  aleatorio                                                 diversidad
                                                            inicial, pero
                                                            acciones
                                                            aleatorias
                                                            peligrosas
                                                            requieren
                                                            límites.

  Frecuencia de                    ---  una o más por paso, Cambia la
  actualización                                según diseño relación entre
                                                            datos nuevos y
                                                            gradientes.

  Longitud máxima                \(T\)      definida por la Debe distinguirse
  del episodio                                        tarea de una
                                                            terminación real
                                                            del entorno.
  ---------------------------------------------------------------------------

### 10.1 Relación entre escala de recompensa y temperatura

Si se multiplican todas las recompensas por un factor, cambia la escala
relativa entre recompensa y entropía. Por ello, una temperatura que
funciona con una recompensa puede no funcionar tras reescalarla. No
conviene ajustar (`\alpha`{=tex}) de forma aislada de la definición de
recompensa.

### 10.2 Relación entre observación y acción

En un humanoide, un vector de acción de 29 dimensiones no significa
automáticamente que el actor controle correctamente 29 articulaciones.
Hay que verificar:

-   orden de las articulaciones;
-   unidad y rango de cada acción;
-   articulaciones realmente actuadas;
-   escalado de la acción normalizada;
-   si la acción representa posición objetivo, velocidad, torque u otra
    magnitud;
-   frecuencia con la que se aplica la acción;
-   saturaciones y límites físicos.

Un error de orden o escala puede impedir el aprendizaje incluso cuando
las pérdidas parecen calcularse correctamente.

------------------------------------------------------------------------

## 11. Límites de funcionamiento y fallas típicas

SAC es potente, pero no es un optimizador universal.

### 11.1 Límites algorítmicos

1.  **No garantiza convergencia global.** Las redes aproximan funciones
    no lineales y el entrenamiento puede quedar atrapado en soluciones
    deficientes.
2.  **Es sensible a la recompensa.** Una señal de recompensa pobre o mal
    escalada puede conducir a comportamientos no deseados.
3.  **Consume interacciones.** Aunque reutiliza datos, necesita
    suficientes transiciones informativas.
4.  **La exploración puede ser peligrosa.** Una política estocástica
    puede producir acciones inestables; en robótica real se necesita una
    capa de seguridad.
5.  **La función Q puede estar mal estimada.** El mínimo de dos críticos
    reduce un problema, pero no lo elimina.
6.  **La simulación puede no representar el mundo real.** Diferencias de
    fricción, masa, latencia, sensores o actuadores pueden degradar la
    política transferida.
7.  **La observación puede ser insuficiente.** Si faltan variables
    importantes, la política puede no distinguir situaciones dinámicas
    diferentes.
8.  **El comportamiento puede sobreajustarse al simulador.** Hay que
    variar condiciones y evaluar fuera de las condiciones de
    entrenamiento.
9.  **La variante importa.** SAC continuo moderno, SAC discreto y
    versiones históricas con una red de valor separada no son idénticos.
10. **La función objetivo no incorpora seguridad por sí sola.** Un
    castigo por caída no reemplaza límites de torque, supervisión ni
    parada de emergencia.

### 11.2 Síntomas y posibles causas

  -----------------------------------------------------------------------
  Síntoma                 Causas posibles         Qué comprobar
  ----------------------- ----------------------- -----------------------
  La recompensa no mejora recompensa mal          graficar cada término
                          diseñada, pocas         de recompensa,
                          muestras, observaciones comprobar dimensiones y
                          erróneas, tasa de       rangos
                          aprendizaje inadecuada  

  El robot cae            acciones mal escaladas, probar acciones
  inmediatamente          reset incorrecto,       controladas, verificar
                          recompensa              límites articulares y
                          insuficiente, estado    terminación
                          inicial difícil         

  Recompensa alta pero    recompensa explotable,  observar métricas
  conducta mala           penalizaciones          físicas independientes
                          ausentes, bug en        y reproducir episodios
                          medición                

  Q crece sin control     objetivos incorrectos,  inspeccionar Q,
                          escalas extremas,       targets, recompensas y
                          máscaras de terminación `done`
                          erróneas                

  NaN o Inf               estados no finitos,     validar observaciones,
                          divisiones por cero,    acciones, recompensas,
                          inestabilidad numérica, gradientes y pérdidas
                          log-probabilidad mal    
                          calculada               

  Actor casi determinista entropía baja,          registrar `alpha`,
  muy pronto              temperatura inadecuada, `log_prob`, desviación
                          mala escala de          estándar y diversidad
                          recompensa              de acciones

  Acciones saturadas en   media/desviación        medir porcentaje de
  ±1                      extremas, escala        saturación por
                          equivocada, saturación  articulación
                          del actuador            

  Entrenamiento muy lento simulador costoso,      medir por separado paso
                          renderizado, llamadas   de entorno y
                          remotas, exceso de      actualización de redes
                          actualizaciones         

  GPU con poco uso        entorno CPU-bound,      perfilar CPU/GPU y
                          transferencias          evitar transferir
                          frecuentes, lotes       tensores repetidamente
                          pequeños                

  Funciona en simulación, brecha sim-to-real,     aleatorización de
  falla en robot          latencia, ruido,        dominio, pruebas
                          límites físicos         seguras y supervisión
                          diferentes              
  -----------------------------------------------------------------------

### 11.3 Qué significa "convergencia"

No debe declararse convergencia porque la pérdida del crítico baje o
porque una sola recompensa sea alta. En RL, la pérdida puede bajar
mientras la política no mejora.

Una evaluación robusta debería medir, durante varios episodios y
semillas:

-   recompensa media y dispersión;
-   tasa de éxito;
-   tasa de caída;
-   duración de los episodios;
-   error de seguimiento de consigna;
-   energía o esfuerzo;
-   suavidad de acciones;
-   estabilidad ante condiciones iniciales diferentes.

La política final se debe probar sin exploración estocástica o con la
configuración de evaluación definida, y en condiciones no usadas para
ajustar los parámetros.

------------------------------------------------------------------------

## 12. Tiempo de entrenamiento: cómo estimarlo correctamente

No existe un tiempo universal para entrenar SAC. Depende de cuántos
pasos se necesitan, cuánto tarda el simulador por paso y cuánto cuesta
cada actualización de redes.

Una estimación simple es:

\[ T\_{`\text{total}`{=tex}}`\approx`{=tex}
N\_{`\text{env}`{=tex}},t\_{`\text{env}`{=tex}}
+N\_{`\text{updates}`{=tex}},t\_{`\text{update}`{=tex}}
+T\_{`\text{evaluación}`{=tex}}+T\_{`\text{guardado}`{=tex}} \]

donde:

-   (N\_{`\text{env}`{=tex}}): pasos de interacción con el entorno;
-   (t\_{`\text{env}`{=tex}}): tiempo medio por paso de simulación;
-   (N\_{`\text{updates}`{=tex}}): cantidad total de actualizaciones de
    gradiente;
-   (t\_{`\text{update}`{=tex}}): tiempo medio de una actualización;
-   los últimos términos incluyen evaluación, inicialización y escritura
    de checkpoints.

Si se realiza aproximadamente una actualización por paso,
(N\_{`\text{updates}`{=tex}}) puede ser del mismo orden que
(N\_{`\text{env}`{=tex}}). Si se hacen varias actualizaciones por paso,
el costo de entrenamiento aumenta.

### 12.1 Ejemplo puramente ilustrativo

Supongamos 500.000 pasos de entorno y una actualización por paso. Si el
paso de entorno tarda 10 ms y la actualización 4 ms:

-   interacción: (500,000`\times0.010`{=tex}=5,000) s;
-   actualizaciones: (500,000`\times0.004`{=tex}=2,000) s;
-   total aproximado: 7.000 s, unos 1,94 h, antes de evaluaciones y
    sobrecostes.

Si el paso del simulador tarda 50 ms, la interacción por sí sola
requiere 25.000 s, casi 6,95 h. El ejemplo muestra que la velocidad del
simulador puede dominar al costo de la red.

**No son tiempos medidos en GIAR-ORION.** Para estimar el entrenamiento
real, medir durante unos minutos: 1. pasos de entorno por segundo; 2.
actualizaciones por segundo; 3. tiempo de reset; 4. tiempo de
evaluación; 5. uso de CPU, RAM, VRAM y GPU.

Luego extrapolar al número de pasos previsto. Los primeros minutos
pueden ser más lentos por inicialización, compilación, carga de modelos
o cachés.

### 12.2 Episodios no son una unidad suficiente

"300 episodios" puede significar muy poco o mucho trabajo según la
duración de cada episodio. Si cada episodio tiene 200 pasos, son 60.000
pasos; si tiene 5.000 pasos, son 1.500.000. Para comparar experimentos,
registrar pasos de entorno, actualizaciones, duración y configuración,
además del número de episodios.

------------------------------------------------------------------------

## 13. Memoria y hardware

Hay que separar **RAM del sistema** y **memoria de GPU (VRAM)**.

### 13.1 RAM

La RAM puede incluir:

-   Replay Buffer;
-   proceso del simulador;
-   observaciones y registros;
-   Python y bibliotecas;
-   múltiples entornos paralelos;
-   checkpoints temporales y herramientas de diagnóstico.

El Replay Buffer suele ser uno de los consumidores previsibles y puede
estimarse con la fórmula de la sección 9. Si el simulador guarda
geometría, sensores o imágenes, el consumo adicional puede ser
importante.

### 13.2 VRAM

La VRAM se utiliza para:

-   parámetros de las redes;
-   gradientes;
-   estados del optimizador (por ejemplo, Adam);
-   tensores de entrada y objetivos;
-   activaciones intermedias;
-   lotes de entrenamiento.

Para redes MLP relativamente pequeñas y observaciones vectoriales, el
modelo SAC puede ocupar bastante menos memoria que un modelo de visión
por imágenes. Pero la cifra exacta depende de las dimensiones y del
lote. El buffer suele mantenerse en RAM y no necesariamente en VRAM;
algunas implementaciones transfieren lotes a la GPU en cada
actualización.

En una GPU con 8 GB de VRAM, como la RTX 5070 Laptop de este entorno,
una implementación SAC MLP de tamaño moderado suele ser razonable como
punto de partida. No se puede prometer un consumo fijo sin medirlo.
Simulación, renderizado, otros procesos de GPU y lotes grandes pueden
cambiar el margen disponible.

### 13.3 Medir consumo real en PyTorch

``` python
import torch

if torch.cuda.is_available():
    torch.cuda.reset_peak_memory_stats()
    # Ejecutar aquí una iteración real de entrenamiento.
    torch.cuda.synchronize()
    allocated = torch.cuda.memory_allocated() / (1024 ** 3)
    reserved = torch.cuda.memory_reserved() / (1024 ** 3)
    peak = torch.cuda.max_memory_allocated() / (1024 ** 3)

    print(f"VRAM asignada: {allocated:.3f} GiB")
    print(f"VRAM reservada por PyTorch: {reserved:.3f} GiB")
    print(f"Pico asignado: {peak:.3f} GiB")
else:
    print("CUDA no está disponible; se está ejecutando en CPU.")
```

`memory_allocated` mide memoria ocupada por tensores administrados por
PyTorch; `memory_reserved` incluye memoria reservada por su asignador.
Ninguna de estas cifras representa por sí sola todo el uso de VRAM del
sistema operativo ni de otras aplicaciones.

### 13.4 Medir tiempo y velocidad

``` python
import time

n_steps = 1000
start = time.perf_counter()

for _ in range(n_steps):
    # Sustituir por una interacción real con el entorno.
    env.step(action)

elapsed = time.perf_counter() - start
print(f"Tiempo por paso: {elapsed / n_steps:.6f} s")
print(f"Pasos por segundo: {n_steps / elapsed:.2f}")
```

Este fragmento presupone que `env` y `action` ya están definidos. Para
medir correctamente hay que incluir la preparación real de acciones,
llamadas a la API remota y recepción de observaciones.

------------------------------------------------------------------------

## 14. Un núcleo ilustrativo de las pérdidas SAC en PyTorch

El fragmento siguiente muestra el núcleo matemático de una
actualización, suponiendo que existen `actor`, `critic1`, `critic2`,
`target_critic1`, `target_critic2`, sus optimizadores y un lote ya
convertido a tensores. No reemplaza la implementación completa: se
omiten detalles de arquitectura, normalización, gestión de episodios y
guardado.

``` python
import torch
import torch.nn.functional as F

def update_critics_and_actor(batch, actor,
                             critic1, critic2,
                             target_critic1, target_critic2,
                             actor_optimizer, critic_optimizer,
                             alpha, gamma):
    obs = batch["obs"]
    actions = batch["actions"]
    rewards = batch["rewards"].view(-1, 1)
    next_obs = batch["next_obs"]
    dones = batch["dones"].view(-1, 1).float()

    # 1. Objetivo de Bellman suavizado.
    with torch.no_grad():
        next_actions, next_log_prob, _ = actor(next_obs)
        next_q1 = target_critic1(next_obs, next_actions)
        next_q2 = target_critic2(next_obs, next_actions)
        next_q = torch.minimum(next_q1, next_q2)
        target_q = rewards + gamma * (1.0 - dones) * (
            next_q - alpha * next_log_prob
        )

    # 2. Actualizar críticos.
    current_q1 = critic1(obs, actions)
    current_q2 = critic2(obs, actions)
    critic_loss = (
        F.mse_loss(current_q1, target_q)
        + F.mse_loss(current_q2, target_q)
    )

    critic_optimizer.zero_grad(set_to_none=True)
    critic_loss.backward()
    critic_optimizer.step()

    # 3. Actualizar actor con acciones nuevas de la política actual.
    new_actions, log_prob, _ = actor(obs)
    q1_pi = critic1(obs, new_actions)
    q2_pi = critic2(obs, new_actions)
    min_q_pi = torch.minimum(q1_pi, q2_pi)
    actor_loss = (alpha * log_prob - min_q_pi).mean()

    actor_optimizer.zero_grad(set_to_none=True)
    actor_loss.backward()
    actor_optimizer.step()

    return {
        "critic_loss": float(critic_loss.detach().cpu()),
        "actor_loss": float(actor_loss.detach().cpu()),
        "q_mean": float(min_q_pi.detach().mean().cpu()),
        "log_prob_mean": float(log_prob.detach().mean().cpu()),
    }
```

### Advertencias sobre el ejemplo

1.  `actor(obs)` debe devolver una acción reparametrizada, la
    log-probabilidad corregida por `tanh` y una acción determinista.
2.  Los críticos deben devolver un escalar por transición, normalmente
    con forma `[batch, 1]`.
3.  La máscara `dones` debe reflejar correctamente la semántica de
    terminación y truncamiento del entorno.
4.  Si `alpha` es automático, debe calcularse y optimizarse mediante una
    pérdida adicional.
5.  Después de la actualización se deben actualizar las redes objetivo.
6.  Para evitar que el actor acumule gradientes en los críticos durante
    su actualización, algunas implementaciones congelan temporalmente
    sus parámetros. No siempre es obligatorio para la corrección
    numérica, pero puede ahorrar cómputo.
7.  No ejecutar este fragmento con un robot real sin validación, límites
    físicos, parada de emergencia y supervisión.

### 14.1 Actualización Polyak en PyTorch

``` python
@torch.no_grad()
def soft_update(source, target, tau=0.005):
    for source_param, target_param in zip(
        source.parameters(), target.parameters()
    ):
        target_param.lerp_(source_param, tau)
```

La función `lerp_` hace que `target_param` se desplace una fracción
`tau` hacia `source_param`. Si la implementación usa una variable
llamada `polyak` cercana a 1, posiblemente utilice la convención
complementaria.

------------------------------------------------------------------------

## 15. Protocolo recomendado para evaluar un SAC de robótica

Antes de entrenar durante muchas horas, seguir un proceso de validación
por etapas.

### Etapa A: validar entorno y datos

-   Confirmar dimensiones y tipos de observación y acción.
-   Verificar que no existan `NaN` ni `Inf`.
-   Comprobar los límites de cada acción.
-   Ejecutar resets repetidos y comprobar que el estado inicial sea
    válido.
-   Ejecutar acciones simples o aleatorias acotadas y verificar que el
    simulador responda como se espera.
-   Confirmar el significado de `terminated`, `truncated` y `done`.

### Etapa B: validar recompensa

-   Calcular cada componente de recompensa en trayectorias conocidas.
-   Verificar signos: lo deseable debe aumentar la recompensa y lo
    indeseable debe reducirla.
-   Revisar rangos y unidades.
-   Comprobar casos extremos: caída, estado inválido, límite articular,
    objetivo alcanzado.
-   Guardar histogramas o estadísticas por componente.

### Etapa C: validar actualizaciones

-   Ejecutar un lote artificial pequeño.
-   Confirmar que pérdidas y gradientes sean finitos.
-   Comprobar que los parámetros cambien tras `optimizer.step()`.
-   Confirmar que las redes objetivo cambien lentamente.
-   Revisar que la log-probabilidad tenga la forma esperada.
-   Comprobar el valor y la evolución de (`\alpha`{=tex}).

### Etapa D: medir rendimiento

-   Medir pasos de entorno por segundo.
-   Medir actualizaciones por segundo.
-   Medir RAM y VRAM tras inicializar las redes y ejecutar
    actualizaciones reales.
-   Desactivar renderizado innecesario durante entrenamiento, si el
    entorno lo permite.
-   Registrar versión de Python, PyTorch, CUDA, simulador y
    configuración.

### Etapa E: entrenamiento y evaluación

-   Fijar semillas y guardar la configuración exacta.
-   Registrar recompensa media, dispersión y métricas físicas.
-   Evaluar periódicamente la política sin exploración adicional.
-   Guardar checkpoints y reanudar desde ellos.
-   Repetir la evaluación con varias semillas y condiciones iniciales.
-   No transferir a hardware real hasta probar límites, latencias,
    supervisión y mecanismos de parada.

------------------------------------------------------------------------

## 16. Lista de comprobación para auditar una implementación concreta

Para saber qué hace realmente un repositorio SAC, inspeccionar:

-   [ ] Definición exacta del vector de observación.
-   [ ] Orden y dimensión de las acciones.
-   [ ] Escala y límites físicos de cada acción.
-   [ ] Arquitectura del actor.
-   [ ] Arquitectura de los dos críticos.
-   [ ] Uso de redes objetivo.
-   [ ] Fórmula exacta de la pérdida del actor.
-   [ ] Fórmula exacta del objetivo de Bellman.
-   [ ] Corrección de log-probabilidad para la transformación `tanh`.
-   [ ] Temperatura fija o automática y su pérdida.
-   [ ] Tamaño y tipo de datos del Replay Buffer.
-   [ ] Tamaño del lote.
-   [ ] Factor de descuento y tasa de aprendizaje.
-   [ ] Convención del coeficiente Polyak.
-   [ ] Frecuencia de actualizaciones por paso de entorno.
-   [ ] Tratamiento de `terminated` frente a `truncated`.
-   [ ] Fórmula de recompensa y componentes registrados.
-   [ ] Condiciones de caída y fin de episodio.
-   [ ] Guardado y carga de redes, optimizadores y temperatura.
-   [ ] Evaluación independiente del entrenamiento.
-   [ ] Medición de tiempo por paso, RAM y VRAM.

**La documentación general explica el algoritmo; el código determina la
variante exacta que se está ejecutando.** Para evaluar un entrenamiento
concreto hay que comparar las ecuaciones anteriores con las funciones de
pérdida, la configuración y el entorno real.

------------------------------------------------------------------------

## 17. Glosario

-   **Actor:** red que representa la política y genera acciones.
-   **Crítico:** red que estima el valor Q de un estado y una acción.
-   **Q-value:** retorno futuro descontado estimado.
-   **Off-policy:** permite aprender de transiciones generadas por
    políticas anteriores.
-   **Replay Buffer:** memoria de transiciones reutilizadas para
    entrenar.
-   **Entropía:** medida de dispersión de la política.
-   **Temperatura (`\alpha`{=tex}):** coeficiente que pondera la
    entropía.
-   **Objetivo de Bellman:** valor de referencia usado para entrenar los
    críticos.
-   **Red objetivo:** copia actualizada lentamente para estabilizar los
    objetivos.
-   **Reparametrización:** forma de muestrear una acción manteniendo un
    camino de gradiente hacia el actor.
-   **Política estocástica:** política que define una distribución sobre
    acciones.
-   **Saturación:** situación en la que una acción llega repetidamente a
    sus límites.
-   **Sim-to-real:** transferencia de una política aprendida en
    simulación a un robot físico.
-   **Escalarización:** combinación de varios objetivos en una sola
    recompensa.
-   **Truncamiento:** fin de un segmento por límite externo, que no
    siempre equivale a una terminación terminal del proceso.

------------------------------------------------------------------------

## 18. Referencias técnicas

1.  Haarnoja, T. et al. (2018). **Soft Actor-Critic: Off-Policy Maximum
    Entropy Deep Reinforcement Learning with a Stochastic Actor.**
    arXiv:1801.01290.\
    https://arxiv.org/abs/1801.01290

2.  Haarnoja, T. et al. (2018). **Soft Actor-Critic Algorithms and
    Applications.** arXiv:1812.05905.\
    https://arxiv.org/abs/1812.05905

3.  OpenAI Spinning Up. **Soft Actor-Critic.** Presenta la formulación
    moderna sin red de valor separada, las pérdidas, el pseudocódigo y
    los hiperparámetros de referencia.\
    https://spinningup.openai.com/en/latest/algorithms/sac.html

4.  Implementación de referencia de OpenAI Spinning Up en PyTorch.\
    https://github.com/openai/spinningup/blob/master/spinup/algos/pytorch/sac/sac.py

------------------------------------------------------------------------

## 19. Conclusiones

SAC combina una política estocástica, dos críticos, objetivos suavizados
por entropía y reutilización de experiencias. La pérdida del crítico
busca aproximar el objetivo de Bellman; la pérdida del actor favorece
acciones con alto valor estimado y regula la aleatoriedad; la
temperatura controla el compromiso entre recompensa y entropía.

En robótica, la calidad del resultado depende tanto del algoritmo como
del diseño de la recompensa, la semántica de observaciones y acciones,
la fidelidad del simulador y la calidad de la evaluación. Una recompensa
con varios componentes normalmente se convierte en un escalar antes de
alimentar al SAC estándar. Una recompensa realmente vectorial requiere
una formulación multiobjetivo o una escalarización explícita.

Los tiempos y el consumo de memoria deben medirse en el entorno
concreto. El número de episodios por sí solo no permite estimar el
esfuerzo de entrenamiento. La forma más fiable de planificar es medir
pasos por segundo, actualizaciones por segundo, tamaño del Replay
Buffer, RAM y pico de VRAM, y luego extrapolar.

Este documento es una guía técnica general. Para certificar el
comportamiento de una implementación específica de GIAR-ORION, se deben
revisar sus archivos de configuración, las redes, el motor de
recompensa, el buffer, el ciclo de actualización y los registros
experimentales.
