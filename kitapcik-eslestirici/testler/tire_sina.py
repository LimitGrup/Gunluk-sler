# -*- coding: utf-8 -*-
"""
Satır sonu tiresi A ile B'de farklı karakterle yazılmışsa (dizgi programına göre
"-", yumuşak tire ya da Unicode tire olabilir) A–B KONTROL sahte "noktalama
farkı" vermemeli. Örnek kitapçıklar satır sonunda kelime bölünerek yeniden
dizilir: A'da "-", B'de "‐" (U+2010), yumuşak tire ya da yine "-".
Beklenen: üç çiftte de 0 HATA, 0 UYARI.

Kullanım:  python3 tire_sina.py <app.py> <cikti_klasoru>
"""
import importlib.util
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
    tire = ["-"]

    def _sar(self, metin, genislik, boy=9, kalin=False):
        """Sığmayan kelimeyi bölüp bu satıra tireyle koyar."""
        f = self.fontb if kalin else self.font
        satirlar, aktif = [], ""
        for k in metin.split():
            aday = (aktif + " " + k).strip()
            if f.text_length(aday, boy) <= genislik:
                aktif = aday
                continue
            bol = next((i for i in range(len(k) - 2, 2, -1)
                        if f.text_length((aktif + " " + k[:i] + "-").strip(), boy)
                        <= genislik), None)
            if bol and aktif:
                satirlar.append((aktif + " " + k[:bol] + tire[0]).strip())
                aktif = k[bol:]
            else:
                satirlar.append(aktif)
                aktif = k
        if aktif:
            satirlar.append(aktif)
        return satirlar

    g.Dizgi._sar = _sar
    a = g.icerik_uret(g.ORTAOKUL, 4, 7)
    b = g.karistir(a, 11)
    g.dizgile(a, "A", "26270704", cikti / "tire_A.pdf", cevapli=False)
    ciftler = (("tire_B_ayni", "-"), ("tire_B_2010", "‐"),
               ("tire_B_yumusak", "­"))
    for ad, t in ciftler:
        tire[0] = t
        g.dizgile(b, "B", "26270705", cikti / f"{ad}.pdf", cevapli=False)

    m = yukle("kitapcik_app", app)
    m.bagimliliklari_yukle()
    a_pdf = str(cikti / "tire_A.pdf")
    yapi = m.yapi_cikar(a_pdf)
    toplam = 0
    for ad, _t in ciftler:
        sonuc, sorunlar = m.kontrol_et(a_pdf, str(cikti / f"{ad}.pdf"), yapi,
                                       lambda _x: None)
        es = sonuc["eslesmeler"]
        print(f"{ad}: {len(sorunlar)} sorun | birebir "
              f"{sum(1 for e in es if not e[6])}/{len(es)} | gruplar "
              f"{sum(1 for g_ in sonuc['gruplar'] if not g_[7])}/{len(sonuc['gruplar'])}")
        for s in sorunlar:
            print(f"   {s['onem']} {s['soru']}: {s['aciklama'][:120]}")
        toplam += len(sorunlar)
    print("SONUÇ:", "temiz" if not toplam else f"{toplam} sahte sorun")


if __name__ == "__main__":
    main(*sys.argv[1:3])
