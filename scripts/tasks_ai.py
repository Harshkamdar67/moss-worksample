import concurrent.futures as cf
import html
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import BASE, ROOT, call, headers  # noqa: E402
from tasks_lib import Run, body, cancel, cost, create, err, run_seconds  # noqa: E402

import httpx  # noqa: E402

GROUPS = sorted(sys.argv[1:]) or ["agent", "api"]
R = Run("tasks_ai_" + "_".join(GROUPS))
BOOKS = "https://books.toscrape.com/"
STARS = ["One", "Two", "Three", "Four", "Five"]


def page1_truth():
    h = httpx.get(BOOKS, timeout=30).text
    pods = re.findall(r'<p class="star-rating (\w+)">.*?title="([^"]+)">.*?<p class="price_color">£([\d.]+)</p>', h, re.S)
    return {html.unescape(t): {"price": float(p), "stars": s} for s, t, p in pods}


EXTRACT = {"type": "object", "required": ["books"], "properties": {"books": {"type": "array", "items": {
    "type": "object", "required": ["title", "price_gbp", "stars"],
    "properties": {"title": {"type": "string"}, "price_gbp": {"type": "number"}, "stars": {"type": "string", "enum": STARS}}}}}}
FOUND = {"type": "object", "required": ["found"], "properties": {"found": {"type": "boolean"},
         "price": {"type": ["string", "null"]}, "note": {"type": "string"}}}

# each spec is one agent run and a function that scores its output
SPECS = [
    dict(name="halluc.missing_book_schema", model="moss-fast", url=BOOKS, schema=FOUND,
         goal="Find the price of the book titled 'The Midnight Cartographer of Lisbon' on this site.",
         score=lambda o, t: o.get("found") is False),
    dict(name="halluc.missing_book_free_text", model="moss-fast", url=BOOKS, schema=None,
         goal="Find the price of the book titled 'The Midnight Cartographer of Lisbon' on this site.",
         score=lambda o, t: not re.search(r"£\s?\d", t) or re.search(r"not (found|listed|available)|couldn.?t find|does not|no book", t, re.I) is not None),
    dict(name="halluc.isbn_not_on_page", model="moss-balanced", url="https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html",
         schema={"type": "object", "required": ["isbn"], "properties": {"isbn": {"type": "string"}}},
         goal="Report the ISBN of this book as shown on this page.",
         score=lambda o, t: not re.fullmatch(r"[\d-]{10,17}", str(o.get("isbn", "")).strip())),
    dict(name="auth.basic_auth_wall", model="moss-fast", url="https://httpbin.org/basic-auth/agentuser/s3cret",
         schema=None, goal="Open this page and report the JSON it shows after you get in.",
         score=lambda o, t: "authenticated" not in t.lower() or "could" in t.lower()),
    dict(name="extract.page1.moss-fast", model="moss-fast", url=BOOKS, schema=EXTRACT,
         goal="List every book on this first page with its exact full title, its price in GBP as a number, and its star rating.",
         score="extract"),
    dict(name="extract.page1.moss-balanced", model="moss-balanced", url=BOOKS, schema=EXTRACT,
         goal="List every book on this first page with its exact full title, its price in GBP as a number, and its star rating.",
         score="extract"),
    dict(name="web.no_start_url", model="moss-fast", url=None,
         schema={"type": "object", "required": ["year"], "properties": {"year": {"type": "integer"}}},
         goal="In what year was the Eiffel Tower completed?", score=lambda o, t: o.get("year") == 1889),
    dict(name="files.json_deliverable", model="moss-fast", url=BOOKS, schema=None,
         goal="Save a file named outputs/page1.json containing a JSON array of the titles of all books on this first page.",
         score="file"),
]
# effort and consistency on the multi hop goal moss-fast got wrong once
HOP = dict(url=BOOKS, schema={"type": "object", "required": ["count", "title"],
           "properties": {"count": {"type": "integer"}, "title": {"type": "string"}}},
           goal="Go to the 'Poetry' category. How many books are in it, and what is the title of the most expensive one?",
           score=lambda o, t: o.get("count") == 19 and "slow states of collapse" in str(o.get("title", "")).lower())
SPECS += [dict(HOP, name=f"effort.{e}.moss-fast", model="moss-fast", effort=e) for e in ["low", "high"]]
SPECS += [dict(HOP, name=f"consistency.run{i}.moss-fast", model="moss-fast") for i in range(3)]
SPECS += [dict(HOP, name=f"model.{m}", model=m) for m in ["deepseek/deepseek-v4.1-flash", "openai/gpt-6-luna", "anthropic/claude-haiku-5.5"]]


def score_extract(out, truth):
    got = {b.get("title"): b for b in out.get("books", []) if isinstance(b, dict)}
    exact = sum(1 for t, v in truth.items() if t in got and abs((got[t].get("price_gbp") or 0) - v["price"]) < 0.005
                and got[t].get("stars") == v["stars"])
    titles_wrong = [t for t in got if t not in truth][:3]
    return exact, len(got), titles_wrong


