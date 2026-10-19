# usage: python3 outils/test-modele.py results.json — teste le modèle sur les matchs déjà joués (log loss, plus bas = mieux)
import json,sys,math,datetime
sys.path.insert(0,'outils'); import ratings as R
res=json.load(open(sys.argv[1]))
def run(K,hl,rho):
    LL=0;LL0=0;n=0;br=0
    for lg,rs in res.items():
        dates=sorted({r['d'] for r in rs})
        for d in dates:
            asof=datetime.date.fromisoformat(d)
            prior=[r for r in rs if r['d']<d]
            if len(prior)<3*len({t for r in rs for t in (r['h'],r['a'])})//2: continue
            m=R.fit(prior,asof,hl,K,25)
            H=sum(r['hg']>r['ag'] for r in prior)/len(prior);D=sum(r['hg']==r['ag'] for r in prior)/len(prior);A=1-H-D
            for r in rs:
                if r['d']!=d: continue
                lh,la=R.lambdas(m,r['h'],r['a']);ph,pd,pa,_,_=R.probs(lh,la,rho)
                o=0 if r['hg']>r['ag'] else 1 if r['hg']==r['ag'] else 2
                p=[ph,pd,pa][o];p0=[H,D,A][o]
                LL+=-math.log(max(p,1e-9));LL0+=-math.log(p0);n+=1
                br+=sum(((x-(1 if i==o else 0))**2) for i,x in enumerate([ph,pd,pa]))
    return n,LL/n,LL0/n,br/n
for K in (2,4,8):
    for hl in (60,100,365):
        n,ll,ll0,b=run(K,hl,-0.08)
        print(f"K={K} demi-vie={hl}j  matchs={n}  logloss={ll:.4f} (base {ll0:.4f})  brier={b:.4f}")
print('---')
for K in (12,16,24):
    n,ll,ll0,b=run(K,365,-0.08);print(f"K={K} demi-vie=365j logloss={ll:.4f} brier={b:.4f}")
for rho in (0,-0.13):
    n,ll,ll0,b=run(12,365,rho);print(f"K=12 rho={rho} logloss={ll:.4f}")
# ancien modèle (moyennes domicile/extérieur régressées) pour comparaison
def old():
    LL=0;n=0
    for lg,rs in res.items():
        for d in sorted({r['d'] for r in rs}):
            prior=[r for r in rs if r['d']<d]
            if len(prior)<3*len({t for r in rs for t in (r['h'],r['a'])})//2: continue
            t={}
            for r in prior:
                a=t.setdefault(r['h'],{'h':[0,0,0],'a':[0,0,0]});a['h'][0]+=1;a['h'][1]+=r['hg'];a['h'][2]+=r['ag']
                b=t.setdefault(r['a'],{'h':[0,0,0],'a':[0,0,0]});b['a'][0]+=1;b['a'][1]+=r['ag'];b['a'][2]+=r['hg']
            lgH=sum(r['hg'] for r in prior)/len(prior);lgA=sum(r['ag'] for r in prior)/len(prior)
            def rates(s,K=6,K0=10):
                gp=s['h'][0]+s['a'][0];lgAll=(lgH+lgA)/2
                gf=(s['h'][1]+s['a'][1]+K0*lgAll)/(gp+K0);ga=(s['h'][2]+s['a'][2]+K0*lgAll)/(gp+K0)
                return dict(hGF=(s['h'][1]+K*gf*lgH/lgAll)/(s['h'][0]+K),hGA=(s['h'][2]+K*ga*lgA/lgAll)/(s['h'][0]+K),aGF=(s['a'][1]+K*gf*lgA/lgAll)/(s['a'][0]+K),aGA=(s['a'][2]+K*ga*lgH/lgAll)/(s['a'][0]+K))
            for r in rs:
                if r['d']!=d or r['h'] not in t or r['a'] not in t: continue
                h=rates(t[r['h']]);a=rates(t[r['a']])
                lh=h['hGF']*a['aGA']/lgH;la=a['aGF']*h['hGA']/lgA
                ph,pd,pa,_,_=R.probs(lh,la,0)
                o=0 if r['hg']>r['ag'] else 1 if r['hg']==r['ag'] else 2
                LL+=-math.log([ph,pd,pa][o]);n+=1
    return n,LL/n
print('ancien modèle',old())
def blend(K=8,hl=365,rho=-0.08,wdc=0.5):
    LL=0;n=0;out=[]
    for lg,rs in res.items():
        for d in sorted({r['d'] for r in rs}):
            prior=[r for r in rs if r['d']<d]
            if len(prior)<3*len({t for r in rs for t in (r['h'],r['a'])})//2: continue
            m=R.fit(prior,datetime.date.fromisoformat(d),hl,K,25)
            t={}
            for r in prior:
                a=t.setdefault(r['h'],{'h':[0,0,0],'a':[0,0,0]});a['h'][0]+=1;a['h'][1]+=r['hg'];a['h'][2]+=r['ag']
                b=t.setdefault(r['a'],{'h':[0,0,0],'a':[0,0,0]});b['a'][0]+=1;b['a'][1]+=r['ag'];b['a'][2]+=r['hg']
            lgH=sum(r['hg'] for r in prior)/len(prior);lgA=sum(r['ag'] for r in prior)/len(prior)
            def rates(s,K=6,K0=10):
                gp=s['h'][0]+s['a'][0];lgAll=(lgH+lgA)/2
                gf=(s['h'][1]+s['a'][1]+K0*lgAll)/(gp+K0);ga=(s['h'][2]+s['a'][2]+K0*lgAll)/(gp+K0)
                return dict(hGF=(s['h'][1]+K*gf*lgH/lgAll)/(s['h'][0]+K),hGA=(s['h'][2]+K*ga*lgA/lgAll)/(s['h'][0]+K),aGF=(s['a'][1]+K*gf*lgA/lgAll)/(s['a'][0]+K),aGA=(s['a'][2]+K*ga*lgH/lgAll)/(s['a'][0]+K))
            for r in rs:
                if r['d']!=d or r['h'] not in t or r['a'] not in t: continue
                h=rates(t[r['h']]);a=rates(t[r['a']])
                l1=(h['hGF']*a['aGA']/lgH,a['aGF']*h['hGA']/lgA); l2=R.lambdas(m,r['h'],r['a'])
                lh=(1-wdc)*l1[0]+wdc*l2[0]; la=(1-wdc)*l1[1]+wdc*l2[1]
                ph,pd,pa,_,_=R.probs(lh,la,rho)
                o=0 if r['hg']>r['ag'] else 1 if r['hg']==r['ag'] else 2
                LL+=-math.log([ph,pd,pa][o]);n+=1
    return n,LL/n
for wdc in (0,0.5):
    for rho in (0,-0.08):
        print('mélange wdc',wdc,'rho',rho,blend(8,365,rho,wdc))
