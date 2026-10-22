# -*- coding: utf-8 -*-
"""
KDS (tek kitapçık) kontrolü: B kitapçığı olmayan denemede hatalar bulunuyor mu?
Baskı PDF'inin kopyaları bilerek bozulur, her kopya KDS kipinde denetlenir:

  temiz            bozulmamış kitapçık: HATA çıkmamalı
  mükerrer         ortadaki soruya bir önceki sorunun numarası yazılır
  ileri numara     ortadaki soruya iki sonraki numara yazılır
  yer değiştirmiş  ardışık iki sorunun numaraları değiştirilir
  numara silinmiş  ortadaki sorunun numarası silinir
  soru silinmiş    son soru (yazısı ve şekliyle) silinir: bant ile sayı uyuşmaz
  bant yanlış      bantta soru sayısı bir eksik yazılır
  açık cevap       bir sorunun cevap yerine SİYAH harf basılır
  açık kod         bir soruya SİYAH soru kodu basılır

Her senaryoda beklenen HATA o soruda çıkmalı; yan HATA en çok belirtilen kadar.
Kopyalar <çıktı_klasörü> içine yazılır; kaynak PDF'e dokunulmaz.

Kullanım:  python3 kds_sina.py <app.py> <kitapcik.pdf> <çıktı_klasörü>
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


def main(app, pdf, cikti):
    m = yukle("kitapcik_app", app)
    m.bagimliliklari_yukle()
    fitz = m.fitz
    out = Path(cikti)
    out.mkdir(parents=True, exist_ok=True)

    def kontrol(yol):
        yapi = m.kds_yapi_cikar(yol)
        return m.kontrol_et(yol, yol, yapi, lambda _x: None, tek=True)

    sonuc, temiz = kontrol(pdf)
    testler = {}
    for o in sonuc["A"]["ogeler"]:
        if o["no"]:
            testler.setdefault(o["ti"], []).append(o)
    # Bozmalar kitapçığın en uzun testinde yapılır (çok testli denemede de)
    sorular = sorted(max(testler.values(), key=len), key=lambda o: o["no"])
    N = len(sorular)
    # Numara bozulan iki soru metne bağlı grubun dışında seçilir (grup içinde
    # numara hatası ayrıca "grup başlığı uyuşmuyor" diye de yazılır)
    grup_ici = {id(o) for b in sonuc["A"]["basliklar"] for o in b["sorular"]}
    uygun = [i for i in range(1, N - 1) if id(sorular[i]) not in grup_ici
             and id(sorular[i + 1]) not in grup_ici]
    k = uygun[len(uygun) // 2] if uygun else N // 2
    a, b_ = sorular[k], sorular[k + 1]
    n, n2 = a["no"], b_["no"]

    def numara_yeri(doc, o):
        bas = o["ham_satirlar"][0]
        page = doc[bas["sayfa"]]
        x0, y0, _x1, _y1 = (bas.get("kutular") or [(bas["x0"], bas["y0"], bas["x1"], bas["y1"])])[0]
        for blk in page.get_text("rawdict")["blocks"]:
            for l in blk.get("lines", []):
                for sp in l["spans"]:
                    ch = sp["chars"]
                    if not ch or abs(ch[0]["bbox"][0] - x0) > 1.5 or abs(ch[0]["bbox"][1] - y0) > 3:
                        continue
                    mm = re.match(r"\s*(\d{1,3})(\s*[.)])?", "".join(c["c"] for c in ch))
                    if mm and int(mm.group(1)) == o["no"]:
                        son = ch[mm.end() - 1]
                        return (page, fitz.Rect(ch[0]["bbox"][0], ch[0]["bbox"][1],
                                                son["bbox"][2], son["bbox"][3]),
                                ch[0]["origin"], sp["size"])
        raise RuntimeError(f"numara bulunamadı: {o['no']}")

    def numara_boz(degisim, yol):
        doc = fitz.open(pdf)
        yerler = [(numara_yeri(doc, o), yeni) for o, yeni in degisim]
        for (page, r, _org, _boy), _y in yerler:
            h = r.height
            page.add_redact_annot(fitz.Rect(r.x0 + 0.2, r.y0 + 0.3 * h, r.x1 - 0.2, r.y1 - 0.3 * h))
        for page in {id(p): p for (p, *_r), _y in yerler}.values():
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                                  graphics=fitz.PDF_REDACT_LINE_ART_NONE)
        for (page, _r, org, boy), yeni in yerler:
            if yeni:
                page.insert_text(org, yeni, fontsize=boy, fontname="hebo", color=(0, 0, 0))
        doc.save(yol)

    def sil(o, yol):                         # sorunun bütün satırları ve şekli
        doc = fitz.open(pdf)
        for r in o["ham_satirlar"]:
            doc[r["sayfa"]].add_redact_annot(
                fitz.Rect(r["x0"] - 1, r["y0"] + 1, r["x1"] + 1, r["y1"] - 1))
        for p_ in {r["sayfa"] for r in o["ham_satirlar"]}:
            doc[p_].apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE,
                                     graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED)
        doc.save(yol)

    def bant_yaz(yol):                       # bantta soru sayısı bir eksik
        # Bant satırının tamamı yeniden yazılır (sayı satırın içinde kalır;
        # yalnız sayıyı ayrı yazı olarak eklemek satırı bölüyordu)
        doc = fitz.open(pdf)
        hedef = f"{N} soru"
        for page in doc:
            for blk in page.get_text("rawdict")["blocks"]:
                for l in blk.get("lines", []):
                    for sp in l["spans"]:
                        ch = sp["chars"]
                        metin = "".join(c["c"] for c in ch)
                        if hedef not in metin:
                            continue
                        r = fitz.Rect(sp["bbox"])
                        h = r.height
                        page.add_redact_annot(fitz.Rect(r.x0 + .2, r.y0 + .3 * h, r.x1 - .2, r.y1 - .3 * h))
                        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                                              graphics=fitz.PDF_REDACT_LINE_ART_NONE)
                        # Türkçe harfli, eski genişliğe sığan yazı (taşmasın)
                        yeni_m = metin.replace(hedef, f"{N - 1} soru")
                        f_ = fitz.Font("helv")
                        boy = sp["size"]
                        g = f_.text_length(yeni_m, fontsize=boy)
                        if g > r.width:
                            boy *= r.width / g
                        tw = fitz.TextWriter(page.rect)
                        tw.append(ch[0]["origin"], yeni_m, font=f_, fontsize=boy)
                        tw.write_text(page)
                        doc.save(yol)
                        return
        raise RuntimeError(f"bantta '{hedef}' bulunamadı")

    def yaz(o, metin, yol, dx=2, dy=14):     # numaranın altına siyah yazı
        doc = fitz.open(pdf)
        page, r, _org, _boy = numara_yeri(doc, o)
        page.insert_text((r.x0 + dx, r.y1 + dy), metin, fontsize=9,
                         fontname="hebo" if len(metin) == 1 else "helv", color=(0, 0, 0))
        doc.save(yol)

    acik = sorular[uygun[len(uygun) // 3] if uygun else N // 3]
    senaryolar = [
        ("mükerrer", lambda y: numara_boz([(a, f"{n - 1}.")], y),
         [f"Soru numarası hatalı: {n}. sorunun yerinde '{n - 1}.' yazıyor"], 1),
        ("ileri numara", lambda y: numara_boz([(a, f"{n + 2}.")], y),
         [f"Soru numarası hatalı: {n}. sorunun yerinde '{n + 2}.' yazıyor"], 1),
        ("yer değiştirmiş", lambda y: numara_boz([(a, f"{n2}."), (b_, f"{n}.")], y),
         [f"Numaralar sırasız: {n2}. soru {n}. sorudan önce"], 1),
        ("numara silinmiş", lambda y: numara_boz([(a, None)], y),
         [f"{n}. soru bulunamadı"], None),
        ("soru silinmiş", lambda y: sil(sorular[-1], y),
         [f"Bantta bu test için {N} soru yazıyor ama testte {N - 1} soru var"], None),
        ("bant yanlış", bant_yaz,
         [f"Bantta bu test için {N - 1} soru yazıyor ama testte {N} soru var"], 2),
        ("açık cevap", lambda y: yaz(acik, "C", y),
         [f"Cevap açık: sayfa {acik['sayfa'] + 1}, soru {acik['no']} — 'C' harfi basılı kalmış"], 1),
        ("açık kod", lambda y: yaz(acik, "56LMT7D1T1S17", y, dx=22),
         [f"Soru kodu açık: sayfa {acik['sayfa'] + 1}, soru {acik['no']} — '56LMT7D1T1S17'"], 1),
    ]
    tset = {(s["onem"], s["aciklama"]) for s in temiz}
    temiz_hata = [s for s in temiz if s["onem"] == "HATA"]
    print(f"temiz: {len(temiz)} sorun ({len(temiz_hata)} HATA) | {N} soru | "
          + " | ".join(", ".join(f"{d} ({a_})" for d, a_ in t["dersler"]) for t in sonuc["yapi"]))
    for s in temiz:
        print(f"     {s['onem']} {s['test']} | {s['soru']} | {s['aciklama'][:140]}")
    hepsi = not temiz_hata
    for i, (ad, boz, beklenen, en_cok) in enumerate(senaryolar):
        yol = str(out / f"kds_{i}.pdf")
        boz(yol)
        yeni = [s for s in kontrol(yol)[1] if (s["onem"], s["aciklama"]) not in tset]
        hata = [s for s in yeni if s["onem"] == "HATA"]
        eksik = [p for p in beklenen
                 if not any(any(q in s["aciklama"] for q in p.split("|")) for s in hata)]
        fazla = en_cok is not None and len(hata) > en_cok
        tamam = not eksik and not fazla
        hepsi &= tamam
        print(f"{'✓' if tamam else '✗'} {ad}: {len(yeni)} yeni sorun"
              + (f"; bulunamayan: {eksik}" if eksik else "")
              + (f"; en çok {en_cok} HATA olmalıydı (yan hata)" if fazla else ""))
        for s in yeni:
            print(f"     {s['onem']} {s['test']} | {s['soru']} | {s['aciklama'][:150]}")
    print("SONUÇ:", "tamam" if hepsi else "SORUN")
    return 0 if hepsi else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
