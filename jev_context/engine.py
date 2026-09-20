"""Dependency-free storage, Jev inference, and exact paragraph assembly."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

POLICY = json.loads(Path(__file__).with_name("policy.json").read_text())

class ProviderError(RuntimeError):
    """Safe-to-display provider failure; never includes keys or source text."""

class Store:
    def __init__(self, path=None):
        self.path = str(Path(path or os.environ.get("JEV_CONTEXT_DB", "~/.local/share/jev-context/context.sqlite3")).expanduser())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS paragraphs (
                id TEXT PRIMARY KEY, collection TEXT NOT NULL, source TEXT NOT NULL,
                position INTEGER NOT NULL, text TEXT NOT NULL, updated_at REAL NOT NULL,
                UNIQUE(collection, source, position));
            CREATE INDEX IF NOT EXISTS collection_idx ON paragraphs(collection);
            CREATE TABLE IF NOT EXISTS judgments (
                fingerprint TEXT PRIMARY KEY, result TEXT NOT NULL, created_at REAL NOT NULL);
            ''')
    def connect(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        return db
    def ingest(self, text, source, collection="default"):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Provide a nonempty document.")
        if not source.strip() or not collection.strip():
            raise ValueError("Source and collection cannot be empty.")
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
        now = time.time()
        with self.connect() as db:
            db.execute("DELETE FROM paragraphs WHERE collection=? AND source=?", (collection, source))
            for position, paragraph in enumerate(paragraphs):
                identity = json.dumps([collection, source, position, paragraph], ensure_ascii=False)
                pid = hashlib.sha256(identity.encode()).hexdigest()[:20]
                db.execute("INSERT INTO paragraphs VALUES (?,?,?,?,?,?)", (pid, collection, source, position, paragraph, now))
        return self.list(collection, source)
    def list(self, collection="default", source=None):
        with self.connect() as db:
            sql = "SELECT * FROM paragraphs WHERE collection=?"
            args = [collection]
            if source is not None:
                sql += " AND source=?"
                args.append(source)
            return [dict(row) for row in db.execute(sql + " ORDER BY source, position", args)]
    def delete(self, source, collection="default"):
        with self.connect() as db:
            count = db.execute("DELETE FROM paragraphs WHERE collection=? AND source=?", (collection, source)).rowcount
            db.execute("DELETE FROM judgments")
        return count
    def cached(self, fingerprint, ttl):
        with self.connect() as db:
            row = db.execute("SELECT result FROM judgments WHERE fingerprint=? AND created_at>?", (fingerprint, time.time()-ttl)).fetchone()
        return json.loads(row[0]) if row else None
    def cache(self, fingerprint, result):
        with self.connect() as db:
            db.execute("DELETE FROM judgments WHERE created_at<?", (time.time()-86400,))
            db.execute("INSERT OR REPLACE INTO judgments VALUES (?,?,?)", (fingerprint, json.dumps(result), time.time()))

class JevClient:
    def __init__(self, api_key=None, model=None, timeout=45):
        self.api_key = api_key or os.environ.get("TYPESAFE_API_KEY")
        self.model = model or os.environ.get("TYPESAFE_MODEL", "jev-latest")
        self.timeout = timeout
    def judge(self, request, paragraphs, policy):
        if not self.api_key:
            raise ProviderError("Set TYPESAFE_API_KEY before selecting context.")
        questions = {p["id"]: {
            "type": "noul",
            "instructions": {"question": policy["instructions"], "paragraph": f"paragraphs[{index}]", "request": "request"},
            "criteria": policy["criteria"],
        } for index, p in enumerate(paragraphs)}
        payload = {"model": self.model, "state": {"request": request, "paragraphs": [
            {"text": p["text"], "source": p["source"], "position": p["position"]} for p in paragraphs]}, "questions": questions}
        req = Request("https://api.typesafe.ai/v1/systemone", data=json.dumps(payload).encode(), headers={
            "Authorization": "Bearer " + self.api_key, "Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=self.timeout) as response:
                result = json.load(response)
        except HTTPError as exc:
            raise ProviderError(f"Jev returned HTTP {exc.code}. Check provider access or quota; no fallback context was fabricated.") from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise ProviderError("Jev could not complete the request. Please retry.") from None
        scores = {}
        try:
            for paragraph in paragraphs:
                answer = result["answers"][paragraph["id"]]
                score = answer["noul"]
                if answer.get("type") != "noul" or isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 1:
                    raise ValueError()
                scores[paragraph["id"]] = score
        except (KeyError, TypeError, ValueError):
            raise ProviderError("Jev returned incomplete or invalid judgments. No partial selection was used.") from None
        return {"scores": scores, "usage": result.get("usage", {}), "model": result.get("model", self.model)}

def assemble(rows, scores, threshold, max_chars):
    selected, ranked, used = [], [], 0
    for paragraph in sorted(rows, key=lambda p: (-scores[p["id"]], p["source"], p["position"])):
        score = scores[paragraph["id"]]
        block = json.dumps({"id": paragraph["id"], "source": paragraph["source"], "paragraph": paragraph["position"]+1, "text": paragraph["text"]}, ensure_ascii=False)
        cost = len(block) + (1 if selected else 0)
        reason = "below_threshold" if score < threshold else "selected" if used+cost <= max_chars else "over_budget"
        ranked.append({**paragraph, "relevance": score, "selected": reason == "selected", "selection_reason": reason})
        if reason == "selected":
            selected.append(block)
            used += cost
    # JSONL preserves source boundaries even when a paragraph contains fake XML delimiters.
    return ranked, "\n".join(selected)

class Engine:
    def __init__(self, store, client=None, policy=None, batch_size=12, workers=3, cache_ttl=3600):
        if batch_size < 1 or workers < 1:
            raise ValueError("Batch size and workers must be positive.")
        self.store, self.client = store, client or JevClient()
        self.policy, self.batch_size, self.workers, self.cache_ttl = policy or POLICY, batch_size, workers, cache_ttl
    def query(self, request, collection="default", threshold=0.5, max_chars=12000):
        if not isinstance(request, str) or not request.strip():
            raise ValueError("Provide a nonempty request.")
        if not math.isfinite(threshold) or not 0 <= threshold <= 1 or max_chars < 1:
            raise ValueError("Threshold must be 0–1 and context budget must be positive.")
        start = time.perf_counter()
        rows = self.store.list(collection)
        fingerprint = hashlib.sha256(json.dumps([request, rows, self.policy, self.client.model, self.batch_size], sort_keys=True).encode()).hexdigest()
        result = self.store.cached(fingerprint, self.cache_ttl) if self.cache_ttl else None
        cached = result is not None
        if result is None:
            batches = [rows[i:i+self.batch_size] for i in range(0, len(rows), self.batch_size)]
            with ThreadPoolExecutor(max_workers=self.workers) as pool:
                results = list(pool.map(lambda b: self.client.judge(request, b, self.policy), batches))
            result = {"scores": {}, "usage": {}, "models": []}
            for item in results:
                result["scores"].update(item["scores"])
                if item["model"] not in result["models"]:
                    result["models"].append(item["model"])
                for key, value in item["usage"].items():
                    if isinstance(value, (int, float)):
                        result["usage"][key] = result["usage"].get(key, 0) + value
            if rows and self.cache_ttl:
                self.store.cache(fingerprint, result)
        ranked, context = assemble(rows, result["scores"], threshold, max_chars)
        return {"request": request, "collection": collection, "paragraphs": ranked, "context": context,
                "selected_count": sum(p["selected"] for p in ranked), "total_count": len(rows),
                "context_chars": len(context), "source_chars": sum(len(p["text"]) for p in rows),
                "threshold": threshold, "max_chars": max_chars, "cached": cached,
                "usage": {} if cached else result["usage"], "original_usage": result["usage"],
                "models": result["models"], "policy_version": self.policy["version"],
                "elapsed_ms": round((time.perf_counter()-start)*1000)}
