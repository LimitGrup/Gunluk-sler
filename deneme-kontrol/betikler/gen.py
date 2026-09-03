# -*- coding: utf-8 -*-
"""Baskı öncesi kontrol raporu üreteci (HTML -> PDF, WeasyPrint)."""
import json, html, os, sys, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
Q   = json.load(open(f'{BASE}/questions.json'))
KEY = json.load(open(f'{BASE}/answerkey.json'))
R   = json.load(open(f'{BASE}/tables.json'))
R['meta'] = json.load(open(f'{BASE}/meta.json'))
R['redaksiyon'] = [dict(onem=r['onem'],ders=r['ders'],sayfa=r['sayfa'],soru=r['soru'],mevcut=r['mevcut'],tur=r['tur'],onerilen=r['onerilen'],aciklama=r['aciklama']) for r in R['red_dil']]
R['tdk'] = [dict(ders=r['ders'],sayfa=r['sayfa'],soru=r['soru'],ifade=r['tur'][:70],mevcut=r['mevcut'],sonuc='<span class="d d-kirmizi">TDK ERİŞİMİ YOK</span><br><span class="kucuk">sozluk.gov.tr adresine erişim ağ çıkış politikası tarafından engellendi (HTTP 403); çevrim içi doğrulama yapılamadı.</span>',onerilen=r['onerilen'],durum='<span class="d d-gri">KONTROL BEKLİYOR</span>') for r in R['tdk_items']]

TN = {'T1':'Türk Dili ve Edebiyatı-Sosyal Bilimler-1',
      'T2':'Sosyal Bilimler-2', 'T3':'Matematik', 'T4':'Fen Bilimleri'}
TSHORT = {'T1':'TDE-Sos-1','T2':'Sos-2','T3':'Matematik','T4':'Fen Bil.'}
SUB = {'T1':[(1,24,'Türk Dili ve Edebiyatı'),(25,34,'Tarih-1'),(35,40,'Coğrafya-1')],
       'T2':[(1,11,'Tarih-2'),(12,22,'Coğrafya-2'),(23,34,'Felsefe Grubu'),
             (35,40,'Din Kültürü ve Ahlak Bilgisi'),(41,46,'DKAB Almayanlar (Ek Sorular)')],
       'T3':[(1,40,'Matematik')],
       'T4':[(1,14,'Fizik'),(15,27,'Kimya'),(28,40,'Biyoloji')]}
COUNTS = {'T1':40,'T2':46,'T3':40,'T4':40}
ORDER = [f'{t}-{i}' for t in ['T1','T2','T3','T4'] for i in range(1, COUNTS[t]+1)]

def sub(t, n):
    for a,b,s in SUB[t]:
        if a <= n <= b: return s
    return ''
def e(x): return html.escape(str(x if x is not None else ''))
def rozet(onem):
    m = {'KRİTİK':'r-kritik','KRITIK':'r-kritik','YÜKSEK':'r-yuksek','YUKSEK':'r-yuksek',
         'ORTA':'r-orta','DÜŞÜK':'r-dusuk','DUSUK':'r-dusuk'}
    lbl = {'KRITIK':'KRİTİK','YUKSEK':'YÜKSEK','DUSUK':'DÜŞÜK'}.get(onem, onem)
    return f'<span class="rozet {m.get(onem,"r-dusuk")}">{e(lbl)}</span>'

def tablo(headers, rows, cls='', widths=None):
    cg = ''
    if widths:
        cg = '<colgroup>' + ''.join(f'<col style="width:{w}">' for w in widths) + '</colgroup>'
    h = ''.join(f'<th>{x}</th>' for x in headers)
    b = ''
    for r in rows:
        b += '<tr>' + ''.join(f'<td{(" class="+chr(34)+c+chr(34)) if c else ""}>{v}</td>'
                              for v, c in r) + '</tr>'
    return f'<table class="{cls}">{cg}<thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'

OUT = []
W = OUT.append
M = R['meta']

# ---------------------------------------------------------------- 1. KAPAK
W(f'''<div class="kapak">
<div class="kicker">Baskı Öncesi Kalite Kontrol</div>
<h1>FINALE DOĞRU KURS<br>AYT DENEME 1A</h1>
<div class="sub">Baskı Öncesi Akademik Çözüm ve Redaksiyon Kontrol Raporu</div>
<div class="meta">
<b>Kaynak dosya</b> FINALE DOGRU KURS AYT DENEME 1A.pdf<br>
<b>Kitapçık türü</b> A · Kitapçık kodu 262711221<br>
<b>Sayfa sayısı</b> 40 sayfa<br>
<b>Toplam soru</b> {M['toplam']} soru (4 test)<br>
<b>Kontrol tarihi</b> {M['tarih']}<br>
<b>Kontrol yöntemi</b> Cevap anahtarından bağımsız çift geçişli çözüm<br>
<b>Rapor sürümü</b> {M['surum']}
</div></div>''')

