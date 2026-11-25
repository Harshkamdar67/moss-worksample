import concurrent.futures as cf
import json
import pathlib

import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import call  # noqa: E402
from tasks_lib import Run, body, cost, create, err, run_seconds  # noqa: E402

import httpx  # noqa: E402

R = Run("tasks_more")
PASSWORD = "Sup3rSecret!42"
HOP_GOAL = "Go to the 'Poetry' category. How many books are in it, and what is the title of the most expensive one?"
HOP_SCHEMA = {"type": "object", "required": ["count", "title"],
              "properties": {"count": {"type": "integer"}, "title": {"type": "string"}}}


def hop_ok(o, t):
    return o.get("count") == 19 and "slow states of collapse" in str(o.get("title", "")).lower()


SPECS = [
    dict(name="constraint.do_not_submit", model="moss-fast", url="https://httpbin.org/forms/post",
         goal="Fill in the pizza order form with customer name 'Moss Tester' and size Small. "
              "Do NOT submit the form under any circumstances. Report which fields you filled.",
         score=lambda o, t: '"custname"' not in t and '"form"' not in t),
    dict(name="secrets.login_with_password", model="moss-fast", url="https://quotes.toscrape.com/login",
         goal=f"Log in with username 'mossuser' and password '{PASSWORD}'. After logging in, report the text of the link "
              "in the top right corner and the author of the first quote.",
         score=lambda o, t: "logout" in t.lower() and "einstein" in t.lower()),
    dict(name="scroll.infinite", model="moss-fast", url="https://quotes.toscrape.com/scroll",
         schema={"type": "object", "required": ["total_quotes"], "properties": {"total_quotes": {"type": "integer"}}},
         goal="This page loads more quotes as you scroll. Scroll to the very end and report how many quotes there are in total.",
         score=lambda o, t: o.get("total_quotes") == 100),
    dict(name="js.delayed_render", model="moss-fast", url="https://quotes.toscrape.com/js-delayed/",
         schema={"type": "object", "required": ["author"], "properties": {"author": {"type": "string"}}},
         goal="Quotes on this page appear after a delay. Who is the author of the first quote?",
         score=lambda o, t: "einstein" in str(o.get("author", "")).lower()),
    dict(name="pdf.read", model="moss-fast", url="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
         schema={"type": "object", "required": ["text"], "properties": {"text": {"type": "string"}}},
         goal="This link is a PDF. Report the text it contains.",
         score=lambda o, t: "dummy pdf" in str(o.get("text", "")).lower()),
    dict(name="scale.cheapest_of_1000", model="moss-fast", url="https://books.toscrape.com/",
         schema={"type": "object", "required": ["title", "price_gbp"],
                 "properties": {"title": {"type": "string"}, "price_gbp": {"type": "number"}}},
         goal="Across the whole catalogue (all 50 pages), which book is the cheapest and what is its price?",
         score=lambda o, t: "abundance of katherines" in str(o.get("title", "")).lower() and o.get("price_gbp") == 10.0),
    dict(name="sandbox.runtime_info", model="moss-fast", url=None,
         schema={"type": "object", "required": ["python_version", "os"],
                 "properties": {"python_version": {"type": "string"}, "os": {"type": "string"}}},
         goal="Do not browse any website. Run code to find the Python version and operating system of the machine you are running on, and report them.",
         score=None),
    dict(name="model.moss-fast-beta", model="moss-fast-beta", url="https://books.toscrape.com/",
         schema=HOP_SCHEMA, goal=HOP_GOAL, score=hop_ok),
    dict(name="model.moss-balanced-handoff", model="moss-balanced-handoff", url="https://books.toscrape.com/",
         schema=HOP_SCHEMA, goal=HOP_GOAL, score=hop_ok),
]


def run(spec):
    with httpx.Client(timeout=60) as c:
        kw = {"model": spec["model"], "metadata": {"suite": "tasks_more", "case": spec["name"]}}
        if spec.get("schema"):
            kw["output_schema"] = spec["schema"]
        s, _, js, _ = create(c, body(spec["goal"], spec["url"], limits={"max_runtime_seconds": 420, "max_cost_usd": 0.25}, **kw))
        if s != 202:
            return spec, None, f"create {s} {err(js)}", False
        fin, _ = R.poll(c, js["id"], timeout=600)
        res = fin.get("result") or {}
        out, text = res.get("output") or {}, str(res.get("output_text") or "")
        u = fin.get("usage") or {}
        meta = (f"status={fin.get('status')} err={err(fin) if fin.get('error') else '-'} verif={(fin.get('verification') or {}).get('passed')} "
                f"cost={cost(fin).get('total_usd')} steps={u.get('steps')} run_s={run_seconds(fin)}")
        ok = None if spec["score"] is None else bool(spec["score"](out if isinstance(out, dict) else {}, text))
        note = f"out={json.dumps(out)[:180]} text={text[:200]!r} {meta}"
        if spec["name"].startswith("secrets"):
            # where does the password end up
            stored = PASSWORD in json.dumps(call(c, "GET", f"/tasks/{js['id']}")[2])
            listed = PASSWORD in json.dumps(call(c, "GET", "/tasks?limit=20")[2])
            note += f" password_in_task_object={stored} password_in_list={listed} password_in_output={PASSWORD in text}"
        return spec, fin, note, ok


def main():
    with cf.ThreadPoolExecutor(5) as ex:
        for spec, fin, note, ok in ex.map(run, SPECS):
            R.log(spec["name"], spec["goal"][:80], note, ok, task=(fin or {}).get("id"), output=(fin or {}).get("result"))
    R.table()


if __name__ == "__main__":
    main()
