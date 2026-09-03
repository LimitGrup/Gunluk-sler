import json, os, re
Q=json.load(open('questions.json'))
C=json.load(open('crops.json'))
BASE=os.path.abspath('.')
os.makedirs('chunks',exist_ok=True)
os.makedirs('pagetxt',exist_ok=True)

SUB={'T1':[(1,24,'Türk Dili ve Edebiyatı'),(25,34,'Tarih-1'),(35,40,'Coğrafya-1')],
     'T2':[(1,11,'Tarih-2'),(12,22,'Coğrafya-2'),(23,34,'Felsefe Grubu'),(35,40,'Din Kültürü ve Ahlak Bilgisi'),(41,46,'DKAB almayanlar için ek sorular (Felsefe/Psikoloji vb.)')],
     'T3':[(1,40,'Matematik')],
     'T4':[(1,14,'Fizik'),(15,27,'Kimya'),(28,40,'Biyoloji')]}
TN={'T1':'Türk Dili ve Edebiyatı-Sosyal Bilimler-1 Testi','T2':'Sosyal Bilimler-2 Testi','T3':'Matematik Testi','T4':'Fen Bilimleri Testi'}
def sub(t,n):
    for a,b,s in SUB[t]:
        if a<=n<=b: return s
    return '?'

def qblock(t,n):
    k=f'{t}-{n}'; q=Q[k]; c=C[k]
    return (f"\n### SORU {t}-{n}  (Test: {TN[t]} | Alan: {sub(t,n)} | Kitapçık sayfası: {q['page']})\n"
            f"GÖRSEL DOSYA (mutlaka Read ile aç): {c['file']}\n"
            f"METİN (PDF metin katmanından, şekil/grafik içerikleri EKSİK olabilir):\n{q['text']}\n")

def write_chunks(tag, plan):
    files=[]
    for i,(t,a,b) in enumerate(plan,1):
        fn=f'chunks/{tag}_{i:02d}.md'
        body=f"# ÇÖZÜM PAKETİ {tag}_{i:02d} — {TN[t]}, sorular {a}-{b}\n"
        for n in range(a,b+1): body+=qblock(t,n)
        open(fn,'w').write(body)
        files.append(dict(id=f'{tag}_{i:02d}',file=os.path.abspath(fn),test=t,testname=TN[t],a=a,b=b,
                          qids=[f'{t}-{n}' for n in range(a,b+1)]))
    return files

planA=[('T1',1,8),('T1',9,16),('T1',17,24),('T1',25,32),('T1',33,40),
       ('T2',1,8),('T2',9,16),('T2',17,24),('T2',25,32),('T2',33,40),('T2',41,46),
       ('T3',1,5),('T3',6,10),('T3',11,15),('T3',16,20),('T3',21,25),('T3',26,30),('T3',31,35),('T3',36,40),
       ('T4',1,5),('T4',6,10),('T4',11,14),('T4',15,19),('T4',20,23),('T4',24,27),('T4',28,32),('T4',33,36),('T4',37,40)]
planB=[('T1',1,6),('T1',7,13),('T1',14,20),('T1',21,27),('T1',28,34),('T1',35,40),
       ('T2',1,6),('T2',7,12),('T2',13,19),('T2',20,26),('T2',27,33),('T2',34,40),('T2',41,46),
       ('T3',1,6),('T3',7,12),('T3',13,18),('T3',19,24),('T3',25,30),('T3',31,35),('T3',36,40),
       ('T4',1,7),('T4',8,14),('T4',15,21),('T4',22,27),('T4',28,34),('T4',35,40)]
A=write_chunks('A',planA); B=write_chunks('B',planB)
assert sorted(x for c in A for x in c['qids'])==sorted(Q.keys())
assert sorted(x for c in B for x in c['qids'])==sorted(Q.keys())

# per-question single files (for adjudication)
os.makedirs('single',exist_ok=True)
for k in Q:
    t,n=k.split('-'); n=int(n)
    open(f'single/{k}.md','w').write(qblock(t,n))

# page payloads for redaction
import pymupdf
d=pymupdf.open('clean.pdf')
pages=[]
for pi,p in enumerate(d,1):
    txt=p.get_text()
    open(f'pagetxt/p{pi:02d}.txt','w').write(txt)
    pages.append(dict(page=pi,txt=os.path.abspath(f'pagetxt/p{pi:02d}.txt'),img=os.path.abspath(f'pages/p{pi:02d}.png')))
json.dump(dict(A=A,B=B,pages=pages,base=BASE),open('plan.json','w'),ensure_ascii=False,indent=1)
key={k:v['ans'] for k,v in Q.items()}
json.dump(key,open('answerkey.json','w'),indent=1)
print('chunksA',len(A),'chunksB',len(B),'pages',len(pages))
print(json.dumps(key,ensure_ascii=False)[:200])
