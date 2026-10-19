# Modèle de type Dixon-Coles : une note d'attaque et de défense par équipe,
# estimée sur les résultats de la saison, les matchs récents comptant plus.
import math,datetime
RHO=-0.08  # correction des petits scores (0-0, 1-0, 0-1, 1-1)

def fit(rs,asof,half_life=100,K=4.0,iters=40):
    """rs : [{d,h,a,hg,ag}] ; asof : date (exclue). Renvoie mu_h, mu_a, att, dfn, n."""
    rs=[r for r in rs if datetime.date.fromisoformat(r['d'])<asof]
    if len(rs)<10: return None
    w=[0.5**((asof-datetime.date.fromisoformat(r['d'])).days/half_life) for r in rs]
    W=sum(w); mu_h=sum(x*r['hg'] for x,r in zip(w,rs))/W; mu_a=sum(x*r['ag'] for x,r in zip(w,rs))/W
    teams={t for r in rs for t in (r['h'],r['a'])}
    att={t:1.0 for t in teams}; dfn={t:1.0 for t in teams}; n={t:0 for t in teams}
    for r in rs: n[r['h']]+=1; n[r['a']]+=1
    for _ in range(iters):
        # K matchs fictifs « moyens » par équipe : évite les notes extrêmes en début de saison
        num={t:K for t in teams}; den={t:K for t in teams}
        for x,r in zip(w,rs):
            num[r['h']]+=x*r['hg']; den[r['h']]+=x*mu_h*dfn[r['a']]
            num[r['a']]+=x*r['ag']; den[r['a']]+=x*mu_a*dfn[r['h']]
        att={t:num[t]/den[t] for t in teams}
        num={t:K for t in teams}; den={t:K for t in teams}
        for x,r in zip(w,rs):
            num[r['h']]+=x*r['ag']; den[r['h']]+=x*mu_a*att[r['a']]
            num[r['a']]+=x*r['hg']; den[r['a']]+=x*mu_h*att[r['h']]
        dfn={t:num[t]/den[t] for t in teams}
        ma=sum(att.values())/len(att); md=sum(dfn.values())/len(dfn)
        att={t:v/ma for t,v in att.items()}; dfn={t:v/md for t,v in dfn.items()}
    return mu_h,mu_a,att,dfn,n

def lambdas(model,home,away):
    mu_h,mu_a,att,dfn,_=model
    return mu_h*att.get(home,1)*dfn.get(away,1), mu_a*att.get(away,1)*dfn.get(home,1)

def probs(lh,la,rho=RHO,maxg=10):
    P=lambda k,l:math.exp(-l)*l**k/math.factorial(k)
    ph=pd=pa=po=pb=0.0
    for i in range(maxg+1):
        for j in range(maxg+1):
            p=P(i,lh)*P(j,la)
            if i==0 and j==0: p*=1-lh*la*rho
            elif i==0 and j==1: p*=1+lh*rho
            elif i==1 and j==0: p*=1+la*rho
            elif i==1 and j==1: p*=1-rho
            if i>j: ph+=p
            elif i==j: pd+=p
            else: pa+=p
            if i+j>2: po+=p
            if i>0 and j>0: pb+=p
    t=ph+pd+pa
    return ph/t,pd/t,pa/t,po/t,pb/t
