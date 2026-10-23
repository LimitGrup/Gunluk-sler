"""İzlenmiş şekilleri bir tasarımcının çizeceği gibi sadeleştirir ("çizime çevirme").

Görselden çıkarılan şekiller kenar izinden gelir; Illustrator'da "görüntü izleme" gibi çok
noktalı yollar olur. Bu adım onları gerçek çizim nesnelerine çevirir:

  - Dikdörtgene benzeyen dolgular (sütunlar, kutular) <rect> olur; degrade korunur.
  - Bir dikdörtgenin kenarını izleyen çizgiler o dikdörtgenin konturu olur (dolgu ve kenar
    tek nesne).
  - Az köşeli dolgular çokgen olur.
  - Aynı doğru üzerindeki parça çizgiler tek çizgi olur.
  - Kenar yumuşatmasından kalan minik ara renkli kırıntılar atılır.
  - Eğriler daha az noktayla yeniden yazılır.
  - Daire, elips, yarım daire gibi şekiller tek nesne olur: dolgu ve kontur birlikte, gölgesi
    dolguya katılır (güneş: sarı daire + turuncu kontur + kesikli ışın halkası).
  - Düzenli dizilmiş kısa çizgiler tek kesikli çizgi, kapalı çerçeveler dikdörtgen olur.
"""
from __future__ import annotations

import math
import re

import numpy as np

from . import egri, sadakat, sekil


def _area(P: np.ndarray) -> float:
    return 0.5 * abs(float(np.dot(P[:, 0], np.roll(P[:, 1], 1)) - np.dot(P[:, 1], np.roll(P[:, 0], 1))))


def _poly_of(e):
    kind, polys = sadakat.element_polys(e)
    return kind, polys


def _f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


# ---------------------------------------------------------------- dolgular
def _rectify(e) -> bool:
    """Dikdörtgene benzeyen dolguyu <rect> yap."""
    if e.prim:
        return e.prim["type"] == "rect"
    _k, polys = _poly_of(e)
    if len(polys) != 1:
        return False
    P = polys[0][0]
    if len(P) < 4:
        return False
    x0, y0 = P.min(axis=0)
    x1, y1 = P.max(axis=0)
    w, h = x1 - x0, y1 - y0
    if w < 1.5 or h < 1.5:
        return False
    if _area(P) < 0.86 * w * h:
        return False
    if not _rect_cover_ok(P, x0, y0, x1, y1):
        return False
    e.prim = {"type": "rect", "x": float(x0), "y": float(y0), "w": float(w), "h": float(h)}
    e.d = ""
    return True


def _rect_cover_ok(P, x0, y0, x1, y1, polys=None) -> bool:
    """Şekil kutusunu dolduruyor mu: eksik kalan yerler yalnız ince kesikler (üstünden geçen
    çizgi) olabilir; L ya da T biçimi gibi kalın eksikler dikdörtgen sayılmaz."""
    import cv2
    k = 3
    W, H = int(math.ceil((x1 - x0) * k)) + 1, int(math.ceil((y1 - y0) * k)) + 1
    if W * H > 9_000_000 or W < 3 or H < 3:
        return False
    m = np.zeros((H, W), np.uint8)
    arr = [np.round((q - [x0, y0]) * k * 16).astype(np.int32) for q in (polys or [P]) if len(q) >= 3]
    cv2.fillPoly(m, arr, 1, shift=4)
    if m.mean() < 0.86:
        return False
    miss = (1 - m).astype(np.uint8)
    if not miss.any():
        return True
    # eksik kısımların kalınlığı (kenardan içeri): 3 pikselden ince olmalı
    dt = cv2.distanceTransform(np.pad(miss, 1, constant_values=0), cv2.DIST_L2, 3)
    return float(dt.max()) / k <= 1.8


def _rectify_occluded(fills: list, strokes: list) -> None:
    """Üstüne küçük bir şekil (nokta, çizgi) binen sütun dikdörtgen sayılmadıysa: eksik kalan yeri
    üstteki şekiller kapatıyorsa yine dikdörtgendir (nokta zaten üstte çizilir)."""
    import cv2
    cands = [e for e in fills if not e.prim and e.layer != "harf" and not e.grad and e.area >= 30]
    if not cands:
        return
    tops = [e for e in fills if e.layer != "harf"] + [s for s in strokes]
    for e in cands:
        _k, polys = _poly_of(e)
        if len(polys) != 1 or len(polys[0][0]) < 4:
            continue
        P = polys[0][0]
        x0, y0 = P.min(axis=0)
        x1, y1 = P.max(axis=0)
        w, h = x1 - x0, y1 - y0
        if w < 3 or h < 3 or _area(P) < 0.6 * w * h:
            continue
        # en az üç kenarı kutunun kenarı boyunca düz olmalı (sütun); yuvarlak şekiller değil
        Q = sadakat_dense(P, True)
        straight = 0
        for axis, val, span in ((1, y0, w), (1, y1, w), (0, x0, h), (0, x1, h)):
            on = np.abs(Q[:, axis] - val) <= 1.0
            if on.sum() > 1 and np.ptp(Q[on, 1 - axis]) >= 0.8 * span:
                straight += 1
        if straight < 3:
            continue
        k = 3
        W, H = int(math.ceil(w * k)) + 1, int(math.ceil(h * k)) + 1
        if W * H > 4_000_000:
            continue
        m = np.zeros((H, W), np.uint8)
        cv2.fillPoly(m, [np.round((P - [x0, y0]) * k * 16).astype(np.int32)], 1, shift=4)
        occ = np.zeros_like(m)
        for o in tops:
            if o is e or o.area > e.area:
                continue
            b = o.bbox
            if b[2] < x0 or b[0] > x1 or b[3] < y0 or b[1] > y1:
                continue
            occ |= sadakat.rasterize(o, k, x0 - 0.5 + 0.5 / k, y0 - 0.5 + 0.5 / k, (H, W))
        if not occ.any():
            continue
        occ = cv2.dilate(occ, np.ones((3, 3), np.uint8))
        full = m | occ
        if full.mean() < 0.9:
            continue
        miss = (1 - full).astype(np.uint8)
        if miss.any():
            dt = cv2.distanceTransform(np.pad(miss, 1), cv2.DIST_L2, 3)
            if float(dt.max()) / k > 1.8:
                continue
        e.prim = {"type": "rect", "x": float(x0), "y": float(y0), "w": float(w), "h": float(h)}
        e.d = ""


def _polygonize(e) -> None:
    """Az köşeli dolguyu çokgen yap (köşe sayısı az ve alan korunuyorsa)."""
    if e.prim or e.layer == "harf":
        return
    _k, polys = _poly_of(e)
    if len(polys) != 1:
        return
    P = polys[0][0]
    if len(P) < 6:
        return
    A = _area(P)
    if A < 20:
        return
    v = egri.rdp(np.vstack([P, P[:1]]), 0.8)[:-1]
    if 3 <= len(v) <= 10 and abs(_area(v) - A) <= 0.04 * A:
        # kenarları gerçekten düz mü: her nokta çokgene yakın
        e.prim = {"type": "polygon", "pts": [(float(x), float(y)) for x, y in v]}
        e.d = ""


def _similar_fill(a, b) -> bool:
    if (a.grad is None) != (b.grad is None):
        return False
    if a.grad is None:
        return np.linalg.norm(np.array(a.color, float) - np.array(b.color, float)) < 12
    ga, gb = a.grad, b.grad
    if ga["type"] != gb["type"] or ga["type"] != "linear":
        return False
    va = np.array([ga["x2"] - ga["x1"], ga["y2"] - ga["y1"]])
    vb = np.array([gb["x2"] - gb["x1"], gb["y2"] - gb["y1"]])
    na, nb = np.hypot(*va), np.hypot(*vb)
    if na < 1e-6 or nb < 1e-6 or abs(float(va @ vb) / (na * nb)) < 0.97:
        return False
    # aynı yönde geçiş; parçalar geçiş yönünde aynı aralığı kaplar (aynı sütunun parçaları)
    horiz = abs(va[0]) >= abs(va[1])
    i0, i1 = (0, 2) if horiz else (1, 3)
    sa, sb = (a.bbox[i0], a.bbox[i1]), (b.bbox[i0], b.bbox[i1])
    return abs(sa[0] - sb[0]) <= 2.5 and abs(sa[1] - sb[1]) <= 2.5


def _union_rects(fills: list) -> list:
    """İnce bir çizginin böldüğü aynı renkli/aynı degradeli komşu parçaları tek dikdörtgen yap."""
    _dead = []
    # yalnız degradeli ya da dikdörtgen olmuş, en az birkaç piksellik parçalar aday
    alive = [e for e in fills if e.layer != "harf" and (e.grad is not None or (e.prim and e.prim.get("type") == "rect"
                                                                                 and not e.prim.get("rot")))
             and _size(e) >= 3]
    if len(alive) > 1500:
        alive = alive[:1500]
    changed = True
    while changed:
        changed = False
        order = sorted(range(len(alive)), key=lambda q: alive[q].bbox[0] if alive[q] is not None else 0)
        for oi, i in enumerate(order):
            a = alive[i]
            if a is None:
                continue
            for j in order[oi + 1:]:
                b = alive[j]
                if b is None:
                    continue
                if b.bbox[0] > a.bbox[2] + 3:
                    break           # x'e göre sıralı: daha sağdakiler değmez
                if not _similar_fill(a, b):
                    continue
                ax0, ay0, ax1, ay1 = a.bbox
                bx0, by0, bx1, by1 = b.bbox
                gapx = max(bx0 - ax1, ax0 - bx1)
                gapy = max(by0 - ay1, ay0 - by1)
                if gapx > 3 or gapy > 3:
                    continue
                x0, y0, x1, y1 = min(ax0, bx0), min(ay0, by0), max(ax1, bx1), max(ay1, by1)
                W, H = int(math.ceil(x1 - x0)) + 2, int(math.ceil(y1 - y0)) + 2
                if W * H > 4_000_000:
                    continue
                allp = []
                for e in (a, b):
                    _k, polys = _poly_of(e)
                    allp += [p for p, _c in polys if len(p) >= 3]
                if allp and _rect_cover_ok(None, x0, y0, x1, y1, polys=allp):
                    a.prim = {"type": "rect", "x": float(x0), "y": float(y0), "w": float(x1 - x0), "h": float(y1 - y0)}
                    a.d = ""
                    a.bbox = (x0, y0, x1, y1)
                    a.area = (x1 - x0) * (y1 - y0)
                    if a.grad and b.grad and a.grad["type"] == "linear":
                        # iki parçanın geçişini birleşik alana yay
                        g = a.grad
                        if abs(g["y2"] - g["y1"]) < abs(g["x2"] - g["x1"]):
                            g["y1"] = g["y2"] = (y0 + y1) / 2
                        else:
                            g["x1"] = g["x2"] = (x0 + x1) / 2
                    _dead.append(b)
                    alive[j] = None
                    changed = True
    dead = {id(e) for e in _dead}
    return [e for e in fills if id(e) not in dead]


def _frames(fills: list, strokes: list):
    """İçi boş dikdörtgen çerçeve olarak izlenmiş kenarları kontura çevir."""
    from .vektor import Element
    out_f, extra_s = [], []
    for e in fills:
        if e.prim or e.layer == "harf" or e.grad:
            out_f.append(e)
            continue
        _k, polys = _poly_of(e)
        if len(polys) != 2:
            out_f.append(e)
            continue
        polys = sorted(polys, key=lambda t: -_area(t[0]))
        P, Q = polys[0][0], polys[1][0]
        bp = (*P.min(axis=0), *P.max(axis=0))
        bq = (*Q.min(axis=0), *Q.max(axis=0))
        t = [bq[0] - bp[0], bq[1] - bp[1], bp[2] - bq[2], bp[3] - bq[3]]
        if min(t) <= 0 or max(t) - min(t) > 1.2 or max(t) > 4:
            out_f.append(e)
            continue
        if _area(P) < 0.9 * (bp[2] - bp[0]) * (bp[3] - bp[1]) or _area(Q) < 0.85 * (bq[2] - bq[0]) * (bq[3] - bq[1]):
            out_f.append(e)
            continue
        wd = float(np.mean(t))
        x0, y0, x1, y1 = bp[0] + wd / 2, bp[1] + wd / 2, bp[2] - wd / 2, bp[3] - wd / 2
        # çerçeve dört kenar çizgisi olarak eklenir; içinde dolgu varsa sonra ona birleşir
        for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            extra_s.append(Element("stroke", e.color, prim={"type": "line", "x1": a[0], "y1": a[1], "x2": b[0], "y2": b[1]},
                                   width=wd, bbox=(min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))))
    return out_f, strokes + extra_s


