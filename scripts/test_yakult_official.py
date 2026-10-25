#!/usr/bin/env python3
"""Read-only connectivity and HTML inspection of the official Yakult Swallows website."""
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser

URLS = [
    "https://www.yakult-swallows.co.jp/game",
    "https://www.yakult-swallows.co.jp/",
]

class TextReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(" ".join(data.split()))

def main():
    successes = 0
    for url in URLS:
        print("Checking:", url, flush=True)
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "ja-JP,ja;q=0.9"}
            )
            with urllib.request.urlopen(request, timeout=12) as response:
                data = response.read(2_000_000)
                print("HTTP:", response.status, "Bytes:", len(data), "Final URL:", response.url, flush=True)
            html = data.decode("utf-8", "replace")
            parser = TextReader()
            parser.feed(html)
            text = " ".join(parser.parts)
            for term in ("2026", "2027", "試合日程", "ヤクルト"):
                print("Contains", term, ":", term in text, flush=True)
            print("Text sample:", text[:400], flush=True)
            successes += 1
        except Exception as exc:
            print("FAILED:", type(exc).__name__, str(exc), flush=True)
    if not successes:
        raise RuntimeError("Official website could not be reached from GitHub Actions")
    print("PASS: official website reachable; schedule parsing not yet validated.", flush=True)
    print("No calendar files were changed.", flush=True)

if __name__ == "__main__":
    main()
