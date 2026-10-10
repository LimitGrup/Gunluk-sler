# -*- coding: utf-8 -*-
"""
A–B KONTROL'ün numara denetimi gerçek bir dizgide doğru mu: baskı A/B
kitapçıklarında B'nin soru numaraları farklı biçimlerde bozulur, her senaryo
ayrı bir kopyada denetlenir:

  mükerrer         ortadaki soruya bir önceki sorunun numarası yazılır
  olmayan numara   ortadaki soruya testte olmayan bir numara yazılır
  yer değiştirmiş  ardışık iki sorunun numaraları değiştirilir
  kaymış           ortadaki sorudan testin sonuna kadar numaralar +1
  branş devamı     ikinci testin numaraları 1'den değil önceki testin
                   sonundan devam eder (Sosyal 1–10 yerine 21–30)
  numara silinmiş  ortadaki sorunun numarası silinir
  nokta unutulmuş  ortadaki sorunun numarası noktasız yazılır ("11")

Her senaryoda beklenen HATA tam o numarada çıkmalı. Temiz kopyada bulunmayan
ve senaryonun dokunmadığı bir yerde yeni HATA çıkmamalı (yan etki yok).

Kopyalar <çıktı_klasörü> içine yazılır; kaynak PDF'lere dokunulmaz.

Kullanım:  python3 numara_sina.py <app.py> <A_baski.pdf> <B_baski.pdf> <OTOMATİK|TYT|AYT|...> <çıktı_klasörü>
(Cevaplı bir çiftten baskı kopyası baski_kopya_sina.py ile üretilebilir.)
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


def main(app, qa, qb, sinav, cikti):
    m = yukle("kitapcik_app", app)
    m.bagimliliklari_yukle()
    fitz = m.fitz
    out = Path(cikti)
    out.mkdir(parents=True, exist_ok=True)
    yapi = m.yapi_cikar(qa) if sinav == "OTOMATİK" else m.YAPILAR[sinav]
    _A, B = m._kitapciklari_hazirla(qa, qb, yapi, None, None)
    testler = {}
    for o in B["ogeler"]:
        if o["no"]:
            testler.setdefault(o["ti"], []).append(o)
    sirali = [sorted(v, key=lambda o: o["no"]) for _t, v in sorted(testler.items())]
    s1 = max(sirali, key=len)                       # en uzun test
    s2 = next(v for v in sirali if v is not s1 and len(v) >= 4 and v[0]["ti"] > s1[0]["ti"])
    N, k = len(s1), len(s1) // 2

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

    def boz(degisim, yol):
        doc = fitz.open(qb)
        yerler = [(numara_yeri(doc, o), yeni) for o, yeni in degisim]
        for (page, r, _org, _boy), _y in yerler:
            h = r.height
            page.add_redact_annot(fitz.Rect(r.x0 + 0.2, r.y0 + 0.3 * h, r.x1 - 0.2, r.y1 - 0.3 * h))
        for page in {id(p): p for (p, *_r), _y in yerler}.values():
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                                  graphics=fitz.PDF_REDACT_LINE_ART_NONE)
        for (page, _r, org, boy), yeni in yerler:
            if yeni:
                page.insert_text(org, yeni, fontsize=boy, fontname="hebo", color=(0, 0, 0))
        doc.save(yol)

    a, b_ = s1[k], s1[k + 1]
    n, n2 = a["no"], b_["no"]
    # ad, değişiklik, beklenen açıklama parçaları (her biri en az bir HATA'da geçmeli)
    senaryolar = [
        ("mükerrer", [(a, f"{n - 1}.")],
         [f"{n}. soru bulunamadı", f"büyük olasılıkla {n}"]),
        ("olmayan numara", [(a, f"{N + 27}.")], [f"{n}. soru bulunamadı"]),
        ("yer değiştirmiş", [(a, f"{n2}."), (b_, f"{n}.")],
         [f"Numaralar sırasız: {n2}. soru {n}. sorudan önce"]),
        ("kaymış", [(o, f"{o['no'] + 1}.") for o in s1[k:]],
         [f"{n}. soru bulunamadı", f"{n}. sorudan itibaren numaralar bir fazla"]),
        ("branş devamı", [(o, f"{o['no'] + len(s1)}.") for o in s2],
         [f"bu testin 1–{len(s2)}. soruları '{len(s1) + 1}.'–'{len(s1) + len(s2)}.'"]),
        ("numara silinmiş", [(a, None)], [f"{n}. soru bulunamadı"]),
        ("nokta unutulmuş", [(a, f"{n}")], [f"{n}. soru bulunamadı"]),
    ]

    def kontrol(yol):
        ya = m.yapi_cikar(qa) if sinav == "OTOMATİK" else yapi
        yb = m.yapi_cikar(yol) if sinav == "OTOMATİK" else None
        return m.kontrol_et(qa, yol, ya, lambda _x: None, yapi_b=yb)[1]

    temiz = kontrol(qb)
    tset = {(s["onem"], s["aciklama"]) for s in temiz}
    print(f"temiz: {len(temiz)} sorun")
    hepsi = True
    for i, (ad, degisim, beklenen) in enumerate(senaryolar):
        yol = str(out / f"B_numara{i}.pdf")
        boz(degisim, yol)
        yeni = [s for s in kontrol(yol) if (s["onem"], s["aciklama"]) not in tset]
        hata = [s for s in yeni if s["onem"] == "HATA"]
        eksik = [p for p in beklenen if not any(p in s["aciklama"] for s in hata)]
        tamam = not eksik
        hepsi &= tamam
        print(f"{'✓' if tamam else '✗'} {ad}: {len(yeni)} yeni sorun"
              + (f"; bulunamayan: {eksik}" if eksik else ""))
        for s in yeni:
            print(f"     {s['onem']} [{s['kitapcik']}] {s['test']} | {s['soru']} | {s['aciklama'][:150]}")
    print("SONUÇ:", "tamam" if hepsi else "SORUN")
    return 0 if hepsi else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:6]))
