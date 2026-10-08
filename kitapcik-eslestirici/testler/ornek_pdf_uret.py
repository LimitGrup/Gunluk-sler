# -*- coding: utf-8 -*-
"""
Test amaçlı sentetik A/B kitapçık PDF'leri üretir (gerçek dizgiye benzer):
iki sütun, sayfa üst/alt bilgileri, magenta cevap harfleri, metne bağlı soru
grupları, tek sütunlu (2x2 şıklı) bir test, şekilli sorular.

Kullanım:  python3 ornek_pdf_uret.py <çıktı_klasörü>
Üretilenler:
  ortaokul_A.pdf, ortaokul_B.pdf          — temiz çift (B, A'nın karıştırılmışı)
  ortaokul_B_baski.pdf                    — B, magenta cevaplar olmadan (baskı)
  ortaokul_B_hatali.pdf + hatalar.txt     — bilinçli hatalar eklenmiş B
  tyt_A.pdf, tyt_B.pdf                    — sabit TYT yapısı için çift
"""
import json
import random
import sys
from pathlib import Path

import pymupdf as fitz

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MAGENTA = (0.93, 0.0, 0.55)
GRI = (0.55, 0.55, 0.55)
SIYAH = (0, 0, 0)
W, H = 595, 842
SOL, SAG, UST, ALT = 40, 555, 70, 790

KELIMELER = (
    "güneş dünya ışık enerji madde canlı hücre doku organ sistem kuvvet hareket "
    "hız ivme kütle ağırlık basınç sıcaklık ısı element bileşik karışım çözelti "
    "asit baz tuz atom molekül iyon elektron proton nötron çekirdek gezegen yıldız "
    "uydu ekosistem besin zinciri üretici tüketici ayrıştırıcı fotosentez solunum "
    "metin paragraf cümle sözcük anlam yazar okur şiir hikâye roman deneme anı "
    "gezi yazısı makale fıkra eleştiri söyleşi biyografi otobiyografi destan "
    "masal efsane tarih coğrafya kültür medeniyet devlet toplum ekonomi ticaret "
    "tarım sanayi göç nüfus iklim bitki örtüsü yer şekilleri akarsu göl deniz "
    "dağ ova plato harita ölçek koordinat enlem boylam saat dilimi mevsim "
    "istikrar başarı disiplin çaba sabır güven saygı sorumluluk özgürlük adalet "
    "eşitlik dayanışma yardımlaşma hoşgörü empati iletişim teknoloji bilim "
    "araştırma gözlem deney hipotez sonuç veri tablo grafik değişken kontrol"
).split()
FIILLER = ("açıklar gösterir belirtir etkiler değiştirir oluşturur sağlar "
           "korur artırır azaltır destekler yansıtır ifade eder").split()


def cumle(rng, n_min=7, n_max=14):
    n = rng.randint(n_min, n_max)
    k = [rng.choice(KELIMELER) for _ in range(n)]
    k.insert(rng.randint(2, n - 1), rng.choice(FIILLER))
    s = " ".join(k)
    return s[0].upper() + s[1:] + "."


