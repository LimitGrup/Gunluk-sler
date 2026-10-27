# -*- coding: utf-8 -*-
"""
Soru numarası yazı stili koruması: soru numarası hizasında duran, soru
numaralarından FARKLI stilde (ince, küçük punto) numaralı yazılar soru başı
sanılmamalı; ama farklı stilde basılmış gerçek bir numara hatası yine
bulunmalı.

Gürültü (A ve B'ye aynı yazı basılır; KONTROL'de yeni sorun çıkmamalı,
EŞLEŞTİR'in A→B numaraları değişmemeli):
  etiket           altı boş sorunun altına, numara hizasında tek satır
                   "<sonraki numara>. Kat" (ince, 8 pt); B'de aynı sorunun altına
  dönem altlığı    her sayfanın sol altına numara hizasında "2. DÖNEM" (7 pt)

Gerçek hata (yalnız B bozulur; o soruda HATA çıkmalı):
  doğru numara     ortadaki sorunun numarası DOĞRU ama ince/küçük yazılır:
                   yeni HATA çıkmamalı (soru kaybolmamalı)
  ileri numara     ortadaki soruya iki sonraki numara, ince/küçük
  mükerrer         ortadaki soruya bir önceki numara, ince/küçük
  yer değiştirmiş  ardışık iki sorunun numaraları değişir, ince/küçük

Kullanım:  python3 stil_sina.py <app.py> <A.pdf> <B.pdf> <OTOMATİK|TYT|AYT|...> <çıktı_klasörü>
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
    A, B = m._kitapciklari_hazirla(a_pdf, b_pdf, yapi, None, None)

    def sol_hiza(k):
        sonuc = {}
        for o in k["ogeler"]:
            if o["no"] and o["ham_satirlar"]:
                bas = o["ham_satirlar"][0]
                p = bas["sayfa"]
                if bas["x0"] < k["genislikler"][p] / 2:
                    sonuc[p] = min(sonuc.get(p, bas["x0"]), bas["x0"])
        return sonuc

    def alt_uclar(k):
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

    def bos_mu(doc, p, x, alt):
        sayfa = doc[p]
        bolge = fitz.Rect(x - 2, alt + 4, x + 70, alt + 30)
        if bolge.y1 > sayfa.rect.height - 110:
            return False
        if any(fitz.Rect(w[:4]).intersects(bolge) for w in sayfa.get_text("words")):
            return False
        if any(fitz.Rect(d["rect"]).intersects(bolge) for d in sayfa.get_drawings()):
            return False
        return not any(fitz.Rect(i["bbox"]).intersects(bolge) for i in sayfa.get_image_info())

    def etiket_yerleri(tab):
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
                metin = f"{an + 1}. Kat"
                yer_a[pa], yer_b[pb] = (xa, alta, metin), (xb, altb, metin)
        return yer_a, yer_b

    def gurultu_bas(src, dst, k, tur, yerler=None):
        doc = fitz.open(src)
        if tur == "dönem altlığı":
            for p, sol in sol_hiza(k).items():
                sayfa = doc[p]
                H = sayfa.rect.height
                bolge = fitz.Rect(sol - 2, H - 64, sol + 60, H - 44)
                if (any(fitz.Rect(w[:4]).intersects(bolge) for w in sayfa.get_text("words"))
                        or any(fitz.Rect(d["rect"]).intersects(bolge)
                               for d in sayfa.get_drawings())):
                    continue                  # o sayfanın altı dolu (yazıya binmesin)
                sayfa.insert_text((sol, H - 52), "2. DÖNEM", fontsize=7,
                                  fontname="hebo", color=(0, 0, 0))
        for p, (x, alt, metin) in (yerler or {}).items():
            doc[p].insert_text((x, alt + 16), metin, fontsize=8, fontname="helv",
                               color=(0, 0, 0))
        doc.save(dst)

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

    def numara_boz(degisim, yol):            # ince ve %80 puntoyla yeniden yazar
        doc = fitz.open(b_pdf)
        yerler = [(numara_yeri(doc, o), yeni) for o, yeni in degisim]
        for (page, r, _org, _boy), _y in yerler:
            h = r.height
            page.add_redact_annot(fitz.Rect(r.x0 + 0.2, r.y0 + 0.3 * h, r.x1 - 0.2, r.y1 - 0.3 * h))
        for page in {id(p): p for (p, *_r), _y in yerler}.values():
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                                  graphics=fitz.PDF_REDACT_LINE_ART_NONE)
        for (page, _r, org, boy), yeni in yerler:
            page.insert_text(org, yeni, fontsize=boy * 0.8, fontname="helv", color=(0, 0, 0))
        doc.save(yol)

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

    def yaz(s):
        print(f"     {s['onem']} [{s['kitapcik']}] {s['test']} | {s['soru']} | "
              f"{s['aciklama'][:130]}")

    for tur in ("etiket", "dönem altlığı"):
        qa, qb = str(out / f"A_{tur}.pdf"), str(out / f"B_{tur}.pdf")
        yer_a, yer_b = etiket_yerleri(temiz_tablo) if tur == "etiket" else ({}, {})
        gurultu_bas(a_pdf, qa, A, tur, yer_a)
        gurultu_bas(b_pdf, qb, B, tur, yer_b)
        yeni = [s for s in kontrol(qa, qb) if (s["onem"], s["aciklama"]) not in tset]
        tab = tablo(qa, qb, tur)
        fark = [(x, y) for x, y in zip(temiz_tablo, tab) if x != y]
        tamam = not yeni and not fark and len(tab) == len(temiz_tablo)
        hepsi &= tamam
        ek = f" ({len(yer_a)} sayfada)" if tur == "etiket" else ""
        print(f"{'✓' if tamam else '✗'} {tur}{ek}: KONTROL {len(yeni)} yeni sorun, "
              f"EŞLEŞTİR {len(fark)} satır farklı")
        for s in yeni[:10]:
            yaz(s)
        for x, y in fark[:6]:
            print(f"     EŞLEŞTİR {x} → {y}")

    testler = {}
    for o in B["ogeler"]:
        if o["no"]:
            testler.setdefault(o["ti"], []).append(o)
    s1 = sorted(max(testler.values(), key=len), key=lambda o: o["no"])
    grup_ici = {id(o) for b in B["basliklar"] for o in b["sorular"]}
    uygun = [i for i in range(1, len(s1) - 1) if id(s1[i]) not in grup_ici
             and id(s1[i + 1]) not in grup_ici]
    k = uygun[len(uygun) // 2] if uygun else len(s1) // 2
    a, b_ = s1[k], s1[k + 1]
    n, n2 = a["no"], b_["no"]
    senaryolar = [
        ("doğru numara", [(a, f"{n}.")], [], 0),
        ("ileri numara", [(a, f"{n + 2}.")],
         [f"{n}. soru bulunamadı|{n}. sorunun yerinde '{n + 2}.'"], None),
        ("mükerrer", [(a, f"{n - 1}.")],
         [f"{n}. soru bulunamadı|{n}. sorunun yerinde '{n - 1}.'"], None),
        ("yer değiştirmiş", [(a, f"{n2}."), (b_, f"{n}.")],
         [f"{n}. soru bulunamadı|{n2}. soru bulunamadı|Numaralar sırasız: {n2}. soru {n}. sorudan önce"
          f"|{n}. sorunun yerinde '{n2}.'"], None),
    ]
    for i, (ad, degisim, beklenen, en_cok) in enumerate(senaryolar):
        yol = str(out / f"B_stil{i}.pdf")
        numara_boz(degisim, yol)
        yeni = [s for s in kontrol(a_pdf, yol) if (s["onem"], s["aciklama"]) not in tset]
        hata = [s for s in yeni if s["onem"] == "HATA"]
        eksik = [p for p in beklenen
                 if not any(any(q in s["aciklama"] for q in p.split("|")) for s in hata)]
        fazla = en_cok is not None and len(hata) > en_cok
        tamam = not eksik and not fazla
        hepsi &= tamam
        print(f"{'✓' if tamam else '✗'} {ad} (ince/küçük, {a['ders']} {n}): {len(yeni)} yeni sorun, "
              f"{len(hata)} HATA" + (f"; bulunamayan: {eksik}" if eksik else "")
              + (f"; en çok {en_cok} HATA olmalıydı" if fazla else ""))
        for s in yeni[:8]:
            yaz(s)
    print("SONUÇ:", "tamam" if hepsi else "SORUN")
    return 0 if hepsi else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:6]))
