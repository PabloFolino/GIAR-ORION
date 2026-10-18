# Unitree G1 — referencia técnica derivada de `g1_29dof_with_hand.xml`

> **Fuente única:** archivo MJCF `g1_29dof_with_hand.xml` suministrado para esta conversión.
> Este documento describe lo que está declarado en ese XML. No completa datos ausentes con documentación externa.
> Las coordenadas, límites, masas, inercias y parámetros se transcriben del archivo fuente.

## 1. Identificación y configuración general

- Modelo MJCF: `g1_29dof_with_hand`.
- Unidad angular declarada por el compilador: `radian`.
- Directorio de mallas declarado: `meshes`.
- El archivo contiene secciones `asset`, `worldbody`, `actuator`, `sensor`, `statistic` y `visual`.
- La base del robot se modela con una articulación libre llamada `floating_base_joint`.

## 2. Resumen estructural

- Declaraciones de malla (`mesh`): **50**.
- Declaraciones de cuerpo (`body`): **1**.
- Declaraciones de articulación (`joint`, incluidos tipos libres): **44**.
- Actuadores declarados: **43**.
- Geometrías (`geom`): **104**.
- Sitios (`site`): **2**.
- Sensores: **4**.

Estas cantidades cuentan declaraciones del XML; no son una validación de que el modelo compile o simule correctamente.

## 3. Árbol cinemático de cuerpos

El siguiente árbol se reconstruye por anidamiento de etiquetas `body` en `worldbody`. Cada elemento hijo está contenido en el cuerpo padre indicado por la estructura XML.

- `pelvis` — joints: `floating_base_joint`; pos=`0 0 0.793`
  - `left_hip_pitch_link` — joints: `left_hip_pitch_joint`; pos=`0 0.064452 -0.1027`
    - `left_hip_roll_link` — joints: `left_hip_roll_joint`; pos=`0 0.052 -0.030465`; quat=`0.996179 0 -0.0873386 0`
      - `left_hip_yaw_link` — joints: `left_hip_yaw_joint`; pos=`0.025001 0 -0.12412`
        - `left_knee_link` — joints: `left_knee_joint`; pos=`-0.078273 0.0021489 -0.17734`; quat=`0.996179 0 0.0873386 0`
          - `left_ankle_pitch_link` — joints: `left_ankle_pitch_joint`; pos=`0 -9.4445e-05 -0.30001`
            - `left_ankle_roll_link` — joints: `left_ankle_roll_joint`; pos=`0 0 -0.017558`
  - `right_hip_pitch_link` — joints: `right_hip_pitch_joint`; pos=`0 -0.064452 -0.1027`
    - `right_hip_roll_link` — joints: `right_hip_roll_joint`; pos=`0 -0.052 -0.030465`; quat=`0.996179 0 -0.0873386 0`
      - `right_hip_yaw_link` — joints: `right_hip_yaw_joint`; pos=`0.025001 0 -0.12412`
        - `right_knee_link` — joints: `right_knee_joint`; pos=`-0.078273 -0.0021489 -0.17734`; quat=`0.996179 0 0.0873386 0`
          - `right_ankle_pitch_link` — joints: `right_ankle_pitch_joint`; pos=`0 9.4445e-05 -0.30001`
            - `right_ankle_roll_link` — joints: `right_ankle_roll_joint`; pos=`0 0 -0.017558`
  - `waist_yaw_link` — joints: `waist_yaw_joint`
    - `waist_roll_link` — joints: `waist_roll_joint`; pos=`-0.0039635 0 0.035`
      - `torso_link` — joints: `waist_pitch_joint`; pos=`0 0 0.019`
        - `left_shoulder_pitch_link` — joints: `left_shoulder_pitch_joint`; pos=`0.0039563 0.10022 0.23778`; quat=`0.990264 0.139201 1.38722e-05 -9.86868e-05`
          - `left_shoulder_roll_link` — joints: `left_shoulder_roll_joint`; pos=`0 0.038 -0.013831`; quat=`0.990268 -0.139172 0 0`
            - `left_shoulder_yaw_link` — joints: `left_shoulder_yaw_joint`; pos=`0 0.00624 -0.1032`
              - `left_elbow_link` — joints: `left_elbow_joint`; pos=`0.015783 0 -0.080518`
                - `left_wrist_roll_link` — joints: `left_wrist_roll_joint`; pos=`0.1 0.00188791 -0.01`
                  - `left_wrist_pitch_link` — joints: `left_wrist_pitch_joint`; pos=`0.038 0 0`
                    - `left_wrist_yaw_link` — joints: `left_wrist_yaw_joint`; pos=`0.046 0 0`
                      - `left_hand_thumb_0_link` — joints: `left_hand_thumb_0_joint`; pos=`0.067 0.003 0`
                        - `left_hand_thumb_1_link` — joints: `left_hand_thumb_1_joint`; pos=`-0.0025 -0.0193 0`
                          - `left_hand_thumb_2_link` — joints: `left_hand_thumb_2_joint`; pos=`0 -0.0458 0`
                      - `left_hand_middle_0_link` — joints: `left_hand_middle_0_joint`; pos=`0.1192 0.0046 -0.0285`
                        - `left_hand_middle_1_link` — joints: `left_hand_middle_1_joint`; pos=`0.0458 0 0`
                      - `left_hand_index_0_link` — joints: `left_hand_index_0_joint`; pos=`0.1192 0.0046 0.0285`
                        - `left_hand_index_1_link` — joints: `left_hand_index_1_joint`; pos=`0.0458 0 0`
        - `right_shoulder_pitch_link` — joints: `right_shoulder_pitch_joint`; pos=`0.0039563 -0.10021 0.23778`; quat=`0.990264 -0.139201 1.38722e-05 9.86868e-05`
          - `right_shoulder_roll_link` — joints: `right_shoulder_roll_joint`; pos=`0 -0.038 -0.013831`; quat=`0.990268 0.139172 0 0`
            - `right_shoulder_yaw_link` — joints: `right_shoulder_yaw_joint`; pos=`0 -0.00624 -0.1032`
              - `right_elbow_link` — joints: `right_elbow_joint`; pos=`0.015783 0 -0.080518`
                - `right_wrist_roll_link` — joints: `right_wrist_roll_joint`; pos=`0.1 -0.00188791 -0.01`
                  - `right_wrist_pitch_link` — joints: `right_wrist_pitch_joint`; pos=`0.038 0 0`
                    - `right_wrist_yaw_link` — joints: `right_wrist_yaw_joint`; pos=`0.046 0 0`
                      - `right_hand_thumb_0_link` — joints: `right_hand_thumb_0_joint`; pos=`0.067 -0.003 0`
                        - `right_hand_thumb_1_link` — joints: `right_hand_thumb_1_joint`; pos=`-0.0025 0.0193 0`
                          - `right_hand_thumb_2_link` — joints: `right_hand_thumb_2_joint`; pos=`0 0.0458 0`
                      - `right_hand_middle_0_link` — joints: `right_hand_middle_0_joint`; pos=`0.1192 -0.0046 -0.0285`
                        - `right_hand_middle_1_link` — joints: `right_hand_middle_1_joint`; pos=`0.0458 0 0`
                      - `right_hand_index_0_link` — joints: `right_hand_index_0_joint`; pos=`0.1192 -0.0046 0.0285`
                        - `right_hand_index_1_link` — joints: `right_hand_index_1_joint`; pos=`0.0458 0 0`

