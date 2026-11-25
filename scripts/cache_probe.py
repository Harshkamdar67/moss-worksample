import pathlib
import sys
import time
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import Logger, call  # noqa: E402

import httpx  # noqa: E402

L = Logger("cache_probe")
WEATHER = [{"type": "function", "function": {"name": "get_weather",
            "parameters": {"type": "object", "properties": {"city": {"type": "string"}}}}}]


def chat(c, body):
    s, dt, js, h = call(c, "POST", "/chat/completions", body)
    text = js["choices"][0]["message"]["content"] if s == 200 else None
    return dict(status=s, dt=round(dt, 3), usage=js.get("usage"), text=text, id=js.get("id"), headers=h)


def hit(r):
    # a reply cache hit reports zero prompt tokens
    return (r["usage"] or {}).get("prompt_tokens") == 0


def m(text, model="moss/fastlane-1", **kw):
    return {"model": model, "messages": [{"role": "user", "content": text}], **kw}


def sys_msg(system, text):
    return {"model": "moss/fastlane-1", "messages": [{"role": "system", "content": system}, {"role": "user", "content": text}]}


def nonce():
    return uuid.uuid4().hex[:8]


def main():
    # each case is a pair of requests that differ in one field
    pairs = [
        ("random prompt temperature 1.0", lambda t: (m(t, temperature=1.0), m(t, temperature=1.0)),
         "Pick a random integer between 1 and 1000000. Reply with only the number."),
        ("temperature 0 vs 1.5", lambda t: (m(t, temperature=0), m(t, temperature=1.5)),
         "Write a one-line, wildly creative haiku about rain."),
        ("max_tokens 200 vs 5", lambda t: (m(t, max_tokens=200), m(t, max_tokens=5)), "List three fruits."),
        ("system prompt differs", lambda t: (sys_msg("Answer in French.", t), sys_msg("Answer in German.", t)), "Describe a cat."),
        ("model fastlane vs luna", lambda t: (m(t), m(t, model="openai/gpt-6-luna")), "Say hello."),
        ("trailing whitespace", lambda t: (m(t), m(t + "  ")), "What's 17*23?"),
        ("case differs", lambda t: (m(t), m(t.upper())), "Name a color."),
        ("n 1 vs 2", lambda t: (m(t), m(t, n=2)), "Explain gravity in 2 sentences."),
        ("user field differs", lambda t: (m(t, user="alice"), m(t, user="bob")), "Give me a fact about owls."),
        ("response_format differs", lambda t: (m(t), m(t, response_format={"type": "json_object"})), "Write JSON with a key 'a'."),
        ("tools present vs absent", lambda t: (m(t), m(t, tools=WEATHER)), "What's the weather in Rome?"),
    ]
    with httpx.Client() as c:
        for name, build, text in pairs:
            a, b = build(f"{text} ({nonce()})")
            ra, rb = chat(c, a), chat(c, b)
            L.log(dict(case=name, a=ra, b=rb, b_cache_hit=hit(rb), same_text=ra["text"] == rb["text"]))
            print(f"{name:32s} hit={hit(rb)!s:5s} same_text={ra['text'] == rb['text']!s:5s} "
                  f"a_ct={(ra['usage'] or {}).get('completion_tokens')} b_ct={(rb['usage'] or {}).get('completion_tokens')} "
                  f"a={ra['dt']}s b={rb['dt']}s")

        # does the entry survive past a minute
        a = m(f"Current time-sensitive: what is today's date? ({nonce()})")
        r1 = chat(c, a)
        time.sleep(65)
        r2 = chat(c, a)
        L.log(dict(case="ttl over 65s", a=r1, b=r2, b_cache_hit=hit(r2)))
        print(f"{'same request after 65s':32s} hit={hit(r2)}")


if __name__ == "__main__":
    main()
