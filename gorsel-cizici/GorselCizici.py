"""Görsel Çizici: ders kitabı çizimlerini (grafik, şekil, harita) görselden düzenlenebilir vektöre çevirir.

Kullanım:
  GorselCizici                 uygulamayı açar
  GorselCizici görsel.png      uygulamayı bu görselle açar
  GorselCizici --svg a.png b.svg   arayüzsüz çevirir
  GorselCizici --test          kendi kendini dener (kurulum denetimi)
"""
import sys


def _selftest() -> int:
    import numpy as np
    from PIL import Image, ImageDraw

    from gorsel_cizici import harita
    from gorsel_cizici.svg import to_svg
    from gorsel_cizici.vektor import vectorize

    im = Image.new("RGB", (320, 220), "white")
    d = ImageDraw.Draw(im)
    d.rectangle([40, 120, 80, 200], fill=(243, 149, 75))
    d.rectangle([100, 60, 140, 200], fill=(95, 190, 182))
    d.line([30, 200, 300, 200], fill=(0, 0, 0), width=1)
    d.line([30, 20, 30, 200], fill=(0, 0, 0), width=1)
    d.ellipse([200, 60, 260, 120], outline=(220, 30, 30), width=2)
    d.pieslice([170, 120, 290, 240], 180, 360, fill=(255, 252, 229), outline=(235, 97, 46))
    scene = vectorize(np.array(im))
    svg = to_svg(scene)
    kinds = {e.kind for e in scene.elements}
    ok = "fill" in kinds and "stroke" in kinds and svg.startswith("<svg")
    m1 = harita.build_svg(harita.MapStyle(kind="dunya", lon_list=[0, 45, 90, 135], points=[("K", -14, 46)]))
    m2 = harita.build_svg(harita.MapStyle(kind="turkiye", borders=True))
    ok = ok and len(m1) > 10000 and len(m2) > 10000
    print("TEST", "TAMAM" if ok else "HATA", len(scene.elements), "şekil;", len(m1), len(m2))
    return 0 if ok else 1


def _ocr_test() -> int:
    """Mac'in yazı tanımasını dener: Türkçe bir satır çizip okur."""
    import os
    import tempfile

    from PIL import Image, ImageDraw, ImageFont

    from gorsel_cizici import metin

    print("yazı tanıma var mı:", metin.available())
    if not metin.available():
        return 0 if sys.platform != "darwin" else 1
    font = None
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf"):
        if os.path.exists(p):
            font = ImageFont.truetype(p, 28)
            break
    im = Image.new("RGB", (640, 120), "white")
    d = ImageDraw.Draw(im)
    d.text((20, 20), "Batı Doğu Kuzey Güney", font=font, fill="black")
    d.text((20, 70), "Yağış 1980 Sıcaklık", font=font, fill="black")
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    im.save(path)
    words = metin.recognize(path, im.width, im.height)
    os.remove(path)
    for w in words:
        print(" ", w["text"], "(okunan: " + w.get("raw", "") + ")", [round(v) for v in w["box"]], round(w["conf"], 2), "satır", w.get("line"))
    import numpy as np
    acc = metin.validate(words, np.array(im))
    print("doğrulanan:", [(a["text"], round(a["score"], 2)) for a in acc])
    ok = len(words) >= 5 and len(acc) >= 5
    print("OCR", "TAMAM" if ok else "HATA", len(words), "kelime,", len(acc), "doğrulandı")
    return 0 if ok else 1


def _convert(src: str, dst: str) -> int:
    from gorsel_cizici.cizim import load_rgb
    from gorsel_cizici.svg import to_svg
    from gorsel_cizici.vektor import vectorize

    scene = vectorize(load_rgb(src))
    with open(dst, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + to_svg(scene))
    print(dst, scene.notes[-1] if scene.notes else "")
    return 0


def _utf8_output() -> None:
    """Windows konsolu Türkçe harfleri yazamayınca çökmesin."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


if __name__ == "__main__":
    _utf8_output()
    if "--test" in sys.argv:
        sys.exit(_selftest())
    if "--ocr-test" in sys.argv:
        sys.exit(_ocr_test())
    if len(sys.argv) >= 4 and sys.argv[1] == "--svg":
        sys.exit(_convert(sys.argv[2], sys.argv[3]))
    from gorsel_cizici.arayuz import main

    main()
