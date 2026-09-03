import pymupdf, json, re
SRC='/root/.claude/uploads/c357eb22-1ae1-5977-a6f1-0b941181983b/325d49e3-FINALE_DOGRU_KURS_AYT_DENEME_1A.pdf'
d=pymupdf.open(SRC)
SPLIT=310
QNUM=re.compile(r'^(\d{1,2})\.\s*$|^(\d{1,2})\.\t')
out=[]
for pi,p in enumerate(d,1):
    items=[]
    for b in p.get_text('dict')['blocks']:
        if b['type']!=0: continue
        for l in b['lines']:
            for s in l['spans']:
                if not s['text'].strip(): continue
                x0,y0,x1,y1=s['bbox']
                items.append(dict(page=pi,col=0 if x0<SPLIT else 1,x=round(x0,1),y=round(y0,1),
                                  sz=round(s['size'],1),c=hex(s['color']),font=s['font'],t=s['text']))
    items.sort(key=lambda s:(s['col'], round(s['y']/3), s['x']))
    out.append(items)
json.dump(out,open('spans.json','w'),ensure_ascii=False)
# print question-number candidates and answer letters
for items in out:
    for s in items:
        if s['sz']==7.2 and s['c']=='0xec008c':
            pass
# report per page: sequence of (qnum) and (answer letters)
for pi,items in enumerate(out,1):
    qs=[s['t'].strip() for s in items if QNUM.match(s['t']) and 'Bold' in s['font'] and s['sz']>=9]
    ans=[s['t'].strip() for s in items if s['sz']==7.2 and s['c']=='0xec008c' and re.fullmatch(r'[A-E]',s['t'].strip())]
    codes=[s['t'].strip() for s in items if s['sz']==7.2 and re.match(r'^56FN',s['t'].strip())]
    print(pi,'Q:',qs,'| ANS:',ans,'| ncodes:',len(codes))
