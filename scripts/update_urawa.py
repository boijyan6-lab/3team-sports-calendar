#!/usr/bin/env python3
"""Conservative J.League Data Site Urawa fixture extractor. Writes JSON only on valid data."""
import json, re, urllib.request
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

URL_TEMPLATE='https://data.j-league.or.jp/SFMS01/search?competition_years={year}&home_away_select=0&team_ids=3'
JST=timezone(timedelta(hours=9))
OUT=Path('fixtures_auto.json')

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
        if len(cells)<10 or not re.search(r'浦和', ' '.join(cells[5:8])): continue
        if '浦和' not in cells[5] and '浦和' not in cells[7]: continue
        m=re.search(r'(\d{2})/(\d{2})/(\d{2})',cells[3]); t=re.search(r'\b(\d{1,2}):(\d{2})\b',cells[4])
        if not m or not t: continue
        year=2000+int(m.group(1)); month=int(m.group(2)); day=int(m.group(3))
        try: iso=date(year,month,day).isoformat()
        except ValueError: continue
        comp=cells[1]; is_cup='ルヴァン' in comp or '天皇杯' in comp
        if not is_cup: continue  # Pilot deliberately limited to cup fixtures.
        ha='H' if '浦和' in cells[5] else 'A'
        opponent=cells[7] if ha=='H' else cells[5]
        if not opponent or opponent in ('未定','-'): continue
        # Future matches only; already played games do not need automatic insertion.
        if iso<datetime.now(JST).date().isoformat(): continue
        broadcast=cells[10] if len(cells)>10 else '未定'
        fixtures.append({'date':iso,'time':f'{int(t.group(1)):02d}:{t.group(2)}',
            'team':'urawa','teamLabel':'浦和','comp':comp+' '+cells[2],
            'opp':opponent,'ha':ha,'watch':broadcast or '未定',
            'venue':cells[8] if len(cells)>8 else ''})
    return sorted({(x['date'],x['comp'],x['opp']):x for x in fixtures}.values(),key=lambda x:x['date'])

def main():
    years = [datetime.now(JST).year, datetime.now(JST).year + 1]
    fixtures = []
    failures = []
    for year in years:
        try:
            url = URL_TEMPLATE.format(year=year)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; 3team-calendar/1.0)'})
            with urllib.request.urlopen(req, timeout=30) as res:
                html = res.read(5_000_000).decode('utf-8', 'replace')
            parser = TableReader()
            parser.feed(html)
            if len(parser.rows) < 5:
                raise RuntimeError('Official table not found')
            found = parse(parser.rows)
            print(f'{year}: {len(found)} future cup fixture(s) parsed')
            fixtures.extend(found)
        except Exception as exc:
            failures.append(f'{year}: {type(exc).__name__}: {exc}')
    for message in failures:
        print('WARNING:', message)
    if not fixtures:
        raise RuntimeError('No confirmed future cup fixtures parsed; existing JSON preserved')
    unique = {(e['date'], e['comp'], e['opp']): e for e in fixtures}
    fixtures = sorted(unique.values(), key=lambda e: (e['date'], e['time']))
    OUT.write_text(json.dumps(fixtures, ensure_ascii=False, indent=2) + '\\n', encoding='utf-8')
    print(f'Wrote {len(fixtures)} confirmed future cup fixture(s)')

if __name__ == '__main__':
    main()