## 4. Articulaciones

Cada fila reproduce los atributos presentes en la etiqueta `joint`. Si un atributo no aparece, se indica como no declarado; no se infiere un valor predeterminado.

| Articulación | Tipo | Eje | Rango declarado | Límite de fuerza declarado |
|---|---|---|---|---|
| `floating_base_joint` | free | `no declarado` | `no declarado` | `no declarado` |
| `left_hip_pitch_joint` | hinge (predeterminado MJCF no explicitado) | `0 1 0` | `-2.5307 2.8798` | `-88 88` |
| `left_hip_roll_joint` | hinge (predeterminado MJCF no explicitado) | `1 0 0` | `-0.5236 2.9671` | `-88 88` |
| `left_hip_yaw_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `-2.7576 2.7576` | `-88 88` |
| `left_knee_joint` | hinge (predeterminado MJCF no explicitado) | `0 1 0` | `-0.087267 2.8798` | `-139 139` |
| `left_ankle_pitch_joint` | hinge (predeterminado MJCF no explicitado) | `0 1 0` | `-0.87267 0.5236` | `-50 50` |
| `left_ankle_roll_joint` | hinge (predeterminado MJCF no explicitado) | `1 0 0` | `-0.2618 0.2618` | `-50 50` |
| `right_hip_pitch_joint` | hinge (predeterminado MJCF no explicitado) | `0 1 0` | `-2.5307 2.8798` | `-88 88` |
| `right_hip_roll_joint` | hinge (predeterminado MJCF no explicitado) | `1 0 0` | `-2.9671 0.5236` | `-88 88` |
| `right_hip_yaw_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `-2.7576 2.7576` | `-88 88` |
| `right_knee_joint` | hinge (predeterminado MJCF no explicitado) | `0 1 0` | `-0.087267 2.8798` | `-139 139` |
| `right_ankle_pitch_joint` | hinge (predeterminado MJCF no explicitado) | `0 1 0` | `-0.87267 0.5236` | `-50 50` |
| `right_ankle_roll_joint` | hinge (predeterminado MJCF no explicitado) | `1 0 0` | `-0.2618 0.2618` | `-50 50` |
| `waist_yaw_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `-2.618 2.618` | `-88 88` |
| `waist_roll_joint` | hinge (predeterminado MJCF no explicitado) | `1 0 0` | `-0.52 0.52` | `-50 50` |
| `waist_pitch_joint` | hinge (predeterminado MJCF no explicitado) | `0 1 0` | `-0.52 0.52` | `-50 50` |
| `left_shoulder_pitch_joint` | hinge (predeterminado MJCF no explicitado) | `0 1 0` | `-3.0892 2.6704` | `-25 25` |
| `left_shoulder_roll_joint` | hinge (predeterminado MJCF no explicitado) | `1 0 0` | `-1.5882 2.2515` | `-25 25` |
| `left_shoulder_yaw_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `-2.618 2.618` | `-25 25` |
| `left_elbow_joint` | hinge (predeterminado MJCF no explicitado) | `0 1 0` | `-1.0472 2.0944` | `-25 25` |
| `left_wrist_roll_joint` | hinge (predeterminado MJCF no explicitado) | `1 0 0` | `-1.97222 1.97222` | `-25 25` |
| `left_wrist_pitch_joint` | hinge (predeterminado MJCF no explicitado) | `0 1 0` | `-1.61443 1.61443` | `-5 5` |
| `left_wrist_yaw_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `-1.61443 1.61443` | `-5 5` |
| `left_hand_thumb_0_joint` | hinge (predeterminado MJCF no explicitado) | `0 1 0` | `-1.0472 1.0472` | `-2.45 2.45` |
| `left_hand_thumb_1_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `-0.724312 1.0472` | `-1.4 1.4` |
| `left_hand_thumb_2_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `0 1.74533` | `-1.4 1.4` |
| `left_hand_middle_0_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `-1.5708 0` | `-1.4 1.4` |
| `left_hand_middle_1_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `-1.74533 0` | `-1.4 1.4` |
| `left_hand_index_0_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `-1.5708 0` | `-1.4 1.4` |
| `left_hand_index_1_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `-1.74533 0` | `-1.4 1.4` |
| `right_shoulder_pitch_joint` | hinge (predeterminado MJCF no explicitado) | `0 1 0` | `-3.0892 2.6704` | `-25 25` |
| `right_shoulder_roll_joint` | hinge (predeterminado MJCF no explicitado) | `1 0 0` | `-2.2515 1.5882` | `-25 25` |
| `right_shoulder_yaw_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `-2.618 2.618` | `-25 25` |
| `right_elbow_joint` | hinge (predeterminado MJCF no explicitado) | `0 1 0` | `-1.0472 2.0944` | `-25 25` |
| `right_wrist_roll_joint` | hinge (predeterminado MJCF no explicitado) | `1 0 0` | `-1.97222 1.97222` | `-25 25` |
| `right_wrist_pitch_joint` | hinge (predeterminado MJCF no explicitado) | `0 1 0` | `-1.61443 1.61443` | `-5 5` |
| `right_wrist_yaw_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `-1.61443 1.61443` | `-5 5` |
| `right_hand_thumb_0_joint` | hinge (predeterminado MJCF no explicitado) | `0 1 0` | `-1.0472 1.0472` | `-2.45 2.45` |
| `right_hand_thumb_1_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `-1.0472 0.724312` | `-1.4 1.4` |
| `right_hand_thumb_2_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `-1.74533 0` | `-1.4 1.4` |
| `right_hand_middle_0_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `0 1.5708` | `-1.4 1.4` |
| `right_hand_middle_1_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `0 1.74533` | `-1.4 1.4` |
| `right_hand_index_0_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `0 1.5708` | `-1.4 1.4` |
| `right_hand_index_1_joint` | hinge (predeterminado MJCF no explicitado) | `0 0 1` | `0 1.74533` | `-1.4 1.4` |

