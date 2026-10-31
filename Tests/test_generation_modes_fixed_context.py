import json
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
EVIDENCE_FILE = (
    BASE_DIR
    / "Tests"
    / "results_actor_critic_fixed_context"
    / "20261018_191844"
    / "evidencia.json"
)
CONFIG_FILE = BASE_DIR / "config.json"

def read_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def call_ollama(base_url, model, messages, think, num_predict, temperature, seed):
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": think,
        "options": {
            "num_predict": num_predict,
            "temperature": temperature,
            "seed": seed,
        },
    }

    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.perf_counter()

    with urllib.request.urlopen(request, timeout=300) as response:
        result = json.loads(response.read().decode("utf-8"))

    elapsed = time.perf_counter() - started
    message = result.get("message", {})

    return {
        "status": "OK",
        "answer": message.get("content", ""),
        "think_content": message.get("thinking", ""),
        "elapsed_seconds_wall": round(elapsed, 3),
        "total_duration_ns": result.get("total_duration"),
        "load_duration_ns": result.get("load_duration"),
        "prompt_eval_count": result.get("prompt_eval_count"),
        "prompt_eval_duration_ns": result.get("prompt_eval_duration"),
        "eval_count": result.get("eval_count"),
        "eval_duration_ns": result.get("eval_duration"),
        "done_reason": result.get("done_reason"),
        "error": "",
    }

def main():
    if not EVIDENCE_FILE.is_file():
        raise FileNotFoundError(f"No existe la evidencia: {EVIDENCE_FILE}")

    config = read_json(CONFIG_FILE)
    evidence = read_json(EVIDENCE_FILE)

    llm = config["llm"]
    modes = config["generation"]["modes"]

    query = evidence["query"]
    system_prompt = evidence["system_prompt"]
    user_prompt = evidence["user_prompt"]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = BASE_DIR / "Tests" / "results_generation_modes" / timestamp
    output_dir.mkdir(parents=True, exist_ok=False)

    results = {
        "query": query,
        "model": llm["model"],
        "temperature": 0.0,
        "seed": 42,
        "evidence_file": str(EVIDENCE_FILE.relative_to(BASE_DIR)),
        "context_fragment_count": len(evidence.get("fragments", [])),
        "modes": {},
    }

    print("=" * 70)
    print("GIAR-ORION - Comparación de modos con contexto fijo")
    print(f"Modelo: {llm['model']}")
    print(f"Fragmentos: {results['context_fragment_count']}")
    print(f"Salida: {output_dir}")
    print("=" * 70)

    for mode_name in ("rapido", "investigacion"):
        params = modes[mode_name]
        print(f"\nEjecutando modo: {mode_name}")
        print(f"  think={params['think']}")
        print(f"  num_predict={params['num_predict']}")

        try:
            result = call_ollama(
                base_url=llm["base_url"],
                model=llm["model"],
                messages=messages,
                think=params["think"],
                num_predict=params["num_predict"],
                temperature=0.0,
                seed=42,
            )
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            result = {
                "status": "ERROR",
                "answer": "",
                "error": str(exc),
            }

        result["parameters"] = {
            "think": params["think"],
            "num_predict": params["num_predict"],
            "temperature": 0.0,
            "seed": 42,
        }
        results["modes"][mode_name] = result

        with (output_dir / f"{mode_name}.json").open(
            "w", encoding="utf-8"
        ) as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"  Estado: {result['status']}")
        if result["status"] == "OK":
            print(f"  Tiempo: {result['elapsed_seconds_wall']} s")
            print(f"  Tokens de salida: {result.get('eval_count')}")
            print(f"  Motivo final: {result.get('done_reason')}")
            print("\nRespuesta:")
            print(result["answer"])
        else:
            print(f"  Error: {result['error']}")

    with (output_dir / "comparacion.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("Prueba finalizada.")
    print(f"Resultados guardados en: {output_dir}")
    print("=" * 70)

if __name__ == "__main__":
    main()
