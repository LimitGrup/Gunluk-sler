"""Dilsiz dünya ve Türkiye haritaları (Natural Earth verisi, kamu malı).

Harita doğrudan SVG olarak üretilir: kara, sınırlar, paralel/meridyenler, noktalar ve
yazılar ayrı katmanlardadır; Illustrator'da her parça düzenlenebilir.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from functools import lru_cache
from xml.sax.saxutils import escape

VERI = os.path.join(os.path.dirname(__file__), "veri")


# ---------------------------------------------------------------- veri
@lru_cache(maxsize=None)
def _geo(name: str):
    with open(os.path.join(VERI, name), encoding="utf-8") as f:
        return json.load(f)


def _polys(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    return []


def world_land(detail: str):
    d = _geo("ne_50m_land.geojson" if detail == "50m" else "ne_110m_land.geojson")
    return [pl for f in d["features"] for pl in _polys(f["geometry"])]


def world_countries(detail: str):
    d = _geo("ne_50m_admin_0_countries.geojson" if detail == "50m" else "ne_110m_admin_0_countries.geojson")
    return [(f["properties"].get("NAME_TR") or f["properties"].get("NAME"), _polys(f["geometry"])) for f in d["features"]]


def turkey():
    return _geo("turkiye.json")


# ---------------------------------------------------------------- izdüşümler
def _miller(lat):
    return 1.25 * math.log(math.tan(math.pi / 4 + 0.4 * math.radians(lat)))


def _mercator(lat):
    lat = max(-85.0, min(85.0, lat))
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


# Robinson tablosu (her 5°): X uzunluk katsayısı, Y yükseklik katsayısı
_ROB = [(1.0000, 0.0000), (0.9986, 0.0620), (0.9954, 0.1240), (0.9900, 0.1860), (0.9822, 0.2480),
        (0.9730, 0.3100), (0.9600, 0.3720), (0.9427, 0.4340), (0.9216, 0.4958), (0.8962, 0.5571),
        (0.8679, 0.6176), (0.8350, 0.6769), (0.7986, 0.7346), (0.7597, 0.7903), (0.7186, 0.8435),
        (0.6732, 0.8936), (0.6213, 0.9394), (0.5722, 0.9761), (0.5322, 1.0000)]


def _robinson(lon, lat):
    a = min(abs(lat), 90.0) / 5.0
    i = min(int(a), 17)
    t = a - i
    X = _ROB[i][0] + (_ROB[i + 1][0] - _ROB[i][0]) * t
    Y = _ROB[i][1] + (_ROB[i + 1][1] - _ROB[i][1]) * t
    return 0.8487 * X * math.radians(lon), 1.3523 * Y * (1 if lat >= 0 else -1)


PROJECTIONS = {
    "miller": "Miller (ders kitaplarındaki gibi)",
    "esdik": "Eşdikdörtgen (enlem-boylam ızgarası)",
    "mercator": "Mercator",
    "robinson": "Robinson",
}


def project(proj: str, lon: float, lat: float, lat0: float = 0.0):
    """Boylam/enlem -> düzlem (x sağa, y yukarı). lon: merkez boylamına göre."""
    if proj == "miller":
        return math.radians(lon), _miller(lat)
    if proj == "mercator":
        return math.radians(lon), _mercator(lat)
    if proj == "robinson":
        return _robinson(lon, lat)
    # eşdikdörtgen: orta enlemde gerçek oran
    return math.radians(lon) * math.cos(math.radians(lat0)), math.radians(lat)


# ---------------------------------------------------------------- kırpma
def _clip(ring, axis, val, keep_greater):
    """Sutherland–Hodgman: bir doğrunun tek yanında kalan kısım."""
    out = []
    n = len(ring)
    if n == 0:
        return out

    def inside(p):
        return p[axis] >= val if keep_greater else p[axis] <= val

    for i in range(n):
        cur, prev = ring[i], ring[i - 1]
        ci, pi = inside(cur), inside(prev)
        if ci:
            if not pi:
                out.append(_cross(prev, cur, axis, val))
            out.append(cur)
        elif pi:
            out.append(_cross(prev, cur, axis, val))
    return out


def _cross(a, b, axis, val):
    t = (val - a[axis]) / (b[axis] - a[axis]) if b[axis] != a[axis] else 0.0
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def clip_ring(ring, lon_min, lon_max, lat_min, lat_max):
    r = [tuple(p) for p in ring]
    r = _clip(r, 0, lon_min, True)
    r = _clip(r, 0, lon_max, False)
    r = _clip(r, 1, lat_min, True)
    r = _clip(r, 1, lat_max, False)
    return r if len(r) >= 3 else []


def _unwrap(ring, center):
    """Boylamları merkez boylamına göre sürekli yap (180°'yi geçen halkalar kopmasın)."""
    out = []
    prev = None
    for lon, lat in ring:
        x = lon - center
        x = (x + 180) % 360 - 180
        if prev is not None:
            while x - prev > 180:
                x -= 360
            while x - prev < -180:
                x += 360
        out.append((x, lat))
        prev = x
    return out


def _ring_copies(ring, center, lon_min, lon_max, lat_min, lat_max):
    """Halkayı merkeze göre aç, harita sınırına kırp; sınırı aşan kısım öbür yanda da çizilir."""
    u = _unwrap(ring, center)
    out = []
    for shift in (-360, 0, 360):
        sh = [(x + shift, y) for x, y in u]
        xs = [x for x, _ in sh]
        if max(xs) < lon_min or min(xs) > lon_max:
            continue
        c = clip_ring(sh, lon_min, lon_max, lat_min, lat_max)
        if c:
            out.append(c)
    return out


# ---------------------------------------------------------------- ayarlar
@dataclass
class MapStyle:
    kind: str = "dunya"                 # "dunya" | "turkiye"
    proj: str = "miller"
    center: float = 10.0                # orta boylam (dünya)
    lat_top: float = 84.0
    lat_bottom: float = -58.0
    detail: str = "110m"                # "110m" (sade) | "50m" (ayrıntılı)
    width_mm: float = 160.0
    land: str = "#CFCFCF"
    sea: str = ""                       # boş: deniz boyanmaz
    outline: str = "#000000"
    outline_pt: float = 0.4
    borders: bool = False               # ülke sınırları (dünya) / il sınırları (Türkiye)
    border_pt: float = 0.25
    neighbors: bool = True              # Türkiye: komşu ülkeleri açık renkte göster
    neighbor_fill: str = "#EDEDED"
    grid_lon: float = 0.0               # meridyen aralığı (°), 0: yok
    grid_lat: float = 0.0               # paralel aralığı (°), 0: yok
    lon_list: list = field(default_factory=list)   # ayrıca çizilecek meridyenler (ör. 0, 45, 90, 135)
    lat_list: list = field(default_factory=list)   # ayrıca çizilecek paraleller
    equator: bool = True
    prime: bool = False                 # başlangıç meridyeni
    grid_pt: float = 0.6
    grid_color: str = "#000000"
    labels: bool = True                 # ızgara derecelerini yaz
    font: str = "Helvetica Neue"
    font_pt: float = 8.0
    frame: bool = False
    points: list = field(default_factory=list)   # [(ad, boylam, enlem)]
    point_color: str = "#E3262B"
    point_mm: float = 1.6


def _deg_label(v: float, axis: str) -> str:
    a = abs(v)
    s = f"{a:g}°"
    if a < 1e-9:
        return "0°"
    if axis == "lon":
        return f"{s} {'D' if v > 0 else 'B'}"
    return f"{s} {'K' if v > 0 else 'G'}"


def _f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def build_svg(st: MapStyle) -> str:
    if st.kind == "turkiye":
        lon_min, lon_max, lat_min, lat_max = 25.4, 45.2, 35.6, 42.35
        center, proj, lat0 = 0.0, "esdik", 39.0
    else:
        lon_min, lon_max = -180.0, 180.0
        lat_min, lat_max = st.lat_bottom, st.lat_top
        center, proj, lat0 = st.center, st.proj, 0.0

    # sınırların düzlemdeki kutusu
    def P(lon_rel, lat):
        return project(proj, lon_rel, lat, lat0)

    corners = [P(x, y) for x in (lon_min, lon_max, (lon_min + lon_max) / 2) for y in (lat_min, lat_max, 0 if lat_min < 0 < lat_max else lat_min)]
    if proj == "robinson":
        corners += [P(lon_min, 0), P(lon_max, 0)]
    X0, X1 = min(c[0] for c in corners), max(c[0] for c in corners)
    Y0, Y1 = min(c[1] for c in corners), max(c[1] for c in corners)
    W = st.width_mm * 72 / 25.4
    s = W / (X1 - X0)
    H = (Y1 - Y0) * s
    pad_top = st.font_pt * 1.6 if (st.labels and (st.grid_lon or st.lon_list or st.prime)) else 2
    pad_right = st.font_pt * 3.2 if (st.labels and (st.grid_lat or st.lat_list or (st.equator and st.kind != "turkiye"))) else 2
    Wt, Ht = W + pad_right + 2, H + pad_top + 2

    def XY(lon_rel, lat):
        x, y = P(lon_rel, lat)
        return 1 + (x - X0) * s, pad_top + (Y1 - y) * s

    def ring_d(ring):
        pts = [XY(x, y) for x, y in ring]
        # çok yakın noktaları at
        out = [pts[0]]
        for p in pts[1:]:
            if abs(p[0] - out[-1][0]) + abs(p[1] - out[-1][1]) > 0.12:
                out.append(p)
        if len(out) < 3:
            return ""
        return "M" + "L".join(f"{_f(x)} {_f(y)}" for x, y in out) + "Z"

    def poly_d(polys, clip_center):
        d = []
        for pl in polys:
            for ring in pl:
                if st.kind == "turkiye":
                    c = clip_ring([tuple(p) for p in ring], lon_min, lon_max, lat_min, lat_max)
                    if c:
                        d.append(ring_d(c))
                else:
                    for c in _ring_copies(ring, clip_center, lon_min, lon_max, lat_min, lat_max):
                        d.append(ring_d(c))
        return "".join(x for x in d if x)

    g_sea, g_neigh, g_land, g_border, g_grid, g_pts, g_txt = [], [], [], [], [], [], []
    ow = _f(st.outline_pt)
    if st.sea:
        g_sea.append(f'<rect x="1" y="{_f(pad_top)}" width="{_f(W)}" height="{_f(H)}" fill="{st.sea}"/>')
    if st.kind == "turkiye":
        data = turkey()
        if st.neighbors:
            for kom in data["komsular"]:
                d = poly_d(kom["p"], 0)
                if d:
                    g_neigh.append(f'<path d="{d}" fill="{st.neighbor_fill}" stroke="{st.outline}" stroke-width="{_f(st.border_pt)}" stroke-linejoin="round" fill-rule="evenodd"/>')
        if st.borders:
            for il in data["iller"]:
                d = poly_d(il["p"], 0)
                if d:
                    g_land.append(f'<path id="{escape(_idsafe(il["ad"]))}" d="{d}" fill="{st.land}" stroke="{st.outline}" stroke-width="{_f(st.border_pt)}" stroke-linejoin="round" fill-rule="evenodd"/>')
            # dış sınır kalın: illerin birleşimi yerine her ilin dış kenarı zaten çizilir; ülke sınırı ayrıca
        d_all = poly_d(_turkey_outline(), 0)
        if not st.borders:
            g_land.append(f'<path id="Turkiye" d="{d_all}" fill="{st.land}" stroke="{st.outline}" stroke-width="{ow}" stroke-linejoin="round" fill-rule="evenodd"/>')
        else:
            g_border.append(f'<path id="Turkiye_siniri" d="{d_all}" fill="none" stroke="{st.outline}" stroke-width="{ow}" stroke-linejoin="round"/>')
    else:
        if st.borders:
            for name, polys in world_countries(st.detail):
                d = poly_d(polys, center)
                if d:
                    g_land.append(f'<path id="{escape(_idsafe(name))}" d="{d}" fill="{st.land}" stroke="{st.outline}" stroke-width="{_f(st.border_pt)}" stroke-linejoin="round" fill-rule="evenodd"/>')
            land = poly_d(world_land(st.detail), center)
            g_border.append(f'<path id="Kiyilar" d="{land}" fill="none" stroke="{st.outline}" stroke-width="{ow}" stroke-linejoin="round"/>')
        else:
            land = poly_d(world_land(st.detail), center)
            g_land.append(f'<path id="Kara" d="{land}" fill="{st.land}" stroke="{st.outline}" stroke-width="{ow}" stroke-linejoin="round" fill-rule="evenodd"/>')

    # paralel ve meridyenler
    gw = _f(st.grid_pt)
    fs = st.font_pt

    def text(x, y, t, anchor="start"):
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        return f'<text x="{_f(x)}" y="{_f(y)}" font-family="{escape(st.font)}" font-size="{_f(fs)}" fill="#000000"{a}>{escape(t)}</text>'

    def meridian(lon_abs):
        rel = lon_abs - center if st.kind != "turkiye" else lon_abs
        rel = (rel + 180) % 360 - 180 if st.kind != "turkiye" else rel
        if not (lon_min - 1e-9 <= rel <= lon_max + 1e-9):
            return
        pts = [XY(rel, lat_min + (lat_max - lat_min) * i / 60) for i in range(61)]
        g_grid.append(f'<path d="M{"L".join(f"{_f(x)} {_f(y)}" for x, y in pts)}" fill="none" stroke="{st.grid_color}" stroke-width="{gw}"/>')
        if st.labels:
            x, y = pts[-1]
            g_txt.append(text(x, y - fs * 0.45, _deg_label(lon_abs, "lon"), "middle"))

    def parallel(lat):
        if not (lat_min <= lat <= lat_max):
            return
        pts = [XY(lon_min + (lon_max - lon_min) * i / 90, lat) for i in range(91)]
        g_grid.append(f'<path d="M{"L".join(f"{_f(x)} {_f(y)}" for x, y in pts)}" fill="none" stroke="{st.grid_color}" stroke-width="{gw}"/>')
        if st.labels:
            x, y = pts[-1]
            g_txt.append(text(x + fs * 0.4, y + fs * 0.35, _deg_label(lat, "lat")))

    done_lon, done_lat = set(), set()
    if st.grid_lon:
        k0 = math.ceil(-180 / st.grid_lon)
        for k in range(k0, int(180 / st.grid_lon) + 1):
            v = round(k * st.grid_lon, 6)
            if st.kind == "turkiye" and not (lon_min <= v <= lon_max):
                continue
            if v in done_lon or v <= -180:
                continue
            done_lon.add(v)
            meridian(v)
    if st.prime and 0.0 not in done_lon:
        done_lon.add(0.0)
        meridian(0.0)
    for v in st.lon_list:
        v = float(v)
        if v not in done_lon:
            done_lon.add(v)
            meridian(v)
    for v in st.lat_list:
        v = float(v)
        if v not in done_lat and abs(v) < 90:
            done_lat.add(v)
            parallel(v)
    if st.grid_lat:
        k0 = math.ceil(-90 / st.grid_lat)
        for k in range(k0, int(90 / st.grid_lat) + 1):
            v = round(k * st.grid_lat, 6)
            if v in done_lat or abs(v) >= 90:
                continue
            done_lat.add(v)
            parallel(v)
    if st.equator and 0.0 not in done_lat and st.kind != "turkiye":
        parallel(0.0)

    # noktalar
    r = st.point_mm * 72 / 25.4 / 2
    for name, lon, lat in st.points:
        rel = lon if st.kind == "turkiye" else ((lon - center + 180) % 360 - 180)
        if not (lon_min <= rel <= lon_max and lat_min <= lat <= lat_max):
            continue
        x, y = XY(rel, lat)
        g_pts.append(f'<circle cx="{_f(x)}" cy="{_f(y)}" r="{_f(r)}" fill="{st.point_color}"/>')
        if name:
            g_txt.append(text(x + r * 1.6, y - r * 0.6, name))

    if st.frame:
        g_grid.append(f'<rect x="1" y="{_f(pad_top)}" width="{_f(W)}" height="{_f(H)}" fill="none" stroke="#000000" stroke-width="{gw}"/>')

    def grp(name, items):
        return f'<g id="{name}">' + "".join(items) + "</g>" if items else ""

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{_f(Wt)}pt" height="{_f(Ht)}pt" viewBox="0 0 {_f(Wt)} {_f(Ht)}">'
            + grp("Deniz", g_sea) + grp("Komsu_ulkeler", g_neigh) + grp("Kara", g_land) + grp("Sinirlar", g_border)
            + grp("Paralel_meridyen", g_grid) + grp("Noktalar", g_pts) + grp("Yazilar", g_txt) + "</svg>")


