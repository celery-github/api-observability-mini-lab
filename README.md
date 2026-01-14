 API Observability Mini-Lab

A free, serverless observability demo that monitors public APIs on a schedule, captures latency + uptime signals, and publishes a dashboard via GitHub Pages.

 Architecture
GitHub Actions (cron) -> Python monitor -> JSON (repo) -> GitHub Pages dashboard

 What it measures
- HTTP status + success rate
- Response time (ms)
- Error capture (timeouts / failures)
- Historical event log (capped)

 Run locally
pip install -r monitor/requirements.txt
python monitor/monitor.py

 Add a new API target
Edit `monitor/targets.json` and add:
```json
{ "name": "My API", "url": "https://example.com/health" }