# ---------------------------------------------------------------- kenar + dolgu
def _merge_outlines(fills: list, strokes: list) -> set:
    """Dikdörtgenin kenarını izleyen çizgileri o dikdörtgenin konturu yap. Dönüş: atılacak çizgiler."""
    used = set()
    cell = 32.0
    grid = {}
    for i, s in enumerate(strokes):
        x0, y0, x1, y1 = s.bbox
        for gx in range(int(x0 // cell), int(x1 // cell) + 1):
            for gy in range(int(y0 // cell), int(y1 // cell) + 1):
                grid.setdefault((gx, gy), []).append(i)
    for r in fills:
        if not (r.prim and r.prim.get("type") == "rect") or r.prim.get("rot") or r.stroke is not None:
            continue
        x, y, w, h = r.prim["x"], r.prim["y"], r.prim["w"], r.prim["h"]
        if w < 3 or h < 3:
            continue
        near_ids = set()
        for gx in range(int((x - 2) // cell), int((x + w + 2) // cell) + 1):
            for gy in range(int((y - 2) // cell), int((y + h + 2) // cell) + 1):
                near_ids.update(grid.get((gx, gy), ()))
        cands = []
        for i in sorted(near_ids):
            s = strokes[i]
            if i in used or s.dash:
                continue
            bx0, by0, bx1, by1 = s.bbox
            if bx0 < x - 3 or by0 < y - 3 or bx1 > x + w + 3 or by1 > y + h + 3:
                continue        # dikdörtgenin dışına taşan çizgi onun kenarı olamaz
            _k, polys = _poly_of(s)
            if not polys:
                continue
            pts = np.vstack([sadakat_dense(p, c) for p, c in polys])
            tol = max(1.4, 0.6 * s.width + 1.0)
            dx = np.minimum(np.abs(pts[:, 0] - x), np.abs(pts[:, 0] - (x + w)))
            dy = np.minimum(np.abs(pts[:, 1] - y), np.abs(pts[:, 1] - (y + h)))
            inside_x = (pts[:, 0] >= x - tol) & (pts[:, 0] <= x + w + tol)
            inside_y = (pts[:, 1] >= y - tol) & (pts[:, 1] <= y + h + tol)
            near = ((dx <= tol) & inside_y) | ((dy <= tol) & inside_x)
            if near.mean() >= 0.97:
                cands.append((i, s, pts))
        if not cands:
            continue
        allp = np.vstack([p for _i, _s, p in cands])
        tol = max(1.4, 0.6 * float(np.median([s.width for _i, s, _p in cands])) + 1.0)
        sides = {}
        for name, axis, val, lo, hi in (("l", 0, x, y, y + h), ("r", 0, x + w, y, y + h),
                                        ("t", 1, y, x, x + w), ("b", 1, y + h, x, x + w)):
            on = np.abs(allp[:, axis] - val) <= tol
            other = allp[on][:, 1 - axis]
            if len(other) == 0:
                sides[name] = (0.0, val)
                continue
            bins = np.zeros(max(1, int(math.ceil(hi - lo))), bool)
            idx = np.clip(((other - lo)).astype(int), 0, len(bins) - 1)
            bins[idx] = True
            sides[name] = (float(bins.mean()), float(np.median(allp[on][:, axis])))
        covered = [k for k, (c, _v) in sides.items() if c >= 0.7]
        if len(covered) < 3:
            continue
        # çizgi orta hattı: kapsanan kenarlarda çizginin yeri, diğerinde dolgunun kenarı
        L = sides["l"][1] if sides["l"][0] >= 0.7 else x
        R = sides["r"][1] if sides["r"][0] >= 0.7 else x + w
        T = sides["t"][1] if sides["t"][0] >= 0.7 else y
        B = sides["b"][1] if sides["b"][0] >= 0.7 else y + h
        sw = float(np.median([s.width for _i, s, _p in cands]))
        col = cands[0][1].color
        r.prim = {"type": "rect", "x": min(L, R), "y": min(T, B), "w": abs(R - L), "h": abs(B - T)}
        r.stroke = col
        r.stroke_width = sw
        for i, _s, _p in cands:
            used.add(i)
    return used


def _on_blend(c, a, b, tol=22.0) -> bool:
    """c, a ile b'nin karışımı (kenar yumuşatma gölgesi) mi."""
    c, a, b = (np.array(v, float) for v in (c, a, b))
    ab = a - b
    n = float(ab @ ab)
    if n < 1e-6:
        return float(np.linalg.norm(c - a)) < tol
    t = float(np.clip((c - b) @ ab / n, 0, 1))
    return float(np.linalg.norm(c - (b + t * ab))) < tol


def _rect_strokes(fills: list, strokes: list, background) -> list:
    """Aynı renkteki sütunların çoğu konturluysa hepsi aynı konturu alır; kenarlarının üstünde
    kalan parça çizgiler (konturun kopukları, kenar gölgeleri) silinir."""
    rects = [r for r in fills if r.prim and r.prim.get("type") in ("rect", "rrect") and not r.prim.get("rot")
             and r.layer != "harf"
             and min(r.prim["w"], r.prim["h"]) >= 3]
    groups = []
    for r in rects:
        for g in groups:
            if _de(g[0].color, r.color) < 10 and bool(g[0].grad) == bool(r.grad):
                g.append(r)
                break
        else:
            groups.append([r])
    for g in groups:
        st = [r for r in g if r.stroke is not None]
        if len(g) < 2 or len(st) < max(2, 0.4 * len(g)):
            continue
        votes = []
        for r in st:
            for v in votes:
                if _de(v[0].stroke, r.stroke) < 12:
                    v.append(r)
                    break
            else:
                votes.append([r])
        best = max(votes, key=len)
        if len(best) < 2:
            continue
        col = best[0].stroke
        wd = float(np.median([r.stroke_width for r in best]))
        for r in g:
            r.stroke, r.stroke_width = col, wd
    stroked = [r for r in rects if r.stroke is not None]
    if not stroked:
        return strokes
    import cv2
    polys = {id(r): sekil.prim_points(r.prim).astype(np.float32) for r in stroked}
    out = []
    for sk in strokes:
        if sk.kind != "stroke" or (sk.dash and _size(sk) > 30):
            out.append(sk)
            continue
        kind, pp = sadakat.element_polys(sk)
        if not pp:
            out.append(sk)
            continue
        Q = np.vstack([sadakat_dense(p_, c_) for p_, c_ in pp])
        bx0, by0 = Q.min(axis=0)
        bx1, by1 = Q.max(axis=0)
        hit = False
        for r in stroked:
            x, y, w, h = r.prim["x"], r.prim["y"], r.prim["w"], r.prim["h"]
            if bx0 < x - 4 or by0 < y - 4 or bx1 > x + w + 4 or by1 > y + h + 4:
                continue
            # rengi kutunun konturu ya da onun zemine/dolguya karışımı olmalı
            if not (_de(sk.color, r.stroke) < 25 or _on_blend(sk.color, r.stroke, background)
                    or _on_blend(sk.color, r.stroke, r.color)):
                continue
            tol = max(1.6, 0.6 * max(sk.width, r.stroke_width) + 1.0)
            pg = polys[id(r)]
            step = max(1, len(Q) // 60)
            dd = np.array([abs(cv2.pointPolygonTest(pg, (float(qx), float(qy)), True)) for qx, qy in Q[::step]])
            if (dd <= tol).mean() >= 0.9:
                hit = True
                break
        if not hit:
            out.append(sk)
    return out


def sadakat_dense(p: np.ndarray, closed: bool) -> np.ndarray:
    """Çizgi noktalarını 0,5 piksel aralıkla sıkılaştır (uç noktaları seyrek doğrular için)."""
    if len(p) < 2:
        return p
    q = np.vstack([p, p[:1]]) if closed else p
    out = [q[:1]]
    for a, b in zip(q[:-1], q[1:]):
        n = max(1, int(math.hypot(*(b - a)) / 0.5))
        t = np.linspace(0, 1, n + 1)[1:, None]
        out.append(a + (b - a) * t)
    return np.vstack(out)


# ---------------------------------------------------------------- çizgiler
def _line_of(e):
    """Elemanı tek doğru parçasına indirgenebiliyorsa (p0, p1) döndür."""
    if e.prim and e.prim.get("type") == "line":
        return np.array([e.prim["x1"], e.prim["y1"]]), np.array([e.prim["x2"], e.prim["y2"]])
    if e.d and "Z" not in e.d:
        polys = sadakat.flatten(e.d)
        if len(polys) == 1 and len(polys[0][0]) >= 2:
            p = polys[0][0]
            if len(p) == 2:
                return p[0], p[1]
            L = float(np.hypot(*(p[-1] - p[0])))
            if L > 4:
                c, dvec, dev = egri.line_fit(p)
                if dev <= max(0.6, 0.5 * e.width):
                    t = (p - c) @ dvec
                    return c + dvec * t.min(), c + dvec * t.max()
    return None


def _same_ink(c1, c2) -> bool:
    """Aynı çizginin parçaları mı (zemine göre biraz farklı görünen gri tonlar dahil)."""
    d = math.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2)
    if d < 30:
        return True
    return d < 140 and max(c1) - min(c1) < 25 and max(c2) - min(c2) < 25


def _split_polylines(strokes: list) -> list:
    """Yalnız düz parçalardan oluşan açık çizgileri (ör. eksen + taban) tek tek doğrulara ayır;
    sonra aynı doğrudaki parçalar birleşir, kenar çizgileri dikdörtgenlere bağlanır."""
    from .vektor import Element
    out = []
    for s in strokes:
        if s.prim or not s.d or s.dash or any(c in s.d for c in "CAZ") or s.layer == "veri":
            out.append(s)
            continue
        polys = sadakat.flatten(s.d)
        if len(polys) != 1 or len(polys[0][0]) < 3 or len(polys[0][0]) > 8:
            out.append(s)
            continue
        p = polys[0][0]
        for a, b in zip(p[:-1], p[1:]):
            out.append(Element("stroke", s.color, prim={"type": "line", "x1": float(a[0]), "y1": float(a[1]),
                                                         "x2": float(b[0]), "y2": float(b[1])},
                               width=s.width, cap="butt",
                               bbox=(float(min(a[0], b[0])), float(min(a[1], b[1])), float(max(a[0], b[0])), float(max(a[1], b[1])))))
    return out


def _merge_lines(strokes: list) -> list:
    """Aynı doğru üzerindeki, aynı renk ve kalınlıktaki parçaları birleştir."""
    from .vektor import Element
    segs = []
    rest = []
    for s in strokes:
        ln = _line_of(s) if not s.dash else None
        if ln is None:
            rest.append(s)
            continue
        segs.append((s, ln[0], ln[1]))
    groups = []
    for s, a, b in segs:
        v = b - a
        L = float(np.hypot(*v))
        if L < 1e-6:
            rest.append(s)
            continue
        d = v / L
        if d[0] < 0 or (abs(d[0]) < 1e-9 and d[1] < 0):
            d = -d
            a, b = b, a
        placed = False
        for g in groups:
            gs, gd, ga = g["s"], g["d"], g["a"]
            if max(gs.width, s.width) > 1.9 * min(gs.width, s.width) + 0.2:
                continue
            if abs(float(gd @ d)) < 0.9995:
                continue
            if not _same_ink(gs.color, s.color):
                continue
            nrm = np.array([-gd[1], gd[0]])
            if abs(float((a - ga) @ nrm)) > 0.8 or abs(float((b - ga) @ nrm)) > 0.8:
                continue
            ta, tb = float((a - ga) @ gd), float((b - ga) @ gd)
            lo, hi = min(ta, tb), max(ta, tb)
            # uzun çizgilerde (harita meridyeni gibi) üstünden geçen kıyının açtığı kısa boşluklar da kapanır
            span = (g["hi"] - g["lo"]) + (hi - lo)
            gap_ok = max(1.6, min(8.0, 0.04 * span))
            if lo > g["hi"] + gap_ok or hi < g["lo"] - gap_ok:
                continue
            g["lo"], g["hi"] = min(g["lo"], lo), max(g["hi"], hi)
            g["n"] += 1
            g["parts"].append(s)
            placed = True
            break
        if not placed:
            groups.append({"s": s, "d": d, "a": a, "lo": 0.0, "hi": float((b - a) @ d), "n": 1, "parts": [s]})
    out = list(rest)
    for g in groups:
        s, d, a = g["s"], g["d"], g["a"]
        if len(g["parts"]) > 1:
            # birleşen parçaların en koyu rengi ve ortanca kalınlığı
            darkest = min(g["parts"], key=lambda q: sum(q.color))
            from copy import copy
            s = copy(s)
            s.color = darkest.color
            s.width = float(np.median([q.width for q in g["parts"]]))
        p0, p1 = a + d * g["lo"], a + d * g["hi"]
        out.append(Element("stroke", s.color, prim={"type": "line", "x1": float(p0[0]), "y1": float(p0[1]),
                                                     "x2": float(p1[0]), "y2": float(p1[1])},
                           width=s.width, cap=s.cap,
                           bbox=(float(min(p0[0], p1[0])), float(min(p0[1], p1[1])), float(max(p0[0], p1[0])), float(max(p0[1], p1[1])))))
    return out


def _merge_dashes(elements: list) -> list:
    """Aynı doğru üzerinde düzenli aralıklarla dizilmiş kısa çizgi ve noktaları tek kesikli çizgi yap
    (kesik-nokta deseni dahil)."""
    from .vektor import Element, _dash_pattern
    pieces = []
    for e in elements:
        if e.kind == "stroke" and not e.dash:
            ln = _line_of(e)
            if ln is not None:
                pieces.append((e, np.asarray(ln[0], float), np.asarray(ln[1], float), e.width))
        elif e.kind == "fill" and e.prim and e.prim.get("type") == "circle" and e.prim["r"] <= 2.0 and not e.stroke:
            c = np.array([e.prim["cx"], e.prim["cy"]], float)
            pieces.append((e, c, c, 2 * e.prim["r"]))
    if len(pieces) < 4:
        return elements
    used = set()
    out_new = []
    order = sorted(range(len(pieces)), key=lambda i: -float(np.hypot(*(pieces[i][2] - pieces[i][1]))))
    for si in order:
        e0, a0, b0, w0 = pieces[si]
        if id(e0) in used:
            continue
        L0 = float(np.hypot(*(b0 - a0)))
        if L0 < 4:
            break
        d = (b0 - a0) / L0
        nrm = np.array([-d[1], d[0]])
        tol = max(0.8, 0.5 * w0)
        mem = []
        for e, a, b, w in pieces:
            if id(e) in used or max(w, w0) > 2.2 * min(w, w0) + 0.3:
                continue
            if abs(float((a - a0) @ nrm)) > tol or abs(float((b - a0) @ nrm)) > tol:
                continue
            if not _same_ink(e.color, e0.color):
                continue
            ta, tb = float((a - a0) @ d), float((b - a0) @ d)
            if e.kind == "fill":
                r = w / 2
                ta, tb = ta - r, tb + r
            mem.append((min(ta, tb), max(ta, tb), e, w))
        if len(mem) < 4:
            continue
        mem.sort(key=lambda m: m[0])
        # boşluğu küçük ardışık parçalar
        runs, cur = [], [mem[0]]
        for m in mem[1:]:
            gap = m[0] - cur[-1][1]
            if gap <= max(4.0, 3.0 * w0) and gap > -1.0:
                cur.append(m)
            else:
                runs.append(cur)
                cur = [m]
        runs.append(cur)
        for run in runs:
            if len(run) < 4:
                continue
            gaps = np.array([run[i + 1][0] - run[i][1] for i in range(len(run) - 1)])
            if gaps.mean() < 0.8 or gaps.std() > 0.5 * gaps.mean():
                continue
            dashes = [m[1] - m[0] for m in run]
            inner = dashes[1:-1] if len(dashes) >= 5 else dashes
            span = run[-1][1] - run[0][0]
            # kesikli çizgide kesikler ve boşluklar düzenlidir (ya hepsi benzer boyda ya da uzun-kısa
            # sırayla, kesik-nokta); araya giren şekiller yüzünden bölünmüş düz çizgi kesikli sayılmaz
            def cv(v):
                v = np.asarray(v, float)
                return float(v.std() / max(v.mean(), 1e-6))
            if gaps.sum() < 0.08 * span or cv(gaps) > 0.4:
                continue
            uniform = cv(inner) <= 0.35
            alt = False
            if len(inner) >= 4:
                ev, od = inner[0::2], inner[1::2]
                lo_, hi_ = sorted([float(np.mean(ev)), float(np.mean(od))])
                alt = cv(ev) <= 0.35 and cv(od) <= 0.35 and hi_ >= 2.5 * lo_
            if not (uniform or alt):
                continue
            w = float(np.median([m[3] for m in run if m[2].kind == "stroke"] or [w0]))
            pat, cap = _dash_pattern(inner, list(gaps), w)
            p0, p1 = a0 + d * run[0][0], a0 + d * run[-1][1]
            col = min((m[2] for m in run), key=lambda q: sum(q.color)).color
            out_new.append(Element("stroke", col, prim={"type": "line", "x1": float(p0[0]), "y1": float(p0[1]),
                                                         "x2": float(p1[0]), "y2": float(p1[1])},
                                   width=w, dash=pat, cap=cap,
                                   bbox=(float(min(p0[0], p1[0])), float(min(p0[1], p1[1])),
                                         float(max(p0[0], p1[0])), float(max(p0[1], p1[1])))))
            for m in run:
                used.add(id(m[2]))
    if not used:
        return elements
    return [e for e in elements if id(e) not in used] + out_new


def _closed_shape(s) -> None:
    """Kapalı çizgi (çerçeve, halka) dikdörtgene ya da daireye/elipse benziyorsa o nesne olsun."""
    import cv2
    if s.prim or not s.d or "Z" not in s.d or s.dash:
        return
    polys = sadakat.flatten(s.d)
    if len(polys) != 1 or not polys[0][1]:
        return
    P = sadakat_dense(polys[0][0], True)
    if len(P) < 8:
        return
    x0, y0 = P.min(axis=0)
    x1, y1 = P.max(axis=0)
    W, H = x1 - x0, y1 - y0
    if min(W, H) < 4:
        return
    tol = max(1.5, 0.6 * s.width)
    dist = np.minimum.reduce([np.abs(P[:, 0] - x0), np.abs(P[:, 0] - x1), np.abs(P[:, 1] - y0), np.abs(P[:, 1] - y1)])
    if float(np.percentile(dist, 97)) <= tol:
        ok = True
        for side in range(4):
            if side < 2:
                on = np.abs(P[:, 1] - (y0 if side == 0 else y1)) <= tol
                span = np.ptp(P[on, 0]) if on.sum() > 1 else 0.0
                ok &= span >= 0.8 * W
            else:
                on = np.abs(P[:, 0] - (x0 if side == 2 else x1)) <= tol
                span = np.ptp(P[on, 1]) if on.sum() > 1 else 0.0
                ok &= span >= 0.8 * H
        if ok:
            s.prim = {"type": "rect", "x": float(x0), "y": float(y0), "w": float(W), "h": float(H)}
            s.d = ""
            return
    try:
        (ex, ey), (ea, eb), ang = cv2.fitEllipse(P.astype(np.float32))
    except cv2.error:
        return
    if ea < 3 or eb < 3:
        return
    t = math.radians(ang)
    qx = (P[:, 0] - ex) * math.cos(t) + (P[:, 1] - ey) * math.sin(t)
    qy = -(P[:, 0] - ex) * math.sin(t) + (P[:, 1] - ey) * math.cos(t)
    rad = np.sqrt((qx / (ea / 2)) ** 2 + (qy / (eb / 2)) ** 2)
    err = np.abs(rad - 1) * min(ea, eb) / 2
    if float(np.percentile(err, 95)) <= max(1.0, 0.5 * s.width):
        rx, ry = ea / 2, eb / 2
        if abs(rx - ry) <= 0.06 * max(rx, ry):
            s.prim = {"type": "circle", "cx": float(ex), "cy": float(ey), "r": float((rx + ry) / 2)}
        else:
            s.prim = {"type": "ellipse", "cx": float(ex), "cy": float(ey), "rx": float(rx), "ry": float(ry), "rot": float(ang)}
        s.d = ""


def _baglantilar(elements: list) -> list:
    """Yatay/dikey bağlantı çizgilerini (şema, ağaç) temizle:

    - aynı hizadaki parçalar tek çizgi; uçlar kesiştikleri çizgiye ya da kutunun kenarına
      tam oturur (aradaki boşluklar kapanır),
    - köşede birleşen çizgiler tek yol (ör. ⊓ biçimli dağıtıcı), düz devam eden kol da aynı yolda,
    - köşelerdeki küçük dolgu parçaları (kalın köşe izleri) atılır,
    - aynı renkteki bağlantıların kalınlığı aynı.
    """
    from .vektor import Element
    # köşeleri yumuşamış dik açılı yolları (⊓, ├ biçimli) düz parçalara ayır
    extra = []
    for e in elements:
        if e.kind != "stroke" or e.dash or e.prim or not e.d or "Z" in e.d:
            continue
        pp = sadakat.flatten(e.d)
        if len(pp) != 1 or len(pp[0][0]) < 2:
            continue
        P = pp[0][0]
        if np.ptp(P[:, 0]) + np.ptp(P[:, 1]) < 12:
            continue
        v = egri.rdp(P, max(1.2, 0.6 * e.width))
        if len(v) < 2 or len(v) > 10:
            continue
        ok = True
        parts = []
        for a, b in zip(v[:-1], v[1:]):
            L = float(np.hypot(*(b - a)))
            if L < 1e-6:
                continue
            ang = math.degrees(math.atan2(abs(b[1] - a[1]), abs(b[0] - a[0])))
            # köşedeki çok kısa yuvarlatma parçası atlanır; kısa parçalar en yakın yöne
            # oturtulur; uzun parçalar zaten yatay/dikey olmalı
            if L < max(3.0, 1.5 * e.width):
                continue
            if L < 8:
                if ang <= 30:
                    yy = (a[1] + b[1]) / 2
                    a, b = np.array([a[0], yy]), np.array([b[0], yy])
                elif ang >= 60:
                    xx = (a[0] + b[0]) / 2
                    a, b = np.array([xx, a[1]]), np.array([xx, b[1]])
                else:
                    ok = False
                    break
                parts.append((a, b))
                continue
            lim = 7 if L < 20 else 8
            if ang <= lim:
                yy = (a[1] + b[1]) / 2
                a, b = np.array([a[0], yy]), np.array([b[0], yy])
            elif ang >= 90 - lim:
                xx = (a[0] + b[0]) / 2
                a, b = np.array([xx, a[1]]), np.array([xx, b[1]])
            else:
                ok = False
                break
            parts.append((a, b))
        if not ok or not parts:
            continue
        for a, b in parts:
            extra.append(Element("stroke", e.color, prim={"type": "line", "x1": float(a[0]), "y1": float(a[1]),
                                                         "x2": float(b[0]), "y2": float(b[1])}, width=e.width,
                                 bbox=(float(min(a[0], b[0])), float(min(a[1], b[1])), float(max(a[0], b[0])), float(max(a[1], b[1])))))
        e.layer = "_bolundu"
    if extra:
        elements = [e for e in elements if e.layer != "_bolundu"] + extra
    segs = []
    kisa = []      # köşe arayışı için bütün yatay/dikey parçalar (kısalar dahil): (renk, yön, uç1, uç2)
    for e in elements:
        if e.kind != "stroke" or e.dash:
            continue
        ln = _line_of(e)
        if ln is None:
            continue
        a, b = np.asarray(ln[0], float), np.asarray(ln[1], float)
        dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
        L = math.hypot(dx, dy)
        if L >= 1.0 and (dy <= 0.36 * L or dx <= 0.36 * L):
            kisa.append((e.color, "h" if dy <= 0.36 * L else "v", a, b))
        if L < 3:
            continue
        if dy <= max(0.9, 0.035 * L):
            y = (a[1] + b[1]) / 2
            segs.append({"e": e, "o": "h", "c": y, "lo": min(a[0], b[0]), "hi": max(a[0], b[0]), "w": e.width})
        elif dx <= max(0.9, 0.035 * L):
            x = (a[0] + b[0]) / 2
            segs.append({"e": e, "o": "v", "c": x, "lo": min(a[1], b[1]), "hi": max(a[1], b[1]), "w": e.width})
    if len(segs) < 2:
        return elements
    used = set()
    # renk gruplarına ayır
    groups = []
    for sg in segs:
        for g in groups:
            if _same_ink(g[0]["e"].color, sg["e"].color) and _de(g[0]["e"].color, sg["e"].color) < 25:
                g.append(sg)
                break
        else:
            groups.append([sg])
    targets = []   # kutu kenarları: (yön, koordinat, alt, üst)
    for e in elements:
        p = e.prim or {}
        if e.kind == "fill" and p.get("type") in ("rect", "rrect") and not p.get("rot") and e.layer != "harf":
            x, y, w_, h_ = p["x"], p["y"], p["w"], p["h"]
            r = p.get("r", 0.0)
            targets += [("h", y, x + r, x + w_ - r), ("h", y + h_, x + r, x + w_ - r),
                        ("v", x, y + r, y + h_ - r), ("v", x + w_, y + r, y + h_ - r)]
    out_new = []
    drop_fills = set()
    for g in groups:
        if len(g) < 2 and not targets:
            continue
        wmed = float(np.median([sg["w"] for sg in g]))
        tol = max(2.0, 1.2 * wmed)
        g_col = g[0]["e"].color
        dik = [(o_, a_, b_) for c_, o_, a_, b_ in kisa if _same_ink(c_, g_col) and _de(c_, g_col) < 25]

        def kose(o, c, pos):
            # parçanın bu ucu dik bir parçanın ucuyla köşe yapıyor mu (küçük sütunun üst kenarı):
            # köşede biten uç başka yere uzatılmaz, öbür parçayla birleşmez
            pt = np.array([pos, c]) if o == "h" else np.array([c, pos])
            for o2, a_, b_ in dik:
                if o2 == o:
                    continue
                if min(float(np.hypot(*(a_ - pt))), float(np.hypot(*(b_ - pt)))) <= 1.5:
                    return True
            return False
        # aynı hizadakileri eşitle ve birleştir
        merged = []
        for o in ("h", "v"):
            items = sorted([sg for sg in g if sg["o"] == o], key=lambda t: t["c"])
            clusters = []
            for sg in items:
                if clusters and abs(sg["c"] - clusters[-1][-1]["c"]) <= tol:
                    clusters[-1].append(sg)
                else:
                    clusters.append([sg])
            for cl in clusters:
                c = float(np.median([t["c"] for t in cl]))
                cl.sort(key=lambda t: t["lo"])
                cur = None
                for t in cl:
                    if cur:
                        gap = t["lo"] - cur["hi"]
                        son = cur["parts"][-1]
                        # kısa parçalar arasındaki, boyları kadar boşluk kopukluk değil, ayrı şekillerdir
                        izin = min(max(3 * wmed, 12), max(1.5 + wmed, 0.5 * min(son["hi"] - son["lo"],
                                                                                 t["hi"] - t["lo"])))
                        if gap > 1.5 + wmed and (kose(o, c, cur["hi"]) or kose(o, c, t["lo"])):
                            izin = 1.5 + wmed
                    if cur and t["lo"] <= cur["hi"] + izin:
                        cur["hi"] = max(cur["hi"], t["hi"])
                        cur["parts"].append(t)
                    else:
                        cur = {"o": o, "c": c, "lo": t["lo"], "hi": t["hi"], "parts": [t]}
                        merged.append(cur)
        if len(merged) < 2 and not targets:
            continue
        reach = 2 * wmed + 4
        # uçları kesiştikleri dik çizgiye ya da kutu kenarına oturt (çizgi kısalıp yok olmasın)
        for m in merged:
            L0 = m["hi"] - m["lo"]
            for end in ("lo", "hi"):
                pos = m[end]
                other = m["hi"] if end == "lo" else m["lo"]
                best = None
                # köşede biten uç yalnız o köşeye oturur; kısa parça boyundan fazla uzatılmaz
                lim = 2.0 if kose(m["o"], m["c"], pos) else max(2.0, L0)
                cands = [(q["c"], q["lo"] - reach, q["hi"] + reach) for q in merged
                         if q is not m and q["o"] != m["o"]]
                cands += [(c, lo - 1, hi + 1) for o, c, lo, hi in targets if o != m["o"]]
                for c, lo, hi in cands:
                    d = abs(c - pos)
                    if d > min(reach, lim) or not (lo <= m["c"] <= hi):
                        continue
                    # çizginin içinden geçtiği dik çizgiye kısaltma yalnız kenar yumuşatması kadar
                    # (eksenin iki yanına taşan çentik yarıya inmesin)
                    ice = (c > pos) if end == "lo" else (c < pos)
                    if ice and d > max(1.5, wmed):
                        continue
                    newL = (other - c) if end == "lo" else (c - other)
                    if newL < max(2.0, 0.5 * L0):
                        continue
                    if best is None or d < best[0]:
                        best = (d, c)
                if best is not None:
                    m[end] = best[1]
            if m["lo"] > m["hi"]:
                m["lo"], m["hi"] = m["hi"], m["lo"]
        # köşe izleri: yatay ile dikey parçanın buluştuğu köşedeki küçük aynı renkli dolgular
        # (grafik çizgisinin veri noktaları köşe değildir)
        uc_h, uc_v = [], []
        for m in merged:
            for v in (m["lo"], m["hi"]):
                if m["o"] == "h":
                    uc_h.append((v, m["c"]))
                else:
                    uc_v.append((m["c"], v))
        pts = [p for p in uc_h if any(math.hypot(p[0] - q[0], p[1] - q[1]) <= 2 * wmed + 4 for q in uc_v)]
        pts += [q for q in uc_v if any(math.hypot(p[0] - q[0], p[1] - q[1]) <= 2 * wmed + 4 for p in uc_h)]
        for e in elements:
            if e.kind != "fill" or id(e) in drop_fills or e.layer == "harf":
                continue
            if _size(e) > 3 * wmed + 6 or not _same_ink(e.color, g[0]["e"].color):
                continue
            cx, cy = (e.bbox[0] + e.bbox[2]) / 2, (e.bbox[1] + e.bbox[3]) / 2
            if any(math.hypot(cx - px, cy - py) <= 2 * wmed + 4 for px, py in pts):
                drop_fills.add(id(e))
        # köşede buluşanları tek yola diz: uç noktalarından grafik
        def ends(m):
            if m["o"] == "h":
                return (round(m["lo"], 1), round(m["c"], 1)), (round(m["hi"], 1), round(m["c"], 1))
            return (round(m["c"], 1), round(m["lo"], 1)), (round(m["c"], 1), round(m["hi"], 1))
        adj = {}
        for i, m in enumerate(merged):
            for pnt in ends(m):
                adj.setdefault(pnt, []).append(i)
        done = set()
        col = min((t["e"] for m in merged for t in m["parts"]), key=lambda e: sum(e.color)).color
        for i, m in enumerate(merged):
            if i in done:
                continue
            # zinciri iki yöne uzat
            chain = [i]
            done.add(i)
            for direction in (0, 1):
                cur = i
                pnt = ends(m)[direction]
                while True:
                    nxt = [j for j in adj.get(pnt, []) if j not in done]
                    if len(adj.get(pnt, [])) != 2 or len(nxt) != 1:
                        break
                    j = nxt[0]
                    done.add(j)
                    if direction == 0:
                        chain.insert(0, j)
                    else:
                        chain.append(j)
                    e0, e1 = ends(merged[j])
                    pnt = e1 if e0 == pnt else e0
                    cur = j
            # yolu noktalar olarak yaz
            if len(chain) == 1:
                a, b = ends(merged[chain[0]])
                poly = [a, b]
            else:
                poly = []
                for idx_c, j in enumerate(chain):
                    a, b = ends(merged[j])
                    if not poly:
                        nb = ends(merged[chain[1]])
                        if a in nb:
                            a, b = b, a
                        poly = [a, b]
                    else:
                        if a == poly[-1]:
                            poly.append(b)
                        elif b == poly[-1]:
                            poly.append(a)
                        else:
                            poly.append(a)
                            poly.append(b)
            P = np.array(poly, float)
            # kalınlık: aynı renkteki bağlantılarınki (ölçüm oynaması eşitlenir); bu yolun kendi
            # kalınlığı ondan belirgin farklıysa (aynı renkte kalın bir çizgi ile ince harf çubukları)
            # kendi kalınlığı kalır
            ws_ = np.array([float(t["e"].width) for j in chain for t in merged[j]["parts"]])
            ls_ = np.array([max(1.0, float(t["hi"] - t["lo"])) for j in chain for t in merged[j]["parts"]])
            o_ = np.argsort(ws_)
            w_kendi = float(ws_[o_][np.searchsorted(np.cumsum(ls_[o_]), 0.5 * float(ls_.sum()))])
            wd_ = wmed if abs(w_kendi - wmed) <= 0.35 * wmed else w_kendi
            if len(P) == 2:
                el = Element("stroke", col, prim={"type": "line", "x1": float(P[0][0]), "y1": float(P[0][1]),
                                                  "x2": float(P[1][0]), "y2": float(P[1][1])}, width=wd_, cap="butt")
            else:
                d = "M" + "L".join(f"{_f(x)} {_f(y)}" for x, y in P)
                el = Element("stroke", col, d=d, width=wd_, cap="butt")
            el.join = "miter"
            el.bbox = (float(P[:, 0].min()), float(P[:, 1].min()), float(P[:, 0].max()), float(P[:, 1].max()))
            out_new.append(el)
            for j in chain:
                for t in merged[j]["parts"]:
                    used.add(id(t["e"]))
    if not used and not drop_fills:
        return elements
    return [e for e in elements if id(e) not in used and id(e) not in drop_fills] + out_new


def _gorunmez(elements: list) -> list:
    """Altındaki dolguyla aynı renkte olan küçük çizgi ve kırıntıları at (görünmezler, yalnız
    nesne kalabalığı yaparlar: harf aralarında kalan kutu rengi, kenar pürüzleri)."""
    import cv2
    shapes = []
    for e in elements:
        if e.kind != "fill" or e.layer == "harf" or e.grad or _size(e) < 8:
            continue
        kind, pp = sadakat.element_polys(e)
        if not pp:
            continue
        P = max((p_ for p_, _c in pp), key=lambda q: len(q))
        if len(P) < 3:
            continue
        shapes.append((e, P.astype(np.float32), e.bbox))
    if not shapes:
        return elements
    out = []
    for e in elements:
        if e.layer == "harf" or e.kind == "text" or _size(e) > 30 or (e.kind == "fill" and e.stroke is not None):
            out.append(e)
            continue
        kind, pp = sadakat.element_polys(e)
        if not pp:
            out.append(e)
            continue
        Q = np.vstack([p_ for p_, _c in pp])
        x0, y0 = Q.min(axis=0)
        x1, y1 = Q.max(axis=0)
        gone = False
        for S, P, b in shapes:
            if S is e or b[0] > x0 or b[1] > y0 or b[2] < x1 or b[3] < y1 or _size(S) <= _size(e):
                continue
            if _de(S.color, e.color) >= 12:
                continue
            if all(cv2.pointPolygonTest(P, (float(qx), float(qy)), True) >= 0.5 for qx, qy in Q[:: max(1, len(Q) // 20)]):
                gone = True
                break
        if not gone:
            out.append(e)
    return out


def _kumele(vals, tol_abs, tol_rel=0.0):
    """Yakın değerleri kümele; her değerin küme ortancasını döndür."""
    vals = np.asarray(vals, float)
    order = np.argsort(vals)
    out = vals.copy()
    grp = [order[0]]
    for i in order[1:]:
        ref = float(np.median(vals[grp]))
        if abs(vals[i] - ref) <= max(tol_abs, tol_rel * abs(ref)):
            grp.append(i)
        else:
            out[grp] = float(np.median(vals[grp]))
            grp = [i]
    out[grp] = float(np.median(vals[grp]))
    return out


def _hizala(elements: list) -> None:
    """Aynı türdeki kutuları eşitle ve hizala (bir tasarımcının yapacağı gibi):
    aynı renkteki benzer kutular aynı boyut, aynı köşe yuvarlaklığı ve aynı konturu alır;
    neredeyse aynı hizadaki kenarlar tam hizalanır."""
    # panel (üstünde başka şekiller duran çerçeveli zemin) kapsayıcıdır: içindekilere hizalanmaz
    boxes = [e for e in elements if e.kind == "fill" and e.prim and e.prim.get("type") in ("rect", "rrect")
             and not e.prim.get("rot") and e.layer != "harf" and min(e.prim["w"], e.prim["h"]) >= 4
             and not getattr(e, "panel", False)]
    if len(boxes) < 2:
        return
    # benzer kutu grupları: dolgu rengi ve boyut
    groups = []
    for e in boxes:
        for g in groups:
            r = g[0]
            same_stroke = (r.stroke is None) == (e.stroke is None) and (r.stroke is None or _de(r.stroke, e.stroke) < 15)
            if (same_stroke and _de(r.color, e.color) < 10
                    and abs(r.prim["w"] - e.prim["w"]) <= 0.12 * max(r.prim["w"], e.prim["w"])
                    and abs(r.prim["h"] - e.prim["h"]) <= 0.15 * max(r.prim["h"], e.prim["h"])):
                g.append(e)
                break
        else:
            groups.append([e])
    for g in groups:
        if len(g) < 2:
            continue
        n_rr = sum(1 for e in g if e.prim["type"] == "rrect")
        rounded = n_rr * 2 >= len(g)
        rs = [e.prim.get("r", 0.0) for e in g if e.prim["type"] == "rrect"]
        r_med = float(np.median(rs)) if rs else 0.0
        ws = _kumele([e.prim["w"] for e in g], 1.5, 0.03)
        hs = _kumele([e.prim["h"] for e in g], 1.5, 0.04)
        st = [e for e in g if e.stroke is not None]
        sw = float(np.median([e.stroke_width for e in st])) if st else 0.0
        sc = None
        if st and len(st) * 2 >= len(g):
            # en sık kontur rengi
            votes = []
            for e in st:
                for v in votes:
                    if _de(v[0].stroke, e.stroke) < 12:
                        v.append(e)
                        break
                else:
                    votes.append([e])
            sc = max(votes, key=len)[0].stroke
        for e, w_, h_ in zip(g, ws, hs):
            cx = e.prim["x"] + e.prim["w"] / 2
            cy = e.prim["y"] + e.prim["h"] / 2
            p = {"type": "rrect" if rounded and r_med > 0.5 else "rect", "x": cx - w_ / 2, "y": cy - h_ / 2,
                 "w": float(w_), "h": float(h_)}
            if p["type"] == "rrect":
                p["r"] = min(r_med, w_ / 2, h_ / 2)
            e.prim = p
            if sc is not None:
                e.stroke, e.stroke_width = sc, sw
    # kenar hizası: yakın sol/üst kenarlar aynı çizgiye, sonra yakın sağ/alt kenarlar
    for key, size in (("x", "w"), ("y", "h")):
        lefts = _kumele([e.prim[key] for e in boxes], 2.0)
        for e, v in zip(boxes, lefts):
            e.prim[key] = float(v)
        rights = _kumele([e.prim[key] + e.prim[size] for e in boxes], 2.0)
        for e, v in zip(boxes, rights):
            nw = float(v) - e.prim[key]
            if abs(nw - e.prim[size]) <= 2.0:
                e.prim[size] = nw
                if e.prim["type"] == "rrect":
                    e.prim["r"] = min(e.prim["r"], e.prim["w"] / 2, e.prim["h"] / 2)
    # şemadaki köşe yuvarlaklıkları birbirine yakınsa hepsi aynı
    rr = [e for e in boxes if e.prim["type"] == "rrect"]
    if len(rr) >= 2:
        rv = _kumele([e.prim["r"] for e in rr], 1.0, 0.25)
        for e, v in zip(rr, rv):
            e.prim["r"] = float(min(v, e.prim["w"] / 2, e.prim["h"] / 2))
    for e in boxes:
        pp = sekil.prim_points(e.prim)
        e.bbox = (float(pp[:, 0].min()), float(pp[:, 1].min()), float(pp[:, 0].max()), float(pp[:, 1].max()))
    # aynı renkteki konturlar aynı kalınlıkta
    st = [e for e in elements if e.kind == "fill" and e.stroke is not None]
    groups = []
    for e in st:
        for g in groups:
            if _de(g[0].stroke, e.stroke) < 12:
                g.append(e)
                break
        else:
            groups.append([e])
    for g in groups:
        if len(g) >= 2:
            w = float(np.median([e.stroke_width for e in g]))
            for e in g:
                e.stroke_width = w


def _simplify_curve(s) -> None:
    """Çok noktalı Bézier eğrisini daha az noktayla yeniden yaz."""
    if not s.d or "C" not in s.d:
        return
    polys = sadakat.flatten(s.d)
    if len(polys) != 1:
        return
    p, closed = polys[0]
    if len(p) < 8:
        return
    pts = egri.resample(p, 0.5, closed)
    cs = egri.corners(pts, closed, 6, 35.0)
    if closed:
        if not cs:
            cs = [0]
        order = cs + [cs[0] + len(pts)]
        segs = [np.vstack([pts[i % len(pts)] for i in range(a, b + 1)]) for a, b in zip(order[:-1], order[1:])]
    else:
        idx = [0] + [c for c in cs if 0 < c < len(pts) - 1] + [len(pts) - 1]
        segs = [pts[a:b + 1] for a, b in zip(idx[:-1], idx[1:])]
    d = [f"M{_f(segs[0][0][0])} {_f(segs[0][0][1])}"]
    tol = max(0.7, 0.35 * s.width)
    for sg in segs:
        kind, val = egri.classify_segment(sg, tol)
        if kind == "L":
            d.append(f"L{_f(val[0])} {_f(val[1])}")
        elif kind == "A":
            cx, cy, r, p1, large, sweep, tot = val
            d.append(f"A{_f(r)} {_f(r)} 0 {large} {sweep} {_f(p1[0])} {_f(p1[1])}")
        else:
            for c in val:
                d.append("C" + " ".join(f"{_f(q[0])} {_f(q[1])}" for q in c[1:]))
    if closed:
        d.append("Z")
    new = "".join(d)
    if new.count("C") + new.count("L") + new.count("A") < s.d.count("C") + s.d.count("L") + s.d.count("A"):
        s.d = new


# ---------------------------------------------------------------- kırıntılar
def _size(e) -> float:
    x0, y0, x1, y1 = e.bbox
    return max(x1 - x0, y1 - y0)


def _is_blend(c, colors) -> bool:
    """Renk, sahnedeki başka iki rengin (ör. siyah ile beyaz) karışımına mı denk geliyor."""
    c = np.array(c, float)
    cols = [np.array(k, float) for k in colors if tuple(k) != tuple(c.astype(int))]
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            A, B = cols[i], cols[j]
            AB = A - B
            n = float(AB @ AB)
            if n < 1e-6:
                continue
            t = float(np.clip((c - B) @ AB / n, 0, 1))
            if 0.1 < t < 0.9 and np.linalg.norm(c - (B + t * AB)) < 20:
                return True
    return False


def _drop_crumbs(elements: list, background) -> list:
    big = [e for e in elements if e.kind != "text" and _size(e) >= 4]
    colors = {tuple(int(v) for v in e.color) for e in big if not e.grad} | {tuple(int(v) for v in background)}
    for e in big:
        if e.grad:
            colors |= {tuple(int(v) for v in c) for _o, c in e.grad["stops"]}
    # görselde gerçekten kullanılan renkler (büyük şekiller ve harfler): bunlar kırıntı sayılmaz
    real = {tuple(int(v) for v in e.color) for e in elements
            if e.kind != "text" and not e.grad and (_size(e) >= 4 or e.layer == "harf")}
    real = np.array(sorted(real), float).reshape(-1, 3)

    def is_real(c):
        if not len(real):
            return False
        return bool((np.linalg.norm(real - np.array(c, float), axis=1) < 14).any())

    harf_kut = np.array([e.bbox for e in elements if e.layer == "harf"], float).reshape(-1, 4)
    kutular = [e.prim for e in elements if e.kind == "fill" and e.prim and e.prim.get("type") in ("rect", "rrect")
               and not e.prim.get("rot") and e.layer != "harf"]

    def kutu_kenarinda(p):
        x1, y1, x2, y2 = p["x1"], p["y1"], p["x2"], p["y2"]
        for q in kutular:
            X0, Y0, X1, Y1 = q["x"], q["y"], q["x"] + q["w"], q["y"] + q["h"]
            for xe in (X0, X1):
                if abs(x1 - xe) <= 1.2 and abs(x2 - xe) <= 1.2 and \
                        min(y1, y2) >= Y0 - 1.5 and max(y1, y2) <= Y1 + 1.5:
                    return True
            for ye in (Y0, Y1):
                if abs(y1 - ye) <= 1.2 and abs(y2 - ye) <= 1.2 and \
                        min(x1, x2) >= X0 - 1.5 and max(x1, x2) <= X1 + 1.5:
                    return True
        return False

    def harf_yaninda(e):
        if not len(harf_kut):
            return False
        cx, cy = (e.bbox[0] + e.bbox[2]) / 2, (e.bbox[1] + e.bbox[3]) / 2
        return bool(((harf_kut[:, 0] - 3 <= cx) & (cx <= harf_kut[:, 2] + 3) &
                     (harf_kut[:, 1] - 3 <= cy) & (cy <= harf_kut[:, 3] + 3)).any())

    out = []
    for e in elements:
        if e.kind == "text" or e.grad:
            out.append(e)
            continue
        sz = _size(e)
        if sz < 1.2 and (e.kind != "fill" or e.area < 1.5):
            continue            # tek pikselden küçük toz
        if e.layer != "harf" and not e.stroke and harf_yaninda(e) and (
                sz <= 3.5 or (sz <= 12 and _lightness(e.color) >= 80)):
            continue            # yazının kenarından kalmış kırıntı (koyu nokta ya da açık hâle)
        if e.layer != "harf" and not e.stroke and _de(e.color, background) < 12 and \
                (e.kind == "stroke" and e.width <= 2.5 and (sz <= 40 or _de(e.color, background) < 6)
                 or e.kind == "fill" and sz <= 4):
            continue            # zeminden ayırt edilmeyen soluk kırıntı / kenar çizgisi (uzun ızgara değil)
        small = sz <= 6 or (e.kind == "stroke" and e.width <= 1.3 and sz <= 10)
        if small and e.layer != "harf" and not is_real(e.color) and _is_blend(e.color, colors):
            continue            # kenar yumuşatmasından kalan ara renk
        if (e.kind == "stroke" and not e.dash and e.width <= 1.5 and e.layer != "cerceve"
                and e.prim and e.prim.get("type") == "line" and _lightness(e.color) >= 55
                and kutu_kenarinda(e.prim)):
            continue            # bir kutunun kenarı boyunca kalan açık renkli kenar yumuşatması şeridi
        out.append(e)
    return out


# ---------------------------------------------------------------- nesneler (daire, elips, yay+taban)
def _hue_close(c1, c2, tol=28.0) -> bool:
    import colorsys
    h1, s1, v1 = colorsys.rgb_to_hsv(*[x / 255 for x in c1])
    h2, s2, v2 = colorsys.rgb_to_hsv(*[x / 255 for x in c2])
    if s1 < 0.15 or s2 < 0.15:
        return False
    d = abs(h1 - h2) * 360
    return min(d, 360 - d) <= tol


def _mask_of(els, x0, y0, W, H, k):
    m = np.zeros((H, W), np.uint8)
    for e in els:
        r = sadakat.rasterize(e, k, x0, y0, (H, W))
        m |= r
    return m


def _ransac_circle(P: np.ndarray, tol: float, iters: int = 300, seed: int = 0):
    """Aykırı noktalara dayanıklı çember uydurma. Dönüş: (cx, cy, r, inlier maskesi) ya da None."""
    n = len(P)
    if n < 8:
        return None
    rng = np.random.default_rng(seed)
    best_in, best = None, None
    for _ in range(iters):
        i, j, l = rng.choice(n, 3, replace=False)
        (x1, y1), (x2, y2), (x3, y3) = P[i], P[j], P[l]
        d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
        if abs(d) < 1e-9:
            continue
        ux = ((x1 * x1 + y1 * y1) * (y2 - y3) + (x2 * x2 + y2 * y2) * (y3 - y1) + (x3 * x3 + y3 * y3) * (y1 - y2)) / d
        uy = ((x1 * x1 + y1 * y1) * (x3 - x2) + (x2 * x2 + y2 * y2) * (x1 - x3) + (x3 * x3 + y3 * y3) * (x2 - x1)) / d
        r = math.hypot(x1 - ux, y1 - uy)
        inl = np.abs(np.hypot(P[:, 0] - ux, P[:, 1] - uy) - r) < tol
        c = int(inl.sum())
        if best_in is None or c > best_in:
            best_in, best = c, inl
    if best is None or best_in < 0.4 * n:
        return None
    fit = egri.circle_fit(P[best])
    if fit is None:
        return None
    cx, cy, r, _ = fit
    inl = np.abs(np.hypot(P[:, 0] - cx, P[:, 1] - cy) - r) < tol
    return cx, cy, r, inl


def _fit_clean(U: np.ndarray, x0: float, y0: float, k: int):
    """Temiz geometri oturt; olmazsa ince çıkıntıları (güneş ışınları, değen çizgi uçları) atıp dene."""
    import cv2
    r = _fit_clean1(U, x0, y0, k)
    if r[0] is not None or r[1] is not None:
        return r
    ys, xs = np.nonzero(U)
    if len(xs) < 30:
        return r
    rad = max(2, int(round(0.12 * max(np.ptp(xs), np.ptp(ys)))))
    Uo = cv2.morphologyEx(U, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1)))
    if Uo.sum() < 0.6 * U.sum():
        return r
    r2 = _fit_clean1(Uo, x0, y0, k)
    if r2[0] is None and r2[1] is None:
        return r
    # çıkıntılar atılınca bulunan şekil bütün nesneyi de karşılamalı (kalın kollar çıkıntı değildir)
    from .vektor import Element
    from scipy import ndimage
    m2 = sadakat.rasterize(Element("fill", (0, 0, 0), prim=r2[0], d=r2[1] or ""), k, x0, y0, U.shape) > 0
    Uf = ndimage.binary_fill_holes(U > 0)
    inter = np.count_nonzero(Uf & m2)
    uni = np.count_nonzero(Uf | m2)
    if not uni or inter / uni < 0.85:
        return r
    return r2


def _fit_clean1(U: np.ndarray, x0: float, y0: float, k: int):
    """Birleşik nesne maskesine temiz geometri oturt: daire/elips ya da tabanlı yay (yarım daire,
    kubbe). Pürüzlere ve üstteki şekillerin açtığı boşluklara dayanıklıdır; sonuç görselle
    örtüşme oranıyla doğrulanır. Dönüş: (prim | None, d | None, örtüşme)"""
    import cv2
    from scipy import ndimage
    # parçalar arasındaki ince çatlakları kapat (dolgu ile gölgesi arasındaki çizgi gibi)
    kc = max(3, 2 * k + 1)
    U = ndimage.binary_fill_holes(cv2.morphologyEx(U, cv2.MORPH_CLOSE, np.ones((kc, kc), np.uint8)) > 0).astype(np.uint8)
    cs, _ = cv2.findContours(U, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        return None, None, 0.0
    c = max(cs, key=cv2.contourArea)
    if len(c) < 16:
        return None, None, 0.0
    P = c[:, 0, :].astype(float)
    H, W = U.shape

    def iou_with(m2):
        inter = np.count_nonzero(U & m2)
        uni = np.count_nonzero(U | m2)
        return inter / uni if uni else 0.0

    def px(xu, yu):
        return (xu + 0.5) / k - 0.5 + x0, (yu + 0.5) / k - 0.5 + y0

    best = (None, None, 0.0)
    # 1) elips / daire: aykırı noktaları atarak birkaç turda
    Q = P.copy()
    for _ in range(3):
        if len(Q) < 8:
            break
        try:
            (ex, ey), (ea, eb), ang = cv2.fitEllipse(Q.astype(np.float32))
        except cv2.error:
            break
        if ea < 4 or eb < 4:
            break
        t = math.radians(ang)
        ct, st = math.cos(t), math.sin(t)
        qx = (Q[:, 0] - ex) * ct + (Q[:, 1] - ey) * st
        qy = -(Q[:, 0] - ex) * st + (Q[:, 1] - ey) * ct
        res = np.abs(np.sqrt((qx / (ea / 2)) ** 2 + (qy / (eb / 2)) ** 2) - 1)
        Q = Q[res <= np.percentile(res, 80)]
    else:
        pass
    try:
        (ex, ey), (ea, eb), ang = cv2.fitEllipse((Q if len(Q) >= 8 else P).astype(np.float32))
        if ea > 4 and eb > 4:
            m2 = np.zeros_like(U)
            cv2.ellipse(m2, ((ex, ey), (ea, eb), ang), 1, -1)
            v = iou_with(m2)
            if v >= 0.9:
                cx, cy = px(ex, ey)
                rx, ry = ea / 2 / k, eb / 2 / k
                if abs(rx - ry) <= 0.08 * max(rx, ry):
                    best = ({"type": "circle", "cx": cx, "cy": cy, "r": (rx + ry) / 2}, None, v)
                else:
                    best = ({"type": "ellipse", "cx": cx, "cy": cy, "rx": rx, "ry": ry, "rot": ang}, None, v)
    except cv2.error:
        pass
    if best[2] >= 0.97:
        return best
    # 2) tabanlı yay: alt (ya da üst/sol/sağ) kenar düz, kalanı tek çember yayı
    from .vektor import Element
    for side in ("alt", "ust", "sol", "sag"):
        if side == "alt":
            base = np.percentile(P[:, 1], 98)
            arcp = P[P[:, 1] < base - 2 * k]
        elif side == "ust":
            base = np.percentile(P[:, 1], 2)
            arcp = P[P[:, 1] > base + 2 * k]
        elif side == "sol":
            base = np.percentile(P[:, 0], 2)
            arcp = P[P[:, 0] > base + 2 * k]
        else:
            base = np.percentile(P[:, 0], 98)
            arcp = P[P[:, 0] < base - 2 * k]
        # taban gerçekten düz mü: kenara yakın noktalar yeterince çok
        on_base = np.abs((P[:, 1] if side in ("alt", "ust") else P[:, 0]) - base) <= 1.5 * k
        if on_base.mean() < 0.12 or len(arcp) < 12:
            continue
        rc = _ransac_circle(arcp, 1.5 * k)
        if rc is None:
            continue
        cx, cy, r, inl = rc
        if side in ("alt", "ust"):
            dy = base - cy
            if abs(dy) >= r:
                continue
            hw = math.sqrt(r * r - dy * dy)
            p1, p2 = (cx - hw, base), (cx + hw, base)
            inside_center = (cy < base) if side == "alt" else (cy > base)
        else:
            dx = base - cx
            if abs(dx) >= r:
                continue
            hh = math.sqrt(r * r - dx * dx)
            p1, p2 = (base, cy + hh), (base, cy - hh)
            inside_center = (cx > base) if side == "sol" else (cx < base)
        large = 1 if inside_center else 0
        for sweep in (1, 0):
            a1, b1 = px(*p1)
            a2, b2 = px(*p2)
            rr = r / k
            dd = f"M{_f(a1)} {_f(b1)}A{_f(rr)} {_f(rr)} 0 {large} {sweep} {_f(a2)} {_f(b2)}Z"
            m2 = sadakat.rasterize(Element("fill", (0, 0, 0), d=dd), k, x0, y0, (H, W))
            v = iou_with(m2)
            # tıknaz şekilde (daire, elips) küçük bir düzlük için yaya geçme: elips daha temiz
            margin = 0.0 if best[0] is None else (0.04 if 2 * hw / max(1e-6, 2 * r) < 0.7 else 0.0) if side in ("alt", "ust") else (0.04 if 2 * hh / max(1e-6, 2 * r) < 0.7 else 0.0)
            if v >= 0.9 and v > best[2] + margin:
                best = (None, dd, v)
    return best


def _de(c1, c2) -> float:
    """İki rengin algısal farkı (Lab)."""
    import cv2
    a = cv2.cvtColor(np.array([[c1, c2]], np.float32) / 255.0, cv2.COLOR_RGB2Lab)[0]
    return float(np.linalg.norm(a[0] - a[1]))


def _lightness(c) -> float:
    import cv2
    return float(cv2.cvtColor(np.array([[c]], np.float32) / 255.0, cv2.COLOR_RGB2Lab)[0, 0, 0])


def _is_shade(c, main) -> bool:
    """c, ana rengin gölgeli / koyu tonu mu (güneşin alt yarısı gibi)."""
    if _de(c, main) < 12:
        return True
    return _hue_close(c, main, 35.0) and _lightness(c) < _lightness(main) - 4


def _overlaps(b, B) -> bool:
    return b[0] <= B[2] and b[2] >= B[0] and b[1] <= B[3] and b[3] >= B[1]


def _ray_ring(prim, pool, used, fill=None, background=(255, 255, 255), k=2):
    """Dairenin çevresindeki küçük aynı renkli parçalar (güneş ışınları) -> tek kesikli halka."""
    if prim.get("type") == "circle":
        cx, cy, r = prim["cx"], prim["cy"], prim["r"]
    elif prim.get("type") == "ellipse" and min(prim["rx"], prim["ry"]) >= 0.8 * max(prim["rx"], prim["ry"]):
        cx, cy, r = prim["cx"], prim["cy"], (prim["rx"] + prim["ry"]) / 2
    else:
        return None
    if r < 3:
        return None
    lo, hi = r - max(1.5, 0.15 * r), r + max(4.0, 0.6 * r)
    byc = {}
    for e in pool:
        if id(e) in used or e.kind == "text" or e.layer == "harf" or e.grad:
            continue
        x0, y0, x1, y1 = e.bbox
        if max(x1 - x0, y1 - y0) > 0.9 * r + 2:
            continue
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dd = math.hypot(mx - cx, my - cy)
        if lo <= dd <= hi:
            byc.setdefault(tuple(int(v) for v in e.color), []).append(e)
    best = None
    for col, els in byc.items():
        if len(els) < 4 or _de(col, background) < 20 or (fill is not None and _de(col, fill) < 20):
            continue
        pts = []
        for e in els:
            kind, polys = sadakat.element_polys(e)
            for P, _c in polys:
                pts.append(P)
        if not pts:
            continue
        P = np.vstack(pts)
        ang = np.degrees(np.arctan2(P[:, 1] - cy, P[:, 0] - cx)) % 360
        cover = len(np.unique((ang // 15).astype(int))) / 24.0
        if cover < 0.3:
            continue
        dist = np.hypot(P[:, 0] - cx, P[:, 1] - cy)
        if best is None or cover > best[0]:
            best = (cover, col, els, float(np.percentile(dist, 10)), float(np.percentile(dist, 90)))
    if best is None:
        return None
    _cv, col, els, r_in, r_out = best
    r_in = max(r_in, r)
    if r_out <= r_in:
        r_out = r_in + 1.0
    from .vektor import Element
    rr = (r_in + r_out) / 2
    wd = float(np.clip(r_out - r_in, 1.0, 0.6 * r))
    ring = Element("stroke", col, prim={"type": "circle", "cx": cx, "cy": cy, "r": rr}, width=wd,
                   dash=[max(0.6, 0.12 * rr), max(0.6, 0.12 * rr)],
                   bbox=(cx - rr - wd / 2, cy - rr - wd / 2, cx + rr + wd / 2, cy + rr + wd / 2), layer="alt")
    return ring, els


def _objects(elements: list, background=(255, 255, 255)) -> list:
    """Bir nesnenin dolgusu, gölgesi ve kenar çizgisi ayrı ayrı çıkmışsa onları tek nesne yap.

    Ör. güneş: sarı yarım + koyu sarı gölge + turuncu kenar -> tek sarı daire, turuncu kontur.
    Küçük nesneler önce kurulur: büyük şeklin üstünde duran güneş kendi parçalarını önce alır.
    """
    import cv2
    from .vektor import Element
    k = 2
    fills = sorted([e for e in elements if e.kind == "fill" and e.layer != "harf" and not e.grad
                    and _size(e) >= 6 and not (e.prim and e.prim.get("type") in ("rect", "rrect", "polygon", "path"))
                    and not getattr(e, "temiz", False)],
                   key=lambda e: e.area)
    used = set()
    out_new = []
    for S in fills:
        if id(S) in used:
            continue
        x0, y0, x1, y1 = S.bbox
        sz = max(x1 - x0, y1 - y0)
        pad = max(2.0, 0.12 * sz)
        X0, Y0, X1, Y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
        # gölge adayları: şekle değen, aynı tonun koyusu, şeklin yanında duran parçalar
        near = (x0 - 2, y0 - 2, x1 + 2, y1 + 2)
        far = (x0 - 0.8 * sz, y0 - 0.8 * sz, x1 + 0.8 * sz, y1 + 0.8 * sz)
        shade_c, group = [], []
        for e in elements:
            if e is S or id(e) in used or e.kind == "text" or e.layer == "harf" or e.grad:
                continue
            b = e.bbox
            if (e.kind == "fill" and not (e.prim and e.prim.get("type") in ("rect", "rrect", "polygon", "path"))
                    and e.area <= 3.0 * S.area
                    and _overlaps(b, near) and b[0] >= far[0] and b[1] >= far[1] and b[2] <= far[2] and b[3] <= far[3]
                    and _is_shade(e.color, S.color)):
                shade_c.append(e)
            elif b[0] >= X0 and b[1] >= Y0 and b[2] <= X1 and b[3] <= Y1:
                group.append(e)
        for e in shade_c:
            X0, Y0 = min(X0, e.bbox[0] - 2), min(Y0, e.bbox[1] - 2)
            X1, Y1 = max(X1, e.bbox[2] + 2), max(Y1, e.bbox[3] + 2)
        W = int(math.ceil((X1 - X0) * k)) + 2
        H = int(math.ceil((Y1 - Y0) * k)) + 2
        if W * H > 6_000_000:
            continue
        base = _mask_of([S], X0, Y0, W, H, k)
        if not base.any():
            continue
        near_base = cv2.dilate(base, np.ones((2 * k + 3, 2 * k + 3), np.uint8)) > 0
        shades = []
        for e in shade_c:
            r = sadakat.rasterize(e, k, X0, Y0, (H, W)) > 0
            if r.any() and int((r & near_base).sum()) >= 4 * k:
                shades.append(e)
        # içte kalan aynı tondaki parçalar da gölgedir
        for e in group:
            if e.kind == "fill" and (_hue_close(e.color, S.color) or _de(e.color, S.color) < 12):
                r = sadakat.rasterize(e, k, X0, Y0, (H, W)) > 0
                if r.any() and float((r & (base > 0)).sum()) / float(r.sum()) >= 0.7:
                    shades.append(e)
        members = [S] + shades
        if S.prim and S.prim.get("type") in ("circle", "ellipse") and sum(e.area for e in shades) < 0.15 * S.area:
            # temiz daireye değen küçük kırıntılar şekli bozmaz: şekil kendi biçimiyle kalır
            fit = _fit_clean(base, X0, Y0, k)
        else:
            fit = _fit_clean(_mask_of(members, X0, Y0, W, H, k), X0, Y0, k)
        if fit[0] is None and fit[1] is None and shades:
            members = [S]
            fit = _fit_clean(base, X0, Y0, k)
        prim, d, v = fit
        if prim is None and d is None:
            continue
        U = _mask_of(members, X0, Y0, W, H, k)
        mem_ids = {id(e) for e in members}
        # kenar çizgisi: şeklin kenarında duran ince parçalar
        ring_r = max(3, int(round(0.025 * sz * k)) + 3)
        inner = max(2, ring_r // 2)
        ring = (cv2.dilate(U, np.ones((2 * ring_r + 1, 2 * ring_r + 1), np.uint8)) > 0) & \
               ~(cv2.erode(U, np.ones((2 * inner + 1, 2 * inner + 1), np.uint8)) > 0)
        # güneş ışınları: dairenin çevresinde dizili küçük parçalar -> ayrı kesikli halka
        rays_el, ray_ids = None, set()
        if prim is not None:
            skip = set(used) | mem_ids
            if S.stroke is not None:
                pool = [e for e in group if _de(e.color, S.stroke) >= 20]
            else:
                pool = group
            rr = _ray_ring(prim, pool, skip, S.color, background)
            if rr is not None:
                rays_el, rays = rr
                ray_ids = {id(e) for e in rays}
        cands = []
        for e in group:
            if id(e) in mem_ids or id(e) in ray_ids:
                continue
            r = sadakat.rasterize(e, k, X0, Y0, (H, W)) > 0
            if not r.any():
                continue
            on_ring = float((r & ring).sum()) / float(r.sum())
            if e.kind == "fill":
                thick = float(cv2.distanceTransform(np.pad(r.astype(np.uint8), 1), cv2.DIST_L2, 3).max()) / k
                thin_ok = thick <= 2.5
            else:
                thin_ok = e.width <= 4.5
            if on_ring >= 0.8 and thin_ok and _de(e.color, S.color) >= 20 and _de(e.color, background) >= 20:
                cands.append((e, r))
        sc, sw = None, 0.0
        if S.stroke is not None and _de(S.stroke, S.color) >= 20 and _de(S.stroke, background) >= 20:
            sc, sw = tuple(S.stroke), S.stroke_width
        edge_members = []
        if sc is None and cands:
            tot = {}
            for e, r in cands:
                tot[tuple(e.color)] = tot.get(tuple(e.color), 0.0) + float(r.sum())
            col = max(tot, key=tot.get)
            same = [(e, r) for e, r in cands if _de(e.color, col) < 15]
            # hepsi şeklin içinden geçen tek bir yatay/dikey doğrunun parçalarıysa (dairenin
            # ortasından geçen ızgara çizgisi) kenar çizgisi değildir
            dz_ = [e.prim for e, _r in same if e.kind == "stroke" and e.prim and e.prim.get("type") == "line"]
            if len(dz_) == len(same) and dz_:
                ys_ = [(q["y1"] + q["y2"]) / 2 for q in dz_]
                xs_ = [(q["x1"] + q["x2"]) / 2 for q in dz_]
                yat = all(abs(q["y1"] - q["y2"]) < 1.0 for q in dz_) and max(ys_) - min(ys_) <= 1.5
                dik = all(abs(q["x1"] - q["x2"]) < 1.0 for q in dz_) and max(xs_) - min(xs_) <= 1.5
                if yat or dik:
                    same = []
            # kenarın yeterince büyük bir kısmını kaplamalı
            edge = (U > 0) & ~(cv2.erode(U, np.ones((3, 3), np.uint8)) > 0)
            cov = np.zeros_like(edge)
            for _e, r in same:
                cov |= r
            cov = cv2.dilate(cov.astype(np.uint8), np.ones((2 * ring_r + 1, 2 * ring_r + 1), np.uint8)) > 0
            if same and edge.any() and float((edge & cov).sum()) / float(edge.sum()) >= 0.35:
                sc = col
                ws = [e.width for e, _r in same if e.kind == "stroke" and e.width > 0]
                if ws:
                    sw = float(np.median(ws))
                else:
                    cs = cv2.findContours(U, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
                    per = max(1.0, sum(cv2.arcLength(c, True) for c in cs) / k)
                    sw = float(np.clip(sum(e.area for e, _r in same if e.kind == "fill") / per, 0.6, 6.0))
        if sc is not None:
            # kenar rengine yakın parçalar konturun kendisidir: ayrıca çizilmez
            # aynı renk ailesinden ama daha açık/koyu kenar parçası (taban çizgisi gibi) yalnız tam
            # kenar üstündeyse konturdur; dışarıda duran parçalar (güneş ışınları) değildir
            eb = (U > 0) & ~(cv2.erode(U, np.ones((3, 3), np.uint8)) > 0)
            tight = cv2.dilate(eb.astype(np.uint8), np.ones((2 * k + 3, 2 * k + 3), np.uint8)) > 0
            edge_members = [e for e, r in cands if _de(e.color, sc) < 25 or
                            (_hue_close(e.color, sc, 30.0) and float((r & tight).sum()) / float(r.sum()) >= 0.8)]
        # dolgu renginde kalan kırıntılar (kenar yumuşatması, ara çizgiler) dolgunun parçasıdır
        Ub = cv2.dilate(U, np.ones((2 * ring_r + 1, 2 * ring_r + 1), np.uint8)) > 0
        for e in group:
            if id(e) in mem_ids or _de(e.color, S.color) >= 10 or (e.kind == "fill" and _size(e) > 0.5 * sz):
                continue
            r = sadakat.rasterize(e, k, X0, Y0, (H, W)) > 0
            if r.any() and float((r & Ub).sum()) / float(r.sum()) >= 0.9:
                edge_members.append(e)
        ne = Element("fill", S.color, prim=prim, d=d or "", area=S.area, bbox=S.bbox, layer=S.layer)
        if sc is not None:
            ne.stroke, ne.stroke_width = sc, max(0.5, sw)
        for e in members + edge_members:
            used.add(id(e))
        out_new.append(ne)
        if rays_el is not None:
            used |= ray_ids
            out_new.append(rays_el)
    return [e for e in elements if id(e) not in used] + _consistent(out_new)


def _consistent(objs: list) -> list:
    """Aynı dolgu rengindeki benzer nesnelerin konturu aynı olsun (çoğunluğun rengi ve kalınlığı)."""
    def kind(e):
        return (e.prim or {}).get("type", "yol")

    groups = []
    for e in objs:
        if e.kind != "fill":
            continue
        for g in groups:
            r = _size(e) / max(1e-6, _size(g[0]))
            if kind(g[0]) == kind(e) and 0.5 <= r <= 2.0 and _de(g[0].color, e.color) < 8:
                g.append(e)
                break
        else:
            groups.append([e])
    for g in groups:
        st = [e for e in g if e.stroke is not None]
        if len(st) < 2:
            continue
        votes = {}
        for e in st:
            key = next((c for c in votes if _de(c, e.stroke) < 12), tuple(e.stroke))
            votes.setdefault(key, []).append(e)
        ranked = sorted(votes.items(), key=lambda kv: len(kv[1]), reverse=True)
        col, best = ranked[0]
        if len(best) < 2 or (len(ranked) > 1 and len(ranked[1][1]) == len(best)):
            continue
        w = float(np.median([e.stroke_width for e in best]))
        for e in st:
            e.stroke, e.stroke_width = col, w
    return objs


# ---------------------------------------------------------------- ana adım
def _uzayan_kenarlar(elements: list) -> list:
    """Kenarları köşelerden dışarı uzayan konturlu kutu (ızgara çizgileri arasında kalan alan):
    kutu konturu yerine dört tam çizgi; çizgilerin köşeden taşan parçaları bu çizgilere katılır."""
    from .vektor import Element
    strokes = [e for e in elements if e.kind == "stroke" and e.layer != "cerceve" and not e.dash]
    pts_of = {}
    for s_ in strokes:
        _k, polys = sadakat.element_polys(s_)
        if polys:
            pts_of[id(s_)] = np.vstack([sadakat_dense(p, c) for p, c in polys])
    drop = set()
    add = []
    for e in elements:
        if not (e.kind == "fill" and e.stroke is not None and e.prim and e.prim.get("type") == "rect"
                and not e.prim.get("rot")):
            continue
        q = e.prim
        X0, Y0, X1, Y1 = q["x"], q["y"], q["x"] + q["w"], q["y"] + q["h"]
        sides = [("v", X0, Y0, Y1), ("v", X1, Y0, Y1), ("h", Y0, X0, X1), ("h", Y1, X0, X1)]
        ext = [[lo, hi] for _o, _c, lo, hi in sides]
        uc = 0
        used = []
        for s_ in strokes:
            if id(s_) in drop or id(s_) not in pts_of or _de(s_.color, e.stroke) >= 20:
                continue
            P = pts_of[id(s_)]
            on_any = np.zeros(len(P), bool)
            for si, (o, c, lo, hi) in enumerate(sides):
                if o == "v":
                    on = (np.abs(P[:, 0] - c) <= 1.5) & ((P[:, 1] < lo - 1) | (P[:, 1] > hi + 1))
                    vals = P[on, 1]
                else:
                    on = (np.abs(P[:, 1] - c) <= 1.5) & ((P[:, 0] < lo - 1) | (P[:, 0] > hi + 1))
                    vals = P[on, 0]
                on_any |= on
                if on.any():
                    # köşeye bitişik olmalı
                    near_lo = vals.max() >= lo - 2.5 and vals.max() <= lo + 0.5
                    near_hi = vals.min() <= hi + 2.5 and vals.min() >= hi - 0.5
                    if (vals < lo).any() and near_lo:
                        ext[si][0] = min(ext[si][0], float(vals.min()))
                    if (vals > hi).any() and near_hi:
                        ext[si][1] = max(ext[si][1], float(vals.max()))
            if on_any.mean() >= 0.85:
                used.append(s_)
        uz = [(ext[si][0] < lo - 2) + (ext[si][1] > hi + 2) for si, (o, c, lo, hi) in enumerate(sides)]
        uc = sum(uz)
        # ızgara: hem dikey hem yatay kenarlar köşelerden taşmalı (yalnız yatay kenarları uzayan
        # ölçek çubuğu parçası ızgara değildir)
        if uc < 4 or not (uz[0] + uz[1]) or not (uz[2] + uz[3]):
            continue
        w = e.stroke_width
        for si, (o, c, lo, hi) in enumerate(sides):
            a_, b_ = ext[si]
            if o == "v":
                pr = {"type": "line", "x1": c, "y1": a_, "x2": c, "y2": b_}
                bb = (c, a_, c, b_)
            else:
                pr = {"type": "line", "x1": a_, "y1": c, "x2": b_, "y2": c}
                bb = (a_, c, b_, c)
            add.append(Element("stroke", e.stroke, prim=pr, width=w, bbox=bb))
        e.stroke, e.stroke_width = None, 0.0
        for s_ in used:
            drop.add(id(s_))
    return [e for e in elements if id(e) not in drop] + add


def _ortulu_birlestir(elements: list) -> list:
    """Üstüne sütunlar oturduğu için parçalanmış düz çizgi (grafiğin yatay ekseni): aynı doğrudaki
    parçalar, aralarındaki boşluğu kutular kapatıyorsa tek çizgi olur."""
    # kutunun kenar çizgisi ve kenar yumuşatması kadar pay
    kut = [(e.bbox, (e.stroke_width / 2 if e.stroke is not None else 0.0) + 1.5)
           for e in elements if e.kind == "fill" and e.prim and e.prim.get("type") in ("rect", "rrect", "polygon")
           and not e.prim.get("rot") and e.layer != "harf"]
    if not kut:
        return elements
    lines = [e for e in elements if e.kind == "stroke" and not e.dash and e.prim and e.prim.get("type") == "line"
             and e.layer != "cerceve"]
    drop = set()
    for yon in ("h", "v"):
        grp = []
        for e in lines:
            p = e.prim
            if yon == "h" and abs(p["y1"] - p["y2"]) < 0.5:
                grp.append((p["y1"], min(p["x1"], p["x2"]), max(p["x1"], p["x2"]), e))
            elif yon == "v" and abs(p["x1"] - p["x2"]) < 0.5:
                grp.append((p["x1"], min(p["y1"], p["y2"]), max(p["y1"], p["y2"]), e))
        grp.sort(key=lambda t: (round(t[0]), t[1]))
        used = set()
        for i, (c, lo, hi, e) in enumerate(grp):
            if id(e) in used:
                continue
            chain = [(c, lo, hi, e)]
            cur_hi = hi
            for c2, lo2, hi2, e2 in grp[i + 1:]:
                if id(e2) in used or abs(c2 - c) > 1.5 or _de(e2.color, e.color) >= 15 or lo2 < cur_hi - 1:
                    continue
                gap_lo, gap_hi = cur_hi, lo2
                if gap_hi - gap_lo > 3:
                    tol = max(2.0, e.width + 1.0)
                    cov = 0.0
                    for (X0, Y0, X1, Y1), m_ in kut:
                        if yon == "h":
                            on = abs(Y1 - c) <= tol + m_ - 1.5 or abs(Y0 - c) <= tol + m_ - 1.5
                            a_, b_ = X0 - m_, X1 + m_
                        else:
                            on = abs(X1 - c) <= tol + m_ - 1.5 or abs(X0 - c) <= tol + m_ - 1.5
                            a_, b_ = Y0 - m_, Y1 + m_
                        if on:
                            cov += max(0.0, min(b_, gap_hi + 1) - max(a_, gap_lo - 1))
                    if cov < 0.8 * (gap_hi - gap_lo):
                        continue
                chain.append((c2, lo2, hi2, e2))
                cur_hi = max(cur_hi, hi2)
            if len(chain) < 2:
                continue
            for _c, _l, _h, ee in chain:
                used.add(id(ee))
            for _c, _l, _h, ee in chain[1:]:
                drop.add(id(ee))
            p = e.prim
            lo0 = min(t[1] for t in chain)
            if yon == "h":
                p["x1"], p["x2"] = lo0, cur_hi
                p["y1"] = p["y2"] = float(np.median([t[0] for t in chain]))
                e.bbox = (lo0, p["y1"], cur_hi, p["y1"])
            else:
                p["y1"], p["y2"] = lo0, cur_hi
                p["x1"] = p["x2"] = float(np.median([t[0] for t in chain]))
                e.bbox = (p["x1"], lo0, p["x1"], cur_hi)
            e.width = float(np.median([t[3].width for t in chain]))

    def kapali(yon, c, g0, g1, wd):
        if g1 - g0 <= 3:
            return True
        tol = max(2.0, wd + 1.0)
        cov = 0.0
        for (X0, Y0, X1, Y1), m_ in kut:
            if yon == "h":
                on = abs(Y1 - c) <= tol + m_ - 1.5 or abs(Y0 - c) <= tol + m_ - 1.5
                a_, b_ = X0 - m_, X1 + m_
            else:
                on = abs(X1 - c) <= tol + m_ - 1.5 or abs(X0 - c) <= tol + m_ - 1.5
                a_, b_ = Y0 - m_, Y1 + m_
            if on:
                cov += max(0.0, min(b_, g1 + 1) - max(a_, g0 - 1))
        return cov >= 0.8 * (g1 - g0)

    # köşeli yolun (eksen ile taban çizgisi) ucundaki düz kol aynı doğrudaki parçayla birleşir
    yollar = []
    for e in elements:
        if (e.kind != "stroke" or e.dash or e.prim or not e.d or "Z" in e.d or e.layer == "cerceve"
                or id(e) in drop):
            continue
        pp = sadakat.flatten(e.d)
        if len(pp) != 1 or len(pp[0][0]) < 3 or not re.fullmatch(r"M[\d.\s-]+(L[\d.\s-]+)+", e.d.strip()):
            continue
        yollar.append((e, [list(map(float, q)) for q in pp[0][0]]))
    for e, P in yollar:
        degisti = False
        for uc in (0, -1):
            pe, pi = P[uc], P[1] if uc == 0 else P[-2]
            if abs(pe[1] - pi[1]) < 0.5 and abs(pe[0] - pi[0]) >= 1:
                yon, c, ileri = "h", pe[1], 1.0 if pe[0] > pi[0] else -1.0
                pos = pe[0]
            elif abs(pe[0] - pi[0]) < 0.5 and abs(pe[1] - pi[1]) >= 1:
                yon, c, ileri = "v", pe[0], 1.0 if pe[1] > pi[1] else -1.0
                pos = pe[1]
            else:
                continue
            adaylar = []
            for l_ in lines:
                if id(l_) in drop or _de(l_.color, e.color) >= 15:
                    continue
                q = l_.prim
                if yon == "h" and abs(q["y1"] - q["y2"]) < 0.5 and abs(q["y1"] - c) <= 1.5:
                    lo, hi = min(q["x1"], q["x2"]), max(q["x1"], q["x2"])
                elif yon == "v" and abs(q["x1"] - q["x2"]) < 0.5 and abs(q["x1"] - c) <= 1.5:
                    lo, hi = min(q["y1"], q["y2"]), max(q["y1"], q["y2"])
                else:
                    continue
                yakin, uzak = (lo, hi) if ileri > 0 else (hi, lo)
                if (yakin - pos) * ileri < -1.0:
                    continue
                adaylar.append(((yakin - pos) * ileri, yakin, uzak, l_))
            for _g, yakin, uzak, l_ in sorted(adaylar, key=lambda t: t[0]):
                g0, g1 = sorted((pos, yakin))
                if not kapali(yon, c, g0, g1, e.width):
                    break
                if (uzak - pos) * ileri > 0:
                    pos = uzak
                drop.add(id(l_))
                degisti = True
            if yon == "h":
                P[uc][0] = pos
            else:
                P[uc][1] = pos
        if degisti:
            e.d = "M" + "L".join(f"{_f(x)} {_f(y)}" for x, y in P)
            A = np.array(P)
            e.bbox = (float(A[:, 0].min()), float(A[:, 1].min()), float(A[:, 0].max()), float(A[:, 1].max()))
    return [e for e in elements if id(e) not in drop]


def _isaret_bagla(elements: list) -> None:
    """Grafik çizgisinin parçaları veri noktalarına (aynı renkte küçük daireler) tam ulaşsın: ucu
    bir dairenin yakınında biten çizgi dairenin merkezine uzatılır."""
    daire = [e for e in elements if e.kind == "fill" and e.prim and e.prim.get("type") == "circle"
             and e.prim["r"] <= 8 and e.layer != "harf"]
    if not daire:
        return
    for s_ in elements:
        if s_.kind != "stroke" or not s_.prim or s_.prim.get("type") != "line":
            continue
        p = s_.prim
        if s_.dash:
            # kesikli sanılan çizgi: aralıklarında aynı renkte işaretler varsa düz çizgidir
            v = np.array([p["x2"] - p["x1"], p["y2"] - p["y1"]], float)
            L = float(np.hypot(*v))
            if L < 1e-6:
                continue
            u = v / L
            on = 0
            for d in daire:
                # veri noktası çizgiden kalındır (kesikli çizginin nokta kırıntıları işaret değil)
                if _de(d.color, s_.color) >= 15 or d.prim["r"] < max(1.2, 0.9 * s_.width):
                    continue
                q = d.prim
                w_ = np.array([q["cx"] - p["x1"], q["cy"] - p["y1"]])
                t = float(w_ @ u)
                if -q["r"] <= t <= L + q["r"] and abs(float(w_[0] * u[1] - w_[1] * u[0])) <= q["r"]:
                    on += 1
            if on < 2:
                continue
            s_.dash = None
        secim = {}
        for kx, ky in (("x1", "y1"), ("x2", "y2")):
            best = None
            for d in daire:
                if _de(d.color, s_.color) >= 15 or d.prim["r"] < max(1.2, 0.9 * s_.width):
                    continue
                q = d.prim
                dd = math.hypot(p[kx] - q["cx"], p[ky] - q["cy"])
                if dd <= q["r"] + max(2.0, 2 * s_.width) + 1.0 and (best is None or dd < best[0]):
                    best = (dd, q["cx"], q["cy"], id(d))
            if best is not None:
                secim[(kx, ky)] = best
        # iki uç aynı işarete bağlanmaz (kısa parça yok olur): yalnız yakın olan uç bağlanır
        if len(secim) == 2:
            (k1, b1), (k2, b2) = secim.items()
            if b1[3] == b2[3]:
                del secim[k2 if b2[0] > b1[0] else k1]
        for (kx, ky), best in secim.items():
            p[kx], p[ky] = best[1], best[2]
        s_.bbox = (min(p["x1"], p["x2"]), min(p["y1"], p["y2"]), max(p["x1"], p["x2"]), max(p["y1"], p["y2"]))


def _hucre_birlestir(elements: list) -> list:
    """Üstünden ızgara çizgileri geçen düz renkli alan (koordinat ızgarası) çizgilerle hücrelere
    bölünmüş, her hücre ızgara renginde konturlu çıkmış olabilir: aynı renkteki, kenarları çakışarak
    bir dikdörtgeni dolduran hücreler tek dikdörtgen olur; hücre kenarları ızgara çizgisi olarak
    aynı renkteki çizgi parçalarıyla birleşip baştan sona kesintisiz çizilir."""
    import cv2
    from .vektor import Element
    huc = [e for e in elements if e.kind == "fill" and e.layer != "harf" and e.prim
           and e.prim.get("type") == "rect" and not e.prim.get("rot") and e.stroke is not None]
    if len(huc) < 3:
        return elements
    out = elements
    kullanildi = set()

    def kutu(e):
        p = e.prim
        if p and p.get("type") == "rect":
            return (p["x"], p["y"], p["x"] + p["w"], p["y"] + p["h"])
        return tuple(e.bbox)

    for e0 in huc:
        if id(e0) in kullanildi:
            continue
        kont = [e for e in huc if id(e) not in kullanildi and _de(e.color, e0.color) < 6
                and _de(e.stroke, e0.stroke) < 15]
        if len(kont) < 3:
            continue
        sw = float(np.median([e.stroke_width for e in kont]))
        kont_id = set(id(e) for e in kont)
        # aynı renkteki bütün parçalar (konturuz, dikdörtgen olmayan): bitişiklik kümesi kutulardan
        grup = kont + [e for e in out if e.kind == "fill" and e.layer != "harf" and id(e) not in kont_id
                       and id(e) not in kullanildi and _de(e.color, e0.color) < 6 and e.bbox[2] - e.bbox[0] >= 2
                       and e.bbox[3] - e.bbox[1] >= 2]
        n = len(grup)
        kut = [kutu(e) for e in grup]
        komsu = [[] for _ in range(n)]
        for i in range(n):
            a = kut[i]
            for j in range(i + 1, n):
                b = kut[j]
                ox = min(a[2], b[2]) - max(a[0], b[0])
                oy = min(a[3], b[3]) - max(a[1], b[1])
                if (ox > 2 * sw and oy >= -(sw + 1.0)) or (oy > 2 * sw and ox >= -(sw + 1.0)):
                    komsu[i].append(j)
                    komsu[j].append(i)
        gor = [False] * n
        for i0 in range(n):
            if gor[i0] or id(grup[i0]) not in kont_id:
                continue
            kume, yig = [], [i0]
            gor[i0] = True
            while yig:
                i = yig.pop()
                kume.append(i)
                for j in komsu[i]:
                    if not gor[j]:
                        gor[j] = True
                        yig.append(j)
            uy = [grup[i] for i in kume]
            kenarli = [e for e in uy if id(e) in kont_id]
            if len(kenarli) < 3:
                continue
            X0 = min(kut[i][0] for i in kume)
            Y0 = min(kut[i][1] for i in kume)
            X1 = max(kut[i][2] for i in kume)
            Y1 = max(kut[i][3] for i in kume)
            Wd, Hd = int(math.ceil(X1 - X0)) + 1, int(math.ceil(Y1 - Y0)) + 1
            if Wd * Hd > 4_000_000:
                continue
            m = np.zeros((Hd, Wd), np.uint8)
            for i in kume:
                b = kut[i]
                m[int(round(b[1] - Y0)):int(round(b[3] - Y0)) + 1, int(round(b[0] - X0)):int(round(b[2] - X0)) + 1] = 1
            k_ = int(2 * math.ceil(sw) + 1)
            m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((k_, k_), np.uint8))
            if float(m.mean()) < 0.97:
                continue
            for e in uy:
                kullanildi.add(id(e))
            # hücre kenarları: ızgara çizgileri
            kenar = {"h": [], "v": []}
            for e in kenarli:
                x0, y0, x1, y1 = kutu(e)
                kenar["h"] += [(y0, x0, x1), (y1, x0, x1)]
                kenar["v"] += [(x0, y0, y1), (x1, y0, y1)]
            sil = set(id(e) for e in uy)
            yeni = []
            # alanın kenarına değen aynı renkteki çizgiler (alanın dışına taşan ızgara) de aday
            for e in out:
                if e.kind != "stroke" or not e.prim or e.prim.get("type") != "line" or _de(e.color, e0.stroke) >= 15:
                    continue
                p = e.prim
                if abs(p["y1"] - p["y2"]) < 0.6 and Y0 - 1 <= p["y1"] <= Y1 + 1:
                    lo, hi = min(p["x1"], p["x2"]), max(p["x1"], p["x2"])
                    if lo <= X1 + 3 and hi >= X0 - 3:
                        kenar["h"].append(((p["y1"] + p["y2"]) / 2, lo, hi))
                elif abs(p["x1"] - p["x2"]) < 0.6 and X0 - 1 <= p["x1"] <= X1 + 1:
                    lo, hi = min(p["y1"], p["y2"]), max(p["y1"], p["y2"])
                    if lo <= Y1 + 3 and hi >= Y0 - 3:
                        kenar["v"].append(((p["x1"] + p["x2"]) / 2, lo, hi))
            for yon in ("h", "v"):
                ks = sorted(kenar[yon])
                kumeler = []
                # (içe kaymış hücre kenarı birkaç piksel yandaki ızgara çizgisidir)
                for c, lo, hi in ks:
                    if kumeler and abs(c - kumeler[-1]["cs"][-1]) <= max(1.5, 2 * sw):
                        kumeler[-1]["parca"].append((lo, hi))
                        kumeler[-1]["cs"].append(c)
                    else:
                        kumeler.append({"c": c, "cs": [c], "parca": [(lo, hi)]})
                for km in kumeler:
                    # konum: boya göre ağırlıklı ortanca (uzun çizgi belirler)
                    cs_ = np.array(km["cs"], float)
                    ls_ = np.array([max(1.0, hi - lo) for lo, hi in km["parca"]])
                    o_ = np.argsort(cs_)
                    c = float(cs_[o_][np.searchsorted(np.cumsum(ls_[o_]), 0.5 * float(ls_.sum()))])
                    parca = list(km["parca"])
                    # aynı doğrudaki aynı renkte çizgi parçaları (alanın dışına taşan ızgara)
                    for e in out:
                        if e.kind != "stroke" or not e.prim or e.prim.get("type") != "line" or id(e) in sil:
                            continue
                        if _de(e.color, e0.stroke) >= 15:
                            continue
                        p = e.prim
                        if yon == "h" and abs(p["y1"] - p["y2"]) < 0.6 and abs((p["y1"] + p["y2"]) / 2 - c) <= max(1.5, 2 * sw):
                            parca.append((min(p["x1"], p["x2"]), max(p["x1"], p["x2"])))
                            sil.add(id(e))
                        elif yon == "v" and abs(p["x1"] - p["x2"]) < 0.6 and abs((p["x1"] + p["x2"]) / 2 - c) <= max(1.5, 2 * sw):
                            parca.append((min(p["y1"], p["y2"]), max(p["y1"], p["y2"])))
                            sil.add(id(e))
                    parca.sort()
                    birlesik = []
                    a_lo, a_hi = (X0, X1) if yon == "h" else (Y0, Y1)
                    for lo, hi in parca:
                        # boşluk küçükse ya da alanın içindeyse (çizgi alanın üstünden geçer) birleşir
                        if birlesik and (lo <= birlesik[-1][1] + max(3.0, 2 * sw)
                                         or (birlesik[-1][1] >= a_lo - 3 and lo <= a_hi + 3)):
                            birlesik[-1][1] = max(birlesik[-1][1], hi)
                        else:
                            birlesik.append([lo, hi])
                    for lo, hi in birlesik:
                        if yon == "h":
                            pr = {"type": "line", "x1": lo, "y1": c, "x2": hi, "y2": c}
                        else:
                            pr = {"type": "line", "x1": c, "y1": lo, "x2": c, "y2": hi}
                        yeni.append(Element("stroke", e0.stroke, prim=pr, width=sw, cap="butt",
                                            bbox=(min(pr["x1"], pr["x2"]), min(pr["y1"], pr["y2"]),
                                                  max(pr["x1"], pr["x2"]), max(pr["y1"], pr["y2"]))))
            alan = Element("fill", e0.color, prim={"type": "rect", "x": X0, "y": Y0, "w": X1 - X0, "h": Y1 - Y0},
                           area=(X1 - X0) * (Y1 - Y0), bbox=(X0, Y0, X1, Y1), layer="alt")
            out = [alan] + [e for e in out if id(e) not in sil] + yeni
    return out


def _hale_cizgiler(strokes: list, background) -> list:
    """Yumuşak kenarlı kalın çizginin kenar hâlesi: koyu bir çizginin hemen yanında ona paralel
    uzanan, onun zeminle karışımı (aynı tonun açığı) çizgi ayrı bir çizgi değildir."""
    bgv = np.asarray(background, float)
    items = []
    for s_ in strokes:
        if not s_.prim or s_.prim.get("type") != "line" or s_.layer == "cerceve":
            continue
        p = s_.prim
        if abs(p["y1"] - p["y2"]) < 0.6:
            items.append((s_, "h", (p["y1"] + p["y2"]) / 2, min(p["x1"], p["x2"]), max(p["x1"], p["x2"])))
        elif abs(p["x1"] - p["x2"]) < 0.6:
            items.append((s_, "v", (p["x1"] + p["x2"]) / 2, min(p["y1"], p["y2"]), max(p["y1"], p["y2"])))
    drop = set()
    for s1, o1, c1, a1, b1 in items:
        L1 = b1 - a1
        if L1 <= 0:
            continue
        C1 = np.asarray(s1.color, float)
        for s2, o2, c2, a2, b2 in items:
            if s2 is s1 or o2 != o1 or id(s2) in drop:
                continue
            # hâle çizgiye bitişiktir (aralarında boşluk yok); yakın ama ayrık paralel çizgiler
            # (Romen rakamının çubukları) hâle değildir
            if abs(c1 - c2) > 1.0 + (s1.width + s2.width) / 2:
                continue
            if min(b1, b2) - max(a1, a2) < 0.7 * L1:
                continue
            C2 = np.asarray(s2.color, float)
            if float(C2.mean()) >= float(C1.mean()) - 15:
                continue
            AB = bgv - C2
            nab = float(AB @ AB)
            if nab < 1e-6:
                continue
            t = float((C1 - C2) @ AB / nab)
            if 0.1 <= t <= 0.95 and float(np.linalg.norm(C1 - (C2 + t * AB))) <= 35:
                drop.add(id(s1))
                break
    return [s_ for s_ in strokes if id(s_) not in drop]


def _isaret_boyu(elements: list) -> None:
    """Grafik çizgisi üstündeki veri noktaları (aynı renkte, çizginin geçtiği küçük daireler) aynı
    boyda: tasarımcı bir serinin işaretlerini tek boyda çizer; pikselden ölçülen yarıçap oynar."""
    daire = [e for e in elements if e.kind == "fill" and e.prim and e.prim.get("type") == "circle"
             and e.prim["r"] <= 8 and e.layer != "harf"]
    if len(daire) < 3:
        return
    yollar = []
    for s_ in elements:
        if s_.kind != "stroke" or s_.layer == "harf":
            continue
        p = s_.prim or {}
        if p.get("type") == "line":
            yollar.append((s_, np.array([[p["x1"], p["y1"]], [p["x2"], p["y2"]]], float)))
        elif not p and s_.d:
            for P, _kap in sadakat.flatten(s_.d):
                if len(P) >= 2:
                    yollar.append((s_, np.asarray(P, float)))
    if not yollar:
        return
    gruplar = []
    for d in daire:
        q = d.prim
        c = np.array([q["cx"], q["cy"]])
        ustunde = False
        for s_, P in yollar:
            if _de(s_.color, d.color) >= 15 or q["r"] < max(1.2, 0.9 * s_.width):
                continue
            a_, b_ = P[:-1], P[1:]
            v = b_ - a_
            n2 = np.maximum((v * v).sum(axis=1), 1e-9)
            t = np.clip(((c - a_) * v).sum(axis=1) / n2, 0, 1)
            dist = np.hypot(*(a_ + t[:, None] * v - c).T)
            if float(dist.min()) <= max(1.0, 0.5 * q["r"]):
                ustunde = True
                break
        if not ustunde:
            continue
        for g in gruplar:
            if _de(g[0].color, d.color) < 15:
                g.append(d)
                break
        else:
            gruplar.append([d])
    cizgiler = [s_ for s_ in elements if s_.kind == "stroke" and s_.prim and s_.prim.get("type") == "line"
                and not s_.dash and s_.layer != "harf"]
    for g in gruplar:
        if len(g) < 3:
            continue
        rm = float(np.median([d.prim["r"] for d in g]))
        for d in g:
            q = d.prim
            if 0.6 * rm <= q["r"] <= 1.6 * rm:
                q["r"] = rm
                d.bbox = (q["cx"] - rm, q["cy"] - rm, q["cx"] + rm, q["cy"] + rm)
                d.area = math.pi * rm * rm
        # aynı serinin daireye dönüşmemiş işareti (ızgara çizgisinin kestiği, çizgi kökleri değen küçük
        # leke): iki çizgi parçasının buluştuğu yerde, işaret boyunda ise o da aynı daire
        for e in elements:
            if e.kind != "fill" or e.layer == "harf" or _de(e.color, g[0].color) >= 15:
                continue
            if e.prim and e.prim.get("type") not in ("polygon", "path", "ellipse"):
                continue
            x0, y0, x1, y1 = e.bbox
            bw, bh = x1 - x0, y1 - y0
            if not (1.2 * rm <= max(bw, bh) <= 3.5 * rm and min(bw, bh) >= 1.2 * rm):
                continue
            uclar = []
            pay = max(2.0, rm)
            for s_ in cizgiler:
                if _de(s_.color, e.color) >= 15:
                    continue
                p = s_.prim
                for kx, ky, ox, oy in (("x1", "y1", "x2", "y2"), ("x2", "y2", "x1", "y1")):
                    if x0 - pay <= p[kx] <= x1 + pay and y0 - pay <= p[ky] <= y1 + pay:
                        uclar.append((s_, kx, ky, np.array([p[kx], p[ky]]), np.array([p[ox], p[oy]])))
            if len(uclar) != 2:
                continue
            (s1, _k1, _l1, a1, b1), (s2, _k2, _l2, a2, b2) = uclar
            if s1 is s2:
                continue
            d1, d2 = a1 - b1, a2 - b2
            den = float(d1[0] * d2[1] - d1[1] * d2[0])
            if abs(den) < 1e-6 * float(np.hypot(*d1) * np.hypot(*d2)) or abs(den) < 1e-9:
                continue
            t = float((a2 - a1)[0] * d2[1] - (a2 - a1)[1] * d2[0]) / den
            c = a1 + t * d1
            if not (x0 - 1 <= c[0] <= x1 + 1 and y0 - 1 <= c[1] <= y1 + 1):
                continue
            e.prim = {"type": "circle", "cx": float(c[0]), "cy": float(c[1]), "r": rm}
            e.d = ""
            e.bbox = (float(c[0]) - rm, float(c[1]) - rm, float(c[0]) + rm, float(c[1]) + rm)
            e.area = math.pi * rm * rm
            for s_, kx, ky, _a, _b in uclar:
                s_.prim[kx], s_.prim[ky] = float(c[0]), float(c[1])
                p = s_.prim
                s_.bbox = (min(p["x1"], p["x2"]), min(p["y1"], p["y2"]), max(p["x1"], p["x2"]), max(p["y1"], p["y2"]))


def _ayni_simgeler(elements: list) -> list:
    """Tekrarlanan simge (aynı renkte, aynı boyda daireler: güneş, nokta) hep aynı çizilir: yarıçap
    ortak, kontur birçoğunda varsa hepsinde (pikselden kimi konturlu kimi konturuz çıkabilir);
    azında bulunan eş merkezli ayrı halka atılır."""
    daire = [e for e in elements if e.kind == "fill" and e.prim and e.prim.get("type") == "circle"
             and e.layer != "harf" and e.prim["r"] >= 2.0]
    if len(daire) < 3:
        return elements
    gruplar = []
    for d in sorted(daire, key=lambda e: e.prim["r"]):
        for g in gruplar:
            rm = float(np.median([q.prim["r"] for q in g]))
            if _de(g[0].color, d.color) < 12 and abs(d.prim["r"] - rm) <= 0.25 * rm:
                g.append(d)
                break
        else:
            gruplar.append([d])
    halkalar = [e for e in elements if e.kind == "stroke" and e.prim and e.prim.get("type") == "circle"]
    drop = set()
    for g in gruplar:
        if len(g) < 3:
            continue
        rm = float(np.median([q.prim["r"] for q in g]))
        konturlu = [q for q in g if q.stroke is not None]
        if len(konturlu) >= 0.4 * len(g):
            renkler = []
            for q in konturlu:
                for r_ in renkler:
                    if _de(r_[0].stroke, q.stroke) < 15:
                        r_.append(q)
                        break
                else:
                    renkler.append([q])
            en = max(renkler, key=len)
            sc = en[0].stroke
            sw = float(np.median([q.stroke_width for q in en]))
            for q in g:
                q.stroke, q.stroke_width = sc, sw
        else:
            for q in g:
                q.stroke, q.stroke_width = None, 0.0
        for q in g:
            p = q.prim
            p["r"] = rm
            q.bbox = (p["cx"] - rm, p["cy"] - rm, p["cx"] + rm, p["cy"] + rm)
            q.area = math.pi * rm * rm
        # üstünden çizgi geçtiği için daireye dönüşmemiş aynı simge: dış çizgisinin çoğu bu boyda
        # bir çemberin üstündeyse o da aynı daire
        for e in elements:
            if e.kind != "fill" or e.layer == "harf" or id(e) in drop or _de(e.color, g[0].color) >= 12:
                continue
            if e.prim and e.prim.get("type") not in ("polygon", "path", "ellipse", "rrect"):
                continue
            if e.prim and e.prim.get("type") == "rrect":
                # köşe yarıçapı kenarın yarısı kadar olan kare: daire
                p = e.prim
                if not p.get("rot") and abs(p["w"] - p["h"]) <= 0.15 * max(p["w"], p["h"]) \
                        and p.get("r", 0) >= 0.8 * min(p["w"], p["h"]) / 2 and abs(max(p["w"], p["h"]) / 2 - rm) <= 0.3 * rm:
                    cx, cy = p["x"] + p["w"] / 2, p["y"] + p["h"] / 2
                    e.prim = {"type": "circle", "cx": float(cx), "cy": float(cy), "r": rm}
                    e.stroke, e.stroke_width = g[0].stroke, g[0].stroke_width
                    e.bbox = (cx - rm, cy - rm, cx + rm, cy + rm)
                    e.area = math.pi * rm * rm
                    g.append(e)
                continue
            if e.prim and e.prim.get("type") == "ellipse":
                # aynı boyda elips (üstünden çizgi geçtiği için biraz basık oturmuş): aynı daire
                p = e.prim
                if 0.7 * rm <= min(p["rx"], p["ry"]) and max(p["rx"], p["ry"]) <= 1.3 * rm:
                    cx, cy = p["cx"], p["cy"]
                    e.prim = {"type": "circle", "cx": float(cx), "cy": float(cy), "r": rm}
                    e.stroke, e.stroke_width = g[0].stroke, g[0].stroke_width
                    e.bbox = (cx - rm, cy - rm, cx + rm, cy + rm)
                    e.area = math.pi * rm * rm
                    g.append(e)
                continue
            x0, y0, x1, y1 = e.bbox
            if not (1.3 * rm <= max(x1 - x0, y1 - y0) <= 2.6 * rm and min(x1 - x0, y1 - y0) >= 0.9 * rm):
                continue
            if e.prim and e.prim.get("type") == "polygon":
                P = np.asarray(e.prim["pts"], float)
            elif e.d:
                ps = sadakat.flatten(e.d)
                if not ps:
                    continue
                P = np.asarray(max(ps, key=lambda t: len(t[0]))[0], float)
            else:
                continue
            if len(P) < 8:
                continue
            fit = egri.circle_fit(P)
            if fit is None:
                continue
            for _ in range(2):
                dd = np.abs(np.hypot(P[:, 0] - fit[0], P[:, 1] - fit[1]) - fit[2])
                ic = P[dd <= max(0.8, 0.12 * fit[2])]
                if len(ic) < 0.5 * len(P) or len(ic) < 6:
                    fit = None
                    break
                fit = egri.circle_fit(ic)
                if fit is None:
                    break
            if fit is None or abs(fit[2] - rm) > 0.25 * rm or fit[3] > 0.6:
                continue
            cx, cy = fit[0], fit[1]
            e.prim = {"type": "circle", "cx": float(cx), "cy": float(cy), "r": rm}
            e.d = ""
            e.stroke, e.stroke_width = g[0].stroke, g[0].stroke_width
            e.bbox = (cx - rm, cy - rm, cx + rm, cy + rm)
            e.area = math.pi * rm * rm
            g.append(e)
        hs = [h for h in halkalar
              if any(math.hypot(h.prim["cx"] - q.prim["cx"], h.prim["cy"] - q.prim["cy"]) <= 1.0
                     and abs(h.prim["r"] - rm) <= 0.35 * rm for q in g)]
        if hs and len(hs) <= 0.4 * len(g):
            drop.update(id(h) for h in hs)
        # konturlu simgenin kenarındaki, kontur renginde ayrı kırıntılar (tırtıklı kenarın parçaları)
        if g[0].stroke is not None:
            for e in elements:
                if e.kind != "fill" or e.layer == "harf" or e in g or _de(e.color, g[0].stroke) >= 20:
                    continue
                x0, y0, x1, y1 = e.bbox
                for q in g:
                    p = q.prim
                    if (x0 >= p["cx"] - rm - 2.5 and x1 <= p["cx"] + rm + 2.5 and y0 >= p["cy"] - rm - 2.5
                            and y1 <= p["cy"] + rm + 2.5):
                        drop.add(id(e))
                        break
    if not drop:
        return elements
    return [e for e in elements if id(e) not in drop]


def _kesik_ortu(elements: list) -> None:
    """Kesikli sanılan düz çizgi: aralıkları üstüne oturan kutular (eksen üstündeki sütunlar)
    kapatıyorsa çizgi düzdür, kesikleri kutuların arası görünen parçalarıdır."""
    kut = [e.prim for e in elements if e.kind == "fill" and e.prim and e.prim.get("type") in ("rect", "rrect")
           and not e.prim.get("rot") and e.layer != "harf"]
    for e in elements:
        if e.kind != "stroke" or not e.dash or not e.prim or e.prim.get("type") != "line":
            continue
        p = e.prim
        x1, y1, x2, y2 = p["x1"], p["y1"], p["x2"], p["y2"]
        yatay = abs(y1 - y2) < 0.5
        dikey = abs(x1 - x2) < 0.5
        if not (yatay or dikey) or len(e.dash) != 2:
            continue
        gap = e.dash[1]
        L = abs(x2 - x1) + abs(y2 - y1)
        n_gap = L / max(1e-6, sum(e.dash))
        hit = 0
        tol = max(1.5, e.width)
        for q in kut:
            X0, Y0, X1, Y1 = q["x"], q["y"], q["x"] + q["w"], q["y"] + q["h"]
            if yatay:
                on = abs(Y1 - y1) <= tol or abs(Y0 - y1) <= tol
                span, lo, hi = X1 - X0, min(x1, x2) - 2, max(x1, x2) + 2
                inside = X0 >= lo and X1 <= hi
            else:
                on = abs(X1 - x1) <= tol or abs(X0 - x1) <= tol
                span, lo, hi = Y1 - Y0, min(y1, y2) - 2, max(y1, y2) + 2
                inside = Y0 >= lo and Y1 <= hi
            if on and inside and span >= 0.6 * gap:
                hit += 1
        if hit >= 2 and hit >= 0.6 * n_gap:
            e.dash = None
            e.cap = "butt"
            # uçtaki kutuların altından da geçer
            for q in kut:
                X0, Y0, X1, Y1 = q["x"], q["y"], q["x"] + q["w"], q["y"] + q["h"]
                if yatay and (abs(Y1 - y1) <= tol or abs(Y0 - y1) <= tol):
                    if X0 <= max(x1, x2) + gap * 1.2 and X1 > max(x1, x2):
                        if x2 >= x1:
                            p["x2"] = x2 = X1
                        else:
                            p["x1"] = x1 = X1
                    if X1 >= min(x1, x2) - gap * 1.2 and X0 < min(x1, x2):
                        if x1 <= x2:
                            p["x1"] = x1 = X0
                        else:
                            p["x2"] = x2 = X0
                elif dikey and (abs(X1 - x1) <= tol or abs(X0 - x1) <= tol):
                    if Y0 <= max(y1, y2) + gap * 1.2 and Y1 > max(y1, y2):
                        if y2 >= y1:
                            p["y2"] = y2 = Y1
                        else:
                            p["y1"] = y1 = Y1
                    if Y1 >= min(y1, y2) - gap * 1.2 and Y0 < min(y1, y2):
                        if y1 <= y2:
                            p["y1"] = y1 = Y0
                        else:
                            p["y2"] = y2 = Y0
            e.bbox = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            # çizginin kutular arasında dolgu olarak kalmış parçaları artık çizginin kendisi
            bx0, by0, bx1, by1 = e.bbox
            r_ = e.width / 2 + 1.0
            for o in elements:
                if (o.kind == "fill" and o is not e and o.layer != "harf" and _de(o.color, e.color) < 15
                        and o.bbox[0] >= bx0 - r_ and o.bbox[2] <= bx1 + r_
                        and o.bbox[1] >= by0 - r_ and o.bbox[3] <= by1 + r_):
                    o.layer = "_sil"
    elements[:] = [o for o in elements if o.layer != "_sil"]


def _ice_al(fills: list) -> None:
    """Konturlu şeklin kenarına dayanan iç kutu (köşedeki kare, başlık bandı) konturun içine
    çekilir: tasarımcının çizdiği gibi kontur görünür kalır, iç şekil onu örtmez."""
    kut = [e for e in fills if e.prim and e.prim.get("type") in ("rect", "rrect") and not e.prim.get("rot")
           and e.layer != "harf"]
    dis = [e for e in fills if e.prim and e.prim.get("type") in ("rect", "rrect", "polygon", "path")
           and not e.prim.get("rot") and e.stroke is not None and e.stroke_width > 0
           and not getattr(e, "panel", False) and e.layer != "harf"]

    def kenarlar(S):
        P = sekil.prim_points(S.prim)
        Q = np.roll(P, -1, axis=0)
        dik, yat = [], []
        for (x1, y1), (x2, y2) in zip(P, Q):
            if abs(x1 - x2) < 0.3 and abs(y1 - y2) > 1:
                dik.append((x1, min(y1, y2), max(y1, y2)))
            elif abs(y1 - y2) < 0.3 and abs(x1 - x2) > 1:
                yat.append((y1, min(x1, x2), max(x1, x2)))
        return dik, yat

    def dayali(v, lo, hi, kenar):
        for c, a_, b_ in kenar:
            if abs(c - v) <= 1.5 and min(hi, b_) - max(lo, a_) >= 0.8 * (hi - lo):
                return c
        return None
    for o in kut:
        if o.stroke is not None:
            continue
        p = o.prim
        ox0, oy0, ox1, oy1 = p["x"], p["y"], p["x"] + p["w"], p["y"] + p["h"]
        for S in dis:
            if S is o or S.area <= o.area:
                continue
            X0, Y0, X1, Y1 = S.bbox
            if ox0 < X0 - 1.5 or oy0 < Y0 - 1.5 or ox1 > X1 + 1.5 or oy1 > Y1 + 1.5:
                continue
            dik, yat = kenarlar(S)
            h = S.stroke_width / 2
            n0 = (ox0, oy0, ox1, oy1)
            c_ = dayali(ox0, oy0, oy1, dik)
            if c_ is not None:
                ox0 = c_ + h
            c_ = dayali(ox1, oy0, oy1, dik)
            if c_ is not None:
                ox1 = c_ - h
            c_ = dayali(oy0, ox0, ox1, yat)
            if c_ is not None:
                oy0 = c_ + h
            c_ = dayali(oy1, ox0, ox1, yat)
            if c_ is not None:
                oy1 = c_ - h
            if (ox0, oy0, ox1, oy1) != n0 and ox1 - ox0 > 1 and oy1 - oy0 > 1:
                p["x"], p["y"], p["w"], p["h"] = ox0, oy0, ox1 - ox0, oy1 - oy0
                if p["type"] == "rrect":
                    p["r"] = min(p["r"], p["w"] / 2, p["h"] / 2)
                o.bbox = (ox0, oy0, ox1, oy1)
                break


def _renk_birligi(elements: list) -> None:
    """Birbirine çok yakın çizgi/kontur renklerini tek renk yap, aynı renkteki çizgilerin
    kalınlıklarını kümele: tasarımcı birkaç renk ve birkaç kalınlık kullanır."""
    import cv2
    refs = []
    for e in elements:
        if e.layer == "harf":
            continue
        if e.kind == "stroke" and e.color is not None:
            refs.append([e, "color", "width", e.color, _size(e)])
        elif e.kind == "fill" and e.stroke is not None:
            b = e.bbox
            refs.append([e, "stroke", "stroke_width", e.stroke, 2.0 * ((b[2] - b[0]) + (b[3] - b[1]))])
    if len(refs) < 2:
        return
    cols = np.array([r[3] for r in refs], np.float32)[None] / 255.0
    labc = cv2.cvtColor(cols, cv2.COLOR_RGB2Lab)[0]
    order = sorted(range(len(refs)), key=lambda i: -refs[i][4])
    groups = []
    for i in order:
        for g in groups:
            if float(np.linalg.norm(labc[i] - labc[g[0]])) <= 10.0:
                g.append(i)
                break
        else:
            groups.append([i])
    for g in groups:
        col = tuple(int(v) for v in refs[g[0]][3])
        for i in g:
            setattr(refs[i][0], refs[i][1], col)
        if len(g) >= 2:
            vals = [float(getattr(refs[i][0], refs[i][2])) for i in g]
            new = _kumele(vals, 0.12, 0.08)
            for i, v in zip(g, new):
                setattr(refs[i][0], refs[i][2], float(v))


def _izgara_kesik(elements: list) -> list:
    """Sütunların arkasından geçen kesikli ızgara çizgisi: aynı doğrudaki kesikli parçalar ve tek
    kesikler toplanır; çizgi kutuların arasında görünen her aralıkta aynı desenle, aynı hizada
    (kesikler tek bir çizginin kesikleri gibi) yeniden çizilir."""
    from .vektor import Element
    kut = []
    for e in elements:
        if (e.kind == "fill" and e.prim and e.prim.get("type") in ("rect", "rrect", "polygon")
                and not e.prim.get("rot") and e.layer != "harf"):
            m_ = (e.stroke_width / 2 if e.stroke is not None else 0.0) + 0.5
            kut.append((e.bbox[0] - m_, e.bbox[1] - m_, e.bbox[2] + m_, e.bbox[3] + m_))
    if not kut:
        return elements
    drop = set()
    add = []
    for yon in ("h", "v"):
        items = []
        for e in elements:
            if e.kind != "stroke" or not e.prim or e.prim.get("type") != "line" or e.layer == "cerceve":
                continue
            if e.dash and len(e.dash) != 2:
                continue
            q = e.prim
            if yon == "h" and abs(q["y1"] - q["y2"]) < 0.6:
                items.append(((q["y1"] + q["y2"]) / 2, min(q["x1"], q["x2"]), max(q["x1"], q["x2"]), e))
            elif yon == "v" and abs(q["x1"] - q["x2"]) < 0.6:
                items.append(((q["x1"] + q["x2"]) / 2, min(q["y1"], q["y2"]), max(q["y1"], q["y2"]), e))
        items.sort(key=lambda t: t[0])
        kullanildi = set()
        for ref in sorted([t for t in items if t[3].dash], key=lambda t: -(t[2] - t[1])):
            if id(ref[3]) in kullanildi:
                continue
            c0, re_ = ref[0], ref[3]
            D, G = re_.dash
            P = D + G
            if D < 1.0 or G < 0.8:
                continue
            mem = []
            for t in items:
                c, lo, hi, e = t
                if id(e) in kullanildi or abs(c - c0) > 1.2 or _de(e.color, re_.color) >= 14:
                    continue
                if abs(e.width - re_.width) > max(0.6, 0.5 * re_.width):
                    continue
                if e.dash:
                    # deseni farklı ölçülmüş kısa kesikli parça (birkaç kesikten) da bu çizginin parçası
                    if abs(sum(e.dash) - P) > 0.25 * P and hi - lo > 4.5 * P:
                        continue
                elif hi - lo > 2 * P + 0.5:
                    continue        # en çok iki kesiğin birleştiği parça (üstünden çizgi geçmiş)
                mem.append(t)
            if len(mem) < 2:
                continue
            # çizgiyi kesen kutular
            ort = []
            for X0, Y0, X1, Y1 in kut:
                if yon == "h":
                    if Y0 <= c0 <= Y1:
                        ort.append((X0, X1))
                elif X0 <= c0 <= X1:
                    ort.append((Y0, Y1))
            ort.sort()

            def ortulu(g0, g1):
                # [g0, g1] aralığının kutularca örtülen payı
                if g1 <= g0:
                    return 1.0
                cov, cur = 0.0, g0
                for a_, b_ in ort:
                    if b_ <= cur or a_ >= g1:
                        continue
                    cov += min(b_, g1) - max(a_, cur)
                    cur = max(cur, min(b_, g1))
                return cov / (g1 - g0)
            # zincirler: ardışık parçalar arası ya bir iki kesik aralığı ya da kutuların örttüğü yer
            # (yan yana iki grafiğin aynı hizadaki çizgileri birleşmesin)
            mem.sort(key=lambda t: t[1])
            zincirler = [[mem[0]]]
            for t in mem[1:]:
                g0, g1 = zincirler[-1][-1][2], t[1]
                aci = g1 - g0
                if aci <= 3.2 * P:
                    zincirler[-1].append(t)
                    continue
                # kutularca örtülmeyen kısım iki üç aralıktan uzun olmamalı
                if ortulu(g0, g1) * aci >= aci - 3.2 * P:
                    zincirler[-1].append(t)
                    continue
                zincirler.append([t])
            for zn in zincirler:
                if len(zn) < 2:
                    continue
                lo = min(t[1] for t in zn)
                hi = max(t[2] for t in zn)
                aral = []
                cur = lo
                for a_, b_ in ort:
                    if b_ <= lo or a_ >= hi:
                        continue
                    if a_ > cur:
                        aral.append((cur, min(a_, hi)))
                    cur = max(cur, b_)
                if cur < hi:
                    aral.append((cur, hi))
                if len(aral) < 2 and not any(t[3].dash is None for t in zn):
                    continue
                # her parça görünen bir aralıkta olmalı
                if any(not any(a_ - 0.8 <= (t[1] + t[2]) / 2 <= b_ + 0.8 for a_, b_ in aral) for t in zn):
                    continue
                # desenin hizası: parçaların başlangıçlarının adıma göre ortak kalanı
                # (deseni farklı ölçülmüş kesikli parçanın başı güvenilmez)
                bas = [t[1] for t in zn if not t[3].dash or abs(sum(t[3].dash) - P) <= 0.25 * P]
                if not bas:
                    continue
                ang = np.array([2 * math.pi * (b0_ % P) / P for b0_ in bas])
                Cm, Sm = float(np.cos(ang).mean()), float(np.sin(ang).mean())
                if math.hypot(Cm, Sm) < 0.6:
                    continue        # başlangıçlar tek bir desene oturmuyor
                xs = (math.atan2(Sm, Cm) % (2 * math.pi)) / (2 * math.pi) * P
                yeni = []
                for a_, b_ in aral:
                    if b_ - a_ < 0.6:
                        continue
                    k0 = math.ceil((a_ - xs) / P - 1e-6)
                    once = xs + (k0 - 1) * P + D        # önceki kesiğin sonu
                    if once - a_ >= 0.8:
                        yeni.append((a_, min(once, b_), None))
                    s_ = xs + k0 * P
                    if b_ - s_ >= 0.8:
                        n_ = math.floor((b_ - s_) / P)
                        son = min(b_, s_ + n_ * P + D)
                        if son - s_ <= D + 0.01:
                            yeni.append((s_, son, None))
                        else:
                            yeni.append((s_, son, [D, G]))
                if not yeni:
                    continue
                for t in zn:
                    drop.add(id(t[3]))
                    kullanildi.add(id(t[3]))
                for a_, b_, ds in yeni:
                    if yon == "h":
                        pr = {"type": "line", "x1": a_, "y1": c0, "x2": b_, "y2": c0}
                        bb = (a_, c0, b_, c0)
                    else:
                        pr = {"type": "line", "x1": c0, "y1": a_, "x2": c0, "y2": b_}
                        bb = (c0, a_, c0, b_)
                    add.append(Element("stroke", re_.color, prim=pr, width=re_.width, dash=ds, cap="butt",
                                       bbox=bb))
    if not drop:
        return elements
    return [e for e in elements if id(e) not in drop] + add


def _yol_parcala(e):
    """Açık tek parça çizgiyi (başlangıç, [(komut, değerler)]) olarak ver; olmuyorsa None."""
    if e.prim and e.prim.get("type") == "line":
        q = e.prim
        return (q["x1"], q["y1"]), [("L", ((q["x2"], q["y2"]),))]
    if e.prim or not e.d or "Z" in e.d:
        return None
    toks = sadakat._TOK.findall(e.d)
    if not toks or toks[0] != "M" or toks.count("M") != 1:
        return None
    i, cmd = 1, None
    try:
        start = (float(toks[i]), float(toks[i + 1]))
        i += 2
        segs = []
        while i < len(toks):
            if toks[i] in "LCA":
                cmd = toks[i]
                i += 1
            if cmd == "L":
                segs.append(("L", ((float(toks[i]), float(toks[i + 1])),)))
                i += 2
            elif cmd == "C":
                v = [float(t) for t in toks[i:i + 6]]
                segs.append(("C", ((v[0], v[1]), (v[2], v[3]), (v[4], v[5]))))
                i += 6
            elif cmd == "A":
                v = [float(t) for t in toks[i:i + 7]]
                segs.append(("A", (v[0], v[1], v[2], int(v[3]), int(v[4]), (v[5], v[6]))))
                i += 7
            else:
                return None
    except (ValueError, IndexError):
        return None
    return (start, segs) if segs else None


def _yol_son(seg):
    return seg[1][-1]


def _yol_ters(start, segs):
    """Yolu tersten yaz."""
    pts = [start] + [_yol_son(sg) for sg in segs]
    out = []
    for j in range(len(segs) - 1, -1, -1):
        c, v = segs[j]
        hedef = pts[j]
        if c == "L":
            out.append(("L", (hedef,)))
        elif c == "C":
            out.append(("C", (v[1], v[0], hedef)))
        else:
            out.append(("A", (v[0], v[1], v[2], v[3], 1 - v[4], hedef)))
    return pts[-1], out


def _yol_yaz(start, segs) -> str:
    parts = [f"M{_f(start[0])} {_f(start[1])}"]
    for c, v in segs:
        if c == "L":
            parts.append(f"L{_f(v[0][0])} {_f(v[0][1])}")
        elif c == "C":
            parts.append("C" + " ".join(f"{_f(a)} {_f(b)}" for a, b in v))
        else:
            parts.append(f"A{_f(v[0])} {_f(v[1])} {_f(v[2])} {v[3]} {v[4]} {_f(v[5][0])} {_f(v[5][1])}")
    return "".join(parts)


def _uc_birlestir(elements: list) -> list:
    """Uçları bir iki piksel aralıkla karşılıklı duran, aynı yönde süren aynı renkli iki çizgi
    (kenar yumuşatmasından kopmuş grafik çizgisi) tek yol olur."""
    adays = []
    for e in elements:
        if e.kind != "stroke" or e.dash or e.layer == "cerceve":
            continue
        y = _yol_parcala(e)
        if y is None:
            continue
        _k, polys = sadakat.element_polys(e)
        if not polys or len(polys) != 1 or len(polys[0][0]) < 2:
            continue
        P = np.asarray(polys[0][0], float)
        adays.append([e, y, P])
    if len(adays) < 2:
        return elements
    drop = set()

    def uclar(P):
        # uç noktası ve dışa doğru yön (uçtan birkaç piksel içeriden)
        res = []
        for uc in (0, -1):
            pe = P[uc]
            sira = P if uc == -1 else P[::-1]
            d = np.hypot(*(sira - pe).T)
            k = np.flatnonzero(d >= 3.0)
            ic = sira[k[-1]] if len(k) else sira[0]
            v = pe - ic
            n = float(np.hypot(*v))
            res.append((pe, v / n if n > 1e-6 else np.zeros(2)))
        return res
    degisti = True
    while degisti:
        degisti = False
        canli = [a for a in adays if id(a[0]) not in drop]
        U = [(a, i, pe, v) for a in canli for i, (pe, v) in enumerate(uclar(a[2]))]
        for ai, (a, ia, pa, va) in enumerate(U):
            ea = a[0]
            esl = []
            yakin = 0
            for b, ib, pb, vb in U:
                if b is a:
                    continue
                dd = float(np.hypot(*(pa - pb)))
                if dd <= max(2.5, 2.0 * ea.width):
                    yakin += 1
                    eb = b[0]
                    if (_de(ea.color, eb.color) < 12 and 0.6 <= ea.width / max(eb.width, 1e-6) <= 1.67
                            and float(va @ -vb) >= 0.5):
                        esl.append((dd, b, ib, pb))
            if yakin != 1 or len(esl) != 1:
                continue
            _dd, b, ib, pb = esl[0]
            # öbür ucun da tek eşi bu olmalı
            say = sum(1 for c_, _i, pc, _v in U if c_ is not b and float(np.hypot(*(pc - pb))) <= max(2.5, 2.0 * ea.width))
            if say != 1:
                continue
            (sa, ga), (sb, gb) = a[1], b[1]
            if ia == 0:
                sa, ga = _yol_ters(sa, ga)
            if ib == 1:
                sb, gb = _yol_ters(sb, gb)
            yeni = ga + [("L", (sb,))] + gb
            La = float(np.sum(np.hypot(*np.diff(a[2], axis=0).T)))
            Lb = float(np.sum(np.hypot(*np.diff(b[2], axis=0).T)))
            ea.width = (ea.width * La + b[0].width * Lb) / max(La + Lb, 1e-6)
            ea.prim = None
            ea.d = _yol_yaz(sa, yeni)
            ea.cap = "round" if ea.cap == "round" or b[0].cap == "round" else ea.cap
            a[1] = (sa, yeni)
            a[2] = np.vstack([a[2][::-1] if ia == 0 else a[2], b[2][::-1] if ib == 1 else b[2]])
            A = a[2]
            ea.bbox = (float(A[:, 0].min()), float(A[:, 1].min()), float(A[:, 0].max()), float(A[:, 1].max()))
            drop.add(id(b[0]))
            degisti = True
            break
    return [e for e in elements if id(e) not in drop]


def cizimlestir(elements: list, background=(255, 255, 255)) -> list:
    # panel çerçeveleri (üstündeki şekillerin de üstünde kapalı çizgi) olduğu gibi kalır
    cerceve = [e for e in elements if e.kind == "stroke" and e.layer == "cerceve"]
    elements = [e for e in elements if not (e.kind == "stroke" and e.layer == "cerceve")]
    fills = [e for e in elements if e.kind == "fill"]
    strokes = [e for e in elements if e.kind == "stroke"]
    others = [e for e in elements if e.kind not in ("fill", "stroke")]
    fills, strokes = _frames(fills, strokes)
    for e in fills:
        if e.layer == "harf":
            continue
        _rectify(e)
    _rectify_occluded(fills, strokes)
    fills = _union_rects(fills)
    strokes = _merge_lines(_split_polylines(strokes))
    used = _merge_outlines(fills, strokes)
    strokes = [s for i, s in enumerate(strokes) if i not in used]
    strokes = _rect_strokes(fills, strokes, background)
    _hizala(fills)
    for s in strokes:
        _closed_shape(s)
        _simplify_curve(s)
    strokes = _merge_lines(_hale_cizgiler(strokes, background))
    before = {id(e) for e in fills}
    out = _objects(_baglantilar(_merge_dashes(fills + strokes + others)), background)
    # nesneye dönüşmeyen az köşeli dolgular çokgen olur
    for e in out:
        if e.kind == "fill" and id(e) in before and not e.prim:
            _polygonize(e)
    out = _drop_crumbs(_gorunmez(out), background) + cerceve
    out = _uzayan_kenarlar(out)
    out = _hucre_birlestir(out)
    _isaret_bagla(out)
    _isaret_boyu(out)
    out = _ayni_simgeler(out)
    _kesik_ortu(out)
    out = _ortulu_birlestir(out)
    out = _izgara_kesik(out)
    out = _uc_birlestir(out)
    _renk_birligi(out)
    _ice_al([e for e in out if e.kind == "fill"])
    return out


def izgara_tamamla(elements: list, rgb: np.ndarray, background) -> list:
    """Grafiğin soluk kesikli ızgara çizgileri: bir kısmı bulunduysa eksenin her çentiğinde (görselde
    izi varsa) aynı biçimde çizilir; hepsi eksenden çizim alanının sonuna kadar uzanır (yazı ve veri
    çizgisi üstlerinden geçer, ızgara arkada tam kalır)."""
    from .vektor import Element
    H, W = rgb.shape[:2]
    gray = rgb.astype(np.float32).mean(axis=2)
    bgg = float(np.mean(background))

    def hv(e):
        p = e.prim
        if abs(p["y1"] - p["y2"]) < 0.6:
            return "h", (p["y1"] + p["y2"]) / 2, min(p["x1"], p["x2"]), max(p["x1"], p["x2"])
        if abs(p["x1"] - p["x2"]) < 0.6:
            return "v", (p["x1"] + p["x2"]) / 2, min(p["y1"], p["y2"]), max(p["y1"], p["y2"])
        return None

    duz, kesik = [], []
    for e in elements:
        if e.kind != "stroke" or not e.prim or e.prim.get("type") != "line" or e.layer in ("harf", "cerceve"):
            continue
        t = hv(e)
        if t is None:
            continue
        if e.dash:
            if len(e.dash) == 2 and e.dash[0] >= 1.0:
                kesik.append((t, e))
        else:
            duz.append((t, e))

    def iz(yon, c, a, b, fam_g):
        # görselde bu doğru boyunca soluk çizgi izi: koyu şeyler (yazı, veri çizgisi) sayılmaz
        a, b = int(math.floor(a)), int(math.ceil(b))
        r = int(round(c))
        if yon == "h":
            if r < 1 or r >= H - 1:
                return 0.0, 0
            band = gray[r - 1:r + 2, max(0, a):min(W, b)].min(axis=0)
        else:
            if r < 1 or r >= W - 1:
                return 0.0, 0
            band = gray[max(0, a):min(H, b), r - 1:r + 2].min(axis=1)
        koyu = band < fam_g - 40
        n = int((~koyu).sum())
        if n < 20:
            return 0.0, n
        soluk = (band <= bgg - 5) & ~koyu
        return float(soluk.sum()) / n, n

    add = []
    for yon in ("h", "v"):
        dik = "v" if yon == "h" else "h"
        eksenler = [(t, e) for t, e in duz if t[0] == dik and t[3] - t[2] >= 60]
        aile = [(t, e) for t, e in kesik if t[0] == yon]
        if not aile or not eksenler:
            continue
        # her kesikli çizginin ekseni: konumunu kapsayan, bir ucuna yakın dik düz çizgi
        gruplar = {}
        for t, e in aile:
            en = None
            for te, ee in eksenler:
                if not (te[2] - 2 <= t[1] <= te[3] + 2):
                    continue
                dd = min(abs(te[1] - t[2]), abs(te[1] - t[3]))
                if (te[1] <= t[2] + 3 or te[1] >= t[3] - 3) and dd <= 0.6 * (t[3] - t[2]) and (en is None or dd < en[0]):
                    en = (dd, te, ee)
            if en is None:
                continue
            anahtar = (id(en[2]), )
            gruplar.setdefault(anahtar, {"eksen": en[1], "uyeler": []})["uyeler"].append((t, e))
        for g in gruplar.values():
            uy = g["uyeler"]
            te = g["eksen"]
            e0 = uy[0][1]
            uy = [(t, e) for t, e in uy if _de(e.color, e0.color) < 12 and abs(sum(e.dash) - sum(e0.dash)) <= 1.5]
            if not uy:
                continue
            lo = min(t[2] for t, _e in uy)
            hi = max(t[3] for t, _e in uy)
            if te[1] <= lo + 3:
                lo = te[1]
            elif te[1] >= hi - 3:
                hi = te[1]
            # karşı uçta eksen (ikinci eksen) varsa oraya kadar
            for t2, _e2 in eksenler:
                if t2 is te or not (t2[2] - 2 <= min(t[1] for t, _e in uy) and max(t[1] for t, _e in uy) <= t2[3] + 2):
                    continue
                if te[1] <= lo + 0.5 and hi - 6 <= t2[1] <= hi + 15:
                    hi = t2[1]
                elif te[1] >= hi - 0.5 and lo - 15 <= t2[1] <= lo + 6:
                    lo = t2[1]
            fam_g = float(np.mean(e0.color))
            wd = float(np.median([e.width for _t, e in uy]))
            pat = [float(np.median([e.dash[0] for _t, e in uy])), float(np.median([e.dash[1] for _t, e in uy]))]
            # adaylar: var olan çizgiler ve eksendeki çentikler
            adaylar = [t[1] for t, _e in uy]
            for t2, _e2 in duz:
                if t2[0] == yon and t2[3] - t2[2] <= 15 and te[2] - 2 <= t2[1] <= te[3] + 2 \
                        and (abs(t2[2] - te[1]) <= 1.5 or abs(t2[3] - te[1]) <= 1.5):
                    adaylar.append(t2[1])
            adaylar.sort()
            gorulen = []
            for c in adaylar:
                if any(abs(c - q) <= 2.0 for q in gorulen):
                    continue
                gorulen.append(c)
                # eksenin kendisi ya da üstünde uzun düz çizgi olan yer (öbür eksen) ızgara değil
                if any(t2[0] == yon and abs(t2[1] - c) <= 2.0 and t2[3] - t2[2] >= 0.5 * (hi - lo) for t2, _e2 in duz):
                    continue
                var = [(t, e) for t, e in uy if abs(t[1] - c) <= 2.0]
                if var:
                    t, e = max(var, key=lambda q: q[0][3] - q[0][2])
                    yeni_lo, yeni_hi = t[2], t[3]
                    if t[2] > lo:
                        f_, n_ = iz(yon, t[1], lo, t[2], fam_g)
                        if t[2] - lo <= 3 or f_ >= 0.4 or n_ < 20:
                            yeni_lo = lo
                    if hi > t[3]:
                        f_, n_ = iz(yon, t[1], t[3], hi, fam_g)
                        if hi - t[3] <= 3 or f_ >= 0.4 or n_ < 20:
                            yeni_hi = hi
                    p = e.prim
                    if yon == "h":
                        p["x1"], p["x2"] = yeni_lo, yeni_hi
                        p["y1"] = p["y2"] = t[1]
                    else:
                        p["y1"], p["y2"] = yeni_lo, yeni_hi
                        p["x1"] = p["x2"] = t[1]
                    e.bbox = (min(p["x1"], p["x2"]), min(p["y1"], p["y2"]), max(p["x1"], p["x2"]), max(p["y1"], p["y2"]))
                    continue
                f_, n_ = iz(yon, c, lo, hi, fam_g)
                if f_ < 0.4 or n_ < 0.3 * (hi - lo):
                    continue
                if yon == "h":
                    pr = {"type": "line", "x1": lo, "y1": c, "x2": hi, "y2": c}
                else:
                    pr = {"type": "line", "x1": c, "y1": lo, "x2": c, "y2": hi}
                add.append(Element("stroke", e0.color, prim=pr, width=wd, dash=list(pat), cap=e0.cap,
                                   bbox=(min(pr["x1"], pr["x2"]), min(pr["y1"], pr["y2"]),
                                         max(pr["x1"], pr["x2"]), max(pr["y1"], pr["y2"]))))
    # düz ızgara çizgileri (koordinat ızgarası): aynı renk ve kalınlıkta, aynı yönde en az üç çizginin
    # çoğu aynı yerde başlayıp bitiyorsa, kısa kalanlar görselde izi varsa o uzunluğa tamamlanır
    def iz_duz(yon, c, a, b, col):
        a, b = int(math.floor(a)), int(math.ceil(b))
        r = int(round(c))
        colv = np.asarray(col, np.float32)
        if yon == "h":
            if r < 1 or r >= H - 1 or b <= a:
                return 0.0
            band = rgb[r - 1:r + 2, max(0, a):min(W, b)].astype(np.float32)
            dd = np.linalg.norm(band - colv, axis=2).min(axis=0)
        else:
            if r < 1 or r >= W - 1 or b <= a:
                return 0.0
            band = rgb[max(0, a):min(H, b), r - 1:r + 2].astype(np.float32)
            dd = np.linalg.norm(band - colv, axis=2).min(axis=1)
        if len(dd) == 0:
            return 0.0
        return float((dd < 40).mean())

    for yon in ("h", "v"):
        cizg = [(t, e) for t, e in duz if t[0] == yon and t[3] - t[2] >= 30]
        kul = set()
        for t0, e0 in cizg:
            if id(e0) in kul:
                continue
            aile = [(t, e) for t, e in cizg if id(e) not in kul and _de(e.color, e0.color) < 12
                    and abs(e.width - e0.width) <= 0.35 * max(e.width, e0.width)
                    and min(t[3], t0[3]) - max(t[2], t0[2]) >= 0.5 * min(t[3] - t[2], t0[3] - t0[2])]
            if len(aile) < 3:
                continue
            for _t, e in aile:
                kul.add(id(e))
            los = sorted(t[2] for t, _e in aile)
            his = sorted(t[3] for t, _e in aile)
            # ortak uç: en az iki çizginin (3 piksel içinde) paylaştığı en dış uç
            lo_h = next((v for i, v in enumerate(los) if sum(abs(w - v) <= 3 for w in los) >= 2), None)
            hi_h = next((v for v in reversed(his) if sum(abs(w - v) <= 3 for w in his) >= 2), None)
            for t, e in aile:
                p = e.prim
                lo, hi = t[2], t[3]
                if lo_h is not None and lo > lo_h + 2 and iz_duz(yon, t[1], lo_h, lo, e.color) >= 0.85:
                    lo = lo_h
                if hi_h is not None and hi < hi_h - 2 and iz_duz(yon, t[1], hi, hi_h, e.color) >= 0.85:
                    hi = hi_h
                if (lo, hi) == (t[2], t[3]):
                    continue
                if yon == "h":
                    p["x1"], p["x2"] = lo, hi
                else:
                    p["y1"], p["y2"] = lo, hi
                e.bbox = (min(p["x1"], p["x2"]), min(p["y1"], p["y2"]), max(p["x1"], p["x2"]), max(p["y1"], p["y2"]))
    return add + elements if add else elements


def koordinat_izgarasi(elements: list, rgb: np.ndarray) -> list:
    """Koordinat ızgarası (gri, düz, yatay ve dikey çizgiler): dokulu zeminde parça parça, farklı
    tonlarda bulunmuş olabilir. Aynı hizadaki parçalar, görselde izi varsa ızgaranın bir ucundan
    öbürüne tek çizgi olur; bütün ızgara aynı renk ve kalınlıkta çizilir."""
    from .vektor import Element
    H, W = rgb.shape[:2]
    gray = rgb.astype(np.float32).mean(axis=2)

    def notr(c):
        return max(c) - min(c) <= 30 and float(np.mean(c)) < 200

    parca = {"h": [], "v": []}
    sinir = {"h": [], "v": []}      # eksenler (kalın düz çizgiler): ızgaranın uçları
    for e in elements:
        if e.kind != "stroke" or not e.prim or e.prim.get("type") != "line" or e.layer in ("harf", "cerceve"):
            continue
        if not notr(e.color) or e.width > 5.0:
            continue
        p = e.prim
        if abs(p["y1"] - p["y2"]) < 0.6:
            t = ((p["y1"] + p["y2"]) / 2, min(p["x1"], p["x2"]), max(p["x1"], p["x2"]), e)
        elif abs(p["x1"] - p["x2"]) < 0.6:
            t = ((p["x1"] + p["x2"]) / 2, min(p["y1"], p["y2"]), max(p["y1"], p["y2"]), e)
        else:
            continue
        yon_ = "h" if abs(p["y1"] - p["y2"]) < 0.6 else "v"
        if e.width > 3.0:
            sinir[yon_].append(t)
        else:
            parca[yon_].append(t)
    # kenarları ızgara çizgisine denk gelen kutuların konturu da ızgara parçasıdır (kutu konturuz kalır)
    kutu_kenar = []
    for e in elements:
        if e.kind != "fill" or e.layer == "harf" or e.stroke is None or not e.prim or e.prim.get("type") != "rect" \
                or e.prim.get("rot") or not notr(e.stroke) or e.stroke_width > 3.0:
            continue
        p = e.prim
        x0, y0, x1, y1 = p["x"], p["y"], p["x"] + p["w"], p["y"] + p["h"]
        kutu_kenar.append(e)
        for t in ((y0, x0, x1, "h"), (y1, x0, x1, "h"), (x0, y0, y1, "v"), (x1, y0, y1, "v")):
            parca[t[3]].append((t[0], t[1], t[2], e))

    def kumele(ps):
        ps = sorted(ps, key=lambda t: t[0])
        out = []
        for t in ps:
            if out and abs(t[0] - out[-1][-1][0]) <= 2.0:
                out[-1].append(t)
            else:
                out.append([t])
        res = []
        for g in out:
            L = sum(t[2] - t[1] for t in g)
            cs = np.array([t[0] for t in g])
            ls = np.array([max(1.0, t[2] - t[1]) for t in g])
            o_ = np.argsort(cs)
            c = float(cs[o_][np.searchsorted(np.cumsum(ls[o_]), 0.5 * float(ls.sum()))])
            res.append({"c": c, "lo": min(t[1] for t in g), "hi": max(t[2] for t in g), "L": L, "uy": g})
        return res

    def iz(yon, c, a, b):
        # çizgi boyunca, iki yanındaki zeminden belirgin koyu piksel oranı
        a, b = int(math.floor(a)), int(math.ceil(b))
        r = int(round(c))
        if b - a < 2:
            return 1.0
        if yon == "h":
            if r < 5 or r >= H - 5:
                return 0.0
            xs = np.arange(max(0, a), min(W, b))
            if len(xs) == 0:
                return 0.0
            cizgi = gray[r - 1:r + 2, xs].min(axis=0)
            yan = np.minimum(np.median(gray[r - 5:r - 2, xs], axis=0), np.median(gray[r + 3:r + 6, xs], axis=0))
        else:
            if r < 5 or r >= W - 5:
                return 0.0
            ys = np.arange(max(0, a), min(H, b))
            if len(ys) == 0:
                return 0.0
            cizgi = gray[ys, r - 1:r + 2].min(axis=1)
            yan = np.minimum(np.median(gray[ys, r - 5:r - 2], axis=1), np.median(gray[ys, r + 3:r + 6], axis=1))
        return float((yan - cizgi >= 12).mean())

    kum = {y: kumele(parca[y]) for y in ("h", "v")}
    add, sil = [], set()
    kenar_ok = {}
    for yon in ("h", "v"):
        dik = "v" if yon == "h" else "h"
        ks = [k for k in kum[yon] if k["L"] >= 25]
        if len(ks) < 3 or len(kum[dik]) < 2:
            continue
        # ızgara alanı: iki yöndeki çizgilerin uç konumları
        dks = [k for k in kum[dik] if k["L"] >= 25]
        if len(dks) < 2:
            continue
        bcs = [k["c"] for k in dks] + [t[0] for t in sinir[dik]]
        lo_f = min(min(bcs), min(k["lo"] for k in ks))
        hi_f = max(max(bcs), max(k["hi"] for k in ks))
        span = hi_f - lo_f
        if span < 60:
            continue
        # ızgara çizgisi: alanın büyük kısmında izi olan hizalar
        izg = []
        for k in ks:
            if k["L"] >= 0.3 * span and iz(yon, k["c"], lo_f, hi_f) >= 0.5:
                izg.append(k)
        if len(izg) < 3:
            continue
        # aralıklar düzenli olmalı (koordinat ızgarası)
        cs = np.sort([k["c"] for k in izg])
        ds = np.diff(cs)
        if len(ds) < 2 or float(np.max(ds)) > 1.35 * float(np.median(ds)) or float(np.min(ds)) < 0.65 * float(np.median(ds)):
            continue
        uyeler = [t for k in izg for t in k["uy"] if t[3].kind == "stroke"]
        if not uyeler:
            continue
        ws = np.array([t[3].width for t in uyeler])
        ls = np.array([max(1.0, t[2] - t[1]) for t in uyeler])
        o_ = np.argsort(ws)
        wd = float(ws[o_][np.searchsorted(np.cumsum(ls[o_]), 0.5 * float(ls.sum()))])
        gs = np.array([float(np.mean(t[3].color)) for t in uyeler])
        o_ = np.argsort(gs)
        e_ref = uyeler[int(o_[np.searchsorted(np.cumsum(ls[o_]), 0.5 * float(ls.sum()))])][3]
        renk = e_ref.color
        for k in izg:
            lo, hi = k["lo"], k["hi"]
            if lo - lo_f > 2 and iz(yon, k["c"], lo_f, lo) >= 0.5:
                lo = lo_f
            if hi_f - hi > 2 and iz(yon, k["c"], hi, hi_f) >= 0.5:
                hi = hi_f
            for t in k["uy"]:
                if t[3].kind == "stroke":
                    sil.add(id(t[3]))
                else:
                    kenar_ok.setdefault(id(t[3]), set()).add((yon, round(t[0], 1)))
            if yon == "h":
                pr = {"type": "line", "x1": lo, "y1": k["c"], "x2": hi, "y2": k["c"]}
            else:
                pr = {"type": "line", "x1": k["c"], "y1": lo, "x2": k["c"], "y2": hi}
            add.append(Element("stroke", renk, prim=pr, width=wd, cap="butt",
                               bbox=(min(pr["x1"], pr["x2"]), min(pr["y1"], pr["y2"]),
                                     max(pr["x1"], pr["x2"]), max(pr["y1"], pr["y2"]))))
    if not add:
        return elements
    # ızgara çizgisinin üstündeki başka renkte çizgi parçaları (üstteki noktanın rengini almış, kesikli
    # sanılmış parça) aynı çizginin kopyasıdır
    for e in elements:
        if e.kind != "stroke" or not e.prim or e.prim.get("type") != "line" or id(e) in sil or e.width > 3.0 \
                or e.layer in ("harf", "cerceve"):
            continue
        p = e.prim
        for q in add:
            r = q.prim
            if abs(r["y1"] - r["y2"]) < 0.6 and abs(p["y1"] - p["y2"]) < 0.6 and abs(p["y1"] - r["y1"]) <= 2.0 \
                    and min(p["x1"], p["x2"]) >= min(r["x1"], r["x2"]) - 3 and max(p["x1"], p["x2"]) <= max(r["x1"], r["x2"]) + 3:
                sil.add(id(e))
                break
            if abs(r["x1"] - r["x2"]) < 0.6 and abs(p["x1"] - p["x2"]) < 0.6 and abs(p["x1"] - r["x1"]) <= 2.0 \
                    and min(p["y1"], p["y2"]) >= min(r["y1"], r["y2"]) - 3 and max(p["y1"], p["y2"]) <= max(r["y1"], r["y2"]) + 3:
                sil.add(id(e))
                break
    # ızgara çizgilerinin üstünde kalan kopya yollar (köşeden dönen parça) atılır
    hs = [(a_["prim"]["y1"], a_["prim"]["x1"], a_["prim"]["x2"]) for a_ in
          [{"prim": q.prim} for q in add] if abs(a_["prim"]["y1"] - a_["prim"]["y2"]) < 0.6]
    vs = [(a_["prim"]["x1"], a_["prim"]["y1"], a_["prim"]["y2"]) for a_ in
          [{"prim": q.prim} for q in add] if abs(a_["prim"]["x1"] - a_["prim"]["x2"]) < 0.6]
    for e in elements:
        if e.kind != "stroke" or e.prim or not e.d or not notr(e.color) or id(e) in sil:
            continue
        ps = sadakat.flatten(e.d)
        if not ps:
            continue
        P = np.vstack([np.asarray(q[0], float) for q in ps])
        ust = np.zeros(len(P), bool)
        for c, lo, hi in hs:
            ust |= (np.abs(P[:, 1] - c) <= 2.0) & (P[:, 0] >= min(lo, hi) - 2) & (P[:, 0] <= max(lo, hi) + 2)
        for c, lo, hi in vs:
            ust |= (np.abs(P[:, 0] - c) <= 2.0) & (P[:, 1] >= min(lo, hi) - 2) & (P[:, 1] <= max(lo, hi) + 2)
        if ust.all():
            sil.add(id(e))
    # ızgara alanının içinde kalan, ızgara renginde kısa kırıntı çizgiler (doku hücrelerinin kenarları)
    if hs and vs:
        gx0 = min(min(c for c, _a, _b in vs), min(min(a_, b_) for _c, a_, b_ in hs))
        gx1 = max(max(c for c, _a, _b in vs), max(max(a_, b_) for _c, a_, b_ in hs))
        gy0 = min(min(c for c, _a, _b in hs), min(min(a_, b_) for _c, a_, b_ in vs))
        gy1 = max(max(c for c, _a, _b in hs), max(max(a_, b_) for _c, a_, b_ in vs))
        renkler = [q.color for q in add]
        for e in elements:
            if (e.kind == "fill" and e.stroke is not None and e.layer != "harf" and id(e) not in sil
                    and max(e.bbox[2] - e.bbox[0], e.bbox[3] - e.bbox[1]) < 8
                    and any(_de(e.stroke, r_) < 15 for r_ in renkler)
                    and gx0 + 3 < e.bbox[0] and e.bbox[2] < gx1 - 3 and gy0 + 3 < e.bbox[1] and e.bbox[3] < gy1 - 3):
                sil.add(id(e))      # ızgara renginde konturlu küçük kutucuk: doku kırıntısı
                continue
            if e.kind != "stroke" or not e.prim or e.prim.get("type") != "line" or id(e) in sil:
                continue
            p = e.prim
            if math.hypot(p["x2"] - p["x1"], p["y2"] - p["y1"]) >= 8 or not any(_de(e.color, r_) < 15 for r_ in renkler):
                continue
            if gx0 + 3 < min(p["x1"], p["x2"]) and max(p["x1"], p["x2"]) < gx1 - 3 \
                    and gy0 + 3 < min(p["y1"], p["y2"]) and max(p["y1"], p["y2"]) < gy1 - 3:
                sil.add(id(e))
    # dört kenarı da ızgara çizgisi olan kutunun konturu çizgilerle zaten çizili
    for e in kutu_kenar:
        if len(kenar_ok.get(id(e), ())) >= 4:
            e.stroke, e.stroke_width = None, 0.0
    return add + [e for e in elements if id(e) not in sil]


def soluk_lekeler(elements: list, rgb: np.ndarray, background) -> list:
    """Zeminden ancak seçilen, düzensiz biçimli soluk lekeler (dokulu zeminin, silik desenin
    parçaları) çizim değildir: atılır. Konturu varsa ve kontur görselde gerçekten varsa yalnız
    kontur kalır."""
    from .vektor import Element
    H, W = rgb.shape[:2]
    img = rgb.astype(np.float32)
    bgv = np.asarray(background, np.float32)

    def zeminde(e):
        # şeklin hemen dışı (kutusunun 3 piksel dışı) çoğunlukla zemin mi (renkli bir alanın üstündeki
        # beyaz bulut silik leke değildir)
        x0, y0, x1, y1 = e.bbox
        x0, y0 = max(0, int(x0) - 3), max(0, int(y0) - 3)
        x1, y1 = min(W - 1, int(math.ceil(x1)) + 3), min(H - 1, int(math.ceil(y1)) + 3)
        if x1 <= x0 or y1 <= y0:
            return False
        kenar = np.concatenate([img[y0, x0:x1 + 1], img[y1, x0:x1 + 1], img[y0:y1 + 1, x0], img[y0:y1 + 1, x1]])
        return float((np.linalg.norm(kenar - bgv, axis=1) < 25).mean()) >= 0.6

    out = []
    for e in elements:
        if (e.kind == "fill" and e.layer != "harf" and not e.grad and e.stroke is None and e.prim
                and e.prim.get("type") != "path" and _de(e.color, background) < 5 and zeminde(e)):
            continue        # zeminden ayırt edilemeyecek kadar silik düzgün şekil (doku tonu)
        if (e.kind != "fill" or e.layer == "harf" or e.grad or (e.prim and e.prim.get("type") != "path")
                or not e.d or _de(e.color, background) >= 6 or not zeminde(e)):
            out.append(e)
            continue
        if e.stroke is None:
            continue
        # kontur görselde var mı: dış çizgi boyunca kontur rengine yakın piksel oranı
        ps = sadakat.flatten(e.d)
        if not ps:
            continue
        P = np.vstack([np.asarray(q[0], float) for q in ps])
        if len(P) > 400:
            P = P[:: len(P) // 400 + 1]
        sc = np.asarray(e.stroke, np.float32)
        tut = 0
        for x, y in P:
            xi, yi = int(round(x)), int(round(y))
            win = img[max(0, yi - 1):min(H, yi + 2), max(0, xi - 1):min(W, xi + 2)].reshape(-1, 3)
            if len(win) and float(np.linalg.norm(win - sc, axis=1).min()) < 40:
                tut += 1
        if tut >= 0.6 * len(P):
            out.append(Element("stroke", e.stroke, d=e.d, width=e.stroke_width, bbox=e.bbox))
    return out


def zemin_cizgileri(elements: list, rgb: np.ndarray, background) -> list:
    """Zemin üzerindeki yatay/dikey çizgiler (şema bağlantıları): yumuşak kenarlı kalın çizgi
    farklı tonlarda birkaç parça olarak bulunmuş olabilir. Her çizginin rengi, kalınlığı ve tam
    konumu görselden yeniden ölçülür; üst üste binen kopyalar tek çizgi olur."""
    from .vektor import Element
    H, W = rgb.shape[:2]
    img = rgb.astype(np.float32)
    bgv = np.asarray(background, np.float32)
    dimg = np.linalg.norm(img - bgv, axis=2)
    # ince uzun dikdörtgen dolgu (kalınca bağlantı çizgisinin kısa kolu) de çizgi adayıdır
    ince = {}           # çizgi adayı id -> özgün dikdörtgen
    yeni_list = []
    for e in elements:
        if e.kind != "fill" or e.layer == "harf" or not e.prim or e.prim.get("type") != "rect" or e.prim.get("rot"):
            yeni_list.append(e)
            continue
        p = e.prim
        kisa, uzun = min(p["w"], p["h"]), max(p["w"], p["h"])
        if kisa > 5.0 or uzun < 6 or uzun < 3 * kisa:
            yeni_list.append(e)
            continue
        if p["w"] >= p["h"]:
            y = p["y"] + p["h"] / 2
            pr = {"type": "line", "x1": p["x"], "y1": y, "x2": p["x"] + p["w"], "y2": y}
        else:
            x = p["x"] + p["w"] / 2
            pr = {"type": "line", "x1": x, "y1": p["y"], "x2": x, "y2": p["y"] + p["h"]}
        cz = Element("stroke", e.stroke if e.stroke is not None else e.color, prim=pr, width=kisa, cap="butt",
                     bbox=(min(pr["x1"], pr["x2"]), min(pr["y1"], pr["y2"]), max(pr["x1"], pr["x2"]), max(pr["y1"], pr["y2"])))
        ince[id(cz)] = e
        yeni_list.append(cz)
    elements = yeni_list
    olcum = {}
    for e in elements:
        if e.kind != "stroke" or not e.prim or e.prim.get("type") != "line" or e.dash or e.layer in ("harf", "cerceve"):
            continue
        p = e.prim
        yat = abs(p["y1"] - p["y2"]) < 0.6
        dik = abs(p["x1"] - p["x2"]) < 0.6
        if not (yat or dik):
            continue
        c = (p["y1"] + p["y2"]) / 2 if yat else (p["x1"] + p["x2"]) / 2
        lo, hi = (min(p["x1"], p["x2"]), max(p["x1"], p["x2"])) if yat else (min(p["y1"], p["y2"]), max(p["y1"], p["y2"]))
        if hi - lo < 6:
            continue
        ts = np.arange(int(math.ceil(lo + 2)), int(math.floor(hi - 2)) + 1)
        ci = int(round(c))
        if len(ts) < 3 or ci < 5 or ci >= (H if yat else W) - 5:
            continue
        if yat:
            prof = dimg[ci - 4:ci + 5, ts].T            # (n, 9)
            renk = img[ci - 4:ci + 5, ts].transpose(1, 0, 2)
        else:
            prof = dimg[ts, ci - 4:ci + 5]
            renk = img[ts, ci - 4:ci + 5]
        # çizgi zeminde mi: profilin iki ucu zemin
        uc = (prof[:, 0] < 15) & (prof[:, -1] < 15)
        if uc.mean() < 0.7:
            continue
        prof, renk = prof[uc], renk[uc]
        # çizginin kendisi: ortadaki (3-5) en belirgin piksel ve ona bitişik koyu piksel dizisi
        # (yanındaki başka bir çizgi, eksen ya da sütun kenarı ölçüme girmez)
        en = 3 + prof[:, 3:6].argmax(axis=1)
        tepe = prof[np.arange(len(prof)), en]
        if float(np.median(tepe)) < 40:
            continue
        col = np.median(renk[np.arange(len(prof)), en], axis=0)
        if _de(tuple(int(v) for v in col), e.color) >= 30:
            continue        # ölçülen başka bir şey (yanındaki koyu eksen): bu çizgi değil
        mask = prof >= 0.5 * tepe[:, None]
        sol = en.copy()
        sag = en.copy()
        for _ in range(4):
            ok_l = (sol > 0) & mask[np.arange(len(prof)), np.maximum(sol - 1, 0)]
            sol = np.where(ok_l, sol - 1, sol)
            ok_r = (sag < 8) & mask[np.arange(len(prof)), np.minimum(sag + 1, 8)]
            sag = np.where(ok_r, sag + 1, sag)
        gen = float(np.median(sag - sol + 1))
        mer = float(np.median((sol + sag) / 2.0 - 4))
        if abs(mer) > 1.0 or gen > max(e.width + 2.0, 1.6 * e.width):
            continue        # ölçüm çizginin kendisine oturmadı: çizgi olduğu gibi kalır
        olcum[id(e)] = (tuple(int(round(v)) for v in col), max(0.8, min(6.0, gen)), mer)
    # ölçülemeyen (zeminde olmayan) ince dikdörtgenler eski hâline döner
    if ince:
        elements = [ince[id(e)] if (id(e) in ince and id(e) not in olcum) else e for e in elements]
    if not olcum:
        return elements
    for e in elements:
        if id(e) not in olcum:
            continue
        col, gen, mer = olcum[id(e)]
        p = e.prim
        e.color = col
        e.width = gen
        if abs(mer) <= 1.5:
            if abs(p["y1"] - p["y2"]) < 0.6:
                p["y1"] = p["y2"] = (p["y1"] + p["y2"]) / 2 + mer
            else:
                p["x1"] = p["x2"] = (p["x1"] + p["x2"]) / 2 + mer
        e.bbox = (min(p["x1"], p["x2"]), min(p["y1"], p["y2"]), max(p["x1"], p["x2"]), max(p["y1"], p["y2"]))
    # kopyalar: aynı doğrultuda üst üste binen, aynı renkteki çizgiler tek çizgi
    sil = set()
    ol = [e for e in elements if id(e) in olcum]
    for i, a in enumerate(ol):
        if id(a) in sil:
            continue
        pa = a.prim
        ya = abs(pa["y1"] - pa["y2"]) < 0.6
        ca = pa["y1"] if ya else pa["x1"]
        la, ha = (min(pa["x1"], pa["x2"]), max(pa["x1"], pa["x2"])) if ya else (min(pa["y1"], pa["y2"]), max(pa["y1"], pa["y2"]))
        for b in ol[i + 1:]:
            if id(b) in sil:
                continue
            pb = b.prim
            yb = abs(pb["y1"] - pb["y2"]) < 0.6
            if yb != ya:
                continue
            cb = pb["y1"] if yb else pb["x1"]
            lb, hb = (min(pb["x1"], pb["x2"]), max(pb["x1"], pb["x2"])) if yb else (min(pb["y1"], pb["y2"]), max(pb["y1"], pb["y2"]))
            if abs(ca - cb) > max(a.width, b.width) / 2 + 1.0 or _de(a.color, b.color) >= 25:
                continue
            if min(ha, hb) - max(la, lb) < -1.0:
                continue
            # birleşik: uzun olanın konumu ve rengi
            if hb - lb > ha - la:
                a, b = b, a
                pa, pb = pb, pa
                ca, cb = cb, ca
            lo_, hi_ = min(la, lb), max(ha, hb)
            if ya:
                pa["x1"], pa["x2"] = lo_, hi_
            else:
                pa["y1"], pa["y2"] = lo_, hi_
            a.bbox = (min(pa["x1"], pa["x2"]), min(pa["y1"], pa["y2"]), max(pa["x1"], pa["x2"]), max(pa["y1"], pa["y2"]))
            la, ha = lo_, hi_
            sil.add(id(b))
    # uçlar: birkaç piksel ötedeki dik çizgiye ya da kutunun kenarına tam ulaşır (bağlantı kolu kutuya
    # değer, omurgaya bağlanır)
    hedef_v, hedef_h = [], []        # (konum, alt, üst)
    for e in elements:
        if id(e) in sil:
            continue
        if id(e) in olcum:
            p = e.prim
            if abs(p["x1"] - p["x2"]) < 0.6:
                hedef_v.append((p["x1"], min(p["y1"], p["y2"]), max(p["y1"], p["y2"]), e.width / 2))
            else:
                hedef_h.append((p["y1"], min(p["x1"], p["x2"]), max(p["x1"], p["x2"]), e.width / 2))
        elif e.kind == "fill" and e.layer != "harf" and e.prim and e.prim.get("type") in ("rect", "rrect") \
                and not e.prim.get("rot"):
            p = e.prim
            r_ = p.get("r", 0.0)
            hedef_v += [(p["x"], p["y"] + r_, p["y"] + p["h"] - r_, 0.0), (p["x"] + p["w"], p["y"] + r_, p["y"] + p["h"] - r_, 0.0)]
            hedef_h += [(p["y"], p["x"] + r_, p["x"] + p["w"] - r_, 0.0), (p["y"] + p["h"], p["x"] + r_, p["x"] + p["w"] - r_, 0.0)]
    for e in elements:
        if id(e) not in olcum or id(e) in sil:
            continue
        p = e.prim
        yat = abs(p["y1"] - p["y2"]) < 0.6
        c = p["y1"] if yat else p["x1"]
        hed = hedef_v if yat else hedef_h
        ka, kb = ("x1", "x2") if yat else ("y1", "y2")
        for k_ in (ka, kb):
            u = p[k_]
            diger = p[kb if k_ == ka else ka]
            yon = 1.0 if u >= diger else -1.0
            en = None
            for hc, hlo, hhi, hw in hed:
                if not (hlo - 1 <= c <= hhi + 1):
                    continue
                # hedefin bu uca bakan yüzü
                yuz = hc - yon * hw
                g = (yuz - u) * yon
                if -1.0 <= g <= max(4.0, 2 * e.width) and (en is None or abs(g) < abs(en - u)):
                    en = yuz
            if en is not None:
                p[k_] = en
        e.bbox = (min(p["x1"], p["x2"]), min(p["y1"], p["y2"]), max(p["x1"], p["x2"]), max(p["y1"], p["y2"]))
    # ölçülen çizgilerin üstünde kalan öbür çizgi parçaları (başka tonda kopya, kesikli sanılmış
    # kopya, köşeden dönen kopya yol, kırıntı) atılır
    bant = []
    for e in elements:
        if id(e) not in olcum or id(e) in sil:
            continue
        p = e.prim
        bant.append((p["x1"], p["y1"], p["x2"], p["y2"], e.width / 2 + 1.5, e.width, e.color))
    if bant:
        def ustunde(P, w_, c_):
            ok = np.zeros(len(P), bool)
            for x1, y1, x2, y2, r_, wb, cb in bant:
                if w_ > wb + 1.0 or _de(c_, cb) >= 25:
                    continue
                v = np.array([x2 - x1, y2 - y1])
                n2 = max(float(v @ v), 1e-9)
                t = np.clip(((P - [x1, y1]) @ v) / n2, 0, 1)
                d = np.hypot(*(P - (np.array([x1, y1]) + t[:, None] * v)).T)
                ok |= d <= r_
            return ok.all()
        for e in elements:
            if e.kind != "stroke" or id(e) in olcum or id(e) in sil or e.layer in ("harf", "cerceve"):
                continue
            pr = e.prim or {}
            if pr.get("type") == "line":
                n_ = max(2, int(math.hypot(pr["x2"] - pr["x1"], pr["y2"] - pr["y1"])) + 1)
                P = np.column_stack([np.linspace(pr["x1"], pr["x2"], n_), np.linspace(pr["y1"], pr["y2"], n_)])
            elif not pr and e.d:
                ps = sadakat.flatten(e.d)
                if not ps:
                    continue
                P = np.vstack([np.asarray(q[0], float) for q in ps])
            else:
                continue
            if ustunde(P, e.width, e.color):
                sil.add(id(e))
    return [e for e in elements if id(e) not in sil]
