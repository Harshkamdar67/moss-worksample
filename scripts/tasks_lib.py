import json
import pathlib
import sys
import time
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import ROOT, Logger, call  # noqa: E402

TASKDIR = ROOT / "logs" / "tasks"
TASKDIR.mkdir(parents=True, exist_ok=True)
DONE = ("completed", "failed", "cancelled")


class Run:
    # collects results for one script run and writes the jsonl log and md table
    def __init__(self, name):
        self.name = name
        self.log_ = Logger(name)
        self.rows = []

    def log(self, test, expect, outcome, ok, **extra):
        self.log_.log({"test": test, "expect": expect, "outcome": outcome, "ok": ok, **extra})
        self.rows.append((test, expect, outcome, ok))
        mark = "OK " if ok else ("BAD" if ok is False else "?? ")
        print(f"[{mark}] {test}: {outcome}"[:400], flush=True)

    def table(self):
        md = ["| test | expected | observed | pass |", "|---|---|---|---|"]
        md += [f"| {n} | {e} | {str(o).replace('|', '/')[:300]} | {'yes' if ok else ('NO' if ok is False else 'n/a')} |"
               for n, e, o, ok in self.rows]
        (ROOT / "logs" / f"{self.name}_summary.md").write_text("\n".join(md), encoding="utf-8")

    def poll(self, c, tid, timeout=900, every=5):
        # log each status change and save the final task object
        t0, last, transitions, js = time.time(), None, [], {}
        while time.time() - t0 < timeout:
            _, _, js, _ = call(c, "GET", f"/tasks/{tid}")
            st = js.get("status")
            if st != last:
                transitions.append((round(time.time() - t0, 1), st))
                self.log_.log({"poll": tid, "status": st, "t": round(time.time() - t0, 1), "usage": js.get("usage")})
                last = st
            if st in DONE:
                (TASKDIR / f"{tid}.json").write_text(json.dumps(js, indent=2))
                return js, transitions
            time.sleep(every)
        return js, transitions + [("timeout", last)]


def create(c, body, idem=None, extra=None):
    h = dict(extra or {})
    if idem:
        h["Idempotency-Key"] = idem
    return call(c, "POST", "/tasks", body, extra_headers=h)


def cancel(c, tid):
    return call(c, "POST", f"/tasks/{tid}/cancel")


def body(goal, start_url=None, limits=None, **kw):
    b = {"goal": goal, "environment": {"type": "browser"}, "model": "moss-fast",
         "limits": {"max_runtime_seconds": 180, "max_cost_usd": 0.15, **(limits or {})}, **kw}
    if start_url:
        b["environment"]["start_url"] = start_url
    return b


def err(js):
    e = js.get("error") or {}
    return f"{e.get('code')}: {str(e.get('message'))[:140]}"


def cost(js):
    return (js.get("usage") or {}).get("cost") or {}


def run_seconds(js):
    try:
        return (datetime.fromisoformat(js["finished_at"]) - datetime.fromisoformat(js["started_at"])).total_seconds()
    except (KeyError, TypeError, ValueError):
        return None
