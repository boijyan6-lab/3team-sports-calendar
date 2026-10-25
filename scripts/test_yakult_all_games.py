#!/usr/bin/env python3
"""Read-only Yakult full schedule JSON preview. Does not write files."""
import json
import re
import urllib.request
from datetime import date
from html.parser import HTMLParser

class GameCards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.li = []
        self.cards = []
        self.in_li = False
    def handle_starttag(self, tag, attrs):
        if tag == 'li':
            if not self.in_li:
                self.in_li = True
                self.depth = 1
                self.li = []
            else:
                self.depth += 1
        elif self.in_li and tag in ('br', 'p', 'div'):
            self.li.append(' ')
    def handle_endtag(self, tag):
        if tag == 'li' and self.in_li:
            self.depth -= 1
            if self.depth == 0:
                text = ' '.join(''.join(self.li).split())
                if re.search(r'\b2026\b.*セ・リーグ公式戦', text) and 'ヤクルト' in text:
                    self.cards.append(text)
                self.in_li = False
    def handle_data(self, data):
        if self.in_li:
            self.li.append(data)

OPPONENTS = ('DeNA', '阪神', '巨人', '中日', '広島')
VENUES = ('神宮', '横浜', '東京ドーム', '甲子園', 'マツダ', 'バンテリンドーム', 'ナゴヤドーム',
          'ZOZOマリン', 'ベルーナドーム', '京セラD大阪', '京セラドーム', '地方', '坊っちゃん',
          'エスコン', '楽天モバイル', 'ほっともっと')
def parse_card(card):
    m = re.search(r'\b(\d{1,2})\s*[・.]\s*(\d{1,2})\s+(?:MON|TUE|WED|THU|FRI|SAT|SUN)\s+(20\d{2})\b', card)
    if not m:
        return None, 'date not found'
    month, day, year = map(int, m.groups())
    try:
        day_iso = date(year, month, day).isoformat()
    except ValueError:
        return None, 'invalid date'
    # The card starts with the home team, followed by the venue, score/status and visiting team.
    body = card[m.end():]
    if 'セ・リーグ公式戦' not in body:
        return None, 'not a league game'
    body = body.split('セ・リーグ公式戦', 1)[1].strip()
    team_pattern = r'(?:ヤクルト|DeNA|阪神|巨人|中日|広島)'
    home = re.match(team_pattern, body)
    if not home:
        return None, 'home team not found'
    home = home.group()
    if home == 'ヤクルト':
        ha = 'H'
    else:
        ha = 'A'
    opponent = next((t for t in OPPONENTS if (t == home if ha == 'A' else re.search(r'(?<!\w)' + re.escape(t), body))), None)
    if not opponent:
        return None, 'opponent not found'
    venue = next((v for v in VENUES if v in body), '')
    # Do not guess time: full schedule page may omit kickoff time in completed games.
    tm = re.search(r'(?<!\d)(\d{1,2}):([0-5]\d)(?!\d)', body)
    time = f'{int(tm.group(1)):02d}:{tm.group(2)}' if tm else ''
    return {'date':day_iso, 'time':time, 'team':'yakult', 'teamLabel':'ヤクルト',
            'comp':'セ・リーグ', 'opp':opponent, 'ha':ha, 'venue':venue, 'watch':'未定'}, None

def main():
    all_games = []
    for month in (9, 10):
        url = f'https://www.yakult-swallows.co.jp/game/2026{month:02d}'
        print('PAGE', url, flush=True)
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read(3_000_000).decode('utf-8', 'replace')
        parser = GameCards()
        parser.feed(html)
        parsed = []
        rejected = {}
        for card in parser.cards:
            game, error = parse_card(card)
            if game:
                parsed.append(game)
            else:
                rejected[error] = rejected.get(error, 0) + 1
        print('Detected cards:',len(parser.cards),'Parsed:',len(parsed),'Rejected:',rejected, flush=True)
        print('Home:',sum(x['ha']=='H' for x in parsed),'Away:',sum(x['ha']=='A' for x in parsed), flush=True)
        print('With start time:',sum(bool(x['time']) for x in parsed), flush=True)
        for game in parsed[:8]:
            print('PREVIEW',json.dumps(game,ensure_ascii=False),flush=True)
        all_games.extend(parsed)
    if not all_games or not any(x['ha']=='H' for x in all_games) or not any(x['ha']=='A' for x in all_games):
        raise RuntimeError('Both home and away fixtures could not be verified')
    print('PREVIEW ONLY: no files changed.',flush=True)

if __name__ == '__main__':
    main()
