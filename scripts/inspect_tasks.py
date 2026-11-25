import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import ROOT, call  # noqa: E402

import httpx  # noqa: E402


def main(ids):
    out = ROOT / "logs" / "tasks"
    out.mkdir(parents=True, exist_ok=True)
    with httpx.Client() as c:
        for tid in ids:
            s, _, js, _ = call(c, "GET", f"/tasks/{tid}")
            (out / f"{tid}.json").write_text(json.dumps(js, indent=2))
            u = js.get("usage") or {}
            print(tid, s, js.get("status"), js.get("error"), u.get("cost"), u.get("steps"),
                  str((js.get("result") or {}).get("output_text"))[:200])


if __name__ == "__main__":
    main(sys.argv[1:])
