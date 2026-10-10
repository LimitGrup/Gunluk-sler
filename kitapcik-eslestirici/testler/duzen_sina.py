# -*- coding: utf-8 -*-
"""
Cevap motoru dayanıklılık sınaması: gerçek denemelerde görülen şık dizilişleri
ve dizgi durumlarıyla A/B kitapçıkları üretir, EŞLEŞTİR'in cevap harfini ve B
numarasını, A–B KONTROL'ün açık cevap denetimini gerçek değerle karşılaştırır.

Üretilen her soruda (A ile B'de aynı):
  - şık dizilişi: alt alta | yan yana | 3+2 | 2+2+1  (4 şıklı testte 2+2 | yan yana)
  - bazılarında şekil ve şeklin içinde KIRMIZI "A" / "B" etiketleri (cevap değil)
  - bazılarında cevap harfinin yanında renkli soru kodu
  - bazılarında şıklar bir sonraki sütuna/sayfaya taşar (cevap harfi şıkların yanında)
Sayfa düzeni: iki sütunlu testler + tam genişlik (tek sütun) testler.
Cevap harfinin yeri iki biçimde denenir:
  sik    — A şıkkı hizasında, sol boşlukta (gerçek denemelerdeki gibi)
  numara — soru numarasının hemen altında

Kullanım:  python3 duzen_sina.py <app.py> <cikti_klasoru>
"""
import importlib.util
import random
import sys
from pathlib import Path

import pymupdf as fitz

KIRMIZI = (0.93, 0.11, 0.14)
DUZENLER5 = ["alt", "yan", "3+2", "2+2+1"]
DUZENLER4 = ["alt", "yan", "2+2"]
SAYI = ("12 15 18 20 24 27 30 32 36 40 45 48 54 60 64 72 80 90 96 100 "
        "108 120 135 144").split()


