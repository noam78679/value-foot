# usage: news.py data.json ancien-data.json — ajoute l'actu des équipes qui jouent bientôt (Google Actualités)
# Chaque équipe est rafraîchie au plus toutes les 4 h ; une alerte est levée si les titres parlent d'absences.
import sys,json,re,html,datetime,time,urllib.parse,os,subprocess
from zoneinfo import ZoneInfo
now=datetime.datetime.now(ZoneInfo('Europe/Paris'))
data=json.load(open(sys.argv[1]))
prev=json.load(open(sys.argv[2])) if os.path.exists(sys.argv[2]) and os.path.getsize(sys.argv[2]) else {}
cache=prev.get('news',{})
ALERT=re.compile(r"bless|forfait|suspend|absent|incertain|out |touché|rupture|entorse|opér|manquer|privé|indisponible|carton rouge|expuls|injur|ruled out|doubt",re.I)
# noms de recherche plus précis pour les clubs au nom de ville ambigu
Q={'PSG':'PSG','Paris FC':'"Paris FC"','Nice':'"OGC Nice"','Lens':'"RC Lens"','Lyon':'"OL" Lyon foot','Marseille':'"OM" Marseille foot','Monaco':'"AS Monaco"','Brest':'"Stade brestois"','Lille':'"LOSC"','Rennes':'"Stade rennais"','Lorient':'"FC Lorient"','Angers':'"Angers SCO"','Toulouse':'"Toulouse FC"','Le Havre':'"HAC" Havre foot','Auxerre':'"AJ Auxerre"','Strasbourg':'"RC Strasbourg"','Troyes':'"ESTAC" Troyes','Le Mans':'"Le Mans FC"'}
def fetch(q):
    url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':q+' when:4d','hl':'fr','gl':'FR','ceid':'FR:fr'})
    s=subprocess.run(['curl','-sfL','--max-time','15','-A','Mozilla/5.0',url],capture_output=True,check=True).stdout.decode('utf-8','ignore')
    out=[]
    for it in re.findall(r'<item>(.*?)</item>',s,re.S)[:12]:
        t=html.unescape(re.search(r'<title>(.*?)</title>',it,re.S).group(1)).strip()
        link=html.unescape(re.search(r'<link>(.*?)</link>',it,re.S).group(1)).strip()
        d=re.search(r'<pubDate>(.*?)</pubDate>',it)
        d=datetime.datetime.strptime(d.group(1),'%a, %d %b %Y %H:%M:%S %Z').replace(tzinfo=datetime.timezone.utc).isoformat() if d else None
        src=t.rsplit(' - ',1)[1] if ' - ' in t else ''
        out.append([t.rsplit(' - ',1)[0],src,link,d])
    return out
soon=[m for m in data['matches'] if datetime.datetime.fromisoformat(m['when'])<now+datetime.timedelta(days=4)]
# grands championnats d'abord, puis les matchs les plus proches
PRIO=['Ligue 1','Ligue des champions','Premier League','Liga','Serie A','Bundesliga','Ligue 2']
soon.sort(key=lambda m:(PRIO.index(m['comp']) if m['comp'] in PRIO else 99,m['when']))
teams=list(dict.fromkeys(t for m in soon for t in (m['home'],m['away'])))
done=0
for t in teams:
    c=cache.get(t)
    if c and datetime.datetime.fromisoformat(c['t'])>now-datetime.timedelta(hours=4): continue
    if done>=70: break  # limite par passage, le reste au passage suivant
    try:
        q=Q.get(t,f'"{t}" foot')
        items=fetch(q); time.sleep(0.4)
        alerts=fetch(q+' (blessure OR blessé OR forfait OR suspendu OR absent OR incertain)'); time.sleep(0.4)
        alerts=[a for a in alerts if ALERT.search(a[0])][:4]
        cache[t]={'t':now.isoformat(timespec='minutes'),'items':items[:4],'alerts':alerts}
        done+=1
    except Exception as e:
        print('actu indisponible :',t,e)
keep={t for m in data['matches'] for t in (m['home'],m['away'])}
data['news']={t:v for t,v in cache.items() if t in keep}
json.dump(data,open(sys.argv[1],'w'),ensure_ascii=False)
print('actu :',done,'équipes mises à jour,',len(data['news']),'en mémoire')
