# Calendrier complet des compétitions (ESPN) sur les prochains jours, avec les cotes du marché quand ESPN les donne.
import json,subprocess,datetime
from concurrent.futures import ThreadPoolExecutor
from fd import ESPN
API='https://site.api.espn.com/apis/site/v2/sports/soccer/'
EXTRA={'EL':('uefa.europa','Ligue Europa'),'ECL':('uefa.europa.conf','Conference League'),'KSA':('ksa.1','Saudi Pro League')}

def _get(url):
    r=subprocess.run(['curl','-sfL','--compressed','--max-time','20','-A','Mozilla/5.0',url],capture_output=True)
    try: return json.loads(r.stdout) if r.returncode==0 and r.stdout else {}
    except ValueError: return {}

def _dec(x):
    # cote décimale à partir d'une cote décimale (bet365) ou américaine (DraftKings)
    if not isinstance(x,dict): return None
    v=x.get('value')
    if isinstance(v,(int,float)) and v>1: return round(float(v),2)
    ml=x.get('moneyLine')
    if isinstance(ml,(int,float)) and ml!=0: return round(1+(ml/100 if ml>0 else 100/abs(ml)),2)
    return None

def fixtures(days=8):
    codes={k:v for k,v in ESPN.items()}; codes.update({k:v[0] for k,v in EXTRA.items()})
    today=datetime.datetime.now(datetime.timezone.utc).date()
    jobs=[(lg,code,(today+datetime.timedelta(days=i)).strftime('%Y%m%d')) for lg,code in codes.items() for i in range(days)]
    with ThreadPoolExecutor(8) as ex:
        pages=list(ex.map(lambda j:(j[0],_get(f'{API}{j[1]}/scoreboard?dates={j[2]}')),jobs))
    out={}
    for lg,d in pages:
        for e in d.get('events',[]):
            c=(e.get('competitions') or [{}])[0]
            stt=(c.get('status') or e.get('status') or {}).get('type') or {}
            if stt.get('state','pre')!='pre': continue
            cs=c.get('competitors') or []; h=next((x for x in cs if x['homeAway']=='home'),None); a=next((x for x in cs if x['homeAway']=='away'),None)
            if not h or not a: continue
            mkt={}
            for o in [x for x in (c.get('odds') or []) if isinstance(x,dict)]:
                hh,aa,dd=_dec(o.get('homeTeamOdds')),_dec(o.get('awayTeamOdds')),_dec(o.get('drawOdds'))
                if hh and aa and dd: mkt=dict(h=hh,d=dd,a=aa); break
            w=datetime.datetime.fromisoformat(e['date'].replace('Z','+00:00'))
            out[e['id']]=dict(lg=lg,espn=[codes[lg],e['id']],when=w,h=h['team']['displayName'],a=a['team']['displayName'],mkt=mkt)
    return list(out.values())
