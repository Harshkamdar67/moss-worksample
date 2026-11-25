import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import Logger, call  # noqa: E402

import httpx  # noqa: E402

L = Logger("context_estimate_probe")
NOCACHE = {"X-Moss-Cache": "off"}


def ask(c, words):
    return call(c, "POST", "/chat/completions", {"model": "moss/fastlane-1", "max_tokens": 3,
                "messages": [{"role": "user", "content": " ".join(["paper"] * words)}]}, extra_headers=NOCACHE)


def main():
    with httpx.Client(timeout=180) as c:
        # the precheck estimate against the real token count on both sides of the cutoff
        for words in [170_000, 174_000, 176_000, 200_000]:
            s, dt, js, h = ask(c, words)
            note = {"words": words, "status": s, "real_prompt_tokens": (js.get("usage") or {}).get("prompt_tokens"),
                    "error": (js.get("error") or {}).get("message")}
            L.log(note)
            print(note)
        # four 170k prompts inside one minute against the 600k tokens per minute limit
        out = []
        for _ in range(4):
            s, dt, js, h = ask(c, 170_000)
            out.append((s, (js.get("usage") or {}).get("prompt_tokens"), (js.get("error") or {}).get("code"),
                        h.get("x-ratelimit-remaining-tokens"), h.get("retry-after"), round(dt, 1)))
        L.log({"test": "tokenlimit.4x170k", "out": out})
        print("tokenlimit", out)


if __name__ == "__main__":
    main()
