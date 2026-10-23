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
    a, b = np.array(c1, float), np.array(c2, float)
    if np.linalg.norm(a - b) < 30:
        return True
    gray = lambda c: float(np.ptp(c)) < 25  # noqa: E731
    return gray(a) and gray(b) and np.linalg.norm(a - b) < 140


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
            if not _same_ink(gs.color, s.color) or max(gs.width, s.width) > 1.9 * min(gs.width, s.width) + 0.2:
                continue
            if abs(float(gd @ d)) < 0.9995:
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
    real = [np.array(e.color, float) for e in elements
            if e.kind != "text" and not e.grad and (_size(e) >= 4 or e.layer == "harf")]

    def is_real(c):
        c = np.array(c, float)
        return any(np.linalg.norm(c - r) < 14 for r in real)

    out = []
    for e in elements:
        if e.kind == "text" or e.grad:
            out.append(e)
            continue
        sz = _size(e)
        if sz < 1.2 and (e.kind != "fill" or e.area < 1.5):
            continue            # tek pikselden küçük toz
        small = sz <= 6 or (e.kind == "stroke" and e.width <= 1.3 and sz <= 10)
        if small and e.layer != "harf" and not is_real(e.color) and _is_blend(e.color, colors):
            continue            # kenar yumuşatmasından kalan ara renk
        out.append(e)
    return out


# ---------------------------------------------------------------- ana adım
def cizimlestir(elements: list, background=(255, 255, 255)) -> list:
    fills = [e for e in elements if e.kind == "fill"]
    strokes = [e for e in elements if e.kind == "stroke"]
    others = [e for e in elements if e.kind not in ("fill", "stroke")]
    fills, strokes = _frames(fills, strokes)
    for e in fills:
        if e.layer == "harf":
            continue
        if not _rectify(e):
            _polygonize(e)
    fills = _union_rects(fills)
    strokes = _merge_lines(_split_polylines(strokes))
    used = _merge_outlines(fills, strokes)
    strokes = [s for i, s in enumerate(strokes) if i not in used]
    for s in strokes:
        _simplify_curve(s)
    strokes = _merge_lines(strokes)
    out = _drop_crumbs(fills + strokes + others, background)
    return out
