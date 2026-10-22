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


def _convert(src: str, dst: str) -> int:
    from gorsel_cizici.cizim import load_rgb
    from gorsel_cizici.svg import to_svg
    from gorsel_cizici.vektor import vectorize

    scene = vectorize(load_rgb(src))
    with open(dst, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + to_svg(scene))
    print(dst, scene.notes[-1] if scene.notes else "")
    return 0


if __name__ == "__main__":
    if "--test" in sys.argv:
        sys.exit(_selftest())
    if len(sys.argv) >= 4 and sys.argv[1] == "--svg":
        sys.exit(_convert(sys.argv[2], sys.argv[3]))
    from gorsel_cizici.arayuz import main

    main()
