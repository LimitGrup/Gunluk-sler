# -*- coding: utf-8 -*-
"""
A–B KONTROL akışını örnek PDF'lerle sınar.
  - Temiz çiftlerde (A ile doğru karıştırılmış B) hiç HATA çıkmamalı.
  - Hatalı B'de hatalar.txt'deki her bilinçli hata yakalanmalı.

Kullanım:  python3 kontrol_sina.py <app.py> <pdf_klasoru>
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


def calistir(m, klasor, ad, sinav, a, b, dogru=None, ayrinti=False):
    loglar = []
    cikti = klasor / f"_{ad}_kontrol.xlsx"
    yapi = m.YAPILAR.get(sinav) or m.yapi_cikar(str(klasor / a))
    yapi_b = None if sinav in m.YAPILAR else m.yapi_cikar(str(klasor / b))
    sonuc, sorunlar = m.kontrol_et(str(klasor / a), str(klasor / b), yapi,
                                   loglar.append, yapi_b=yapi_b)
    m.kontrol_raporu_yaz(sonuc, sorunlar, str(cikti))
    m.kontrol_pdf_isaretle(sonuc, sorunlar, klasor)
    hata = [s for s in sorunlar if s["onem"] == "HATA"]
    uyari = [s for s in sorunlar if s["onem"] == "UYARI"]
    es = sonuc["eslesmeler"]
    print(f"\n=== {ad}: {len(hata)} HATA, {len(uyari)} UYARI | eşleşen "
          f"{sum(1 for e in es if e[0]['no'])}/{sonuc['numara']['A'][1]}, "
          f"birebir {sum(1 for e in es if not e[6])}/{len(es)}, gruplar "
          f"{sum(1 for g in sonuc['gruplar'] if not g[7])}/{len(sonuc['gruplar'])}")
    if dogru:
        beklenen = (json.loads((klasor / dogru).read_text()) if dogru != "kimlik"
                    else None)
        yanlis = []
        for e in es:
            oa, ob = e[0], e[1]
            b_bek = beklenen[f"{oa['ti']}-{oa['no']}"] if beklenen else oa["no"]
            if b_bek != ob["no"]:
                yanlis.append((oa["ti"], oa["no"], ob["no"], b_bek))
        print(f"  eşleşme doğruluğu: {len(es) - len(yanlis)}/{len(es)}"
              + (f"  YANLIŞ: {yanlis}" if yanlis else ""))
    if ayrinti or hata or uyari:
        for s in hata + uyari:
            print(f"  {s['onem']:5} [{s['kitapcik']}] {s['test']} | {s['soru']} | "
                  f"{s['aciklama'][:150]}")
    return sonuc, sorunlar


def main(app, klasor):
    m = motoru_yukle(app)
    klasor = Path(klasor)
    temiz_hata = 0
    for ad, sinav, a, b, dogru in [
        ("ortaokul", "ORTAOKUL", "ortaokul_A.pdf", "ortaokul_B.pdf",
         "ortaokul_dogru_eslesme.json"),
        ("ortaokul_baski", "ORTAOKUL", "ortaokul_A.pdf", "ortaokul_B_baski.pdf",
         "ortaokul_dogru_eslesme.json"),
        ("tyt", "TYT", "tyt_A.pdf", "tyt_B.pdf", "tyt_dogru_eslesme.json"),
        ("tyt_nokta", "TYT", "tyt_nokta_A.pdf", "tyt_nokta_B.pdf",
         "tyt_dogru_eslesme.json"),
        ("ayni_dosya", "ORTAOKUL", "ortaokul_A.pdf", "ortaokul_A.pdf", "kimlik"),
    ]:
        _s, sorunlar = calistir(m, klasor, ad, sinav, a, b, dogru)
        temiz_hata += sum(1 for s in sorunlar if s["onem"] == "HATA")
    _s, sorunlar = calistir(m, klasor, "hatali", "ORTAOKUL", "ortaokul_A.pdf",
                            "ortaokul_B_hatali.pdf")
    print("\nBilinçli eklenen hatalar:")
    print((klasor / "hatalar.txt").read_text(encoding="utf-8"))
    print(f"Temiz çiftlerde toplam HATA: {temiz_hata}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
