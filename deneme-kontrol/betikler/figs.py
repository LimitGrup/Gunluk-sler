# -*- coding: utf-8 -*-
import pymupdf, json, re
Q=json.load(open('questions.json')); C=json.load(open('crops.json'))
d=pymupdf.open('clean.pdf')
REF=re.compile(r'(Aşağıda|aşağıda|Şekil|şekil|grafi|Grafi|tablo|Tablo|harita|Harita|görsel|Görsel|çizim|düzlem|koordinat|şema|Şema|verilmiştir|gösterilmiştir)')
STRONG=re.compile(r'(Aşağıda(ki)?\s|[Şş]ekil(de|deki)?\b|grafi[kğ]|tablo(da|daki)?\b|harita(da|daki)?\b|şema)')
rows=[]
for pi,p in enumerate(d,1):
    draws=p.get_drawings()
    imgs=[p.get_image_bbox(i) for i in p.get_images(full=True)] if p.get_images() else []
    for k,c in C.items():
        if c['page']!=pi: continue
        r=pymupdf.Rect(c['rect'])
        nd=sum(1 for dr in draws if r.intersects(dr['rect']) and dr['rect'].get_area()>4)
        ni=sum(1 for b in imgs if r.intersects(b))
        txt=Q[k]['text']
        needs=bool(STRONG.search(txt))
        rows.append((k,pi,nd,ni,needs,len(txt)))
susp=[r for r in rows if r[4] and r[2]<3 and r[3]==0]
print('== Şekil/grafik REFERANSI olup çizim bulunmayan sorular ==')
for r in susp: print('  ',r[0],'s.'+str(r[1]),'çizim=',r[2],'img=',r[3],'|',Q[r[0]]['text'][:90])
print('  toplam:',len(susp))
print()
print('== Çok kısa metinli sorular (olası eksik metin) ==')
for r in sorted(rows,key=lambda x:x[5])[:8]:
    print('  ',r[0],'s.'+str(r[1]),'uzunluk',r[5],'|',Q[r[0]]['text'][:100])
print()
print('== Çizim yoğunluğu olan soru sayısı ==')
print('  çizimli:',sum(1 for r in rows if r[2]>=3),'/',len(rows))