def yukle(ad, yol):
    spec = importlib.util.spec_from_file_location(ad, yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def icerik(g, tohum):
    """5 şıklı (iki sütun + tam genişlik) ve 4 şıklı testler; her soruya düzen,
    şekil/etiket, kod ve taşma özelliği atanır."""
    rng = random.Random(tohum)
    t5 = g.icerik_uret([
        ("SÖZEL BÖLÜM - TÜRKÇE", [("Türkçe", 16)], False, {"Türkçe": {4: 2}}),
        ("SAYISAL BÖLÜM - MATEMATİK", [("Matematik", 16)], True, {}),
    ], 5, tohum)
    t4 = g.icerik_uret([
        ("SAYISAL BÖLÜM - FEN BİLİMLERİ", [("Fen Bilimleri", 16)], False, {}),
        ("SÖZEL BÖLÜM - İNGİLİZCE", [("İngilizce", 12)], True, {}),
    ], 4, tohum + 1)
    testler = t5 + t4
    sira = 0
    for t in testler:
        for _d, birimler in t["dersler"]:
            for blk in birimler:
                for s in blk["sorular"]:
                    sira += 1
                    duzenler = DUZENLER5 if len(s["sik"]) == 5 else DUZENLER4
                    s["duzen"] = duzenler[sira % len(duzenler)]
                    if s["duzen"] != "alt":          # yan yana dizilecek kısa şıklar
                        s["sik"] = rng.sample(SAYI, len(s["sik"]))
                    s["etiket"] = sira % 3 == 0       # şekilde kırmızı A/B etiketi
                    if s["etiket"]:
                        s["sekil"] = "kare"
                    s["kod"] = sira % 4 == 1          # cevabın yanında renkli kod
                    s["tasma"] = sira % 7 == 3 and blk["parca"] is None
    return testler


def dizgi_sinifi(g, yer):
    class Dizgi(g.Dizgi):
        def soru(self, no, govde, secenekler, cevap, sekil=None, numara_metni=None,
                 cevap_acik=False, s=None):
            s = s or {}
            duzen = s.get("duzen", "alt")
            _x, gen = self.sutun_x()
            sat_g = self._sar(govde, gen - 20)
            harfler = "ABCDE"[:len(secenekler)]
            if duzen == "alt":
                sik_satir = [[i] for i in range(len(secenekler))]
            elif duzen == "yan":
                sik_satir = [list(range(len(secenekler)))]
            elif duzen == "3+2":
                sik_satir = [[0, 1, 2], [3, 4]]
            elif duzen == "2+2+1":
                sik_satir = [[0, 1], [2, 3], [4]]
            else:                                    # 2+2
                sik_satir = [[0, 1], [2, 3]]
            sik_yuk = 14 * len(sik_satir) + 8
            govde_yuk = 12 * len(sat_g) + (50 if sekil else 0) + 18
            tasma = s.get("tasma")
            self.yer_ac(govde_yuk + (0 if tasma else sik_yuk))
            x, gen = self.sutun_x()
            ic = x + 18
            self.y += 12
            y_no = self.y
            self._yaz(x, y_no, numara_metni or f"{no}.", kalin=True)
            cevapli = self.cevapli or cevap_acik

            def isaret(xx, yy):
                if cevap_acik == "siyah":            # rengi elle siyaha çevrilmiş
                    self._yaz(xx, yy, cevap, boy=9, kalin=True)
                    return
                if cevap_acik == "egri":             # eğriye çevrilmiş: metin yok
                    k_ = fitz.Rect(xx, yy - 8, xx + 6, yy)
                    self.sayfa.draw_polyline([k_.bl, (k_.x0 + 3, k_.y0), k_.br],
                                             color=g.MAGENTA, width=1.4)
                    self.sayfa.draw_line((k_.x0 + 1.2, k_.y1 - 3), (k_.x1 - 1.2, k_.y1 - 3),
                                         color=g.MAGENTA, width=1.2)
                    return
                self._yaz(xx, yy, cevap, boy=9, kalin=True, renk=g.MAGENTA)
                if s.get("kod") and yer == "sik":
                    self._yaz(ic, yy, f"56TS{no:02d}T1S{no}", boy=7, renk=g.MAGENTA)

            if cevapli and yer == "numara":
                isaret(x + 2, y_no + 14)
            for i, satir in enumerate(sat_g):
                if i:
                    self.y += 12
                self._yaz(ic, self.y, satir, kalin=(i == len(sat_g) - 1))
            if sekil:
                self.y += 8
                r = fitz.Rect(ic + 10, self.y, ic + 60, self.y + 40)
                self.sayfa.draw_rect(r, color=g.SIYAH, fill=(0.6, 0.8, 0.95))
                if s.get("etiket"):                  # şekil içi renkli etiketler
                    self._yaz(r.x0 + 4, r.y0 + 12, "A", boy=9, kalin=True, renk=KIRMIZI)
                    self._yaz(r.x1 - 10, r.y1 - 4, "B", boy=9, kalin=True, renk=KIRMIZI)
                self.y += 42
            if tasma:                                # şıklar sonraki sütuna/sayfaya
                self.y = g.ALT
                self.yer_ac(sik_yuk)
                x, gen = self.sutun_x()
                ic = x + 18
            self.y += 6
            hucre = (gen - 18) / max(len(r_) for r_ in sik_satir)
            for j, satir in enumerate(sik_satir):
                self.y += 14
                if j == 0 and cevapli and yer == "sik":
                    isaret(x, self.y - 10)           # A şıkkı hizası, sol boşluk
                for k, i in enumerate(satir):
                    self._yaz(ic + k * hucre, self.y,
                              f"{harfler[i]}) {secenekler[i]}"[:60])
            self.y += 8
    return Dizgi


def dizgile(g, Dizgi, testler, harf, kod, yol, cevapli=True, acik=None, acik_tur=True):
    d = Dizgi(harf, kod, cevapli)
    for ti, t in enumerate(testler):
        toplam = sum(len(b["sorular"]) for _d, bl in t["dersler"] for b in bl)
        d.bolum(t["ad"], toplam, tek_sutun=t["tek"])
        no = 0
        for _ders, birimler in t["dersler"]:
            for b in birimler:
                nolar = list(range(no + 1, no + 1 + len(b["sorular"])))
                if b["parca"]:
                    d.grup_basligi(nolar, b["parca"])
                for s in b["sorular"]:
                    no += 1
                    d.soru(no, s["govde"], s["sik"], s["cevap"], sekil=s["sekil"],
                           cevap_acik=(acik_tur if acik == (ti, no) else False), s=s)
    d.kaydet(yol)


def main(app, cikti):
    cikti = Path(cikti)
    cikti.mkdir(parents=True, exist_ok=True)
    g = yukle("ornek_pdf_uret", Path(__file__).with_name("ornek_pdf_uret.py"))
    m = yukle("kitapcik_app", app)
    m.bagimliliklari_yukle()
    a = icerik(g, 31)
    b = g.karistir(a, 32)
    ha, hb = g.numara_haritasi(a), g.numara_haritasi(b)
    b_no = {id(s): key[1] for key, s in hb.items()}
    toplam_hata = 0
    for yer in ("sik", "numara"):
        Dizgi = dizgi_sinifi(g, yer)
        pa, pb = cikti / f"duzen_{yer}_A.pdf", cikti / f"duzen_{yer}_B.pdf"
        dizgile(g, Dizgi, a, "A", "26279901", pa)
        dizgile(g, Dizgi, b, "B", "26279902", pb)
        # --- EŞLEŞTİR: cevap harfi ve B numarası --------------------------------
        log = []
        x = cikti / f"_duzen_{yer}.xlsx"
        m.calistir(str(pa), str(pb), "OTOMATİK", None, None, None, str(x), log.append)
        import openpyxl
        satirlar = [r for r in list(openpyxl.load_workbook(x)["OTOMATİK"].iter_rows(
            values_only=True))[1:] if r[2] is not None]
        yanlis_c, yanlis_b = [], []
        for ((ti, no), s), r in zip(sorted(ha.items()), satirlar):
            if r[3] != s["cevap"]:
                yanlis_c.append((ti + 1, no, s["duzen"], r[3], s["cevap"]))
            if r[4] != b_no[id(s)]:
                yanlis_b.append((ti + 1, no, r[4], b_no[id(s)]))
        cevap_uyari = [l for l in log if "CEVAP" in l and "⚠" in l]
        print(f"[{yer}] EŞLEŞTİR: cevap {len(ha) - len(yanlis_c)}/{len(ha)}, "
              f"B numarası {len(ha) - len(yanlis_b)}/{len(ha)}, cevap uyarısı "
              f"{len(cevap_uyari)}")
        for y_ in yanlis_c[:8]:
            print("     yanlış cevap (test, no, düzen, okunan, doğru):", y_)
        for y_ in yanlis_b[:5]:
            print("     yanlış B no (test, no, okunan, doğru):", y_)
        for u in cevap_uyari[:5]:
            print("     ", u)
        toplam_hata += len(yanlis_c) + len(yanlis_b) + len(cevap_uyari)
        # --- A–B KONTROL: baskıda açık cevap -------------------------------------
        qa, qb = cikti / f"duzen_{yer}_A_baski.pdf", cikti / f"duzen_{yer}_B_baski.pdf"
        dizgile(g, Dizgi, a, "A", "26279901", qa, cevapli=False)
        dizgile(g, Dizgi, b, "B", "26279902", qb, cevapli=False)
        etiketli = sorted(k for k, s in hb.items() if s.get("etiket"))
        tasan = sorted(k for k, s in hb.items() if s.get("tasma"))
        sade = sorted(k for k, s in hb.items() if not s.get("etiket") and not s.get("tasma"))
        durumlar = [("temiz", None, True), (f"açık renkli {etiketli[0]}", etiketli[0], True),
                    (f"açık renkli {tasan[0]}", tasan[0], True),
                    (f"açık SİYAH {sade[3]}", sade[3], "siyah"),
                    (f"açık EĞRİ {sade[7]}", sade[7], "egri")]
        for ad, acik, tur in durumlar:
            qb2 = cikti / f"duzen_{yer}_B_baski_{'temiz' if acik is None else 'acik'}.pdf"
            dizgile(g, Dizgi, b, "B", "26279902", qb2, cevapli=False, acik=acik,
                    acik_tur=tur)
            yapi = m.yapi_cikar(str(qa))
            _sonuc, sorunlar = m.kontrol_et(str(qa), str(qb2), yapi, lambda _x: None,
                                            yapi_b=m.yapi_cikar(str(qb2)))
            hata = [s_ for s_ in sorunlar if s_["onem"] == "HATA"]
            acik_bulunan = [s_ for s_ in hata if "Açık kalan" in s_["aciklama"]
                            or "Cevap yerinde" in s_["aciklama"]]
            sorular_ = {(s_["test"], s_["soru"]) for s_ in acik_bulunan}
            beklenen = set() if acik is None else {str(acik[1])}
            durum = "tamam" if (len(hata) == len(acik_bulunan)
                                and {q for _t, q in sorular_} == beklenen
                                and len(sorular_) == len(beklenen)) else "SORUN"
            print(f"[{yer}] KONTROL baskı ({ad}): {len(hata)} HATA, açık cevaplı soru "
                  f"{sorted(q for _t, q in sorular_)} (beklenen {sorted(beklenen)}) → {durum}")
            for s_ in hata[:4]:
                print("     ", s_["test"], s_["soru"], s_["aciklama"][:100])
            toplam_hata += durum != "tamam"
    print("SONUÇ:", "temiz" if not toplam_hata else f"{toplam_hata} sorun")


if __name__ == "__main__":
    main(*sys.argv[1:3])
