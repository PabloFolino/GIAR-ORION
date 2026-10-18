#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
g1_xml_to_markdown.py

Genera Markdown orientado a preguntas técnicas sobre el modelo Unitree G1 en MJCF.
La salida está organizada en bloques breves y autocontenidos para facilitar la recuperación
RAG: resumen, cuerpo/joint, actuador, site, sensor y relaciones explícitas.

No modifica el XML ni requiere dependencias externas.

Uso:
    python Tools/g1_xml_to_markdown.py "Knowledge/Unitree/G1/g1_29dof_with_hand.xml"
    python Tools/g1_xml_to_markdown.py "ruta/modelo.xml" -o "ruta/salida.md"
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


def tag_name(tag: object) -> str:
    """Nombre local de una etiqueta XML; maneja namespaces y comentarios."""
    if not isinstance(tag, str):
        return "comment"
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def md(value: object) -> str:
    """Escapa valores para que no rompan la estructura Markdown."""
    return str(value).replace("|", r"\|").replace("\r", " ").replace("\n", " ").strip()


def attrs(element: ET.Element, exclude: set[str] | None = None) -> str:
    exclude = exclude or set()
    pairs = [(key, value) for key, value in element.attrib.items() if key not in exclude]
    return "; ".join(f"`{md(key)}`=`{md(value)}`" for key, value in pairs) or "sin atributos adicionales"


def named(element: ET.Element) -> str:
    return element.attrib.get("name", "")


def table(headers: list[str], rows: list[list[object]]) -> list[str]:
    if not rows:
        return ["_No hay elementos declarados de este tipo._", ""]
    result = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    result.extend("| " + " | ".join(md(v) for v in row) + " |" for row in rows)
    result.append("")
    return result


def body_tree(root: ET.Element) -> list[dict[str, object]]:
    """Obtiene cada body una vez, con su ruta, padre directo y joints propios."""
    result: list[dict[str, object]] = []

    def walk(body: ET.Element, parent_path: str, parent_name: str) -> None:
        name = named(body) or "(body sin nombre)"
        path = f"{parent_path}/{name}" if parent_path else name
        own_joints = [
            el for el in list(body)
            if tag_name(el.tag) in {"joint", "freejoint"}
        ]
        direct_geoms = sum(tag_name(el.tag) == "geom" for el in list(body))
        direct_sites = sum(tag_name(el.tag) == "site" for el in list(body))
        result.append({
            "name": name,
            "parent": parent_name or "worldbody",
            "path": path,
            "pos": body.attrib.get("pos", "no declarado"),
            "quat": body.attrib.get("quat", "no declarado"),
            "joints": own_joints,
            "direct_geoms": direct_geoms,
            "direct_sites": direct_sites,
            "inertial": any(tag_name(el.tag) == "inertial" for el in list(body)),
        })
        for child in list(body):
            if tag_name(child.tag) == "body":
                walk(child, path, name)

    for worldbody in (el for el in root.iter() if tag_name(el.tag) == "worldbody"):
        for child in list(worldbody):
            if tag_name(child.tag) == "body":
                walk(child, "", "worldbody")
    return result


def collect_actuators(root: ET.Element) -> list[ET.Element]:
    actuator_tags = {
        "motor", "position", "velocity", "general", "intvelocity", "intposition",
        "muscle", "adhesion", "cylinder", "damper", "friction", "magnet", "plugin",
    }
    # Solo recoger actuadores que sean hijos directos de un contenedor <actuator>.
    result = []
    for container in root.iter():
        if tag_name(container.tag) == "actuator":
            result.extend(child for child in list(container) if tag_name(child.tag) in actuator_tags)
    return result


def collect_sensors(root: ET.Element) -> list[ET.Element]:
    sensor_tags = {
        "accelerometer", "velocimeter", "gyro", "force", "torque", "magnetometer",
        "rangefinder", "jointpos", "jointvel", "jointactuatorfrc", "tendonpos",
        "tendonvel", "actuatorpos", "actuatorvel", "actuatorfrc", "ballquat",
        "ballangvel", "jointlimitpos", "jointlimitvel", "jointlimitfrc", "framepos",
        "framequat", "framexaxis", "frameyaxis", "framezaxis", "framelinvel",
        "frameangvel", "framelinacc", "frameangacc", "subtreecom", "subtreelinvel",
        "subtreeangmom", "user", "plugin",
    }
    result = []
    for container in root.iter():
        if tag_name(container.tag) == "sensor":
            result.extend(child for child in list(container) if tag_name(child.tag) in sensor_tags)
    return result


