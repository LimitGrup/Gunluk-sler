# -*- coding: utf-8 -*-
"""
==============================================================================
 KİTAPÇIK EŞLEŞTİRİCİ (Uygulama Sürümü) — Limit Yayınları
==============================================================================
Pencereli sürüm: A/B kitapçık PDF'lerini dosya seçiciyle seçin, EŞLEŞTİR'e
basın; kazanım tablosu Excel'i otomatik oluşsun. Terminal bilgisi gerekmez.

Çalıştırma: Kitapcik_Eslestirici.command dosyasına çift tıklayın
            (veya terminalden: python3 kitapcik_eslestirici_app.py)
==============================================================================
"""

import difflib
import importlib
import importlib.util
import os
import queue
import re
import subprocess
import sys
import threading
import traceback
import unicodedata
from pathlib import Path

SURUM = "2.18"
GEREKLI = ["pymupdf", "numpy", "scipy", "openpyxl", "tkinterdnd2",
           "python-docx"]
LOG_DOSYASI = Path.home() / "Library" / "Logs" / "KitapcikEslestirici.log"


def logla(mesaj):
    try:
        LOG_DOSYASI.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_DOSYASI, "a", encoding="utf-8") as f:
            f.write(mesaj + "\n")
    except OSError:
        pass


def hata_penceresi(mesaj):
    try:
        subprocess.run(["osascript", "-e",
                        'display dialog "' + mesaj.replace('"', "'") +
                        '" buttons {"Tamam"} default button 1 '
                        'with title "Kitapçık Eşleştirici"'], timeout=60)
    except Exception:
        pass

# ----------------------------------------------------------------------------
# SINAV YAPILARI
# ----------------------------------------------------------------------------
YAPILAR = {
    "TYT": [
        {"test": "Türkçe", "dersler": [["Türkçe", 40]]},
        {"test": "Sosyal Bilimler", "dersler": [["Tarih", 5], ["Coğrafya", 5],
                                                ["Felsefe", 5], ["Din Kültürü", 5],
                                                ["Seçmeli Felsefe", 5]]},
        {"test": "Temel Matematik", "dersler": [["Temel Matematik", 40]]},
        {"test": "Fen Bilimleri", "dersler": [["Fizik", 7], ["Kimya", 7],
                                              ["Biyoloji", 6]]},
    ],
    "AYT": [
        {"test": "Türk Dili ve Edebiyatı-Sosyal Bilimler-1",
         "dersler": [["Edebiyat", 24], ["Tarih", 10], ["Coğrafya", 6]]},
        {"test": "Sosyal Bilimler-2",
         "dersler": [["Tarih-2", 11], ["Coğrafya-2", 11], ["Felsefe Grubu", 12],
                     ["Din Kültürü", 6], ["Seçmeli Felsefe", 6]]},
        {"test": "Matematik", "dersler": [["Matematik", 40]]},
        {"test": "Fen Bilimleri", "dersler": [["Fizik", 14], ["Kimya", 13],
                                              ["Biyoloji", 13]]},
    ],
}

SORU_BASI_RE = re.compile(r"^(\d{1,3})\s*[\.\)]\s*(.*)$")
SECENEK_A_RE = re.compile(r"(?m)^\s*A\s*[\)\.]")
CEVAP_SATIRI_RE = re.compile(r"^\s*([A-E])\s+([A-Z0-9ÇĞİÖŞÜ]{5,})\s*$")
# Test başı yönerge satırları ("1. Bu testte 40 soru vardır." vb.) soru DEĞİLDİR
YONERGE_RE = re.compile(r"^(Bu\s+test|Cevaplar)", re.IGNORECASE)


def renkli_mi(renk):
    """Span rengi siyah/gri değilse True (magenta cevap işaretleri için)."""
    r, g, b = (renk >> 16) & 255, (renk >> 8) & 255, renk & 255
    return max(r, g, b) - min(r, g, b) > 60


def cevap_kodu_bul(satir, sadece_renk=False):
    """Satırdaki renkli (magenta) cevap harfi ile soru kodunu döndürür.
    Parçalara bölünmüş kodları birleştirir; sadece_renk=True ise yalnızca
    renkli span'lara bakar (soru numarası satırı için güvenli mod)."""
    cevap, kod_parcalari = None, []
    for metin, renk in satir.get("spanlar", []):
        t = metin.strip()
        if not t or not renkli_mi(renk):
            continue
        if re.fullmatch(r"[A-E]", t):
            cevap = t
        else:
            temiz = t.replace(" ", "")
            if re.fullmatch(r"[A-Za-z0-9ÇĞİÖŞÜçğıöşü]{2,}", temiz):
                kod_parcalari.append(temiz)
    kod = "".join(kod_parcalari) if kod_parcalari else None
    if kod and (len(kod) < 5 or not re.search(r"\d", kod)):
        kod = None  # rakamsız/kısa renkli metin kod değildir (vurgu vb. olabilir)
    if cevap is None and not sadece_renk:  # renk bilgisi yoksa satır deseni
        m = CEVAP_SATIRI_RE.match(satir["metin"])
        if m:
            cevap, kod = m.group(1), m.group(2)
    return cevap, kod


def bagimliliklari_yukle():
    """Ağır kütüphaneleri yükler; eksikse ImportError fırlatır."""
    global fitz, np, linear_sum_assignment
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz  # eski sürüm adı
    import numpy as np
    from scipy.optimize import linear_sum_assignment


def eksikleri_bul():
    importlib.invalidate_caches()
    return [p for p in GEREKLI if importlib.util.find_spec({"pymupdf": "fitz", "python-docx": "docx"}.get(p, p)) is None
        and not (p == "pymupdf" and importlib.util.find_spec("fitz"))]


def normalize(s):
    s = unicodedata.normalize("NFC", s).casefold()
    return re.sub(r"[^a-zçğıöşü0-9]+", "", s)


# Deneme ders adı <-> ana sözlük ders adı eşlemesi (özel durumlar dahil)
_DERS_ESLEME_EK = {
    "felsefegrubu": ["felsefe", "psikoloji", "sosyoloji", "mantık"],
    "edebiyat": ["edebiyat", "türk dili ve edebiyatı"],
}


def _ders_uyusur(yapi_ders, sozluk_ders):
    a = normalize(re.sub(r"-\d+$", "", str(yapi_ders)))
    b = normalize(str(sozluk_ders))
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    for hedef in _DERS_ESLEME_EK.get(a, []):
        if normalize(hedef) in b or b in normalize(hedef):
            return True
    return False


