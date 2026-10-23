"""Sahneyi Illustrator'ın düzenlenebilir açtığı SVG'ye yazar.

SVG'nin kullanıcı birimi özgün görselin pikselidir; width/height pt cinsinden gerçek ölçüyü
verir (viewBox ile ölçeklenir). Kullanıcı yazı puntosu ya da çizgi kalınlığını pt olarak
verdiyse ölçeğe bölünerek yazılır.
"""
from __future__ import annotations

from dataclasses import dataclass
from xml.sax.saxutils import escape

from .vektor import Scene


@dataclass
class Style:
    width_mm: float | None = None      # None: görselin pikseli 0,75 pt (96 dpi)
    font: str = "Helvetica Neue"
    font_pt: float | None = None       # None: görseldeki boyut
    stroke_pt: float | None = None     # None: görseldeki kalınlık
    color: str | None = None           # None: görseldeki renkler; "#RRGGBB": çizgi ve yazılar bu renkte
    keep_background: bool = False


def _hex(c) -> str:
    return "#{:02X}{:02X}{:02X}".format(*[max(0, min(255, int(v))) for v in c])


def _f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def _rect_attrs(p: dict) -> str:
    """Dikdörtgen (köşesi yuvarlak ve döndürülmüş olabilir) öznitelikleri."""
    a = f' x="{_f(p["x"])}" y="{_f(p["y"])}" width="{_f(p["w"])}" height="{_f(p["h"])}"'
    if p["type"] == "rrect" and p.get("r", 0) > 0.05:
        a += f' rx="{_f(p["r"])}" ry="{_f(p["r"])}"'
    rot = p.get("rot", 0.0)
    if abs(rot) > 0.05:
        cx, cy = p["x"] + p["w"] / 2, p["y"] + p["h"] / 2
        a += f' transform="rotate({_f(rot)} {_f(cx)} {_f(cy)})"'
    return a


def _elips_duz(p: dict):
    """Elipsin döndürmesini sadeleştir: 90° döndürülmüş elips, yarıçapları yer değiştirmiş
    döndürülmemiş elipstir (Illustrator'da düz elips olarak açılsın)."""
    rx, ry, rot = p["rx"], p["ry"], float(p.get("rot", 0.0)) % 180.0
    if abs(rot - 90) <= 1.0:
        return ry, rx, 0.0
    if rot <= 1.0 or rot >= 179.0:
        return rx, ry, 0.0
    return rx, ry, rot


def scale_of(scene: Scene, st: Style) -> float:
    """1 piksel kaç pt."""
    if st.width_mm:
        return st.width_mm * 72 / 25.4 / max(scene.width, 1)
    return 0.75


