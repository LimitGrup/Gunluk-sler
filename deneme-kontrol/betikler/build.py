import pymupdf, json, re, os
SRC='/root/.claude/uploads/c357eb22-1ae1-5977-a6f1-0b941181983b/325d49e3-FINALE_DOGRU_KURS_AYT_DENEME_1A.pdf'
d=pymupdf.open(SRC)
SPLIT=310
QRE=re.compile(r'^(\d{1,2})\.(\s|\t|$)')

TESTS=[('T1','Türk Dili ve Edebiyatı-Sosyal Bilimler-1',2,10,40),
       ('T2','Sosyal Bilimler-2',11,20,46),
       ('T3','Matematik',21,30,40),
       ('T4','Fen Bilimleri',31,40,40)]
def testof(pg):
    for t in TESTS:
        if t[2]<=pg<=t[3]: return t
    return None

questions={}
for pi,p in enumerate(d,1):
    T=testof(pi)
    if not T: continue
    cols={0:[],1:[]}
    for b in p.get_text('dict')['blocks']:
        if b['type']!=0: continue
        for l in b['lines']:
            for s in l['spans']:
                if not s['text'].strip(): continue
                x0,y0,x1,y1=s['bbox']
                if y0<95 or y0>735: continue   # header/footer
                if round(s['size'],1)==30.0: continue  # big 'A' watermark
                cols[0 if x0<SPLIT else 1].append(dict(x=x0,y=y0,sz=round(s['size'],1),c=hex(s['color']),font=s['font'],t=s['text']))
    for ci in (0,1):
        sp=sorted(cols[ci],key=lambda s:(round(s['y']/3),s['x']))
        # find question starts
        starts=[]
        for i,s in enumerate(sp):
            m=QRE.match(s['t'])
            if m and 'Bold' in s['font'] and s['sz']>=9.0 and s['x']<(60 if ci==0 else 330):
                starts.append((i,int(m.group(1))))
        for k,(i,num) in enumerate(starts):
            j=starts[k+1][0] if k+1<len(starts) else len(sp)
            body=sp[i:j]
            ans=None; lines=[]
            for s in body:
                txt=s['t']
                if s['sz']<=7.6 and s['c']=='0xec008c':
                    st=txt.strip()
                    if re.fullmatch(r'[A-E]',st): ans=st
                    continue
                if s['sz']<=7.6 and re.match(r'^56FN',txt.strip()): continue
                lines.append(txt)
            raw=''.join(lines)
            raw=re.sub(r'\t+',' ',raw); raw=re.sub(r'[ ]{2,}',' ',raw).strip()
            key=(T[0],num)
            questions[key]=dict(test=T[0],testname=T[1],num=num,page=pi,col=ci,ans=ans,text=raw)

print('total questions:',len(questions))
for t in TESTS:
    got=sorted(n for (tt,n) in questions if tt==t[0])
    missing=[i for i in range(1,t[4]+1) if i not in got]
    print(t[0],t[1],'count',len(got),'missing',missing,'extra',[n for n in got if n>t[4]])
noans=[k for k,v in questions.items() if not v['ans']]
print('no answer:',noans)
json.dump({f'{k[0]}-{k[1]}':v for k,v in questions.items()},open('questions.json','w'),ensure_ascii=False,indent=1)
