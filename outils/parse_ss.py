def _read(p):
    b=open(p,"rb").read()
    try: return b.decode("utf-8")
    except UnicodeDecodeError: return b.decode("cp1252",errors="replace")
import sys,re,html,json
res={}
for path in sys.argv[1:]:
    lg=path.split('/')[-1][:-5]
    s=_read(path)
    tabs=[];cur=None
    for r in re.findall(r'<tr[^>]*>(.*?)</tr>',s,re.S):
        c=[re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',x))).strip() for x in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>',r,re.S)]
        if c[:11]==['','','GP','W','D','L','GF','GA','GD','Pts','PPG'] and len(c)==11:
            cur=[];tabs.append(cur);continue
        if cur is not None and len(c)==11 and c[0].isdigit():
            cur.append(c)
        elif cur is not None and cur and len(c)!=11: cur=None
    home,away=tabs[0],tabs[1]
    t={}
    for side,tb in (('h',home),('a',away)):
        for c in tb: t.setdefault(c[1],{})[side]=[int(c[2]),int(c[6]),int(c[7])]
    res[lg]=t
print(json.dumps(res,ensure_ascii=False))
