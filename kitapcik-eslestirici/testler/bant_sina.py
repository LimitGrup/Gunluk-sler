# -*- coding: utf-8 -*-
"""
Kitapçık türü (A/B) denetimi: soru sayfalarının üst bandında kitapçığın harfi
("A A A A A" / "B B B B B") ve kapakta "A KİTAPÇIĞI". Bantlı bir A/B çiftinin
kopyaları bilerek bozulur:

  temiz                   bant sorunu çıkmamalı
  B'de bir sayfada yok    B'nin bir sayfasında bant silinir
  B'de yanlış harf        B'nin bir sayfasının bandında "A" yazar
  B'de hiç bant yok       B'nin bütün bantları silinir
  yer değiştirmiş         A ve B dosyaları ters verilir
  B yerine A seçilmiş     A dosyası B olarak da verilir
  hiç bant yok            iki kitapçıkta da bant silinir: tek satır
  B kapağında A           B'nin başına "A KİTAPÇIĞI" kapağı eklenir
  B kapağında B           doğru kapak: sorun çıkmamalı
  KDS bir sayfada yok     tek kitapçık (KDS) kontrolünde bir sayfada bant yok

Bozmalarda bant dışında yeni sorun çıkmamalı.

Kullanım:  python3 bant_sina.py <app.py> <A.pdf> <B.pdf> <OTOMATİK|TYT|AYT|...> <çıktı_klasörü>
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

    def kontrol(qa, qb, tek=False):
        if tek:
            return m.kontrol_et(qa, qa, m.kds_yapi_cikar(qa), lambda _x: None, tek=True)
        ya = m.YAPILAR[sinav] if sinav in m.YAPILAR else m.yapi_cikar(qa)
        yb = None if sinav in m.YAPILAR else m.yapi_cikar(qb)
        return m.kontrol_et(qa, qb, ya, lambda _x: None, yapi_b=yb)

    def bant_harfleri(page):              # üst bant satırının harf kutuları
        H = page.rect.height
        harfler = []
        for blk in page.get_text("rawdict", clip=fitz.Rect(0, 0, page.rect.width,
                                                            H * m.BANT_ORANI))["blocks"]:
            for l in blk.get("lines", []):
                for sp in l["spans"]:
                    if sp["size"] >= m.BANT_EN_KUCUK_PUNTO:
                        for c in sp["chars"]:
                            if c["c"].isalpha():
                                harfler.append((c["origin"][1], c["c"], fitz.Rect(c["bbox"]),
                                                c["origin"], sp["size"]))
        harfler.sort(key=lambda t: t[0])
        satirlar, onceki = [], None       # taban çizgisine göre satırlar
        for t in harfler:
            if onceki is None or t[0] - onceki > 2:
                satirlar.append([])
            satirlar[-1].append(t)
            onceki = t[0]
        # yalnız bant satırı: bütün harfleri aynı A/B harfi (başlık satırı değil)
        return [(r, org, boy) for s in satirlar
                if len({t[1] for t in s}) == 1 and s[0][1] in ("A", "B")
                for _y, _h, r, org, boy in s]

    def bozuk(pdf, ad, sayfalar=None, harf=None, kapak=None):
        """sayfalar: bandı silinecek ya da değiştirilecek sayfalar (None: hepsi);
        harf: yerine yazılacak harf (None: silinir); kapak: başa eklenecek kapak harfi."""
        doc = fitz.open(pdf)
        for p in (range(len(doc)) if sayfalar is None else sayfalar):
            page = doc[p]
            kutular = bant_harfleri(page)
            for r, _o, _s in kutular:
                page.add_redact_annot(r)
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                                  graphics=fitz.PDF_REDACT_LINE_ART_NONE)
            if harf:
                for _r, org, boy in kutular:
                    page.insert_text(org, harf, fontsize=boy, fontname="hebo",
                                     color=(0, 0, 0))
        if kapak:
            page = doc.new_page(0, width=doc[0].rect.width, height=doc[0].rect.height)
            page.insert_text((80, 300), kapak, fontsize=68, fontname="hebo")
            page.insert_text((150, 300), "KİTAPÇIĞI".replace("İ", "I").replace("Ç", "C")
                             .replace("Ğ", "G"), fontsize=20, fontname="hebo")
        yol = str(out / ad)
        doc.save(yol)
        return yol

    def bant_mi(s):
        return s["soru"] in ("üst bant", "kapak")

    sonuc, temiz = kontrol(a_pdf, b_pdf)
    tset = {(s["onem"], s["aciklama"]) for s in temiz}
    ozet = sonuc["bant"]
    print("temiz:", len(temiz), "sorun | bant:", ozet, "|",
          [l for l in m.kontrol_ozeti(sonuc, temiz) if "Üst bant" in l])
    hepsi = not any(bant_mi(s) for s in temiz) and all(v[0] == v[1] and v[1] > 0
                                                       for v in ozet.values())
    if not hepsi:
        print("✗ temiz çiftte bant bulunamadı ya da bant sorunu var")
    _s, temiz_tek = kontrol(a_pdf, None, tek=True)
    tset_tek = {(s["onem"], s["aciklama"]) for s in temiz_tek}

    sb = sorted({r["sayfa"] for o in sonuc["B"]["ogeler"] for r in o["ham_satirlar"]})
    sa = sorted({r["sayfa"] for o in sonuc["A"]["ogeler"] for r in o["ham_satirlar"]})
    p1, p2 = sb[len(sb) // 3], sb[2 * len(sb) // 3]

    senaryolar = [
        ("B'de bir sayfada yok", lambda: (a_pdf, bozuk(b_pdf, "B_eksik.pdf", [p1])), False,
         [f"Üst bantta kitapçık türü yok: sayfa {p1 + 1} (diğer sayfalarda 'B' var)"]),
        ("B'de yanlış harf", lambda: (a_pdf, bozuk(b_pdf, "B_yanlis.pdf", [p2], "A")), False,
         [f"B olarak seçilen kitapçığın üst bandında 'A' yazıyor: sayfa {p2 + 1}."]),
        ("B'de hiç bant yok", lambda: (a_pdf, bozuk(b_pdf, "B_hic.pdf")), False,
         ["bu kitapçığın hiçbir soru sayfasında bant harfi yok (A kitapçığında var)"]),
        ("yer değiştirmiş", lambda: (b_pdf, a_pdf), False,
         ["A ve B dosyaları yer değiştirmiş olabilir"]),
        ("B yerine A seçilmiş", lambda: (a_pdf, a_pdf), False,
         ["B yerine A kitapçığı seçilmiş olabilir"]),
        ("hiç bant yok", lambda: (bozuk(a_pdf, "A_hic.pdf"), bozuk(b_pdf, "B_hic2.pdf")), False,
         ["Üst bantta kitapçık türü (A/B) yok: ne A'nın ne B'nin"]),
        ("B kapağında A", lambda: (a_pdf, bozuk(b_pdf, "B_kapak_A.pdf", [], kapak="A")), False,
         ["Kapakta 'A KİTAPÇIĞI' yazıyor ama bu B kitapçığı"]),
        ("B kapağında B", lambda: (a_pdf, bozuk(b_pdf, "B_kapak_B.pdf", [], kapak="B")), False,
         []),
        ("KDS bir sayfada yok", lambda: (bozuk(a_pdf, "A_kds.pdf", [sa[1]]), None), True,
         [f"Üst bantta kitapçık türü yok: sayfa {sa[1] + 1} (diğer sayfalarda 'A' var)"]),
    ]
    for ad, hazirla, tek, beklenen in senaryolar:
        qa, qb = hazirla()
        sor = kontrol(qa, qb, tek)[1]
        eski = tset_tek if tek else tset
        yeni = [s for s in sor if (s["onem"], s["aciklama"]) not in eski]
        bantli = [s for s in yeni if bant_mi(s)]
        eksik = [b for b in beklenen if not any(b in s["aciklama"] for s in bantli
                                                if s["onem"] == "HATA")]
        # yer değiştirmiş / aynı dosya: içerik karşılaştırması da değişir, yalnız bant bakılır
        diger = [] if ad in ("yer değiştirmiş", "B yerine A seçilmiş") else \
            [s for s in yeni if not bant_mi(s)]
        fazla = not beklenen and bantli
        tamam = not eksik and not diger and not fazla
        hepsi &= tamam
        print(f"{'✓' if tamam else '✗'} {ad}: {len(bantli)} bant sorunu"
              + (f"; bulunamayan: {eksik}" if eksik else "")
              + (f"; bant dışında {len(diger)} yeni sorun" if diger else "")
              + ("; sorun çıkmamalıydı" if fazla else ""))
        for s in (bantli + diger)[:5]:
            print(f"     {s['onem']} [{s['kitapcik']}] {s['soru']} | {s['aciklama'][:150]}")
    print("SONUÇ:", "tamam" if hepsi else "SORUN")
    return 0 if hepsi else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:6]))