# ---------------------------------------------------------------- 2. ÖZET
W('<h2>1. Yönetici Özeti</h2>')
W(f'<p>{M["ozet_giris"]}</p>')
rows = [(k, str(v)) for k, v in M['ozet_tablo']]
W(tablo(['Kontrol Alanı','Sonuç'],
        [[(a,''),(b,'n')] for a,b in rows], cls='istatistik', widths=['72%','28%']))
for blok in M.get('ozet_notlar', []):
    W(f'<div class="{blok[0]}">{blok[1]}</div>')

# ---------------------------------------------------------------- 3. BASKI KARARI
W('<h2>2. Baskı Kararı</h2>')
W(f'''<div class="karar {M['karar_sinif']}">
<div class="baslik">{M['karar_baslik']}</div>{M['karar_metin']}</div>''')
W('<h3>Kararın gerekçesi</h3><ol>')
for g in M['karar_gerekce']: W(f'<li>{g}</li>')
W('</ol>')

# ---------------------------------------------------------------- 4. ENVANTER
W('<div class="section"><h2>3. Sınav / Soru Envanteri</h2>')
W(f'<p>{M["envanter_giris"]}</p>')
rows = []
for t in ['T1','T2','T3','T4']:
    for a, b, s in SUB[t]:
        sayfalar = sorted({Q[f'{t}-{i}']['page'] for i in range(a, b+1)})
        rows.append([(e(TN[t]),''),(e(s),''),(f'{a}',"c"),(f'{b}',"c"),
                     (f'{b-a+1}',"c"), (f'{sayfalar[0]}–{sayfalar[-1]}','c')])
rows.append([('<b>TOPLAM</b>',''),('<b>4 test · 12 alan</b>',''),('','c'),('','c'),
             (f'<b>{M["toplam"]}</b>','c'),('<b>2–40</b>','c')])
W(tablo(['Test','Alan','İlk Soru','Son Soru','Soru Sayısı','Kitapçık Sayfası'], rows,
        widths=['26%','26%','11%','11%','13%','13%']))
W(M['envanter_not'])
W('</div>')

# ---------------------------------------------------------------- 5. ANA TABLO
W('<div class="section landscape"><h2>4. Tüm Sorular Kontrol Tablosu</h2>')
W(f'<p>{M["ana_tablo_giris"]}</p>')
rows = []
for qid in ORDER:
    t, n = qid.split('-'); n = int(n)
    d = R['ana'][qid]
    rows.append([
        (e(TSHORT[t]),''), (e(sub(t,n)),''), (str(Q[qid]['page']),'c'), (str(n),'c'),
        (f'<b>{e(d["bagimsiz"])}</b>','c'), (e(d['anahtar']),'c'),
        (d['durum'],''), (d['akademik'],''), (d['redaksiyon'],''), (d['aciklama'],'')])
W(tablo(['Test','Alan','Sayfa','Soru','Bağımsız<br>Cevap','Anahtar','Durum',
         'Akademik Sonuç','Redaksiyon','Kısa Açıklama'], rows,
        widths=['7%','11%','4%','4%','5%','5%','13%','10%','10%','31%']))
W('</div>')

# ---------------------------------------------------------------- 6. UYUŞMAZLIK
W('<div class="section landscape"><h2>5. Cevap Anahtarı Uyuşmazlıkları</h2>')
W(f'<p>{M["uyusmazlik_giris"]}</p>')
if R['uyusmazlik']:
    rows = [[(x['ders'],''),(e(x['soru']),'c'),(x['bagimsiz'],'c'),(e(x['anahtar']),'c'),
             (x['ikinci'],''),(x['karar'],''),(x['gerekce'],'')] for x in R['uyusmazlik']]
    W(tablo(['Ders / Alan','Soru','Bağımsız Çözüm','Anahtar','İkinci Kontrol Sonucu',
             'Nihai Karar','Gerekçe'], rows, widths=['13%','5%','7%','5%','18%','14%','38%']))
else:
    W('<div class="bilgi"><b>Uyuşmazlık bulunmamıştır.</b> 166 sorunun tamamında bağımsız '
      'çözüm ile kitapçığa gömülü cevap anahtarı örtüşmektedir.</div>')
W('</div>')

# ---------------------------------------------------------------- 7. AKADEMİK HATALAR
W('<div class="section landscape"><h2>6. Akademik ve Teknik Soru Hataları</h2>')
W(f'<p>{M["akademik_giris"]}</p>')
if R['akademik']:
    rows = [[(rozet(x['onem']),'c'),(e(x['ders']),''),(str(x['sayfa']),'c'),(e(x['soru']),'c'),
             (x['problem'],''),(x['neden'],''),(x['duzeltme'],'')] for x in R['akademik']]
    W(tablo(['Önem','Ders / Alan','Sayfa','Soru','Problem','Neden Hatalı?','Önerilen Düzeltme'],
            rows, widths=['7%','12%','5%','5%','24%','26%','21%']))
