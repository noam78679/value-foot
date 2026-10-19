# Génère les icônes PNG de l'app (sans dépendance) : ballon blanc sur dégradé orange
import zlib,struct,math,sys
def png(n,path):
    S=3;bg=None;rows=[]
    pent=[(math.cos(math.radians(-90+72*k))*0.13,math.sin(math.radians(-90+72*k))*0.13) for k in range(5)]
    def inpoly(x,y,P):
        c=False
        for i in range(len(P)):
            (x1,y1),(x2,y2)=P[i],P[i-1]
            if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:c=not c
        return c
    for j in range(n):
        row=bytearray([0])
        for i in range(n):
            acc=[0,0,0]
            for sj in range(S):
                for si in range(S):
                    x=(i+(si+.5)/S)/n-.5;y=(j+(sj+.5)/S)/n-.5;r=math.hypot(x,y)
                    col=(255,int(106+(179-106)*(x+y+1)/2),int(43+(35-43)*(x+y+1)/2))
                    if r<0.33: col=(255,255,255)
                    if inpoly(x,y,pent): col=(6,8,13)
                    for a in range(5):
                        ang=math.radians(-90+72*a);px,py=math.cos(ang)*0.29,math.sin(ang)*0.29
                        if r<0.33 and math.hypot(x-px,y-py)<0.07: col=(6,8,13)
                    acc=[acc[k]+col[k] for k in range(3)]
            row+=bytes(v//(S*S) for v in acc)
        rows.append(bytes(row))
    raw=zlib.compress(b''.join(rows),9)
    ch=lambda t,d:struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',n,n,8,2,0,0,0))+ch(b'IDAT',raw)+ch(b'IEND',b''))
for n in (180,192,512): png(n,f'icone-{n}.png')
