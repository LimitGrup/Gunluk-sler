"""Uygulama simgesi: koyu zemin üzerinde sarı elmas ve beyaz bir sütun-çizgi çizimi.

python paketleme/simge.py         -> simge.iconset (Mac: iconutil ile simge.icns yapılır)
python paketleme/simge.py --ico   -> simge.ico (Windows)
"""
import os
import sys

from PIL import Image, ImageDraw


def draw(n: int) -> Image.Image:
    s = n / 1024
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([int(64 * s), int(64 * s), int(960 * s), int(960 * s)], radius=int(200 * s), fill=(31, 31, 31, 255))
    # sütunlar
    bars = [(250, 600), (390, 470), (530, 380), (670, 520)]
    for x, top in bars:
        d.rectangle([int(x * s), int(top * s), int((x + 95) * s), int(800 * s)], fill=(255, 176, 0, 255))
    # eksen
    d.line([int(200 * s), int(820 * s), int(820 * s), int(820 * s)], fill=(240, 240, 240, 255), width=max(1, int(22 * s)))
    d.line([int(200 * s), int(230 * s), int(200 * s), int(820 * s)], fill=(240, 240, 240, 255), width=max(1, int(22 * s)))
    # çizgi
    pts = [(297, 520), (437, 360), (577, 300), (717, 400)]
    d.line([(int(x * s), int(y * s)) for x, y in pts], fill=(255, 255, 255, 255), width=max(1, int(26 * s)), joint="curve")
    for x, y in pts:
        r = 34 * s
        d.ellipse([x * s - r, y * s - r, x * s + r, y * s + r], fill=(255, 255, 255, 255))
    return im


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    if "--ico" in sys.argv:
        draw(256).save(os.path.join(root, "simge.ico"), sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    else:
        out = os.path.join(root, "simge.iconset")
        os.makedirs(out, exist_ok=True)
        for size in (16, 32, 128, 256, 512):
            draw(size).save(os.path.join(out, f"icon_{size}x{size}.png"))
            draw(size * 2).save(os.path.join(out, f"icon_{size}x{size}@2x.png"))
    print("simge hazır")