class Dizgi:
    """Basit akışlı dizgi motoru: sütunlara metin kutuları yerleştirir."""

    def __init__(self, harf, kod, cevapli=True, baslik_bicimi="ve"):
        self.baslik_bicimi = baslik_bicimi   # "ve": "14 ve 15.", "nokta": "14. ve 15."
        self.doc = fitz.open()
        self.harf, self.kod, self.cevapli = harf, kod, cevapli
        self.font = fitz.Font(fontfile=FONT)
        self.fontb = fitz.Font(fontfile=FONT_B)
        self.sayfa = None
        self.sayfa_no = 0
        self.bolum_adi = ""

    # --- yardımcılar -------------------------------------------------------
    def _yaz(self, x, y, metin, boy=9, kalin=False, renk=SIYAH):
        self.sayfa.insert_text((x, y), metin, fontsize=boy,
                               fontname="dvb" if kalin else "dv",
                               fontfile=FONT_B if kalin else FONT, color=renk)

    def _sar(self, metin, genislik, boy=9, kalin=False):
        f = self.fontb if kalin else self.font
        satirlar, aktif = [], ""
        for k in metin.split():
            aday = (aktif + " " + k).strip()
            if f.text_length(aday, boy) <= genislik:
                aktif = aday
            else:
                satirlar.append(aktif)
                aktif = k
        if aktif:
            satirlar.append(aktif)
        return satirlar

    def yeni_sayfa(self, bolum_basi=False, tek_sutun=False, yonerge=None):
        self.sayfa = self.doc.new_page(width=W, height=H)
        self.sayfa_no += 1
        for i in range(5):           # üstteki "A A A A A"
            self._yaz(SOL + 10 + i * 118, 40, self.harf, boy=18, kalin=True,
                      renk=GRI)
        self.sayfa.draw_rect(fitz.Rect(SOL, 50, SAG, 72), color=(0.4, 0.7, 0.7),
                             width=0.8)
        self._yaz(W / 2 - self.fontb.text_length(self.bolum_adi, 13) / 2, 66,
                  self.bolum_adi, boy=13, kalin=True, renk=GRI)
        self._yaz(SOL, 815, "7. SINIF DENEME SINAVI", boy=7, kalin=True)
        self._yaz(W / 2 - 4, 815, str(self.sayfa_no), boy=10, kalin=True)
        self._yaz(SAG - 40, 815, self.kod, boy=7, kalin=True)
        self._yaz(SAG - 90, 828, "Diğer sayfaya geçiniz.", boy=8)
        self.y = UST + 16
        if yonerge:
            for satir in yonerge:
                self._yaz(SOL + 10, self.y, satir, boy=9, kalin=True)
                self.y += 14
            self.y += 6
        self.tek = tek_sutun
        self.sutun = 0
        self.ust_sinir = self.y
        if not tek_sutun:
            self.sayfa.draw_line((W / 2, self.y - 4), (W / 2, ALT), color=GRI,
                                 dashes="[2] 2", width=0.5)

    def sutun_x(self):
        if self.tek:
            return SOL, SAG - SOL
        if self.sutun == 0:
            return SOL, W / 2 - 12 - SOL
        return W / 2 + 12, SAG - (W / 2 + 12)

    def yer_ac(self, yukseklik):
        if self.y + yukseklik <= ALT:
            return
        if not self.tek and self.sutun == 0:
            self.sutun = 1
            self.y = self.ust_sinir
            return
        self.yeni_sayfa(tek_sutun=self.tek)

    # --- öğeler ------------------------------------------------------------
    def bolum(self, ad, soru_sayisi, tek_sutun=False):
        self.bolum_adi = ad
        self.yeni_sayfa(bolum_basi=True, tek_sutun=tek_sutun, yonerge=[
            f"Bu testte {soru_sayisi} soru vardır.",
            "Cevaplarınızı, cevap kâğıdına işaretleyiniz."])

    def grup_basligi(self, numaralar, parca, tam_genislik=False):
        if len(numaralar) == 2 and self.baslik_bicimi == "nokta":
            bas = f"{numaralar[0]}. ve {numaralar[1]}. soruları"
        elif len(numaralar) == 2:
            bas = f"{numaralar[0]} ve {numaralar[1]}. soruları"
        else:
            bas = f"{numaralar[0]}-{numaralar[-1]}. soruları"
        bas += " aşağıdaki metne göre cevaplayınız."
        if tam_genislik and not self.tek:
            x, gen = SOL, SAG - SOL
        else:
            x, gen = self.sutun_x()
        sat_bas = self._sar(bas, gen - 12, kalin=True)
        sat_par = self._sar(parca, gen - 6)
        yuk = 14 * len(sat_bas) + 12 + 12 * len(sat_par)
        if not tam_genislik:
            self.yer_ac(min(yuk, 300))
            x, gen = self.sutun_x()
        y0 = self.y
        self.sayfa.draw_rect(fitz.Rect(x, y0 - 2, x + gen, y0 + 14 * len(sat_bas) + 2),
                             color=SIYAH, width=0.6)
        for s in sat_bas:
            self.y += 11
            self._yaz(x + 6, self.y, s, kalin=True)
        self.y += 14
        for s in sat_par:
            if not tam_genislik:
                self.yer_ac(12)
            self.y += 12
            self._yaz(x + 3, self.y, s)
        self.y += 12
        if tam_genislik and not self.tek:
            self.ust_sinir = self.y
            self.sayfa.draw_line((W / 2, self.y - 4), (W / 2, ALT), color=GRI,
                                 dashes="[2] 2", width=0.5)

    def soru(self, no, govde, secenekler, cevap, sekil=None, numara_metni=None):
        _x, gen = self.sutun_x()
        sat_g = self._sar(govde, gen - 20, kalin=False)
        iki_sutunlu_sik = self.tek and all(
            self.font.text_length(s, 9) < gen / 2 - 30 for s in secenekler)
        if iki_sutunlu_sik:
            sik_yuk = 14 * ((len(secenekler) + 1) // 2)
        else:
            sik_yuk = 14 * len(secenekler)
        yuk = 12 * len(sat_g) + sik_yuk + (50 if sekil else 0) + 18
        self.yer_ac(yuk)
        x, gen = self.sutun_x()
        ic = x + 18
        self.y += 12
        y_no = self.y
        self._yaz(x, y_no, numara_metni or f"{no}.", kalin=True)
        if self.cevapli:
            self._yaz(x + 2, y_no + 14, cevap, boy=9, kalin=True, renk=MAGENTA)
        for i, s in enumerate(sat_g):
            if i:
                self.y += 12
            self._yaz(ic, self.y, s, kalin=(i == len(sat_g) - 1))
        if sekil:
            self.y += 8
            r = fitz.Rect(ic + 10, self.y, ic + 60, self.y + 40)
            if sekil == "daire":
                self.sayfa.draw_circle(r.tl + (25, 20), 18, color=SIYAH,
                                       fill=(0.95, 0.8, 0.3))
            elif sekil == "kare":
                self.sayfa.draw_rect(r, color=SIYAH, fill=(0.6, 0.8, 0.95))
            else:
                self.sayfa.draw_polyline([r.bl, r.tr, r.br, r.bl], color=SIYAH,
                                         fill=(0.7, 0.9, 0.6))
            self.y += 42
        self.y += 6
        harfler = "ABCDE"
        if iki_sutunlu_sik:
            for i in range(0, len(secenekler), 2):
                self.y += 14
                self._yaz(ic, self.y, f"{harfler[i]}) {secenekler[i]}")
                if i + 1 < len(secenekler):
                    self._yaz(x + gen / 2 + 10, self.y,
                              f"{harfler[i+1]}) {secenekler[i+1]}")
        else:
            for i, s in enumerate(secenekler):
                for j, parca in enumerate(self._sar(f"{harfler[i]}) {s}",
                                                    gen - 22)):
                    self.y += 14 if j == 0 else 11
                    self._yaz(ic + (12 if j else 0), self.y, parca)
        self.y += 8

    def kaydet(self, yol):
        self.doc.save(yol)
        self.doc.close()


# ----------------------------------------------------------------------------
# İçerik üretimi
# ----------------------------------------------------------------------------
def icerik_uret(yapi, sik_sayisi, tohum):
    """yapi: [(test_adi, [(ders, adet)], tek_sutun, grup_tanimlari)]
    grup_tanimlari: {ders_ici_baslangic_indeksi: grup_boyu}"""
    rng = random.Random(tohum)
    testler = []
    for t_adi, dersler, tek, gruplar in yapi:
        ders_listesi = []
        for ders, adet in dersler:
            birimler, i = [], 0      # birim = tek soru ya da metne bağlı grup
            grup_tanim = gruplar.get(ders, {})
            while i < adet:
                boy = grup_tanim.get(i, 1)
                sorular = []
                for _ in range(boy):
                    govde = " ".join(cumle(rng) for _ in range(rng.randint(1, 3)))
                    govde += " " + rng.choice([
                        "Buna göre aşağıdakilerden hangisi söylenebilir?",
                        "Bu durumun nedeni aşağıdakilerden hangisidir?",
                        "Aşağıdakilerden hangisi bu bilgiye örnek olamaz?"])
                    sik = [cumle(rng, 3, 6)[:-1] for _ in range(sik_sayisi)]
                    sekil = rng.choice([None, None, None, "daire", "kare", "ucgen"])
                    sorular.append({"govde": govde, "sik": sik,
                                    "cevap": rng.choice("ABCDE"[:sik_sayisi]),
                                    "sekil": sekil, "ders": ders})
                parca = (" ".join(cumle(rng, 10, 16) for _ in range(rng.randint(3, 5)))
                         if boy > 1 else None)
                birimler.append({"parca": parca, "sorular": sorular})
                i += boy
            ders_listesi.append((ders, birimler))
        testler.append({"ad": t_adi, "dersler": ders_listesi, "tek": tek})
    return testler


def karistir(testler, tohum):
    """B kitapçığı: her dersin içinde birimlerin (grup bütün kalır) sırası değişir."""
    rng = random.Random(tohum)
    yeni = []
    for t in testler:
        dl = []
        for ders, birimler in t["dersler"]:
            b = birimler[:]
            while True:
                rng.shuffle(b)
                if len(b) < 2 or b != birimler:
                    break
            dl.append((ders, b))
        yeni.append({**t, "dersler": dl})
    return yeni


def dizgile(testler, harf, kod, yol, cevapli=True, oynama=None,
            baslik_bicimi="ve"):
    """oynama: hatalı varyant için (test_i, no) -> değişiklik sözlüğü."""
    oynama = oynama or {}
    d = Dizgi(harf, kod, cevapli, baslik_bicimi)
    for ti, t in enumerate(testler):
        toplam = sum(len(b["sorular"]) for _d, bl in t["dersler"] for b in bl)
        d.bolum(t["ad"], toplam, tek_sutun=t["tek"])
        no = 0
        ilk = True
        for ders, birimler in t["dersler"]:
            for b in birimler:
                nolar = list(range(no + 1, no + 1 + len(b["sorular"])))
                if b["parca"]:
                    bas_nolar = oynama.get(("baslik", ti, nolar[0]), nolar)
                    parca = oynama.get(("parca", ti, nolar[0]), b["parca"])
                    d.grup_basligi(bas_nolar, parca,
                                   tam_genislik=(ilk and not t["tek"] and ti == 0))
                ilk = False
                for s in b["sorular"]:
                    no += 1
                    o = oynama.get(("soru", ti, no), {})
                    if o.get("sil"):
                        continue
                    d.soru(no, o.get("govde", s["govde"]), o.get("sik", s["sik"]),
                           o.get("cevap", s["cevap"]), sekil=o.get("sekil", s["sekil"]),
                           numara_metni=o.get("numara"))
    d.kaydet(yol)


ORTAOKUL = [
    ("SÖZEL BÖLÜM - TÜRKÇE", [("Türkçe", 20)], False,
     {"Türkçe": {0: 4, 9: 2, 14: 3}}),
    ("SÖZEL BÖLÜM - SOSYAL BİLGİLER", [("Sosyal Bilgiler", 10)], False,
     {"Sosyal Bilgiler": {4: 2}}),
    ("SAYISAL BÖLÜM - MATEMATİK", [("Matematik", 20)], False,
     {"Matematik": {12: 2}}),
    ("SAYISAL BÖLÜM - FEN BİLİMLERİ", [("Fen Bilimleri", 20)], True,
     {"Fen Bilimleri": {13: 2, 6: 2}}),
]

TYT = [
    ("TÜRKÇE TESTİ", [("Türkçe", 40)], False, {"Türkçe": {0: 2, 20: 3}}),
    ("SOSYAL BİLİMLER TESTİ", [("Tarih", 5), ("Coğrafya", 5), ("Felsefe", 5),
                               ("Din Kültürü", 5), ("Seçmeli Felsefe", 5)], False,
     {"Coğrafya": {1: 2}}),
    ("TEMEL MATEMATİK TESTİ", [("Temel Matematik", 40)], False, {}),
    ("FEN BİLİMLERİ TESTİ", [("Fizik", 7), ("Kimya", 7), ("Biyoloji", 6)], False,
     {"Kimya": {2: 2}}),
]


def numara_haritasi(testler):
    """(ti, no) -> soru içeriği kimliği (govde)."""
    h = {}
    for ti, t in enumerate(testler):
        no = 0
        for _d, bl in t["dersler"]:
            for b in bl:
                for s in b["sorular"]:
                    no += 1
                    h[(ti, no)] = s
    return h


def main(cikti):
    cikti = Path(cikti)
    cikti.mkdir(parents=True, exist_ok=True)

    a = icerik_uret(ORTAOKUL, 4, 7)
    b = karistir(a, 11)
    dizgile(a, "A", "26270704", cikti / "ortaokul_A.pdf")
    dizgile(b, "B", "26270705", cikti / "ortaokul_B.pdf")
    dizgile(b, "B", "26270705", cikti / "ortaokul_B_baski.pdf", cevapli=False)

    # Doğru eşleşme (sınama için): A no -> B no
    ha, hb = numara_haritasi(a), numara_haritasi(b)
    ters = {id(s): k for k, s in hb.items()}
    dogru = {f"{k[0]}-{k[1]}": ters[id(s)][1] for k, s in ha.items()}
    (cikti / "ortaokul_dogru_eslesme.json").write_text(json.dumps(dogru))

    # --- Hatalı B: her hata türünden bir tane --------------------------------
    hb_ = numara_haritasi(b)
    oynama, notlar = {}, []

    def b_no_bul(ti, kosul):
        for (t, n), s in sorted(hb_.items()):
            if t == ti and kosul(n, s):
                return n
        raise RuntimeError("bulunamadı")

    grup_baslari = {}
    for ti, t in enumerate(b):
        no = 0
        for _d, bl in t["dersler"]:
            for blk in bl:
                if blk["parca"]:
                    grup_baslari.setdefault(ti, []).append(
                        list(range(no + 1, no + 1 + len(blk["sorular"]))))
                no += len(blk["sorular"])

    # 1) Türkçe'de bir soru basılmamış
    n = b_no_bul(0, lambda n, s: n > 5 and not any(n in g for g in grup_baslari[0]))
    oynama[("soru", 0, n)] = {"sil": True}
    notlar.append(f"Türkçe B-{n}: soru silindi (eksik soru)")
    # 2) Grup başlığı numarası yanlış
    g = grup_baslari[0][-1]
    yanlis = [x + 2 for x in g]
    oynama[("baslik", 0, g[0])] = yanlis
    notlar.append(f"Türkçe B {g[0]}-{g[-1]} grubu: başlık {yanlis[0]}-{yanlis[-1]} yazıyor")
    # 3) Görseldeki gibi: grup içinde aynı numara iki kez (8. 8.)
    g2 = grup_baslari[2][0]
    oynama[("soru", 2, g2[1])] = {"numara": f"{g2[0]}."}
    notlar.append(f"Matematik B-{g2[1]}: '{g2[0]}.' olarak numaralanmış (mükerrer numara)")
    # 4) Metinde yazım farkı
    n4 = b_no_bul(1, lambda n, s: n == 2)
    s4 = hb_[(1, n4)]
    k4 = s4["govde"].split()
    k4[3] = k4[3] + "lar"
    oynama[("soru", 1, n4)] = {"govde": " ".join(k4)}
    notlar.append(f"Sosyal B-{n4}: gövdede bir kelime farklı")
    # 5) Cevap harfi farklı
    n5 = b_no_bul(3, lambda n, s: n == 3)
    s5 = hb_[(3, n5)]
    oynama[("soru", 3, n5)] = {"cevap": "ABCD"[("ABCD".index(s5["cevap"]) + 1) % 4]}
    notlar.append(f"Fen B-{n5}: cevap harfi farklı")
    # 6) Şık metni farklı
    n6 = b_no_bul(2, lambda n, s: n == 4)
    s6 = hb_[(2, n6)]
    sik6 = s6["sik"][:]
    sik6[3] = sik6[3] + " değildir"
    oynama[("soru", 2, n6)] = {"sik": sik6}
    notlar.append(f"Matematik B-{n6}: D şıkkı farklı")
    # 7) Şekil değişmiş (metin aynı)
    n7 = b_no_bul(2, lambda n, s: s["sekil"] in ("daire", "kare") and n > 6)
    s7 = hb_[(2, n7)]
    oynama[("soru", 2, n7)] = {"sekil": "ucgen"}
    notlar.append(f"Matematik B-{n7}: şekil farklı ({s7['sekil']} → ucgen)")
    # 8) Parça metni değişmiş
    g8 = grup_baslari[3][0]
    oynama[("parca", 3, g8[0])] = (
        "Bu parça metni B kitapçığında yanlışlıkla farklı basılmıştır. " * 4)
    notlar.append(f"Fen B {g8[0]}-{g8[-1]} grubu: parça metni farklı")
    # 9) Aynı soru iki kez basılmış (bir sorunun yerine başkası)
    tekler = [n for (t, n) in sorted(hb_) if t == 1
              and not any(n in gg for gg in grup_baslari[1])]
    n9k, n9 = tekler[-2], tekler[-1]
    s9 = hb_[(1, n9k)]
    oynama[("soru", 1, n9)] = {"govde": s9["govde"], "sik": s9["sik"],
                               "cevap": s9["cevap"], "sekil": s9["sekil"]}
    notlar.append(f"Sosyal B-{n9}: B-{n9k} ile aynı soru tekrar basılmış "
                  f"(asıl soru yok)")
    dizgile(b, "B", "26270705", cikti / "ortaokul_B_hatali.pdf", oynama=oynama)
    (cikti / "hatalar.txt").write_text("\n".join(notlar) + "\n", encoding="utf-8")

    # --- TYT çifti -------------------------------------------------------------
    ta = icerik_uret(TYT, 5, 21)
    tb = karistir(ta, 22)
    dizgile(ta, "A", "26271101", cikti / "tyt_A.pdf")
    dizgile(tb, "B", "26271102", cikti / "tyt_B.pdf")
    # "12. ve 13. soruları" biçimli başlıklar (soru numarası sanılma riski)
    dizgile(ta, "A", "26271101", cikti / "tyt_nokta_A.pdf", baslik_bicimi="nokta")
    dizgile(tb, "B", "26271102", cikti / "tyt_nokta_B.pdf", baslik_bicimi="nokta")
    ha, hb = numara_haritasi(ta), numara_haritasi(tb)
    ters = {id(s): k for k, s in hb.items()}
    dogru = {f"{k[0]}-{k[1]}": ters[id(s)][1] for k, s in ha.items()}
    (cikti / "tyt_dogru_eslesme.json").write_text(json.dumps(dogru))
    print("Üretildi:", ", ".join(sorted(p.name for p in cikti.iterdir())))
    print("\n".join(notlar))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ornek_pdfler")
