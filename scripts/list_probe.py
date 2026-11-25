import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import Logger, call  # noqa: E402

import httpx  # noqa: E402

L = Logger("list_probe")
QUERIES = ["", "?limit=2", "?limit=2&after=", "?status=completed&limit=3", "?status=bogus",
           "?limit=0", "?limit=100000", "?order=asc&limit=2"]


def main():
    # the list route works but is not in the docs
    with httpx.Client() as c:
        for q in QUERIES:
            s, _, js, _ = call(c, "GET", "/tasks" + q)
            data = js.get("data") or []
            meta = {k: v for k, v in js.items() if k != "data"}
            L.log({"q": q, "status": s, "n": len(data), "statuses": [d.get("status") for d in data][:5], "meta": meta})
            print(f"{q or '(none)':30s} {s} n={len(data)} meta={meta}")


if __name__ == "__main__":
    main()
