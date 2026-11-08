"""
EvidenceVerifier.py
===================

Módulo independiente de verificación de evidencias para GIAR-ORION.

Versión: 0.3.0

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

Limitación deliberada
---------------------
Esta versión NO determina si el contenido de una evidencia demuestra
semánticamente una afirmación. Tampoco descarga páginas web ni consulta
modelos externos. Por lo tanto, una referencia coincidente no equivale a
una afirmación científicamente verificada.

El módulo no modifica RAG, DDGS, Ollama ni la interfaz de GIAR-ORION.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any
from urllib.parse import urlsplit, urlunsplit


class EvidenceVerifierError(ValueError):
    """Error en los datos recibidos por el verificador."""


class EvidenceVerifier:
    """Realiza controles deterministas sobre referencias y evidencias."""

    VERSION = "0.3.0"

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
        """Clasifica todas las evidencias de una afirmación en una llamada local.

        Regla conservadora:
        - SUPPORTED exige respaldo directo del contenido.
        - CONTRADICTED exige incompatibilidad directa sobre la misma proposición.
        - Si solo habla de otro aspecto/componente, es INSUFFICIENT.
        """
        import json
        import urllib.request

        numbered = [
            {"id": i, "source": str(item.get("source", "")), "text": item["text"]}
            for i, item in enumerate(evidence_items)
        ]
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
            "Return valid JSON only, with this exact shape: "
            '{"items":[{"id":0,"label":"SUPPORTED","reason":"short reason"}]}. '
            "Include every id exactly once. Reasons must be short and in Spanish.\n\n"
            f"CLAIM:\n{claim}\n\nEVIDENCE ITEMS:\n"
            f"{json.dumps(numbered, ensure_ascii=False)}"
        )
        payload = {
            "model": self.adjudication_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0, "num_predict": 700},
        }
        request = urllib.request.Request(
            f"{self.ollama_url}/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.adjudication_timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        raw = body.get("message", {}).get("content", "")
        parsed = json.loads(raw)
        rows = parsed.get("items") if isinstance(parsed, dict) else None
        if not isinstance(rows, list):
            raise ValueError("Qwen no devolvió el arreglo JSON 'items'.")

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
            }:
                continue
            by_id[idx] = {
                "label": label,
                "reason": str(row.get("reason", ""))[:500],
            }
        if len(by_id) != len(evidence_items):
            raise ValueError(
                f"Qwen devolvió {len(by_id)} clasificaciones válidas de "
                f"{len(evidence_items)} evidencias."
            )
        return {"items": by_id, "model": self.adjudication_model}

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
        for ci, claim in enumerate(claims):
            comparisons = grouped[ci]
            try:
                adjudication = self._ollama_adjudicate(claim.strip(), selected) \
                    if self.use_ollama_adjudication else None
                judge_items = adjudication["items"] if adjudication else {}
                judge_ok = adjudication is not None
                judge_error = None
            except Exception as exc:
                judge_items = {}
                judge_ok = False
                judge_error = f"{type(exc).__name__}: {exc}"
                judge_errors.append({"claim": claim.strip(), "error": judge_error})

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
