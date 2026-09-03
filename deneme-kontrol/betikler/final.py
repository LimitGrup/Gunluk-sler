# -*- coding: utf-8 -*-
import json, collections, os, html
BASE=os.path.dirname(os.path.abspath(__file__))
P1=json.load(open(f'{BASE}/phase1.json')); P2=json.load(open(f'{BASE}/phase2.json'))
Q=json.load(open(f'{BASE}/questions.json')); KEY=json.load(open(f'{BASE}/answerkey.json'))
RED=json.load(open(f'{BASE}/red_dedup.json')); OVR=json.load(open(f'{BASE}/overrides.json'))
DET=json.load(open(f'{BASE}/deterministik.json'))

TN={'T1':'Türk Dili ve Edebiyatı-Sosyal Bilimler-1','T2':'Sosyal Bilimler-2','T3':'Matematik','T4':'Fen Bilimleri'}
TSHORT={'T1':'TDE-Sos-1','T2':'Sos-2','T3':'Matematik','T4':'Fen Bil.'}
SUB={'T1':[(1,24,'Türk Dili ve Edebiyatı'),(25,34,'Tarih-1'),(35,40,'Coğrafya-1')],
     'T2':[(1,11,'Tarih-2'),(12,22,'Coğrafya-2'),(23,34,'Felsefe Grubu'),(35,40,'Din Kültürü'),(41,46,'DKAB Almayanlar')],
     'T3':[(1,40,'Matematik')],'T4':[(1,14,'Fizik'),(15,27,'Kimya'),(28,40,'Biyoloji')]}
COUNTS={'T1':40,'T2':46,'T3':40,'T4':40}
ORDER=[f'{t}-{i}' for t in ['T1','T2','T3','T4'] for i in range(1,COUNTS[t]+1)]
ONEM={'KRITIK':0,'KRİTİK':0,'YUKSEK':1,'YÜKSEK':1,'ORTA':2,'DUSUK':3,'DÜŞÜK':3}
TRLBL={'KRITIK':'KRİTİK','YUKSEK':'YÜKSEK','DUSUK':'DÜŞÜK','ORTA':'ORTA','KRİTİK':'KRİTİK','YÜKSEK':'YÜKSEK','DÜŞÜK':'DÜŞÜK'}
def sub(t,n):
    for a,b,s in SUB[t]:
        if a<=n<=b: return s
def esc(x): return html.escape(str(x if x is not None else '')).replace('\n',' ').strip()
def testof(p):
    return 'T1' if 2<=p<=10 else 'T2' if 11<=p<=20 else 'T3' if 21<=p<=30 else 'T4' if 31<=p<=40 else None

A=P1['solveA']; B=P1['solveB']
KAR={k['qid']:k['verdict'] for k in P2['kararlar'] if k}
V={s['idx']:s for s in P2['redVerdicts']}

# ---------- redaksiyon: doğrulama + Claude override
red=[]
elenen=0; override_elenen=0; override_onem=0
for r in RED:
    v=V.get(r['idx'])
    if v is None: continue
    gecerli=bool(v.get('gecerli')); onem=v.get('duzeltilmis_onem') or r.get('onem') or 'DUSUK'
    ov_note=''
    for rule in OVR['kurallar']:
        m=rule['eslesme']
        if r.get('sayfa')==m['sayfa'] and str(r.get('soru'))==m['soru']:
            if rule['islem']=='GECERSIZ' and gecerli:
                gecerli=False; override_elenen+=1
            elif rule['islem']=='ONEM_DEGISTIR' and gecerli:
                if onem!=rule['yeni_onem']: override_onem+=1
                onem=rule['yeni_onem']; ov_note=' [Önem, Claude tarafından yapılan yüksek çözünürlüklü görsel doğrulama sonucu güncellenmiştir.]'
    if not gecerli:
        elenen+=1; continue
    p=r.get('sayfa'); t=testof(p)
    red.append(dict(sayfa=p,test=t,ders=(TSHORT[t] if t else 'Kapak'),soru=str(r.get('soru')),
        mevcut=(v.get('duzeltilmis_mevcut') or r.get('mevcut') or '').strip()[:250],
        tur=(v.get('duzeltilmis_hata_turu') or r.get('hata_turu') or '')[:110],
        onerilen=(v.get('duzeltilmis_oneri') or r.get('onerilen') or '')[:250],
        aciklama=((v.get('duzeltilmis_gerekce') or r.get('gerekce') or '')[:320]+ov_note),
        onem=TRLBL.get(onem,onem),kategori=v.get('kategori') or r.get('kategori'),
        tdk=bool(v.get('tdk_gerekli'))))

