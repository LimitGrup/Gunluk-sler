"""Uygulama simgesi: deniz yeşili zemin üzerinde beyaz sütunlar ve bir kalem ucu.

python paketleme/simge.py         -> simge.iconset (Mac: iconutil ile simge.icns yapılır)
python paketleme/simge.py --ico   -> simge.ico (Windows)
"""
import math
import os
import sys

from PIL import Image, ImageDraw

ZEMIN = (15, 118, 110, 255)      # #0F766E
ACIK = (204, 237, 232, 255)      # açık deniz yeşili
BEYAZ = (255, 255, 255, 255)


def draw(n: int) -> Image.Image:
    k = 4 if n < 256 else 2            # küçük boylarda yumuşak kenar için büyük çiz, küçült
    N = n * k
    s = N / 1024
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([int(80 * s), int(80 * s), int(944 * s), int(944 * s)], radius=int(190 * s), fill=ZEMIN)
    # taban çizgisi ve üç sütun
    d.rounded_rectangle([int(200 * s), int(786 * s), int(824 * s), int(818 * s)], radius=int(16 * s), fill=ACIK)
    for x, top in ((220, 600), (360, 470), (500, 540)):
        d.rounded_rectangle([int(x * s), int(top * s), int((x + 100) * s), int(800 * s)], radius=int(22 * s), fill=BEYAZ)
    # kalem ucu (aşağı-sola bakan)
    cx, cy, ang = 690, 380, math.radians(45)
    nib = [(-105, -190), (105, -190), (105, -50), (0, 175), (-105, -50)]

    def rot(x, y):
        return (cx + x * math.cos(ang) - y * math.sin(ang)) * s, (cy + x * math.sin(ang) + y * math.cos(ang)) * s

    d.polygon([rot(x, y) for x, y in nib], fill=BEYAZ)
    d.line([rot(0, 170), rot(0, 10)], fill=ZEMIN, width=max(1, int(18 * s)))
    hx, hy = rot(0, -5)
    r = 30 * s
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=ZEMIN)
    return im.resize((n, n), Image.LANCZOS)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    if "--ico" in sys.argv:
        draw(256).save(os.path.join(root, "simge.ico"), sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    elif "--png" in sys.argv:
        draw(512).save(sys.argv[sys.argv.index("--png") + 1])
    else:
        out = os.path.join(root, "simge.iconset")
        os.makedirs(out, exist_ok=True)
        for size in (16, 32, 128, 256, 512):
            draw(size).save(os.path.join(out, f"icon_{size}x{size}.png"))
            draw(size * 2).save(os.path.join(out, f"icon_{size}x{size}@2x.png"))
    print("simge hazır")
