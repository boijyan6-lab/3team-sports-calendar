#!/usr/bin/env python3
"""Read-only probe of NPB official schedule pages. Does not update the calendar."""
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser

class ScheduleTable(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None
    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []
    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)
    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None

def probe(year, month):
    url = f"https://npb.jp/games/{year}/schedule_{month:02d}_detail.html"
    print("URL:", url, flush=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            page = response.read(4_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        if year == 2027 and exc.code == 404:
            print("2027 page not published yet (HTTP 404); this is expected.", flush=True)
            return
        raise
    parser = ScheduleTable()
    parser.feed(page)
    print("HTML table rows:", len(parser.rows), flush=True)
    hits = [row for row in parser.rows if any("ヤクルト" in cell for cell in row)]
    print("Rows mentioning Yakult:", len(hits), flush=True)
    for row in hits[:8]:
        print(" | ".join(row)[:320], flush=True)
    if year == 2026 and month == 3 and not hits:
        raise RuntimeError("Known 2026 March Yakult games not found; inspect NPB HTML structure")
    if year == 2027 and not hits:
        print("No 2027 fixtures detected; no data will be published.", flush=True)

def main():
    probe(2026, 3)  # Known games: validates the extractor against published data.
    probe(2027, 3)  # Future schedule: may be absent, which is not an error.
    print("Read-only NPB probe completed. No files changed.", flush=True)

if __name__ == "__main__":
    main()
