"""Yazı tanımanın düşürdüğü Türkçe harfleri geri koyar (ı, ş, ğ, ç, ö, ü, İ).

Mac'in yazı tanıması Türkçe bilmediğinde "Batı"yı "Bati", "Yağış"ı "Yagis" diye okur.
Ders kitaplarında sık geçen kelimeler (yönler, aylar, iklim, harita, geometri), 81 il ve
ülke adları bu listeyle düzeltilir. Listede olmayan kelimeye dokunulmaz.
"""
from __future__ import annotations

import json
import os

_FOLD = str.maketrans("ıİşŞğĞüÜöÖçÇâÂîÎûÛ", "iIsSgGuUoOcCaAiIuU")

_KELIMELER = """
Batı Batısı Batıda Batıya Doğu Doğusu Doğuda Doğuya Güney Güneyi Güneyde Güneye
Kuzeydoğu Kuzeybatı Güneydoğu Güneybatı Kuzeyi Kuzeyde Kuzeye yön yönü yönleri
Şubat Mayıs Ağustos Eylül Kasım Aralık Salı Çarşamba Perşembe
Kış Kışın İlkbahar mevsim mevsimi mevsimler
yıl yılı yıllar yılları yıllık aylık günlük haftalık gün günü günler gündüz
öğle öğleyin öğleden önce akşam sabahleyin süre süresi
Sıcaklık Sıcaklığı Sıcaklıklar sıcak soğuk ılık ılıman ısı ısınma soğuma
Yağış Yağışı Yağışlar Yağışlı yağmur yağış basınç basıncı rüzgâr rüzgar rüzgârı rüzgarı
yükselti yükseltisi yüksek yükseklik yüksekliği alçak düşük
kıyı kıyısı dağ dağı dağlar dağları dağlık göl gölü göller ırmak ırmağı çöl çölü çöller
örtüsü bitki örtü buzul buzulları körfez körfezi boğaz boğazı yarımada yarımadası ada adası
Bölge Bölgesi Bölgeler Bölgeleri yöre yöresi
iklim iklimi iklimler karasal muson savan tundra tayga ekvatoral okyanusal
Dünya Dünyanın Türkiye Türkiyenin Güneş Güneşin Güneşten ışın ışınlar ışınları ışık ışığı
gölge gölgesi gölgeler açı açısı açılar açıları geliş gelme doğuş batış
gündönümü gündönümünde ekinoks yarım küre Küre Kürede Yarımküre
dönence dönencesi Dönencesi Yengeç Oğlak Kutup Dairesi Başlangıç başlangıç meridyeni
aydınlanma aydınlanma çizgi çizgisi çizgiler düzlem düzlemi gökyüzü gök ufuk
harita haritası ölçek ölçeği ölçekli enlem boylam kuşak kuşağı kuşaklar
nüfus nüfusu yoğunluk yoğunluğu göç göçü şehir şehirler kır kırsal ülke ülkeler ülkesi
üretim üretimi tarım tarımı ürün ürünü ürünler ürünleri buğday arpa çay fındık üzüm
hayvancılık balıkçılık kömür doğalgaz enerji ulaşım ihracat ithalat
yüzde oranı miktarı değer değeri değerler değişim artış azalış toplam
üçgen dörtgen dikdörtgen çember çemberi daire yarıçap çap çapı kenar köşe köşesi
uzunluk uzunluğu alan alanı çevre çevresi hacim hacmi eğim eğimi doğru doğrusu
kütle kütlesi ağırlık ağırlığı kuvvet hız hızı sıvı katı buharlaşma yoğuşma erime donma kaynama
şekil Şekil Şekilde sütun sütunu sütunlar satır sayı sayısı sayılar öğrenci kişi kişiler
çok büyük küçük aşağı yukarı sağ üst iç dış orta
Okyanus Okyanusu Büyük Hint Atlas Buz Denizi Kızıldeniz Baltık Hazar
Çin Japonya Güney Afrika Mısır Fransa Almanya İngiltere İspanya İtalya Norveç İsveç
Finlandiya İzlanda İrlanda İsviçre Belçika Çekya Moğolistan Özbekistan Türkmenistan
Kırgızistan Tacikistan Bangladeş Şili Küba Grönland Birleşik Emirlikleri Çad Moritanya
Kızılırmak Yeşilırmak Fırat Göksu Meriç Çoruh Çukurova Ovası Gölü Dağı Dağları Ağrı Uludağ
Toroslar Göller Yöresi Süveyş Cebelitarık Kanalı İstanbul Boğazı Çanakkale Anadolu İç
Kıbrıs Türk Gürcistan Hırvatistan Lübnan Sırbistan Ürdün İran İsrail Yeşil Karadağ
Ağrotur Bosna Hersek Ermenistan Azerbaycan Bulgaristan Yunanistan Ukrayna Rusya Suriye Irak
""".split()


