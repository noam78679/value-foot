# usage: build_data.py dossier-fd betclic.json buteurs.json ancien-data.json out.json
# Assemble tous les championnats de football-data.co.uk (résultats avec xG, matchs à venir, cotes du marché)
# avec les cotes Betclic relevées sur compare-bet.fr, puis calcule le modèle, la forme, les classements et l'archive.
import sys,json,re,datetime,os,glob,unicodedata,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ratings,fd
from zoneinfo import ZoneInfo
PARIS=ZoneInfo('Europe/Paris'); now=datetime.datetime.now(PARIS)
FD,CB,SC,PREV,OUT=sys.argv[1:6]
SSR=sys.argv[6] if len(sys.argv)>6 else ''
betclic=json.load(open(CB)) if os.path.exists(CB) else []
scorers=json.load(open(SC)) if os.path.exists(SC) else {}
prev=json.load(open(PREV)) if os.path.exists(PREV) and os.path.getsize(PREV) else {}

# ---------- résultats de la saison ----------
results={}
for p in glob.glob(FD+'/res/*.csv'):
    n=os.path.basename(p)[:-4]; t=open(p,encoding='utf-8',errors='ignore').read()
    rs=fd.results_new(t) if n.startswith('new-') else fd.results_main(n,t)
    if rs: results[n.replace('new-','')]=rs
fix=fd.fixtures(open(FD+'/fixtures.csv',encoding='utf-8',errors='ignore').read(),open(FD+'/new_league_fixtures.csv',encoding='utf-8',errors='ignore').read())
team_lg={t:lg for lg,rs in results.items() for r in rs for t in (r['h'],r['a'])}
# résultats les plus récents des grands championnats (soccerstats, à jour plus vite) ajoutés s'ils manquent
SS2FD={'Manchester Utd':'Man United','Nottm Forest':"Nott'm Forest",'Newcastle Utd':'Newcastle','Leeds Utd':'Leeds','Coventry City':'Coventry','Hull City':'Hull','Ipswich Town':'Ipswich','Manchester City':'Man City',
 'Atletico Madrid':'Ath Madrid','Athletic Bilbao':'Ath Bilbao','Deportivo':'La Coruna','Espanyol':'Espanol','FC Barcelona':'Barcelona','Racing':'Santander','Rayo Vallecano':'Vallecano','Real Betis':'Betis','Real Sociedad':'Sociedad','Sevilla FC':'Sevilla','Celta Vigo':'Celta',
 'AC Milan':'Milan','AS Roma':'Roma','Inter Milan':'Inter','E. Frankfurt':'Ein Frankfurt','FC Augsburg':'Augsburg','FSV Mainz':'Mainz','Hamburger SV':'Hamburg','Monchengladbach':"M'gladbach",
 'Saint-Etienne':'St Etienne','Rodez Aveyron':'Rodez','USL Dunkerque':'Dunkerque'}
SSLG={'france':'F1','france2':'F2','england':'E0','spain':'SP1','italy':'I1','germany':'D1'}
if SSR and os.path.exists(SSR):
    for k,rs in json.load(open(SSR)).items():
        lg=SSLG.get(k)
        if lg not in results: continue
        names={t for r in results[lg] for t in (r['h'],r['a'])}
        def m2(t):
            t2=SS2FD.get(t,t)
            if t2 in names: return t2
            nt=re.sub(r'[^a-z]','',t2.lower())
            return next((x for x in names if re.sub(r'[^a-z]','',x.lower())==nt),None)
        have={(r['h'],r['a']) for r in results[lg]}
        for r in rs:
            h,a=m2(r['h']),m2(r['a'])
            if h and a and (h,a) not in have: results[lg].append(dict(d=r['d'],h=h,a=a,hg=r['hg'],ag=r['ag'],hx=None,ax=None,hc=None,ac=None,hy=None,ay=None)); have.add((h,a))
        results[lg].sort(key=lambda r:r['d'])

