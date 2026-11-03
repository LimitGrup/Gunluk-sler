# -*- coding: utf-8 -*-
"""
EŞLEŞTİR akışının gerilemesini sınar: uygulamanın motorunu (arayüzsüz)
örnek PDF'lerle çalıştırır, Excel çıktısını JSON'a döker ve doğru eşleşme
dosyasıyla karşılaştırır.

Kullanım:  python3 eslestir_sina.py <app.py> <pdf_klasoru> <cikti.json>
"""
import importlib.util
import json
import sys
from pathlib import Path


def motoru_yukle(yol):
    spec = importlib.util.spec_from_file_location("kitapcik_app", yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.bagimliliklari_yukle()
    return m


def excel_dok(yol):
    import openpyxl
    wb = openpyxl.load_workbook(yol)
    return {ws.title: [list(r) for r in ws.iter_rows(values_only=True)]
            for ws in wb.worksheets}


def main(app, klasor, cikti_json):
    m = motoru_yukle(app)
    klasor = Path(klasor)
    sonuc = {}
    for ad, sinav, a, b, dogru in [
        ("ortaokul", "ORTAOKUL", "ortaokul_A.pdf", "ortaokul_B.pdf",
         "ortaokul_dogru_eslesme.json"),
        ("ortaokul_baski", "ORTAOKUL", "ortaokul_A.pdf", "ortaokul_B_baski.pdf",
         "ortaokul_dogru_eslesme.json"),
        ("tyt", "TYT", "tyt_A.pdf", "tyt_B.pdf", "tyt_dogru_eslesme.json"),
        ("tyt_nokta", "TYT", "tyt_nokta_A.pdf", "tyt_nokta_B.pdf",
         "tyt_dogru_eslesme.json"),
    ]:
        out = klasor / f"_{ad}_tablo.xlsx"
        loglar = []
        m.calistir(str(klasor / a), str(klasor / b), sinav, None, None, None,
                   str(out), loglar.append)
        dokum = excel_dok(out)
        dogru_h = json.loads((klasor / dogru).read_text())
        ana = dokum[sinav]
        # Ana sayfadaki satırlardan (test sırası korunarak) A no -> B no
        ti, onceki, hata, toplam = -1, None, 0, 0
        for satir in ana[1:]:
            if satir[2] is None:
                continue
            if satir[2] == 1 or (onceki is not None and satir[2] < onceki):
                ti += 1
            onceki = satir[2]
            beklenen = dogru_h.get(f"{ti}-{satir[2]}")
            toplam += 1
            if beklenen != satir[4]:
                hata += 1
        print(f"{ad}: {toplam - hata}/{toplam} doğru eşleşme")
        sonuc[ad] = {"excel": dokum, "dogru": toplam - hata, "toplam": toplam,
                     "log": [l for l in loglar if "Motor sürümü" not in l
                             and "Tablo yazıldı" not in l]}
    Path(cikti_json).write_text(json.dumps(sonuc, ensure_ascii=False, indent=1,
                                           default=str), encoding="utf-8")


if __name__ == "__main__":
    main(*sys.argv[1:4])
