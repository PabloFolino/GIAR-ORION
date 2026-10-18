#!/usr/bin/env python3
"""
xml_to_markdown.py
------------------
Convierte un archivo XML en una representación Markdown legible y trazable.

Uso:
    python Tools/xml_to_markdown.py archivo.xml
    python Tools/xml_to_markdown.py archivo.xml -o salida.md
    python Tools/xml_to_markdown.py archivo.xml --encoding utf-8

La herramienta no modifica el XML de origen. Si no se indica -o, crea el
Markdown junto al XML, con el mismo nombre base y el sufijo "_converted.md".

Ej: python Tools/xml_to_markdown.py "Knowledge/Unitree/G1/g1_29dof_with_hand.xml"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET


def local_name(tag: object) -> str:
    """Devuelve un nombre legible, conservando el nombre completo si no es texto."""
    if not isinstance(tag, str):
        return str(tag)
    # ElementTree representa etiquetas con namespace como {URI}nombre.
    if tag.startswith("{") and "}" in tag:
        namespace, name = tag[1:].split("}", 1)
        return f"{name} (namespace: {namespace})"
    return tag


def escape_table_cell(value: object) -> str:
    """Escapa caracteres que romperían una tabla Markdown."""
    return str(value).replace("\\", "\\\\").replace("|", r"\|").replace("\r", " ").replace("\n", "<br>")


def clean_text(value: str | None) -> str:
    """Normaliza espacios de texto sin cambiar su contenido léxico esencial."""
    if value is None:
        return ""
    return " ".join(value.split())


def element_path(element: ET.Element, parent_path: str) -> str:
    """Construye una ruta descriptiva del elemento dentro del documento."""
    tag = local_name(element.tag)
    # Agrega un índice cuando existen hermanos con el mismo nombre.
    if parent_path:
        return f"{parent_path}/{tag}"
    return f"/{tag}"


def render_element(
    element: ET.Element,
    *,
    depth: int,
    parent_path: str,
    sibling_index: int,
    sibling_count: int,
    lines: list[str],
) -> None:
    """Representa recursivamente un elemento XML y todos sus descendientes."""
    tag = local_name(element.tag)
    path = element_path(element, parent_path)
    if sibling_count > 1:
        path = f"{path}[{sibling_index}]"

    # Markdown admite hasta seis niveles de encabezado.
    heading_level = min(depth + 2, 6)
    heading = "#" * heading_level
    lines.append("")
    lines.append(f"{heading} `{tag}`")
    lines.append("")
    lines.append(f"- **Ruta:** `{path}`")

    attributes = list(element.attrib.items())
    if attributes:
        lines.extend(["", "**Atributos**", "", "| Nombre | Valor |", "|---|---|"])
        for name, value in attributes:
            lines.append(f"| `{escape_table_cell(name)}` | `{escape_table_cell(value)}` |")

    text = clean_text(element.text)
    if text:
        lines.extend(["", "**Texto**", "", text])

    # Los comentarios se conservan si el parser fue configurado para insertarlos.
    children = list(element)
    if children:
        lines.extend(["", f"**Elementos hijos ({len(children)})**"])
        counts: dict[str, int] = {}
        for child in children:
            key = local_name(child.tag)
            counts[key] = counts.get(key, 0) + 1
        seen: dict[str, int] = {}
        for child in children:
            key = local_name(child.tag)
            seen[key] = seen.get(key, 0) + 1
            if not isinstance(child.tag, str):
                # Representa comentarios u otros nodos especiales.
                comment_text = clean_text(child.text)
                lines.extend(["", f"- **Nodo especial:** `{child.tag}`"])
                if comment_text:
                    lines.append(f"  - Contenido: {comment_text}")
                continue
            render_element(
                child,
                depth=depth + 1,
                parent_path=path,
                sibling_index=seen[key],
                sibling_count=counts[key],
                lines=lines,
            )

    # En XML mixto, el texto posterior a un hijo también forma parte del contenido.
    for child in children:
        tail = clean_text(child.tail)
        if tail:
            lines.extend(["", f"**Texto posterior a `{local_name(child.tag)}`**", "", tail])


def convert_xml_to_markdown(
    input_path: Path,
    output_path: Path,
    *,
    encoding: str = "utf-8",
) -> None:
    """Lee XML, genera Markdown y lo escribe en el destino indicado."""
    if not input_path.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {input_path}")
    if not input_path.is_file():
        raise ValueError(f"La ruta de entrada no es un archivo: {input_path}")
    if input_path.resolve() == output_path.resolve():
        raise ValueError("El archivo de salida no puede sobrescribir el XML de origen.")

    # Conserva comentarios en la estructura analizada.
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    tree = ET.parse(input_path, parser=parser)
    root = tree.getroot()

    lines: list[str] = [
        f"# Documento XML: `{input_path.name}`",
        "",
        "> Markdown generado automáticamente por `xml_to_markdown.py`.",
        "> La fuente de referencia es el XML original; esta representación no lo modifica.",
        "",
        f"- **Archivo de origen:** `{input_path.name}`",
        f"- **Elemento raíz:** `{local_name(root.tag)}`",
        f"- **Codificación de salida:** `{encoding}`",
        "",
        "---",
    ]

    render_element(
        root,
        depth=0,
        parent_path="",
        sibling_index=1,
        sibling_count=1,
        lines=lines,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines).rstrip() + "\n"
    output_path.write_text(content, encoding=encoding)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convierte un archivo XML en una representación Markdown."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Ruta del archivo XML de origen.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help=(
            "Ruta del Markdown de salida. Si se omite, se crea junto al XML "
            "con el sufijo '_converted.md'."
        ),
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Codificación del Markdown de salida (predeterminada: utf-8).",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = args.input.expanduser()
    if not input_path.is_absolute():
        input_path = (Path.cwd() / input_path).resolve()

    output_path = args.output.expanduser() if args.output else input_path.with_name(
        f"{input_path.stem}_converted.md"
    )
    if not output_path.is_absolute():
        output_path = (Path.cwd() / output_path).resolve()

    try:
        convert_xml_to_markdown(input_path, output_path, encoding=args.encoding)
    except (ET.ParseError, OSError, ValueError, LookupError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("Conversión completada.")
    print(f"Origen : {input_path}")
    print(f"Destino: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
