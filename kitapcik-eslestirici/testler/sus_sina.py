# -*- coding: utf-8 -*-
"""
Sayfa süsü yanlış "şekil eksik/fazla" vermemeli: bazı kitapçıklarda her sütunun
altında (sorunun son satırının hemen altında) noktalı bir süs çizgisi vardır.
A ile B'de sorular yer değiştirince süs başka sorunun altına düşer; bu bir
baskı hatası değildir. İki durum denetlenir, ikisinde de A ve B'ye aynı süs
çizilir:

  sütun sonu süsü  her sütunun son sorusunun hemen altına (yeri sayfaya göre
                   değişir) noktalı süs
  sabit süs        her sayfada aynı yerde (sayfa ortasında, soruların üstünde)
                   noktalı süs

Her durumda rapora, süssüz kopyaya göre yeni sorun düşmemeli.

Kullanım:  python3 sus_sina.py <app.py> <A.pdf> <B.pdf> <OTOMATİK|TYT|AYT|...> <çıktı_klasörü>
"""
import importlib.util
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

    def sus(sayfa, xo, y):                 # noktalı mercek biçimli süs (3 eğri)
        for dy in (0.0, 1.2, 2.4):
            sh = sayfa.new_shape()
            sh.draw_bezier((xo - 75, y + 3.5), (xo - 25, y + dy), (xo + 25, y + dy),
                           (xo + 75, y + 3.5))
            sh.finish(color=(0.36, 0.25, 0.6), width=0.9, dashes="[0 2.2] 0",
                      lineCap=1, closePath=False)
            sh.commit()

    def sutun_sonlari(k):                  # {(sayfa, taraf): son satırın alt kenarı}
        son = {}                           # (tam genişlik soru iki sütunu da kapatır)
        for o in k["ogeler"]:
            for pno, x0, _y0, x1, y1 in o["nesne_bolgeleri"]:
                W = k["genislikler"][pno]
                for taraf in (["L"] if x0 < W / 2 - 4 else []) + (["R"] if x1 > W / 2 + 4 else []):
                    son[(pno, taraf)] = max(son.get((pno, taraf), 0), y1 - 3)
        return son

    def suslu(src, dst, k, tur):
        doc = fitz.open(src)
        if tur == "sütun":
            for (pno, taraf), y1 in sutun_sonlari(k).items():
                W = doc[pno].rect.width
                sus(doc[pno], W / 4 if taraf == "L" else 3 * W / 4, y1 + 0.6)
        else:
            for sayfa in doc:
                W, H = sayfa.rect.width, sayfa.rect.height
                for xo in (W / 4, 3 * W / 4):
                    sus(sayfa, xo, 0.5 * H)
        doc.save(dst)

    def kontrol(qa, qb):
        ya = m.yapi_cikar(qa) if sinav == "OTOMATİK" else yapi
        yb = m.yapi_cikar(qb) if sinav == "OTOMATİK" else None
        return m.kontrol_et(qa, qb, ya, lambda _x: None, yapi_b=yb)[1]

    temiz = kontrol(a_pdf, b_pdf)
    tset = {(s["onem"], s["aciklama"]) for s in temiz}
    print(f"süssüz: {len(temiz)} sorun")
    hepsi = True
    for ad, tur in (("sütun sonu süsü", "sütun"), ("sabit süs", "sabit")):
        qa, qb = str(out / f"A_{tur}.pdf"), str(out / f"B_{tur}.pdf")
        suslu(a_pdf, qa, A, tur)
        suslu(b_pdf, qb, B, tur)
        yeni = [s for s in kontrol(qa, qb) if (s["onem"], s["aciklama"]) not in tset]
        tamam = not yeni
        hepsi &= tamam
        print(f"{'✓' if tamam else '✗'} {ad}: {len(yeni)} yeni sorun")
        for s in yeni:
            print(f"     {s['onem']} [{s['kitapcik']}] {s['test']} | {s['soru']} | "
                  f"{s['aciklama'][:130]}")
    print("SONUÇ:", "tamam" if hepsi else "SORUN")
    return 0 if hepsi else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:6]))