# ---------- noms : comparateur Betclic (français) -> football-data ----------
CB2FD={'PSG':'Paris SG','Hull City':'Hull','Ipswich Town':'Ipswich','Manchester City':'Man City','Manchester United':'Man United','Nottingham Forest':"Nott'm Forest",
 'Alavés':'Alaves','Athletic Bilbao':'Ath Bilbao','Atletico Madrid':'Ath Madrid','Betis Séville':'Betis','Celta Vigo':'Celta','Espanyol Barcelone':'Espanol','FC Barcelone':'Barcelona',
 'FC Séville':'Sevilla','La Corogne':'La Coruna','Rayo Vallecano':'Vallecano','Real Sociedad':'Sociedad','Valence':'Valencia',
 'AS Rome':'Roma','Atalanta Bergame':'Atalanta','Bologne':'Bologna','Come':'Como','Côme':'Como','Frosinone Calcio':'Frosinone','Inter Milan':'Inter','Juventus Turin':'Juventus','Lazio Rome':'Lazio','Milan AC':'Milan','Naples':'Napoli','Parme':'Parma',
 'Augsbourg':'Augsburg','Bayer Leverkusen':'Leverkusen','Borussia Dortmund':'Dortmund',"Borussia M'gladbach":"M'gladbach",'Cologne':'FC Koln','Eintracht Francfort':'Ein Frankfurt','Fribourg':'Freiburg','Hambourg':'Hamburg','Mayence':'Mainz','Werder Breme':'Werder Bremen',
 'Saint-Etienne':'St Etienne','Pau':'Pau FC','Fenerbahçe':'Fenerbahce','FC Porto':'Porto','AEK Athènes':'AEK','Bodø/Glimt':'Bodo/Glimt','Viking FK':'Viking','Feyenoord Rotterdam':'Feyenoord',
 'Bruges':'Club Brugge','Sporting Portugal':'Sp Lisbon','LASK Linz':'LASK','Ajax Amsterdam':'Ajax'}
# noms affichés pour les équipes au nom abrégé chez football-data
SHOW={'Paris SG':'PSG','Man City':'Manchester City','Man United':'Manchester United',"Nott'm Forest":'Nottingham Forest','Ath Madrid':'Atlético Madrid','Ath Bilbao':'Athletic Bilbao',
 'Sociedad':'Real Sociedad','Vallecano':'Rayo Vallecano','Espanol':'Espanyol','Betis':'Betis Séville','Sevilla':'FC Séville','Barcelona':'FC Barcelone','Celta':'Celta Vigo','La Coruna':'La Corogne','Valencia':'Valence',
 'Inter':'Inter Milan','Milan':'Milan AC','Roma':'AS Rome','Napoli':'Naples','Como':'Côme','Parma':'Parme','Bologna':'Bologne','Lazio':'Lazio Rome','Juventus':'Juventus Turin',
 'Ein Frankfurt':'Eintracht Francfort','FC Koln':'Cologne',"M'gladbach":"Borussia M'gladbach",'Dortmund':'Borussia Dortmund','Leverkusen':'Bayer Leverkusen','Freiburg':'Fribourg','Augsburg':'Augsbourg','Hamburg':'Hambourg','Werder Bremen':'Werder Brême','Mainz':'Mayence',
 'St Etienne':'Saint-Étienne','Sp Lisbon':'Sporting CP','Sp Braga':'SC Braga','Club Brugge':'Club Bruges','AEK':'AEK Athènes','Bodo/Glimt':'Bodø/Glimt'}
def norm(s): return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFD',s).encode('ascii','ignore').decode().lower())
def resolve(name,lg=None):
    n=CB2FD.get(name,name)
    if n in team_lg and (lg is None or team_lg[n]==lg): return n
    pool=[t for t,l in team_lg.items() if lg is None or l==lg]
    k=norm(n)
    for t in pool:
        if norm(t)==k: return t
    for t in pool:  # « Fenerbahce » dans « Fenerbahce SK », etc.
        if len(norm(t))>=4 and len(k)>=4 and (norm(t) in k or k in norm(t)): return t
    return None

