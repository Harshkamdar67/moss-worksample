import pathlib
import sys
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import Logger, call  # noqa: E402

import httpx  # noqa: E402

L = Logger("token_overhead")


def main():
    with httpx.Client() as c:
        # prompt tokens billed for a two word message with the project prompt on and off
        for model in ["moss/fastlane-1", "openai/gpt-6-luna", "anthropic/claude-haiku-5.5"]:
            for sp in ["on", "off"]:
                body = {"model": model, "max_tokens": 5, "messages": [{"role": "user", "content": f"Hi {uuid.uuid4().hex[:6]}"}]}
                s, _, js, _ = call(c, "POST", "/chat/completions", body,
                                   extra_headers={"X-Moss-System-Prompt": sp, "X-Moss-Cache": "off"})
                L.log({"model": model, "system_prompt": sp, "status": s, "usage": js.get("usage"), "err": js.get("error")})
                print(model, "system prompt", sp, s, (js.get("usage") or {}).get("prompt_tokens"))

        # params the docs say are refused on the moss key
        for model in ["moss/fastlane-1", "openai/gpt-6-luna", "deepseek/deepseek-v4.1-flash"]:
            for p, v in [("seed", 7), ("frequency_penalty", 0.5), ("logit_bias", {"1": 5})]:
                body = {"model": model, "max_tokens": 5, p: v, "messages": [{"role": "user", "content": "hi"}]}
                s, _, js, _ = call(c, "POST", "/chat/completions", body)
                L.log({"model": model, "param": p, "status": s, "err": js.get("error")})
                print(model, p, s, (js.get("error") or {}).get("code"))


if __name__ == "__main__":
    main()
