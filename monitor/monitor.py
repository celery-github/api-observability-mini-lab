import json
import time
import os
from datetime import datetime, timezone
import requests

ROOT = os.path.dirname(os.path.dirname(__file__))
DOCS_DATA = os.path.join(ROOT, "docs", "data")

LATEST_PATH = os.path.join(DOCS_DATA, "latest.json")
HISTORY_PATH = os.path.join(DOCS_DATA, "history.json")
STATE_PATH = os.path.join(DOCS_DATA, "state.json")
ALERTS_PATH = os.path.join(DOCS_DATA, "alerts.json")
RECOVERIES_PATH = os.path.join(DOCS_DATA, "recoveries.json")
TARGETS_PATH = os.path.join(ROOT, "monitor", "targets.json")

TIMEOUT_SECONDS = 10
FAIL_THRESHOLD = 3
MAX_HISTORY_EVENTS = 2000

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
    state = load_json(STATE_PATH, {"streaks": {}, "open_alerts": {}})

    alerts_to_create = []
    recoveries_to_close = []

    for t in targets:
        res = check_target(t["name"], t["url"])
        latest["results"].append(res)
        history["events"].append(res)

        key = res["url"]
        prev_streak = int(state["streaks"].get(key, 0))
        has_open_alert = key in state.get("open_alerts", {})

        if res["ok"]:
            # If it was failing before and we have an open alert, mark recovery
            if prev_streak > 0 and has_open_alert:
                recoveries_to_close.append({
                    "name": res["name"],
                    "url": res["url"],
                    "issue_number": state["open_alerts"][key],
                    "timestamp": res["timestamp"],
                    "status_code": res["status_code"],
                    "latency_ms": res["latency_ms"]
                })

            # Reset streak on success
            state["streaks"][key] = 0

        else:
            # Increment streak on failure
            new_streak = prev_streak + 1
            state["streaks"][key] = new_streak

            # If threshold reached and no open issue exists, request issue creation
            if new_streak >= FAIL_THRESHOLD and not has_open_alert:
                alerts_to_create.append({
                    "name": res["name"],
                    "url": res["url"],
                    "streak": new_streak,
                    "last_status_code": res["status_code"],
                    "last_error": res["error"],
                    "last_latency_ms": res["latency_ms"],
                    "timestamp": res["timestamp"]
                })

    # Cap history size
    history["events"] = history["events"][-MAX_HISTORY_EVENTS:]

    save_json(LATEST_PATH, latest)
    save_json(HISTORY_PATH, history)
    save_json(STATE_PATH, state)
    save_json(ALERTS_PATH, {"generated_at": now_iso(), "alerts": alerts_to_create})
    save_json(RECOVERIES_PATH, {"generated_at": now_iso(), "recoveries": recoveries_to_close})

if __name__ == "__main__":
    main()
