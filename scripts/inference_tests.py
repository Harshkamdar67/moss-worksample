import asyncio
import json
import pathlib
import statistics
import sys
import time
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import AUTH, BASE, PID, PKEY, ROOT, Logger, call, headers, pick_headers  # noqa: E402

import httpx  # noqa: E402

GROUPS = sorted(sys.argv[1:]) or ["burst", "caching", "errors", "functional", "models", "streaming"]
L = Logger("inference_" + "_".join(GROUPS))
rows = []
Q = "In one short sentence: what is the capital of Australia?"
FAST = "moss/fastlane-1"


def rec(name, expect, status, dt, js, hdrs, ok=None, note=""):
    excerpt = json.dumps(js)[:600]
    L.log({"test": name, "expect": expect, "status": status, "latency_s": round(dt, 3),
           "headers": hdrs, "body_excerpt": excerpt, "note": note})
    rows.append((name, expect, f"{status} in {dt:.2f}s {note}".strip(), ok))
    mark = "OK " if ok else ("BAD" if ok is False else "?? ")
    print(f"[{mark}] {name}: {status} {dt:.2f}s {note} :: {excerpt[:160]}")


def msg(text, model=FAST, **kw):
    return {"model": model, "messages": [{"role": "user", "content": text}], **kw}


def chat_text(js):
    try:
        return js["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None


def err_code(js):
    e = js.get("error") if isinstance(js, dict) else None
    return (e.get("code") or e.get("type")) if isinstance(e, dict) else None


def functional(c):
    s, dt, js, h = call(c, "POST", "/responses", {"model": FAST, "input": Q})
    out = "".join(p.get("text", "") for o in js.get("output", []) for p in o.get("content") or [])
    rec("responses.basic", "200 + text", s, dt, js, h, s == 200 and bool(out), f"text={out!r:.80}")

    s, dt, js, h = call(c, "POST", "/responses", {"input": Q})
    rec("responses.default_model", "200 model=moss/fastlane-1", s, dt, js, h, s == 200, f"model={js.get('model')}")

    s, dt, js, h = call(c, "POST", "/chat/completions", msg(Q))
    rec("chat.basic", "200 + usage", s, dt, js, h, s == 200 and "usage" in js,
        f"text={chat_text(js)!r:.80} usage={js.get('usage')}")

    s, dt, js, h = call(c, "POST", "/chat/completions", msg(Q, model="moss"))
    rec("chat.alias_moss", "200 deprecated alias", s, dt, js, h, s == 200, f"model={js.get('model')}")

    schema = {"type": "json_schema", "json_schema": {"name": "city", "strict": True, "schema": {
        "type": "object", "additionalProperties": False,
        "properties": {"city": {"type": "string"}, "country": {"type": "string"}, "population_millions": {"type": "number"}},
        "required": ["city", "country", "population_millions"]}}}
    s, dt, js, h = call(c, "POST", "/chat/completions", msg("Give me data on the capital of Japan.", response_format=schema))
    try:
        parsed = json.loads(chat_text(js))
        valid = set(parsed) == {"city", "country", "population_millions"}
    except (TypeError, ValueError):
        parsed, valid = None, False
    rec("chat.json_schema", "valid json matching schema", s, dt, js, h, s == 200 and valid, f"parsed={parsed}")

    tools = [{"type": "function", "function": {"name": "get_weather", "description": "Weather for a city",
              "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]
    ask = "What's the weather in Paris right now?"
    s, dt, js, h = call(c, "POST", "/chat/completions", msg(ask, tools=tools))
    tc = (js.get("choices") or [{}])[0].get("message", {}).get("tool_calls")
    rec("chat.tool_call", "tool_calls get_weather paris", s, dt, js, h, bool(tc), f"tool_calls={tc}")
    if tc:
        # send the tool result back and check the model uses it
        history = [{"role": "user", "content": ask}, js["choices"][0]["message"],
                   {"role": "tool", "tool_call_id": tc[0]["id"], "content": json.dumps({"temp_c": 14, "sky": "rain"})}]
        s, dt, js2, h = call(c, "POST", "/chat/completions", {"model": FAST, "tools": tools, "messages": history})
        t = chat_text(js2) or ""
        rec("chat.tool_loop_round2", "answer uses 14c rain", s, dt, js2, h, s == 200 and "14" in t, f"text={t!r:.100}")

    history = [{"role": "user", "content": "My name is Zorblat. Remember it."},
               {"role": "assistant", "content": "Got it, Zorblat."},
               {"role": "user", "content": "What is my name? One word."}]
    s, dt, js, h = call(c, "POST", "/chat/completions", {"model": FAST, "messages": history})
    t = chat_text(js) or ""
    rec("chat.multiturn", "says zorblat", s, dt, js, h, "zorblat" in t.lower(), f"text={t!r:.60}")

    s, dt, js, h = call(c, "POST", "/chat/completions", msg("Who are you? One sentence."),
                        extra_headers={"X-Moss-System-Prompt": "off"})
    rec("chat.system_prompt_off", "200", s, dt, js, h, s == 200, f"text={chat_text(js)!r:.100}")

    s, dt, js, h = call(c, "POST", "/chat/completions",
                        msg("What does the stored agent memory say? Summarize in 2 sentences."),
                        extra_headers={"X-Moss-Indexes": "agent-memory-context"})
    has_ms = any(k.lower() == "x-moss-retrieve-ms" for k in h)
    rec("chat.index_retrieval", "200 + x-moss-retrieve-ms", s, dt, js, h, s == 200 and has_ms, f"text={chat_text(js)!r:.120}")

    # the stock openai sdk pointed at moss with no other changes
    try:
        from openai import OpenAI
        oc = OpenAI(base_url=BASE, api_key=AUTH)
        t0 = time.perf_counter()
        r = oc.chat.completions.create(model=FAST, messages=[{"role": "user", "content": Q}])
        rec("openai_sdk.chat", "works unmodified", 200, time.perf_counter() - t0, r.model_dump(), {}, True,
            f"text={r.choices[0].message.content!r:.60}")
        t0 = time.perf_counter()
        r = oc.responses.create(model=FAST, input=Q)
        rec("openai_sdk.responses", "works unmodified", 200, time.perf_counter() - t0, r.model_dump(), {}, True,
            f"output_text={r.output_text!r:.60}")
    except Exception as e:  # noqa: BLE001
        rec("openai_sdk", "works unmodified", "EXC", 0, {"exc": repr(e)}, {}, False)


def caching(c):
    body = msg(f"Name 3 primary colors. nonce={uuid.uuid4()}")
    _, dt1, js1, _ = call(c, "POST", "/chat/completions", body)
    s2, dt2, js2, h2 = call(c, "POST", "/chat/completions", body)
    u2 = js2.get("usage", {})
    rec("cache.reply_cache_hit", "2nd call faster prompt_tokens 0", s2, dt2, js2, h2, u2.get("prompt_tokens") == 0,
        f"1st={dt1:.2f}s usage1={js1.get('usage')} 2nd usage={u2}")
    s3, dt3, js3, h3 = call(c, "POST", "/chat/completions", body, extra_headers={"X-Moss-Cache": "off"})
    rec("cache.reply_cache_off", "full cost again", s3, dt3, js3, h3,
        (js3.get("usage", {}).get("prompt_tokens") or 0) > 0, f"usage={js3.get('usage')}")

    # same long system prompt with a different question each time
    system = "You are a meticulous assistant. " + " ".join(f"Rule {i}: be accurate and cite facts." for i in range(400))
    for i, q in enumerate(["What is 2+2?", "What is 3+3?", "What is 4+4?"]):
        s, dt, js, h = call(c, "POST", "/chat/completions", {"model": FAST, "messages": [
            {"role": "system", "content": system}, {"role": "user", "content": q}]})
        u = js.get("usage", {})
        cached = (u.get("prompt_tokens_details") or {}).get("cached_tokens")
        rec(f"cache.prefix_{i}", "cached_tokens above 0 on calls 2 and 3", s, dt, js, h,
            (cached or 0) > 0 if i else None, f"prompt={u.get('prompt_tokens')} cached={cached}")


async def stream_chat(model, extra=None):
    body = msg("Count from 1 to 20, comma separated.", model=model, stream=True, stream_options={"include_usage": True})
    ttft, chunks, done, usage, text, err = None, 0, False, None, "", None
    async with httpx.AsyncClient(timeout=120) as ac:
        t0 = time.perf_counter()
        async with ac.stream("POST", BASE + "/chat/completions", headers=headers(extra), json=body) as r:
            async for line in r.aiter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    done = True
                    break
                try:
                    j = json.loads(data)
                except ValueError:
                    continue
                err = j.get("error") or err
                usage = j.get("usage") or usage
                for ch in j.get("choices", []):
                    delta = (ch.get("delta") or {}).get("content")
                    if delta:
                        ttft = ttft or time.perf_counter() - t0
                        text += delta
                        chunks += 1
        return dict(status=r.status_code, ttft=ttft, total=time.perf_counter() - t0, chunks=chunks, done=done,
                    usage=usage, text=text, err=err, headers=pick_headers(r))


async def stream_responses():
    events, ttft, text = {}, None, ""
    async with httpx.AsyncClient(timeout=120) as ac:
        t0 = time.perf_counter()
        async with ac.stream("POST", BASE + "/responses", headers=headers(),
                             json={"model": FAST, "stream": True, "input": "Count from 1 to 10."}) as r:
            async for line in r.aiter_lines():
                if line.startswith("event:"):
                    ev = line[6:].strip()
                    events[ev] = events.get(ev, 0) + 1
                elif line.startswith("data:"):
                    try:
                        j = json.loads(line[5:])
                    except ValueError:
                        continue
                    if j.get("type") == "response.output_text.delta":
                        ttft = ttft or time.perf_counter() - t0
                        text += j.get("delta", "")
        return dict(status=r.status_code, ttft=ttft, total=time.perf_counter() - t0, events=events, text=text)


def streaming():
    r = asyncio.run(stream_chat(FAST))
    rec("stream.chat_fastlane", "ttft + done + usage chunk", r["status"], r["total"], r, r["headers"],
        r["done"] and r["usage"] is not None, f"ttft={r['ttft']} chunks={r['chunks']} usage={r['usage']}")
    r = asyncio.run(stream_responses())
    rec("stream.responses", "delta events + response.completed", r["status"], r["total"], r, {},
        "response.completed" in r["events"], f"ttft={r['ttft']} events={r['events']}")


MODELS = [FAST, "openai/gpt-6-luna", "anthropic/claude-haiku-5.5", "google/gemini-3.5-flash-lite", "z-ai/glm-5.3-flash",
          "deepseek/deepseek-v4.1-flash", "qwen/qwen3.8-flash", "minimax/minimax-m3.1-flash", "moonshotai/kimi-k3", "z-ai/glm-5.3"]


def models(n=3):
    # cache off so we time the model and not the cache
    table = []
    for m in MODELS:
        ttfts, totals, errs, usage = [], [], [], None
        for _ in range(n):
            try:
                r = asyncio.run(stream_chat(m, {"X-Moss-Cache": "off"}))
            except httpx.HTTPError as e:
                errs.append(repr(e))
                continue
            if r["status"] != 200 or r["err"] or not r["text"]:
                errs.append(f"{r['status']} {r['err']} text={r['text'][:40]!r}")
            else:
                ttfts.append(r["ttft"])
                totals.append(r["total"])
                usage = r["usage"]
        row = dict(model=m, ok=len(ttfts), n=n, usage=usage, errors=errs[:2],
                   ttft_p50=round(statistics.median(ttfts), 3) if ttfts else None,
                   total_p50=round(statistics.median(totals), 3) if totals else None)
        table.append(row)
        rec(f"models.{m}", f"{n}/{n} streams ok", 200 if ttfts else "ERR", row["total_p50"] or 0, row, {},
            len(ttfts) == n, f"ttft_p50={row['ttft_p50']} total_p50={row['total_p50']} errs={errs[:1]}")
    (ROOT / "logs" / "model_matrix.json").write_text(json.dumps(table, indent=2))


def errors(c):
    m = [{"role": "user", "content": "hi"}]
    chat = "/chat/completions"
    cases = [
        ("err.no_auth", "401", "POST", chat, msg("hi"), {"auth": None}),
        ("err.bad_key", "401", "POST", chat, msg("hi"), {"auth": f"{PID}:moss_deadbeef"}),
        ("err.key_only_no_project", "401", "POST", chat, msg("hi"), {"auth": PKEY}),
        ("err.swapped_id_key", "401", "POST", chat, msg("hi"), {"auth": f"{PKEY}:{PID}"}),
        ("err.unknown_model", "400", "POST", chat, msg("hi", model="moss/does-not-exist"), {}),
        ("err.vendor_native_no_byok", "400", "POST", chat, msg("hi", model="gpt-6-luna"), {}),
        ("err.bad_byok_key", "401", "POST", chat, msg("hi", model="gpt-6-luna"),
         {"extra_headers": {"X-Moss-Provider-Key": "sk-invalid-test"}}),
        ("err.responses_unknown_field", "400", "POST", "/responses", {"model": FAST, "input": "hi", "bogus_field": 1}, {}),
        ("err.responses_previous_id", "400", "POST", "/responses",
         {"model": FAST, "input": "hi", "previous_response_id": "resp_123"}, {}),
        ("err.unsupported_seed", "400", "POST", chat, msg("hi", seed=7), {}),
        ("err.openai_stop", "400", "POST", chat, msg("hi", model="openai/gpt-6-luna", stop=["\n"]), {}),
        ("err.anthropic_temperature", "400", "POST", chat, msg("hi", model="anthropic/claude-haiku-5.5", temperature=0.2), {}),
        ("err.empty_messages", "400", "POST", chat, {"model": FAST, "messages": []}, {}),
        ("err.missing_messages", "400", "POST", chat, {"model": FAST}, {}),
        ("err.bad_role", "400", "POST", chat, {"model": FAST, "messages": [{"role": "wizard", "content": "hi"}]}, {}),
        ("err.temperature_out_of_range", "400", "POST", chat, msg("hi", temperature=9), {}),
        ("err.negative_max_tokens", "400", "POST", chat, msg("hi", max_tokens=-5), {}),
        ("err.max_tokens_1", "200", "POST", chat, msg("Write a long poem.", max_tokens=1), {}),
        ("err.malformed_json", "400", "POST", chat, None, {"raw_body": b'{"model": "moss/fastlane-1", "messages": ['}),
        ("err.unknown_index", "403", "POST", chat, msg("hi"), {"extra_headers": {"X-Moss-Indexes": "no-such-index"}}),
        ("err.33_indexes", "400", "POST", chat, msg("hi"),
         {"extra_headers": {"X-Moss-Indexes": ",".join(f"i{i}" for i in range(33))}}),
        ("err.wrong_method_get_chat", "405", "GET", chat, None, {}),
        ("err.unknown_route", "404", "GET", "/does-not-exist", None, {}),
        ("err.path_like_model", "400", "POST", chat, msg("hi", model="../../etc/passwd"), {}),
        ("err.model_wrong_type", "400", "POST", chat, {"model": 123, "messages": m}, {}),
        ("err.content_null", "400", "POST", chat, {"model": FAST, "messages": [{"role": "user", "content": None}]}, {}),
        ("err.unicode_heavy", "200", "POST", chat, msg("Reply OK. " + "\U0001f642\u0000‮" * 200), {}),
    ]
    for name, expect, method, path, body, kw in cases:
        try:
            s, dt, js, h = call(c, method, path, body, **kw)
        except httpx.HTTPError as e:
            rec(name, expect, "EXC", 0, {"exc": repr(e)}, {}, False)
            continue
        extra = ""
        if name == "err.max_tokens_1" and s == 200:
            extra = f" finish={js['choices'][0]['finish_reason']} usage={js.get('usage')}"
        rec(name, expect, s, dt, js, h, str(s) == expect, f"code={err_code(js)}{extra}")

    # big bodies around the documented 4 mb and 262k token limits
    for name, expect, text in [("err.body_over_4mb", 413, "a " * 2_200_000),
                               ("err.body_just_under_4mb", 400, "a " * 1_990_000),
                               ("err.context_length_300k_tokens", 400, "cat " * 300_000)]:
        t0 = time.perf_counter()
        try:
            s, dt, js, h = call(c, "POST", chat, msg(text))
            rec(name, str(expect), s, dt, js, h, s == expect, f"code={err_code(js)} bytes={len(text)}")
        except httpx.HTTPError as e:
            rec(name, str(expect), "EXC", time.perf_counter() - t0, {"exc": repr(e)}, {}, False,
                f"connection error {e!r} bytes={len(text)}")


async def burst(n=25):
    # docs say fastlane allows 10 burst and 120 per minute
    async with httpx.AsyncClient(timeout=120) as ac:
        async def one(i):
            t0 = time.perf_counter()
            r = await ac.post(BASE + "/chat/completions", headers=headers({"X-Moss-Cache": "off"}),
                              json=msg(f"Say {i}", max_tokens=5))
            return r.status_code, time.perf_counter() - t0, pick_headers(r)
        out = await asyncio.gather(*(one(i) for i in range(n)))
    codes = {}
    for s, _, _ in out:
        codes[s] = codes.get(s, 0) + 1
    lat = sorted(t for s, t, _ in out if s == 200)
    hdr429 = next((h for s, _, h in out if s == 429), None)
    p50 = statistics.median(lat) if lat else 0
    rec(f"burst.{n}x_{FAST}", "429 with retry-after past burst 10", "mixed", p50,
        {"codes": codes, "lat_p50": p50, "lat_max": lat[-1] if lat else None, "429_headers": hdr429}, {}, None,
        f"codes={codes} p50={p50:.2f}s max={lat[-1] if lat else 0:.2f}s 429_headers={hdr429}")


def main():
    with httpx.Client() as c:
        if "functional" in GROUPS:
            functional(c)
        if "caching" in GROUPS:
            caching(c)
        if "streaming" in GROUPS:
            streaming()
        if "models" in GROUPS:
            models()
        if "errors" in GROUPS:
            errors(c)
        if "burst" in GROUPS:
            asyncio.run(burst())
    md = ["| test | expected | observed | pass |", "|---|---|---|---|"]
    md += [f"| {n} | {e} | {o.replace('|', '/')[:220]} | {'yes' if ok else ('NO' if ok is False else 'n/a')} |"
           for n, e, o, ok in rows]
    (ROOT / "logs" / f"inference_summary_{'_'.join(GROUPS)}.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
