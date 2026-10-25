#!/usr/bin/env python3
"""Conservative official-site change watcher. Never guesses fixtures."""
import hashlib
import json
import os
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

SOURCES = {
    'yakult': 'https://www.yakult-swallows.co.jp/',
    'urawa': 'https://www.urawa-reds.co.jp/',
    'hachinohe': 'https://vanraure.net/',
}
STATE = Path('source_state.json')

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            d = dict(attrs)
            if 'href' in d:
                self.hrefs.append(d['href'])

def signature(url):
    req = urllib.request.Request(url, headers={'User-Agent': '3team-calendar-monitor/1.0 (GitHub Actions)'})
    with urllib.request.urlopen(req, timeout=25) as res:
        html = res.read(3_000_000).decode('utf-8', errors='replace')
    parser = Links()
    parser.feed(html)
    # Only monitor schedule-related links; avoid banners, headlines and other noise.
    links = sorted(set(x.strip() for x in parser.hrefs if re.search(r'schedule|game|match|fixture|日程|試合', x, re.I)))
    if not links:
        raise ValueError('No schedule-related links found; no state update')
    return hashlib.sha256('\n'.join(links).encode()).hexdigest(), len(links)

def main():
    old = json.loads(STATE.read_text()) if STATE.exists() else {}
    new = dict(old)
    changes, failures = [], []
    for team, url in SOURCES.items():
        try:
            digest, count = signature(url)
            previous = old.get(team)
            if previous and previous != digest:
                changes.append(f'- {team}: {url} (schedule-related links changed; {count} links)')
            new[team] = digest
        except Exception as exc:
            failures.append(f'- {team}: {type(exc).__name__}: {exc}')
    STATE.write_text(json.dumps(new, indent=2, ensure_ascii=False) + '\n')
    with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
        f.write(f'changed={str(bool(changes)).lower()}\n')
        f.write(f'failed={str(bool(failures)).lower()}\n')
    Path('schedule_check_report.md').write_text(
        '## 公式サイトの変更検知\n\n' + ('\n'.join(changes) if changes else '変更検知なし（または初回実行）。')
        + '\n\n## 取得エラー\n\n' + ('\n'.join(failures) if failures else 'なし')
        + '\n\n**注意:** これは公式サイトのリンク変更検知であり、試合日程の自動更新ではありません。\n'
    )
    print(Path('schedule_check_report.md').read_text())

if __name__ == '__main__':
    main()
