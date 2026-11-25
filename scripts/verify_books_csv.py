import csv
import html
import io
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import BASE, ROOT, headers  # noqa: E402

import httpx  # noqa: E402

TID = sys.argv[1] if len(sys.argv) > 1 else "task_55718fbd6ea84310a31cfdc542deb3d7"


def main():
    # compare the csv the agent wrote with a direct scrape of all 50 pages
    with httpx.Client(timeout=60) as c:
        r = c.get(f"{BASE}/tasks/{TID}/files/outputs/books.csv", headers=headers())
        (ROOT / "logs" / "tasks" / f"{TID}_books.csv").write_bytes(r.content)
        rows = list(csv.DictReader(io.StringIO(r.content.decode("utf-8-sig"))))
        truth = set()
        for p in range(1, 51):
            page = c.get(f"https://books.toscrape.com/catalogue/page-{p}.html").text
            for title, price in re.findall(r'<h3><a href="[^"]+" title="([^"]+)">.*?<p class="price_color">([^<]+)</p>', page, re.S):
                truth.add((html.unescape(title), price.replace("Â", "")))
    got = {(row.get("title"), (row.get("price") or "").replace("Â", "")) for row in rows}
    res = {"task": TID, "truth_rows": len(truth), "agent_rows": len(rows), "exact_matches": len(truth & got)}
    (ROOT / "logs" / "books_csv_verification.json").write_text(json.dumps(res))
    print(res)


if __name__ == "__main__":
    main()
