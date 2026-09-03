import pymupdf, json, re, os
SRC='/root/.claude/uploads/c357eb22-1ae1-5977-a6f1-0b941181983b/325d49e3-FINALE_DOGRU_KURS_AYT_DENEME_1A.pdf'
d=pymupdf.open(SRC)
# cover answer-key spans (magenta small) with white rects
n=0
for p in d:
    for b in p.get_text('dict')['blocks']:
        if b['type']!=0: continue
        for l in b['lines']:
            for s in l['spans']:
                if round(s['size'],1)<=7.6 and hex(s['color'])=='0xec008c':
                    r=pymupdf.Rect(s['bbox']); r.x0-=1; r.y0-=1; r.x1+=2; r.y1+=2
                    p.draw_rect(r,color=None,fill=(1,1,1),overlay=True); n+=1
print('redacted spans',n)
d.save('clean.pdf')
os.makedirs('pages',exist_ok=True)
c=pymupdf.open('clean.pdf')
for i,p in enumerate(c,1):
    p.get_pixmap(dpi=170).save(f'pages/p{i:02d}.png')
print('rendered',c.page_count)
