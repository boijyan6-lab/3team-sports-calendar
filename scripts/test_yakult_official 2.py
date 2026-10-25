#!/usr/bin/env python3
"""Read-only diagnostic of Yakult's official monthly broadcast/schedule page."""
from html.parser import HTMLParser
import re
import urllib.request

URLS = [
    "https://www.yakult-swallows.co.jp/game/broadcast/202609",
    "https://www.yakult-swallows.co.jp/game/broadcast/202610",
]

class Inspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = {}
        self.lines = []
        self.current = []
    def handle_starttag(self, tag, attrs):
        self.tags[tag] = self.tags.get(tag, 0) + 1
        if tag in ("div", "li", "article", "section", "tr"):
            self.flush()
    def handle_data(self, data):
        text = " ".join(data.split())
        if text:
            self.current.append(text)
    def handle_endtag(self, tag):
        if tag in ("div", "li", "article", "section", "tr"):
            self.flush()
    def flush(self):
        if self.current:
            self.lines.append(" ".join(self.current))
            self.current = []

def main():
    success = 0
    for url in URLS:
        print("\nURL:", url, flush=True)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                html = resp.read(3_000_000).decode("utf-8", "replace")
                print("HTTP:", resp.status, "bytes:", len(html), flush=True)
            inspector = Inspector()
            inspector.feed(html)
            inspector.flush()
            print("Tag counts:", inspector.tags, flush=True)
            interesting = [
                line for line in inspector.lines
                if ("試合開始" in line or "vs" in line or "2026" in line)
                and len(line) < 350
            ]
            print("Candidate lines:", len(interesting), flush=True)
            for line in interesting[:35]:
                print("  ", line[:250], flush=True)
            if "18:00" in html and ("巨人" in html or "広島" in html):
                success += 1
                print("PASS: expected 2026 schedule markers found", flush=True)
            else:
                print("WARNING: schedule markers missing; parsing needs review", flush=True)
        except Exception as exc:
            print("ERROR:", type(exc).__name__, str(exc), flush=True)
    if not success:
        raise RuntimeError("No known monthly schedule could be verified")
    print("Read-only diagnostic finished. No published files changed.", flush=True)

if __name__ == "__main__":
    main()