# ---------- modèle par championnat : notes attaque/défense sur 70 % xG + 30 % buts (meilleur réglage au test) ----------
def target(r,b=0.7):
    if r['hx'] is None: return r
    return dict(r,hg=(1-b)*r['hg']+b*r['hx'],ag=(1-b)*r['ag']+b*r['ax'])
DC={lg:ratings.fit([target(r) for r in rs],now.date()+datetime.timedelta(days=1),365,8.0) for lg,rs in results.items()}
DC={k:v for k,v in DC.items() if v}

# ---------- forme, classement, derniers matchs, stats ----------
form,rank,size={},{},{}
for lg,rs in results.items():
    tab={}
    for r in rs:
        for team,gf,ga in ((r['h'],r['hg'],r['ag']),(r['a'],r['ag'],r['hg'])):
            t=tab.setdefault(team,[0,0,0]); t[0]+=3 if gf>ga else 1 if gf==ga else 0; t[1]+=gf-ga; t[2]+=gf
            form.setdefault(team,[]).append(('V' if gf>ga else 'N' if gf==ga else 'D',r['d']))
    for i,k in enumerate(sorted(tab,key=lambda k:(-tab[k][0],-tab[k][1],-tab[k][2]))): rank[k]=i+1; size[k]=len(tab)
form={k:''.join(x for x,_ in sorted(v,key=lambda y:y[1],reverse=True)[:5]) for k,v in form.items()}
def last(team,side=None,k=5):
    lg=team_lg.get(team); rs=[r for r in results.get(lg,[]) if (side in (None,'h') and r['h']==team) or (side in (None,'a') and r['a']==team)]
    rs=sorted(rs,key=lambda r:r['d'],reverse=True)[:k]
    opp=lambda r:r['a'] if r['h']==team else r['h']
    return [[r['d'],'D' if r['h']==team else 'E',SHOW.get(opp(r),opp(r)),r['hg'] if r['h']==team else r['ag'],r['ag'] if r['h']==team else r['hg']] for r in rs]
def fpts(team):
    l=last(team); return sum(3 if a>b else 1 if a==b else 0 for *_,a,b in l)/len(l)-1.4 if l else 0
def tstats(team,side):
    rs=[r for r in results.get(team_lg.get(team),[]) if r[side]==team]
    rs=[((r['hg'],r['ag']) if side=='h' else (r['ag'],r['hg'])) for r in rs]; n=len(rs)
    if not n: return None
    f=lambda c:round(sum(1 for x in rs if c(*x))/n,2)
    return [n,round(sum(x[0] for x in rs)/n,2),round(sum(x[1] for x in rs)/n,2),f(lambda a,b:a+b>2),f(lambda a,b:a>0 and b>0),f(lambda a,b:b==0),f(lambda a,b:a==0)]
# corners et cartons attendus : moyennes pour/contre de chaque équipe, ramenées vers la moyenne du championnat
def side_avgs(lg,key_h,key_a,K=4):
    rs=[r for r in results.get(lg,[]) if r.get(key_h) is not None]
    if len(rs)<20: return None
    mean=sum(r[key_h]+r[key_a] for r in rs)/len(rs)/2
    acc={}
    for r in rs:
        for t,f_,a_ in ((r['h'],r[key_h],r[key_a]),(r['a'],r[key_a],r[key_h])):
            x=acc.setdefault(t,[0,0,0]); x[0]+=f_; x[1]+=a_; x[2]+=1
    return mean,{t:((v[0]+K*mean)/(v[2]+K),(v[1]+K*mean)/(v[2]+K)) for t,v in acc.items()}
CORN={lg:side_avgs(lg,'hc','ac') for lg in results}; CARD={lg:side_avgs(lg,'hy','ay') for lg in results}
def expect(tab,lg,hk,ak):
    t=tab.get(lg)
    if not t or hk not in t[1] or ak not in t[1]: return None
    m,v=t; return [round((v[hk][0]+v[ak][1])/2,2),round((v[ak][0]+v[hk][1])/2,2)]