## 5. Actuadores

Los actuadores son elementos `<motor>` y vinculan un nombre de actuador con una articulación mediante el atributo `joint`.

| Actuador | Articulación controlada | Tipo de elemento |
|---|---|---|
| `left_hip_pitch_joint` | `left_hip_pitch_joint` | `motor` |
| `left_hip_roll_joint` | `left_hip_roll_joint` | `motor` |
| `left_hip_yaw_joint` | `left_hip_yaw_joint` | `motor` |
| `left_knee_joint` | `left_knee_joint` | `motor` |
| `left_ankle_pitch_joint` | `left_ankle_pitch_joint` | `motor` |
| `left_ankle_roll_joint` | `left_ankle_roll_joint` | `motor` |
| `right_hip_pitch_joint` | `right_hip_pitch_joint` | `motor` |
| `right_hip_roll_joint` | `right_hip_roll_joint` | `motor` |
| `right_hip_yaw_joint` | `right_hip_yaw_joint` | `motor` |
| `right_knee_joint` | `right_knee_joint` | `motor` |
| `right_ankle_pitch_joint` | `right_ankle_pitch_joint` | `motor` |
| `right_ankle_roll_joint` | `right_ankle_roll_joint` | `motor` |
| `waist_yaw_joint` | `waist_yaw_joint` | `motor` |
| `waist_roll_joint` | `waist_roll_joint` | `motor` |
| `waist_pitch_joint` | `waist_pitch_joint` | `motor` |
| `left_shoulder_pitch_joint` | `left_shoulder_pitch_joint` | `motor` |
| `left_shoulder_roll_joint` | `left_shoulder_roll_joint` | `motor` |
| `left_shoulder_yaw_joint` | `left_shoulder_yaw_joint` | `motor` |
| `left_elbow_joint` | `left_elbow_joint` | `motor` |
| `left_wrist_roll_joint` | `left_wrist_roll_joint` | `motor` |
| `left_wrist_pitch_joint` | `left_wrist_pitch_joint` | `motor` |
| `left_wrist_yaw_joint` | `left_wrist_yaw_joint` | `motor` |
| `left_hand_thumb_0_joint` | `left_hand_thumb_0_joint` | `motor` |
| `left_hand_thumb_1_joint` | `left_hand_thumb_1_joint` | `motor` |
| `left_hand_thumb_2_joint` | `left_hand_thumb_2_joint` | `motor` |
| `left_hand_middle_0_joint` | `left_hand_middle_0_joint` | `motor` |
| `left_hand_middle_1_joint` | `left_hand_middle_1_joint` | `motor` |
| `left_hand_index_0_joint` | `left_hand_index_0_joint` | `motor` |
| `left_hand_index_1_joint` | `left_hand_index_1_joint` | `motor` |
| `right_shoulder_pitch_joint` | `right_shoulder_pitch_joint` | `motor` |
| `right_shoulder_roll_joint` | `right_shoulder_roll_joint` | `motor` |
| `right_shoulder_yaw_joint` | `right_shoulder_yaw_joint` | `motor` |
| `right_elbow_joint` | `right_elbow_joint` | `motor` |
| `right_wrist_roll_joint` | `right_wrist_roll_joint` | `motor` |
| `right_wrist_pitch_joint` | `right_wrist_pitch_joint` | `motor` |
| `right_wrist_yaw_joint` | `right_wrist_yaw_joint` | `motor` |
| `right_hand_thumb_0_joint` | `right_hand_thumb_0_joint` | `motor` |
| `right_hand_thumb_1_joint` | `right_hand_thumb_1_joint` | `motor` |
| `right_hand_thumb_2_joint` | `right_hand_thumb_2_joint` | `motor` |
| `right_hand_index_0_joint` | `right_hand_index_0_joint` | `motor` |
| `right_hand_index_1_joint` | `right_hand_index_1_joint` | `motor` |
| `right_hand_middle_0_joint` | `right_hand_middle_0_joint` | `motor` |
| `right_hand_middle_1_joint` | `right_hand_middle_1_joint` | `motor` |

## 6. Sitios (`site`)

| Sitio | Cuerpo contenedor | Posición declarada | Tamaño |
|---|---|---|---|
| `imu_in_pelvis` | `pelvis` | `0.04525 0 -0.08339` | `0.01` |
| `imu_in_torso` | `torso_link` | `-0.03959 -0.00224 0.13792` | `0.01` |

## 7. Sensores

| Sensor | Tipo MJCF | Site referenciado | Parámetros declarados |
|---|---|---|---|
| `imu-torso-angular-velocity` | `gyro` | `imu_in_torso` | `noise=5e-4`, `cutoff=34.9` |
| `imu-torso-linear-acceleration` | `accelerometer` | `imu_in_torso` | `noise=1e-2`, `cutoff=157` |
| `imu-pelvis-angular-velocity` | `gyro` | `imu_in_pelvis` | `noise=5e-4`, `cutoff=34.9` |
| `imu-pelvis-linear-acceleration` | `accelerometer` | `imu_in_pelvis` | `noise=1e-2`, `cutoff=157` |

