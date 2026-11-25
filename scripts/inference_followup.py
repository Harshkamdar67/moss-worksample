import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import Logger  # noqa: E402
from inference_ai import FAST, NOCACHE, WEATHER, call, chat, haystack, user  # noqa: E402

import httpx  # noqa: E402

L = Logger("inference_followup")


def main():
    with httpx.Client() as c:
        # haystacks sized at about 1.5 tokens per word to land under each limit
        for model, words, pos in [(FAST, 165_000, 0.5), (FAST, 165_000, 0.95), ("openai/gpt-6-luna", 80_000, 0.5),
                                  ("anthropic/claude-haiku-5.5", 40_000, 0.5)]:
            code = str(random.Random(words + int(pos * 100)).randint(100000, 999999))
            s, dt, js, m = chat(c, model, user(haystack(words, pos, code) + "\n\nWhat is the secret vault code? Reply with only the code."), max_tokens=20)
            note = f"{s} found={code in str(m.get('content'))} prompt_tokens={(js.get('usage') or {}).get('prompt_tokens')} {dt:.1f}s {str(js.get('error') or m.get('content'))[:120]}"
            L.log({"test": f"longctx.{model}.{words}w@{pos}", "note": note})
            print(f"longctx {model} {words}w@{pos}: {note}")

        # what haiku returns when told not to use tools
        s, _, js, m = chat(c, "anthropic/claude-haiku-5.5", user("What's the weather in Paris?"), tools=[WEATHER], tool_choice="none")
        note = f"{s} finish={(js.get('choices') or [{}])[0].get('finish_reason')} content={m.get('content')!r} tool_calls={m.get('tool_calls')} usage={js.get('usage')}"
        L.log({"test": "haiku.tool_choice_none", "note": note})
        print("haiku tool_choice none:", note[:400])

        # the one question fastlane missed
        q = "How many prime numbers are there between 1 and 50? Think briefly, then put only the final number on the last line."
        for i in range(3):
            s, _, js, m = chat(c, FAST, user(q), max_tokens=600)
            L.log({"test": f"fastlane.primes.{i}", "reply": m.get("content")})
            print(f"fastlane primes run {i}: ...{str(m.get('content'))[-160:]!r}")


if __name__ == "__main__":
    main()
