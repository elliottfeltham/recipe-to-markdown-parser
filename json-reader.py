"""Small debugging utility for inspecting a page's JSON-LD blocks."""

import argparse
import html
import json

import requests
from bs4 import BeautifulSoup


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    args = parser.parse_args()
    response = requests.get(
        args.url,
        timeout=10,
        headers={"User-Agent": "recipe-to-markdown-parser/1.0"},
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(html.unescape(tag.get_text() or ""))
        except json.JSONDecodeError:
            continue
        print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