# ----------------------------------------------------------------------------
# MOTOR (PDF okuma → soru ayıklama → eşleştirme → Excel)
# ----------------------------------------------------------------------------
def satirlari_al(pdf_yolu):
    doc = fitz.open(pdf_yolu)
    satirlar = []
    kolonlar = {0: [1e9, 0], 1: [1e9, 0]}
    for pno, page in enumerate(doc):
        d = page.get_text("dict")
        orta = page.rect.width / 2
        sol, sag = [], []
        for blk in d.get("blocks", []):
            if blk.get("type", 0) != 0:
                continue
            for ln in blk.get("lines", []):
                spanlar = [(sp.get("text", ""), sp.get("color", 0))
                           for sp in ln.get("spans", [])]
                metin = "".join(t for t, _ in spanlar).strip()
                if not metin:
                    continue
                x0, y0, x1, y1 = ln["bbox"]
                sutun = 0 if (x0 + x1) / 2 < orta else 1
                kayit = {"metin": metin, "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                         "sayfa": pno, "sutun": sutun, "spanlar": spanlar}
                (sol if sutun == 0 else sag).append(kayit)
                kolonlar[sutun][0] = min(kolonlar[sutun][0], x0)
                kolonlar[sutun][1] = max(kolonlar[sutun][1], x1)
        for sutun in (sol, sag):
            sutun.sort(key=lambda r: (round(r["y0"], 1), r["x0"]))
        satirlar.extend(sol)
        satirlar.extend(sag)
    doc.close()
    if not satirlar:
        raise RuntimeError(f"'{Path(pdf_yolu).name}' içinden metin okunamadı. "
                           f"Taranmış/görsel PDF ise önce OCR gerekir.")
    return satirlar, kolonlar



def yapi_cikar(a_pdf):
    """Yapıyı A kitapçığının kendisinden türetir: numaraların 1'e döndüğü
    yerler test bloklarını, blok üstündeki başlık satırı test adını verir."""
    satirlar, _kolonlar = satirlari_al(a_pdf)
    adaylar, _yedek = _adaylari_bul(satirlar)
    if not adaylar:
        raise RuntimeError("A kitapçığında soru numarası bulunamadı; yapı "
                           "çıkarılamadı.")
    bloklar = []
    bas_idx, en_buyuk = None, 0
    for p, (i, no) in enumerate(adaylar):
        yeni = (no == 1 and (bas_idx is None or en_buyuk >= 3)
                and any(a[1] == 2 for a in adaylar[p + 1:p + 4]))
        if yeni:
            if bas_idx is not None:
                bloklar.append((bas_idx, en_buyuk))
            bas_idx, en_buyuk = i, 1
        elif bas_idx is not None:
            en_buyuk = max(en_buyuk, no)
    if bas_idx is not None:
        bloklar.append((bas_idx, en_buyuk))
    if not bloklar:
        raise RuntimeError("A kitapçığında test bloğu bulunamadı.")

    def blok_bilgisi(bas_satir, sira, adet, onceki_bas):
        test_adi, dersler, yonerge_adet = None, None, None
        for k in range(bas_satir - 1, max(-1, bas_satir - 10), -1):
            m = re.sub(r"[\x00-\x1f]+", " ", satirlar[k]["metin"]).strip()
            if not m:
                continue
            if test_adi is None:
                eb = re.search(r"BÖLÜM\s*[-–—]\s*(.{2,30})$", m)
                if eb:
                    test_adi = eb.group(1).strip()
            if test_adi is None:
                e = re.search(r"cevap kâğıdının\s+(.+?)\s+Testi",
                              m, re.IGNORECASE)
                if e:
                    test_adi = e.group(1).strip()
                else:
                    e2 = re.match(r"^(.+?)\s+TESTİNE GEÇİNİZ", m)
                    if e2:
                        test_adi = e2.group(1).strip()
            if yonerge_adet is None and "Bu testte" in m:
                ya = re.search(r"Bu testte[^0-9]*(\d+)\s*soru", m)
                if ya:
                    yonerge_adet = int(ya.group(1))
            if dersler is None and "Bu testte" in m:
                bul = re.findall(
                    r"([A-Za-zÇĞİÖŞÜçğıöşü][\w ÇĞİÖŞÜçğıöşü.\-]*?)"
                    r"\s*\((\d+)\s*[-–]\s*(\d+)\)", m)
                cift = [(re.sub(r"^(ve|ile)\s+", "",
                                ad.strip(" ,.")), int(b2) - int(b1) + 1)
                        for ad, b1, b2 in bul]
                if cift and sum(a for _n, a in cift) == adet:
                    dersler = [[n, a] for n, a in cift]
        if test_adi is None:      # daha geriye, bir önceki bloğa kadar bak
            for k in range(bas_satir - 1, max(onceki_bas - 1, -1), -1):
                mm = re.sub(r"[\x00-\x1f]+", " ", satirlar[k]["metin"]).strip()
                e3 = re.match(r"^(.+?)\s+TEST[İI]NE GEÇ[İI]N[İI]Z", mm)
                if e3:
                    test_adi = e3.group(1).strip()
                    break
                eb2 = re.search(r"BÖLÜM\s*[-–—]\s*(.{2,30})$", mm)
                if eb2:
                    test_adi = eb2.group(1).strip()
                    break
                if mm == "TEST ADI":
                    for kk3 in range(k + 1, min(k + 4, len(satirlar))):
                        ad3 = satirlar[kk3]["metin"].strip()
                        if ad3 and ad3 not in ("SORU SAYISI", "SINIFI",
                                               "ADI", "SOYADI"):
                            test_adi = ad3
                            break
                    if test_adi:
                        break
        if test_adi is None:
            for k in range(bas_satir - 1, max(-1, bas_satir - 7), -1):
                m = satirlar[k]["metin"].strip()
                if not m or SORU_BASI_RE.match(m) or "Bu test" in m:
                    continue
                if any(len(t) >= 8 and t.isupper()
                       and any(c.isdigit() for c in t) for t in m.split()):
                    continue
                if not any(len(t) >= 4 and t.isalpha() for t in m.split()):
                    continue
                buyukce = sum(1 for ch in m if ch.isalpha() and ch == ch.upper())
                harf = sum(1 for ch in m if ch.isalpha())
                if harf >= 4 and ("TEST" in m.upper()
                                  or (harf and buyukce / harf > 0.8)):
                    test_adi = m[:40]
                    break
        if test_adi is None:
            test_adi = f"Bölüm {sira}"
        if yonerge_adet and yonerge_adet > adet:
            adet = yonerge_adet          # yönergedeki sayı esas alınır
        if not dersler:
            dersler = [[test_adi, int(adet)]]
        return {"test": test_adi, "dersler": dersler}

    yapi = []
    for s, (bas_satir, adet) in enumerate(bloklar, 1):
        onceki = bloklar[s - 2][0] if s >= 2 else 0
        yapi.append(blok_bilgisi(bas_satir, s, int(adet), onceki))
    return yapi


def beklenen_dizi(yapi):
    dizi = []
    for ti, test in enumerate(yapi):
        n = 0
        for ders, adet in test["dersler"]:
            for _ in range(int(adet)):
                n += 1
                dizi.append((ti, ders, n))
    return dizi


def _adaylari_bul(satirlar):
    ham = []
    for i, r in enumerate(satirlar):
        m = SORU_BASI_RE.match(r["metin"])
        if not m or not (1 <= int(m.group(1)) <= 60):
            continue
        kalan = m.group(2)
        if YONERGE_RE.match(kalan):
            continue                      # "1. Bu testte ..." aynı satırda
        if re.match(r"^S[Iİı]N[Iİı]F\b", kalan, re.IGNORECASE) and \
                re.search(r"DENEME|OKUL|FINAL|TEST|YAYIN",
                          r["metin"], re.IGNORECASE):
            continue                      # "6. SINIF FINAL ..." koşan başlığı
        if not kalan.strip() and i + 1 < len(satirlar) \
                and YONERGE_RE.match(satirlar[i + 1]["metin"]):
            continue                      # "1." ayrı satır, yönerge metni altında
        ham.append((i, int(m.group(1)), r["sutun"], r["x0"]))

    # Kenar hizası filtresi: gerçek soru numaraları sütunun sol kenarına dizilir;
    # soru İÇİNDEKİ numaralı maddeler (öncüller) içeriden başlar ve elenir.
    from collections import Counter as _Sayac
    kenar = {}
    for _i, _no, _sutun, _x0 in ham:
        kenar.setdefault(_sutun, _Sayac())[round(_x0)] += 1
    kenar = {s: c.most_common(1)[0][0] for s, c in kenar.items()}
    adaylar, yedekler = [], []
    kenarlar = list(kenar.values())
    for i, no, sutun, x0 in ham:
        uyan = abs(x0 - kenar.get(sutun, x0)) <= 6
        if not uyan:
            genis = (satirlar[i].get("x1", x0) - x0) > 250  # tam genişlik satırı
            uyan = genis and min((abs(x0 - m) for m in kenarlar),
                                 default=99) <= 6
        if uyan:
            adaylar.append((i, no))
        else:
            yedekler.append((i, no))
    return adaylar, yedekler


def sorulari_ayikla(pdf_yolu, yapi, etiket, log):
    satirlar, kolonlar = satirlari_al(pdf_yolu)
    adaylar, yedekler = _adaylari_bul(satirlar)

    beklenen = beklenen_dizi(yapi)
    # Deterministik hizalama: beklenen numaralar sırayla yürünür; blok
    # karışması imkânsızdır. Aday uymazsa ya gürültüdür (yakında doğrusu
    # geliyorsa atlanır) ya da o soru gerçekten eksiktir.
    eslesen = {}
    p = i = 0
    while i < len(adaylar) and p < len(beklenen):
        if adaylar[i][1] == beklenen[p][2]:
            eslesen[p] = adaylar[i][0]
            i += 1
            p += 1
        elif any(adaylar[j][1] == beklenen[p][2]
                 for j in range(i + 1, min(i + 4, len(adaylar)))):
            i += 1      # gürültü aday: beklenen numara hemen arkasından geliyor
        else:
            p += 1      # bu beklenen soru adaylar arasında yok (eksik)

    # --- Kurtarma 1: sırası kaymış (çapraz kolona dizilmiş) soruları kazan ---
    kullanilan = set(eslesen.values())
    for bek_i in range(len(beklenen)):
        if bek_i in eslesen:
            continue
        ti_b, _d, no_b = beklenen[bek_i]
        komsular = [eslesen[b] for b in eslesen
                    if beklenen[b][0] == ti_b and abs(b - bek_i) <= 4]
        if not komsular:
            continue
        alt, ust = min(komsular), max(komsular)
        bulundu = False
        for sat_i, aday_no in adaylar:
            if (aday_no == no_b and sat_i not in kullanilan
                    and alt <= sat_i <= ust):
                eslesen[bek_i] = sat_i
                kullanilan.add(sat_i)
                bulundu = True
                break
        if not bulundu:          # blok-geneli arama: önce asıl, sonra yedek
            test_satirlari = [eslesen[b] for b in eslesen
                              if beklenen[b][0] == ti_b]
            sonraki_bas = min([eslesen[b] for b in eslesen
                               if beklenen[b][0] > ti_b] or [len(satirlar)])
            g_alt = min(test_satirlari) if test_satirlari else 0
            for kaynak in (adaylar, yedekler):
                for sat_i, aday_no in kaynak:
                    if (aday_no == no_b and sat_i not in kullanilan
                            and g_alt <= sat_i < sonraki_bas):
                        eslesen[bek_i] = sat_i
                        kullanilan.add(sat_i)
                        bulundu = True
                        break
                if bulundu:
                    break

    # --- Kurtarma 2: şıksız (sahte) çapaları aynı numaralı gerçek satıra taşı ---
    def _secenekli(bas, son):
        return any(re.match(r"^\s*A\s*[\)\.]", satirlar[k]["metin"])
                   for k in range(bas, min(son, len(satirlar))))

    for _tur in range(3):
        degisti = False
        baslar = sorted(eslesen.values())
        for bek_i, sat_i in list(eslesen.items()):
            son = next((b for b in baslar if b > sat_i), len(satirlar))
            if _secenekli(sat_i, son):
                continue
            ti_b, _d, no_b = beklenen[bek_i]
            ayni_test = [eslesen[b] for b in eslesen if beklenen[b][0] == ti_b]
            sinir = max(ayni_test) if ayni_test else len(satirlar)
            for aday_sat, aday_no in adaylar:
                if (aday_no != no_b or aday_sat in kullanilan
                        or aday_sat <= sat_i or aday_sat > sinir):
                    continue
                son2 = next((b for b in baslar if b > aday_sat), len(satirlar))
                if _secenekli(aday_sat, son2):
                    kullanilan.discard(sat_i)
                    kullanilan.add(aday_sat)
                    eslesen[bek_i] = aday_sat
                    degisti = True
                    break
        if not degisti:
            break

    sorular, uyarilar = {}, []
    sirali = sorted(eslesen.items())
    tum_baslar = sorted(eslesen.values())
    for bek_i, sat_i in sirali:
        ti, ders, no = beklenen[bek_i]
        son = next((b for b in tum_baslar if b > sat_i), len(satirlar))
        bolum = satirlar[sat_i:son]
        ilk_secenek = next((i for i, r in enumerate(bolum)
                            if re.match(r"^\s*A\s*[\)\.]", r["metin"])), len(bolum))
        cevap = kod = None
        atla = set()
        c0, k0 = cevap_kodu_bul(bolum[0], sadece_renk=True)
        if c0 or k0:
            cevap, kod = c0, k0
        for i in range(1, ilk_secenek):  # cevap işareti seçeneklerden önce durur
            c, k = cevap_kodu_bul(bolum[i])
            if c or k:
                atla.add(i)
                cevap = cevap or c
                kod = kod or k
        parcalar = []
        for i, r in enumerate(bolum):
            if i in atla:
                continue
            if i == 0:
                ham = ("".join(t for t, rk in r["spanlar"]
                               if not renkli_mi(rk)).strip()
                       if (c0 or k0) else r["metin"])
                m0 = SORU_BASI_RE.match(ham)
                parcalar.append(m0.group(2) if m0 else ham)
            else:
                parcalar.append(r["metin"])
        metin = "\n".join(parcalar)
        m = SECENEK_A_RE.search(metin)
        govde = metin[:m.start()] if m else metin
        bas = bolum[0]
        ayni = [r for r in bolum
                if r["sayfa"] == bas["sayfa"] and r["sutun"] == bas["sutun"]]
        e_idx = next((i for i, r in enumerate(ayni)
                      if re.match(r"^\s*E\s*[\)\.]", r["metin"])), None)
        if e_idx is None:
            kesit = ayni
        else:
            kesit = ayni[:e_idx + 1]
            adimlar = [ayni[j + 1]["y0"] - ayni[j]["y0"]
                       for j in range(max(0, e_idx - 4), e_idx)]
            adimlar = [d for d in adimlar if d > 0]
            tipik = sorted(adimlar)[len(adimlar) // 2] if adimlar else 14
            son_y0 = ayni[e_idx]["y0"]
            j = e_idx + 1
            while j < len(ayni) and (ayni[j]["y0"] - son_y0) < 1.8 * tipik:
                kesit.append(ayni[j])       # E şıkkının devam satırları
                son_y0 = ayni[j]["y0"]
                j += 1
        ks = kolonlar.get(bas["sutun"])
        if ks and ks[0] < ks[1]:
            gx0, gx1 = ks[0] - 2, ks[1] + 2
        else:
            gx0 = min(r["x0"] for r in ayni) - 2
            gx1 = max(r["x1"] for r in ayni) + 2
        bolge = (bas["sayfa"], gx0, bas["y0"] - 3, gx1,
                 max(r["y1"] for r in kesit) + 3)
        sorular[(ti, no)] = {"ders": ders, "no": no, "cevap": cevap, "kod": kod,
                             "bolge": bolge, "tam": metin,
                             "govde": govde.strip(), "norm": normalize(metin)}
    for bek_i, (ti, ders, no) in enumerate(beklenen):
        if bek_i not in eslesen:
            uyarilar.append(f"{etiket} kitapçığı: {yapi[ti]['test']} / {ders} "
                            f"{no}. soru PDF'te bulunamadı.")

    # Erken uyarı teli: magenta kodları numaralardan BAĞIMSIZ say ve karşılaştır.
    # Henüz görülmemiş dizgi desenleri bile bu sayımda kendini ele verir.
    kod_sayim = {}
    for r in satirlar:
        _c, _k = cevap_kodu_bul(r, sadece_renk=True)
        if _k:
            mt = re.search(r"T(\d{1,2})S\d{1,3}$", _k)
            if mt:
                t_i = int(mt.group(1)) - 1
                kod_sayim[t_i] = kod_sayim.get(t_i, 0) + 1
    bulunan_test = {}
    for (ti2, _no2) in sorular:
        bulunan_test[ti2] = bulunan_test.get(ti2, 0) + 1
    for ti2 in sorted(kod_sayim):
        if 0 <= ti2 < len(yapi) and kod_sayim[ti2] > bulunan_test.get(ti2, 0):
            uyarilar.append(
                f"{etiket} kitapçığı: {yapi[ti2]['test']} bölümünde "
                f"{kod_sayim[ti2]} soru kodu sayıldı ama "
                f"{bulunan_test.get(ti2, 0)} soru bulundu — yeni bir dizgi "
                f"deseni olabilir; log dosyasını iletin.")
    if uyarilar:
        # Tanı dökümü: sorun bölgesinde parser'ın tam olarak ne gördüğü
        logla(f"--- TANI ({etiket} kitapçığı, {Path(pdf_yolu).name}) ---")
        logla("Aday numara dizisi: " + " ".join(str(n) for _, n in adaylar))
        eksikler = [bp for bp in range(len(beklenen)) if bp not in eslesen]
        onceki = max((bp for bp in eslesen if bp < eksikler[0]), default=None)
        bas = eslesen[onceki] if onceki is not None else 0
        logla("İlk eksik bölge çevresindeki ham satırlar:")
        for k in range(bas, min(bas + 30, len(satirlar))):
            logla(f"  [{k}] {satirlar[k]['metin'][:70]}")
    log(f"  {etiket} kitapçığı: {len(sorular)} soru bulundu.")
    return sorular, uyarilar


def eslestir(a_sorular, b_sorular, yapi, esik=0.60):
    """Önce magenta soru kodlarıyla birebir eşler; kod yoksa/konumsal ise
    şıklar dahil tam metin benzerliğiyle Macar algoritmasına düşer."""
    from collections import Counter
    sonuc, uyarilar = {}, []

    def benzerlik(sa, sb):
        if sa["norm"] and sb["norm"]:
            return difflib.SequenceMatcher(None, sa["norm"], sb["norm"]).ratio()
        return 0.0

    for ti, test in enumerate(yapi):
        n = 0
        for ders, adet in test["dersler"]:
            aralik = list(range(n + 1, n + int(adet) + 1))
            n += int(adet)
            ga = [(no, a_sorular[(ti, no)]) for no in aralik if (ti, no) in a_sorular]
            gb = [(no, b_sorular[(ti, no)]) for no in aralik if (ti, no) in b_sorular]
            if not ga or not gb:
                continue

            # --- 1) Soru kodu tabanlı eşleme (kod her iki tarafta da tekilse) ---
            ka = Counter(s["kod"] for _, s in ga if s.get("kod"))
            kb = Counter(s["kod"] for _, s in gb if s.get("kod"))
            a_by = {s["kod"]: (no, s) for no, s in ga
                    if s.get("kod") and ka[s["kod"]] == 1}
            b_by = {s["kod"]: (no, s) for no, s in gb
                    if s.get("kod") and kb[s["kod"]] == 1}
            ortak = set(a_by) & set(b_by)
            kod_es = {}
            if ortak:
                kullan = True
                ayni_yerde = all(a_by[k][0] == b_by[k][0] for k in ortak)
                if ayni_yerde and len(ortak) > 1:
                    # Kodlar konumsal (kitapçığa göre yeniden numaralı) olabilir;
                    # aynı konumdaki metinler gerçekten benziyorsa güvenilir say.
                    ort = sum(benzerlik(a_by[k][1], b_by[k][1])
                              for k in ortak) / len(ortak)
                    kullan = ort >= 0.75
                if kullan:
                    for k in ortak:
                        a_no, sa = a_by[k]
                        b_no, sb = b_by[k]
                        kod_es[a_no] = b_no
                        sonuc[(ti, a_no)] = {"b_no": b_no,
                                             "benzerlik": benzerlik(sa, sb),
                                             "yontem": "KOD"}

            # --- 2) Kalanlar için tam metin benzerliğiyle en iyi birebir atama ---
            kalan_a = [(no, s) for no, s in ga if no not in kod_es]
            alinan_b = set(kod_es.values())
            kalan_b = [(no, s) for no, s in gb if no not in alinan_b]
            if kalan_a and kalan_b:
                M = np.zeros((len(kalan_a), len(kalan_b)))
                for i, (_, sa) in enumerate(kalan_a):
                    for j, (_, sb) in enumerate(kalan_b):
                        s_ = benzerlik(sa, sb)
                        ca_, cb_ = sa.get("cevap"), sb.get("cevap")
                        if ca_ and cb_:
                            if ca_ == cb_:      # magenta cevaplar uyuşuyor
                                s_ = min(1.0, s_ + 0.25)
                            else:               # farklı cevap: güçlü ceza
                                s_ *= 0.35
                        M[i, j] = s_
                sat, sut = linear_sum_assignment(1 - M)
                for i, j in zip(sat, sut):
                    a_no, b_no, oran = kalan_a[i][0], kalan_b[j][0], M[i, j]
                    sonuc[(ti, a_no)] = {"b_no": b_no, "benzerlik": oran,
                                         "yontem": "METİN"}
                    if oran < esik:
                        uyarilar.append(
                            f"DÜŞÜK BENZERLİK: {test['test']} / {ders} A-{a_no} → "
                            f"B-{b_no} (%{oran*100:.0f}).")
    return sonuc, uyarilar


# ----------------------------------------------------------------------------
# GÖRSEL DOĞRULAMA: her eşleşen çift sayfa görüntüsü olarak üst üste bindirilir
# ----------------------------------------------------------------------------
def _kupur(doc, bolge, onbellek, anahtar, genislik=180, azami_yukseklik=300):
    """Sorunun sayfadaki bölgesini küçük gri tonlamalı görüntü olarak keser."""
    if anahtar in onbellek:
        return onbellek[anahtar]
    sayfa_no, x0, y0, x1, y1 = bolge
    y1 = min(y1, y0 + azami_yukseklik)
    sayfa = doc[sayfa_no]
    r = fitz.Rect(x0, y0, x1, y1) & sayfa.rect
    sonuc = None
    if not r.is_empty and r.width >= 20 and r.height >= 20:
        olcek = genislik / r.width
        pix = sayfa.get_pixmap(clip=r, matrix=fitz.Matrix(olcek, olcek),
                               colorspace=fitz.csGRAY, alpha=False)
        a = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width).astype(np.float32)
        if a.shape[0] > 4 and a.shape[1] > 4:  # 3x3 yumuşatma (kayma toleransı)
            b = a.copy()
            b[1:-1, 1:-1] = (a[:-2, :-2] + a[:-2, 1:-1] + a[:-2, 2:] +
                             a[1:-1, :-2] + a[1:-1, 1:-1] + a[1:-1, 2:] +
                             a[2:, :-2] + a[2:, 1:-1] + a[2:, 2:]) / 9.0
            a = b
        sonuc = a
    onbellek[anahtar] = sonuc
    return sonuc


def _gorsel_benzerlik(a, b):
    """İki soru görüntüsünün üst üste bindirme puanı; küçük kaymaları ve
    kitapçıklar arası satır aralığı (leading) farkını tolere eder."""
    if a is None or b is None:
        return None
    ha, hb = a.shape[0], b.shape[0]
    h = min(ha, hb)
    w = min(a.shape[1], b.shape[1])
    if h < 16 or w < 16:
        return None
    oran = h / max(ha, hb)

    def esitle(x):
        # Satır aralığı kısılmış kitapçık için dikey yeniden örnekleme
        if x.shape[0] == h:
            return x[:, :w]
        idx = np.round(np.linspace(0, x.shape[0] - 1, h)).astype(int)
        return x[idx][:, :w]

    if oran >= 0.7:          # makul sıkıştırma: ölçek eşitle
        a2, b2 = esitle(a), esitle(b)
    else:                    # çok farklı yükseklik: üstten ortak kesit
        a2, b2 = a[:h, :w], b[:h, :w]

    en_iyi = None
    for dy in range(-2, 3):
        for dx in (-1, 0, 1):
            aa = a2[max(0, dy):, max(0, dx):]
            bb = b2[max(0, -dy):, max(0, -dx):]
            hh = min(aa.shape[0], bb.shape[0])
            ww = min(aa.shape[1], bb.shape[1])
            if hh < 16 or ww < 16:
                continue
            x, y = aa[:hh, :ww].ravel(), bb[:hh, :ww].ravel()
            if x.std() < 1 or y.std() < 1:
                continue
            r = float(np.corrcoef(x, y)[0, 1])
            en_iyi = r if en_iyi is None else max(en_iyi, r)
    if en_iyi is None:
        return None
    return max(0.0, min(1.0, en_iyi * (0.85 + 0.15 * oran)))


def gorsel_dogrula(a_pdf, b_pdf, a_sorular, b_sorular, eslesme, yapi, log,
                   esik=0.78, cevap_a=None, cevap_b=None, onar=False):
    """Tüm çiftleri görüntü olarak karşılaştırıp raporlar. Varsayılan olarak
    SALT DOĞRULAMA yapar: eşleşmeleri asla değiştirmez, yalnızca şüpheli
    çiftleri işaretler. (onar=True yalnızca test amaçlıdır.)"""
    from collections import defaultdict
    cevap_a, cevap_b = cevap_a or {}, cevap_b or {}
    uyarilar, puanlar = [], {}
    docA, docB = fitz.open(a_pdf), fitz.open(b_pdf)
    onbellek = {}

    def puan(ak, bk):
        ka = _kupur(docA, a_sorular[ak]["bolge"], onbellek, ("A",) + ak)
        kb = _kupur(docB, b_sorular[bk]["bolge"], onbellek, ("B",) + bk)
        return _gorsel_benzerlik(ka, kb)

    for anahtar, es in eslesme.items():
        if (anahtar[0], es["b_no"]) in b_sorular:
            puanlar[anahtar] = puan(anahtar, (anahtar[0], es["b_no"]))

    # (Yalnızca onar=True iken) zayıf METİN çiftlerini görselle yeniden ata
    gruplar = defaultdict(list)
    if onar:
        for k, p in puanlar.items():
            es = eslesme[k]
            if es.get("yontem") != "METİN":
                continue
            ca_ = cevap_a.get(k, "")
            cb_ = cevap_b.get((k[0], es["b_no"]), "")
            celiski = bool(ca_ and cb_ and ca_ != cb_)
            if p is None or p < esik or celiski:
                gruplar[(k[0], a_sorular[k]["ders"])].append(k[1])
    for (ti, ders), a_lar in gruplar.items():
        b_ler = [eslesme[(ti, a)]["b_no"] for a in a_lar]
        if len(a_lar) < 2:
            continue
        M = np.zeros((len(a_lar), len(b_ler)))
        for i, a in enumerate(a_lar):
            for j, b in enumerate(b_ler):
                p = puan((ti, a), (ti, b))
                M[i, j] = p if p is not None else 0.0
        sat, sut = linear_sum_assignment(1 - M)
        for i, j in zip(sat, sut):
            a, b = a_lar[i], b_ler[j]
            if eslesme[(ti, a)]["b_no"] != b:
                eslesme[(ti, a)] = {"b_no": b,
                                    "benzerlik": eslesme[(ti, a)]["benzerlik"],
                                    "yontem": "GÖRSEL"}
                log(f"  ↺ Görsel doğrulama düzeltti: {ders} A-{a} → B-{b}")
            puanlar[(ti, a)] = M[i, j]

    # METİN çiftleri için çapraz kıyas: görsel olarak daha benzer aday var mı?
    ders_b = defaultdict(list)
    for (ti2, b_no2), s in b_sorular.items():
        ders_b[(ti2, s["ders"])].append(b_no2)
    for k, es in list(eslesme.items()):
        if es.get("yontem") != "METİN":
            continue
        p_mevcut = puanlar.get(k)
        taban = p_mevcut if p_mevcut is not None else (esik - 0.05)
        en_iyi_b, en_iyi_p = es["b_no"], taban
        for b in ders_b.get((k[0], a_sorular[k]["ders"]), []):
            if b == es["b_no"]:
                continue
            p2 = puan(k, (k[0], b))
            if p2 is not None and p2 > en_iyi_p + 0.05:
                en_iyi_b, en_iyi_p = b, p2
        if en_iyi_b != es["b_no"]:
            uyarilar.append(
                f"GÖRSEL KONTROL: {a_sorular[k]['ders']} A-{k[1]} şu an "
                f"B-{es['b_no']} ile eşli (görsel %{(p_mevcut or 0)*100:.0f}); "
                f"B-{en_iyi_b} görsel olarak daha benzer (%{en_iyi_p*100:.0f}). "
                f"Elle doğrulayın.")

    tam = 0
    for k in sorted(puanlar):
        p = puanlar[k]
        if p is None:
            continue
        if p >= esik:
            tam += 1
        else:
            es = eslesme[k]
            uyarilar.append(f"GÖRSEL KONTROL: {a_sorular[k]['ders']} A-{k[1]} → "
                            f"B-{es['b_no']} görsel örtüşme %{p*100:.0f} — "
                            f"elle doğrulayın.")
    docA.close()
    docB.close()
    log(f"Görsel doğrulama: {tam}/{len(puanlar)} çift birebir örtüştü.")
    return puanlar, uyarilar


def anahtar_oku(yol, yapi):
    if not yol:
        return {}
    metin = Path(yol).read_text(encoding="utf-8", errors="ignore")
    parcalar = re.split(r"\[([^\]]+)\]", metin)
    cevaplar = {}
    test_adlari = [normalize(t["test"]) for t in yapi]
    for k in range(1, len(parcalar), 2):
        na, ti = normalize(parcalar[k]), None
        for i, t in enumerate(test_adlari):
            if na and (na in t or t in na):
                ti = i
                break
        if ti is None:
            continue
        icerik = parcalar[k + 1]
        ciftler = re.findall(r"(\d{1,3})\s*[-\.\):]?\s*([A-Ea-e])\b", icerik)
        if ciftler:
            for no, harf in ciftler:
                cevaplar[(ti, int(no))] = harf.upper()
        else:
            for no, harf in enumerate(re.findall(r"[A-Ea-e]", icerik), 1):
                cevaplar[(ti, no)] = harf.upper()
    return cevaplar


def _konular_kaynagi(yol):
    """Şablon dosyasından Konular satırlarını okur.
    Dönen: (satirlar, tur)  tur: 'sablon' (Konular sayfası var, dokunma),
    'liste' (yalın kazanım listesi) ya da (None, None)."""
    import openpyxl
    u = str(yol).lower()
    if u.endswith(".csv"):
        import csv
        for kodlama in ("utf-8-sig", "utf-8", "cp1254"):
            try:
                with open(yol, encoding=kodlama, newline="") as f:
                    satirlar = [row for row in csv.reader(f)]
                if satirlar:
                    return satirlar, "liste"
            except UnicodeDecodeError:
                continue
        return None, None
    if u.endswith(".docx"):
        try:
            import docx
        except Exception:
            return None, ("hata: Word şablonu için 'python-docx' kütüphanesi "
                          "kurulamadı. Terminale şunu yapıştırın: "
                          "python3 -m pip install --user python-docx")
        belge = docx.Document(yol)
        satirlar = []
        for tablo in belge.tables:
            for row in tablo.rows:
                hucreler = [h.text.strip() for h in row.cells]
                if any(hucreler):
                    satirlar.append(hucreler)
        if not satirlar:                    # tablo yoksa sekmeli paragraflar
            for p in belge.paragraphs:
                m = p.text.strip()
                if m:
                    satirlar.append(re.split(r"\t+|\s{2,}", m))
        return (satirlar, "liste") if satirlar else (None, None)
    if u.endswith(".pdf"):
        doc = fitz.open(yol)
        satirlar = []
        for sayfa in doc:
            try:                            # önce çizgili tabloları dene
                for tablo in sayfa.find_tables():
                    for row in tablo.extract():
                        hucreler = [str(h).strip() if h is not None else ""
                                    for h in row]
                        if any(hucreler):
                            satirlar.append(hucreler)
            except Exception:
                pass
        if not satirlar:            # çizgisiz: sütunları koordinattan ayır
            for sayfa in doc:
                gruplar = {}
                for x0, y0, x1, y1, w, *_k in sayfa.get_text("words"):
                    anahtar = round((y0 + y1) / 6)
                    gruplar.setdefault(anahtar, []).append((x0, x1, w))
                for _y in sorted(gruplar):
                    parcalar = sorted(gruplar[_y])
                    hucreler, aktif, son_x1 = [], "", None
                    for x0, x1, w in parcalar:
                        if son_x1 is not None and x0 - son_x1 > 6:
                            hucreler.append(aktif)
                            aktif = w
                        else:
                            aktif = (aktif + " " + w).strip()
                        son_x1 = x1
                    if aktif:
                        hucreler.append(aktif)
                    if any(hucreler):
                        satirlar.append(hucreler)
        doc.close()
        return (satirlar, "liste") if satirlar else (None, None)
    wb = openpyxl.load_workbook(yol, data_only=True)
    if "Konular" in wb.sheetnames:
        return None, "sablon"          # şablonun kendi Konular'ı aynen taşınır
    ws = wb.worksheets[0]
    satirlar = [list(r) for r in ws.iter_rows(values_only=True)
                if r and any(c not in (None, "") for c in r)]
    return (satirlar, "liste") if satirlar else (None, None)


def excel_yaz(sablon, sayfa_adi, yapi, eslesme, a_sorular,
              cevap_a, cevap_b, uyarilar):
    sablon_verildi = bool(sablon)
    import openpyxl
    from openpyxl.styles import Font
    BASLIKLAR = ["DersAdi", "Kitapcik", "SoruNo", "Cevap",
                 "B Kitapçığındaki Soru", "K12 Kodu", "Konu Adı",
                 "Çözüm Link", "Çift Soru Var mı?"]
    liste_satirlari = None
    if sablon:
        _s, _tur = _konular_kaynagi(sablon)
        if _tur == "liste":
            liste_satirlari = _s
            sablon = None              # yalın liste: taze tabanda ilerle
        elif isinstance(_tur, str) and _tur.startswith("hata"):
            uyarilar.append(_tur.split(":", 1)[1].strip())
            sablon = None
            sablon_verildi = False
    if sablon:
        wb = openpyxl.load_workbook(sablon)
        ws = wb[sayfa_adi] if sayfa_adi in wb.sheetnames else wb.create_sheet(sayfa_adi)
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sayfa_adi
        kws = wb.create_sheet("Konular")
        if liste_satirlari:
            for satir_ in liste_satirlari:   # yüklenen dosya birebir işlenir
                kws.append(list(satir_))
        else:
            kws.append(["K12 Kodu", "Ders", "Sınıf", "Ünite", "Konu",
                        "Alt Kazanım"])
    for c, b in enumerate(BASLIKLAR, 1):
        h = ws.cell(row=1, column=c, value=b)
        h.font = Font(name="Tahoma", bold=True)

    farklar, r = [], 2
    for ti, test in enumerate(yapi):
        n = 0
        for ders, adet in test["dersler"]:
            for _ in range(int(adet)):
                n += 1
                es = eslesme.get((ti, n), {})
                b_no = es.get("b_no", "")
                ca = cevap_a.get((ti, n), "")
                cb = cevap_b.get((ti, b_no), "") if b_no != "" else ""
                if ca and cb and ca != cb:
                    farklar.append(f"CEVAP UYUŞMAZLIĞI: {test['test']} "
                                   f"A-{n} ({ca}) ↔ B-{b_no} ({cb}).")
                ws.cell(row=r, column=1, value=ders)
                ws.cell(row=r, column=2, value="A")
                ws.cell(row=r, column=3, value=n)
                ws.cell(row=r, column=4, value=ca)
                ws.cell(row=r, column=5, value=b_no)
                ws.cell(row=r, column=6, value=None)
                ws.cell(row=r, column=7,
                        value=f'=IF(F{r}="","",VLOOKUP(F{r},Konular!A:F,5,0))')
                ws.cell(row=r, column=8, value=None)
                ws.cell(row=r, column=9, value=f"=CONCATENATE(A{r},E{r})")
                r += 1
    for eski in range(r, ws.max_row + 1):
        for c in range(1, 10):
            ws.cell(row=eski, column=c, value=None)

    if "Kontrol" in wb.sheetnames:
        del wb["Kontrol"]
    kw = wb.create_sheet("Kontrol")
    kw.append(["Test", "Ders", "A Soru", "B Soru", "Benzerlik %", "Yöntem",
               "A Cevap", "B Cevap", "Soru Kodu (A)", "Durum"])
    for ti, test in enumerate(yapi):
        n = 0
        for ders, adet in test["dersler"]:
            for _ in range(int(adet)):
                n += 1
                es = eslesme.get((ti, n))
                ca_ = cevap_a.get((ti, n), "")
                kod = (a_sorular.get((ti, n)) or {}).get("kod") or ""
                if es:
                    yuzde = round(es["benzerlik"] * 100, 1)
                    yontem = es.get("yontem", "METİN")
                    cb_ = cevap_b.get((ti, es["b_no"]), "")
                    if ca_ and cb_ and ca_ != cb_:
                        durum = "CEVAP FARKLI"
                    elif yontem == "METİN" and yuzde < 60:
                        durum = "KONTROL ET"
                    else:
                        durum = "OK"
                    kw.append([test["test"], ders, n, es["b_no"], yuzde, yontem,
                               ca_, cb_, kod, durum])
                else:
                    kw.append([test["test"], ders, n, "", "", "",
                               ca_, "", kod, "EŞLEŞMEDİ"])
    _kn = wb["Konular"] if "Konular" in wb.sheetnames else None
    if sablon_verildi and (_kn is None or not any(
            any(c not in (None, "") for c in r_)
            for r_ in _kn.iter_rows(min_row=2, values_only=True))):
        uyarilar.append("Konular sekmesi boş kaldı — yüklenen kazanım "
                        "dosyasını kontrol edin.")
    kw.append([])
    kw.append(["UYARILAR"])
    for u in uyarilar + farklar:
        kw.append([u])
    return wb, farklar


def calistir(a_pdf, b_pdf, sinav, sablon, anah_a, anah_b, cikti, log,
             yol_sor=None):
    log(f"Motor sürümü: {SURUM}")
    if sinav in ("OTOMATİK", "ORTAOKUL"):
        log("Yapı A kitapçığından çıkarılıyor...")
        yapi = yapi_cikar(a_pdf)
        log("  Bulunan yapı: " + " | ".join(
            f"{t['test']} ({t['dersler'][0][1]} soru)" for t in yapi))
    else:
        yapi = YAPILAR[sinav]
    log("A kitapçığı okunuyor...")
    a_s, u1 = sorulari_ayikla(a_pdf, yapi, "A", log)
    log("B kitapçığı okunuyor...")
    b_s, u2 = sorulari_ayikla(b_pdf, yapi, "B", log)

    # Kitapçık doğrulaması: soru içermeyen dosya (ör. cevap anahtarı) seçildiyse
    # kullanıcıyı bekletmeden, dosya adıyla açıkça söyle
    def _kitapcik_dogrula(ad, sorular, yol):
        if not sorular:
            raise RuntimeError(
                f"'{Path(yol).name}' içinde hiç soru bulunamadı. Bu dosya bir "
                f"deneme kitapçığı değil gibi görünüyor (örneğin cevap "
                f"anahtarı / 'CA' belgesi seçilmiş olabilir). {ad} Kitapçığı "
                f"alanına soruların olduğu kitapçık PDF'ini seçin.")
    _kitapcik_dogrula("A", a_s, a_pdf)
    _kitapcik_dogrula("B", b_s, b_pdf)

    # Yapı doğrulaması: seçilen tür dosyaya uymuyorsa doğru yapıyı kendisi bulur
    if sinav not in ("OTOMATİK", "ORTAOKUL") and len(u1) + len(u2) > 5:
        for aday_sinav, aday_yapi in YAPILAR.items():
            if aday_sinav == sinav:
                continue
            log(f"Seçilen '{sinav}' yapısına {len(u1)+len(u2)} soru uymadı; "
                f"'{aday_sinav}' yapısı deneniyor...")
            a2, v1 = sorulari_ayikla(a_pdf, aday_yapi, "A", log)
            b2, v2 = sorulari_ayikla(b_pdf, aday_yapi, "B", log)
            if len(v1) + len(v2) < len(u1) + len(u2):
                log(f"⚠ DİKKAT: Dosyalar '{aday_sinav}' düzeninde; sınav türü "
                    f"otomatik '{aday_sinav}' olarak düzeltildi.")
                sinav, yapi = aday_sinav, aday_yapi
                a_s, b_s, u1, u2 = a2, b2, v1, v2
                break
    log("Sorular eşleştiriliyor...")
    esl, u3 = eslestir(a_s, b_s, yapi)
    pdf_a = {k: s["cevap"] for k, s in a_s.items() if s.get("cevap")}
    pdf_b = {k: s["cevap"] for k, s in b_s.items() if s.get("cevap")}
    log(f"PDF içinden okunan renkli cevaplar: A kitapçığı {len(pdf_a)}/{len(a_s)}, "
        f"B kitapçığı {len(pdf_b)}/{len(b_s)}")
    ca = {**pdf_a, **anahtar_oku(anah_a, yapi)}
    cb = {**pdf_b, **anahtar_oku(anah_b, yapi)}
    uyarilar = u1 + u2 + u3
    if a_s and not pdf_a and not anah_a:
        uyarilar.append("A kitapçığında renkli cevap işareti bulunamadı; "
                        "Cevap sütunu boş kalacak.")
    beklenen_toplam = sum(int(a) for t_ in yapi for _d, a in t_["dersler"])
    if a_s and len(a_s) < beklenen_toplam * 0.5:
        log("")
        log("⚠⚠ DİKKAT: A kitapçığında beklenenin çok altında soru bulundu "
            f"({len(a_s)}/{beklenen_toplam}). Seçtiğiniz dosya soru kitapçığı "
            "olmayabilir — örneğin '- CA' ile biten CEVAP ANAHTARI dosyası "
            "seçilmiş olabilir. A satırından 'DENEME A' kitapçığını seçip "
            "tekrar deneyin.")
        log("")
    wb, farklar = excel_yaz(sablon, sinav, yapi, esl, a_s, ca, cb, uyarilar)

    hedef = cikti
    while True:
        try:
            wb.save(hedef)
            break
        except OSError as h:
            log(f"\n⚠ '{hedef}' konumuna yazılamadı ({h}).")
            log("  macOS gizlilik koruması: Masaüstü/Belgeler gibi klasörlere yazmak")
            log("  için konumun kayıt penceresinden seçilmesi gerekir.")
            yeni = yol_sor(hedef) if yol_sor else None
            if not yeni:
                raise RuntimeError("Kayıt tamamlanamadı. Çıktı konumunu penceredeki "
                                   "Seç... düğmesiyle belirleyip tekrar deneyin.") from h
            hedef = yeni

    log(f"\n✓ Tablo yazıldı: {hedef}")
    log(f"  Eşleşen soru: {len(esl)}  |  Uyarı: {len(uyarilar) + len(farklar)}")
    for u in uyarilar + farklar:
        log("  ⚠ " + u)
    if not (uyarilar or farklar):
        log("  Tüm eşleşmeler eşik üstünde, uyarı yok.")
    return hedef


# ----------------------------------------------------------------------------
# ARAYÜZ (tkinter)
# ----------------------------------------------------------------------------
def gui_baslat():
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk

    # --- eksik kütüphane kontrolü ve otomatik kurulum (görünür pencereyle) ---
    eksik = eksikleri_bul()
    if eksik:
        kok = tk.Tk()
        kok.title("Kitapçık Eşleştirici")
        kok.geometry("400x110")
        kok.attributes("-topmost", True)
        durum = tk.Label(kok, text="Başlatılıyor...", pady=20)
        durum.pack(fill="both", expand=True)
        kok.update()
        if messagebox.askyesno("Kurulum gerekli",
                               "Şu kütüphaneler eksik:\n  " + ", ".join(eksik) +
                               "\n\nŞimdi otomatik kurulsun mu? (internet gerekir)",
                               parent=kok):
            durum.configure(text="Kütüphaneler kuruluyor...\n"
                                 "Bu birkaç dakika sürebilir, pencereyi kapatmayın.")
            kok.update()
            komut = [sys.executable, "-m", "pip", "install", "--user"] + eksik
            p = subprocess.run(komut, capture_output=True, text=True)
            if p.returncode != 0:
                p = subprocess.run(komut + ["--break-system-packages"],
                                   capture_output=True, text=True)
            logla("pip kurulum çıktısı:\n" + (p.stdout or "") + (p.stderr or ""))
            importlib.invalidate_caches()
            try:
                import site
                site.addsitedir(site.getusersitepackages())
            except Exception:
                pass
            kalan = eksikleri_bul()
            istege_bagli = {"tkinterdnd2", "python-docx"}
            kritik = [p for p in kalan if p not in istege_bagli]
            if kalan and not kritik:
                logla(f"İsteğe bağlı kurulamayan: {kalan} — uygulama tam "
                      f"çalışır (ilgili özellik kapalı kalır).")
            if kritik:
                messagebox.showerror(
                    "Kurulamadı",
                    "Otomatik kurulum başarısız oldu.\nTerminale şunu yapıştırın:\n\n"
                    f"python3 -m pip install --user {' '.join(eksik)}\n\n"
                    "Sonra uygulamayı yeniden açın.\n\nHata:\n" + p.stderr[-400:],
                    parent=kok)
                kok.destroy()
                return
            messagebox.showinfo("Tamam", "Kurulum bitti, uygulama açılıyor.",
                                parent=kok)
        else:
            kok.destroy()
            return
        kok.destroy()
    try:
        bagimliliklari_yukle()
    except ImportError as h:
        if "incompatible architecture" not in str(h):
            raise
        # Paketler yanlış işlemci mimarisiyle kurulmuş (Intel/Apple karışması)
        kok = tk.Tk()
        kok.withdraw()
        onar = messagebox.askyesno(
            "Onarım gerekli",
            "Kütüphaneler bu bilgisayarın işlemcisine uymayan biçimde "
            "kurulmuş görünüyor (Intel/Apple Silicon karışması).\n\n"
            "Şimdi otomatik onarılsın mı? Birkaç dakika sürebilir "
            "(internet gerekir).", parent=kok)
        kok.destroy()
        hata_ozeti = ""
        if onar:
            r = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user",
                 "--force-reinstall", "--no-cache-dir",
                 "pymupdf", "numpy", "scipy"],
                capture_output=True, text=True, timeout=1800)
            logla("Mimari onarım pip çıktısı:\n"
                  + (r.stdout or "")[-600:] + (r.stderr or "")[-600:])
            importlib.invalidate_caches()
            # Doğrulama TEMİZ bir süreçte yapılır (bu oturumun hafızası kirli)
            dogrulama = subprocess.run(
                [sys.executable, "-c", "import pymupdf; print('ONARIM_OK')"],
                capture_output=True, text=True, timeout=120)
            if "ONARIM_OK" in (dogrulama.stdout or ""):
                kok = tk.Tk()
                kok.withdraw()
                messagebox.showinfo(
                    "Onarım tamam",
                    "Kütüphaneler onarıldı. Uygulama şimdi kendini yeniden "
                    "başlatacak.", parent=kok)
                kok.destroy()
                subprocess.Popen([sys.executable,
                                  str(Path(__file__).resolve())])
                return
            hata_ozeti = ((r.stderr or "") + "\n"
                          + (dogrulama.stderr or "")).strip()[-500:]
        logla("Onarım doğrulanamadı.\n" + hata_ozeti)
        kok = tk.Tk()
        kok.withdraw()
        messagebox.showerror(
            "Onarım tamamlanamadı",
            "Şu komutu Terminale yapıştırıp çalıştırın, bitince uygulamayı "
            "yeniden açın:\n\n"
            f"{sys.executable} -m pip install --user --force-reinstall "
            f"--no-cache-dir pymupdf numpy scipy"
            + (f"\n\nHata özeti:\n{hata_ozeti}" if hata_ozeti else ""),
            parent=kok)
        kok.destroy()
        return

    # Sürükle-bırak desteği (kurulamazsa/çalışmazsa normal pencereyle devam edilir)
    dnd = None
    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD
        pencere = TkinterDnD.Tk()
        dnd = DND_FILES
    except Exception as h:
        logla(f"Sürükle-bırak devre dışı: {h}")
        try:
            tk._default_root = None   # yarım kalan pencere varsayılan olmasın
        except Exception:
            pass
        pencere = tk.Tk()
    pencere.title(f"Kitapçık Eşleştirici v{SURUM} — Limit Yayınları")
    pencere.geometry("780x720")
    pencere.minsize(720, 600)

    sinav = tk.StringVar(master=pencere, value="TYT")
    yollar = {ad: tk.StringVar(master=pencere) for ad in
              ("a", "b", "sablon", "anah_a", "anah_b", "cikti")}

    def sec(ad, tur, kaydet=False):
        if kaydet:
            yol = filedialog.asksaveasfilename(
                defaultextension=".xlsx", initialfile="kazanim_tablosu.xlsx",
                filetypes=[("Excel", "*.xlsx")])
        else:
            yol = filedialog.askopenfilename(filetypes=tur)
        if yol:
            yollar[ad].set(yol)
            if ad == "a" and not yollar["cikti"].get():
                yollar["cikti"].set(str(Path(yol).with_name("kazanim_tablosu.xlsx")))

    ana = ttk.Frame(pencere, padding=14)
    ana.pack(fill="both", expand=True)

    ust = ttk.Frame(ana)
    ust.pack(fill="x", pady=(0, 8))
    ttk.Label(ust, text="Sınav türü:").pack(side="left")
    ttk.Radiobutton(ust, text="TYT", variable=sinav,
                    value="TYT").pack(side="left", padx=6)
    ttk.Radiobutton(ust, text="AYT", variable=sinav,
                    value="AYT").pack(side="left")
    ttk.Radiobutton(ust, text="Lise 9-11", variable=sinav,
                    value="OTOMATİK").pack(side="left", padx=6)
    ttk.Radiobutton(ust, text="Ortaokul 5-8", variable=sinav,
                    value="ORTAOKUL").pack(side="left")

    girisler = {}

    def satir(etiket, ad, tur, kaydet=False):
        cerceve = ttk.Frame(ana)
        cerceve.pack(fill="x", pady=3)
        ttk.Label(cerceve, text=etiket, width=26).pack(side="left")
        giris = ttk.Entry(cerceve, textvariable=yollar[ad])
        giris.pack(side="left", fill="x", expand=True, padx=(0, 6))
        girisler[ad] = giris
        ttk.Button(cerceve, text="Seç...",
                   command=lambda: sec(ad, tur, kaydet)).pack(side="left")

    HEPSI = ("Tüm Dosyalar", "*")
    PDF = [("PDF", "*.pdf"), HEPSI]
    XLSX = [("Kazanım dosyası", "*.xlsx *.xlsm *.csv *.docx *.pdf"),
            ("Excel", "*.xlsx"), HEPSI]
    TXT = [("Metin", "*.txt"), HEPSI]
    satir("A Kitapçığı PDF (zorunlu):", "a", PDF)
    satir("B Kitapçığı PDF (zorunlu):", "b", PDF)
    satir("Kazanım şablonu Excel:", "sablon", XLSX)
    satir("Cevap anahtarı A (txt):", "anah_a", TXT)
    satir("Cevap anahtarı B (txt):", "anah_b", TXT)

    satir("Çıktı Excel dosyası:", "cikti", XLSX, kaydet=True)

    def ciktiyi_doldur(a_yolu):
        if not yollar["cikti"].get():
            yollar["cikti"].set(str(Path(a_yolu).with_name("kazanim_tablosu.xlsx")))

    if dnd:
        def yollari_ayikla(veri):
            try:
                return [str(p) for p in pencere.tk.splitlist(veri)]
            except Exception:
                return [veri.strip("{}").strip()] if veri else []

        def alana_birak(ad):
            def isleyici(olay):
                dosyalar = yollari_ayikla(olay.data)
                if dosyalar:
                    yollar[ad].set(dosyalar[0])
                    if ad == "a":
                        ciktiyi_doldur(dosyalar[0])
                return getattr(olay, "action", None)
            return isleyici

        def pencereye_birak(olay):
            for yol in sorted(yollari_ayikla(olay.data)):
                u = yol.lower()
                if u.endswith(".pdf"):
                    hedef = "a" if not yollar["a"].get() else "b"
                elif u.endswith((".xlsx", ".xlsm", ".csv", ".docx")):
                    hedef = "sablon"
                elif u.endswith(".txt"):
                    hedef = "anah_a" if not yollar["anah_a"].get() else "anah_b"
                else:
                    continue
                yollar[hedef].set(yol)
                if hedef == "a":
                    ciktiyi_doldur(yol)
            return getattr(olay, "action", None)

        try:
            pencere.drop_target_register(dnd)
            pencere.dnd_bind("<<Drop>>", pencereye_birak)
            for ad_, giris_ in girisler.items():
                giris_.drop_target_register(dnd)
                giris_.dnd_bind("<<Drop>>", alana_birak(ad_))
            ttk.Label(ana, text="İpucu: dosyaları ilgili kutunun üzerine ya da "
                                "pencerenin boş bir yerine sürükleyip bırakabilirsiniz "
                                "(A ve B PDF'lerini birlikte bırakın, ikisi de dolar).",
                      foreground="#666666").pack(anchor="w", pady=(4, 0))
        except Exception as h:
            logla(f"Sürükle-bırak kaydı yapılamadı: {h}")
    if not dnd:
        ttk.Label(ana, text="Not: Sürükle-bırak bu bilgisayarda kullanılamıyor; "
                            "dosyaları Seç... düğmeleriyle ekleyin (tam işlevlidir).",
                  foreground="#8a6d00").pack(anchor="w", pady=(4, 0))

    buton = ttk.Button(ana, text="EŞLEŞTİR",
                       command=lambda: calistir_tikla())
    buton.pack(side="bottom", pady=(6, 2), ipadx=30, ipady=6)

    log_kutusu = scrolledtext.ScrolledText(ana, height=16, state="disabled",
                                           font=("Menlo", 11))
    log_kutusu.pack(fill="both", expand=True, pady=(10, 8))
    kuyruk = queue.Queue()
    kayit_kuyrugu = queue.Queue()

    def log(msg):
        kuyruk.put(str(msg))

    def yol_sor(varsayilan):
        kuyruk.put(("KAYIT", varsayilan))
        return kayit_kuyrugu.get()

    def kuyrugu_isle():
        while not kuyruk.empty():
            oge = kuyruk.get()
            if isinstance(oge, tuple) and oge and oge[0] == "BITTI":
                bitti(oge[1])
                continue
            if isinstance(oge, tuple) and oge and oge[0] == "KAYIT":
                messagebox.showinfo(
                    "Kayıt izni gerekli",
                    "macOS, çıktı klasörüne doğrudan yazmaya izin vermedi.\n"
                    "Şimdi açılacak pencerede kayıt konumunu seçin — seçtiğiniz "
                    "konuma yazma izni verilmiş olur.", parent=pencere)
                yol = filedialog.asksaveasfilename(
                    parent=pencere, defaultextension=".xlsx",
                    initialdir=os.path.dirname(oge[1]) or str(Path.home()),
                    initialfile=os.path.basename(oge[1]),
                    filetypes=[("Excel", "*.xlsx")])
                kayit_kuyrugu.put(yol or "")
                continue
            log_kutusu.configure(state="normal")
            log_kutusu.insert("end", str(oge) + "\n")
            log_kutusu.see("end")
            log_kutusu.configure(state="disabled")
        pencere.after(150, kuyrugu_isle)

    def bitti(cikti_yolu):
        buton.configure(state="normal")
        if cikti_yolu and messagebox.askyesno(
                "Tamamlandı", "Tablo hazır.\nExcel dosyası şimdi açılsın mı?",
                parent=pencere):
            subprocess.run(["open", cikti_yolu])

    def calistir_tikla():
        a, b = yollar["a"].get().strip(), yollar["b"].get().strip()
        if not a or not b:
            messagebox.showwarning("Eksik", "A ve B kitapçık PDF'lerini seçin.",
                                   parent=pencere)
            return
        cikti = yollar["cikti"].get().strip() or str(
            Path(a).with_name("kazanim_tablosu.xlsx"))
        buton.configure(state="disabled")
        log_kutusu.configure(state="normal")
        log_kutusu.delete("1.0", "end")
        log_kutusu.configure(state="disabled")

        def is_parcasi():
            try:
                yol = calistir(a, b, sinav.get(),
                               yollar["sablon"].get().strip() or None,
                               yollar["anah_a"].get().strip() or None,
                               yollar["anah_b"].get().strip() or None,
                               cikti, log, yol_sor=yol_sor)
                kuyruk.put(("BITTI", yol))
            except Exception as h:
                log(f"\nHATA: {h}")
                kuyruk.put(("BITTI", None))

        threading.Thread(target=is_parcasi, daemon=True).start()

    pencere.lift()
    pencere.attributes("-topmost", True)
    pencere.after(900, lambda: pencere.attributes("-topmost", False))
    pencere.focus_force()

    kuyrugu_isle()
    pencere.mainloop()


if __name__ == "__main__":
    try:
        logla(f"--- Uygulama başlatılıyor --- Python {sys.version.split()[0]} ---")
        gui_baslat()
    except Exception:
        detay = traceback.format_exc()
        logla("BAŞLATMA HATASI:\n" + detay)
        print(detay)
        hata_penceresi("Uygulama başlatılırken bir hata oluştu. Ayrıntı şu dosyaya "
                       "kaydedildi: Library/Logs/KitapcikEslestirici.log")
