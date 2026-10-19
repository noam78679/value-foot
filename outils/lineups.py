# usage: lineups.py data.json — ajoute les compos officielles (ESPN) des matchs qui commencent bientôt.
# Les compos sortent en général 1 h avant le coup d'envoi ; ce script tourne toutes les 10 minutes.
import sys,json,re,datetime,subprocess,unicodedata,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from fd import ESPN
from zoneinfo import ZoneInfo
now=datetime.datetime.now(ZoneInfo('Europe/Paris'))
path=sys.argv[1]; data=json.load(open(path))
API='https://site.api.espn.com/apis/site/v2/sports/soccer/'

def get(url):
    r=subprocess.run(['curl','-sfL','--compressed','--max-time','20','-A','Mozilla/5.0',url],capture_output=True)
    return json.loads(r.stdout) if r.returncode==0 and r.stdout else {}
def norm(s): return re.sub(r'[^a-z0-9 ]','',unicodedata.normalize('NFD',s).encode('ascii','ignore').decode().lower())
STOP={'fc','ac','as','sc','cf','afc','rc','ss','us','sv','vfb','vfl','tsg','fk','sk','cd','ud','rcd','club','de','the','stade','olympique','real','sporting'}
def same(a,b):
    # deux noms d'équipe désignent le même club si un mot significatif commence pareil (« Rennes » / « Stade Rennais »)
    ta=[w for w in norm(a).split() if w not in STOP] or norm(a).split(); tb=[w for w in norm(b).split() if w not in STOP] or norm(b).split()
    return any(x[:4]==y[:4] and len(x)>=4 and len(y)>=4 for x in ta for y in tb) or norm(a).replace(' ','')==norm(b).replace(' ','')

todo=[m for m in data['matches'] if not (m.get('lu') or {}).get('h')
      and now-datetime.timedelta(minutes=20)<datetime.datetime.fromisoformat(m['when'])<now+datetime.timedelta(minutes=150)]
boards={}
found=0
for m in todo:
    lg=ESPN.get(m.get('lg'))
    if not lg: continue
    w=datetime.datetime.fromisoformat(m['when'])
    if not m.get('espn'):
        day=w.astimezone(datetime.timezone.utc).strftime('%Y%m%d')
        if (lg,day) not in boards: boards[(lg,day)]=get(f'{API}{lg}/scoreboard?dates={day}').get('events',[])
        for e in boards[(lg,day)]:
            t=datetime.datetime.fromisoformat(e['date'].replace('Z','+00:00'))
            if abs((t-w).total_seconds())>100*60: continue
            cs=e['competitions'][0]['competitors']; h=next(c for c in cs if c['homeAway']=='home'); a=next(c for c in cs if c['homeAway']=='away')
            if same(m['home'],h['team']['displayName']) or same(m['away'],a['team']['displayName']) or same(m.get('hk') or '',h['team']['displayName']):
                m['espn']=[lg,e['id']]; break
    if not m.get('espn'): continue
    d=get(f"{API}{m['espn'][0]}/summary?event={m['espn'][1]}")
    ro=d.get('rosters',[])
    if len(ro)<2: continue
    side={r.get('homeAway'):r for r in ro}
    if 'home' not in side or 'away' not in side: continue
    def xi(r): return [[p['athlete'].get('displayName',''),(p.get('position') or {}).get('abbreviation','')] for p in r.get('roster',[]) if p.get('starter')]
    def bench(r): return [p['athlete'].get('displayName','') for p in r.get('roster',[]) if not p.get('starter')]
    H,A=xi(side['home']),xi(side['away'])
    if len(H)<11 or len(A)<11: continue  # compo pas encore publiée
    m['lu']={'t':now.isoformat(timespec='minutes'),'f':[side['home'].get('formation',''),side['away'].get('formation','')],'h':H,'a':A,'bh':bench(side['home'])[:12],'ba':bench(side['away'])[:12]}
    found+=1
json.dump(data,open(path,'w'),ensure_ascii=False)
print('compos :',found,'nouvelles,',len(todo),'matchs surveillés')
