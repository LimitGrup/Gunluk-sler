# -*- coding: utf-8 -*-
"""
Aynı soru iki kez basılmış mı? Gerçek bir A/B çiftinde bir sorunun yerine
(numarası kalır) başka bir sorunun metni ve şıkları basılır; uygulama
"Aynı soru iki kez basılmış" HATA'sını o kitapçıkta vermeli:

  B'de tekrar              yalnız B bozulur (B dizilirken yanlış soru yapıştırılmış)
  A ve B'de tekrar         A'da ve B'de aynı soru bozulur (asıl dosyada hata)
  KDS'de tekrar            tek kitapçık (KDS) kontrolünde A bozulur
  B'de başka testten       B'de bir sorunun yerine başka testten bir soru: HATA
                           çıkmalı (A'daki soru B'de yok)
  A ve B'de başka testten  aynı bozma iki kitapçıkta: "Aynı soru iki kez basılmış"

Soru seçimi: şekilsiz, tek sayfada duran, metne bağlı grupta olmayan iki soru;
kopyalanan soru, yerine konduğu sorunun alanına sığar.

Kullanım:  python3 tekrar_sina.py <app.py> <A.pdf> <B.pdf> <OTOMATİK|TYT|AYT|...> <çıktı_klasörü>
(Yazı tipi: DejaVu Sans; KITAPCIK_TEST_FONT_DIR ile klasörü verilebilir.)
"""
import importlib.util
import os
import re
import sys
from pathlib import Path

