import pymupdf, json, re, os
QRE=re.compile(r'^(\d{1,2})\.(\s|\t|$)')
SPLIT=310
TESTS=[('T1',2,10),('T2',11,20),('T3',21,30),('T4',31,40)]
def testof(pg):
    for t in TESTS:
        if t[1]<=pg<=t[2]: return t[0]
c=pymupdf.open('clean.pdf')
os.makedirs('q',exist_ok=True)
meta={}
for pi,p in enumerate(c,1):
    T=testof(pi)
    if not T: continue
    cols={0:[],1:[]}
    for b in p.get_text('dict')['blocks']:
        if b['type']!=0: continue
        for l in b['lines']:
            for s in l['spans']:
                if not s['text'].strip(): continue
                x0,y0,x1,y1=s['bbox']
                if y0<95 or y0>735: continue
                if round(s['size'],1)==30.0: continue
                cols[0 if x0<SPLIT else 1].append((x0,y0,s))
    for ci in (0,1):
        sp=sorted(cols[ci],key=lambda z:(round(z[1]/3),z[0]))
        starts=[]
        for i,(x0,y0,s) in enumerate(sp):
            m=QRE.match(s['text'])
            if m and 'Bold' in s['font'] and round(s['size'],1)>=9.0 and x0<(60 if ci==0 else 330):
                starts.append((y0,int(m.group(1))))
        for k,(y0,num) in enumerate(starts):
            y1=starts[k+1][0]-4 if k+1<len(starts) else 738
            X0,X1=(28,308) if ci==0 else (312,592)
            r=pymupdf.Rect(X0,max(y0-8,92),X1,min(y1,740))
            fn=f'q/{T}_{num:02d}.png'
            p.get_pixmap(dpi=260,clip=r).save(fn)
            meta[f'{T}-{num}']=dict(file=os.path.abspath(fn),page=pi,rect=[round(v,1) for v in r])
json.dump(meta,open('crops.json','w'),indent=1)
print(len(meta),'crops')
