import json
import pathlib
import sys
import time
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import AUTH, BASE, PID, PKEY, ROOT, Logger, call, headers, pick_headers, redact  # noqa: E402

import httpx  # noqa: E402

L = Logger("api_probe")
rows = []
FAST = "moss/fastlane-1"
CHAT = BASE + "/chat/completions"


def rec(name, ok, note):
    # client errors can echo the auth header so scrub before printing
    note = redact(note)
    L.log({"test": name, "ok": ok, "note": note})
    rows.append((name, note, ok))
    print(f"[{'OK ' if ok else ('BAD' if ok is False else '?? ')}] {name}: {note}"[:400], flush=True)


def tiny(text="Say hi.", **kw):
    return {"model": FAST, "max_tokens": 5, "messages": [{"role": "user", "content": text}], **kw}


def main():
    c = httpx.Client(timeout=60)

    # browser access with the project key
    r = c.options(CHAT, headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST",
                                 "Access-Control-Request-Headers": "authorization,content-type"})
    acao = r.headers.get("access-control-allow-origin")
    rec("cors.preflight_any_origin", None, f"{r.status_code} allow-origin={acao} allow-headers={r.headers.get('access-control-allow-headers')}")

    # request id echo and response headers
    rid = f"wsample-{uuid.uuid4()}"
    r = c.post(CHAT, headers=headers({"X-Request-Id": rid, "X-Moss-Cache": "off"}), json=tiny())
    rec("headers.request_id_echo", rid in json.dumps(dict(r.headers)), f"{r.status_code} echoed={rid in json.dumps(dict(r.headers))} headers={pick_headers(r)}")
    rec("headers.server_leak", None, f"server={r.headers.get('server')} via={r.headers.get('via')} x-moss-box={r.headers.get('x-moss-box')}")

    # rate limit counters should go down
    rem = []
    for _ in range(4):
        r = c.post(CHAT, headers=headers({"X-Moss-Cache": "off"}), json=tiny())
        rem.append(r.headers.get("x-ratelimit-remaining-requests"))
        time.sleep(0.6)
    rec("headers.ratelimit_remaining_moves", len(set(rem)) > 1, f"remaining over 4 calls={rem} limit={r.headers.get('x-ratelimit-limit-requests')} reset={r.headers.get('x-ratelimit-reset-requests')}")

    # compression
    r = c.post(CHAT, headers=headers({"Accept-Encoding": "gzip", "X-Moss-Cache": "off"}), json=tiny("Count to 50."))
    rec("http.gzip", None, f"content-encoding={r.headers.get('content-encoding')} http_version={r.http_version}")

    # auth parsing edge cases
    for name, h in [("auth.lowercase_bearer", {"Authorization": f"bearer {AUTH}"}),
                    ("auth.extra_spaces", {"Authorization": f"Bearer   {AUTH}  "}),
                    ("auth.x_api_key_header", {"x-api-key": AUTH}),
                    ("auth.key_with_newline", {"Authorization": f"Bearer {AUTH}\\n"}),
                    ("auth.basic_scheme", {"Authorization": "Basic " + __import__("base64").b64encode(AUTH.encode()).decode()})]:
        hh = {"Content-Type": "application/json", **h}
        try:
            r = c.post(CHAT, headers=hh, json=tiny())
            rec(name, None, f"{r.status_code} {r.text[:120]}")
        except httpx.HTTPError as e:
            rec(name, None, f"client error {e!r}")
    r = c.post(CHAT + f"?api_key={PKEY}", headers={"Content-Type": "application/json"}, json=tiny())
    rec("auth.key_in_query_string", r.status_code == 401, f"{r.status_code}")

    # timing of rejected keys
    ts = {}
    for label, a in [("valid_project_bad_key", f"{PID}:moss_{'0' * 32}"), ("bad_project", f"{uuid.uuid4()}:moss_{'0' * 32}")]:
        times = []
        for _ in range(5):
            t0 = time.perf_counter()
            c.post(CHAT, headers=headers(auth=a), json=tiny())
            times.append(time.perf_counter() - t0)
        ts[label] = round(sorted(times)[2], 3)
    rec("auth.reject_timing_p50", None, f"{ts}")

    # stop reading a long stream early and see what gets billed
    body = {"model": FAST, "stream": True, "stream_options": {"include_usage": True},
            "messages": [{"role": "user", "content": f"Write a 1500 word story about a lighthouse. ({uuid.uuid4().hex[:6]})"}]}
    got = 0
    with c.stream("POST", CHAT, headers=headers({"X-Moss-Cache": "off", "X-Request-Id": "wsample-abort"}), json=body) as r:
        for line in r.iter_lines():
            if line.startswith("data:"):
                got += 1
            if got >= 20:
                break
    rec("stream.client_abort", None, f"read {got} chunks then closed; check logs for billed tokens of request wsample-abort")

    # retrieval on and off against the project index
    q = "What topics are covered in the stored documents? Name three specific facts."
    for label, extra in [("on", {}), ("off", {"X-Moss-Retrieve": "off"})]:
        s, dt, js, h = call(c, "POST", "/chat/completions", {"model": FAST, "messages": [{"role": "user", "content": q}]},
                            extra_headers={"X-Moss-Indexes": "agent-memory-context", "X-Moss-Cache": "off", **extra})
        u = js.get("usage") or {}
        rec(f"retrieval.{label}", None, f"{s} retrieve_ms={h.get('x-moss-retrieve-ms')} prompt_tokens={u.get('prompt_tokens')} "
            f"steps={js.get('moss_tool_steps')} reply={str((js.get('choices') or [{}])[0].get('message', {}).get('content'))[:220]!r}")
    s, dt, js, h = call(c, "POST", "/responses", {"model": FAST, "input": q, "tools": [{"type": "moss_search"}]},
                        extra_headers={"X-Moss-Indexes": "agent-memory-context", "X-Moss-Cache": "off"})
    rec("retrieval.moss_search_tool", s == 200, f"{s} output_types={[o.get('type') for o in js.get('output', [])]} "
        f"text={str(js.get('output_text') or js.get('error'))[:200]!r}")

    md = ["| test | observed | pass |", "|---|---|---|"]
    md += [f"| {n} | {str(o).replace('|', '/')[:300]} | {'yes' if ok else ('NO' if ok is False else 'n/a')} |" for n, o, ok in rows]
    (ROOT / "logs" / "api_probe_summary.md").write_text("\n".join(md), encoding="utf-8")



def moss_search_tool():
    # the tool wants its own index list
    L2 = Logger("api_probe_moss_search")
    with httpx.Client(timeout=60) as c:
        q = "What topics are covered in the stored documents? Name three specific facts."
        for label, tool, extra in [("tool_indexes", {"type": "moss_search", "indexes": ["agent-memory-context"]}, {}),
                                   ("tool_bad_index", {"type": "moss_search", "indexes": ["no-such-index"]}, {})]:
            s, _, js, _ = call(c, "POST", "/responses", {"model": FAST, "input": q, "tools": [tool]},
                               extra_headers={"X-Moss-Cache": "off", **extra})
            out = [o.get("type") for o in js.get("output", [])]
            note = f"{s} output_types={out} usage={js.get('usage')} text={str(js.get('output_text') or js.get('error'))[:200]!r}"
            L2.log({"test": f"retrieval.moss_search.{label}", "note": note, "output": js.get("output")})
            print(label, note[:380])


if __name__ == "__main__":
    main()
    moss_search_tool()
