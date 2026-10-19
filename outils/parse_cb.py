import sys,re,json,html
out=[]
for path,comp in zip(sys.argv[1::2],sys.argv[2::2]):
    s=open(path,encoding='utf-8',errors='ignore').read()
    for m in re.finditer(r'<h2[^>]*>([^<]+ - [^<]+)</h2>\s*<p class="date">([^<]+)</p>(.*?)</table>',s,re.S):
        name,date,blk=html.unescape(m.group(1)).strip(),m.group(2).strip(),m.group(3)
        row=re.search(r'alt="Betclic".*?<td class="cote[^"]*">([\d.]+)</td><td class="cote[^"]*">([\d.]+)</td><td class="cote[^"]*">([\d.]+)</td>',blk,re.S)
        h,a=name.split(' - ',1)
        out.append({'comp':comp,'home':h.strip(),'away':a.strip(),'when':re.sub(r'\s+',' ',date),'odds':[float(x) for x in row.groups()] if row else None})
print(json.dumps(out,ensure_ascii=False,indent=0))