# deterministik bulguları redaksiyona ekle (DET-01)
det1=DET['bulgular'][0]
for p,qs in ((38,['30','31']),(39,['32','33','34','35']),(40,['36','37','38'])):
    for qn in qs:
        if not any(x['sayfa']==p and x['soru']==qn and 'l' in x['tur'].lower() for x in red):
            red.append(dict(sayfa=p,test='T4',ders='Fen Bil.',soru=qn,
                mevcut='Öncül ve seçeneklerde "l. / ll. / lll." (küçük L harfi)',
                tur='Roma rakamı yerine küçük "l" harfi (U+006C) kullanılmış',
                onerilen='Öncül ve seçenekler büyük Roma rakamıyla dizilmeli: I. / II. / III. / IV.',
                aciklama='Unicode kod noktası incelemesiyle doğrulandı: kitapçığın diğer 32 sorusunda U+0049 (büyük I) kullanılırken bu sorularda U+006C (küçük l) kullanılmıştır.',
                onem='ORTA',kategori='BICIM',tdk=False))
red.sort(key=lambda x:(ONEM.get(x['onem'],9),x['sayfa'],int(x['soru']) if str(x['soru']).isdigit() else 0))
tdk_items=[r for r in red if r['tdk']]; red_dil=[r for r in red if not r['tdk']]

# ---------- ana tablo
DURUM={'UYUMLU':'✅ UYUMLU','ILK_COZUM_HATASI':'✅ UYUMLU','CEVAP_ANAHTARI_HATASI':'🔴 CEVAP ANAHTARI HATASI',
       'SORU_HATALI':'🔴 SORU HATASI','TARTISMALI':'🟠 TARTIŞMALI','KESINLESTIRILMESI_GEREKIYOR':'⚪ İNCELEME GEREKİYOR'}
redbyq=collections.defaultdict(list)
for r in red:
    if str(r['soru']).isdigit() and r['test']: redbyq[f"{r['test']}-{int(r['soru'])}"].append(r)

