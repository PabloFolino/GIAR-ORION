"""
EvidenceVerifier.py
===================

Módulo independiente de verificación de evidencias para GIAR-ORION.

Versión: 0.3.3

Alcance de esta primera versión
-------------------------------
1. Recibe los resultados RAG con el formato actual:
   {"source": str, "text": str, "score": float, "mode": str}
2. Recibe los resultados DDGS con el formato actual:
   {"title": str, "url": str, "description": str, "source": str}
3. Comprueba si las URLs y las rutas de fuentes mencionadas en la respuesta
   aparecen en las evidencias recibidas.
4. Detecta URLs duplicadas dentro de las evidencias.
5. Devuelve un informe estructurado.

Alcance
-------
Comprueba referencias y adjudica semánticamente afirmaciones frente a las
evidencias suministradas mediante Qwen local (Ollama). mDeBERTa se conserva
como señal NLI diagnóstica. El glosario Terminology.json aporta contexto
terminológico pertinente, sin sustituir ni ampliar la evidencia.

El módulo no modifica RAG, DDGS ni la interfaz de GIAR-ORION.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


class EvidenceVerifierError(ValueError):
    """Error en los datos recibidos por el verificador."""


class EvidenceVerifier:
    """Realiza controles deterministas sobre referencias y evidencias."""

    VERSION = "0.3.3-batch-experiment-1"
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    DEFAULT_TERMINOLOGY_FILE = (PROJECT_ROOT / "Knowledge" / "Terminology.json" )
    MAX_TERMINOLOGY_CONTEXT_TERMS = 12

    # Se capturan URLs HTTP(S) escritas en la respuesta.
    URL_PATTERN = re.compile(r"https?://[^\s<>\]\[\"'()]+", re.IGNORECASE)

    DEFAULT_NLI_MODEL = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"

    def __init__(
        self,
        nli_model_name: str = DEFAULT_NLI_MODEL,
        entailment_threshold: float = 0.80,
        contradiction_threshold: float = 0.80,
        decision_margin: float = 0.15,
        device: str | None = None,
        *,
        ollama_url: str = "http://localhost:11434",
        adjudication_model: str = "qwen3:8b",
        adjudication_timeout: int = 90,
        use_ollama_adjudication: bool = True,
        terminology_path: str | Path | None = None,
    ) -> None:
        """Inicializa NLI diagnóstico y juez semántico local.

        NLI deja de ser la autoridad final: sus scores se conservan como
        diagnóstico. La decisión semántica se realiza con Ollama/Qwen,
        usando exclusivamente la evidencia suministrada.
        """
        if not 0 <= entailment_threshold <= 1:
            raise ValueError("entailment_threshold debe estar entre 0 y 1.")
        if not 0 <= contradiction_threshold <= 1:
            raise ValueError("contradiction_threshold debe estar entre 0 y 1.")
        if not 0 <= decision_margin <= 1:
            raise ValueError("decision_margin debe estar entre 0 y 1.")
        self.nli_model_name = nli_model_name
        self.entailment_threshold = entailment_threshold
        self.contradiction_threshold = contradiction_threshold
        self.decision_margin = decision_margin
        self.device = device
        self._tokenizer = None
        self._nli_model = None
        self._label_indices = None
        self.ollama_url = ollama_url.rstrip("/")
        self.adjudication_model = adjudication_model
        self.adjudication_timeout = adjudication_timeout
        self.use_ollama_adjudication = use_ollama_adjudication
        self.terminology_path = (
            Path(terminology_path).expanduser().resolve()
            if terminology_path is not None
            else self.DEFAULT_TERMINOLOGY_FILE
        )
        if not self.terminology_path.is_file():
            raise FileNotFoundError(
                f"No se encontró Terminology.json: {self.terminology_path}"
            )        
        self._terminology = self._load_terminology(self.terminology_path)

    @staticmethod
    def _load_terminology(path: Path) -> dict[str, Any]:
        """Carga y valida el glosario; no permite continuar sin contexto válido."""
        if not path.is_file():
            raise FileNotFoundError(
                f"No se encontró Terminology.json en: {path}. "
                "Coloque el archivo junto a EvidenceVerifier.py o indique terminology_path."
            )
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise EvidenceVerifierError(
                f"No se pudo leer Terminology.json ({path}): {type(exc).__name__}: {exc}"
            ) from exc
        if not isinstance(data, dict) or not isinstance(data.get("terms"), list):
            raise EvidenceVerifierError(
                "Terminology.json inválido: se requiere un objeto raíz con 'terms' como lista."
            )
        if not data["terms"]:
            raise EvidenceVerifierError("Terminology.json inválido: 'terms' no puede estar vacío.")
        required_text = ("id", "domain", "term_es", "term_en", "definition_es")
        seen_ids = set()
        for index, term in enumerate(data["terms"]):
            if not isinstance(term, dict):
                raise EvidenceVerifierError(f"Terminology.json: terms[{index}] debe ser un objeto.")
            for key in required_text:
                if not isinstance(term.get(key), str) or not term[key].strip():
                    raise EvidenceVerifierError(
                        f"Terminology.json: terms[{index}].{key} debe ser texto no vacío."
                    )
            if term["id"] in seen_ids:
                raise EvidenceVerifierError(
                    f"Terminology.json: identificador duplicado {term['id']!r}."
                )
            seen_ids.add(term["id"])
            aliases = term.get("aliases", [])
            if not isinstance(aliases, list) or not all(
                isinstance(alias, str) and alias.strip() for alias in aliases
            ):
                raise EvidenceVerifierError(
                    f"Terminology.json: terms[{index}].aliases debe ser una lista de textos no vacíos."
                )
            if not isinstance(term.get("notes", ""), str):
                raise EvidenceVerifierError(
                    f"Terminology.json: terms[{index}].notes debe ser texto."
                )
        return data

    @staticmethod
    def _normalize_terminology_text(text: str) -> str:
        text = unicodedata.normalize("NFKC", text).casefold()
        return re.sub(r"\s+", " ", text).strip()

    def _select_terminology(
        self, claim: str, evidence_items: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Selecciona entradas cuyo término aparece literalmente en claim/evidencias."""
        corpus = self._normalize_terminology_text(
            " ".join([claim] + [str(item.get("text", "")) for item in evidence_items])
        )
        matches = []
        for entry in self._terminology["terms"]:
            candidates = [entry["term_es"], entry["term_en"], *entry.get("aliases", [])]
            matched = []
            for candidate in candidates:
                candidate_norm = self._normalize_terminology_text(candidate)
                if len(candidate_norm) < 2:
                    continue
                if re.search(rf"(?<!\w){re.escape(candidate_norm)}(?!\w)", corpus):
                    matched.append(candidate)
            if matched:
                matches.append((max(map(len, matched)), entry, matched))
        matches.sort(key=lambda item: item[0], reverse=True)
        selected = []
        for _, entry, matched in matches[: self.MAX_TERMINOLOGY_CONTEXT_TERMS]:
            selected.append({
                "id": entry["id"],
                "domain": entry["domain"],
                "term_es": entry["term_es"],
                "term_en": entry["term_en"],
                "definition_es": entry["definition_es"],
                "matched_forms": ", ".join(dict.fromkeys(matched)),
                "aliases": ", ".join(entry.get("aliases", [])),
                "notes": entry.get("notes", ""),
            })
        return selected

    def _load_nli_model(self) -> None:
        """Carga el modelo NLI solo cuando se solicita verificación semántica."""
        if self._nli_model is not None:
            return
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "La verificación NLI requiere instalar torch y transformers."
            ) from exc

        selected_device = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._tokenizer = AutoTokenizer.from_pretrained(self.nli_model_name)
        self._nli_model = AutoModelForSequenceClassification.from_pretrained(
            self.nli_model_name
        )
        self._nli_model.to(selected_device)
        self._nli_model.eval()
        self.device = selected_device

        labels = {
            str(label).lower(): int(index)
            for index, label in self._nli_model.config.id2label.items()
        }
        indices = {}
        for target in ("entailment", "neutral", "contradiction"):
            found = [idx for label, idx in labels.items() if target in label]
            if len(found) != 1:
                raise RuntimeError(
                    f"No se identifica la etiqueta NLI {target!r}: {labels}"
                )
            indices[target] = found[0]
        self._label_indices = indices

    @staticmethod
    def _roles_in_text(text: str) -> set[str]:
        """
        Detecta roles técnicos explícitos para evitar contradicciones espurias
        cuando la evidencia y la afirmación hablan de componentes distintos.

        Es una salvaguarda conservadora, no un parser semántico general.
        """
        normalized = re.sub(r"[^a-záéíóúüñ0-9_]+", " ", text.lower())
        role_groups = {
            "actor": ("actor", "policy network", "red actor"),
            "critic": ("critic", "crítico", "red critic", "red crítica"),
            "replay_buffer": ("replay buffer", "buffer de repetición"),
            "environment": ("environment", "entorno"),
            "robot": ("robot", "robotic system", "sistema robótico"),
            "policy": ("policy", "política"),
            "value_function": ("value function", "función de valor"),
        }
        found = set()
        padded = f" {normalized} "
        for role, variants in role_groups.items():
            if any(f" {variant} " in padded for variant in variants):
                found.add(role)
        return found

    @classmethod
    def _role_mismatch(cls, evidence_text: str, claim_text: str) -> bool:
        """
        True cuando ambos textos identifican roles técnicos, pero no comparten
        ninguno. En ese caso, la etiqueta CONTRADICTED no se acepta solo por NLI.
        """
        evidence_roles = cls._roles_in_text(evidence_text)
        claim_roles = cls._roles_in_text(claim_text)
        return bool(
            evidence_roles
            and claim_roles
            and evidence_roles.isdisjoint(claim_roles)
        )

    def _ollama_adjudicate(self, claim: str, evidence_items: list[dict[str, Any]]) -> dict[str, Any]:
        """Adjudica con JSON Schema y un único reintento ante salida inválida.

        Los errores HTTP/conectividad no se reintentan. Se conserva la respuesta
        original de cada intento para diagnosticar fallos de formato o truncamiento.
        """
        import json
        import urllib.request

        numbered = [
            {"id": i, "source": str(item.get("source", "")), "text": item["text"]}
            for i, item in enumerate(evidence_items)
        ]
        terminology_context = self._select_terminology(claim, evidence_items)
        terminology_block = (
            "RELEVANT TERMINOLOGY FROM THE PROJECT GLOSSARY (context only; "
            "do not treat topical similarity as evidence):\n"
            + json.dumps(terminology_context, ensure_ascii=False)
            + "\n\n"
            if terminology_context else
            "RELEVANT TERMINOLOGY: no glossary entry matched the supplied claim/evidence.\n\n"
        )
        prompt = (
            "You are a strict evidence-verification component. Judge ONLY the supplied evidence; "
            "do not use outside knowledge and do not infer missing facts.\n"
            "For each evidence item return exactly one label:\n"
            "SUPPORTED = the evidence directly states or clearly entails the whole claim.\n"
            "CONTRADICTED = the evidence directly states an incompatible fact about the SAME "
            "subject, property and conditions.\n"
            "INSUFFICIENT = related topic, different component/aspect, partial support, "
            "or no information sufficient to decide. Lack of mention is NOT contradiction.\n"
            "Terminology and paraphrases may be equivalent across Spanish and English. "
            "Recognize synonyms only when the meaning is genuinely equivalent. "
            "Do not treat mere topical similarity as support.\n"
            "In the context of the Soft Actor-Critic (SAC) algorithm, "
            "'alpha' (α), 'entropy temperature', and "
            "'entropy temperature coefficient' refer to the same parameter: "
            "the coefficient that weights the entropy term in the policy objective. "
            "Treat these terms as equivalent when evaluating evidence about SAC.\n"
            "Return one item for every evidence id, exactly once. Reasons must be in Spanish and no longer than 20 words.\n\n"
            f"{terminology_block}"
            f"CLAIM:\n{claim}\n\nEVIDENCE ITEMS:\n"
            f"{json.dumps(numbered, ensure_ascii=False)}"
        )
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer", "minimum": 0},
                            "label": {"type": "string", "enum": ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT"]},
                            "reason": {"type": "string", "maxLength": 240},
                        },
                        "required": ["id", "label", "reason"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["items"],
            "additionalProperties": False,
        }
        diagnostics = []
        last_error = None
        first_done_reason = None

        for attempt in (1, 2):
            messages = [{"role": "user", "content": prompt}]
            if attempt == 2:
                if first_done_reason == "length":
                    correction = (
                        "CORRECTION: the previous response was cut off by the output-token limit. "
                        "Complete the required JSON object. Return exactly one item per evidence id. "
                        "Keep each Spanish reason to at most 20 words. Return JSON only."
                    )
                else:
                    correction = (
                        "CORRECTION: the previous output did not satisfy the required schema. "
                        "Return ONLY an object with the required 'items' array, including every "
                        "evidence id exactly once. Keep each Spanish reason to at most 20 words. "
                        "Do not add any other top-level key."
                    )
                messages.append({"role": "user", "content": correction})

            # Solo se amplía el límite del segundo intento si Ollama informó
            # truncamiento ("length") en el primero. Los demás reintentos
            # conservan el presupuesto original.
            num_predict = 1000 if attempt == 2 and first_done_reason == "length" else 700
            payload = {
                "model": self.adjudication_model,
                "messages": messages,
                "stream": False,
                "format": schema,
                "options": {"temperature": 0, "num_predict": num_predict},
            }
            request = urllib.request.Request(
                f"{self.ollama_url}/api/chat",
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            # No reintento para errores HTTP, timeout o conectividad.
            with urllib.request.urlopen(request, timeout=self.adjudication_timeout) as response:
                body = json.loads(response.read().decode("utf-8"))

            message = body.get("message", {}) if isinstance(body, dict) else {}
            raw = message.get("content", "") if isinstance(message, dict) else ""
            done_reason = body.get("done_reason") if isinstance(body, dict) else None
            if attempt == 1:
                first_done_reason = done_reason
            diagnostic = {
                "attempt": attempt,
                "num_predict": num_predict,
                "done_reason": done_reason,
                "total_duration_ns": body.get("total_duration") if isinstance(body, dict) else None,
                "prompt_eval_count": body.get("prompt_eval_count") if isinstance(body, dict) else None,
                "eval_count": body.get("eval_count") if isinstance(body, dict) else None,
                "raw_response": raw,
                "validation_error": None,
            }
            try:
                parsed = json.loads(raw)
                rows = parsed.get("items") if isinstance(parsed, dict) else None
                if not isinstance(rows, list):
                    raise ValueError("La respuesta JSON no contiene un arreglo 'items'.")

                by_id = {}
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    try:
                        idx = int(row.get("id"))
                    except (TypeError, ValueError):
                        continue
                    label = str(row.get("label", "")).upper().strip()
                    if idx not in range(len(evidence_items)) or label not in {
                        "SUPPORTED", "CONTRADICTED", "INSUFFICIENT"
                    } or idx in by_id:
                        continue
                    by_id[idx] = {
                        "label": label,
                        "reason": str(row.get("reason", ""))[:500],
                    }
                if len(by_id) != len(evidence_items):
                    raise ValueError(
                        f"Se recibieron {len(by_id)} clasificaciones válidas de "
                        f"{len(evidence_items)} evidencias."
                    )
                diagnostics.append(diagnostic)
                return {
                    "items": by_id,
                    "model": self.adjudication_model,
                    "diagnostics": diagnostics,
                    "terminology_terms_used": [item["id"] for item in terminology_context],
                }
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                diagnostic["validation_error"] = last_error
                diagnostics.append(diagnostic)

        error = RuntimeError(
            f"Qwen produjo una salida inválida en los dos intentos. Último error: {last_error}"
        )
        error.diagnostics = diagnostics
        raise error

    def _ollama_adjudicate_batch(
        self, claims: list[str], evidence_items: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Adjudica un pequeño lote de afirmaciones en una sola llamada Ollama.

        La salida conserva una clasificación independiente por par
        (afirmación, evidencia). Si falta cualquier clasificación, el lote
        completo falla de forma cerrada y sus afirmaciones quedan INSUFFICIENT.
        """
        import json
        import urllib.request

        claim_rows = [
            {"claim_id": i, "claim": claim,
             "terminology": self._select_terminology(claim, evidence_items)}
            for i, claim in enumerate(claims)
        ]
        evidence_rows = [
            {"evidence_id": i, "source": str(item.get("source", "")),
             "text": item["text"]}
            for i, item in enumerate(evidence_items)
        ]
        prompt = (
            "You are a strict evidence-verification component. Judge ONLY the supplied evidence; "
            "do not use outside knowledge and do not infer missing facts.\n"
            "For EVERY claim_id and EVERY evidence_id, return exactly one label:\n"
            "SUPPORTED = the evidence directly states or clearly entails the whole claim.\n"
            "CONTRADICTED = the evidence directly states an incompatible fact about the SAME "
            "subject, property and conditions.\n"
            "INSUFFICIENT = related topic, different component/aspect, partial support, or "
            "insufficient information. Lack of mention is NOT contradiction.\n"
            "Terminology and paraphrases may be equivalent across Spanish and English only "
            "when genuinely equivalent. For SAC, alpha (α), entropy temperature and "
            "entropy temperature coefficient refer to the same policy-entropy coefficient.\n"
            "The terminology attached to each claim is context only, never evidence.\n"
            "Return one classification for every pair. Reasons must be in Spanish, at most "
            "15 words. Do not omit pairs.\n\n"
            "CLAIMS (each has its own terminology context):\n"
            f"{json.dumps(claim_rows, ensure_ascii=False)}\n\n"
            "EVIDENCE:\n"
            f"{json.dumps(evidence_rows, ensure_ascii=False)}"
        )
        schema = {
            "type": "object",
            "properties": {"results": {"type": "array", "items": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "integer", "minimum": 0},
                    "items": {"type": "array", "items": {
                        "type": "object",
                        "properties": {
                            "evidence_id": {"type": "integer", "minimum": 0},
                            "label": {"type": "string", "enum": ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT"]},
                            "reason": {"type": "string", "maxLength": 180},
                        },
                        "required": ["evidence_id", "label", "reason"],
                        "additionalProperties": False,
                    }},
                },
                "required": ["claim_id", "items"],
                "additionalProperties": False,
            }}},
            "required": ["results"], "additionalProperties": False,
        }
        diagnostics = []
        first_done_reason = None
        last_error = None
        for attempt in (1, 2):
            messages = [{"role": "user", "content": prompt}]
            if attempt == 2:
                correction = (
                    "Return the complete JSON schema only. Include every claim_id and every "
                    "evidence_id exactly once. Keep reasons very short."
                )
                messages.append({"role": "user", "content": correction})
            num_predict = 1200 if attempt == 2 and first_done_reason == "length" else 900
            payload = {
                "model": self.adjudication_model,
                "messages": messages,
                "stream": False,
                "format": schema,
                "options": {"temperature": 0, "num_predict": num_predict},
            }
            request = urllib.request.Request(
                f"{self.ollama_url}/api/chat",
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(request, timeout=self.adjudication_timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
            message = body.get("message", {}) if isinstance(body, dict) else {}
            raw = message.get("content", "") if isinstance(message, dict) else ""
            done_reason = body.get("done_reason") if isinstance(body, dict) else None
            if attempt == 1:
                first_done_reason = done_reason
            diagnostic = {
                "attempt": attempt, "num_predict": num_predict,
                "done_reason": done_reason,
                "total_duration_ns": body.get("total_duration"),
                "prompt_eval_count": body.get("prompt_eval_count"),
                "eval_count": body.get("eval_count"),
                "raw_response": raw, "validation_error": None,
                "batch_claim_count": len(claims),
                "batch_evidence_count": len(evidence_items),
            }
            try:
                parsed = json.loads(raw)
                rows = parsed.get("results") if isinstance(parsed, dict) else None
                if not isinstance(rows, list):
                    raise ValueError("La respuesta no contiene 'results'.")
                by_claim = {}
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    try:
                        ci = int(row.get("claim_id"))
                    except (TypeError, ValueError):
                        continue
                    if ci not in range(len(claims)) or ci in by_claim:
                        continue
                    evidence_map = {}
                    for item in row.get("items", []):
                        if not isinstance(item, dict):
                            continue
                        try:
                            ei = int(item.get("evidence_id"))
                        except (TypeError, ValueError):
                            continue
                        label = str(item.get("label", "")).upper().strip()
                        if ei in range(len(evidence_items)) and label in {
                            "SUPPORTED", "CONTRADICTED", "INSUFFICIENT"
                        } and ei not in evidence_map:
                            evidence_map[ei] = {
                                "label": label, "reason": str(item.get("reason", ""))[:500]
                            }
                    if len(evidence_map) == len(evidence_items):
                        by_claim[ci] = evidence_map
                if len(by_claim) != len(claims):
                    raise ValueError(
                        f"Se validaron {len(by_claim)}/{len(claims)} afirmaciones del lote."
                    )
                diagnostics.append(diagnostic)
                return {
                    "claims": by_claim,
                    "diagnostics": diagnostics,
                    "terminology_terms_used": {
                        i: [x["id"] for x in claim_rows[i]["terminology"]]
                        for i in range(len(claims))
                    },
                }
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                diagnostic["validation_error"] = last_error
                diagnostics.append(diagnostic)
        error = RuntimeError(f"Qwen produjo una salida inválida para el lote. {last_error}")
        error.diagnostics = diagnostics
        raise error

    def verify_claims(
        self,
        claims: list[str],
        rag_results: list[dict[str, Any]] | None = None,
        web_results: list[dict[str, Any]] | None = None,
        max_evidence_per_claim: int = 10,
    ) -> dict[str, Any]:
        """Verifica afirmaciones con adjudicación semántica local.

        NLI se conserva como señal diagnóstica, pero no decide por sí solo.
        Si Ollama no está disponible o devuelve una salida inválida, el resultado
        es INSUFFICIENT (fail-closed), nunca una aceptación automática por NLI.
        """
        if not isinstance(claims, list) or not claims:
            raise EvidenceVerifierError("'claims' debe ser una lista no vacía.")
        if not isinstance(max_evidence_per_claim, int) or max_evidence_per_claim < 1:
            raise EvidenceVerifierError("max_evidence_per_claim debe ser >= 1.")
        for i, claim in enumerate(claims):
            if not isinstance(claim, str) or not claim.strip():
                raise EvidenceVerifierError(f"claims[{i}] debe ser texto no vacío.")

        rag = self._validar_lista("rag_results", rag_results)
        web = self._validar_lista("web_results", web_results)
        evidence = []

        for i, item in enumerate(rag):
            if not isinstance(item.get("text"), str) or not item["text"].strip():
                raise EvidenceVerifierError(f"rag_results[{i}] requiere 'text'.")
            evidence.append({
                "evidence_type": "RAG",
                "source": item.get("source", ""),
                "text": item["text"].strip(),
            })

        for i, item in enumerate(web):
            title, description = item.get("title"), item.get("description")
            if not isinstance(title, str) or not isinstance(description, str):
                raise EvidenceVerifierError(
                    f"web_results[{i}] requiere 'title' y 'description' de texto."
                )
            snippet = " — ".join(x.strip() for x in (title, description) if x.strip())
            if snippet:
                evidence.append({
                    "evidence_type": "DDGS_SNIPPET",
                    "source": item.get("url", ""),
                    "text": snippet,
                })

        selected = evidence[:max_evidence_per_claim]
        if not selected:
            return {
                "model": self.nli_model_name,
                "adjudication_model": self.adjudication_model,
                "device": self.device,
                "claims": [
                    {"claim": c.strip(), "status": "INSUFFICIENT", "comparisons": []}
                    for c in claims
                ],
                "overall_status": "INSUFFICIENT",
                "limitations": ["No se recibieron fragmentos de evidencia."],
            }

        # NLI scores are retained for diagnostics only, not as final decisions.
        self._load_nli_model()
        import torch

        pairs, mapping = [], []
        for ci, claim in enumerate(claims):
            for ei, item in enumerate(selected):
                pairs.append((item["text"], claim.strip()))
                mapping.append((ci, ei, item))

        all_scores = []
        batch_size = 8
        for start_batch in range(0, len(pairs), batch_size):
            batch = pairs[start_batch:start_batch + batch_size]
            encoded = self._tokenizer(
                [x[0] for x in batch],
                [x[1] for x in batch],
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            encoded = {k: v.to(self.device) for k, v in encoded.items()}
            with torch.inference_mode():
                logits = self._nli_model(**encoded).logits
                all_scores.extend(torch.softmax(logits, dim=-1).detach().cpu().tolist())

        grouped = {i: [] for i in range(len(claims))}
        for (ci, ei, item), scores in zip(mapping, all_scores):
            idx = self._label_indices
            grouped[ci].append({
                "evidence_id": ei,
                "evidence_type": item["evidence_type"],
                "source": item["source"],
                "role_mismatch": self._role_mismatch(item["text"], claims[ci]),
                "scores": {
                    "entailment": float(scores[idx["entailment"]]),
                    "neutral": float(scores[idx["neutral"]]),
                    "contradiction": float(scores[idx["contradiction"]]),
                },
                "text": item["text"],
            })

        reports = []
        judge_errors = []
        # Experimento: dos afirmaciones por llamada. Mantiene el mismo conjunto
        # de evidencias y el mismo criterio fail-closed del verificador original.
        adjudication_batch_size = 2
        for batch_start in range(0, len(claims), adjudication_batch_size):
            batch_claims = claims[batch_start:batch_start + adjudication_batch_size]
            try:
                batch_result = self._ollama_adjudicate_batch(batch_claims, selected) \
                    if self.use_ollama_adjudication else None
                batch_ok = batch_result is not None
                batch_diagnostics = batch_result.get("diagnostics", []) if batch_result else []
                batch_items = batch_result.get("claims", {}) if batch_result else {}
                batch_terms = batch_result.get("terminology_terms_used", {}) if batch_result else {}
                batch_error = None
            except Exception as exc:
                batch_ok = False
                batch_items = {}
                batch_terms = {}
                batch_error = f"{type(exc).__name__}: {exc}"
                batch_diagnostics = getattr(exc, "diagnostics", [])
                judge_errors.append({
                    "claims": [c.strip() for c in batch_claims],
                    "error": batch_error,
                    "diagnostics": batch_diagnostics,
                })

            for local_ci, claim in enumerate(batch_claims):
                ci = batch_start + local_ci
                comparisons = grouped[ci]
                judge_items = batch_items.get(local_ci, {}) if batch_ok else {}
                judge_ok = batch_ok and len(judge_items) == len(selected)
                judge_error = None if judge_ok else (batch_error or "Adjudicación de lote incompleta.")
                for comparison in comparisons:
                    decision = judge_items.get(comparison["evidence_id"])
                    comparison["adjudication"] = decision or {
                        "label": "UNAVAILABLE",
                        "reason": "No se obtuvo una decisión semántica válida.",
                    }
                labels = [x["label"] for x in judge_items.values()]
                has_support = "SUPPORTED" in labels
                has_contradiction = "CONTRADICTED" in labels
                if not judge_ok:
                    status = "INSUFFICIENT"
                elif has_support and has_contradiction:
                    status = "CONFLICTING_EVIDENCE"
                elif has_support:
                    status = "SUPPORTED"
                elif has_contradiction:
                    status = "CONTRADICTED"
                else:
                    status = "INSUFFICIENT"
                reports.append({
                    "claim": claim.strip(),
                    "status": status,
                    "adjudication_available": judge_ok,
                    "adjudication_error": judge_error,
                    "adjudication_diagnostics": batch_diagnostics,
                    "terminology_terms_used": batch_terms.get(local_ci, []) if judge_ok else [],
                    "best_entailment_score": max(
                        (x["scores"]["entailment"] for x in comparisons), default=0.0
                    ),
                    "best_contradiction_score": max(
                        (x["scores"]["contradiction"] for x in comparisons), default=0.0
                    ),
                    "comparisons": comparisons,
                })

        statuses = [x["status"] for x in reports]
        if "CONFLICTING_EVIDENCE" in statuses:
            overall = "CONFLICTING_EVIDENCE"
        elif all(x == "SUPPORTED" for x in statuses):
            overall = "SUPPORTED"
        elif "SUPPORTED" in statuses and "CONTRADICTED" not in statuses:
            overall = "PARTIALLY_SUPPORTED"
        elif "SUPPORTED" in statuses and "CONTRADICTED" in statuses:
            overall = "MIXED_EVIDENCE"
        elif "CONTRADICTED" in statuses:
            overall = "CONTRADICTED"
        else:
            overall = "INSUFFICIENT"

        return {
            "model": self.nli_model_name,
            "adjudication_model": self.adjudication_model,
            "adjudication_provider": "Ollama",
            "adjudication_enabled": self.use_ollama_adjudication,
            "adjudication_errors": judge_errors,
            "device": self.device,
            "thresholds": {
                "entailment": self.entailment_threshold,
                "contradiction": self.contradiction_threshold,
                "decision_margin": self.decision_margin,
                "note": "Se conservan por compatibilidad/diagnóstico; no gobiernan la decisión final.",
            },
            "claims": reports,
            "overall_status": overall,
            "limitations": [
                "La decisión semántica final la realiza Qwen local sobre los textos originales.",
                "NLI se conserva como señal diagnóstica y no puede aceptar por sí solo una afirmación.",
                "Si Ollama falla, se adopta INSUFFICIENT por seguridad (fail-closed).",
                "La clasificación de un LLM no constituye certificación científica.",
                "DDGS se evalúa solo con title + description, no con el artículo completo.",
                "Las afirmaciones deben ser atómicas y suministradas explícitamente.",
                "La contradicción exige incompatibilidad directa sobre la misma proposición; la falta de mención no es contradicción.",
                "La selección de evidencia se limita a los primeros elementos recibidos.",
            ],
        }


    @staticmethod
    def _normalizar_url(url: str) -> str:
        """
        Normaliza una URL para comparar referencias.
        Conserva ruta, consulta y fragmento; normaliza esquema/host.
        No intenta resolver redirecciones ni equivalencias entre URLs.
        """
        try:
            parsed = urlsplit(url.strip().rstrip(".,;:!?"))
            if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
                return ""

            host = parsed.hostname.lower().rstrip(".")
            port = parsed.port
            netloc = host
            if port is not None and not (
                (parsed.scheme.lower() == "http" and port == 80)
                or (parsed.scheme.lower() == "https" and port == 443)
            ):
                netloc = f"{host}:{port}"

            path = parsed.path or "/"
            return urlunsplit(
                (parsed.scheme.lower(), netloc, path, parsed.query, parsed.fragment)
            )
        except (TypeError, ValueError):
            return ""

    @staticmethod
    def _validar_lista(nombre: str, elementos: Any) -> list[dict[str, Any]]:
        if elementos is None:
            return []
        if not isinstance(elementos, list):
            raise EvidenceVerifierError(f"'{nombre}' debe ser una lista.")

        salida: list[dict[str, Any]] = []
        for indice, item in enumerate(elementos):
            if not isinstance(item, dict):
                raise EvidenceVerifierError(
                    f"El elemento {indice} de '{nombre}' debe ser un diccionario."
                )
            salida.append(item)
        return salida

    @staticmethod
    def _extraer_urls(texto: str) -> list[str]:
        return [
            coincidencia.rstrip(".,;:!?")
            for coincidencia in EvidenceVerifier.URL_PATTERN.findall(texto)
        ]

    def verify(
        self,
        response: str,
        rag_results: list[dict[str, Any]] | None = None,
        web_results: list[dict[str, Any]] | None = None,
        claims: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Verifica referencias explícitas y, opcionalmente, afirmaciones atómicas.

        Parámetros:
            response: texto generado por el LLM.
            rag_results: resultados originales de retriever.search().
            web_results: resultados originales de WebSearch.

        Devuelve un informe JSON-serializable.
        """
        if not isinstance(response, str):
            raise EvidenceVerifierError("'response' debe ser un texto.")

        rag = self._validar_lista("rag_results", rag_results)
        web = self._validar_lista("web_results", web_results)

        # Recolectar rutas locales realmente entregadas por el RAG.
        rag_sources: list[str] = []
        for indice, item in enumerate(rag):
            source = item.get("source")
            text = item.get("text")
            if not isinstance(source, str) or not source.strip():
                raise EvidenceVerifierError(
                    f"rag_results[{indice}] no contiene un 'source' válido."
                )
            if not isinstance(text, str):
                raise EvidenceVerifierError(
                    f"rag_results[{indice}] no contiene un 'text' válido."
                )
            rag_sources.append(source.strip())

        # Recolectar URLs web realmente entregadas por DDGS.
        web_records: list[dict[str, str]] = []
        for indice, item in enumerate(web):
            title = item.get("title")
            url = item.get("url")
            description = item.get("description")
            source = item.get("source")

            if not isinstance(url, str) or not self._normalizar_url(url):
                raise EvidenceVerifierError(
                    f"web_results[{indice}] no contiene una URL HTTP(S) válida."
                )
            if not isinstance(title, str):
                raise EvidenceVerifierError(
                    f"web_results[{indice}] no contiene un 'title' válido."
                )
            if not isinstance(description, str):
                raise EvidenceVerifierError(
                    f"web_results[{indice}] no contiene una 'description' válida."
                )
            if not isinstance(source, str):
                raise EvidenceVerifierError(
                    f"web_results[{indice}] no contiene un 'source' válido."
                )

            web_records.append(
                {
                    "title": title,
                    "url": url,
                    "normalized_url": self._normalizar_url(url),
                    "description": description,
                    "source": source,
                }
            )

        # Detección de URLs duplicadas en el conjunto recuperado.
        url_counts = Counter(record["normalized_url"] for record in web_records)
        duplicate_urls = sorted(
            url for url, count in url_counts.items() if count > 1
        )

        # Comparación de URLs explícitas en la respuesta contra DDGS.
        response_urls = self._extraer_urls(response)
        normalized_available_urls = {
            record["normalized_url"] for record in web_records
        }

        matched_urls: list[str] = []
        unmatched_urls: list[str] = []
        seen_response_urls: set[str] = set()

        for url in response_urls:
            normalized = self._normalizar_url(url)
            if not normalized:
                unmatched_urls.append(url)
                continue
            if normalized in seen_response_urls:
                continue
            seen_response_urls.add(normalized)

            if normalized in normalized_available_urls:
                matched_urls.append(url)
            else:
                unmatched_urls.append(url)

        # Detectar menciones literales de rutas RAG recuperadas y no recuperadas.
        matched_rag_sources = [
            source for source in dict.fromkeys(rag_sources) if source in response
        ]

        # No se puede inferir con seguridad que una cadena parecida a una ruta
        # sea una cita. Solo se informa la coincidencia literal de fuentes RAG.
        semantic_report = (
            self.verify_claims(claims, rag_results=rag, web_results=web)
            if claims is not None else None
        )

        report = {
            "verifier": "EvidenceVerifier",
            "version": self.VERSION,
            "checks": {
                "web_url_reference_check": {
                    "status": (
                        "PASS" if not unmatched_urls else "UNVERIFIED"
                    ),
                    "urls_found_in_response": response_urls,
                    "urls_matched_to_search_results": matched_urls,
                    "urls_not_found_in_search_results": unmatched_urls,
                },
                "rag_source_reference_check": {
                    "status": (
                        "PASS"
                        if not rag_sources or matched_rag_sources
                        else "NOT_CITED"
                    ),
                    "retrieved_sources": list(dict.fromkeys(rag_sources)),
                    "sources_mentioned_literally": matched_rag_sources,
                },
                "duplicate_web_reference_check": {
                    "status": "WARNING" if duplicate_urls else "PASS",
                    "duplicate_urls": duplicate_urls,
                },
                "semantic_support_check": (
                    semantic_report if semantic_report is not None else {
                        "status": "NOT_PERFORMED",
                        "reason": (
                            "No se proporcionaron afirmaciones atómicas. "
                            "La extracción automática no forma parte del verificador."
                        ),
                    }
                ),
            },
            "evidence_counts": {
                "rag_fragments": len(rag),
                "rag_unique_sources": len(set(rag_sources)),
                "web_results": len(web_records),
                "web_unique_urls": len(normalized_available_urls),
            },
            "overall_status": self._overall_status(
                unmatched_urls=unmatched_urls,
                duplicate_urls=duplicate_urls,
                rag_sources=rag_sources,
                matched_rag_sources=matched_rag_sources,
            ),
            "limitations": [
                "La coincidencia de una URL solo confirma que fue recuperada por DDGS.",
                "DDGS aporta título, URL y fragmento; este módulo no descarga la página.",
                "La coincidencia de una ruta RAG no demuestra que respalde la afirmación.",
                "No se realiza verificación semántica ni comprobación científica.",
                "La ausencia de una cita no demuestra por sí sola que una afirmación sea falsa.",
            ],
        }
        return report

    @staticmethod
    def _overall_status(
        unmatched_urls: list[str],
        duplicate_urls: list[str],
        rag_sources: list[str],
        matched_rag_sources: list[str],
    ) -> str:
        if unmatched_urls:
            return "UNVERIFIED_REFERENCES"
        if duplicate_urls:
            return "WARNING_DUPLICATE_REFERENCES"
        if rag_sources and not matched_rag_sources:
            return "RAG_SOURCES_NOT_CITED"
        return "REFERENCE_CHECKS_PASSED"


def verify_response(
    response: str,
    rag_results: list[dict[str, Any]] | None = None,
    web_results: list[dict[str, Any]] | None = None,
    claims: list[str] | None = None,
) -> dict[str, Any]:
    """Función de conveniencia para ejecutar una verificación."""
    return EvidenceVerifier().verify(
        response=response,
        rag_results=rag_results,
        web_results=web_results,
        claims=claims,
    )


if __name__ == "__main__":
    # Prueba autocontenida con datos sintéticos.
    # No consulta Internet, Ollama ni la base documental real.
    rag_demo = [
        {
            "source": "Fundamentos_de_SAC_GIAR_ORION.md",
            "text": "SAC es un algoritmo de aprendizaje por refuerzo off-policy.",
            "score": 0.82,
            "mode": "hybrid",
        }
    ]

    web_demo = [
        {
            "title": "Soft Actor-Critic",
            "url": "https://spinningup.openai.com/en/latest/algorithms/sac.html",
            "description": "Documentación de referencia sobre Soft Actor-Critic.",
            "source": "spinningup.openai.com",
        }
    ]

    response_demo = (
        "Según Fundamentos_de_SAC_GIAR_ORION.md, SAC es off-policy. "
        "Referencia: https://spinningup.openai.com/en/latest/algorithms/sac.html"
    )

    resultado = verify_response(
        response=response_demo,
        rag_results=rag_demo,
        web_results=web_demo,
    )

    import json

    print(json.dumps(resultado, ensure_ascii=False, indent=2))
