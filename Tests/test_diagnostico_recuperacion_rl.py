from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT_DIR / "Agent"
KNOWLEDGE_DIR = ROOT_DIR / "Knowledge"

sys.path.insert(0, str(AGENT_DIR))

from MultilingualKnowledgeRetriever import MultilingualKnowledgeRetriever


QUERIES = [
    "¿Qué función cumplen la política del agente y la función de valor en aprendizaje por refuerzo?",
    "¿Qué función cumple el Replay Buffer en SAC?",
    "¿Cómo se calcula la actualización de los críticos en Soft Actor-Critic?",
]

retriever = None

try:
    print("=" * 80)
    print("GIAR-ORION | Diagnóstico aislado de recuperación RAG")
    print("=" * 80)

    retriever = MultilingualKnowledgeRetriever(
        knowledge_dir=KNOWLEDGE_DIR,
        mode="hybrid",
        e5_weight=0.7,
        bge_weight=0.3,
        device="cpu",
        local_files_only=True,
    )

    for number, query in enumerate(QUERIES, start=1):
        print(f"\n{'=' * 80}")
        print(f"CONSULTA {number}: {query}")
        print("=" * 80)

        results = retriever.search(query, top_k=5)

        if not results:
            print("No se recuperaron fragmentos.")
            continue

        for rank, item in enumerate(results, start=1):
            print(f"\n[{rank}] Fuente: {item['source']}")
            print(f"Similitud: {item['score']:.4f}")
            print("-" * 60)
            print(item["text"])

    print("\nDiagnóstico finalizado.")

finally:
    if retriever is not None:
        retriever.close()