# usage: parse_sc.py sc-france.html ... — meilleurs buteurs par équipe (soccerstats scorers.asp)
def _read(p):
    b=open(p,"rb").read()
    try: return b.decode("utf-8")
    except UnicodeDecodeError: return b.decode("cp1252",errors="replace")
import sys,re,html,json,datetime
MON={m:i+1 for i,m in enumerate('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split())}
today=datetime.date.today(); y0=today.year if today.month>=7 else today.year-1
out={}
for path in sys.argv[1:]:
    s=_read(path)
    for r in re.findall(r'<tr[^>]*>(.*?)</tr>',s,re.S):
        if 'teamstats.asp' not in r or 'player.asp' not in r: continue
        c=[re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',x))).strip() for x in re.findall(r'<td[^>]*>(.*?)</td>',r,re.S)]
        try:
            name,team,goals=c[1],c[2],int(c[3])
            dm=re.fullmatch(r'(\d{1,2}) (\w{3})',c[-4]); last=None
            if dm and dm[2] in MON:
                mo=MON[dm[2]]; last=datetime.date(y0 if mo>=7 else y0+1,mo,int(dm[1])).isoformat()
        except (ValueError,IndexError): continue
        out.setdefault(team,[]).append([name,goals,last])
out={t:sorted(v,key=lambda x:-x[1])[:3] for t,v in out.items()}
print(json.dumps(out,ensure_ascii=False))