@lru_cache(maxsize=1)
def _turkey_outline():
    """İllerin dış kenarlarından Türkiye sınırı: yalnız bir ile ait kenarlar."""
    data = turkey()
    from collections import Counter
    cnt = Counter()
    rings = []
    for il in data["iller"]:
        for pl in il["p"]:
            for ring in pl:
                rings.append(ring)
                for a, b in zip(ring, ring[1:] + ring[:1]):
                    key = (tuple(a), tuple(b)) if tuple(a) < tuple(b) else (tuple(b), tuple(a))
                    cnt[key] += 1
    # dış kenarları zincirle
    outer = {k for k, v in cnt.items() if v == 1}
    adj = {}
    for a, b in outer:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    used = set()
    polys = []
    for a, b in outer:
        if (a, b) in used:
            continue
        ring = [a]
        prev, cur = a, b
        used.add((a, b))
        while cur != a and len(ring) < 200000:
            ring.append(cur)
            nxt = [q for q in adj.get(cur, []) if q != prev and ((cur, q) if cur < q else (q, cur)) not in used]
            if not nxt:
                break
            q = nxt[0]
            used.add((cur, q) if cur < q else (q, cur))
            prev, cur = cur, q
        if len(ring) >= 3:
            polys.append([[list(p) for p in ring]])
    return polys


def _idsafe(s: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFD", str(s)).replace("ı", "i")
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return "".join(ch if ch.isalnum() else "_" for ch in t) or "x"
