#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoría independiente del inventario MJCF del Unitree G1 frente al dossier.
No modifica ningún archivo. Genera un informe TXT y un CSV.
"""
import argparse
import csv
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

def local_name(tag):
    return tag.rsplit("}", 1)[-1]

def choose_existing(candidates):
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None

def main():
    parser = argparse.ArgumentParser(description="Audita el MJCF del G1 contra el dossier Markdown.")
    parser.add_argument("--xml", type=Path, help="Ruta al XML/MJCF exacto.")
    parser.add_argument("--md", type=Path, help="Ruta al dossier Markdown actualizado.")
    parser.add_argument("--out", type=Path, default=Path("Tests"), help="Carpeta donde guardar resultados.")
    args = parser.parse_args()

    xml_candidates = [
        Path("resources/robots/g1_description/g1_29dof_with_hand_rev_1_0.xml"),
        Path("g1_29dof_with_hand_rev_1_0.xml"),
        Path("Models/g1_29dof_with_hand_rev_1_0.xml"),
        Path("Knowledge/Unitree/G1/g1_29dof_with_hand_rev_1_0.xml"),
    ]
    md_candidates = [
        Path("Knowledge/Unitree/G1/Unitree_G1_Dossier_Tecnico_GIAR_ORION.md"),
        Path("Unitree_G1_Dossier_Tecnico_GIAR_ORION(3).md"),
        Path("Unitree_G1_Dossier_Tecnico_GIAR_ORION_actualizado.md"),
    ]
    xml_path = args.xml or choose_existing(xml_candidates)
    md_path = args.md or choose_existing(md_candidates)

    if not xml_path or not xml_path.is_file():
        print("ERROR: No se encontró el archivo MJCF/XML.")
        print("Indicá su ruta con --xml.")
        return 2
    if not md_path or not md_path.is_file():
        print("ERROR: No se encontró el dossier Markdown.")
        print("Indicá su ruta con --md.")
        return 2

    xml_path = xml_path.resolve()
    md_path = md_path.resolve()
    root = ET.parse(xml_path).getroot()
    md = md_path.read_text(encoding="utf-8-sig")

    actuator_rows = []
    actuator_section = root.find("actuator")
    if actuator_section is not None:
        for element in list(actuator_section):
            name = element.attrib.get("name", "")
            joint = element.attrib.get("joint", "")
            if name or joint:
                actuator_rows.append((name, joint))

    joints = []
    bodies = []
    sites = []
    sensors = []
    for element in root.iter():
        tag = local_name(element.tag)
        name = element.attrib.get("name", "")
        if tag == "joint" and name:
            joints.append((name, element.attrib.get("type", "hinge")))
        elif tag == "body" and name:
            bodies.append(name)
        elif tag == "site" and name:
            sites.append(name)
        elif tag in {"gyro", "accelerometer", "magnetometer", "touch", "force", "torque",
                     "jointpos", "jointvel", "framepos", "framequat", "framelinvel", "frameangvel"} and name:
            sensors.append((name, tag, element.attrib.get("site", ""), element.attrib.get("objname", "")))

    section_parts = md.split("### 6.3 Inventario nominal de las 43 articulaciones actuadas", 1)
    inventory = section_parts[1].split("\n## ", 1)[0] if len(section_parts) == 2 else ""
    md_joint_names = list(dict.fromkeys(re.findall(r"`([A-Za-z][A-Za-z0-9_]*_joint)`", inventory)))
    md_sensor_names = set(re.findall(r"`(imu-[A-Za-z0-9_-]+)`", md))
    md_imu_sites = set(re.findall(r"`(imu_in_[A-Za-z0-9_]+)`", md))

    actuator_names = [a for a, j in actuator_rows]
    actuator_targets = [j for a, j in actuator_rows]
    actuator_set = set(actuator_names)
    md_joint_set = set(md_joint_names)
    joint_set = {name for name, _ in joints}
    sensor_set = {name for name, _, _, _ in sensors}
    imu_site_set = {name for name in sites if name.startswith("imu_in_")}

    outdir = args.out / ("results_g1_mjcf_audit_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / "actuadores_y_articulaciones.csv"
    fields = ["orden_actuador_1based", "nombre_actuador", "joint_objetivo",
              "nombre_coincide_con_joint", "joint_existe_en_mjcf", "aparece_en_dossier"]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for index, (actuator, target) in enumerate(actuator_rows, 1):
            writer.writerow({
                "orden_actuador_1based": index,
                "nombre_actuador": actuator,
                "joint_objetivo": target,
                "nombre_coincide_con_joint": actuator == target,
                "joint_existe_en_mjcf": target in joint_set,
                "aparece_en_dossier": actuator in md_joint_set,
            })

    missing_dossier = sorted(actuator_set - md_joint_set)
    extra_dossier = sorted(md_joint_set - actuator_set)
    missing_sensors = sorted(sensor_set - md_sensor_names)
    missing_sites = sorted(imu_site_set - md_imu_sites)
    duplicates = sorted({name for name in actuator_names if actuator_names.count(name) > 1})

    lines = [
        "AUDITORÍA MJCF ↔ DOSSIER UNITREE G1", "=" * 72,
        "MJCF: " + str(xml_path), "Dossier: " + str(md_path),
        "Modelo declarado: " + root.attrib.get("model", "(sin atributo model)",),
        "", "CONTEOS",
        f"- Elementos del bloque actuator: {len(actuator_rows)}",
        f"- Nombres de actuador únicos: {len(actuator_set)}",
        f"- Articulaciones nombradas en MJCF: {len(joints)}",
        f"- Cuerpos nombrados: {len(bodies)}",
        f"- Sitios nombrados: {len(sites)}",
        f"- Sensores explícitos reconocidos: {len(sensors)}",
        f"- Nombres de articulación en sección 6.3 del dossier: {len(md_joint_names)}",
        "", "VALIDACIONES",
        f"- Actuadores duplicados: {duplicates or 'ninguno'}",
        f"- Actuadores cuyo nombre difiere del joint objetivo: {[a for a,j in actuator_rows if a != j] or 'ninguno'}",
        f"- Joints objetivo no encontrados: {[j for a,j in actuator_rows if j not in joint_set] or 'ninguno'}",
        f"- Actuadores ausentes de la sección 6.3: {missing_dossier or 'ninguno'}",
        f"- Nombres de la sección 6.3 que no son actuadores: {extra_dossier or 'ninguno'}",
        f"- Sensores MJCF no nombrados explícitamente en el dossier: {missing_sensors or 'ninguno'}",
        f"- Sitios IMU MJCF no mencionados en el dossier: {missing_sites or 'ninguno'}",
        "", "ORDEN EXACTO DEL BLOQUE ACTUATOR",
    ]
    lines.extend(f"{i:02d}. {a} -> joint={j}" for i, (a, j) in enumerate(actuator_rows, 1))
    lines.extend(["", "SENSORES EXPLÍCITOS EN MJCF"])
    lines.extend(f"- {name}: tipo={kind}; site={site or '(no indicado)'}; objname={obj or '(no indicado)'}"
                 for name, kind, site, obj in sensors)
    lines.extend(["", "SITIOS IMU"])
    lines.extend(f"- {site}" for site in sorted(imu_site_set))
    lines.extend(["", "CUERPOS NOMBRADOS"])
    lines.extend(f"- {body}" for body in bodies)
    lines.extend([
        "", "CONSULTAS SUGERIDAS PARA PRUEBAS RAG",
        "1. Enumerá las articulaciones de la pierna izquierda y citá sus nombres exactos.",
        "2. ¿Qué articulaciones de cintura aparecen en el bloque actuator y en qué orden?",
        "3. ¿Cuáles son los sensores IMU definidos en el MJCF y qué mide cada uno?",
        "4. ¿Qué diferencia hay entre imu_in_torso e imu-torso-angular-velocity?",
        "5. Enumerá las articulaciones de la mano derecha según el MJCF.",
        "6. ¿Cuál es el orden exacto de actuadores en el bloque actuator?",
        "", "Esta auditoría solo lee el XML y el Markdown; no modifica esos archivos."
    ])
    report_path = outdir / "informe_auditoria.txt"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print("Auditoría finalizada.")
    print("MJCF:", xml_path)
    print("Dossier:", md_path)
    print("Actuadores:", len(actuator_rows), "| únicos:", len(actuator_set))
    print("Articulaciones en sección 6.3:", len(md_joint_names))
    print("Actuadores ausentes del dossier:", len(missing_dossier))
    print("Nombres del dossier que no son actuadores:", len(extra_dossier))
    print("Sensores MJCF reconocidos:", len(sensors))
    print("Informe:", report_path.resolve())
    print("CSV:", csv_path.resolve())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
