import json, time
from pathlib import Path
from datetime import datetime

LOG_PATH = Path(__file__).resolve().parent / "performance_metrics.jsonl"

def record(component, operation, elapsed_s, **data):
    row = {"timestamp": datetime.now().astimezone().isoformat(), "component": component,
           "operation": operation, "elapsed_s": round(float(elapsed_s), 6), **data}
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return row

def timed_call(component, operation, fn, *args, **kwargs):
    start = time.perf_counter()
    try:
        result = fn(*args, **kwargs)
    except Exception as exc:
        record(component, operation, time.perf_counter()-start, status="ERROR", error=f"{type(exc).__name__}: {exc}")
        raise
    record(component, operation, time.perf_counter()-start, status="OK")
    return result
