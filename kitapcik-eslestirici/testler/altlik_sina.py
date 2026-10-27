# -*- coding: utf-8 -*-
"""
Soru numarası hizasındaki numaralı yazılar soru başı sanılmamalı:

  altlık  her sayfanın sol altına, soru numaralarıyla aynı hizada "6. SINIF"
          (5. ve 6. sınıf kitapçıklarındaki sınıf etiketi gibi)
  liste   altı boş olan bir sorunun altına, soru numarası hizasında art arda
          "1. Taksit:" … "5. Taksit:" satırları (sütun kenarına hizalı tablo
          gibi); B'de aynı sorunun altına (her sayfada en çok bir liste)

A ve B'ye aynı yazılar basılır. KONTROL'de basılmamış kopyaya göre yeni sorun
çıkmamalı; EŞLEŞTİR'in A→B numaraları değişmemeli.

Kullanım:  python3 altlik_sina.py <app.py> <A.pdf> <B.pdf> <OTOMATİK|TYT|AYT|...> <çıktı_klasörü>
"""
import importlib.util
import sys
from pathlib import Path


def yukle(ad, yol):
    spec = importlib.util.spec_from_file_location(ad, yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main(app, a_pdf, b_pdf, sinav, cikti):
    m = yukle("kitapcik_app", app)
    m.bagimliliklari_yukle()
    fitz = m.fitz
    out = Path(cikti)
    out.mkdir(parents=True, exist_ok=True)
    yapi = m.yapi_cikar(a_pdf) if sinav == "OTOMATİK" else m.YAPILAR[sinav]
    A, B = m._kitapciklari_hazirla(a_pdf, b_pdf, yapi, None, None)

    def sol_hiza(k):                      # {sayfa: soru numaralarının sol sütun x'i}
        sonuc = {}
        for o in k["ogeler"]:
            if o["no"] and o["ham_satirlar"]:
                bas = o["ham_satirlar"][0]
                p = bas["sayfa"]
                if bas["x0"] < k["genislikler"][p] / 2:
                    sonuc[p] = min(sonuc.get(p, bas["x0"]), bas["x0"])
        return sonuc

    def alt_uclar(k):                     # {(ders, no): (sayfa, numara x, ilk sayfadaki alt y)}
        sonuc = {}
        for o in k["ogeler"]:
            if not o["no"] or not o["ham_satirlar"]:
                continue
            bas = o["ham_satirlar"][0]
            p, W = bas["sayfa"], k["genislikler"][bas["sayfa"]]
            sag = bas["x0"] >= W / 2
            alt = max(r["y1"] for r in o["ham_satirlar"]
                      if r["sayfa"] == p and (r["x0"] >= W / 2 - 4) == sag)
            sonuc[(o["ders"], o["no"])] = (p, bas["x0"], alt)
        return sonuc

    def bos_mu(doc, p, x, alt):           # liste basılacak yer boş mu (yazı/şekil yok)
        sayfa = doc[p]
        bolge = fitz.Rect(x - 2, alt + 4, x + 70, alt + 78)
        if bolge.y1 > sayfa.rect.height - 110:     # altlık bölgesine girmesin
            return False
        if any(fitz.Rect(w[:4]).intersects(bolge) for w in sayfa.get_text("words")):
            return False
        if any(fitz.Rect(d["rect"]).intersects(bolge) for d in sayfa.get_drawings()):
            return False
        return not any(fitz.Rect(i["bbox"]).intersects(bolge) for i in sayfa.get_image_info())

    def liste_yerleri(tab):
        # Liste bir sorunun altındaki boşluğa, B'de AYNI sorunun altına basılır
        # (iki kitapçıkta da altı boşsa): sorunun metni iki kitapçıkta aynı
        # kalır, yalnız numara bulma sınanır. Her sayfaya en çok bir liste.
        ua, ub = alt_uclar(A), alt_uclar(B)
        da, db = fitz.open(a_pdf), fitz.open(b_pdf)
        yer_a, yer_b = {}, {}
        for d, an, bn in tab:
            if (d, an) not in ua or (d, bn) not in ub:
                continue
            pa, xa, alta = ua[(d, an)]
            pb, xb, altb = ub[(d, bn)]
            if pa in yer_a or pb in yer_b:
                continue
            if bos_mu(da, pa, xa, alta) and bos_mu(db, pb, xb, altb):
                yer_a[pa], yer_b[pb] = (xa, alta), (xb, altb)
        return yer_a, yer_b

    def bas(src, dst, k, tur, yerler=None):
        doc = fitz.open(src)
        if tur == "altlık":
            for p, sol in sol_hiza(k).items():
                sayfa = doc[p]
                sayfa.insert_text((sol, sayfa.rect.height - 52), "6. SINIF", fontsize=8,
                                  fontname="hebo", color=(0, 0, 0))
        for p, (x, alt) in (yerler or {}).items():
            for j in range(5):
                doc[p].insert_text((x, alt + 18 + j * 11), f"{j + 1}. Taksit:",
                                   fontsize=8, fontname="helv", color=(0, 0, 0))
        doc.save(dst)

    def kontrol(qa, qb):
        ya = m.yapi_cikar(qa) if sinav == "OTOMATİK" else yapi
        yb = m.yapi_cikar(qb) if sinav == "OTOMATİK" else None
        return m.kontrol_et(qa, qb, ya, lambda _x: None, yapi_b=yb)[1]

    def tablo(qa, qb, ad):
        import openpyxl
        yol = out / f"_{ad}.xlsx"
        m.calistir(qa, qb, sinav, None, None, None, str(yol), lambda _x: None)
        ws = openpyxl.load_workbook(yol)[sinav]
        return [(r[0], r[2], r[4]) for r in ws.iter_rows(min_row=2, values_only=True)
                if r[2] is not None]

    temiz = kontrol(a_pdf, b_pdf)
    tset = {(s["onem"], s["aciklama"]) for s in temiz}
    temiz_tablo = tablo(a_pdf, b_pdf, "temiz")
    print(f"basılmamış: {len(temiz)} sorun, EŞLEŞTİR {len(temiz_tablo)} satır")
    hepsi = True
    for tur in ("altlık", "liste"):
        qa, qb = str(out / f"A_{tur}.pdf"), str(out / f"B_{tur}.pdf")
        if tur == "liste":
            yer_a, yer_b = liste_yerleri(temiz_tablo)
            bas(a_pdf, qa, A, tur, yer_a)
            bas(b_pdf, qb, B, tur, yer_b)
            print(f"   liste {len(yer_a)} sayfada (A) / {len(yer_b)} sayfada (B)")
        else:
            bas(a_pdf, qa, A, tur)
            bas(b_pdf, qb, B, tur)
        yeni = [s for s in kontrol(qa, qb) if (s["onem"], s["aciklama"]) not in tset]
        tab = tablo(qa, qb, tur)
        fark = [(x, y) for x, y in zip(temiz_tablo, tab) if x != y]
        tamam = not yeni and not fark and len(tab) == len(temiz_tablo)
        hepsi &= tamam
        print(f"{'✓' if tamam else '✗'} {tur}: KONTROL {len(yeni)} yeni sorun, "
              f"EŞLEŞTİR {len(fark)} satır farklı")
        for s in yeni[:15]:
            print(f"     {s['onem']} [{s['kitapcik']}] {s['test']} | {s['soru']} | "
                  f"{s['aciklama'][:120]}")
        for x, y in fark[:10]:
            print(f"     EŞLEŞTİR {x} → {y}")
    print("SONUÇ:", "tamam" if hepsi else "SORUN")
    return 0 if hepsi else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:6]))