def collect_sites(root: ET.Element) -> list[dict[str, str]]:
    result = []
    for body in root.iter():
        if tag_name(body.tag) != "body":
            continue
        for site in list(body):
            if tag_name(site.tag) == "site":
                result.append({
                    "name": named(site) or "(site sin nombre)",
                    "body": named(body) or "(body sin nombre)",
                    "pos": site.attrib.get("pos", "no declarado"),
                    "quat": site.attrib.get("quat", "no declarado"),
                    "attributes": attrs(site, {"name", "pos", "quat"}),
                })
    return result


def emit_body_and_joint_blocks(out: list[str], bodies: list[dict[str, object]]) -> None:
    out.extend(["## Cuerpos y joints", "",
                "Esta sección permite responder preguntas sobre dónde está un body, cuál es su padre, "
                "qué joints declara directamente y qué parámetros cinemáticos aparecen en el XML.", ""])
    for body in bodies:
        out.extend([
            f"### Body `{body['name']}`",
            "",
            f"- **Padre directo:** `{body['parent']}`.",
            f"- **Ruta desde la raíz cinemática:** `{body['path']}`.",
            f"- **Posición declarada (`pos`):** `{body['pos']}`.",
            f"- **Orientación declarada (`quat`):** `{body['quat']}`.",
            f"- **Geometrías directas (`geom`):** {body['direct_geoms']}.",
            f"- **Sites directos:** {body['direct_sites']}.",
            f"- **Elemento `inertial` directo:** {'sí' if body['inertial'] else 'no'}.",
        ])
        joints = body["joints"]
        if joints:
            out.append("- **Joints declarados directamente en este body:**")
            for joint in joints:
                jtype = "free" if tag_name(joint.tag) == "freejoint" else joint.attrib.get("type", "hinge (valor predeterminado si no se especifica)")
                out.append(
                    f"  - `{named(joint) or '(joint sin nombre)'}`: tipo `{jtype}`; "
                    f"{attrs(joint, {'name', 'type'})}."
                )
        else:
            out.append("- **Joints declarados directamente en este body:** ninguno.")
        out.append("")


def emit_actuator_blocks(out: list[str], actuators: list[ET.Element]) -> None:
    out.extend(["## Actuadores", "",
                "Cada bloque corresponde a un actuador declarado como hijo de `<actuator>`. "
                "Las referencias a joint, site o tendon se reproducen solo cuando están declaradas.", ""])
    for actuator in actuators:
        name = named(actuator) or "(actuador sin nombre)"
        kind = tag_name(actuator.tag)
        out.extend([
            f"### Actuador `{name}`",
            "",
            f"- **Tipo XML:** `{kind}`.",
            f"- **Joint referenciado:** `{actuator.attrib.get('joint', 'no declarado')}`.",
            f"- **Site referenciado:** `{actuator.attrib.get('site', 'no declarado')}`.",
            f"- **Tendon referenciado:** `{actuator.attrib.get('tendon', 'no declarado')}`.",
            f"- **Otros atributos:** {attrs(actuator, {'name', 'joint', 'site', 'tendon'})}.",
            "",
        ])


def emit_site_blocks(out: list[str], sites: list[dict[str, str]]) -> None:
    out.extend(["## Sites", "",
                "Un site y un sensor son elementos XML diferentes. Un site puede ser referenciado por un sensor; "
                "esa referencia no convierte al site en sensor.", ""])
    for site in sites:
        out.extend([
            f"### Site `{site['name']}`",
            "",
            f"- **Body contenedor:** `{site['body']}`.",
            f"- **Posición (`pos`):** `{site['pos']}`.",
            f"- **Orientación (`quat`):** `{site['quat']}`.",
            f"- **Otros atributos:** {site['attributes']}.",
            "",
        ])


def emit_sensor_blocks(out: list[str], sensors: list[ET.Element], site_names: set[str]) -> None:
    out.extend(["## Sensores", "",
                "Cada bloque representa un elemento sensor explícito dentro de `<sensor>`. "
                "El atributo `site` identifica el site referenciado cuando está presente.", ""])
    for sensor in sensors:
        name = named(sensor) or "(sensor sin nombre)"
        kind = tag_name(sensor.tag)
        site = sensor.attrib.get("site", "")
        site_status = (
            f"`{site}` (existe en la sección Sites)" if site and site in site_names
            else f"`{site}` (no encontrado en la extracción de sites)" if site
            else "no declarado"
        )
        out.extend([
            f"### Sensor `{name}`",
            "",
            f"- **Tipo de sensor:** `{kind}`.",
            f"- **Site referenciado:** {site_status}.",
            f"- **Joint referenciado:** `{sensor.attrib.get('joint', 'no declarado')}`.",
            f"- **Body referenciado:** `{sensor.attrib.get('body', 'no declarado')}`.",
            f"- **Ruido (`noise`):** `{sensor.attrib.get('noise', 'no declarado')}`.",
            f"- **Frecuencia de corte/parámetro `cutoff`:** `{sensor.attrib.get('cutoff', 'no declarado')}`.",
            f"- **Otros atributos:** {attrs(sensor, {'name', 'site', 'joint', 'body', 'noise', 'cutoff'})}.",
            "",
        ])


