"""
ClaimExtractor.py
=================

Extractor de afirmaciones para GIAR-ORION.

Responsabilidades:
- Segmentar una respuesta en unidades textuales.
- Solicitar a Ollama la extracción de afirmaciones factuales atómicas.
- Exigir una clasificación para cada unidad de entrada.
- Detectar omisiones, duplicados y estructuras inconsistentes.
- Devolver un informe JSON-serializable.

Importante:
La cobertura estructural no garantiza exhaustividad semántica. Este módulo
no verifica la verdad de las afirmaciones; esa tarea corresponde a
EvidenceVerifier.py.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from typing import Any


class ClaimExtractorError(RuntimeError):
    """Error durante la extracción o validación de afirmaciones."""


class ClaimExtractor:
    """Extrae afirmaciones factuales utilizando un modelo servido por Ollama."""

    VERSION = "0.1.2"

    def __init__(
        self,
        base_url: str,
        model: str,
        think: bool = False,
        num_predict: int = 2048,
        timeout: int = 180,
    ) -> None:
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("base_url debe ser un texto no vacío.")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model debe ser un texto no vacío.")
        if not isinstance(think, bool):
            raise ValueError("think debe ser booleano.")
        if (
            isinstance(num_predict, bool)
            or not isinstance(num_predict, int)
            or num_predict <= 0
        ):
            raise ValueError("num_predict debe ser un entero positivo.")
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, int)
            or timeout <= 0
        ):
            raise ValueError("timeout debe ser un entero positivo.")

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.think = think
        self.num_predict = num_predict
        self.timeout = timeout

    @staticmethod
    def _split_units(response: str) -> list[str]:
        """
        Divide el texto en unidades numeradas.

        La segmentación es deliberadamente sencilla y heurística. Separa
        líneas y oraciones cuando detecta puntuación terminal seguida de
        un comienzo probable de oración. No constituye un análisis
        lingüístico completo.
        """
        units: list[str] = []

        for line in response.splitlines():
            line = line.strip()
            if not line:
                continue

            parts = re.split(
                r'(?<=[.!?])\s+(?=(?:[¿¡"\']?[A-ZÁÉÍÓÚÜÑ0-9]))',
                line,
            )

            for part in parts:
                cleaned = part.strip()
                if cleaned:
                    units.append(cleaned)

        return units

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        """Decodifica un objeto JSON, tolerando cercas Markdown externas."""
        cleaned = text.strip()

        if cleaned.startswith("```"):
            cleaned = re.sub(
                r"^```(?:json)?\s*",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")

            if start < 0 or end <= start:
                raise ClaimExtractorError(
                    "El modelo no devolvió un objeto JSON válido."
                )

            try:
                data = json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError as exc:
                raise ClaimExtractorError(
                    "El modelo devolvió JSON malformado."
                ) from exc

        if not isinstance(data, dict):
            raise ClaimExtractorError(
                "La salida JSON del modelo debe ser un objeto."
            )

        return data

    def _call_ollama(self, prompt: str) -> str:
        """Envía el prompt a la API local de chat de Ollama."""
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Sos un extractor de afirmaciones factuales. "
                        "No evalúes si las afirmaciones son verdaderas. "
                        "No agregues conocimiento ni completes información "
                        "ausente. Respondé exclusivamente con JSON válido."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "stream": False,
            "think": self.think,
            "format": "json",
            "options": {
                "num_predict": self.num_predict,
                "temperature": 0,
            },
        }

        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as http_response:
                result = json.loads(
                    http_response.read().decode("utf-8")
                )
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ClaimExtractorError(
                f"Ollama devolvió HTTP {exc.code}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise ClaimExtractorError(
                "No se pudo conectar con Ollama para extraer afirmaciones. "
                "Verificá que el servicio esté funcionando."
            ) from exc
        except json.JSONDecodeError as exc:
            raise ClaimExtractorError(
                "Ollama devolvió una respuesta JSON inválida."
            ) from exc

        message = result.get("message")

        if (
            not isinstance(message, dict)
            or not isinstance(message.get("content"), str)
        ):
            raise ClaimExtractorError(
                "Ollama no devolvió el contenido textual esperado."
            )

        return message["content"]

    @staticmethod
    def _build_prompt(units: list[str]) -> str:
        """Construye el prompt de extracción con unidades identificadas."""
        numbered_units = [
            {"id": index, "text": text}
            for index, text in enumerate(units, start=1)
        ]

        return (
            "Analizá la respuesta completa, unidad por unidad.\n"
            "Identificá todas las afirmaciones factuales explícitas de cada "
            "unidad. Dividí las oraciones que contengan varias afirmaciones "
            "en afirmaciones atómicas.\n"
            "No agregues información, no completes datos implícitos y no "
            "corrijas el contenido original.\n"
            "No conviertas preguntas, opiniones, títulos o instrucciones "
            "en afirmaciones factuales.\n\n"
            "Para CADA unidad de entrada devolvé exactamente un elemento "
            "en la lista coverage:\n"
            '- status "FACTUAL" si contiene una o más afirmaciones factuales;\n'
            '- status "NON_FACTUAL" si no contiene afirmaciones factuales.\n'
            "Si es FACTUAL, claims debe contener una o más afirmaciones "
            "atómicas que correspondan a esa unidad.\n"
            "Si es NON_FACTUAL, claims debe ser una lista vacía.\n"
            "No omitas unidades, no inventes identificadores y no combines "
            "unidades distintas.\n\n"
            "Devolvé exclusivamente un JSON con esta estructura:\n"
            "{"
            '"coverage":['
            '{"unit_id":1,"status":"FACTUAL",'
            '"claims":["Afirmación atómica."]}'
            '],'
            '"notes":[]'
            "}\n\n"
            "UNIDADES DE LA RESPUESTA:\n"
            + json.dumps(numbered_units, ensure_ascii=False, indent=2)
        )

    @staticmethod
    def _validate_extraction(
        units: list[str],
        data: dict[str, Any],
        model: str,
    ) -> dict[str, Any]:
        """Valida la estructura y la cobertura de las unidades recibidas."""
        coverage = data.get("coverage")

        if not isinstance(coverage, list):
            raise ClaimExtractorError(
                "La salida no contiene una lista 'coverage'."
            )

        expected_ids = set(range(1, len(units) + 1))
        received_ids: list[int] = []
        claims: list[dict[str, Any]] = []
        errors: list[str] = []

        for index, item in enumerate(coverage):
            if not isinstance(item, dict):
                errors.append(
                    f"coverage[{index}] no es un objeto."
                )
                continue

            unit_id = item.get("unit_id")

            if isinstance(unit_id, bool) or not isinstance(unit_id, int):
                errors.append(
                    f"coverage[{index}] tiene unit_id inválido."
                )
                continue

            received_ids.append(unit_id)

            if unit_id not in expected_ids:
                errors.append(
                    f"Se recibió un unit_id inexistente: {unit_id}."
                )
                continue

            status = item.get("status")
            unit_claims = item.get("claims")

            if status not in ("FACTUAL", "NON_FACTUAL"):
                errors.append(
                    f"Unidad {unit_id}: status inválido."
                )
                continue

            if not isinstance(unit_claims, list):
                errors.append(
                    f"Unidad {unit_id}: claims debe ser una lista."
                )
                continue

            if not all(
                isinstance(claim, str) and claim.strip()
                for claim in unit_claims
            ):
                errors.append(
                    f"Unidad {unit_id}: contiene afirmaciones vacías "
                    "o inválidas."
                )
                continue

            if status == "FACTUAL" and not unit_claims:
                errors.append(
                    f"Unidad {unit_id}: FACTUAL sin afirmaciones."
                )
                continue

            if status == "NON_FACTUAL" and unit_claims:
                errors.append(
                    f"Unidad {unit_id}: NON_FACTUAL contiene afirmaciones."
                )
                continue

            for claim in unit_claims:
                claims.append(
                    {
                        "claim": claim.strip(),
                        "unit_id": unit_id,
                        "source_unit": units[unit_id - 1],
                    }
                )

        duplicates = sorted(
            unit_id
            for unit_id in set(received_ids)
            if received_ids.count(unit_id) > 1
        )

        if duplicates:
            errors.append(
                f"Unidades duplicadas en coverage: {duplicates}."
            )

        missing_ids = sorted(expected_ids - set(received_ids))
        if missing_ids:
            errors.append(
                f"Unidades sin clasificar: {missing_ids}."
            )

        extra_ids = sorted(set(received_ids) - expected_ids)
        if extra_ids:
            errors.append(
                f"IDs de unidad no esperados: {extra_ids}."
            )

        notes = data.get("notes", [])
        if not isinstance(notes, list):
            errors.append("'notes' debe ser una lista.")
            notes = []

        return {
            "extractor": "ClaimExtractor",
            "version": ClaimExtractor.VERSION,
            "model": model,
            "complete": not errors,
            "unit_count": len(units),
            "classified_unit_count": len(
                set(received_ids) & expected_ids
            ),
            "claim_count": len(claims),
            "claims": claims,
            "coverage": coverage,
            "errors": errors,
            "notes": notes,
            "limitations": [
                "La cobertura estructural no garantiza exhaustividad semántica.",
                "El modelo puede omitir afirmaciones o clasificarlas incorrectamente.",
                "La extracción no verifica la verdad ni el respaldo de las afirmaciones.",
                "Si complete es False, la respuesta no debe considerarse verificada.",
            ],
        }

    def extract(self, response: str) -> dict[str, Any]:
        """
        Extrae afirmaciones atómicas y audita la cobertura estructural.

        `complete=True` indica que todas las unidades recibieron una clasificación
        estructuralmente válida. No garantiza que el modelo haya detectado cada
        afirmación semántica presente en el texto.
        """
        if not isinstance(response, str) or not response.strip():
            raise ValueError("response debe ser un texto no vacío.")

        units = self._split_units(response)

        if not units:
            raise ClaimExtractorError(
                "No se pudieron identificar unidades de texto."
            )

        prompt = self._build_prompt(units)
        raw_output = self._call_ollama(prompt)
        data = self._extract_json(raw_output)

        return self._validate_extraction(
            units=units,
            data=data,
            model=self.model,
        )


def extract_claims(
    response: str,
    base_url: str = "http://localhost:11434",
    model: str = "qwen3:8b",
    think: bool = False,
    num_predict: int = 2048,
    timeout: int = 180,
) -> dict[str, Any]:
    """Función de conveniencia para extraer afirmaciones."""
    extractor = ClaimExtractor(
        base_url=base_url,
        model=model,
        think=think,
        num_predict=num_predict,
        timeout=timeout,
    )
    return extractor.extract(response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prueba independiente de ClaimExtractor."
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:11434",
    )
    parser.add_argument(
        "--model",
        default="qwen3:8b",
    )
    parser.add_argument(
        "--text",
        default=(
            "SAC es un algoritmo off-policy. "
            "Su Actor genera acciones mediante una distribución probabilística."
        ),
    )
    parser.add_argument(
        "--think",
        action="store_true",
        help="Habilita el parámetro think de Ollama.",
    )
    args = parser.parse_args()

    result = extract_claims(
        response=args.text,
        base_url=args.base_url,
        model=args.model,
        think=args.think,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )
