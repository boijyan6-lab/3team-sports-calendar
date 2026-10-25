#!/usr/bin/env python3
"""Conservative official Yakult schedule updater: only future games with confirmed start times."""
import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

JST = timezone(timedelta(hours=9))
OUT = Path("fixtures_yakult.json")
TEAMS = ("ヤクルト", "DeNA", "阪神", "巨人", "中日", "広島")
VENUES = ("神宮", "横浜", "東京ドーム", "甲子園", "マツダ", "バンテリンドーム",
          "ナゴヤドーム", "ZOZOマリン", "ベルーナドーム", "京セラD大阪",
          "京セラドーム", "エスコン", "楽天モバイル", "坊っちゃん", "ほっともっと")
DATE = re.compile(r"\b(\d{1,2})\s*[・.]\s*(\d{1,2})\s+(?:MON|TUE|WED|THU|FRI|SAT|SUN)\s+(20\d{2})\b")
TIME = re.compile(r"(?<!\d)([01]?\d|2[0-3]):([0-5]\d)(?!\d)")

class Cards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.cards = []
    def handle_starttag(self, tag, attrs):
        if tag == "li":
            if not self.depth:
                self.parts = []
            self.depth += 1
        elif self.depth and tag in ("div", "p", "br"):
            self.parts.append(" ")
    def handle_endtag(self, tag):
        if tag == "li" and self.depth:
            self.depth -= 1
            if not self.depth:
                value = " ".join("".join(self.parts).split())
                if "セ・リーグ公式戦" in value and "ヤクルト" in value:
                    self.cards.append(value)
    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)

def parse(card, today):
    d = DATE.search(card)
    if not d:
        return None
    month, day, year = map(int, d.groups())
    try:
        iso = datetime(year, month, day, tzinfo=JST).date().isoformat()
    except ValueError:
        return None
    if iso < today or "セ・リーグ公式戦" not in card:
        return None
    body = card.split("セ・リーグ公式戦", 1)[1].strip()
    home_match = re.match(r"(ヤクルト|DeNA|阪神|巨人|中日|広島)(?!\w)", body)
    if not home_match:
        return None
    home = home_match.group(1)
    venue = next((v for v in VENUES if v in body), "")
    if not venue:
        return None
    after_venue = body.split(venue, 1)[1]
    # Require an opponent/team name after the venue, not just a name in navigation text.
    after_teams = re.findall(r"ヤクルト|DeNA|阪神|巨人|中日|広島", after_venue)
    if not after_teams:
        return None
    visitor = after_teams[0]
    if home == visitor or "ヤクルト" not in (home, visitor):
        return None
    # The completed-game result replaces the scheduled start time. Never invent it.
    time_match = TIME.search(after_venue)
    if not time_match or "試合終了" in after_venue or "試合中止" in after_venue:
        return None
    start = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
    ha = "H" if home == "ヤクルト" else "A"
    opponent = visitor if ha == "H" else home
    return {"date": iso, "time": start, "team": "yakult", "teamLabel": "ヤクルト",
            "comp": "セ・リーグ", "opp": opponent, "ha": ha, "venue": venue,
            "watch": "未定"}

def main():
    now = datetime.now(JST)
    today = now.date().isoformat()
    months = []
    for offset in range(15):
        index = now.year * 12 + now.month - 1 + offset
        year, m0 = divmod(index, 12)
        months.append((year, m0 + 1))
    found = {}
    fetched = 0
    for year, month in months:
        url = f"https://www.yakult-swallows.co.jp/game/{year}{month:02d}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=18) as resp:
                html = resp.read(3_000_000).decode("utf-8", "replace")
            cards = Cards()
            cards.feed(html)
            fetched += 1
            count = 0
            for card in cards.cards:
                item = parse(card, today)
                if item:
                    found[(item["date"], item["opp"], item["ha"])] = item
                    count += 1
            print(f"{year}-{month:02d}: {len(cards.cards)} cards, {count} confirmed future games", flush=True)
        except Exception as exc:
            print(f"WARNING {year}-{month:02d}: {type(exc).__name__}: {exc}", flush=True)
    if not fetched:
        raise RuntimeError("No official pages reachable; existing JSON preserved")
    existing = []
    if OUT.exists():
        try:
            existing = json.loads(OUT.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            raise RuntimeError("Existing JSON invalid; refusing to overwrite")
    # Preserve previously confirmed games when the website temporarily hides times.
    for item in existing:
        if (isinstance(item, dict) and item.get("team") == "yakult"
                and isinstance(item.get("date"), str) and item["date"] >= today
                and item.get("time") and item.get("opp") and item.get("ha") in ("H", "A")):
            key = (item["date"], item["opp"], item["ha"])
            found.setdefault(key, item)
    if not found:
        print("No confirmed future games; leaving existing JSON unchanged.", flush=True)
        return
    data = sorted(found.values(), key=lambda x: (x["date"], x["time"], x["opp"]))
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(data)} confirmed future Yakult games", flush=True)

if __name__ == "__main__":
    main()
