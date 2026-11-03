# -*- coding: utf-8 -*-
"""
Soru metninin ilk satırında üst üste kesir (315/2) varsa satırın üst kenarı soru
numarasının üstüne taşar. Bu satır bir önceki soruya yazılmamalı.

B kitapçığında her sorunun ilk satırı numaranın 5 pt üstünden başlar (kesirli
satırın üst kenarı gibi; A'da numarayla aynı hizada):
  - kesir_B:       metin A ile aynı → beklenen 0 sorun
  - kesir_B_hatali: ayrıca bir sorunun İLK satırında bir kelime değişik →
                    beklenen tam olarak o soruda "Metin farklı"

Kullanım:  python3 kesir_sina.py <app.py> <cikti_klasoru>
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


def main(app, cikti):
    cikti = Path(cikti)
    cikti.mkdir(parents=True, exist_ok=True)
    g = yukle("ornek_pdf_uret", Path(__file__).with_name("ornek_pdf_uret.py"))
    ayar = {"kesir": False, "degis": None}
    asil_yaz = g.Dizgi._yaz

    def _yaz(self, x, y, metin, boy=9, kalin=False, renk=g.SIYAH):
        if re.fullmatch(r"'?\d+\.'?", metin) and kalin:
            self._numara = (x, y, metin)          # soru numarası
        elif (ayar["kesir"] and getattr(self, "_numara", None)
              and y == self._numara[1] and x > self._numara[0] + 5
              and renk == g.SIYAH):
            # ilk satır numaranın 5 pt üstünden başlar
            if ayar["degis"] and ayar["degis"][0] == self._numara[2]:
                metin = metin.replace(ayar["degis"][1], ayar["degis"][2], 1)
            self._numara = None
            return asil_yaz(self, x, y - 5, metin, boy=boy, kalin=kalin, renk=renk)
        return asil_yaz(self, x, y, metin, boy=boy, kalin=kalin, renk=renk)

    g.Dizgi._yaz = _yaz
    a = g.icerik_uret(g.ORTAOKUL, 4, 7)
    b = g.karistir(a, 11)
    g.dizgile(a, "A", "26270704", cikti / "kesir_A.pdf", cevapli=False)
    ayar["kesir"] = True
    g.dizgile(b, "B", "26270705", cikti / "kesir_B.pdf", cevapli=False)
    # B'nin 3. sorusunun (Türkçe) ilk satırındaki ilk kelimeyi değiştir
    ilk = b[0]["dersler"][0][1]
    s3 = [s for blk in ilk for s in blk["sorular"]][2]
    kelime = s3["govde"].split()[0]
    ayar["degis"] = ("3.", kelime, kelime + "lar")
    g.dizgile(b, "B", "26270705", cikti / "kesir_B_hatali.pdf", cevapli=False)

    m = yukle("kitapcik_app", app)
    m.bagimliliklari_yukle()
    a_pdf = str(cikti / "kesir_A.pdf")
    yapi = m.yapi_cikar(a_pdf)
    for ad, beklenen in (("kesir_B", 0), ("kesir_B_hatali", 1)):
        sonuc, sorunlar = m.kontrol_et(a_pdf, str(cikti / f"{ad}.pdf"), yapi,
                                       lambda _x: None)
        es = sonuc["eslesmeler"]
        print(f"{ad}: {len(sorunlar)} sorun (beklenen {beklenen}) | birebir "
              f"{sum(1 for e in es if not e[6])}/{len(es)}")
        for s in sorunlar:
            print(f"   {s['onem']} {s['soru']}: {s['aciklama'][:110]}")
        if ad == "kesir_B_hatali":
            yakalandi = any("B-3" in s["soru"] and kelime in s["aciklama"]
                            for s in sorunlar)
            print("   değiştirilen ilk satır kelimesi yakalandı mı:", yakalandi)


if __name__ == "__main__":
    main(*sys.argv[1:3])
