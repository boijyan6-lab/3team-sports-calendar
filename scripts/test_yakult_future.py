#!/usr/bin/env python3
"""Read-only check: official Yakult schedule cards with future start times."""
import re
import urllib.request
from datetime import date
from html.parser import HTMLParser

class Cards(HTMLParser):
    def __init__(self):
        super().__init__(); self.depth=0; self.parts=[]; self.cards=[]
    def handle_starttag(self,tag,attrs):
        if tag=='li':
            if not self.depth: self.parts=[]
            self.depth+=1
        elif self.depth and tag in ('div','p','br'): self.parts.append(' ')
    def handle_endtag(self,tag):
        if tag=='li' and self.depth:
            self.depth-=1
            if not self.depth:
                value=' '.join(''.join(self.parts).split())
                if re.search(r'\b20\d{2}\b.*セ・リーグ公式戦',value) and 'ヤクルト' in value:
                    self.cards.append(value)
    def handle_data(self,data):
        if self.depth:self.parts.append(data)

def main():
    total=0
    for year,month in ((2026,9),(2026,10),(2027,3),(2027,4)):
        url=f'https://www.yakult-swallows.co.jp/game/{year}{month:02d}'
        print('\nPAGE',url,flush=True)
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req,timeout=20) as resp:
                html=resp.read(3_000_000).decode('utf-8','replace')
            p=Cards();p.feed(html)
            times=0
            for card in p.cards:
                m=re.search(r'\b(\d{1,2})\s*[・.]\s*(\d{1,2})\s+(?:MON|TUE|WED|THU|FRI|SAT|SUN)\s+(20\d{2})\b',card)
                if not m:continue
                mm,dd,yy=map(int,m.groups())
                if date(yy,mm,dd)<date.today():continue
                tm=re.search(r'(?<!\d)([01]?\d|2[0-3]):([0-5]\d)(?!\d)',card)
                print('FUTURE',f'{yy}-{mm:02d}-{dd:02d}', 'TIME '+tm.group(0) if tm else 'TIME UNKNOWN',card[:150],flush=True)
                times+=bool(tm);total+=bool(tm)
            print('Cards:',len(p.cards),'future cards with time:',times,flush=True)
        except Exception as e:
            print('WARNING',type(e).__name__,str(e),flush=True)
    print('\nREAD ONLY; future start times found:',total,flush=True)
    print('Historical games can lose time after results appear. No files changed.',flush=True)
if __name__=='__main__':main()
