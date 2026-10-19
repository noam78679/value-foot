# usage: build_data.py odds.json stats.json results.json ancien-data.json out.json
# Assemble les cotes Betclic, les stats domicile/extérieur, la forme, le classement,
# l'historique des cotes et les résultats des matchs déjà joués.
import sys,json,re,datetime,os
from zoneinfo import ZoneInfo
PARIS=ZoneInfo('Europe/Paris')
odds=json.load(open(sys.argv[1])); stats=json.load(open(sys.argv[2])); results=json.load(open(sys.argv[3]))
prev=json.load(open(sys.argv[4])) if os.path.exists(sys.argv[4]) and os.path.getsize(sys.argv[4]) else {}
LG={'Ligue 1':'france','Ligue 2':'france2','Premier League':'england','Liga':'spain','Serie A':'italy','Bundesliga':'germany'}
NAME={'PSG':'Paris SG','Coventry':'Coventry City','Manchester United':'Manchester Utd','Newcastle':'Newcastle Utd','Nottingham Forest':'Nottm Forest','Leeds':'Leeds Utd',
 'Alavés':'Alaves','La Corogne':'Deportivo','Espanyol Barcelone':'Espanyol','FC Barcelone':'FC Barcelona','Santander':'Racing','Betis Séville':'Real Betis','FC Séville':'Sevilla FC','Valence':'Valencia','Atletico Madrid':'Atletico Madrid',
 'Milan AC':'AC Milan','AS Rome':'AS Roma','Atalanta Bergame':'Atalanta','Bologne':'Bologna','Come':'Como','Côme':'Como','Frosinone Calcio':'Frosinone','Juventus Turin':'Juventus','Lazio Rome':'Lazio','Naples':'Napoli','Parme':'Parma',
 'Borussia Dortmund':'Dortmund','Eintracht Francfort':'E. Frankfurt','Augsbourg':'FC Augsburg','Cologne':'FC Koln','Mayence':'FSV Mainz','Mainz':'FSV Mainz','Fribourg':'Freiburg','Hambourg':'Hamburger SV','Bayer Leverkusen':'Leverkusen',"Borussia M'gladbach":'Monchengladbach','Werder Breme':'Werder Bremen',
 'Pau':'Pau FC','Rodez':'Rodez Aveyron','Dunkerque':'USL Dunkerque'}
SHOW={'Come':'Côme'}
MOIS={m:i+1 for i,m in enumerate('janvier février mars avril mai juin juillet août septembre octobre novembre décembre'.split())}
now=datetime.datetime.now(PARIS)

def league_avgs(t):
    gh=sum(v['h'][1] for v in t.values()); ph=sum(v['h'][0] for v in t.values())
    ga=sum(v['a'][1] for v in t.values()); pa=sum(v['a'][0] for v in t.values())
    return gh/ph, ga/pa
def find(name):
    n=NAME.get(name,name)
    for lg,t in stats.items():
        if n in t: return lg,n,t[n]
    return None,n,None
def rates(s,lgH,lgA,K=6,K0=10):
    # régression vers la moyenne : peu de matchs joués en début de saison
    gp=s['h'][0]+s['a'][0]; lgAll=(lgH+lgA)/2
    gf=(s['h'][1]+s['a'][1]+K0*lgAll)/(gp+K0); ga=(s['h'][2]+s['a'][2]+K0*lgAll)/(gp+K0)
    hGF=(s['h'][1]+K*gf*lgH/lgAll)/(s['h'][0]+K); hGA=(s['h'][2]+K*ga*lgA/lgAll)/(s['h'][0]+K)
    aGF=(s['a'][1]+K*gf*lgA/lgAll)/(s['a'][0]+K); aGA=(s['a'][2]+K*ga*lgH/lgAll)/(s['a'][0]+K)
    return dict(hGF=hGF,hGA=hGA,aGF=aGF,aGA=aGA,gp=gp)
avg={lg:league_avgs(t) for lg,t in stats.items()}

# forme (5 derniers, le plus récent d'abord) et classement, à partir des résultats
form,rank,size={},{},{}
for lg,rs in results.items():
    tab={}
    for r in rs:
        for team,gf,ga in ((r['h'],r['hg'],r['ag']),(r['a'],r['ag'],r['hg'])):
            t=tab.setdefault(team,[0,0,0]); t[0]+=3 if gf>ga else 1 if gf==ga else 0; t[1]+=gf-ga; t[2]+=gf
            form.setdefault(team,[]).append(('V' if gf>ga else 'N' if gf==ga else 'D',r['d']))
    order=sorted(tab,key=lambda k:(-tab[k][0],-tab[k][1],-tab[k][2]))
    for i,k in enumerate(order): rank[k]=i+1; size[k]=len(order)
