# usage: parse_res.py results-france.html ... — résultats de la saison (soccerstats results.asp)
import sys,re,html,json,datetime
MON={m:i+1 for i,m in enumerate('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split())}
today=datetime.date.today(); y0=today.year if today.month>=7 else today.year-1
res={}
for path in sys.argv[1:]:
    lg=re.sub(r'^res-|\.html$','',path.split('/')[-1])
    s=open(path,encoding='utf-8',errors='ignore').read(); out=[]
    for r in re.findall(r'<tr[^>]*>(.*?)</tr>',s,re.S):
        c=[re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',x))).strip() for x in re.findall(r'<td[^>]*>(.*?)</td>',r,re.S)]
        c=[x for x in c if x]
        if len(c)<4: continue
        dm=re.fullmatch(r'(?:\w{3} )?(\d{1,2}) (\w{3})',c[0]); sc=re.fullmatch(r'(\d+):(\d+)',c[2])
        if not(dm and sc and dm[2] in MON): continue
        mo=MON[dm[2]]; d=datetime.date(y0 if mo>=7 else y0+1,mo,int(dm[1]))
        if d>=today: continue  # à venir : la colonne score contient l'heure du coup d'envoi
        out.append(dict(d=d.isoformat(),h=c[1],a=c[3],hg=int(sc[1]),ag=int(sc[2])))
    res[lg]=sorted({(x['d'],x['h'],x['a']):x for x in out}.values(),key=lambda x:x['d'])
print(json.dumps(res,ensure_ascii=False))
