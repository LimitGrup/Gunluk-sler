# -*- coding: utf-8 -*-
"""
A–B KONTROL'ün açık cevap taraması gerçek bir dizgide doğru mu: cevaplı A/B
kitapçıklarından baskı kopyası üretilir (renkli cevap harfleri ve soru kodları
silinir), sonra iki durum denetlenir:

  temiz    A baskı ↔ B baskı: açık cevap bildirilmemeli (yanlış alarm yok).
  karışık  B'de bir sorunun cevabı SİYAH metin olarak, başka bir sorununki
           EĞRİ olarak (metin katmanında yok, cevap renginde çizim) bırakılır:
           tam o iki soru HATA olmalı, başka açık cevap bildirilmemeli.

Kopyalar <çıktı_klasörü> içine yazılır; kaynak PDF'lere dokunulmaz. Kitapçıkların
kendi içerik farkları (gerçek metin farkı vb.) iki durumda da aynı çıkar ve
sonuçta ayrıca gösterilir.

Kullanım:  python3 baski_kopya_sina.py <app.py> <A.pdf> <B.pdf> <OTOMATİK|TYT|AYT|...> <çıktı_klasörü>
"""
import importlib.util
import re
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

    # B'deki gerçek cevap işaretleri (motorun oluk adayları)
    _A, B = m._kitapciklari_hazirla(a_pdf, b_pdf, yapi, None, None)
    cevaplar = []
    for o in B["ogeler"]:
        if o["no"]:
            ad_ = [a for a in m._cevap_adaylari(o, B.get("genislikler"))
                   if a["renkli"] and a["oluk"]]
            if len(ad_) == 1:
                cevaplar.append((o, ad_[0]))
    if len(cevaplar) < 3:
        print("Bu çift cevaplı görünmüyor (cevap işareti bulunamadı).")
        return 1
    siyah, egri = cevaplar[len(cevaplar) // 3], cevaplar[2 * len(cevaplar) // 3]

    def baski(src, dst, siyah=None, egri=None):
        doc = fitz.open(src)
        for page in doc:
            for b in page.get_text("dict")["blocks"]:
                for l in b.get("lines", []):
                    for sp in l["spans"]:
                        t = sp["text"].strip()
                        if m.renkli_mi(sp["color"]) and (
                                re.fullmatch(r"[A-E]", t) or
                                (re.fullmatch(r"[A-Z0-9]{4,20}", t) and re.search(r"\d", t))):
                            r = fitz.Rect(sp["bbox"])
                            h = r.height       # yalnız glifin ortası: komşu satıra dokunmaz
                            page.add_redact_annot(fitz.Rect(r.x0 + 0.5, r.y0 + 0.35 * h,
                                                            r.x1 - 0.5, r.y1 - 0.35 * h))
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                                  graphics=fitz.PDF_REDACT_LINE_ART_NONE)
        if siyah:
            _o, a = siyah
            x0, y0, _x1, y1 = a["kutu"]
            doc[a["satir"]["sayfa"]].insert_text((x0, y0 + 0.72 * (y1 - y0)), a["harf"],
                                                 fontsize=9, fontname="hebo", color=(0, 0, 0))
        if egri:                               # "C" biçiminde, metin olmayan çizim
            _o, a = egri
            x0, y0, _x1, y1 = a["kutu"]
            cy = (y0 + y1) / 2
            sh = doc[a["satir"]["sayfa"]].new_shape()
            sh.draw_bezier((x0 + 5.5, cy - 3.2), (x0 + 3, cy - 6), (x0 + 0.3, cy - 4.2), (x0 + 0.3, cy))
            sh.draw_bezier((x0 + 0.3, cy), (x0 + 0.3, cy + 4.2), (x0 + 3, cy + 6), (x0 + 5.5, cy + 3.2))
            sh.finish(color=(0.93, 0, 0.55), width=1.3)
            sh.commit()
        doc.save(dst)

    qa, qb, qk = str(out / "A_baski.pdf"), str(out / "B_baski.pdf"), str(out / "B_karisik.pdf")
    baski(a_pdf, qa)
    baski(b_pdf, qb)
    baski(b_pdf, qk, siyah=siyah, egri=egri)

    def kontrol(b):
        ya = m.yapi_cikar(qa) if sinav == "OTOMATİK" else yapi
        yb = m.yapi_cikar(b) if sinav == "OTOMATİK" else None
        return m.kontrol_et(qa, b, ya, lambda _x: None, yapi_b=yb)[1]

    def cevap_sorunu(s):
        return "Açık kalan" in s["aciklama"] or "Cevap yerinde" in s["aciklama"]

    def yaz(sorunlar):
        for s in sorunlar:
            print(f"    {s['onem']} {s['kitapcik']} {s['test']} {s['soru']} {s['aciklama'][:140]}")

    temiz = kontrol(qb)
    kar = kontrol(qk)
    print(f"temiz: {len(temiz)} sorun, açık cevap {sum(map(cevap_sorunu, temiz))}")
    yaz(temiz)
    print(f"karışık: siyah {siyah[0]['ders']} {siyah[0]['etiket_no']} '{siyah[1]['harf']}', "
          f"eğri {egri[0]['ders']} {egri[0]['etiket_no']}")
    yaz(kar)
    beklenen = {str(siyah[0]["etiket_no"]), str(egri[0]["etiket_no"])}
    kar_cevap = [s for s in kar if cevap_sorunu(s)]
    diger = lambda ss: sorted((s["onem"], s["aciklama"]) for s in ss if not cevap_sorunu(s))
    tamam = (not any(map(cevap_sorunu, temiz))
             and len(kar_cevap) == 2 and all(s["onem"] == "HATA" for s in kar_cevap)
             and {str(s["soru"]) for s in kar_cevap} == beklenen
             and diger(kar) == diger(temiz))
    print("SONUÇ:", "tamam" if tamam else "SORUN")
    return 0 if tamam else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:6]))