def goals_for(team):
    rs=[r for r in results.get(team_lg.get(team),[]) if team in (r['h'],r['a'])]
    return [sum(r['hg'] if r['h']==team else r['ag'] for r in rs),len(rs)]
sc={}
for t,v in scorers.items():
    k=resolve(t)
    if k: sc[k]=v

old={m['id']:m for m in prev.get('matches',[])+prev.get('past',[])}
def mkid(lg,h,a,w): return re.sub(r'\W+','-',f'{lg}-{h}-{a}-{w.date().isoformat()}'.lower())

def build(lg,comp,w,hk,ak,home,away,odds,mkt,cross=False):
    rec=dict(id=mkid(lg,hk or home,ak or away,w),lg=lg,comp=comp,when=w.isoformat(timespec='minutes'),home=home,away=away,hk=hk,ak=ak,odds=odds,mkt={k:v for k,v in mkt.items() if v})
    rec['open']=old.get(rec['id'],{}).get('open') or odds or rec['mkt']
    lh,la=team_lg.get(hk),team_lg.get(ak)
    if hk and ak and lh in DC and la in DC:
        if lh==la and not cross:
            xh,xa=ratings.lambdas(DC[lh],hk,ak); _,_,att,dfn,_=DC[lh]
            rec['rt']=[round(att.get(hk,1)*100),round(100/dfn.get(hk,1)),round(att.get(ak,1)*100),round(100/dfn.get(ak,1))]
            rec['lgH'],rec['lgA']=round(DC[lh][0],3),round(DC[lh][1],3)
        else:
            # coupe d'Europe : chaque équipe notée dans son propre championnat (moins fiable)
            mh,ma,ah,dh,_=DC[lh]; mh2,ma2,aa,da,_=DC[la]; mu_h=(mh+mh2)/2; mu_a=(ma+ma2)/2
            xh=mu_h*ah.get(hk,1)*da.get(ak,1); xa=mu_a*aa.get(ak,1)*dh.get(hk,1); rec['cross']=1
            rec['lgH'],rec['lgA']=round(mu_h,3),round(mu_a,3)
        fa=0.03*(fpts(hk)-fpts(ak))  # forme des 5 derniers matchs, petit poids (testé)
        rec['xh'],rec['xa']=round(xh*math.exp(fa),3),round(xa*math.exp(-fa),3)
        rec['gp']=[len(last(hk,k=99)),len(last(ak,k=99))]
        rec['xg']=1 if results[lh][0]['hx'] is not None else 0
    elif cross: rec['cross']=1
    for side,k in (('h',hk),('a',ak)):
        if not k: continue
        if k in form: rec[side+'f']=form[k]
        if k in rank and not rec.get('cross'): rec[side+'r']=rank[k]; rec['n']=size[k]
        if k in sc: rec[side+'s']=sc[k]
    if hk and last(hk): rec['hl'],rec['hh']=last(hk),last(hk,'h')
    if ak and last(ak): rec['al'],rec['aa']=last(ak),last(ak,'a')
    if hk and ak and team_lg.get(hk)==team_lg.get(ak):
        c=expect(CORN,lh,hk,ak); y=expect(CARD,lh,hk,ak)
        if c: rec['cc']=c
        if y: rec['cy']=y
    if hk and ak: rec['tg']=goals_for(hk)+goals_for(ak)  # buts marqués et matchs joués : base des cotes buteurs
    o=old.get(rec['id'],{})
    for k in ('lu','espn'):
        if k in o: rec[k]=o[k]  # compo déjà récupérée
    th,ta=(tstats(hk,'h') if hk else None),(tstats(ak,'a') if ak else None)
    if th and ta and not rec.get('cross'): rec['ts']=[th,ta]
    return rec

