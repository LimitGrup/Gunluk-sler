# -*- coding: utf-8 -*-
import json, re, collections
Q=json.load(open('questions.json'))
K=json.load(open('answerkey.json'))
order=[]
for t,n in [('T1',40),('T2',46),('T3',40),('T4',40)]:
    order+= [f'{t}-{i}' for i in range(1,n+1)]

print('== 1) SEÇENEK HARFİ KONTROLÜ (A-E eksiksiz ve sıralı) ==')
prob=[]
for k in order:
    txt=Q[k]['text']
    found=[m.group(1) for m in re.finditer(r'([A-E])\)', txt)]
    # dedupe consecutive
    if found!=['A','B','C','D','E']:
        prob.append((k,Q[k]['page'],found))
for p in prob: print('  ',p)
print('  toplam sorunlu:',len(prob))

print('== 2) ÖNCÜL NUMARALANDIRMA: küçük L (l., ll., lll.) kullanımı ==')
lprob=[]
for k in order:
    t=Q[k]['text']
    if re.search(r'(?<![A-Za-zçğıöşüÇĞİÖŞÜ])l{1,3}\.\s', t):
        hits=re.findall(r'(?<![A-Za-zçğıöşüÇĞİÖŞÜ])(l{1,3})\.\s', t)
        lprob.append((k,Q[k]['page'],hits))
for p in lprob: print('  ',p)
print('  toplam:',len(lprob))

print('== 3) ROMEN I/II/III kullanan sorular (karşılaştırma) ==')
iprob=[k for k in order if re.search(r'(?<![A-Za-z])I{1,3}\.\s', Q[k]['text'])]
print('  I./II./III. kullanan soru sayısı:',len(iprob))

print('== 4) SEÇENEK METNİ TEKRARI (aynı soru içinde) ==')
dups=[]
for k in order:
    t=Q[k]['text']
    parts=re.split(r'\b([A-E])\)\s*',t)
    opts={}
    for i in range(1,len(parts)-1,2):
        opts[parts[i]]=re.sub(r'\s+',' ',parts[i+1]).strip()
    vals=collections.Counter(v for v in opts.values() if len(v)>2)
    for v,c in vals.items():
        if c>1: dups.append((k,Q[k]['page'],v[:60],c))
for d in dups: print('  ',d)
print('  toplam:',len(dups))

print('== 5) CEVAP ANAHTARI DAĞILIMI ==')
for t,n in [('T1',40),('T2',46),('T3',40),('T4',40)]:
    c=collections.Counter(K[f'{t}-{i}'] for i in range(1,n+1))
    print('  ',t,dict(sorted(c.items())),'toplam',sum(c.values()))
allc=collections.Counter(K.values()); print('   GENEL',dict(sorted(allc.items())),'toplam',sum(allc.values()))
print('== 5b) ÜST ÜSTE AYNI HARF (>=5) ==')
for t,n in [('T1',40),('T2',46),('T3',40),('T4',40)]:
    s=''.join(K[f'{t}-{i}'] for i in range(1,n+1))
    for m in re.finditer(r'(.)\1{4,}', s):
        print('  ',t,'soru',m.start()+1,'-',m.end(),'harf',m.group(1),'x',len(m.group(0)))

print('== 6) TİPOGRAFİ: çift boşluk / noktalama öncesi boşluk ==')
tip=collections.Counter()
for k in order:
    t=Q[k]['text']
    if re.search(r'\s[,;:!?]', t): tip['noktalama_oncesi_bosluk']+=1
    if '  ' in t: tip['cift_bosluk']+=1
    if re.search(r"[a-zçğıöşü]'[a-zçğıöşü]", t): tip['kesme_kucuk_harf']+=1
print('  ',dict(tip))

print('== 7) APOSTROF TÜRLERİ ==')
ap=collections.Counter()
for k in order:
    for ch in Q[k]['text']:
        if ch in "'’‘`´": ap[ch]+=1
print('  ',dict(ap))

print('== 8) SORU METNİ TEKRARI (testler arası) ==')
norm={}
for k in order:
    n=re.sub(r'\W+','',Q[k]['text'])[:120]
    norm.setdefault(n,[]).append(k)
for n,ks in norm.items():
    if len(ks)>1: print('  TEKRAR:',ks)
print('== 9) SORU SAYISI ==')
print('  toplam',len(order),' T1=40 T2=46 T3=40 T4=40')
