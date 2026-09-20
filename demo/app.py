"""Public, sample-only playground. Private memory stays in the local CLI database."""
import json
import os
from pathlib import Path
import threading
import time
from collections import deque
from flask import Flask, jsonify, render_template, request
from jev_context.engine import Engine, Store, ProviderError

HERE = Path(__file__).parent
SAMPLE = json.loads((HERE / "sample.json").read_text())
BASE = os.environ.get("CONTEXT_DEMO_PREFIX", "/demos/context-engine").rstrip("/")
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8192
store = Store(os.environ.get("JEV_CONTEXT_DB", str(HERE / "sample.sqlite3")))
for doc in SAMPLE["documents"]:
    if [p["text"] for p in store.list("demo", doc["source"])] != doc["text"].split("\n\n"):
        store.ingest(doc["text"], doc["source"], "demo")
engine = Engine(store)
lock = threading.Lock()
requests_window = deque()
concurrency = threading.BoundedSemaphore(3)

@app.get(BASE + "/")
def home():
    return render_template("index.html", base=BASE)

@app.get(BASE + "/health")
def health():
    return jsonify(status="ok", configured=bool(os.environ.get("TYPESAFE_API_KEY")), paragraphs=len(store.list("demo")))

@app.get(BASE + "/api/sample")
def sample():
    return jsonify(name=SAMPLE["name"], description=SAMPLE["description"], requests=SAMPLE["requests"], paragraphs=store.list("demo"))

@app.post(BASE + "/api/select")
def select():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Send a JSON request object."), 400
    query = payload.get("request")
    if not isinstance(query, str) or not query.strip() or len(query) > 2000:
        return jsonify(error="Enter a request between 1 and 2,000 characters."), 400
    try:
        threshold = float(payload.get("threshold", 0.5))
        max_chars = int(payload.get("max_chars", 6000))
        if not 0 <= threshold <= 1 or not 250 <= max_chars <= 20000:
            raise ValueError()
    except (TypeError, ValueError, OverflowError):
        return jsonify(error="Threshold must be 0–1; budget must be 250–20,000 characters."), 400
    with lock:
        now = time.monotonic()
        while requests_window and requests_window[0] < now-60:
            requests_window.popleft()
        if len(requests_window) >= int(os.environ.get("CONTEXT_DEMO_RPM", "30")):
            return jsonify(error="The shared demo is busy. Please try again in a minute."), 429
        requests_window.append(now)
    if not concurrency.acquire(blocking=False):
        return jsonify(error="All demo inference slots are busy. Please retry shortly."), 429
    try:
        return jsonify(engine.query(query, "demo", threshold, max_chars))
    except ProviderError as exc:
        return jsonify(error=str(exc)), 502
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    finally:
        concurrency.release()

@app.after_request
def headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    if "/api/" in request.path:
        response.headers["Cache-Control"] = "no-store"
    return response

@app.get(BASE + "/assets/<path:name>")
def assets(name):
    return app.send_static_file(name)
