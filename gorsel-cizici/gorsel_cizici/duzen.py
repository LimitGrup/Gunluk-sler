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

import numpy as np

from . import egri, sadakat


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
    if e.prim and e.prim.get("type") in ("rect", "circle", "ellipse"):
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
    alive = [e for e in fills if e.layer != "harf" and (e.grad is not None or (e.prim and e.prim.get("type") == "rect"))
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
        if not (r.prim and r.prim.get("type") == "rect") or r.stroke is not None:
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
    rects = [r for r in fills if r.prim and r.prim.get("type") == "rect" and r.layer != "harf"
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
    out = []
    for sk in strokes:
        if sk.dash or sk.kind != "stroke":
            out.append(sk)
            continue
        ln = _line_of(sk)
        if ln is None:
            out.append(sk)
            continue
        a, b = np.asarray(ln[0], float), np.asarray(ln[1], float)
        x0, y0 = np.minimum(a, b) - 2
        x1, y1 = np.maximum(a, b) + 2
        near = [r for r in stroked if r.prim["x"] - 2 <= x1 and r.prim["x"] + r.prim["w"] + 2 >= x0
                and r.prim["y"] - 2 <= y1 and r.prim["y"] + r.prim["h"] + 2 >= y0]
        if not near:
            out.append(sk)
            continue
        n = max(2, int(np.hypot(*(b - a)) / 0.5) + 1)
        P = a + (b - a) * np.linspace(0, 1, n)[:, None]
        on = np.zeros(n, bool)
        ok_col = False
        for r in near:
            x, y, w, h = r.prim["x"], r.prim["y"], r.prim["w"], r.prim["h"]
            tol = max(1.5, 0.6 * max(sk.width, r.stroke_width) + 0.8)
            inx = (P[:, 0] >= x - tol) & (P[:, 0] <= x + w + tol)
            iny = (P[:, 1] >= y - tol) & (P[:, 1] <= y + h + tol)
            e = ((np.minimum(np.abs(P[:, 0] - x), np.abs(P[:, 0] - x - w)) <= tol) & iny) | \
                ((np.minimum(np.abs(P[:, 1] - y), np.abs(P[:, 1] - y - h)) <= tol) & inx)
            if e.any():
                on |= e
                if _de(sk.color, r.stroke) < 25 or _on_blend(sk.color, r.stroke, background) or \
                        _on_blend(sk.color, r.stroke, r.color):
                    ok_col = True
        if ok_col and on.mean() >= 0.95:
            continue
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
        if s.prim or not s.d or s.dash or any(c in s.d for c in "CAZ"):
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

    out = []
    for e in elements:
        if e.kind == "text" or e.grad:
            out.append(e)
            continue
        sz = _size(e)
        if sz < 1.2 and (e.kind != "fill" or e.area < 1.5):
            continue            # tek pikselden küçük toz
        if e.layer != "harf" and not e.stroke and _de(e.color, background) < 12 and \
                (e.kind == "stroke" and e.width <= 2.5 or e.kind == "fill" and sz <= 4):
            continue            # zeminden ayırt edilmeyen soluk kırıntı / kenar çizgisi
        small = sz <= 6 or (e.kind == "stroke" and e.width <= 1.3 and sz <= 10)
        if small and e.layer != "harf" and not is_real(e.color) and _is_blend(e.color, colors):
            continue            # kenar yumuşatmasından kalan ara renk
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
    return _fit_clean1(Uo, x0, y0, k)


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
                    and _size(e) >= 6 and not (e.prim and e.prim.get("type") == "rect")],
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
            if (e.kind == "fill" and not (e.prim and e.prim.get("type") == "rect") and e.area <= 3.0 * S.area
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
            # kenarın yeterince büyük bir kısmını kaplamalı
            edge = (U > 0) & ~(cv2.erode(U, np.ones((3, 3), np.uint8)) > 0)
            cov = np.zeros_like(edge)
            for _e, r in same:
                cov |= r
            cov = cv2.dilate(cov.astype(np.uint8), np.ones((2 * ring_r + 1, 2 * ring_r + 1), np.uint8)) > 0
            if edge.any() and float((edge & cov).sum()) / float(edge.sum()) >= 0.35:
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
def cizimlestir(elements: list, background=(255, 255, 255)) -> list:
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
    for s in strokes:
        _closed_shape(s)
        _simplify_curve(s)
    strokes = _merge_lines(strokes)
    before = {id(e) for e in fills}
    out = _objects(_merge_dashes(fills + strokes + others), background)
    # nesneye dönüşmeyen az köşeli dolgular çokgen olur
    for e in out:
        if e.kind == "fill" and id(e) in before and not e.prim:
            _polygonize(e)
    out = _drop_crumbs(out, background)
    return out
