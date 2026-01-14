import json
import time
import os
from datetime import datetime, timezone
import requests

ROOT = os.path.dirname(os.path.dirname(__file__))
DOCS_DATA = os.path.join(ROOT, "docs", "data")
LATEST_PATH = os.path.join(DOCS_DATA, "latest.json")
HISTORY_PATH = os.path.join(DOCS_DATA, "history.json")
TARGETS_PATH = os.path.join(ROOT, "monitor", "targets.json")

TIMEOUT_SECONDS = 10

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def check_target(name, url):
    start = time.perf_counter()
    try:
        r = requests.get(url, timeout=TIMEOUT_SECONDS, headers={"User-Agent": "api-observability-mini-lab"})
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        ok = 200 <= r.status_code < 300
        return {
            "name": name,
            "url": url,
            "timestamp": now_iso(),
            "status_code": r.status_code,
            "latency_ms": elapsed_ms,
            "ok": ok,
            "error": None
        }
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {
            "name": name,
            "url": url,
            "timestamp": now_iso(),
            "status_code": None,
            "latency_ms": elapsed_ms,
            "ok": False,
            "error": str(e)
        }

def main():
    targets = load_json(TARGETS_PATH, [])
    latest = {"generated_at": now_iso(), "results": []}

    history = load_json(HISTORY_PATH, {"events": []})

    for t in targets:
        res = check_target(t["name"], t["url"])
        latest["results"].append(res)
        history["events"].append(res)

    # Keep history from exploding: last 2,000 events
    history["events"] = history["events"][-2000:]

    save_json(LATEST_PATH, latest)
    save_json(HISTORY_PATH, history)

if __name__ == "__main__":
    main()