form={k:''.join(x for x,_ in sorted(v,key=lambda y:y[1],reverse=True)[:5]) for k,v in form.items()}

def score_for(rec):
    # cherche le résultat d'un match déjà joué (même affiche, à un jour près)
    if 'hk' not in rec: return None
    d=datetime.datetime.fromisoformat(rec['when']).date()
    for rs in results.values():
        for r in rs:
            if r['h']==rec['hk'] and r['a']==rec['ak'] and abs((datetime.date.fromisoformat(r['d'])-d).days)<=1:
                return [r['hg'],r['ag']]
    return None

old={m['id']:m for m in prev.get('matches',[])+prev.get('past',[])}
out=[]
for m in odds:
    if not m['odds']: continue
    d=re.search(r'(\d+) (\w+) (\d{4}) - (\d+):(\d+)',m['when'])
    # heures de compare-bet.fr = heure de Paris ; on ajoute le décalage pour un affichage juste partout
    iso=datetime.datetime(int(d[3]),MOIS[d[2]],int(d[1]),int(d[4]),int(d[5]),tzinfo=PARIS).isoformat(timespec='minutes')
    lh,kh,sh=find(m['home']); la,ka,sa=find(m['away'])
    home,away=SHOW.get(m['home'],m['home']),SHOW.get(m['away'],m['away'])
    rid=re.sub(r'\W+','-',(home+'-'+away+'-'+iso[:10]).lower())
    cur=dict(h=m['odds'][0],d=m['odds'][1],a=m['odds'][2])
    rec=dict(id=rid,comp=m['comp'],when=iso,home=home,away=away,odds=cur,open=old.get(rid,{}).get('open') or cur)
    if sh and sa:
        lgH,lgA=avg[LG.get(m['comp'],lh)]
        rh,ra=rates(sh,*avg[lh]),rates(sa,*avg[la])
        rec.update(hGF=round(rh['hGF'],3),hGA=round(rh['hGA'],3),aGF=round(ra['aGF'],3),aGA=round(ra['aGA'],3),lgH=round(lgH,3),lgA=round(lgA,3),gp=[rh['gp'],ra['gp']],hk=kh,ak=ka)
        if lh!=la or m['comp'] not in LG: rec['cross']=1
    for side,k in (('h',kh),('a',ka)):
        if k in form: rec[side+'f']=form[k]
        if k in rank and not rec.get('cross'): rec[side+'r']=rank[k]; rec['n']=size[k]
    out.append(rec)
if len(out)<20: sys.exit(f'Seulement {len(out)} matchs récupérés : données gardées telles quelles')

# archive : matchs commencés (dernière cote connue avant le coup d'envoi) + leurs résultats, 45 jours
ids={r['id'] for r in out}
upcoming=[r for r in out if datetime.datetime.fromisoformat(r['when'])>now-datetime.timedelta(hours=2)]
started=[r for r in out if r not in upcoming]
past={m['id']:m for m in prev.get('past',[])}
for m in prev.get('matches',[])+started:
    if datetime.datetime.fromisoformat(m['when'])<=now: past[m['id']]=m
limit=now-datetime.timedelta(days=45)
past=[m for m in past.values() if datetime.datetime.fromisoformat(m['when'])>limit and m['id'] not in {u['id'] for u in upcoming}]
for m in past:
    if not m.get('score'):
        sc=score_for(m)
        if sc: m['score']=sc
past.sort(key=lambda m:m['when'],reverse=True)

json.dump(dict(updated=now.isoformat(timespec='minutes'),
  source='Cotes Betclic relevées sur compare-bet.fr · stats, forme, classements et résultats soccerstats.com',
  matches=upcoming,past=past),open(sys.argv[5],'w'),ensure_ascii=False)
print(len(upcoming),'matchs;',sum(1 for x in upcoming if 'hGF' in x),'avec stats;',len(past),'archivés dont',sum(1 for x in past if x.get('score')),'avec score')
print('sans stats :',[(x['home'],x['away']) for x in upcoming if 'hGF' not in x and x['comp'] in LG])
