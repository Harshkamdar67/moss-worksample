import json
import pathlib
import re

import httpx

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOOKS = "https://books.toscrape.com/catalogue"


def main():
    # plain scraping with no model so the task answers can be checked against facts
    c = httpx.Client(timeout=30, follow_redirects=True)
    gt = {}

    h = c.get(f"{BOOKS}/category/books/poetry_23/index.html").text
    items = re.findall(r'title="([^"]+)">.*?<p class="price_color">£([\d.]+)', h, re.S)
    gt["poetry_count"] = int(re.search(r"<strong>(\d+)</strong> results", h).group(1))
    gt["poetry_most_expensive"] = max(items, key=lambda x: float(x[1]))

    h = c.get(f"{BOOKS}/tipping-the-velvet_999/index.html").text
    gt["tipping_price"] = re.search(r'<p class="price_color">([^<]+)', h).group(1)

    count, page, first = 0, 1, None
    while True:
        h = c.get(f"https://quotes.toscrape.com/page/{page}/").text
        authors = re.findall(r'<small class="author" itemprop="author">([^<]+)', h)
        if not authors:
            break
        if page == 1:
            first = re.search(r'<span class="text" itemprop="text">(.+?)</span>', h).group(1)
        count += authors.count("Albert Einstein")
        page += 1
    gt.update(einstein_count=count, first_quote=first, pages=page - 1)

    (ROOT / "logs" / "ground_truth.json").write_text(json.dumps(gt, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(gt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