else:
    W('<div class="bilgi"><b>Akademik/teknik soru hatası tespit edilmemiştir.</b></div>')
W('</div>')

# ---------------------------------------------------------------- 8. REDAKSİYON
W('<div class="section landscape"><h2>7. Redaksiyon Hataları</h2>')
W(f'<p>{M["redaksiyon_giris"]}</p>')
if R['redaksiyon']:
    rows = [[(rozet(x['onem']),'c'),(e(x['ders']),''),(str(x['sayfa']),'c'),(e(x['soru']),'c'),
             (f'<span class="alinti">{e(x["mevcut"])}</span>',''),(e(x['tur']),''),
             (e(x['onerilen']),''),(x['aciklama'],'')] for x in R['redaksiyon']]
    W(tablo(['Önem','Ders','Sayfa','Soru','Mevcut İfade','Hata Türü',
             'Önerilen Düzeltme','Açıklama'], rows,
            widths=['6%','9%','4%','4%','23%','11%','20%','23%']))
else:
    W('<div class="bilgi"><b>Redaksiyon hatası tespit edilmemiştir.</b></div>')
W('</div>')

# ---------------------------------------------------------------- 9. TDK
W('<div class="section landscape"><h2>8. TDK Yazım Doğrulama Tablosu</h2>')
W(M['tdk_giris'])
if R['tdk']:
    rows = [[(e(x['ders']),''),(str(x['sayfa']),'c'),(e(x['soru']),'c'),(e(x['ifade']),''),
             (e(x['mevcut']),''),(x['sonuc'],''),(e(x['onerilen']),''),(x['durum'],'')]
            for x in R['tdk']]
    W(tablo(['Ders','Sayfa','Soru','Kelime / İfade','Mevcut Yazım',
             'TDK Kontrol Sonucu','Önerilen Yazım','Durum'], rows,
            widths=['10%','4%','4%','15%','15%','24%','14%','14%']))
else:
    W('<div class="bilgi">TDK doğrulaması gerektiren yazım maddesi tespit edilmemiştir.</div>')
W('</div>')

# ---------------------------------------------------------------- 10. EDİTÖR
W('<div class="section"><h2>9. Editör Tarafından Kontrol Edilmesi Gereken Maddeler</h2>')
W(f'<p>{M["editor_giris"]}</p>')
if R['editor']:
    rows = [[(str(i+1),'c'),(e(x['konu']),''),(e(x['yer']),''),(x['aciklama'],''),(x['islem'],'')]
            for i, x in enumerate(R['editor'])]
    W(tablo(['#','Konu','Yer (Sayfa / Soru)','Açıklama','Beklenen İşlem'], rows,
            widths=['4%','17%','13%','40%','26%']))
W('</div>')

# ---------------------------------------------------------------- 11. SON KONTROL
W('<div class="section"><h2>10. Son Kontrol ve İstatistik</h2>')
W('<h3>10.1 Kontrol listesi</h3>')
rows = [[(a,''),(b,'c')] for a, b in M['son_kontrol']]
W(tablo(['Kontrol Maddesi','Durum'], rows, widths=['82%','18%']))
W('<h3>10.2 Sayısal denklik kontrolü</h3>')
rows = [[(e(a),''),(f'<b>{b}</b>','c')] for a, b in M['denklik']]
W(tablo(['Ölçüt','Değer'], rows, widths=['72%','28%']))
W(M['denklik_not'])
W('<h3>10.3 Cevap anahtarı dağılımı</h3>')
import collections
rows = []
for t in ['T1','T2','T3','T4']:
    c = collections.Counter(KEY[f'{t}-{i}'] for i in range(1, COUNTS[t]+1))
    rows.append([(e(TN[t]),'')] + [(str(c.get(x,0)),'c') for x in 'ABCDE'] +
                [(str(sum(c.values())),'c')])
c = collections.Counter(KEY.values())
rows.append([('<b>GENEL</b>','')] + [(f'<b>{c.get(x,0)}</b>','c') for x in 'ABCDE'] +
            [(f'<b>{sum(c.values())}</b>','c')])
W(tablo(['Test','A','B','C','D','E','Toplam'], rows,
        widths=['40%','10%','10%','10%','10%','10%','10%']))
W(M['dagilim_not'])
W('<h3>10.4 Yöntem ve kapsam beyanı</h3>')
W(M['yontem'])
W('</div>')

htmlout = f'''<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8">
<title>Baskı Öncesi Kontrol Raporu</title>
<link rel="stylesheet" href="report/style.css"></head><body>{''.join(OUT)}</body></html>'''
open(f'{BASE}/report.html','w').write(htmlout)

import weasyprint
weasyprint.HTML(f'{BASE}/report.html', base_url=BASE).write_pdf(
    f'{BASE}/DENEME_SINAVI_BASKI_ONCESI_KONTROL_RAPORU.pdf')
print('PDF üretildi')