### 7.1 Relación explícita entre sensores y sitios

| Sensor | Site | Tipo de medición según el tipo declarado |
|---|---|---|
| `imu-torso-angular-velocity` | `imu_in_torso` | velocidad angular (tipo `gyro`) |
| `imu-torso-linear-acceleration` | `imu_in_torso` | aceleración (tipo `accelerometer`) |
| `imu-pelvis-angular-velocity` | `imu_in_pelvis` | velocidad angular (tipo `gyro`) |
| `imu-pelvis-linear-acceleration` | `imu_in_pelvis` | aceleración (tipo `accelerometer`) |

El XML declara dos sensores con `site="imu_in_torso"` y dos con `site="imu_in_pelvis"`. Los nombres de los sensores y los nombres de los sitios son identificadores distintos.

## 8. Geometrías

Las geometrías pueden ser mallas u otras formas primitivas. La tabla lista cada declaración `geom` y su cuerpo contenedor, además de los atributos escritos en el XML.

| N.º | Cuerpo contenedor | Tipo | Malla | Atributos adicionales declarados |
|---:|---|---|---|---|
| 1 | `pelvis` | `mesh` | `pelvis` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.2 0.2 0.2 1` |
| 2 | `pelvis` | `mesh` | `pelvis_contour_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 3 | `pelvis` | `mesh` | `pelvis_contour_link` | `rgba=0.7 0.7 0.7 1` |
| 4 | `left_hip_pitch_link` | `mesh` | `left_hip_pitch_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.2 0.2 0.2 1` |
| 5 | `left_hip_pitch_link` | `mesh` | `left_hip_pitch_link` | `rgba=0.2 0.2 0.2 1` |
| 6 | `left_hip_roll_link` | `mesh` | `left_hip_roll_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 7 | `left_hip_roll_link` | `mesh` | `left_hip_roll_link` | `rgba=0.7 0.7 0.7 1` |
| 8 | `left_hip_yaw_link` | `mesh` | `left_hip_yaw_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 9 | `left_hip_yaw_link` | `mesh` | `left_hip_yaw_link` | `rgba=0.7 0.7 0.7 1` |
| 10 | `left_knee_link` | `mesh` | `left_knee_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 11 | `left_knee_link` | `mesh` | `left_knee_link` | `rgba=0.7 0.7 0.7 1` |
| 12 | `left_ankle_pitch_link` | `mesh` | `left_ankle_pitch_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 13 | `left_ankle_pitch_link` | `mesh` | `left_ankle_pitch_link` | `rgba=0.7 0.7 0.7 1` |
| 14 | `left_ankle_roll_link` | `mesh` | `left_ankle_roll_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.2 0.2 0.2 1` |
| 15 | `left_ankle_roll_link` | `no declarado` | `—` | `size=0.005`, `pos=-0.05 0.025 -0.03`, `rgba=0.2 0.2 0.2 1` |
| 16 | `left_ankle_roll_link` | `no declarado` | `—` | `size=0.005`, `pos=-0.05 -0.025 -0.03`, `rgba=0.2 0.2 0.2 1` |
| 17 | `left_ankle_roll_link` | `no declarado` | `—` | `size=0.005`, `pos=0.12 0.03 -0.03`, `rgba=0.2 0.2 0.2 1` |
| 18 | `left_ankle_roll_link` | `no declarado` | `—` | `size=0.005`, `pos=0.12 -0.03 -0.03`, `rgba=0.2 0.2 0.2 1` |
| 19 | `right_hip_pitch_link` | `mesh` | `right_hip_pitch_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.2 0.2 0.2 1` |
| 20 | `right_hip_pitch_link` | `mesh` | `right_hip_pitch_link` | `rgba=0.2 0.2 0.2 1` |
| 21 | `right_hip_roll_link` | `mesh` | `right_hip_roll_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 22 | `right_hip_roll_link` | `mesh` | `right_hip_roll_link` | `rgba=0.7 0.7 0.7 1` |
| 23 | `right_hip_yaw_link` | `mesh` | `right_hip_yaw_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 24 | `right_hip_yaw_link` | `mesh` | `right_hip_yaw_link` | `rgba=0.7 0.7 0.7 1` |
| 25 | `right_knee_link` | `mesh` | `right_knee_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 26 | `right_knee_link` | `mesh` | `right_knee_link` | `rgba=0.7 0.7 0.7 1` |
| 27 | `right_ankle_pitch_link` | `mesh` | `right_ankle_pitch_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 28 | `right_ankle_pitch_link` | `mesh` | `right_ankle_pitch_link` | `rgba=0.7 0.7 0.7 1` |
| 29 | `right_ankle_roll_link` | `mesh` | `right_ankle_roll_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.2 0.2 0.2 1` |
| 30 | `right_ankle_roll_link` | `no declarado` | `—` | `size=0.005`, `pos=-0.05 0.025 -0.03`, `rgba=0.2 0.2 0.2 1` |
| 31 | `right_ankle_roll_link` | `no declarado` | `—` | `size=0.005`, `pos=-0.05 -0.025 -0.03`, `rgba=0.2 0.2 0.2 1` |
| 32 | `right_ankle_roll_link` | `no declarado` | `—` | `size=0.005`, `pos=0.12 0.03 -0.03`, `rgba=0.2 0.2 0.2 1` |
| 33 | `right_ankle_roll_link` | `no declarado` | `—` | `size=0.005`, `pos=0.12 -0.03 -0.03`, `rgba=0.2 0.2 0.2 1` |
| 34 | `waist_yaw_link` | `mesh` | `waist_yaw_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 35 | `waist_roll_link` | `mesh` | `waist_roll_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 36 | `torso_link` | `mesh` | `torso_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 37 | `torso_link` | `mesh` | `torso_link` | `rgba=0.7 0.7 0.7 1` |
| 38 | `torso_link` | `mesh` | `logo_link` | `pos=0.0039635 0 -0.054`, `quat=1 0 0 0`, `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.2 0.2 0.2 1` |
| 39 | `torso_link` | `mesh` | `logo_link` | `pos=0.0039635 0 -0.054`, `quat=1 0 0 0`, `rgba=0.2 0.2 0.2 1` |
| 40 | `torso_link` | `mesh` | `head_link` | `pos=0.0039635 0 -0.054`, `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.2 0.2 0.2 1` |
| 41 | `torso_link` | `mesh` | `head_link` | `pos=0.0039635 0 -0.054`, `rgba=0.2 0.2 0.2 1` |
| 42 | `torso_link` | `mesh` | `waist_support_link` | `pos=0.0039635 0 -0.054`, `quat=1 0 0 0`, `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 43 | `torso_link` | `mesh` | `waist_support_link` | `pos=0.0039635 0 -0.054`, `quat=1 0 0 0`, `rgba=0.7 0.7 0.7 1` |
| 44 | `left_shoulder_pitch_link` | `mesh` | `left_shoulder_pitch_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 45 | `left_shoulder_pitch_link` | `cylinder` | `—` | `size=0.03 0.025`, `pos=0 0.04 -0.01`, `quat=0.707107 0 0.707107 0`, `rgba=0.7 0.7 0.7 1` |
| 46 | `left_shoulder_roll_link` | `mesh` | `left_shoulder_roll_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 47 | `left_shoulder_roll_link` | `cylinder` | `—` | `size=0.03 0.015`, `pos=-0.004 0.006 -0.053`, `rgba=0.7 0.7 0.7 1` |
| 48 | `left_shoulder_yaw_link` | `mesh` | `left_shoulder_yaw_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 49 | `left_shoulder_yaw_link` | `mesh` | `left_shoulder_yaw_link` | `rgba=0.7 0.7 0.7 1` |
| 50 | `left_elbow_link` | `mesh` | `left_elbow_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 51 | `left_elbow_link` | `mesh` | `left_elbow_link` | `rgba=0.7 0.7 0.7 1` |
| 52 | `left_wrist_roll_link` | `mesh` | `left_wrist_roll_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 53 | `left_wrist_roll_link` | `mesh` | `left_wrist_roll_link` | `rgba=0.7 0.7 0.7 1` |
| 54 | `left_wrist_pitch_link` | `mesh` | `left_wrist_pitch_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 55 | `left_wrist_pitch_link` | `mesh` | `left_wrist_pitch_link` | `rgba=0.7 0.7 0.7 1` |
| 56 | `left_wrist_yaw_link` | `mesh` | `left_wrist_yaw_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 57 | `left_wrist_yaw_link` | `mesh` | `left_wrist_yaw_link` | `rgba=0.7 0.7 0.7 1` |
| 58 | `left_wrist_yaw_link` | `mesh` | `left_hand_palm_link` | `pos=0.0415 0.003 0`, `quat=1 0 0 0`, `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 59 | `left_wrist_yaw_link` | `mesh` | `left_hand_palm_link` | `pos=0.0415 0.003 0`, `quat=1 0 0 0`, `rgba=0.7 0.7 0.7 1` |
| 60 | `left_hand_thumb_0_link` | `mesh` | `left_hand_thumb_0_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 61 | `left_hand_thumb_0_link` | `mesh` | `left_hand_thumb_0_link` | `rgba=0.7 0.7 0.7 1` |
| 62 | `left_hand_thumb_1_link` | `mesh` | `left_hand_thumb_1_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 63 | `left_hand_thumb_1_link` | `box` | `—` | `size=0.01 0.015 0.01`, `pos=-0.001 -0.032 0`, `rgba=0.7 0.7 0.7 1` |
| 64 | `left_hand_thumb_2_link` | `mesh` | `left_hand_thumb_2_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 65 | `left_hand_thumb_2_link` | `mesh` | `left_hand_thumb_2_link` | `rgba=0.7 0.7 0.7 1` |
| 66 | `left_hand_middle_0_link` | `mesh` | `left_hand_middle_0_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 67 | `left_hand_middle_0_link` | `mesh` | `left_hand_middle_0_link` | `rgba=0.7 0.7 0.7 1` |
| 68 | `left_hand_middle_1_link` | `mesh` | `left_hand_middle_1_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 69 | `left_hand_middle_1_link` | `mesh` | `left_hand_middle_1_link` | `rgba=0.7 0.7 0.7 1` |
| 70 | `left_hand_index_0_link` | `mesh` | `left_hand_index_0_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 71 | `left_hand_index_0_link` | `mesh` | `left_hand_index_0_link` | `rgba=0.7 0.7 0.7 1` |
| 72 | `left_hand_index_1_link` | `mesh` | `left_hand_index_1_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 73 | `left_hand_index_1_link` | `mesh` | `left_hand_index_1_link` | `rgba=0.7 0.7 0.7 1` |
| 74 | `right_shoulder_pitch_link` | `mesh` | `right_shoulder_pitch_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 75 | `right_shoulder_pitch_link` | `cylinder` | `—` | `size=0.03 0.025`, `pos=0 -0.04 -0.01`, `quat=0.707107 0 0.707107 0`, `rgba=0.7 0.7 0.7 1` |
| 76 | `right_shoulder_roll_link` | `mesh` | `right_shoulder_roll_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 77 | `right_shoulder_roll_link` | `cylinder` | `—` | `size=0.03 0.015`, `pos=-0.004 -0.006 -0.053`, `rgba=0.7 0.7 0.7 1` |
| 78 | `right_shoulder_yaw_link` | `mesh` | `right_shoulder_yaw_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 79 | `right_shoulder_yaw_link` | `mesh` | `right_shoulder_yaw_link` | `rgba=0.7 0.7 0.7 1` |
| 80 | `right_elbow_link` | `mesh` | `right_elbow_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 81 | `right_elbow_link` | `mesh` | `right_elbow_link` | `rgba=0.7 0.7 0.7 1` |
| 82 | `right_wrist_roll_link` | `mesh` | `right_wrist_roll_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 83 | `right_wrist_roll_link` | `mesh` | `right_wrist_roll_link` | `rgba=0.7 0.7 0.7 1` |
| 84 | `right_wrist_pitch_link` | `mesh` | `right_wrist_pitch_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 85 | `right_wrist_pitch_link` | `mesh` | `right_wrist_pitch_link` | `rgba=0.7 0.7 0.7 1` |
| 86 | `right_wrist_yaw_link` | `mesh` | `right_wrist_yaw_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 87 | `right_wrist_yaw_link` | `mesh` | `right_wrist_yaw_link` | `rgba=0.7 0.7 0.7 1` |
| 88 | `right_wrist_yaw_link` | `mesh` | `right_hand_palm_link` | `pos=0.0415 -0.003 0`, `quat=1 0 0 0`, `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 89 | `right_wrist_yaw_link` | `mesh` | `right_hand_palm_link` | `pos=0.0415 -0.003 0`, `quat=1 0 0 0`, `rgba=0.7 0.7 0.7 1` |
| 90 | `right_hand_thumb_0_link` | `mesh` | `right_hand_thumb_0_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 91 | `right_hand_thumb_0_link` | `mesh` | `right_hand_thumb_0_link` | `rgba=0.7 0.7 0.7 1` |
| 92 | `right_hand_thumb_1_link` | `mesh` | `right_hand_thumb_1_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 93 | `right_hand_thumb_1_link` | `box` | `—` | `size=0.01 0.015 0.01`, `pos=-0.001 0.032 0`, `rgba=0.7 0.7 0.7 1` |
| 94 | `right_hand_thumb_2_link` | `mesh` | `right_hand_thumb_2_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 95 | `right_hand_thumb_2_link` | `mesh` | `right_hand_thumb_2_link` | `rgba=0.7 0.7 0.7 1` |
| 96 | `right_hand_middle_0_link` | `mesh` | `right_hand_middle_0_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 97 | `right_hand_middle_0_link` | `mesh` | `right_hand_middle_0_link` | `rgba=0.7 0.7 0.7 1` |
| 98 | `right_hand_middle_1_link` | `mesh` | `right_hand_middle_1_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 99 | `right_hand_middle_1_link` | `mesh` | `right_hand_middle_1_link` | `rgba=0.7 0.7 0.7 1` |
| 100 | `right_hand_index_0_link` | `mesh` | `right_hand_index_0_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 101 | `right_hand_index_0_link` | `mesh` | `right_hand_index_0_link` | `rgba=0.7 0.7 0.7 1` |
| 102 | `right_hand_index_1_link` | `mesh` | `right_hand_index_1_link` | `contype=0`, `conaffinity=0`, `group=1`, `density=0`, `rgba=0.7 0.7 0.7 1` |
| 103 | `right_hand_index_1_link` | `mesh` | `right_hand_index_1_link` | `rgba=0.7 0.7 0.7 1` |

## 9. Mallas declaradas

| Nombre de malla | Archivo declarado |
|---|---|
| `pelvis` | `pelvis.STL` |
| `pelvis_contour_link` | `pelvis_contour_link.STL` |
| `left_hip_pitch_link` | `left_hip_pitch_link.STL` |
| `left_hip_roll_link` | `left_hip_roll_link.STL` |
| `left_hip_yaw_link` | `left_hip_yaw_link.STL` |
| `left_knee_link` | `left_knee_link.STL` |
| `left_ankle_pitch_link` | `left_ankle_pitch_link.STL` |
| `left_ankle_roll_link` | `left_ankle_roll_link.STL` |
| `right_hip_pitch_link` | `right_hip_pitch_link.STL` |
| `right_hip_roll_link` | `right_hip_roll_link.STL` |
| `right_hip_yaw_link` | `right_hip_yaw_link.STL` |
| `right_knee_link` | `right_knee_link.STL` |
| `right_ankle_pitch_link` | `right_ankle_pitch_link.STL` |
| `right_ankle_roll_link` | `right_ankle_roll_link.STL` |
| `waist_yaw_link` | `waist_yaw_link.STL` |
| `waist_roll_link` | `waist_roll_link.STL` |
| `torso_link` | `torso_link.STL` |
| `logo_link` | `logo_link.STL` |
| `head_link` | `head_link.STL` |
| `waist_support_link` | `waist_support_link.STL` |
| `left_shoulder_pitch_link` | `left_shoulder_pitch_link.STL` |
| `left_shoulder_roll_link` | `left_shoulder_roll_link.STL` |
| `left_shoulder_yaw_link` | `left_shoulder_yaw_link.STL` |
| `left_elbow_link` | `left_elbow_link.STL` |
| `left_wrist_roll_link` | `left_wrist_roll_link.STL` |
| `left_wrist_pitch_link` | `left_wrist_pitch_link.STL` |
| `left_wrist_yaw_link` | `left_wrist_yaw_link.STL` |
| `left_hand_palm_link` | `left_hand_palm_link.STL` |
| `left_hand_thumb_0_link` | `left_hand_thumb_0_link.STL` |
| `left_hand_thumb_1_link` | `left_hand_thumb_1_link.STL` |
| `left_hand_thumb_2_link` | `left_hand_thumb_2_link.STL` |
| `left_hand_middle_0_link` | `left_hand_middle_0_link.STL` |
| `left_hand_middle_1_link` | `left_hand_middle_1_link.STL` |
| `left_hand_index_0_link` | `left_hand_index_0_link.STL` |
| `left_hand_index_1_link` | `left_hand_index_1_link.STL` |
| `right_shoulder_pitch_link` | `right_shoulder_pitch_link.STL` |
| `right_shoulder_roll_link` | `right_shoulder_roll_link.STL` |
| `right_shoulder_yaw_link` | `right_shoulder_yaw_link.STL` |
| `right_elbow_link` | `right_elbow_link.STL` |
| `right_wrist_roll_link` | `right_wrist_roll_link.STL` |
| `right_wrist_pitch_link` | `right_wrist_pitch_link.STL` |
| `right_wrist_yaw_link` | `right_wrist_yaw_link.STL` |
| `right_hand_palm_link` | `right_hand_palm_link.STL` |
| `right_hand_thumb_0_link` | `right_hand_thumb_0_link.STL` |
| `right_hand_thumb_1_link` | `right_hand_thumb_1_link.STL` |
| `right_hand_thumb_2_link` | `right_hand_thumb_2_link.STL` |
| `right_hand_middle_0_link` | `right_hand_middle_0_link.STL` |
| `right_hand_middle_1_link` | `right_hand_middle_1_link.STL` |
| `right_hand_index_0_link` | `right_hand_index_0_link.STL` |
| `right_hand_index_1_link` | `right_hand_index_1_link.STL` |

## 10. Propiedades inerciales

Se listan las etiquetas `inertial` tal como aparecen bajo cada cuerpo. Los valores no se convierten ni se recalculan.

| Cuerpo | Masa | Posición inercial | Quaternion | Inercia diagonal |
|---|---:|---|---|---|
| `pelvis` | `3.813` | `0 0 -0.07605` | `1 0 -0.000399148 0` | `0.010549 0.0093089 0.0079184` |
| `left_hip_pitch_link` | `1.35` | `0.002741 0.047791 -0.02606` | `0.954862 0.293964 0.0302556 0.030122` | `0.00181517 0.00153422 0.00116212` |
| `left_hip_roll_link` | `1.52` | `0.029812 -0.001045 -0.087934` | `0.977808 -1.97119e-05 0.205576 -0.0403793` | `0.00254986 0.00241169 0.00148755` |
| `left_hip_yaw_link` | `1.702` | `-0.057709 -0.010981 -0.15078` | `0.600598 0.15832 0.223482 0.751181` | `0.00776166 0.00717575 0.00160139` |
| `left_knee_link` | `1.932` | `0.005457 0.003964 -0.12074` | `0.923418 -0.0327699 0.0158246 0.382067` | `0.0113804 0.0112778 0.00146458` |
| `left_ankle_pitch_link` | `0.074` | `-0.007269 0 0.011137` | `0.603053 0.369225 0.369225 0.603053` | `1.89e-05 1.40805e-05 6.9195e-06` |
| `left_ankle_roll_link` | `0.608` | `0.026505 0 -0.016425` | `-0.000481092 0.728482 -0.000618967 0.685065` | `0.00167218 0.0016161 0.000217621` |
| `right_hip_pitch_link` | `1.35` | `0.002741 -0.047791 -0.02606` | `0.954862 -0.293964 0.0302556 -0.030122` | `0.00181517 0.00153422 0.00116212` |
| `right_hip_roll_link` | `1.52` | `0.029812 0.001045 -0.087934` | `0.977808 1.97119e-05 0.205576 0.0403793` | `0.00254986 0.00241169 0.00148755` |
| `right_hip_yaw_link` | `1.702` | `-0.057709 0.010981 -0.15078` | `0.751181 0.223482 0.15832 0.600598` | `0.00776166 0.00717575 0.00160139` |
| `right_knee_link` | `1.932` | `0.005457 -0.003964 -0.12074` | `0.923439 0.0345276 0.0116333 -0.382012` | `0.011374 0.0112843 0.00146452` |
| `right_ankle_pitch_link` | `0.074` | `-0.007269 0 0.011137` | `0.603053 0.369225 0.369225 0.603053` | `1.89e-05 1.40805e-05 6.9195e-06` |
| `right_ankle_roll_link` | `0.608` | `0.026505 0 -0.016425` | `0.000481092 0.728482 0.000618967 0.685065` | `0.00167218 0.0016161 0.000217621` |
| `waist_yaw_link` | `0.244` | `0.003964 0 0.018769` | `-0.0178291 0.628464 0.0282471 0.777121` | `0.000158561 0.000124229 9.67669e-05` |
| `waist_roll_link` | `0.047` | `0 -0.000236 0.010111` | `0.99979 0.020492 0 0` | `7.515e-06 6.40206e-06 3.98394e-06` |
| `torso_link` | `9.598` | `0.00331658 0.000261533 0.179856` | `0.999831 0.000376204 0.0179895 -0.00377704` | `0.12407 0.111951 0.0325382` |
| `left_shoulder_pitch_link` | `0.718` | `0 0.035892 -0.011628` | `0.654152 0.0130458 -0.326267 0.68225` | `0.000465864 0.000432842 0.000406394` |
| `left_shoulder_roll_link` | `0.643` | `-0.000227 0.00727 -0.063243` | `0.701256 -0.0196223 -0.00710317 0.712604` | `0.000691311 0.000618011 0.000388977` |
| `left_shoulder_yaw_link` | `0.734` | `0.010773 -0.002949 -0.072009` | `0.716879 -0.0964829 -0.0679942 0.687134` | `0.00106187 0.00103217 0.000400661` |
| `left_elbow_link` | `0.6` | `0.064956 0.004454 -0.010062` | `0.541765 0.636132 0.388821 0.388129` | `0.000443035 0.000421612 0.000259353` |
| `left_wrist_roll_link` | `0.085445` | `0.0171394 0.000537591 4.8864e-07` | `0.575338 0.411667 -0.574906 0.411094` | `5.48211e-05 4.96646e-05 3.57798e-05` |
| `left_wrist_pitch_link` | `0.48405` | `0.0229999 -0.00111685 -0.00111658` | `0.249998 0.661363 0.293036 0.643608` | `0.000430353 0.000429873 0.000164648` |
| `left_wrist_yaw_link` | `0.457415` | `0.0885506 0.00212216 -0.000374562` | `0.487149 0.493844 0.513241 0.505358` | `0.00105989 0.000895419 0.000323842` |
| `left_hand_thumb_0_link` | `0.0862366` | `-0.000884246 -0.00863407 0.000944293` | `0.462991 0.643965 -0.460173 0.398986` | `1.6546e-05 1.60058e-05 1.43741e-05` |
| `left_hand_thumb_1_link` | `0.0588507` | `-0.000827888 -0.0354744 -0.0003809` | `0.685598 0.705471 -0.15207 0.0956069` | `1.28514e-05 1.22902e-05 5.9666e-06` |
| `left_hand_thumb_2_link` | `0.0203063` | `-0.00171735 -0.0262819 0.000107789` | `0.703174 0.710977 -0.00017564 -0.00766553` | `4.61314e-06 3.86645e-06 1.53495e-06` |
| `left_hand_middle_0_link` | `0.0588507` | `0.0354744 0.000827888 0.0003809` | `0.391313 0.552395 0.417187 0.606373` | `1.28514e-05 1.22902e-05 5.9666e-06` |
| `left_hand_middle_1_link` | `0.0203063` | `0.0262819 0.00171735 -0.000107789` | `0.502612 0.491799 0.502639 0.502861` | `4.61314e-06 3.86645e-06 1.53495e-06` |
| `left_hand_index_0_link` | `0.0588507` | `0.0354744 0.000827888 0.0003809` | `0.391313 0.552395 0.417187 0.606373` | `1.28514e-05 1.22902e-05 5.9666e-06` |
| `left_hand_index_1_link` | `0.0203063` | `0.0262819 0.00171735 -0.000107789` | `0.502612 0.491799 0.502639 0.502861` | `4.61314e-06 3.86645e-06 1.53495e-06` |
| `right_shoulder_pitch_link` | `0.718` | `0 -0.035892 -0.011628` | `0.68225 -0.326267 0.0130458 0.654152` | `0.000465864 0.000432842 0.000406394` |
| `right_shoulder_roll_link` | `0.643` | `-0.000227 -0.00727 -0.063243` | `0.712604 -0.00710317 -0.0196223 0.701256` | `0.000691311 0.000618011 0.000388977` |
| `right_shoulder_yaw_link` | `0.734` | `0.010773 0.002949 -0.072009` | `0.687134 -0.0679942 -0.0964829 0.716879` | `0.00106187 0.00103217 0.000400661` |
| `right_elbow_link` | `0.6` | `0.064956 -0.004454 -0.010062` | `0.388129 0.388821 0.636132 0.541765` | `0.000443035 0.000421612 0.000259353` |
| `right_wrist_roll_link` | `0.085445` | `0.0171394 -0.000537591 4.8864e-07` | `0.411667 0.575338 -0.411094 0.574906` | `5.48211e-05 4.96646e-05 3.57798e-05` |
| `right_wrist_pitch_link` | `0.48405` | `0.0229999 0.00111685 -0.00111658` | `0.643608 0.293036 0.661363 0.249998` | `0.000430353 0.000429873 0.000164648` |
| `right_wrist_yaw_link` | `0.457415` | `0.0885506 -0.00212216 -0.000374562` | `0.505358 0.513241 0.493844 0.487149` | `0.00105989 0.000895419 0.000323842` |
| `right_hand_thumb_0_link` | `0.0862366` | `-0.000884246 0.00863407 0.000944293` | `0.643965 0.462991 -0.398986 0.460173` | `1.6546e-05 1.60058e-05 1.43741e-05` |
| `right_hand_thumb_1_link` | `0.0588507` | `-0.000827888 0.0354744 -0.0003809` | `0.705471 0.685598 -0.0956069 0.15207` | `1.28514e-05 1.22902e-05 5.9666e-06` |
| `right_hand_thumb_2_link` | `0.0203063` | `-0.00171735 0.0262819 0.000107789` | `0.710977 0.703174 0.00766553 0.00017564` | `4.61314e-06 3.86645e-06 1.53495e-06` |
| `right_hand_middle_0_link` | `0.0588507` | `0.0354744 -0.000827888 0.0003809` | `0.606373 0.417187 0.552395 0.391313` | `1.28514e-05 1.22902e-05 5.9666e-06` |
| `right_hand_middle_1_link` | `0.0203063` | `0.0262819 -0.00171735 -0.000107789` | `0.502861 0.502639 0.491799 0.502612` | `4.61314e-06 3.86645e-06 1.53495e-06` |
| `right_hand_index_0_link` | `0.0588507` | `0.0354744 -0.000827888 0.0003809` | `0.606373 0.417187 0.552395 0.391313` | `1.28514e-05 1.22902e-05 5.9666e-06` |
| `right_hand_index_1_link` | `0.0203063` | `0.0262819 -0.00171735 -0.000107789` | `0.502861 0.502639 0.491799 0.502612` | `4.61314e-06 3.86645e-06 1.53495e-06` |

## 11. Configuración visual y escena

### `statistic`
- `<statistic center="1.0 0.7 1.0" extent="0.8" />`

### `visual/headlight`
- `<headlight diffuse="0.6 0.6 0.6" ambient="0.1 0.1 0.1" specular="0.9 0.9 0.9" />`

### `visual/rgba`
- `<rgba haze="0.15 0.25 0.35 1" />`

### `visual/global`
- `<global azimuth="-140" elevation="-20" />`

### `asset/texture`
- `<texture type="skybox" builtin="flat" rgb1="0 0 0" rgb2="0 0 0" width="512" height="3072" />`
- `<texture type="2d" name="groundplane" builtin="checker" mark="edge" rgb1="0.2 0.3 0.4" rgb2="0.1 0.2 0.3" markrgb="0.8 0.8 0.8" width="300" height="300" />`

### `asset/material`
- `<material name="groundplane" texture="groundplane" texuniform="true" texrepeat="5 5" reflectance="0.2" />`

### `worldbody/light`
- `<light pos="1 0 3.5" dir="0 0 -1" directional="true" />`

### `worldbody/geom`
- `<geom name="floor" size="0 0 0.05" type="plane" material="groundplane" />`

## 12. Límites y alcance de esta referencia

- Este documento es una extracción descriptiva del XML entregado; no certifica que el modelo sea físicamente correcto ni que compile sin errores.
- No se incorporan datos del fabricante ni de otras fuentes.
- Las mallas se enumeran por el nombre y la ruta declarados; el contenido de los archivos STL no se inspecciona aquí.
- Las descripciones de sensores se limitan al tipo MJCF declarado (`gyro` o `accelerometer`) y a sus atributos explícitos.
- Los rangos, ejes y parámetros se mantienen en el formato del XML. El compilador declara `angle="radian"`.
- El archivo contiene dos bloques `worldbody` y dos bloques `asset`; esta extracción lista sus elementos sin modificar el XML original.

## 13. Archivo fuente

- `g1_29dof_with_hand.xml` (archivo proporcionado para generar esta referencia).
