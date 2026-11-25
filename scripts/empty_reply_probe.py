import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import Logger  # noqa: E402
from inference_ai import chat, haystack, user  # noqa: E402

import httpx  # noqa: E402

L = Logger("empty_reply_probe")


def main():
    # raw responses for long prompts that came back empty
    with httpx.Client() as c:
        for model, words in [("openai/gpt-6-luna", 80_000), ("openai/gpt-6-luna", 40_000), ("openai/gpt-6-luna", 10_000),
                             ("anthropic/claude-haiku-5.5", 40_000), ("anthropic/claude-haiku-5.5", 25_000),
                             ("anthropic/claude-haiku-5.5", 10_000)]:
            code = str(random.Random(words).randint(100000, 999999))
            s, dt, js, m = chat(c, model, user(haystack(words, 0.5, code) + "\n\nWhat is the secret vault code? Reply with only the code."), max_tokens=20)
            ch = (js.get("choices") or [{}])[0]
            rec = {"model": model, "words": words, "status": s, "finish": ch.get("finish_reason"), "content": m.get("content"),
                   "usage": js.get("usage"), "error": js.get("error"), "found": code in str(m.get("content"))}
            L.log(rec)
            print(json.dumps(rec)[:330])


if __name__ == "__main__":
    main()
