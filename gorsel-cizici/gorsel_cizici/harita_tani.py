"""Görseldeki dilsiz haritayı tanıma ve temiz harita verisiyle yeniden çizme.

Ders kitabı soruları çoğu zaman dilsiz bir dünya ya da Türkiye haritası üzerine harf, nokta,
ok ve çizgilerle işaretleme yapar. Haritanın kıyılarını izlemek yerine:

  1. Görseldeki kara alanı bulunur (en geniş düz renklerden biri).
  2. Kara biçimi, Natural Earth verisinin olası izdüşüm/merkez boylamı seçenekleriyle
     karşılaştırılır; en iyi oturan ölçek ve konum bulunur (örtüşme oranıyla).
  3. Harita bu verilerle temiz vektör olarak çizilir; görseldeki işaretlemeler (harfler,
     noktalar, oklar, paralel/meridyenler) ayrıca çizim nesnesi olarak üstüne konur.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import cv2
import numpy as np

from . import harita


@dataclass
class Eslesme:
    kind: str                       # "dunya" | "turkiye"
    proj: str
    center: float
    lat0: float
    sx: float                       # görsel pikseli = sx * X + tx ; = -sy * Y + ty
    sy: float
    tx: float
    ty: float
    iou: float
    land: tuple                     # kara rengi (r, g, b)
    sea: tuple                      # deniz / zemin rengi
    land_mask: np.ndarray | None = None
    second: tuple | None = None     # komşu ülke rengi (Türkiye)
    notes: list = field(default_factory=list)
    borders: bool = False           # görselde iç sınırlar (ülke / il) var mı
    outline: tuple | None = None    # kıyı çizgisi rengi
    outline_w: float = 0.0

    def to_px(self, X, Y):
        return self.sx * X + self.tx, -self.sy * Y + self.ty


# ---------------------------------------------------------------- hedef şekiller
_CACHE = {}


def _target_rings(kind: str, proj: str, center: float, lat0: float, detail: str = "110m", holes: bool = False):
    """Kara halkaları izdüşüm biriminde (X sağa, Y yukarı)."""
    key = (kind, proj, center, lat0, detail, holes)
    if key in _CACHE:
        return _CACHE[key]
    out = []
    if kind == "dunya":
        for pl in harita.world_land(detail):
            for ring in (pl if holes else pl[:1]):   # eşleştirmede yalnız dış halkalar
                if np.mean([p[1] for p in ring]) < -60:
                    continue             # Antarktika: ders kitabı haritalarında çoğunlukla yok
                for c in harita._ring_copies(ring, center, -180.0, 180.0, -85.0, 84.0):
                    out.append(np.array([harita.project(proj, x, y) for x, y in c], float))
    else:
        for pl in harita._turkey_outline():
            for ring in pl[:1]:
                out.append(np.array([_tr_project(proj, x, y, lat0) for x, y in ring], float))
    _CACHE[key] = out
    return out


def _tr_project(proj, lon, lat, lat0):
    if proj == "mercator":
        return math.radians(lon), harita._mercator(lat)
    return math.radians(lon) * math.cos(math.radians(lat0)), math.radians(lat)


def _render(rings, sx, sy, tx, ty, shape) -> np.ndarray:
    m = np.zeros(shape, np.uint8)
    arr = []
    for r in rings:
        px = sx * r[:, 0] + tx
        py = -sy * r[:, 1] + ty
        arr.append(np.round(np.column_stack([px, py]) * 16).astype(np.int32))
    if arr:
        cv2.fillPoly(m, arr, 1, lineType=cv2.LINE_8, shift=4)
    return m


def _iou(a: np.ndarray, b: np.ndarray) -> float:
    inter = np.count_nonzero(a & b)
    uni = np.count_nonzero(a | b)
    return inter / uni if uni else 0.0


# ---------------------------------------------------------------- kara maskesi
def _candidates(rgb_small: np.ndarray):
    """(kara maskesi, kara rengi, deniz rengi) adayları."""
    lab = cv2.cvtColor(rgb_small.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)
    q = np.round(lab.reshape(-1, 3) / 5).astype(np.int32)
    keys, inv, cnt = np.unique(q, axis=0, return_inverse=True, return_counts=True)
    order = np.argsort(-cnt)
    n = lab.shape[0] * lab.shape[1]
    tops = []
    for i in order[:12]:
        if cnt[i] < 0.04 * n:
            break
        c = keys[i] * 5.0
        if any(np.linalg.norm(c - t) < 10 for t in tops):
            continue
        tops.append(c)
    if len(tops) < 2:
        return []

    def rgb_of(c):
        px = cv2.cvtColor(np.array(c, np.float32).reshape(1, 1, 3), cv2.COLOR_Lab2RGB)[0, 0]
        return tuple(int(round(float(v) * 255)) for v in np.clip(px, 0, 1))

    out = []
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    for si, sea in enumerate(tops[:2]):
        for li, land in enumerate(tops):
            if li == si:
                continue
            m = (np.linalg.norm(lab - land, axis=2) < 12).astype(np.uint8)
            # yazı, nokta ve kıyı çizgisi deliklerini kapat
            m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, ker)
            if m.mean() < 0.05:
                continue
            out.append((m, rgb_of(land), rgb_of(sea)))
    return out


# ---------------------------------------------------------------- eşleştirme
def _fit(mask: np.ndarray, rings, aspect_free: bool, refine: bool = True, start=None):
    """Maskeye en iyi oturan ölçek ve kaydırma (sx, sy, tx, ty, iou)."""
    H, W = mask.shape
    if start is not None:
        cur = start[:4]
        best = start[4]
        return _refine(mask, rings, aspect_free, cur, best)
    H, W = mask.shape
    ys, xs = np.nonzero(mask)
    if len(xs) < 50:
        return None
    allp = np.vstack(rings)
    X0, X1 = np.percentile(allp[:, 0], 0.5), np.percentile(allp[:, 0], 99.5)
    Y0, Y1 = np.percentile(allp[:, 1], 0.5), np.percentile(allp[:, 1], 99.5)
    xa, xb = np.percentile(xs, 0.5), np.percentile(xs, 99.5)
    ya, yb = np.percentile(ys, 0.5), np.percentile(ys, 99.5)
    if X1 - X0 < 1e-6 or Y1 - Y0 < 1e-6:
        return None
    sx = (xb - xa) / (X1 - X0)
    sy = (yb - ya) / (Y1 - Y0) if aspect_free else sx
    tx = xa - sx * X0
    # dikey konum: satır profillerini kaydırarak (görsel üstten/alttan kırpılmış olabilir)
    big = _render(rings, sx, sy, tx, sy * Y1 + H, (3 * H, W))
    prof_t = big.mean(axis=1)
    prof_i = mask.mean(axis=1)
    best_off, best_c = 0, -1e9
    for off in range(0, 2 * H + 1):
        seg = prof_t[off:off + H]
        if len(seg) < H:
            break
        c = -float(np.abs(seg - prof_i).sum())
        if c > best_c:
            best_c, best_off = c, off
    ty = sy * Y1 + H - best_off
    if aspect_free:
        ty = ya + sy * Y1 if abs((ya + sy * Y1) - ty) < 0.15 * H else ty
    cur = (sx, sy, tx, ty)
    best = _iou(mask > 0, _render(rings, *cur, (H, W)) > 0)
    if not refine:
        return (*cur, best)
    return _refine(mask, rings, aspect_free, cur, best)


def _refine(mask, rings, aspect_free, cur, best):
    H, W = mask.shape
    # yerel iyileştirme
    steps = [(0.04, 3.0), (0.015, 1.5), (0.005, 0.6)]
    for ds, dt in steps:
        improved = True
        it = 0
        while improved and it < 12:
            improved = False
            it += 1
            sx, sy, tx, ty = cur
            trials = []
            for f in (1 - ds, 1 + ds):
                # ölçeği görüntü merkezine göre değiştir (konum kaymasın)
                cx, cy = W / 2, H / 2
                nsx, nsy = sx * f, (sy * f if not aspect_free else sy)
                trials.append((nsx, nsy, cx - (cx - tx) * f, ty if aspect_free else cy - (cy - ty) * f))
                if aspect_free:
                    trials.append((sx, sy * f, tx, cy - (cy - ty) * f))
            for d in (-dt, dt):
                trials.append((sx, sy, tx + d, ty))
                trials.append((sx, sy, tx, ty + d))
            for t in trials:
                v = _iou(mask > 0, _render(rings, *t, (H, W)) > 0)
                if v > best + 1e-4:
                    best, cur, improved = v, t, True
    return (*cur, best)


def _edge_f1(mask, rings, sx, sy, tx, ty) -> float:
    """Kıyı çizgilerinin örtüşmesi (2 piksel hoşgörüyle)."""
    ker = np.ones((3, 3), np.uint8)
    rend = _render(rings, sx, sy, tx, ty, mask.shape)
    e1 = cv2.morphologyEx(mask, cv2.MORPH_GRADIENT, ker) > 0
    e2 = cv2.morphologyEx(rend, cv2.MORPH_GRADIENT, ker) > 0
    # görselin kenarına denk gelen (kırpılmış) sınırları sayma
    e1[:2, :] = e1[-2:, :] = False
    e1[:, :2] = e1[:, -2:] = False
    e2[:2, :] = e2[-2:, :] = False
    e2[:, :2] = e2[:, -2:] = False
    if not e1.any() or not e2.any():
        return 0.0
    d = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    p = float((e2 & (cv2.dilate(e1.astype(np.uint8), d) > 0)).sum()) / float(e2.sum())
    r = float((e1 & (cv2.dilate(e2.astype(np.uint8), d) > 0)).sum()) / float(e1.sum())
    return 2 * p * r / max(p + r, 1e-9)


def tani(rgb: np.ndarray) -> Eslesme | None:
    """Görsel bir dilsiz dünya ya da Türkiye haritası mı; öyleyse eşleşmeyi döndür."""
    H0, W0 = rgb.shape[:2]
    if min(H0, W0) < 80:
        return None
    k = min(1.0, 420.0 / max(H0, W0))
    small = cv2.resize(rgb, (max(1, int(W0 * k)), max(1, int(H0 * k))), interpolation=cv2.INTER_AREA) if k < 1 else rgb
    cands = _candidates(small)
    if not cands:
        return None
    # önce bütün seçenekler kaba eşleştirilir, yalnız en umutlu birkaçı ince ayarlanır
    rough = []
    for ci, (m, land, sea) in enumerate(cands):
        for kind in ("dunya", "turkiye"):
            if kind == "dunya":
                opts = [(p, c, 0.0) for p in ("miller", "esdik", "robinson", "mercator")
                        for c in (0.0, 10.0, 20.0, -10.0, 30.0, 150.0, 160.0)]
            else:
                opts = [("esdik", 0.0, 39.0), ("mercator", 0.0, 0.0)]
            for proj, center, lat0 in opts:
                rings = _target_rings(kind, proj, center, lat0)
                r = _fit(m, rings, True, refine=False)
                if r is not None:
                    rough.append((r[4], ci, kind, proj, center, lat0, r))
    rough.sort(key=lambda t: -t[0])
    best = None
    for iou0, ci, kind, proj, center, lat0, r in rough[:4]:
        if iou0 < 0.45:
            break
        m, land, sea = cands[ci]
        rings = _target_rings(kind, proj, center, lat0)
        sx, sy, tx, ty, iou = _fit(m, rings, True, start=r)
        if best is None or iou > best.iou:
            best = Eslesme(kind, proj, center, lat0, sx / k, sy / k, tx / k, ty / k, iou, land, sea)
            best.land_mask = m
    if best is not None and best.kind == "dunya":
        # orta boylamı ince ayarla (kenarlarda bölünen kıtalar doğru yere düşsün)
        m = best.land_mask
        for dc in (-10.0, -5.0, 5.0, 10.0):
            c2 = best.center + dc
            rings = _target_rings("dunya", best.proj, c2, 0.0)
            sx, sy = best.sx * k, best.sy * k
            start = (sx, sy, best.tx * k + math.radians(dc) * sx, best.ty * k,
                     _iou(m > 0, _render(rings, sx, sy, best.tx * k + math.radians(dc) * sx, best.ty * k, m.shape) > 0))
            r = _fit(m, rings, True, start=start)
            if r[4] > best.iou + 0.002:
                best.center, best.iou = c2, r[4]
                best.sx, best.sy, best.tx, best.ty = r[0] / k, r[1] / k, r[2] / k, r[3] / k
    if best is None or best.iou < 0.78:
        return None
    # oran makul olmalı ve kıyı çizgileri de örtüşmeli (sütun, kutu gibi şekiller elensin)
    ratio = best.sy / best.sx
    if not (0.75 < ratio < 1.35):
        return None
    if _edge_f1(best.land_mask, _target_rings(best.kind, best.proj, best.center, best.lat0),
                best.sx * k, best.sy * k, best.tx * k, best.ty * k) < (0.55 if best.kind == "dunya" else 0.65):
        return None
    best.notes.append(f"{'Dünya' if best.kind == 'dunya' else 'Türkiye'} haritası tanındı "
                      f"({harita.PROJECTIONS.get(best.proj, best.proj).split(' (')[0]}, uyum %{best.iou * 100:.0f})")
    return best


# ---------------------------------------------------------------- yeniden çizim
def _clip_px(pts: np.ndarray, W: float, H: float):
    r = [tuple(p) for p in pts]
    r = harita._clip(r, 0, 0.0, True)
    r = harita._clip(r, 0, W, False)
    r = harita._clip(r, 1, 0.0, True)
    r = harita._clip(r, 1, H, False)
    return r


def _fmt(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def _hex(c) -> str:
    return "#{:02X}{:02X}{:02X}".format(*[int(v) for v in c])


def _rings_d(e: Eslesme, rings_geo, W, H, detail_center=None) -> str:
    d = []
    for ring in rings_geo:
        pts = np.array(ring, float)
        X = np.array([e.to_px(x, y) for x, y in pts])
        c = _clip_px(X, W, H)
        if len(c) < 3:
            continue
        out = [c[0]]
        for p in c[1:]:
            if abs(p[0] - out[-1][0]) + abs(p[1] - out[-1][1]) > 0.25:
                out.append(p)
        if len(out) >= 3:
            d.append("M" + "L".join(f"{_fmt(x)} {_fmt(y)}" for x, y in out) + "Z")
    return "".join(d)


def harita_svg(e: Eslesme, W: int, H: int, outline=(0, 0, 0), outline_w: float = 0.8,
               borders: bool = False, detail: str = "50m") -> str:
    """Eşleşen haritayı görselin piksel koordinatında SVG grubu olarak çiz."""
    parts = []
    if e.kind == "dunya":
        rings = []
        for pl in harita.world_land(detail):
            for ring in pl:
                for c in harita._ring_copies(ring, e.center, -180.0, 180.0, -85.0, 84.0):
                    rings.append([harita.project(e.proj, x, y) for x, y in c])
        d = _rings_d(e, rings, W, H)
        parts.append(f'<path id="Kara" d="{d}" fill="{_hex(e.land)}" stroke="{_hex(outline)}" '
                     f'stroke-width="{_fmt(outline_w)}" stroke-linejoin="round" fill-rule="evenodd"/>')
        if borders:
            bd = []
            for _name, polys in harita.world_countries(detail):
                g = []
                for pl in polys:
                    for ring in pl:
                        for c in harita._ring_copies(ring, e.center, -180.0, 180.0, -85.0, 84.0):
                            g.append([harita.project(e.proj, x, y) for x, y in c])
                bd.append(_rings_d(e, g, W, H))
            parts.append(f'<path id="Sinirlar" d="{"".join(bd)}" fill="none" stroke="{_hex(outline)}" '
                         f'stroke-width="{_fmt(outline_w * 0.6)}" stroke-linejoin="round"/>')
    else:
        data = harita.turkey()
        if e.second is not None:
            for kom in data["komsular"]:
                g = [[_tr_project(e.proj, x, y, e.lat0) for x, y in ring] for pl in kom["p"] for ring in pl]
                dd = _rings_d(e, g, W, H)
                if dd:
                    parts.append(f'<path d="{dd}" fill="{_hex(e.second)}" stroke="{_hex(outline)}" '
                                 f'stroke-width="{_fmt(outline_w * 0.6)}" stroke-linejoin="round" fill-rule="evenodd"/>')
        if borders:
            for il in data["iller"]:
                g = [[_tr_project(e.proj, x, y, e.lat0) for x, y in ring] for pl in il["p"] for ring in pl]
                dd = _rings_d(e, g, W, H)
                if dd:
                    parts.append(f'<path d="{dd}" fill="{_hex(e.land)}" stroke="{_hex(outline)}" '
                                 f'stroke-width="{_fmt(outline_w * 0.5)}" stroke-linejoin="round" fill-rule="evenodd"/>')
        g = [[_tr_project(e.proj, x, y, e.lat0) for x, y in ring] for pl in harita._turkey_outline() for ring in pl]
        d = _rings_d(e, g, W, H)
        fill = "none" if borders else _hex(e.land)
        parts.append(f'<path id="Turkiye" d="{d}" fill="{fill}" stroke="{_hex(outline)}" '
                     f'stroke-width="{_fmt(outline_w)}" stroke-linejoin="round" fill-rule="evenodd"/>')
    return '<g id="Harita">' + "".join(parts) + "</g>"


def _border_lines(e: Eslesme, shape, thickness: int = 1) -> np.ndarray:
    H, W = shape
    lines = np.zeros((H, W), np.uint8)
    if e.kind == "dunya":
        for _name, polys in harita.world_countries("50m"):
            for pl in polys:
                for ring in pl:
                    for c in harita._ring_copies(ring, e.center, -180.0, 180.0, -85.0, 84.0):
                        P = np.array([e.to_px(*harita.project(e.proj, x, y)) for x, y in c])
                        cv2.polylines(lines, [np.round(P * 16).astype(np.int32)], True, 1, thickness=thickness, shift=4)
    else:
        for il in harita.turkey()["iller"]:
            for pl in il["p"]:
                for ring in pl:
                    P = np.array([e.to_px(*_tr_project(e.proj, x, y, e.lat0)) for x, y in ring])
                    cv2.polylines(lines, [np.round(P * 16).astype(np.int32)], True, 1, thickness=thickness, shift=4)
    return lines


def _chamfer_refine(e: Eslesme, lab: np.ndarray) -> None:
    """Tam çözünürlükte kıyı çizgisini görseldeki çizgiye (ya da kara kenarına) birebir oturt."""
    H, W = lab.shape[:2]
    land = np.linalg.norm(lab - cv2.cvtColor(np.array(e.land, np.float32).reshape(1, 1, 3) / 255.0,
                                             cv2.COLOR_RGB2Lab)[0, 0], axis=2) < 14
    edge = cv2.morphologyEx(land.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    dark = lab[:, :, 0] < 72
    target = edge | dark
    dist = cv2.distanceTransform((~target).astype(np.uint8), cv2.DIST_L2, 3)
    rings = _target_rings(e.kind, e.proj, e.center if e.kind == "dunya" else 0.0, e.lat0, "50m" if e.kind == "dunya" else "110m")
    pts = np.vstack(rings) if rings else np.zeros((0, 2))
    if len(pts) > 20000:
        pts = pts[:: len(pts) // 20000 + 1]

    def cost(sx, sy, tx, ty):
        x = sx * pts[:, 0] + tx
        y = -sy * pts[:, 1] + ty
        ok = (x >= 0) & (x < W - 1) & (y >= 0) & (y < H - 1)
        if ok.sum() < 30:
            return 1e9
        d = dist[y[ok].astype(int), x[ok].astype(int)]
        return float(np.minimum(d, 6.0).mean())

    cur = (e.sx, e.sy, e.tx, e.ty)
    best = cost(*cur)
    cx, cy = W / 2, H / 2
    for ds, dt in ((0.01, 2.0), (0.004, 1.0), (0.0015, 0.5), (0.0006, 0.25)):
        improved, it = True, 0
        while improved and it < 15:
            improved, it = False, it + 1
            sx, sy, tx, ty = cur
            trials = []
            for f in (1 - ds, 1 + ds):
                trials.append((sx * f, sy, cx - (cx - tx) * f, ty))
                trials.append((sx, sy * f, tx, cy - (cy - ty) * f))
                trials.append((sx * f, sy * f, cx - (cx - tx) * f, cy - (cy - ty) * f))
            for d in (-dt, dt):
                trials += [(sx, sy, tx + d, ty), (sx, sy, tx, ty + d)]
            for t in trials:
                c = cost(*t)
                if c < best - 1e-4:
                    best, cur, improved = c, t, True
    e.sx, e.sy, e.tx, e.ty = cur


def hazirla(rgb: np.ndarray, e: Eslesme) -> None:
    """Kıyı çizgisinin rengi/kalınlığı ve iç sınırların varlığı."""
    H, W = rgb.shape[:2]
    lab = cv2.cvtColor(rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)
    # kara ve deniz rengi: kümenin ortası değil, görseldeki piksellerin ortancası
    for attr in ("land", "sea"):
        c = getattr(e, attr)
        cl = cv2.cvtColor(np.array(c, np.float32).reshape(1, 1, 3) / 255.0, cv2.COLOR_RGB2Lab)[0, 0]
        m = np.linalg.norm(lab - cl, axis=2) < 10
        if m.sum() > 50:
            setattr(e, attr, tuple(int(v) for v in np.median(rgb[m], axis=0)))
    _chamfer_refine(e, lab)
    rings = _target_rings(e.kind, e.proj, e.center, e.lat0, "50m", holes=True) if e.kind == "dunya" else _target_rings(e.kind, e.proj, 0.0, e.lat0)
    band = np.zeros((H, W), np.uint8)
    for r in rings:
        P = np.column_stack([e.sx * r[:, 0] + e.tx, -e.sy * r[:, 1] + e.ty])
        cv2.polylines(band, [np.round(P * 16).astype(np.int32)], True, 1, thickness=3, lineType=cv2.LINE_8, shift=4)
    band = band > 0
    dark = lab[:, :, 0] < 72
    if band.any() and dark[band].mean() > 0.08:
        e.outline = tuple(int(v) for v in np.median(rgb[band & dark], axis=0))
        e.outline_w = float(np.clip(dark[band].sum() / max(1.0, band.sum() / 3.0), 0.5, 3.0))
    lines = _border_lines(e, (H, W))
    far = (lines > 0) & ~(cv2.dilate(band.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0)
    if far.sum() >= 50:
        dark_near = cv2.dilate(dark.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        e.borders = float(dark_near[far].mean()) > 0.45


def harita_kalintisi(rgb: np.ndarray, e: Eslesme, outline_px: float = 4.0) -> np.ndarray:
    """Haritanın kendisinden gelen pikselleri (kara, deniz, kıyı çizgisi) zemin rengiyle boya.

    Geriye yalnız işaretlemeler (harf, nokta, ok, paralel/meridyen) kalır.
    """
    H, W = rgb.shape[:2]
    lab = cv2.cvtColor(rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)

    def near(c, t=14):
        c_lab = cv2.cvtColor(np.array(c, np.float32).reshape(1, 1, 3) / 255.0, cv2.COLOR_RGB2Lab)[0, 0]
        return np.linalg.norm(lab - c_lab, axis=2) < t

    out = rgb.copy()
    land = near(e.land)
    sea = near(e.sea)
    # kıyı çizgisi: eşleşen haritanın kıyısına yakın, koyu pikseller
    if e.kind == "dunya":
        rings = _target_rings("dunya", e.proj, e.center, 0.0, "50m", holes=True)
    else:
        rings = _target_rings("turkiye", e.proj, 0.0, e.lat0)
    edge = np.zeros((H, W), np.uint8)
    th = max(2, int(round(outline_px)))
    for r in rings:
        P = np.column_stack([e.sx * r[:, 0] + e.tx, -e.sy * r[:, 1] + e.ty])
        cv2.polylines(edge, [np.round(P * 16).astype(np.int32)], True, 1, thickness=th, lineType=cv2.LINE_8, shift=4)
    if e.borders:
        edge |= _border_lines(e, (H, W), thickness=th)
    band = edge > 0
    chroma = np.hypot(lab[:, :, 1], lab[:, :, 2])

    def chroma_of(c):
        q = cv2.cvtColor(np.array(c, np.float32).reshape(1, 1, 3) / 255.0, cv2.COLOR_RGB2Lab)[0, 0]
        return float(np.hypot(q[1], q[2]))

    # renkli işaretler (kırmızı nokta, mavi ok…) kıyı çizgisi değildir: hiç silinmez. Eşik kara ve
    # deniz renginin doygunluğunun üstünde (bej kara üstündeki koyu sınırlar kahverengi görünür)
    cmin = max(28.0, chroma_of(e.land) + 18, chroma_of(e.sea) + 18)
    colored = (chroma > cmin) & ~land & ~sea
    rest = (~land & ~sea & ~colored).astype(np.uint8)
    # Kıyı bandındaki kara/deniz dışı pikseller kıyı çizgisidir; ama kıyıya değen küçük
    # işaretler (harf, nokta) bandın içinde kalmayan parçalarıyla birlikte korunur.
    n, cc, st, _ = cv2.connectedComponentsWithStats(rest, connectivity=8)
    in_band = np.bincount(cc[band].ravel(), minlength=n)
    keep = np.zeros(n, bool)
    for i in range(1, n):
        x, y, ww, hh, area = st[i]
        if max(ww, hh) <= 40 and in_band[i] < 0.85 * area:
            keep[i] = True
    # uzun düz yatay/dikey çizgiler (meridyen, paralel) kıyıyı kesse de silinmez
    ink = (rest > 0) | colored
    L = max(25, int(0.08 * min(H, W)))
    vert = cv2.morphologyEx(ink.astype(np.uint8), cv2.MORPH_OPEN, np.ones((L, 1), np.uint8))
    horz = cv2.morphologyEx(ink.astype(np.uint8), cv2.MORPH_OPEN, np.ones((1, L), np.uint8))
    straight = cv2.dilate(vert | horz, np.ones((3, 3), np.uint8)) > 0
    coast = band & ~keep[cc] & (rest > 0) & ~straight
    expl = land | sea | coast
    out[expl] = np.array(e.sea, np.uint8)
    return out


def harita_cizimi(rgb: np.ndarray, e: Eslesme) -> str:
    """Eşleşen haritayı görselin kıyı çizgisi, sınırları ve deniz rengiyle çiz."""
    H, W = rgb.shape[:2]
    sea_white = min(e.sea) > 235
    body = harita_svg(e, W, H, outline=e.outline or e.land, outline_w=e.outline_w if e.outline else 0.0,
                      borders=e.borders, detail="50m")
    if not sea_white:
        body = body.replace('<g id="Harita">', f'<g id="Harita"><rect id="Deniz" width="{W}" height="{H}" fill="{_hex(e.sea)}"/>', 1)
    return body
