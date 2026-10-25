#!/usr/bin/env python3
"""Read-only inspection of Yakult official full schedule, including away games."""
import re
import urllib.request
from html.parser import HTMLParser

class GameCards(HTMLParser):
    def __init__(self):
        super().__init__(); self.depth=0; self.li=[]; self.cards=[]; self.in_li=False
    def handle_starttag(self, tag, attrs):
        if tag=='li':
            if not self.in_li: self.in_li=True; self.depth=1; self.li=[]
            else: self.depth+=1
        elif self.in_li and tag in ('br','p','div'): self.li.append(' ')
    def handle_endtag(self, tag):
        if tag=='li' and self.in_li:
            self.depth-=1
            if self.depth==0:
                text=' '.join(''.join(self.li).split())
                if re.search(r'\b2026\b.*セ・リーグ公式戦',text) and 'ヤクルト' in text:
                    self.cards.append(text)
                self.in_li=False
    def handle_data(self, data):
        if self.in_li: self.li.append(data)

for month in (9,10):
    url=f'https://www.yakult-swallows.co.jp/game/2026{month:02d}'
    print('\nPAGE',url,flush=True)
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=20) as resp:
            html=resp.read(3000000).decode('utf-8','replace')
            print('HTTP',resp.status,'bytes',len(html),flush=True)
        p=GameCards();p.feed(html)
        print('Detected game cards:',len(p.cards),flush=True)
        for card in p.cards[:35]: print('GAME',card[:280],flush=True)
        if not p.cards: print('WARNING: Card parser needs adjustment',flush=True)
    except Exception as exc: print('ERROR',type(exc).__name__,str(exc),flush=True)
print('\nREAD ONLY: no files changed')