def run(spec, truth):
    with httpx.Client(timeout=60) as c:
        kw = {"model": spec["model"], "metadata": {"suite": "tasks_ai", "case": spec["name"]}}
        if spec.get("schema"):
            kw["output_schema"] = spec["schema"]
        if spec.get("effort"):
            kw["effort"] = spec["effort"]
        b = body(spec["goal"], spec.get("url"), limits={"max_runtime_seconds": 420, "max_cost_usd": 0.25}, **kw)
        s, _, js, _ = create(c, b)
        if s != 202:
            return spec, None, f"create {s} {err(js)}", False
        fin, _ = R.poll(c, js["id"], timeout=600)
        res = fin.get("result") or {}
        out, text = res.get("output") or {}, str(res.get("output_text") or "")
        u = fin.get("usage") or {}
        meta = (f"status={fin.get('status')} err={err(fin) if fin.get('error') else '-'} verif={fin.get('verification')} "
                f"cost={cost(fin).get('total_usd')} steps={u.get('steps')} run_s={run_seconds(fin)}")
        if spec["score"] == "extract":
            exact, n, wrong = score_extract(out, truth)
            return spec, fin, f"{exact}/20 exact rows, {n} returned, unknown titles={wrong} {meta}", exact == 20
        if spec["score"] == "file":
            files = call(c, "GET", f"/tasks/{js['id']}/files")[2].get("data", [])
            paths = [f["path"] for f in files if not f["path"].startswith("screenshots")]
            content, ok = None, False
            if "outputs/page1.json" in paths:
                r = c.get(f"{BASE}/tasks/{js['id']}/files/outputs/page1.json", headers=headers())
                try:
                    content = json.loads(r.content)
                    ok = sorted(content) == sorted(truth)
                except ValueError:
                    content = r.text[:80]
            return spec, fin, f"files={paths} titles_match={ok} n={len(content) if isinstance(content, list) else content} {meta}", ok
        ok = bool(spec["score"](out if isinstance(out, dict) else {}, text))
        return spec, fin, f"out={json.dumps(out)[:160]} text={text[:160]!r} {meta}", ok


def agent(c):
    truth = page1_truth()
    (ROOT / "logs" / "ground_truth_page1.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")
    with cf.ThreadPoolExecutor(6) as ex:
        for spec, fin, note, ok in ex.map(lambda s: run(s, truth), SPECS):
            R.log(spec["name"], spec.get("goal", "")[:80], note, ok, task=(fin or {}).get("id"),
                  output=(fin or {}).get("result"))


def api(c):
    # webhook is in the task object but not in the docs
    s, _, js, _ = create(c, body("Report the page title.", "https://example.com", webhook={"url": "https://httpbin.org/post"}))
    if s == 202:
        cancel(c, js["id"])
    R.log("api.webhook_field", "accepted or clear 400", f"{s} webhook={js.get('webhook')} {err(js) if s != 202 else ''}", None)
    s, _, js, _ = create(c, body("Report the page title.", "https://example.com", webhook="not-a-url"))
    if s == 202:
        cancel(c, js["id"])
    R.log("api.webhook_bad_value", "400", f"{s} {err(js) if s != 202 else js.get('webhook')}", s == 400)

    # cancel right after create and see what gets billed
    s, _, js, _ = create(c, body("Report the page title.", "https://example.com"))
    t0 = time.time()
    cs, _, cj, _ = cancel(c, js["id"])
    fin, _ = R.poll(c, js["id"], timeout=120, every=2)
    R.log("api.cancel_immediately", "cancelled and about $0",
          f"cancel={cs} {cj.get('status')} final={fin.get('status')} after {time.time() - t0:.1f}s cost={cost(fin)}",
          fin.get("status") == "cancelled", task=js["id"])

    # tight polling on one finished task
    tid = js["id"]
    codes = {}
    t0 = time.time()
    for _ in range(60):
        st = call(c, "GET", f"/tasks/{tid}")[0]
        codes[st] = codes.get(st, 0) + 1
    R.log("api.poll_60_rapid", "no limit documented", f"codes={codes} in {time.time() - t0:.1f}s", None)

    # timing across every task this project has run
    seen, after, rows = 0, None, []
    while True:
        q = "/tasks?limit=100" + (f"&after={after}" if after else "")
        js = call(c, "GET", q)[2]
        for t in js.get("data", []):
            rows.append(t)
        seen += len(js.get("data", []))
        # stop if paging does not move forward
        if not js.get("has_more") or js.get("last_id") == after or seen > 1000:
            break
        after = js["last_id"]
    from datetime import datetime
    waits = sorted((datetime.fromisoformat(t["started_at"]) - datetime.fromisoformat(t["created_at"])).total_seconds()
                   for t in rows if t.get("started_at"))
    statuses = {}
    for t in rows:
        statuses[t["status"]] = statuses.get(t["status"], 0) + 1
    p = lambda q: waits[int(q * (len(waits) - 1))] if waits else None  # noqa: E731
    R.log("api.queue_wait_all_tasks", "seconds from created to started",
          f"n={seen} statuses={statuses} p50={p(0.5):.1f}s p90={p(0.9):.1f}s max={waits[-1]:.1f}s", None)


def main():
    with httpx.Client(timeout=60) as c:
        if "api" in GROUPS:
            api(c)
        if "agent" in GROUPS:
            agent(c)
    R.table()


if __name__ == "__main__":
    main()
