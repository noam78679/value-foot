# usage: build_data.py odds.json stats.json out.json
import sys,json,re,datetime
from zoneinfo import ZoneInfo
odds=json.load(open(sys.argv[1])); stats=json.load(open(sys.argv[2]))
LG={'Ligue 1':'france','Premier League':'england','Liga':'spain','Serie A':'italy','Bundesliga':'germany'}
NAME={'PSG':'Paris SG','Coventry':'Coventry City','Manchester United':'Manchester Utd','Newcastle':'Newcastle Utd','Nottingham Forest':'Nottm Forest','Leeds':'Leeds Utd',
 'Alavés':'Alaves','La Corogne':'Deportivo','Espanyol Barcelone':'Espanyol','FC Barcelone':'FC Barcelona','Santander':'Racing','Betis Séville':'Real Betis','FC Séville':'Sevilla FC','Valence':'Valencia','Atletico Madrid':'Atletico Madrid',
 'Milan AC':'AC Milan','AS Rome':'AS Roma','Atalanta Bergame':'Atalanta','Bologne':'Bologna','Come':'Como','Frosinone Calcio':'Frosinone','Juventus Turin':'Juventus','Lazio Rome':'Lazio','Naples':'Napoli','Parme':'Parma',
 'Borussia Dortmund':'Dortmund','Eintracht Francfort':'E. Frankfurt','Augsbourg':'FC Augsburg','Cologne':'FC Koln','Mayence':'FSV Mainz','Mainz':'FSV Mainz','Fribourg':'Freiburg','Hambourg':'Hamburger SV','Bayer Leverkusen':'Leverkusen',"Borussia M'gladbach":'Monchengladbach','Werder Breme':'Werder Bremen'}
MOIS={m:i+1 for i,m in enumerate('janvier février mars avril mai juin juillet août septembre octobre novembre décembre'.split())}
def league_avgs(t):
    gh=sum(v['h'][1] for v in t.values()); ph=sum(v['h'][0] for v in t.values())
    ga=sum(v['a'][1] for v in t.values()); pa=sum(v['a'][0] for v in t.values())
    return gh/ph, ga/pa
def find(name):
    n=NAME.get(name,name)
    for lg,t in stats.items():
        if n in t: return lg,t[n]
    return None,None
def rates(s,lgH,lgA,K=6,K0=10):
    # régression vers la moyenne : peu de matchs joués en début de saison
    gp=s['h'][0]+s['a'][0]; lgAll=(lgH+lgA)/2
    gf=(s['h'][1]+s['a'][1]+K0*lgAll)/(gp+K0); ga=(s['h'][2]+s['a'][2]+K0*lgAll)/(gp+K0)
    hGF=(s['h'][1]+K*gf*lgH/lgAll)/(s['h'][0]+K); hGA=(s['h'][2]+K*ga*lgA/lgAll)/(s['h'][0]+K)
    aGF=(s['a'][1]+K*gf*lgA/lgAll)/(s['a'][0]+K); aGA=(s['a'][2]+K*ga*lgH/lgAll)/(s['a'][0]+K)
    return dict(hGF=hGF,hGA=hGA,aGF=aGF,aGA=aGA,gp=gp)
avg={lg:league_avgs(t) for lg,t in stats.items()}
out=[]
for m in odds:
    if not m['odds']: continue
    d=re.search(r'(\d+) (\w+) (\d{4}) - (\d+):(\d+)',m['when'])
    # heures de compare-bet.fr = heure de Paris ; on ajoute le décalage pour un affichage juste partout
    iso=datetime.datetime(int(d[3]),MOIS[d[2]],int(d[1]),int(d[4]),int(d[5]),tzinfo=ZoneInfo('Europe/Paris')).isoformat(timespec='minutes')
    lh,sh=find(m['home']); la,sa=find(m['away'])
    rec=dict(id=re.sub(r'\W+','-',(m['home']+'-'+m['away']+'-'+iso[:10]).lower()),comp=m['comp'],when=iso,home=m['home'],away=m['away'],
             odds=dict(h=m['odds'][0],d=m['odds'][1],a=m['odds'][2]))
    if sh and sa:
        lgH,lgA=avg[LG.get(m['comp'],lh)]
        rh,ra=rates(sh,*avg[lh]),rates(sa,*avg[la])
        rec.update(hGF=round(rh['hGF'],3),hGA=round(rh['hGA'],3),aGF=round(ra['aGF'],3),aGA=round(ra['aGA'],3),lgH=round(lgH,3),lgA=round(lgA,3),gp=[rh['gp'],ra['gp']])
        if lh!=la or m['comp'] not in LG: rec['cross']=1
    out.append(rec)
if len(out)<20: sys.exit(f'Seulement {len(out)} matchs récupérés : données gardées telles quelles')
json.dump(dict(updated=datetime.datetime.now(ZoneInfo('Europe/Paris')).isoformat(timespec='minutes'),source='Cotes Betclic relevées sur compare-bet.fr · stats domicile/extérieur soccerstats.com',matches=out),open(sys.argv[3],'w'),ensure_ascii=False)
print(len(out),'matchs;',sum(1 for x in out if 'hGF' in x),'avec stats')
print([ (x['home'],x['away']) for x in out if 'hGF' not in x])