def to_svg(scene: Scene, st: Style | None = None) -> str:
    st = st or Style()
    s = scale_of(scene, st)
    Wpt, Hpt = scene.width * s, scene.height * s
    fills, strokes, texts = [], [], []
    defs = []
    for e in scene.elements:
        if e.kind == "text":
            size = (st.font_pt / s) if st.font_pt else e.size
            col = st.color or _hex(e.color)
            weight = ' font-weight="bold"' if e.bold else ""
            anchor = f' text-anchor="{e.anchor}"' if e.anchor in ("middle", "end") else ""
            texts.append(f'<text x="{_f(e.x)}" y="{_f(e.y)}" font-family="{escape(st.font)}" font-size="{_f(size)}" fill="{col}"{weight}{anchor}>{escape(e.text)}</text>')
            continue
        if e.kind == "fill":
            col = _hex(e.color)
            if st.color and e.layer == "harf":
                col = st.color
            if e.grad:
                gid = f"degrade{len(defs) + 1}"
                g = e.grad
                stops = "".join(f'<stop offset="{_f(o)}" stop-color="{_hex(c)}"/>' for o, c in g["stops"])
                if g["type"] == "radial":
                    defs.append(f'<radialGradient id="{gid}" gradientUnits="userSpaceOnUse" cx="{_f(g["cx"])}" cy="{_f(g["cy"])}" r="{_f(max(g["r"], 0.5))}">{stops}</radialGradient>')
                else:
                    defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{_f(g["x1"])}" y1="{_f(g["y1"])}" x2="{_f(g["x2"])}" y2="{_f(g["y2"])}">{stops}</linearGradient>')
                col = f"url(#{gid})"
            p = e.prim
            ks = ""
            if e.stroke is not None:
                kc = st.color or _hex(e.stroke)
                kw = (st.stroke_pt / s) if st.stroke_pt else e.stroke_width
                ks = f' stroke="{kc}" stroke-width="{_f(kw)}" stroke-linejoin="miter"'
            if p and p["type"] in ("rect", "rrect"):
                fills.append(f'<rect{_rect_attrs(p)} fill="{col}"{ks}/>')
            elif p and p["type"] == "circle":
                fills.append(f'<circle cx="{_f(p["cx"])}" cy="{_f(p["cy"])}" r="{_f(p["r"])}" fill="{col}"{ks}/>')
            elif p and p["type"] == "ellipse":
                rx_, ry_, ro_ = _elips_duz(p)
                rot = f' transform="rotate({_f(ro_)} {_f(p["cx"])} {_f(p["cy"])})"' if abs(ro_) > 0.5 else ""
                fills.append(f'<ellipse cx="{_f(p["cx"])}" cy="{_f(p["cy"])}" rx="{_f(rx_)}" ry="{_f(ry_)}" fill="{col}"{rot}{ks}/>')
            elif p and p["type"] == "polygon":
                pts = " ".join(f"{_f(x)},{_f(y)}" for x, y in p["pts"])
                fills.append(f'<polygon points="{pts}" fill="{col}"{ks}/>')
            elif p and p["type"] == "path":
                from .sekil import path_d
                fills.append(f'<path d="{path_d(p)}" fill="{col}"{ks}/>')
            elif e.d:
                fills.append(f'<path d="{e.d}" fill="{col}" fill-rule="evenodd"{ks}/>')
            continue
        # çizgi
        col = st.color or _hex(e.color)
        wd = (st.stroke_pt / s) if st.stroke_pt else e.width
        attrs = f'fill="none" stroke="{col}" stroke-width="{_f(wd)}"'
        if e.dash:
            scale_d = (wd / e.width) if (st.stroke_pt and e.width > 0) else 1.0
            attrs += ' stroke-dasharray="' + " ".join(_f(v * (scale_d if i % 2 == 0 and v > 0.05 else 1)) for i, v in enumerate(e.dash)) + '"'
        if e.cap in ("round", "square"):
            attrs += f' stroke-linecap="{e.cap}"'
        attrs += f' stroke-linejoin="{getattr(e, "join", "round") or "round"}"'
        p = e.prim
        if p and p["type"] == "line":
            strokes.append(f'<line x1="{_f(p["x1"])}" y1="{_f(p["y1"])}" x2="{_f(p["x2"])}" y2="{_f(p["y2"])}" {attrs}/>')
        elif p and p["type"] == "circle":
            strokes.append(f'<circle cx="{_f(p["cx"])}" cy="{_f(p["cy"])}" r="{_f(p["r"])}" {attrs}/>')
        elif p and p["type"] in ("rect", "rrect"):
            attrs = attrs.replace('stroke-linejoin="round"', 'stroke-linejoin="miter"')
            strokes.append(f'<rect{_rect_attrs(p)} {attrs}/>')
        elif p and p["type"] == "ellipse":
            rx_, ry_, ro_ = _elips_duz(p)
            rot = f' transform="rotate({_f(ro_)} {_f(p["cx"])} {_f(p["cy"])})"' if abs(ro_) > 0.5 else ""
            strokes.append(f'<ellipse cx="{_f(p["cx"])}" cy="{_f(p["cy"])}" rx="{_f(rx_)}" ry="{_f(ry_)}" {attrs}{rot}/>')
        elif p and p["type"] == "path":
            from .sekil import path_d
            strokes.append(f'<path d="{path_d(p)}" {attrs}/>')
        elif p and p["type"] == "polygon":
            pts = " ".join(f"{_f(x)},{_f(y)}" for x, y in p["pts"])
            strokes.append(f'<polygon points="{pts}" {attrs}/>')
        elif e.d:
            strokes.append(f'<path d="{e.d}" {attrs}/>')
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{_f(Wpt)}pt" height="{_f(Hpt)}pt" viewBox="0 0 {scene.width} {scene.height}">']
    if defs:
        parts.append("<defs>" + "".join(defs) + "</defs>")
    if st.keep_background:
        parts.append(f'<rect id="Zemin" width="{scene.width}" height="{scene.height}" fill="{_hex(scene.background)}"/>')
    if getattr(scene, "underlay", ""):
        parts.append(scene.underlay)
    # Dolgular ve çizgiler, alttan üste çizim sırasıyla (küçük noktalar çizgilerin üstünde kalır)
    if fills:
        parts.append('<g id="Dolgular">' + "".join(_ordered(scene, "fill", fills)) + "</g>")
    if strokes:
        parts.append('<g id="Cizgiler">' + "".join(strokes) + "</g>")
    tops = _ordered(scene, "fill-top", fills)
    if tops:
        parts.append('<g id="Ustteki_sekiller">' + "".join(tops) + "</g>")
    if texts:
        parts.append('<g id="Yazilar">' + "".join(texts) + "</g>")
    parts.append("</svg>")
    return "".join(parts)


def _ordered(scene: Scene, which: str, fills: list) -> list:
    """Dolguları alttakiler ve çizgilerin üstündekiler (küçük noktalar, harfler) diye ayır."""
    out = []
    i = 0
    for e in scene.elements:
        if e.kind != "fill":
            continue
        top = getattr(e, "_top", None)
        if top is None:
            top = e.layer == "harf" or e.layer == "ust"
        if (which == "fill" and not top) or (which == "fill-top" and top):
            out.append(fills[i])
        i += 1
    return out