def _fold(s: str) -> str:
    return s.translate(_FOLD).lower()


def _lower(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()


def _upper(s: str) -> str:
    return s.replace("i", "İ").replace("ı", "I").upper()


def _load() -> dict:
    words = list(_KELIMELER)
    try:
        p = os.path.join(os.path.dirname(__file__), "veri", "turkiye.json")
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        for k in ("iller", "komsular"):
            for it in d.get(k, []):
                words.extend(it["ad"].replace("-", " ").split())
    except Exception:
        pass
    out = {}
    for w in words:
        if w.translate(_FOLD) == w:  # Türkçe harfi yok: düzeltilecek bir şey yok
            continue
        k = _fold(w)
        out.setdefault(k, _lower(w))
    return out


_SOZLUK: dict | None = None
_GERI = set("aıou")
_UNLU = set("aeıioöuü")


def _case_like(src: str, word: str) -> str:
    letters = [c for c in src if c.isalpha()]
    if len(letters) > 1 and all(c.isupper() for c in letters):
        return _upper(word)
    if letters and letters[0].isupper():
        return _upper(word[0]) + word[1:]
    return word


def _harmony(stem: str, suffix: str) -> str:
    """Ekteki 'i' kalın ünlüden (a, ı) sonra 'ı' olur: Batı+sinda -> Batısında."""
    last = next((c for c in reversed(_lower(stem)) if c in _UNLU), "e")
    out = []
    for c in suffix:
        if c in "iI":
            back = last in "aı"
            if c == "i":
                c = "ı" if back else "i"
            else:                   # büyük harfle yazılmış ek: NIN / NİN
                c = "I" if back else "İ"
            lc = "ı" if back else "i"
        else:
            lc = _lower(c)
        if lc in _UNLU:
            last = lc
        out.append(c)
    return "".join(out)


def _fix_core(core: str) -> str:
    global _SOZLUK
    if _SOZLUK is None:
        _SOZLUK = _load()
    k = _fold(core)
    if k in _SOZLUK:
        return _case_like(core, _SOZLUK[k])
    # ekli kelime: en uzun bilinen gövde + ek (Batısında, Sıcaklığı)
    for n in range(len(k) - 1, 3, -1):
        p, suf = k[:n], core[n:]
        stem = None
        if p in _SOZLUK:
            stem = _SOZLUK[p]
        elif p.endswith("g") and p[:-1] + "k" in _SOZLUK:
            stem = _SOZLUK[p[:-1] + "k"][:-1] + "ğ"
        if stem is not None and len(suf) <= 6:
            return _case_like(core[:n], stem) + _harmony(stem, suf)
    return core


def duzelt(word: str) -> str:
    """Tek kelimeyi düzelt; baştaki/sondaki işaretler ve kesme işaretli ek korunur."""
    if not word:
        return word
    i, j = 0, len(word)
    while i < j and not word[i].isalpha():
        i += 1
    while j > i and not word[j - 1].isalpha():
        j -= 1
    if j - i < 2:
        return word
    head, core, tail = word[:i], word[i:j], word[j:]
    for ap in ("'", "’"):
        if ap in core:
            stem, suf = core.split(ap, 1)
            stem = _fix_core(stem) if len(stem) >= 2 else stem
            return head + stem + ap + _harmony(stem, suf) + tail
    return head + _fix_core(core) + tail


_GEVSEK = None
_LOOSE = str.maketrans({"l": "i", "1": "i", "|": "i", "j": "i", "!": "i"})


def _loose(s: str) -> str:
    return _fold(s).translate(_LOOSE)


def duzelt_gevsek(word: str) -> str:
    """Yazı tanımanın ı/i/l/1 karıştırmasına dayanıklı düzeltme: "Sicakllk" -> "Sıcaklık".

    Yalnız kelimenin tamamı sözlükteki tek bir kelimeye denk gelirse değiştirir.
    """
    global _GEVSEK, _SOZLUK
    if _SOZLUK is None:
        _SOZLUK = _load()
    if _GEVSEK is None:
        g = {}
        for v in set(_SOZLUK.values()):
            g.setdefault(_loose(v), set()).add(v)
        _GEVSEK = {k: next(iter(v)) for k, v in g.items() if len(v) == 1}
    if not word:
        return word
    i, j = 0, len(word)
    while i < j and not word[i].isalnum():
        i += 1
    while j > i and not word[j - 1].isalnum():
        j -= 1
    core = word[i:j]
    hit = _GEVSEK.get(_loose(core)) if len(core) >= 3 else None
    if hit is None:
        return duzelt(word)
    return word[:i] + _case_like(core, hit) + word[j:]


def duzelt_satir(text: str) -> str:
    return " ".join(duzelt(w) for w in text.split(" "))
