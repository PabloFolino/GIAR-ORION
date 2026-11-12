"""
ClaimVerificationPipeline.py
Orquesta ClaimExtractor y EvidenceVerifier sin modificar esos componentes.
"""

from __future__ import annotations
from typing import Any, Optional


class ClaimVerificationPipelineError(RuntimeError):
    """Error de configuración o inicialización del pipeline."""


class ClaimVerificationPipeline:
    VERSION = "0.1.0"
    NO_FACTUAL_CLAIMS = "NO_FACTUAL_CLAIMS"
    EXTRACTION_INCOMPLETE = "EXTRACTION_INCOMPLETE"
    EXTRACTION_ERROR = "EXTRACTION_ERROR"
    VERIFICATION_ERROR = "VERIFICATION_ERROR"
    SEMANTIC_VERIFICATION_NOT_PERFORMED = "SEMANTIC_VERIFICATION_NOT_PERFORMED"

    def __init__(
        self,
        claim_extractor: Any = None,
        evidence_verifier: Any = None,
        *,
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "qwen3:8b",
        extractor_options: Optional[dict] = None,
        verifier_options: Optional[dict] = None,
    ) -> None:
        """Acepta componentes reales o mocks para pruebas independientes."""
        try:
            if claim_extractor is None:
                from Agent.ClaimExtractor import ClaimExtractor
                options = dict(extractor_options or {})
                options.setdefault("base_url", ollama_base_url)
                options.setdefault("model", ollama_model)
                claim_extractor = ClaimExtractor(**options)

            if evidence_verifier is None:
                from Agent.EvidenceVerifier import EvidenceVerifier
                evidence_verifier = EvidenceVerifier(**dict(verifier_options or {}))
        except Exception as exc:
            raise ClaimVerificationPipelineError(
                f"No se pudieron inicializar los componentes: {exc}"
            ) from exc

        self.claim_extractor = claim_extractor
        self.evidence_verifier = evidence_verifier

    @staticmethod
    def _version(component: Any) -> Optional[str]:
        return getattr(component, "VERSION", None)

    @staticmethod
    def _reference_status(verification: Any) -> Optional[str]:
        return verification.get("overall_status") if isinstance(verification, dict) else None

    @staticmethod
    def _semantic_report(verification: Any) -> Optional[dict]:
        if not isinstance(verification, dict):
            return None
        checks = verification.get("checks")
        if not isinstance(checks, dict):
            return None
        report = checks.get("semantic_support_check")
        return report if isinstance(report, dict) else None

    @staticmethod
    def _extract_claim_texts(extraction: dict) -> list[str]:
        raw_claims = extraction.get("claims")
        if not isinstance(raw_claims, list):
            raise ValueError("El campo 'claims' de ClaimExtractor no es una lista.")

        texts = []
        for index, item in enumerate(raw_claims):
            if not isinstance(item, dict):
                raise ValueError(f"La afirmación {index} no tiene el formato esperado.")
            claim = item.get("claim")
            if not isinstance(claim, str) or not claim.strip():
                raise ValueError(f"La afirmación {index} no contiene un campo 'claim' válido.")
            texts.append(claim.strip())
        return texts

    def run(
        self,
        response: str,
        rag_results: Optional[list] = None,
        web_results: Optional[list] = None,
        think: Optional[bool] = None,
    ) -> dict:
        """
        Ejecuta extracción y verificación.
        complete=True indica cobertura estructural, no exhaustividad semántica.
        SUPPORTED no constituye certificación científica.
        """
        if not isinstance(response, str) or not response.strip():
            raise ValueError("'response' debe ser un string no vacío.")
        if think is not None and not isinstance(think, bool):
            raise ValueError("'think' debe ser booleano o None.")
        if think is not None:
            # El modo puede cambiar durante la sesión (/modo rapido / investigacion).
            # Se actualiza la instancia ya creada, sin reinicializar modelos.
            if not hasattr(self.evidence_verifier, "think"):
                raise ClaimVerificationPipelineError(
                    "El EvidenceVerifier configurado no admite el parámetro think."
                )
            self.evidence_verifier.think = think

        result = {
            "pipeline": "ClaimVerificationPipeline",
            "pipeline_version": self.VERSION,
            "status": None,
            "can_present_as_supported": False,
            "claims_submitted": 0,
            "adjudication_think": getattr(self.evidence_verifier, "think", None),
            "extractor_version": self._version(self.claim_extractor),
            "verifier_version": self._version(self.evidence_verifier),
            "extraction": None,
            "verification": None,
            "reference_status": None,
            "semantic_status": None,
            "limitations": [
                "La cobertura estructural del extractor no demuestra exhaustividad semántica.",
                "Los puntajes NLI no son probabilidades calibradas.",
                "El respaldo semántico no equivale a una verificación científica definitiva.",
                "Los resultados DDGS contienen título y fragmento; no necesariamente el contenido completo de la página.",
            ],
        }

        # 1. Extracción de afirmaciones.
        try:
            extraction = self.claim_extractor.extract(response)
            result["extraction"] = extraction
        except Exception as exc:
            result["status"] = self.EXTRACTION_ERROR
            result["error"] = f"{type(exc).__name__}: {exc}"
            return result

        if not isinstance(extraction, dict):
            result["status"] = self.EXTRACTION_ERROR
            result["error"] = "ClaimExtractor no devolvió un diccionario."
            return result

        if extraction.get("complete") is not True:
            result["status"] = self.EXTRACTION_INCOMPLETE
            result["extraction_errors"] = extraction.get("errors", [])
            result["limitations"].append(
                "La extracción no alcanzó cobertura estructural completa; se detuvo la verificación semántica."
            )
            return result

        try:
            claim_texts = self._extract_claim_texts(extraction)
        except Exception as exc:
            result["status"] = self.EXTRACTION_ERROR
            result["error"] = f"{type(exc).__name__}: {exc}"
            return result

        result["claims_submitted"] = len(claim_texts)

        # 2. Caso sin afirmaciones: no pasar claims=[] al EvidenceVerifier.
        if not claim_texts:
            try:
                verification = self.evidence_verifier.verify(
                    response,
                    rag_results=rag_results,
                    web_results=web_results,
                    claims=None,
                )
                result["verification"] = verification
                result["reference_status"] = self._reference_status(verification)
            except Exception as exc:
                result["status"] = self.VERIFICATION_ERROR
                result["error"] = f"{type(exc).__name__}: {exc}"
                return result

            result["status"] = self.NO_FACTUAL_CLAIMS
            result["semantic_status"] = "NOT_PERFORMED"
            result["limitations"].append(
                "No se detectaron afirmaciones factuales; no se realizó verificación semántica."
            )
            return result

        # 3. Verificación semántica.
        try:
            verification = self.evidence_verifier.verify(
                response,
                rag_results=rag_results,
                web_results=web_results,
                claims=claim_texts,
            )
            result["verification"] = verification
            result["reference_status"] = self._reference_status(verification)
        except Exception as exc:
            result["status"] = self.VERIFICATION_ERROR
            result["error"] = f"{type(exc).__name__}: {exc}"
            return result

        semantic_report = self._semantic_report(verification)
        if semantic_report is None:
            result["status"] = self.SEMANTIC_VERIFICATION_NOT_PERFORMED
            result["semantic_status"] = "NOT_PERFORMED"
            result["limitations"].append(
                "El verificador no devolvió el informe de respaldo semántico esperado."
            )
            return result

        semantic_status = semantic_report.get("overall_status")
        result["semantic_status"] = semantic_status
        accepted = {
            "SUPPORTED", "PARTIALLY_SUPPORTED", "MIXED_EVIDENCE",
            "CONTRADICTED", "INSUFFICIENT", "CONFLICTING_EVIDENCE",
        }
        if semantic_status not in accepted:
            result["status"] = self.SEMANTIC_VERIFICATION_NOT_PERFORMED
            result["limitations"].append(
                f"Estado semántico ausente o no reconocido: {semantic_status!r}."
            )
            return result

        # El estado principal procede del análisis semántico, no del estado
        # global de referencias del EvidenceVerifier.
        result["status"] = semantic_status
        result["can_present_as_supported"] = semantic_status == "SUPPORTED"
        return result

    def verify(self, response: str, rag_results: Optional[list] = None,
               web_results: Optional[list] = None,
               think: Optional[bool] = None) -> dict:
        """Alias de run()."""
        return self.run(
            response, rag_results=rag_results, web_results=web_results, think=think
        )


def run_pipeline(response: str, rag_results: Optional[list] = None,
                 web_results: Optional[list] = None, **pipeline_options: Any) -> dict:
    """Atajo funcional para crear y ejecutar el pipeline."""
    pipeline = ClaimVerificationPipeline(**pipeline_options)
    return pipeline.run(response, rag_results=rag_results, web_results=web_results)
