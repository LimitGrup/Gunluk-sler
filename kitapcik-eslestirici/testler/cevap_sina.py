# -*- coding: utf-8 -*-
"""
EŞLEŞTİR'in ana tablosu cevaplı örnek kitapçıklarda doğru mu: her A sorusu için
"Cevap" sütunundaki harf ve "B Kitapçığındaki Soru" numarası, örnek üreticinin
bildiği gerçek değerle karşılaştırılır.

Kullanım:  python3 cevap_sina.py <app.py> <ornek_pdf_klasoru>
(klasör ornek_pdf_uret.py ile üretilmiş olmalı)
"""
import importlib.util
import sys
from pathlib import Path

import openpyxl


def yukle(ad, yol):
    spec = importlib.util.spec_from_file_location(ad, yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main(app, klasor):
    k = Path(klasor)
    g = yukle("ornek_pdf_uret", Path(__file__).with_name("ornek_pdf_uret.py"))
    m = yukle("kitapcik_app", app)
    m.bagimliliklari_yukle()
    # ornek_pdf_uret.main ile aynı içerik ve karıştırma tohumları
    for ad, yapi, sinav, sik, t_a, t_b in (("ortaokul", g.ORTAOKUL, "ORTAOKUL", 4, 7, 11),
                                           ("tyt", g.TYT, "TYT", 5, 21, 22)):
        a = g.icerik_uret(yapi, sik, t_a)
        b = g.karistir(a, t_b)
        ha, hb = g.numara_haritasi(a), g.numara_haritasi(b)
        b_no = {id(s): key[1] for key, s in hb.items()}
        cikti = k / f"_{ad}_cevap_sina.xlsx"
        m.calistir(str(k / f"{ad}_A.pdf"), str(k / f"{ad}_B.pdf"), sinav, None, None,
                   None, str(cikti), lambda _x: None)
        satirlar = [r for r in list(openpyxl.load_workbook(cikti)[sinav].iter_rows(
            values_only=True))[1:] if r[2] is not None]
        cevap_ok = no_ok = 0
        yanlis = []
        for ((ti, no), s), r in zip(sorted(ha.items()), satirlar):
            cevap_ok += r[3] == s["cevap"]
            no_ok += r[4] == b_no[id(s)]
            if r[3] != s["cevap"] or r[4] != b_no[id(s)]:
                yanlis.append((ti, no, r[3], s["cevap"], r[4], b_no[id(s)]))
        print(f"{ad}: cevap {cevap_ok}/{len(ha)}, B numarası {no_ok}/{len(ha)} doğru"
              + (f"  YANLIŞ (test, no, okunan cevap, doğru, okunan B, doğru): {yanlis[:5]}"
                 if yanlis else ""))


if __name__ == "__main__":
    main(*sys.argv[1:3])
