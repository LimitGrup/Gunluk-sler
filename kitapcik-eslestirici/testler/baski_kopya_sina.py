# -*- coding: utf-8 -*-
"""
A–B KONTROL'ün açık cevap ve eksik şekil denetimi gerçek bir dizgide doğru mu:
cevaplı A/B kitapçıklarından baskı kopyası üretilir (renkli cevap harfleri ve
soru kodları silinir), sonra dört durum denetlenir:

  temiz    A baskı ↔ B baskı: açık cevap bildirilmemeli (yanlış alarm yok).
  karışık  B'de bir sorunun cevabı SİYAH metin olarak, başka bir sorununki
           EĞRİ olarak (metin katmanında yok, cevap renginde çizim) bırakılır:
           tam o iki soru HATA olmalı, başka açık cevap bildirilmemeli.
  şekilsiz B'de tek şekilli bir sorunun şekli ve çok şekilli bir sorunun bir
           şekli silinir (resim/çizim; yazısı kalır): tam o iki soru
           "şekil/resim eksik" HATA'sı olmalı.
  stil     B'de 21 soruda cevap farklı renk / yazı tipi / boy / biçimde bırakılır
           (magenta, kırmızı, mavi, gri, siyah, "C)", "C.", italik, Times, 7 ve
           13 pt, kaymış, eğri, magenta sayı, beyaz): her biri beklenen önemle
           bildirilmeli; beyaz (basılmayan) harf bildirilmemeli.

Kopyalar <çıktı_klasörü> içine yazılır; kaynak PDF'lere dokunulmaz. Kitapçıkların
kendi içerik farkları (gerçek metin farkı vb.) her durumda aynı çıkar ve
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

    def egri_ciz(sayfa, x0, y0, y1, renk):     # "C" biçiminde, metin olmayan çizim
        cy = (y0 + y1) / 2
        sh = sayfa.new_shape()
        sh.draw_bezier((x0 + 5.5, cy - 3.2), (x0 + 3, cy - 6), (x0 + 0.3, cy - 4.2), (x0 + 0.3, cy))
        sh.draw_bezier((x0 + 0.3, cy), (x0 + 0.3, cy + 4.2), (x0 + 3, cy + 6), (x0 + 5.5, cy + 3.2))
        sh.finish(color=renk, width=1.3)
        sh.commit()

    def baski(src, dst, siyah=None, egri=None, sil=(), stil=()):
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
        if egri:
            _o, a = egri
            x0, y0, _x1, y1 = a["kutu"]
            egri_ciz(doc[a["satir"]["sayfa"]], x0, y0, y1, (0.93, 0, 0.55))
        for (_o, a), (_ad, renk, font, boy, kalip, dx, _bek) in stil:
            x0, y0, _x1, y1 = a["kutu"]
            sayfa = doc[a["satir"]["sayfa"]]
            if font:
                sayfa.insert_text((x0 + dx, y0 + 0.72 * (y1 - y0)), kalip.format(h=a["harf"]),
                                  fontsize=boy, fontname=font, color=renk)
            else:
                egri_ciz(sayfa, x0, y0, y1, renk)
        for pno, r in sil:                     # unutulmuş şekil
            doc[pno].add_redact_annot(fitz.Rect(r.x0 - 1, r.y0 - 1, r.x1 + 1, r.y1 + 1))
            doc[pno].apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE,
                                      graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED,
                                      text=fitz.PDF_REDACT_TEXT_NONE)
        doc.save(dst)

    # B'de şekilli sorular (KONTROL'ün şekil kutularıyla)
    with fitz.open(b_pdf) as d_:
        sekilli = [(o, m._sekil_kutulari(d_, o["nesne_bolgeleri"], {}))
                   for o in B["ogeler"] if o["no"]]
    tek = [(o, k) for o, k in sekilli if len(k) == 1]
    cok = [(o, k) for o, k in sekilli if len(k) >= 2]
    sekil_hedef = ([tek[len(tek) // 2]] if tek else []) + ([cok[len(cok) // 2]] if cok else [])
    sekil_hedef = [(o, k) for o, k in sekil_hedef if o is not siyah[0] and o is not egri[0]]

    qa, qb, qk = str(out / "A_baski.pdf"), str(out / "B_baski.pdf"), str(out / "B_karisik.pdf")
    qs = str(out / "B_sekilsiz.pdf")
    baski(a_pdf, qa)
    baski(b_pdf, qb)
    baski(b_pdf, qk, siyah=siyah, egri=egri)
    baski(b_pdf, qs, sil=[k[-1] for _o, k in sekil_hedef])

    def kontrol(b):
        ya = m.yapi_cikar(qa) if sinav == "OTOMATİK" else yapi
        yb = m.yapi_cikar(b) if sinav == "OTOMATİK" else None
        return m.kontrol_et(qa, b, ya, lambda _x: None, yapi_b=yb)[1]

    def cevap_sorunu(s):
        return any(k in s["aciklama"] for k in ("Açık kalan", "Cevap yerinde", "Cevap renginde"))

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

    sek = kontrol(qs)
    print("şekilsiz: " + ", ".join(f"{o['ders']} {o['etiket_no']} ({len(k)} şekilden biri)"
                                   for o, k in sekil_hedef))
    yaz(sek)
    eksik = [s for s in sek if "şekil/resim eksik" in s["aciklama"]]
    temiz_set = {(s["onem"], s["aciklama"]) for s in temiz}
    tamam = tamam and (len(eksik) == len(sekil_hedef)
                       and all(s["onem"] == "HATA" for s in eksik)
                       and {str(s["soru"]).split("B-")[-1] for s in eksik}
                       == {str(o["etiket_no"]) for o, _k in sekil_hedef}
                       and all((s["onem"], s["aciklama"]) in temiz_set
                               for s in sek if s not in eksik))
    # Renk / stil / biçim varyantları, her biri ayrı soruda
    MAG, KIR, MAVI, CYAN = (0.93, 0, 0.55), (0.93, 0.11, 0.14), (0, 0, 1), (0, 0.68, 0.94)
    YESIL, GRI, SIYAH, LACI, BEYAZ = (0, 0.6, 0.3), (0.5, 0.5, 0.5), (0, 0, 0), (0.1, 0.1, 0.4), (1, 1, 1)
    STIL = [  # ad, renk, yazı tipi (None: eğri), boy, metin, sağa kayma, beklenen önem
        ("magenta C", MAG, "hebo", 9, "{h}", 0, "HATA"),
        ("kırmızı C", KIR, "hebo", 9, "{h}", 0, "HATA"),
        ("mavi C", MAVI, "hebo", 9, "{h}", 0, "HATA"),
        ("camgöbeği C", CYAN, "hebo", 9, "{h}", 0, "HATA"),
        ("yeşil C", YESIL, "hebo", 9, "{h}", 0, "HATA"),
        ("gri C", GRI, "hebo", 9, "{h}", 0, "HATA"),
        ("siyah C", SIYAH, "hebo", 9, "{h}", 0, "HATA"),
        ("lacivert C", LACI, "hebo", 9, "{h}", 0, "HATA"),
        ("magenta C)", MAG, "hebo", 9, "{h})", 0, "HATA"),
        ("mavi C.", MAVI, "hebo", 9, "{h}.", 0, "HATA"),
        ("siyah C)", SIYAH, "hebo", 9, "{h})", 0, "HATA"),
        ("gri C.", GRI, "helv", 9, "{h}.", 0, "HATA"),
        ("siyah italik", SIYAH, "heit", 9, "{h}", 0, "HATA"),
        ("siyah Times", SIYAH, "tiro", 10, "{h}", 0, "HATA"),
        ("magenta 13 pt", MAG, "hebo", 13, "{h}", 0, "HATA"),
        ("siyah 7 pt", SIYAH, "helv", 7, "{h}", 0, "HATA"),
        ("siyah, 8 pt sağa kaymış", SIYAH, "hebo", 9, "{h}", 8, "HATA"),
        ("magenta eğri", MAG, None, 0, "", 0, "HATA"),
        ("siyah eğri", SIYAH, None, 0, "", 0, "UYARI"),
        ("magenta sayı '12'", MAG, "hebo", 9, "12", 0, "UYARI"),
        ("beyaz C (basılmaz)", BEYAZ, "hebo", 9, "{h}", 0, None),
    ]
    adim = max(1, len(cevaplar) // len(STIL))
    stil_hedef = [(cevaplar[i * adim], v) for i, v in enumerate(STIL) if i * adim < len(cevaplar)]
    qst = str(out / "B_stil.pdf")
    baski(b_pdf, qst, stil=stil_hedef)
    st = kontrol(qst)
    yer = lambda s, o: str(s["soru"]) == str(o["etiket_no"]) and s.get("ders") == o["ders"]
    print("stil:")
    for (o, _a), (ad, *_r, bek) in stil_hedef:
        bul = [s for s in st if cevap_sorunu(s) and yer(s, o)]
        onem = bul[0]["onem"] if bul else None
        tamam = tamam and onem == bek
        print(f"    {'✓' if onem == bek else '✗'} {ad:24s} {o['ders']} {o['etiket_no']}: "
              + (f"{onem} {bul[0]['aciklama'][:90]}" if bul else "bildirilmedi"))
    sayi = [o for (o, _a), v in stil_hedef if v[4] == "12"]
    fazla = [s for s in st if not (cevap_sorunu(s) and any(yer(s, o) for (o, _a), _v in stil_hedef))
             and (s["onem"], s["aciklama"]) not in temiz_set
             and not ("Metin farklı" in s["aciklama"] and any(f"B-{o['etiket_no']}" in str(s["soru"])
                                                            for o in sayi))]
    yaz(fazla)
    tamam = tamam and not fazla
    print("SONUÇ:", "tamam" if tamam else "SORUN")
    return 0 if tamam else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:6]))
