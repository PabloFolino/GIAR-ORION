"""
MultilingualKnowledgeRetriever.py

Recuperador semántico independiente para GIAR-ORION.
- E5: intfloat/multilingual-e5-base (sentence-transformers)
- BGE-M3: BAAI/bge-m3 (FlagEmbedding)
- Hybrid: combina similitudes densas de ambos modelos con pesos configurables.

No modifica main.py ni KnowledgeRetriever_experimento.py.
Los modelos se descargan la primera vez y luego pueden utilizarse offline
si sus archivos permanecen en la caché local.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


DEFAULT_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "Knowledge"
E5_MODEL_NAME = "intfloat/multilingual-e5-base"
BGE_MODEL_NAME = "BAAI/bge-m3"


@dataclass
class KnowledgeChunk:
    source: str
    text: str
    embedding_e5: np.ndarray | None = None
    embedding_bge: np.ndarray | None = None


class MultilingualKnowledgeRetriever:
    """Busca fragmentos de Markdown por similitud semántica."""

    def __init__(
        self,
        knowledge_dir: str | Path = DEFAULT_KNOWLEDGE_DIR,
        mode: str = "e5",
        device: str | None = None,
        e5_weight: float = 0.5,
        bge_weight: float = 0.5,
        chunk_chars: int = 1100,
        overlap_chars: int = 150,
        batch_size: int = 16,
        local_files_only: bool = False,
    ) -> None:
        mode = mode.lower().strip()
        if mode not in {"e5", "bge-m3", "hybrid"}:
            raise ValueError("mode debe ser 'e5', 'bge-m3' o 'hybrid'.")
        if e5_weight < 0 or bge_weight < 0 or (e5_weight + bge_weight) <= 0:
            raise ValueError("Los pesos deben ser no negativos y sumar más que cero.")
        if chunk_chars < 200:
            raise ValueError("chunk_chars debe ser al menos 200.")
        if overlap_chars < 0 or overlap_chars >= chunk_chars:
            raise ValueError("overlap_chars debe estar entre 0 y chunk_chars - 1.")

        self.knowledge_dir = Path(knowledge_dir).resolve()
        self.mode = mode
        self.e5_weight = e5_weight
        self.bge_weight = bge_weight
        self.chunk_chars = chunk_chars
        self.overlap_chars = overlap_chars
        self.batch_size = batch_size
        self.local_files_only = local_files_only

        if device is None:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        self.chunks = self._load_chunks()
        if not self.chunks:
            raise FileNotFoundError(
                f"No se encontraron fragmentos Markdown en: {self.knowledge_dir}"
            )

        self._e5_model: Any = None
        self._bge_model: Any = None

        if self.mode in {"e5", "hybrid"}:
            self._load_e5()
            self._embed_e5_corpus()

        if self.mode in {"bge-m3", "hybrid"}:
            self._load_bge()
            self._embed_bge_corpus()

    def _load_chunks(self) -> list[KnowledgeChunk]:
        if not self.knowledge_dir.exists():
            raise FileNotFoundError(f"No existe el directorio: {self.knowledge_dir}")

        chunks: list[KnowledgeChunk] = []
        for path in sorted(self.knowledge_dir.rglob("*.md")):
            try:
                text = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError):
                continue

            # Conserva el título más reciente como contexto del fragmento.
            section = ""
            paragraphs: list[str] = []
            for block in re.split(r"\n\s*\n", text):
                block = block.strip()
                if not block:
                    continue
                if block.startswith("#"):
                    section = re.sub(r"^#+\s*", "", block).strip()
                    continue
                combined = f"{section}\n{block}".strip() if section else block
                paragraphs.append(combined)

            for paragraph in paragraphs:
                for piece in self._split_text(paragraph):
                    if len(piece.strip()) >= 25:
                        chunks.append(
                            KnowledgeChunk(
                                source=str(path.relative_to(self.knowledge_dir)),
                                text=piece.strip(),
                            )
                        )
        return chunks

    def _split_text(self, text: str) -> list[str]:
        text = re.sub(r"[ \t]+", " ", text).strip()
        if len(text) <= self.chunk_chars:
            return [text]

        pieces: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_chars, len(text))
            if end < len(text):
                boundary = max(
                    text.rfind(". ", start, end),
                    text.rfind("; ", start, end),
                    text.rfind(" ", start, end),
                )
                if boundary > start + self.chunk_chars // 2:
                    end = boundary + 1
            pieces.append(text[start:end].strip())
            if end >= len(text):
                break
            start = max(end - self.overlap_chars, start + 1)
        return pieces

    def _load_e5(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Falta sentence-transformers. Instalalo en el entorno virtual activo."
            ) from exc

        kwargs: dict[str, Any] = {"device": self.device}
        if self.local_files_only:
            os.environ["HF_HUB_OFFLINE"] = "1"
            kwargs["local_files_only"] = True
        self._e5_model = SentenceTransformer(E5_MODEL_NAME, **kwargs)

    def _load_bge(self) -> None:
        try:
            from FlagEmbedding import BGEM3FlagModel
        except ImportError as exc:
            raise RuntimeError(
                "Para BGE-M3 hace falta FlagEmbedding. Instalá y verificá esa "
                "dependencia antes de usar mode='bge-m3' o mode='hybrid'."
            ) from exc

        if self.local_files_only:
            os.environ["HF_HUB_OFFLINE"] = "1"
        self._bge_model = BGEM3FlagModel(
            BGE_MODEL_NAME,
            use_fp16=(self.device == "cuda"),
            devices=self.device,
        )

    def _embed_e5_corpus(self) -> None:
        texts = ["passage: " + chunk.text for chunk in self.chunks]
        vectors = self._e5_model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        for chunk, vector in zip(self.chunks, vectors):
            chunk.embedding_e5 = np.asarray(vector, dtype=np.float32)

    def _embed_bge_corpus(self) -> None:
        texts = [chunk.text for chunk in self.chunks]
        result = self._bge_model.encode(
            texts,
            batch_size=self.batch_size,
            max_length=8192,
        )
        vectors = np.asarray(result["dense_vecs"], dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / np.maximum(norms, 1e-12)
        for chunk, vector in zip(self.chunks, vectors):
            chunk.embedding_bge = vector

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Devuelve resultados ordenados por similitud descendente."""
        query = query.strip()
        if not query:
            return []
        if top_k < 1:
            raise ValueError("top_k debe ser mayor o igual a 1.")

        scores = np.zeros(len(self.chunks), dtype=np.float32)

        if self.mode in {"e5", "hybrid"}:
            query_vector = self._e5_model.encode(
                ["query: " + query],
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )[0]
            matrix = np.vstack([c.embedding_e5 for c in self.chunks])
            e5_scores = matrix @ np.asarray(query_vector, dtype=np.float32)
            if self.mode == "e5":
                scores = e5_scores
            else:
                scores += self.e5_weight * e5_scores

        if self.mode in {"bge-m3", "hybrid"}:
            result = self._bge_model.encode([query], max_length=8192)
            query_vector = np.asarray(result["dense_vecs"][0], dtype=np.float32)
            query_vector /= max(float(np.linalg.norm(query_vector)), 1e-12)
            matrix = np.vstack([c.embedding_bge for c in self.chunks])
            bge_scores = matrix @ query_vector
            if self.mode == "bge-m3":
                scores = bge_scores
            else:
                scores += self.bge_weight * bge_scores

        order = np.argsort(scores)[::-1][:top_k]
        return [
            {
                "source": self.chunks[int(i)].source,
                "text": self.chunks[int(i)].text,
                "score": float(scores[int(i)]),
                "mode": self.mode,
            }
            for i in order
        ]

    def close(self) -> None:
        """Libera referencias a los modelos para permitir liberar memoria."""
        self._e5_model = None
        self._bge_model = None
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Prueba independiente del recuperador multilingüe de GIAR-ORION."
    )
    parser.add_argument("query", nargs="*", help="Consulta de búsqueda")
    parser.add_argument("--mode", choices=["e5", "bge-m3", "hybrid"], default="e5")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--knowledge-dir", default=str(DEFAULT_KNOWLEDGE_DIR))
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    query = " ".join(args.query).strip()
    if not query:
        query = input("Consulta: ").strip()

    retriever = MultilingualKnowledgeRetriever(
        knowledge_dir=args.knowledge_dir,
        mode=args.mode,
        local_files_only=args.offline,
    )
    try:
        for rank, item in enumerate(retriever.search(query, top_k=args.top_k), 1):
            print(f"\n{rank}. {item['source']}  score={item['score']:.4f}")
            print(item["text"])
    finally:
        retriever.close()
