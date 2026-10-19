# Lecture des fichiers football-data.co.uk : résultats de la saison (avec xG quand disponibles) et matchs à venir.
import csv,io,datetime,re
from zoneinfo import ZoneInfo
LON,PARIS=ZoneInfo('Europe/London'),ZoneInfo('Europe/Paris')
MAIN={'F1':'Ligue 1','F2':'Ligue 2','E0':'Premier League','SP1':'Liga','I1':'Serie A','D1':'Bundesliga',
 'E1':'Championship','E2':'League One','E3':'League Two','D2':'2. Bundesliga','I2':'Serie B','SP2':'Liga 2',
 'N1':'Eredivisie','B1':'Jupiler Pro League','P1':'Liga Portugal','T1':'Süper Lig','G1':'Super League (Grèce)',
 'SC0':'Premiership (Écosse)','SC1':'Championship (Écosse)','SC2':'League One (Écosse)','SC3':'League Two (Écosse)'}
NEW={('Argentina','Liga Profesional'):('ARG','Liga Profesional (Argentine)'),('Austria','Bundesliga'):('AUT','Bundesliga (Autriche)'),
 ('Brazil','Serie A'):('BRA','Série A (Brésil)'),('China','Super League'):('CHN','Super League (Chine)'),('Denmark','Superliga'):('DNK','Superliga (Danemark)'),
 ('Finland','Veikkausliiga'):('FIN','Veikkausliiga (Finlande)'),('Ireland','Premier Division'):('IRL','Premier Division (Irlande)'),('Japan','J1 League'):('JPN','J1 League (Japon)'),
 ('Mexico','Liga MX'):('MEX','Liga MX (Mexique)'),('Norway','Eliteserien'):('NOR','Eliteserien (Norvège)'),('Poland','Ekstraklasa'):('POL','Ekstraklasa (Pologne)'),
 ('Romania','Superliga'):('ROU','Superliga (Roumanie)'),('Sweden','Allsvenskan'):('SWE','Allsvenskan (Suède)'),('USA','MLS'):('USA','MLS (États-Unis)'),('Switzerland','Super League'):('SWZ','Super League (Suisse)')}
NAME={k:v for k,v in MAIN.items()}; NAME.update({c:n for c,n in NEW.values()})

def rows(text):
    return list(csv.DictReader(io.StringIO(text.lstrip('﻿'))))
def when(d,t):
    dd=datetime.datetime.strptime(d,'%d/%m/%Y' if len(d.split('/')[-1])==4 else '%d/%m/%y')
    hh,mm=(t or '15:00').split(':')
    return dd.replace(hour=int(hh),minute=int(mm),tzinfo=LON).astimezone(PARIS)
def f(x):
    try: v=float(x); return v if v>1 else None
    except (TypeError,ValueError): return None
def num(x):
    try: return float(x)
    except (TypeError,ValueError): return None

def results_main(code,text):
    out=[]
    for r in rows(text):
        if not r.get('FTHG') or not r.get('HomeTeam'): continue
        w=when(r['Date'],r.get('Time'))
        out.append(dict(d=w.date().isoformat(),h=r['HomeTeam'],a=r['AwayTeam'],hg=int(r['FTHG']),ag=int(r['FTAG']),hx=num(r.get('HxG')),ax=num(r.get('AxG'))))
    return out
def results_new(text):
    rs=rows(text)
    rs=[r for r in rs if r.get('HG') not in (None,'') and r.get('Home')]
    if not rs: return []
    last=max(rs,key=lambda r:datetime.datetime.strptime(r['Date'],'%d/%m/%Y'))['Season']
    out=[]
    for r in rs:
        if r['Season']!=last: continue
        w=when(r['Date'],r.get('Time'))
        out.append(dict(d=w.date().isoformat(),h=r['Home'],a=r['Away'],hg=int(float(r['HG'])),ag=int(float(r['AG'])),hx=None,ax=None))
    return out

def fixtures(main_text,new_text):
    out=[]
    for r in rows(main_text):
        if r.get('Div') not in MAIN: continue
        out.append(dict(lg=r['Div'],when=when(r['Date'],r.get('Time')),h=r['HomeTeam'],a=r['AwayTeam'],
            mkt=dict(h=f(r.get('AvgH')),d=f(r.get('AvgD')),a=f(r.get('AvgA')),o25=f(r.get('Avg>2.5')),u25=f(r.get('Avg<2.5')))))
    for r in rows(new_text):
        k=NEW.get((r.get('Country'),r.get('League')))
        if not k: continue
        out.append(dict(lg=k[0],when=when(r['Date'],r.get('Time')),h=r['Home'],a=r['Away'],
            mkt=dict(h=f(r.get('AvgH')),d=f(r.get('AvgD')),a=f(r.get('AvgA')),o25=None,u25=None)))
    return out
