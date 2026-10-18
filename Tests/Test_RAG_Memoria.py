import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
AGENT_DIR = BASE_DIR / "Agent"

sys.path.insert(0, str(AGENT_DIR))

from MultilingualKnowledgeRetriever import MultilingualKnowledgeRetriever

print("\nInicializando exclusivamente el recuperador RAG híbrido...")

recuperador = None

try:
    recuperador = MultilingualKnowledgeRetriever(
        knowledge_dir=BASE_DIR / "Knowledge",
        mode="hybrid",
        e5_weight=0.7,
        bge_weight=0.3,
        device="cpu",   # cuda o cpu
    )

    print("\nRAG inicializado correctamente.")
    print("Modo: hybrid")
    print("E5: 70 %")
    print("BGE-M3: 30 %")
    print("\nEl recuperador permanece cargado.")
    print("Abrí otra ventana de PowerShell y ejecutá: nvidia-smi")
    print("\nPara terminar esta prueba, presioná Ctrl+C.")

    while True:
        input("RAG activo. Presioná Enter para continuar...")

except KeyboardInterrupt:
    print("\nFinalizando prueba...")

finally:
    if recuperador is not None:
        recuperador.close()

    print("Prueba finalizada.")
