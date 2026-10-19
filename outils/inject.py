# usage: inject.py data.json page.html  — remplace les données intégrées à l'app
import sys,re
d=open(sys.argv[1],encoding='utf-8').read().replace('</','<\\/')
p=open(sys.argv[2],encoding='utf-8').read()
p2,n=re.subn(r'(<script id="data" type="application/json">).*?(</script>)',lambda m:m.group(1)+d+m.group(2),p,flags=re.S)
assert n==1; open(sys.argv[2],'w',encoding='utf-8').write(p2)
