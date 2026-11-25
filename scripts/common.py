import datetime
import json
import os
import pathlib
import time

import httpx

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://inference.moss.dev/v1"


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    return os.environ["MOSS_PROJECT_ID"], os.environ["MOSS_PROJECT_KEY"]


PID, PKEY = load_env()
AUTH = f"{PID}:{PKEY}"
KEEP = ("x-moss", "x-ratelimit", "retry-after", "x-should-retry", "x-request-id", "idempotent-replayed", "content-type")


def redact(s):
    return s.replace(PKEY, "moss_***").replace(PID, "<project_id>")


class Logger:
    # one jsonl file per run and the key never lands on disk
    def __init__(self, name):
        (ROOT / "logs").mkdir(exist_ok=True)
        self.path = ROOT / "logs" / f"{name}.jsonl"
        self.path.write_text("")

    def log(self, rec):
        rec = {"ts": datetime.datetime.utcnow().isoformat() + "Z", **rec}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(redact(json.dumps(rec, default=str)) + "\n")
        return rec


def headers(extra=None, auth=AUTH):
    h = {"Content-Type": "application/json"}
    if auth is not None:
        h["Authorization"] = f"Bearer {auth}"
    h.update(extra or {})
    return h


def pick_headers(resp):
    return {k: v for k, v in resp.headers.items() if k.lower().startswith(KEEP)}


def call(client, method, path, body=None, extra_headers=None, auth=AUTH, raw_body=None):
    t0 = time.perf_counter()
    r = client.request(method, BASE + path, headers=headers(extra_headers, auth),
                       json=body if raw_body is None else None, content=raw_body, timeout=120)
    dt = time.perf_counter() - t0
    try:
        js = r.json()
    except ValueError:
        js = {"_text": r.text[:2000]}
    return r.status_code, dt, js, pick_headers(r)
