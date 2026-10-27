# -*- coding: utf-8 -*-
"""
TYT/AYT şablonundan farklı düzenli deneme (ör. Sosyal Bilimler 25 değil 20
soru olan kurs denemesi) TYT seçiliyken denetlenir. Uygulama, EŞLEŞTİR'deki
gibi yapıyı kitapçıktan okumalı (21–25 "bulunamadı" demeden) ve bunu raporda
bir UYARI ile söylemeli; gerçek hatalar yine bulunmalı:

  temiz                 HATA yok, şablon farkını söyleyen 1 UYARI var
  B'de son soru yok     farklı testin son sorusu B'den silinir
  A ve B'de son soru yok  aynı soru iki kitapçıktan da silinir (bant 20, basılı 19)
  B'de mükerrer numara  farklı testin ortadaki sorusuna önceki numara
  B'de bant şablon gibi B'nin bandında şablondaki sayı yazar (20 yerine 25)
  A ve B'de bant şablon gibi  iki kitapçığın bandında da şablondaki sayı

Kullanım:  python3 sablon_sina.py <app.py> <A.pdf> <B.pdf> <TYT|AYT> <çıktı_klasörü>
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

    def adet(t):
        return sum(int(a) for _d, a in t["dersler"])
    sablon = m.YAPILAR[sinav]
    oto = m.yapi_cikar(a_pdf)
    farkli = [i for i, (s, t) in enumerate(zip(sablon, oto)) if adet(s) != adet(t)]
    if len(sablon) != len(oto) or not farkli:
        print(f"Bu çift {sinav} şablonundan farklı değil; sınanacak bir şey yok.")
        return 1
    ti = farkli[0]
    n, f_ = adet(oto[ti]), adet(sablon[ti])
    A, B = m._kitapciklari_hazirla(a_pdf, b_pdf, oto, None, None)

    def sorular(k):
        return sorted((o for o in k["ogeler"] if o["ti"] == ti and o["no"]),
                      key=lambda o: o["no"])
    sa, sb = sorular(A), sorular(B)
    grup_ici = {id(o) for b in B["basliklar"] for o in b["sorular"]}
    uygun = [o for o in sb[1:-1] if id(o) not in grup_ici]
    orta = uygun[len(uygun) // 2] if uygun else sb[len(sb) // 2]

    def numara_yeri(doc, o):
        bas = o["ham_satirlar"][0]
        page = doc[bas["sayfa"]]
        x0, y0, _x1, _y1 = (bas.get("kutular") or [(bas["x0"], bas["y0"], bas["x1"], bas["y1"])])[0]
        for b in page.get_text("rawdict")["blocks"]:
            for l in b.get("lines", []):
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
        raise RuntimeError(f"numara bulunamadı: {o['ders']} {o['no']}")

    def sil(doc, o):                         # sorunun bütün satırları ve şekli
        for r in o["ham_satirlar"]:
            doc[r["sayfa"]].add_redact_annot(
                fitz.Rect(r["x0"] - 1, r["y0"] + 1, r["x1"] + 1, r["y1"] - 1))
        for p_ in {r["sayfa"] for r in o["ham_satirlar"]}:
            doc[p_].apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE,
                                     graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED)

    def numara(doc, o, yeni):
        page, r, org, boy = numara_yeri(doc, o)
        h = r.height
        page.add_redact_annot(fitz.Rect(r.x0 + 0.2, r.y0 + 0.3 * h, r.x1 - 0.2, r.y1 - 0.3 * h))
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                              graphics=fitz.PDF_REDACT_LINE_ART_NONE)
        page.insert_text(org, yeni, fontsize=boy, fontname="hebo", color=(0, 0, 0))

    def bant(doc, pdf):                      # farklı testin bandında şablondaki sayı
        sayfa_no = m._bant_listesi(pdf)[ti][0]
        page = doc[sayfa_no]
        hedef = f"{n} soru"
        for blk in page.get_text("rawdict")["blocks"]:
            for l in blk.get("lines", []):
                for sp in l["spans"]:
                    ch = sp["chars"]
                    i = "".join(c["c"] for c in ch).find(hedef)
                    if i < 0:
                        continue
                    son = ch[i + len(str(n)) - 1]
                    r = fitz.Rect(ch[i]["bbox"][0], ch[i]["bbox"][1], son["bbox"][2], son["bbox"][3])
                    h = r.height
                    page.add_redact_annot(fitz.Rect(r.x0 + .2, r.y0 + .3 * h, r.x1 - .2, r.y1 - .3 * h))
                    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                                          graphics=fitz.PDF_REDACT_LINE_ART_NONE)
                    page.insert_text(ch[i]["origin"], str(f_), fontsize=sp["size"],
                                     fontname="helv", color=(0, 0, 0))
                    return
        raise RuntimeError(f"bantta '{hedef}' bulunamadı (sayfa {sayfa_no + 1})")

    def kontrol(qa, qb):
        yakala, asil = {}, m.kontrol_et

        def sar(*a, **k):
            yakala["r"] = asil(*a, **k)
            return yakala["r"]
        m.kontrol_et = sar
        try:
            m.kontrol_calistir(qa, qb, sinav, None, None, str(out / "_rapor.pdf"),
                               lambda _x: None)
        finally:
            m.kontrol_et = asil
        return yakala["r"][1]

    def kopya(ad, a_boz=None, b_boz=None):
        qa, qb = a_pdf, b_pdf
        if a_boz:
            d = fitz.open(a_pdf)
            a_boz(d, a_pdf)
            qa = str(out / f"A_{ad}.pdf")
            d.save(qa)
        if b_boz:
            d = fitz.open(b_pdf)
            b_boz(d, b_pdf)
            qb = str(out / f"B_{ad}.pdf")
            d.save(qb)
        return qa, qb

    test = oto[ti]["test"]
    print(f"{test}: kitapçıkta {n} soru, {sinav} şablonunda {f_}")
    senaryolar = [
        ("temiz", None, None, [], 0),
        ("B'de son soru yok", None, lambda d, _p: sil(d, sb[-1]),
         [f"Bantta bu test için {n} soru yazıyor ama testte {n - 1} soru var"
          f"|A-{sa[-1]['no']} sorusu B kitapçığında bulunamadı"], None),
        ("A ve B'de son soru yok", lambda d, _p: sil(d, sa[-1]), lambda d, _p: sil(d, sb[-1]),
         [f"Bantta bu test için {n} soru yazıyor ama testte {n - 1} soru var"], None),
        ("B'de mükerrer numara", None, lambda d, _p: numara(d, orta, f"{orta['no'] - 1}."),
         [f"Soru numarası hatalı: {orta['no']}. sorunun yerinde '{orta['no'] - 1}.'"], None),
        ("B'de bant şablon gibi", None, bant,
         [f"Bantta bu test için {f_} soru yazıyor ama testte {n} soru var"], None),
        ("A ve B'de bant şablon gibi", bant, bant,
         [f"Bantta bu test için {f_} soru yazıyor ama testte {n} soru var"], None),
    ]
    hepsi = True
    for ad, a_boz, b_boz, beklenen, en_cok in senaryolar:
        sor = kontrol(*kopya(re.sub(r"\W+", "_", ad), a_boz, b_boz))
        hata = [s for s in sor if s["onem"] == "HATA"]
        uyari = [s for s in sor if s["onem"] == "UYARI" and "düzeninde değil" in s["aciklama"]]
        eksik = [p for p in beklenen
                 if not any(any(q in s["aciklama"] for q in p.split("|")) for s in hata)]
        tamam = not eksik and (en_cok is None or len(hata) <= en_cok)
        if ad == "temiz":
            tamam = tamam and len(uyari) == 1
        hepsi &= tamam
        print(f"{'✓' if tamam else '✗'} {ad}: {len(hata)} HATA, "
              f"{len(sor) - len(hata)} UYARI (şablon uyarısı: {len(uyari)})"
              + (f"; bulunamayan: {eksik}" if eksik else ""))
        for s in sor[:8]:
            print(f"     {s['onem']} [{s['kitapcik']}] {s['test']} | {s['soru']} | "
                  f"{s['aciklama'][:140]}")
    print("SONUÇ:", "tamam" if hepsi else "SORUN")
    return 0 if hepsi else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:6]))
