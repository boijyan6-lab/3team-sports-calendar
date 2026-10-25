#!/usr/bin/env python3
"""Conservative J.League Data Site Urawa fixture extractor. Writes JSON only on valid data."""
import json, re, urllib.request
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

URL_TEMPLATE='https://data.j-league.or.jp/SFMS01/search?competition_years={year}&home_away_select=0&team_ids=3'
JST=timezone(timedelta(hours=9))
OUT=Path('fixtures_hachinohe.json')

class TableReader(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.row=None; self.cell=None; self.depth=0
    def handle_starttag(self, tag, attrs):
        if tag=='tr': self.row=[]
        elif tag in ('td','th') and self.row is not None: self.cell=[]
    def handle_data(self,data):
        if self.cell is not None: self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split())); self.cell=None
        elif tag=='tr' and self.row is not None:
            if self.row: self.rows.append(self.row)
            self.row=None

def parse(rows):
    fixtures=[]
    for cells in rows:
        # Official results table: season, competition, round, date, KO, home, score, away, venue, attendance, broadcast.
        if len(cells)<10 or not re.search(r'八戸', ' '.join(cells[5:8])): continue
        if '八戸' not in cells[5] and '八戸' not in cells[7]: continue
        m=re.search(r'(\d{2})/(\d{2})/(\d{2})',cells[3]); t=re.search(r'\b(\d{1,2}):(\d{2})\b',cells[4])
        if not m or not t: continue
        year=2000+int(m.group(1)); month=int(m.group(2)); day=int(m.group(3))
        try: iso=date(year,month,day).isoformat()
        except ValueError: continue
        comp=cells[1]; is_cup='ルヴァン' in comp or '天皇杯' in comp
        if not ('Ｊ２' in comp or 'J2' in comp or is_cup): continue
        ha='H' if '八戸' in cells[5] else 'A'
        opponent=cells[7] if ha=='H' else cells[5]
        if not opponent or opponent in ('未定','-'): continue
        # Future matches only; already played games do not need automatic insertion.
        if iso<datetime.now(JST).date().isoformat(): continue
        broadcast=cells[10] if len(cells)>10 else '未定'
        fixtures.append({'date':iso,'time':f'{int(t.group(1)):02d}:{t.group(2)}',
            'team':'hachinohe','teamLabel':'八戸','comp':comp+' '+cells[2],
            'opp':opponent,'ha':ha,'watch':broadcast or '未定',
            'venue':cells[8] if len(cells)>8 else ''})
    return sorted({(x['date'],x['comp'],x['opp']):x for x in fixtures}.values(),key=lambda x:x['date'])


def main():
    years = [datetime.now(JST).year, datetime.now(JST).year + 1]
    fixtures = []
    errors = []
    for year in years:
        url = URL_TEMPLATE.format(year=year).replace('team_ids=3', 'team_ids=362')
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read(5_000_000).decode('utf-8', 'replace')
            reader = TableReader()
            reader.feed(html)
            if len(reader.rows) < 5:
                raise RuntimeError('Official table not found')
            matches = parse(reader.rows)
            print(f'{year}: {len(matches)} future fixtures')
            fixtures.extend(matches)
        except Exception as exc:
            errors.append(f'{year}: {exc}')
    for error in errors:
        print('WARNING:', error)
    if not fixtures:
        raise RuntimeError('No confirmed future fixtures; existing JSON preserved')
    unique = {(x['date'], x['comp'], x['opp']): x for x in fixtures}
    fixtures = sorted(unique.values(), key=lambda x: (x['date'], x['time']))
    OUT.write_text(json.dumps(fixtures, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {len(fixtures)} confirmed Hachinohe fixtures to {OUT}')

if __name__ == '__main__':
    main()