def generate_markdown(xml_path: Path) -> str:
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    root = ET.parse(xml_path, parser=parser).getroot()
    model_name = root.attrib.get("model", xml_path.stem)
    counts = Counter(tag_name(element.tag) for element in root.iter())
    bodies = body_tree(root)
    actuators = collect_actuators(root)
    sites = collect_sites(root)
    sensors = collect_sensors(root)
    joints = [element for element in root.iter() if tag_name(element.tag) in {"joint", "freejoint"}]
    meshes = [element for element in root.iter() if tag_name(element.tag) == "mesh"]
    geoms = [element for element in root.iter() if tag_name(element.tag) == "geom"]
    site_names = {site["name"] for site in sites}

    out = [
        f"# Modelo MJCF: {model_name}", "",
        f"- **Archivo fuente:** `{xml_path.name}`.",
        f"- **Elemento raíz:** `{tag_name(root.tag)}`; atributos: {attrs(root)}.",
        f"- **Resumen:** {len(bodies)} bodies; {len(joints)} joints/freejoints; "
        f"{len(actuators)} actuadores; {len(geoms)} geoms; {len(meshes)} meshes; "
        f"{len(sites)} sites; {len(sensors)} sensores.",
        "- **Uso del documento:** referencia estructurada derivada del XML para búsquedas técnicas. "
        "El XML original sigue siendo la fuente de verdad.", "",
        "## Índice de consultas", "",
        "- **Cuerpos y articulaciones:** buscar por nombre de body, joint, padre o ruta cinemática.",
        "- **Actuadores:** buscar por nombre de actuador o por joint/site/tendon referenciado.",
        "- **Sites:** buscar por nombre exacto del site o por body contenedor.",
        "- **Sensores:** buscar por nombre, tipo, site referenciado, `noise` o `cutoff`.",
        "- **Relaciones:** buscar qué sensores referencian un site y qué sensores están asociados a un body.", "",
    ]
    emit_body_and_joint_blocks(out, bodies)
    emit_actuator_blocks(out, actuators)
    emit_site_blocks(out, sites)
    emit_sensor_blocks(out, sensors, site_names)

    out.extend(["## Relaciones explícitas sensor–site", "",
                "Relaciones extraídas del atributo `site` de cada sensor. No se infieren relaciones ausentes del XML.", ""])
    relations = [sensor for sensor in sensors if sensor.attrib.get("site")]
    if not relations:
        out.extend(["_No se encontraron sensores con atributo `site`._", ""])
    else:
        for sensor in relations:
            sensor_name = named(sensor) or "(sensor sin nombre)"
            site = sensor.attrib["site"]
            validation = "site declarado en el XML" if site in site_names else "referencia sin site coincidente en la extracción"
            out.extend([
                f"### `{sensor_name}` referencia al site `{site}`",
                "",
                f"- **Elemento sensor:** `{tag_name(sensor.tag)}`.",
                f"- **Validación de referencia:** {validation}.",
                f"- **Parámetros:** noise=`{sensor.attrib.get('noise', 'no declarado')}`; "
                f"cutoff=`{sensor.attrib.get('cutoff', 'no declarado')}`.",
                "",
            ])

    out.extend(["## Notas de interpretación", "",
                "- Los nombres entre backticks se conservan literalmente del XML.",
                "- `site` es el nombre de un atributo de referencia en algunos sensores; no es el nombre del sensor.",
                "- `no declarado` significa que el atributo no aparece en ese elemento XML; no equivale a cero.",
                "- Las explicaciones de este documento describen la estructura extraída y no sustituyen la documentación completa de MJCF.", ""])
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genera Markdown orientado a preguntas técnicas para el MJCF de Unitree G1."
    )
    parser.add_argument("xml", type=Path, help="Ruta al XML MJCF de entrada.")
    parser.add_argument("-o", "--output", type=Path, help="Ruta del Markdown de salida.")
    args = parser.parse_args()

    xml_path = args.xml.expanduser()
    if not xml_path.is_file():
        print(f"ERROR: no existe el archivo XML: {xml_path}", file=sys.stderr)
        return 2
    output_path = args.output or xml_path.with_name(f"{xml_path.stem}_rag.md")
    try:
        markdown = generate_markdown(xml_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    except (ET.ParseError, OSError, UnicodeError) as exc:
        print(f"ERROR al procesar el XML: {exc}", file=sys.stderr)
        return 1
    print("Generación completada.")
    print(f"XML fuente : {xml_path.resolve()}")
    print(f"Markdown   : {output_path.resolve()}")
    print(f"Tamaño     : {output_path.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
