#!/usr/bin/env python3
"""Read-only Yakult official schedule-to-JSON preview. Never changes published data."""
import json
import re
import urllib.request
from datetime import date
from html.parser import HTMLParser

URL = 'https://www.yakult-swallows.co.jp/game/broadcast/202610'

class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        if tag in ('div', 'li', 'tr', 'section', 'article', 'p', 'h2', 'h3'):
            self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1
        if tag in ('div', 'li', 'tr', 'section', 'article', 'p', 'h2', 'h3'):
            self.parts.append('\n')
    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(' ' + ' '.join(data.split()) + ' ')

def extract(html):
    reader = Reader()
    reader.feed(html)
    lines = [' '.join(s.split()) for s in ''.join(reader.parts).splitlines()]
    lines = [s for s in lines if s]
    found = []
    # Example observed in live GitHub Actions log:
    # '10 ・ 2 FRI 2026 JERA セ・リーグ公式戦 神宮', 'vs 巨人', '18:00 試合開始'
    date_re = re.compile(r'(?<!\d)(\d{1,2})\s*[・./]\s*(\d{1,2})\s+(?:MON|TUE|WED|THU|FRI|SAT|SUN)\s+(20\d{2})\b', re.I)
    for i, line in enumerate(lines):
        match = date_re.search(line)
        if not match:
            continue
        month, day, year = map(int, (match.group(1), match.group(2), match.group(3)))
        try:
            iso = date(year, month, day).isoformat()
        except ValueError:
            continue
        window = ' '.join(lines[i:i+7])
        opp = re.search(r'\bvs\s+(巨人|中日|広島|阪神|DeNA|ＤｅＮＡ|横浜|ヤクルト|日本ハム|楽天|西武|ロッテ|オリックス|ソフトバンク)\b', window)
        start = re.search(r'\b([01]?\d|2[0-3]):([0-5]\d)\s*試合開始', window)
        if not opp or not start:
            print('SKIP (incomplete):', iso, window[:180])
            continue
        opponent = opp.group(1)
        if opponent == 'ヤクルト':
            continue
        venue = ''
        for name in ('神宮', '東京ドーム', '横浜', '甲子園', 'マツダ', 'バンテリンドーム', '京セラD大阪', 'ZOZOマリン', 'ベルーナドーム', 'エスコンF', '楽天モバイル', 'PayPayドーム'):
            if name in line:
                venue = name
                break
        # Home/away cannot safely be inferred from venue for neutral-site games.
        # This is a PREVIEW, not production calendar data.
        found.append({'date': iso, 'time': f'{int(start.group(1)):02d}:{start.group(2)}', 'opp': opponent, 'venue': venue, 'source': URL})
    return list({(e['date'], e['opp']): e for e in found}.values())

def main():
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'ja-JP,ja;q=0.9'})
    with urllib.request.urlopen(req, timeout=25) as response:
        html = response.read(3_000_000).decode('utf-8', 'replace')
        print('HTTP:', response.status, 'HTML characters:', len(html))
    fixtures = extract(html)
    print('Parsed fixtures:', len(fixtures))
    print(json.dumps(fixtures, ensure_ascii=False, indent=2))
    if not fixtures:
        raise RuntimeError('No fixture records parsed. Existing site remains unchanged.')
    print('PREVIEW ONLY: no JSON file or website was modified.')

if __name__ == '__main__':
    main()
