import json
import pathlib
import sys
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import BASE, Logger, headers  # noqa: E402

import httpx  # noqa: E402

L = Logger("stream_abort")


def main():
    # read 20 chunks of a long story then hang up and record the moss id
    body = {"model": "moss/fastlane-1", "stream": True, "stream_options": {"include_usage": True},
            "messages": [{"role": "user", "content": f"Write a 1500 word story about a lighthouse. ({uuid.uuid4().hex[:6]})"}]}
    with httpx.Client(timeout=60) as c:
        got = 0
        with c.stream("POST", BASE + "/chat/completions", headers=headers({"X-Moss-Cache": "off"}), json=body) as r:
            rid = r.headers.get("x-moss-request-id")
            for line in r.iter_lines():
                got += line.startswith("data:")
                if got >= 20:
                    break
    L.log({"moss_request_id": rid, "chunks_read": got})
    print(json.dumps({"moss_request_id": rid, "chunks_read": got}))


if __name__ == "__main__":
    main()