FONT_DIR = Path(os.environ.get("KITAPCIK_TEST_FONT_DIR", "/usr/share/fonts/truetype/dejavu"))


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
    duz = fitz.Font(fontfile=str(FONT_DIR / "DejaVuSans.ttf"))
    kalin = fitz.Font(fontfile=str(FONT_DIR / "DejaVuSans-Bold.ttf"))
    yapi = m.yapi_cikar(a_pdf) if sinav == "OTOMATİK" else m.YAPILAR[sinav]

    def kontrol(qa, qb, tek=False):
        if tek:
            return m.kontrol_et(qa, qa, m.kds_yapi_cikar(qa), lambda _x: None, tek=True)
        ya = m.yapi_cikar(qa) if sinav == "OTOMATİK" else yapi
        yb = m.yapi_cikar(qb) if sinav == "OTOMATİK" else None
        return m.kontrol_et(qa, qb, ya, lambda _x: None, yapi_b=yb)

    sonuc, temiz = kontrol(a_pdf, b_pdf)
    A, B = sonuc["A"], sonuc["B"]
    a_b = {(oa["ti"], oa["no"]): ob for oa, ob, *_r in sonuc["eslesmeler"]
           if oa["no"] and ob is not None and ob["no"]}
    tset = {(s["onem"], s["aciklama"]) for s in temiz}
    _s, temiz_tek = kontrol(a_pdf, None, tek=True)
    tset_tek = {(s["onem"], s["aciklama"]) for s in temiz_tek}

    def alan(o):
        sat = o["ham_satirlar"]
        return fitz.Rect(min(r["x0"] for r in sat) - 1, min(r["y0"] for r in sat) - 1,
                         max(r["x1"] for r in sat) + 1, max(r["y1"] for r in sat) + 1)

    sekil_say = {}

    def sade_mi(kk, o):                    # tek sayfa, şekilsiz, grup dışı
        if not o["no"] or not o["ham_satirlar"]:
            return False
        if len({r["sayfa"] for r in o["ham_satirlar"]}) != 1:
            return False
        if any(o is x for b in kk["basliklar"] for x in b["sorular"]):
            return False
        p = o["ham_satirlar"][0]["sayfa"]
        key = (kk["etiket"], p)
        if key not in sekil_say:
            with fitz.open(kk["pdf"]) as d:
                sekil_say[key] = ([fitz.Rect(x["rect"]) for x in d[p].get_drawings()]
                                  + [fitz.Rect(x["bbox"]) for x in d[p].get_image_info()])
        r = alan(o)
        return not any(s.intersects(r) for s in sekil_say[key])

    def sigar(j, k):                       # j'nin metni k'nin alanına sığar mı
        rj, rk = alan(j), alan(k)
        return rj.height <= rk.height + 2 and abs(rj.width - rk.width) < 25

    def numara_eki(sp_chars, no):          # satır başındaki "12." karakter sayısı
        metin = "".join(c["c"] for c in sp_chars)
        mm = re.match(rf"\s*{no}\s*[.)]?\s*", metin)
        return mm.end() if mm else 0

    def kopyala(doc, kaynak_doc, j, k):
        """k sorusunun numarası kalır, metni ve şıkları yerine j'ninki basılır."""
        rj, rk = alan(j), alan(k)
        pj, pk = j["ham_satirlar"][0]["sayfa"], k["ham_satirlar"][0]["sayfa"]
        bas_j, bas_k = j["ham_satirlar"][0], k["ham_satirlar"][0]
        k_no = None
        for blk in doc[pk].get_text("rawdict")["blocks"]:
            for l in blk.get("lines", []):
                for sp in l["spans"]:
                    ch = sp["chars"]
                    if ch and abs(ch[0]["bbox"][0] - bas_k["x0"]) < 1.5 and \
                            abs(ch[0]["bbox"][1] - bas_k["y0"]) < 3 and numara_eki(ch, k["no"]):
                        k_no = (ch[0]["origin"], sp["size"])
        if k_no is None:
            raise RuntimeError(f"numara bulunamadı: {k['no']}")
        dx, dy = bas_k["x0"] - bas_j["x0"], bas_k["y0"] - bas_j["y0"]
        yazilar = []
        for blk in kaynak_doc[pj].get_text("rawdict")["blocks"]:
            for l in blk.get("lines", []):
                for sp in l["spans"]:
                    ch = [c for c in sp["chars"] if fitz.Rect(c["bbox"]).intersects(rj)]
                    if not ch:
                        continue
                    if abs(ch[0]["bbox"][0] - bas_j["x0"]) < 1.5 and \
                            abs(ch[0]["bbox"][1] - bas_j["y0"]) < 3:
                        ch = ch[numara_eki(ch, j["no"]):]      # j'nin numarası atlanır
                    if not ch:
                        continue
                    metin = "".join(c["c"] for c in ch).replace("\t", " ")
                    if not metin.strip():
                        continue
                    yazilar.append((ch[0]["origin"], metin, sp["size"], bool(sp["flags"] & 16),
                                    ch[-1]["bbox"][2] - ch[0]["bbox"][0]))
        page = doc[pk]
        page.add_redact_annot(rk)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                              graphics=fitz.PDF_REDACT_LINE_ART_NONE)
        tw = fitz.TextWriter(page.rect)
        tw.append(k_no[0], f"{k['no']}.", font=kalin, fontsize=k_no[1])
        for (x, y), metin, boy, kal, gen in yazilar:
            f_ = kalin if kal else duz
            g = f_.text_length(metin, fontsize=boy)
            if gen > 0 and g > gen:
                boy *= gen / g               # eski genişliğe sığsın (taşmasın)
            tw.append((x + dx, y + dy), metin, font=f_, fontsize=boy)
        tw.write_text(page)

    def cift_sec(kk, sart=None, ayni_test=True):
        sor = [o for o in kk["ogeler"] if sade_mi(kk, o)]
        for j in sor:
            for k in reversed(sor):
                if k is j or (j["ti"] == k["ti"]) != ayni_test:
                    continue
                if ayni_test and k["ham_satirlar"][0]["sayfa"] == j["ham_satirlar"][0]["sayfa"]:
                    continue
                if sigar(j, k) and (sart is None or sart(j, k)):
                    return j, k
        return None

    def b_karsiligi(j, k):
        jb, kb = a_b.get((j["ti"], j["no"])), a_b.get((k["ti"], k["no"]))
        if jb is None or kb is None or not sade_mi(B, jb) or not sade_mi(B, kb) \
                or not sigar(jb, kb):
            return None
        return jb, kb

    def bozuk_kopya(pdf, j, k, ad):
        d, kd = fitz.open(pdf), fitz.open(pdf)
        kopyala(d, kd, j, k)
        yol = str(out / ad)
        d.save(yol)
        return yol

    hepsi = True

    def yaz(ad, sor, eski, beklenen, ekstra=""):
        nonlocal hepsi
        yeni = [s for s in sor if (s["onem"], s["aciklama"]) not in eski]
        hata = [s for s in yeni if s["onem"] == "HATA"]
        eksik = [p for p in beklenen if not any(all(q in s["aciklama"] for q in p) for s in hata)]
        tamam = not eksik and bool(hata)
        hepsi &= tamam
        print(f"{'✓' if tamam else '✗'} {ad}{ekstra}: {len(hata)} HATA"
              + (f"; bulunamayan: {eksik}" if eksik else ""))
        for s in yeni[:6]:
            print(f"     {s['onem']} [{s['kitapcik']}] {s['test']} | {s['soru']} | "
                  f"{s['aciklama'][:130]}")

    def nolar(j, k):
        return f"{min(j['no'], k['no'])}. ve {max(j['no'], k['no'])}."

    # 1) B'de tekrar
    c = cift_sec(B)
    if c:
        j, k = c
        qb = bozuk_kopya(b_pdf, j, k, "B_tekrar.pdf")
        yaz("B'de tekrar", kontrol(a_pdf, qb)[1], tset,
            [("Aynı soru iki kez basılmış", nolar(j, k))],
            f" ({j['ders']} B-{j['no']} → B-{k['no']} yerine)")
    else:
        print("– B'de tekrar: uygun soru çifti yok")

    # 2) A ve B'de tekrar (asıl dosyada hata: iki kitapçıkta da) + 3) KDS
    c = cift_sec(A, sart=lambda j, k: b_karsiligi(j, k) is not None)
    if c:
        j, k = c
        jb, kb = b_karsiligi(j, k)
        qa = bozuk_kopya(a_pdf, j, k, "A_tekrar.pdf")
        qb = bozuk_kopya(b_pdf, jb, kb, "B_tekrar2.pdf")
        yaz("A ve B'de tekrar", kontrol(qa, qb)[1], tset,
            [("Aynı soru iki kez basılmış", nolar(j, k)),
             ("Aynı soru iki kez basılmış", nolar(jb, kb))],
            f" ({j['ders']} A-{j['no']} → A-{k['no']}, B-{jb['no']} → B-{kb['no']})")
        yaz("KDS'de tekrar", kontrol(qa, None, tek=True)[1], tset_tek,
            [("Aynı soru iki kez basılmış", nolar(j, k))])
    else:
        print("– A ve B'de tekrar: uygun soru çifti yok")

    # 4) B'de başka testten bir soru
    c = cift_sec(B, ayni_test=False)
    if c:
        j, k = c
        qb = bozuk_kopya(b_pdf, j, k, "B_baska_test.pdf")
        yaz("B'de başka testten", kontrol(a_pdf, qb)[1], tset, [],
            f" ({j['ders']} B-{j['no']} → {k['ders']} B-{k['no']} yerine)")
    else:
        print("– B'de başka testten: uygun soru çifti yok")

    # 5) A ve B'de başka testten (asıl dosyada: bir soru başka testte de basılmış)
    c = cift_sec(A, sart=lambda j, k: b_karsiligi(j, k) is not None, ayni_test=False)
    if c:
        j, k = c
        jb, kb = b_karsiligi(j, k)
        qa = bozuk_kopya(a_pdf, j, k, "A_baska_test.pdf")
        qb = bozuk_kopya(b_pdf, jb, kb, "B_baska_test2.pdf")
        yaz("A ve B'de başka testten", kontrol(qa, qb)[1], tset,
            [("Aynı soru iki kez basılmış", "iki ayrı testte")],
            f" ({j['ders']} A-{j['no']} → {k['ders']} A-{k['no']} yerine; B'de de)")
    else:
        print("– A ve B'de başka testten: uygun soru çifti yok")
    print("SONUÇ:", "tamam" if hepsi else "SORUN")
    return 0 if hepsi else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:6]))