ana={}; uyusmazlik=[]; akademik=[]
for qid in ORDER:
    t,n=qid.split('-'); n=int(n); k=KEY[qid]
    rl=redbyq.get(qid,[]); eo=min([ONEM.get(x['onem'],9) for x in rl],default=9)
    redtxt=('🟡 %d madde · %s'%(len(rl),['KRİTİK','YÜKSEK','ORTA','DÜŞÜK'][eo])) if rl else '🟢 Temiz'
    if qid in KAR:
        v=KAR[qid]; durum=DURUM.get(v['karar'],'⚪ İNCELEME GEREKİYOR'); bag=v['nihai_cevap']
        akad={'UYUMLU':'🟢 Sorun yok','ILK_COZUM_HATASI':'🟢 Sorun yok','CEVAP_ANAHTARI_HATASI':'🔴 Anahtar hatalı',
              'SORU_HATALI':'🔴 Soru hatalı','TARTISMALI':'🟠 Tartışmalı'}.get(v['karar'],'⚪ Kesinleştirilmeli')
        acik=esc(v['gerekce'])[:300]
        if v['karar'] not in ('UYUMLU','ILK_COZUM_HATASI') or bag!=k:
            uyusmazlik.append(dict(ders=f'{TN[t]}<br><span class="kucuk">{sub(t,n)}</span>',soru=str(n),
                bagimsiz=f"A: {A[qid]['cevap']}<br>B: {B[qid]['cevap']}",anahtar=k,
                ikinci=esc(v['ikinci_kontrol_ozeti'])[:420],karar=DURUM.get(v['karar'],v['karar']),
                gerekce=esc(v['gerekce'])[:700]))
        if v['karar'] in ('CEVAP_ANAHTARI_HATASI','SORU_HATALI','TARTISMALI','KESINLESTIRILMESI_GEREKIYOR'):
            akademik.append(dict(onem=TRLBL.get(v['onem'],'ORTA') if v['onem']!='YOK' else 'ORTA',
                ders=f'{TN[t]} / {sub(t,n)}',sayfa=Q[qid]['page'],soru=str(n),
                problem=('Cevap anahtarı yanlış: anahtar <b>%s</b>, akademik olarak doğru seçenek <b>%s</b>'%(k,bag))
                         if v['karar']=='CEVAP_ANAHTARI_HATASI' else esc(v['soru_kusuru'])[:300],
                neden=esc(v['gerekce'])[:700],duzeltme=esc(v['onerilen_duzeltme'])[:400]))
    else:
        durum='✅ UYUMLU'; bag=A[qid]['cevap']; akad='🟢 Sorun yok'
        acik='İki bağımsız geçiş aynı cevapta birleşti; anahtarla örtüşüyor.'
    if rl and durum.startswith('✅'): durum='✅ UYUMLU + 🟡 REDAKSİYON'
    ana[qid]=dict(bagimsiz=bag,anahtar=k,durum=durum,akademik=akad,redaksiyon=redtxt,aciklama=acik)

akademik.sort(key=lambda x:(ONEM.get(x['onem'],9),x['sayfa']))
st=dict(toplam=len(ORDER),uyumlu=sum(1 for v in ana.values() if v['durum'].startswith('✅')),
    anahtar_hatasi=sum(1 for v in ana.values() if 'CEVAP ANAHTARI HATASI' in v['durum']),
    soru_hatasi=sum(1 for v in ana.values() if 'SORU HATASI' in v['durum']),
    tartismali=sum(1 for v in ana.values() if 'TARTIŞMALI' in v['durum']),
    inceleme=sum(1 for v in ana.values() if 'İNCELEME' in v['durum']),
    red_toplam=len(red),red_dil=len(red_dil),tdk=len(tdk_items),
    red_ham=len(RED),red_elenen=elenen,ovr_elenen=override_elenen,ovr_onem=override_onem,
    red_kritik=sum(1 for r in red if r['onem']=='KRİTİK'),red_yuksek=sum(1 for r in red if r['onem']=='YÜKSEK'),
    red_orta=sum(1 for r in red if r['onem']=='ORTA'),red_dusuk=sum(1 for r in red if r['onem']=='DÜŞÜK'),
    etkilenen_soru=len(redbyq))
json.dump(dict(ana=ana,uyusmazlik=uyusmazlik,akademik=akademik,red=red,red_dil=red_dil,
               tdk_items=tdk_items,stats=st),open(f'{BASE}/tables.json','w'),ensure_ascii=False,indent=1)
print(json.dumps(st,ensure_ascii=False,indent=1))
print('\n== AKADEMİK HATA TABLOSU ==')
for x in akademik: print(' ',x['onem'],x['ders'],'s.'+str(x['sayfa']),'soru',x['soru'],'|',x['problem'][:90])
print('\n== REDAKSİYON ÖNEM DAĞILIMI ==',collections.Counter(r['onem'] for r in red))
print('== KATEGORİ ==',collections.Counter(r['kategori'] for r in red))
