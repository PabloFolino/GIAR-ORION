
import argparse
import csv
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

DEFAULT_XML_CANDIDATES = [
    Path("resources/robots/g1_description/g1_29dof_with_hand_rev_1_0.xml"),
    Path("g1_29dof_with_hand_rev_1_0.xml"),
    Path("Models/g1_29dof_with_hand_rev_1_0.xml"),
    Path("Knowledge/Unitree/G1/g1_29dof_with_hand_rev_1_0.xml"),
]
DEFAULT_MD_CANDIDATES = [
    Path("Knowledge/Unitree/G1/Unitree_G1_Dossier_Tecnico_GIAR_ORION.md"),
    Path("Unitree_G1_Dossier_Tecnico_GIAR_ORION(3).md"),
    Path("Unitree_G1_Dossier_Tecnico_GIAR_ORION_actualizado.md"),
]

def first_existing(candidates):
    return next((p for p in candidates if p.is_file()), None)

def local_name(tag):
    return tag.rsplit("}", 1)[-1]

def main():
    ap = argparse.ArgumentParser(description="Audita inventario MJCF del G1 contra el dossier.")
    ap.add_argument("--xml", type=Path, help="Ruta al XML/MJCF exacto.")
    ap.add_argument("--md", type=Path, help="Ruta al dossier Markdown actualizado.")
    ap.add_argument("--out", type=Path, default=Path("Tests"), help="Directorio para resultados (predeterminado: Tests).")
    args = ap.parse_args()

    xml_path = args.xml or first_existing(DEFAULT_XML_CANDIDATES)
    md_path = args.md or first_existing(DEFAULT_MD_CANDIDATES)

    if not xml_path or not xml_path.is_file():
        print("ERROR: no encuentro el MJCF. Indicá la ruta con --xml.")
        print("Busqué:")
        for c in DEFAULT_XML_CANDIDATES:
            print(" -", c)
        return 2
    if not md_path or not md_path.is_file():
        print("ERROR: no encuentro el dossier Markdown. Indicá la ruta con --md.")
        print("Busqué:")
        for c in DEFAULT_MD_CANDIDATES:
            print(" -", c)
        return 2

    xml_path = xml_path.resolve()
    md_path = md_path.resolve()
    root = ET.parse(xml_path).getroot()
    md = md_path.read_text(encoding="utf-8-sig")

    actuator_names = []
    actuator_joints = []
    actuator_section = root.find("actuator")
    if actuator_section is not None:
        for elem in list(actuator_section):
            name = elem.attrib.get("name", "")
            joint = elem.attrib.get("joint", "")
            if name or joint:
                actuator_names.append(name)
                actuator_joints.append(joint)

    joint_names = []
    body_names = []
    sites = []
    sensor_names = []
    sensor_types = []
    for elem in root.iter():
        tag = local_name(elem.tag)
        if tag == "joint":
            name = elem.attrib.get("name")
            if name:
                joint_names.append((name, elem.attrib.get("type", "hinge"), elem.attrib.get("limited", "")))
        elif tag == "body":
            name = elem.attrib.get("name")
            if name:
                body_names.append(name)
        elif tag == "site":
            name = elem.attrib.get("name")
            if name:
                sites.append(name)
        elif tag in {"gyro", "accelerometer", "magnetometer", "touch", "force", "torque", "jointpos", "jointvel", "framepos", "framequat", "framelinvel", "frameangvel"}:
            name = elem.attrib.get("name")
            if name:
                sensor_names.append(name)
                sensor_types.append((name, tag, elem.attrib.get("site", ""), elem.attrib.get("objname", "")))

    # Nombres explícitos del inventario de articulaciones de la sección 6.3.
    section = md.split("### 6.3 Inventario nominal de las 43 articulaciones actuadas", 1)
    inventory_text = section[1].split("\n## ", 1)[0] if len(section) == 2 else ""
    md_joint_names = list(dict.fromkeys(re.findall(r"`([A-Za-z][A-Za-z0-9_]*_joint)`", inventory_text)))
    md_sensor_names = list(dict.fromkeys(re.findall(r"`(imu-[A-Za-z0-9_-]+)`", md)))
    md_sites = list(dict.fromkeys(re.findall(r"`(imu_in_[A-Za-z0-9_]+)`", md)))

    xml_actuator_set = set(actuator_names)
    xml_actuator_joint_set = set(actuator_joints)
    md_joint_set = set(md_joint_names)
    xml_sensor_set = set(sensor_names)
    xml_site_set = set(sites)

    rows = []
    for i, (name, joint) in enumerate(zip(actuator_names, actuator_joints), start=1):
        rows.append({
            "actuator_order_1based": i,
            "actuator_name": name,
            "joint_target": joint,
            "name_matches_joint": name == joint,
            "joint_exists_in_mjcf": joint in {j[0] for j in joint_names},
            "listed_in_dossier_section_6_3": name in md_joint_set,
        })

    missing_from_dossier = sorted(xml_actuator_set - md_joint_set)
    dossier_not_actuator = sorted(md_joint_set - xml_actuator_set)
    sensor_missing = sorted(xml_sensor_set - set(md_sensor_names))
    site_missing = sorted({s for s in xml_site_set if s.startswith("imu_in_")} - set(md_sites))
    duplicates = sorted({x for x in actuator_names if actuator_names.count(x) > 1})

    outdir = args.out / ("results_g1_mjcf_audit_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / "actuadores_y_articulaciones.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [
            "actuator_order_1based", "actuator_name", "joint_target", "name_matches_joint",
            "joint_exists_in_mjcf", "listed_in_dossier_section_6_3"])
        writer.writeheader()
        writer.writerows(rows)

    report = []
    report += [
        "AUDITORÍA MJCF ↔ DOSSIER UNITREE G1",
        "=" * 72,
        f"MJCF: {xml_path}",
        f"Dossier: {md_path}",
        f"Modelo declarado: {root.attrib.get('model', '(sin atributo model)')}",
        "",
        "CONTEOS",
        f"- Elementos actuator con name/joint: {len(actuator_names)}",
        f"- Nombres de actuador únicos: {len(xml_actuator_set)}",
        f"- Articulaciones nombradas en el MJCF (incluye base libre si tiene nombre): {len(joint_names)}",
        f"- Cuerpos nombrados: {len(body_names)}",
        f"- Sitios nombrados: {len(sites)}",
        f"- Sensores explícitos MJCF reconocidos: {len(sensor_names)}",
        f"- Articulaciones listadas en la sección 6.3 del dossier: {len(md_joint_names)}",
        "",
        "VALIDACIONES",
        f"- Actuadores con nombre duplicado: {duplicates if duplicates else 'ninguno'}",
        f"- Actuadores cuyo nombre no coincide con joint objetivo: {[r['actuator_name'] for r in rows if not r['name_matches_joint']] or 'ninguno'}",
        f"- Actuadores cuyo joint objetivo no aparece como joint nombrado: {[r['joint_target'] for r in rows if not r['joint_exists_in_mjcf']] or 'ninguno'}",
        f"- Actuadores del MJCF ausentes de sección 6.3: {missing_from_dossier or 'ninguno'}",
        f"- Nombres de sección 6.3 que no son actuadores del MJCF: {dossier_not_actuator or 'ninguno'}",
        f"- Sensores MJCF no mencionados como identificadores en el dossier: {sensor_missing or 'ninguno'}",
        f"- Sitios IMU MJCF no mencionados en el dossier: {site_missing or 'ninguno'}",
        "",
        "ORDEN EXACTO DE ACTUADORES EN EL BLOQUE <actuator>",
    ]
    report += [f"{i:02d}. {a} -> joint={j}" for i, (a, j) in enumerate(zip(actuator_names, actuator_joints), 1)]
    report += ["", "SENSORES EXPLÍCITOS EN EL MJCF"]
    report += [f"- {name}: tipo={typ}; site={site or '(no indicado)'}; objname={obj or '(no indicado)'}" for name, typ, site, obj in sensor_types]
    report += ["", "SITIOS IMU Y OTROS SITIOS NOMBRADOS", *[f"- {s}" for s in sites]]
    report += ["", "CUERPOS NOMBRADOS EN EL MJCF", *[f"- {b}" for b in body_names]]
    report += [
        "",
        "CONSULTAS SUGERIDAS PARA PRUEBAS RAG",
        "1. Enumerá las seis articulaciones de la pierna izquierda del modelo G1 y citá sus nombres exactos.",
        "2. ¿Qué articulaciones de la cintura están definidas y en qué orden aparecen en el bloque actuator?",
        "3. ¿Cuáles son los cuatro sensores de IMU definidos en el MJCF y qué mide cada uno?",
        "4. ¿Qué diferencia hay entre imu_in_torso y imu-torso-angular-velocity?",
        "5. Enumerá las siete articulaciones de la mano derecha según el MJCF.",
        "6. ¿Cuál es el orden exacto de actuadores en el bloque actuator? No infieras índices fuera del archivo.",
        "7. ¿Qué cuerpos nombrados aparecen en la cadena del torso y la cabeza?",
        "",
        "Nota: esta auditoría lee el XML y el Markdown locales. No modifica ninguno de los dos.",
    ]
    report_path = outdir / "informe_auditoria.txt"
    report_path.write_text("\n".join(report), encoding="utf-8")
    print("Auditoría finalizada.")
    print("MJCF:", xml_path)
    print("Dossier:", md_path)
    print("Actuadores:", len(actuator_names), "| únicos:", len(xml_actuator_set))
    print("Articulaciones listadas en sección 6.3:", len(md_joint_names))
    print("Actuadores ausentes del dossier:", len(missing_from_dossier))
    print("Nombres del dossier que no son actuadores:", len(dossier_not_actuator))
    print("Sensores MJCF reconocidos:", len(sensor_names))
    print("Informe:", report_path.resolve())
    print("CSV:", csv_path.resolve())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
