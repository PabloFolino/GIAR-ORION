from pathlib import Path
import shutil, sys
root = Path(__file__).resolve().parent
project = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
test = root / "Test" / "TEST_PERFORMANCE"
src_agent = project / "Agent"
dst_agent = test / "Agent"
if not (project / "main_multilinea.py").exists() or not src_agent.is_dir():
    raise SystemExit("Ejecutá indicando la raíz GIAR-ORION, donde están main_multilinea.py y Agent/.")
core = {"ClaimExtractor.py", "ClaimVerificationPipeline.py", "EvidenceVerifier.py", "__init__.py"}
for item in src_agent.iterdir():
    if item.name in core:
        continue
    target = dst_agent / item.name
    if item.is_dir():
        if target.exists(): shutil.rmtree(target)
        shutil.copytree(item, target)
    elif item.is_file() and item.suffix == ".py":
        shutil.copy2(item, target)
print("Dependencias auxiliares de Agent copiadas a Test/TEST_PERFORMANCE/Agent.")
print("La base Knowledge se lee desde el proyecto original; Memory y Logs quedan aislados.")
