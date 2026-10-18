"""
Experimento independiente de ponderación E5 + BGE-M3 para GIAR-ORION.

No modifica main.py ni los recuperadores existentes.
Ejecutar desde la raíz de GIAR-ORION:
    python Tests\test_hybrid_weights.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
AGENT_DIR = ROOT_DIR / "Agent"
sys.path.insert(0, str(AGENT_DIR))

from MultilingualKnowledgeRetriever import MultilingualKnowledgeRetriever  # noqa: E402


QUERIES = [
    "¿Qué sensores están asociados a imu_in_torso? Indicar nombre, tipo, ruido y frecuencia de corte.",
    "¿Qué función cumple el Replay Buffer en SAC?",
    "¿Cómo se calcula la actualización de los críticos en Soft Actor-Critic?",
    "¿Qué articulaciones forman parte de la cintura del Unitree G1?",
]

WEIGHT_CONFIGS = [
    ("E5 70% / BGE-M3 30%", 0.7, 0.3),
    ("E5 50% / BGE-M3 50%", 0.5, 0.5),
    ("E5 30% / BGE-M3 70%", 0.3, 0.7),
]

TOP_K = 5


def main() -> int:
    knowledge_dir = ROOT_DIR / "Knowledge"
    print("=" * 76)
    print("GIAR-ORION | Experimento independiente de pesos E5 + BGE-M3")
    print("=" * 76)
    print(f"Base de conocimiento: {knowledge_dir}")
    print(f"Consultas: {len(QUERIES)} | Top-K: {TOP_K}")
    print("Se cargan/indexan ambos modelos una sola vez.\n")

    retriever = MultilingualKnowledgeRetriever(
        knowledge_dir=knowledge_dir,
        mode="hybrid",
        e5_weight=0.5,
        bge_weight=0.5,
    )

    try:
        for query_num, query in enumerate(QUERIES, start=1):
            print("\n" + "#" * 76)
            print(f"CONSULTA {query_num}: {query}")
            print("#" * 76)

            for label, e5_weight, bge_weight in WEIGHT_CONFIGS:
                retriever.e5_weight = e5_weight
                retriever.bge_weight = bge_weight
                results = retriever.search(query, top_k=TOP_K)

                print(f"\n--- {label} ---")
                for rank, item in enumerate(results, start=1):
                    source = item["source"]
                    score = item["score"]
                    text = " ".join(item["text"].split())
                    if len(text) > 220:
                        text = text[:217] + "..."
                    print(f"{rank}. score={score:.4f} | {source}")
                    print(f"   {text}")

    finally:
        retriever.close()

    print("\n" + "=" * 76)
    print("Experimento finalizado. No se modificó main.py ni config.json.")
    print("Compará qué ponderación coloca primero los fragmentos correctos.")
    print("=" * 76)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"\nERROR durante el experimento: {type(exc).__name__}: {exc}")
        raise