recs={}
for x in fix:
    if x['when']<now-datetime.timedelta(hours=2) or x['when']>now+datetime.timedelta(days=15): continue
    hk,ak=x['h'],x['a']
    r=build(x['lg'],fd.NAME[x['lg']],x['when'],hk,ak,SHOW.get(hk,hk),SHOW.get(ak,ak),None,x['mkt'])
    recs[r['id']]=r
CBLG={'Ligue 1':'F1','Ligue 2':'F2','Premier League':'E0','Liga':'SP1','Serie A':'I1','Bundesliga':'D1'}
MOIS={m:i+1 for i,m in enumerate('janvier février mars avril mai juin juillet août septembre octobre novembre décembre'.split())}
unmatched=set()
for m in betclic:
    if not m.get('odds'): continue
    d=re.search(r'(\d+) (\w+) (\d{4}) - (\d+):(\d+)',m['when'])
    w=datetime.datetime(int(d[3]),MOIS[d[2]],int(d[1]),int(d[4]),int(d[5]),tzinfo=PARIS)
    if w<now-datetime.timedelta(hours=2): continue
    lg=CBLG.get(m['comp'])
    hk,ak=resolve(m['home'],lg),resolve(m['away'],lg)
    for t,k in ((m['home'],hk),(m['away'],ak)):
        if not k: unmatched.add(t)
    odds=dict(h=m['odds'][0],d=m['odds'][1],a=m['odds'][2])
    home=SHOW.get(hk,hk) if hk else m['home']; away=SHOW.get(ak,ak) if ak else m['away']
    hit=None
    if lg and hk and ak:
        for r in recs.values():
            if r['lg']==lg and r['hk']==hk and r['ak']==ak and abs((datetime.datetime.fromisoformat(r['when'])-w).total_seconds())<36*3600: hit=r;break
    if hit:
        hit['odds']=odds; hit['when']=w.isoformat(timespec='minutes')
        if not old.get(hit['id'],{}).get('open'): hit['open']=odds
    else:
        r=build(lg or 'CL',m['comp'],w,hk,ak,home,away,odds,{},cross=not lg)
        recs[r['id']]=r
out=sorted(recs.values(),key=lambda r:r['when'])
if len(out)<40: sys.exit(f'Seulement {len(out)} matchs récupérés : données gardées telles quelles')

# ---------- archive : dernière cote avant le match + score final, 45 jours ----------
def score_for(m):
    hk,ak=m.get('hk'),m.get('ak'); d=datetime.datetime.fromisoformat(m['when']).date()
    for r in results.get(team_lg.get(hk),[]):
        if r['h']==hk and r['a']==ak and abs((datetime.date.fromisoformat(r['d'])-d).days)<=1: return [r['hg'],r['ag']]
    return None
upcoming=out
ids={u['id'] for u in upcoming}
past={m['id']:m for m in prev.get('past',[])}
for m in prev.get('matches',[]):
    if datetime.datetime.fromisoformat(m['when'])<=now and m['id'] not in ids: past[m['id']]=m
limit=now-datetime.timedelta(days=45)
past=[m for m in past.values() if datetime.datetime.fromisoformat(m['when'])>limit]
for m in past:
    if not m.get('score') and m.get('hk'):
        s=score_for(m)
        if s: m['score']=s
past.sort(key=lambda m:m['when'],reverse=True)
json.dump(dict(updated=now.isoformat(timespec='minutes'),
  source='Cotes Betclic relevées sur compare-bet.fr · autres cotes : moyenne des bookmakers, résultats et xG football-data.co.uk · buteurs soccerstats.com · actu Google Actualités',
  matches=upcoming,past=past),open(OUT,'w'),ensure_ascii=False)
print(len(upcoming),'matchs dans',len({r['comp'] for r in upcoming}),'compétitions ;',sum(1 for r in upcoming if r.get('odds')),'avec cotes Betclic ;',sum(1 for r in upcoming if r.get('xh')),'avec modèle ;',len(past),'archivés')
if unmatched: print('noms non reconnus :',sorted(unmatched))
