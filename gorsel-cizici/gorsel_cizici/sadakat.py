"""Çizilen şekilleri görselle karşılaştırma (sadakat denetimi).

Akıllı dönüşümler (çizgi, dikdörtgen, çember, yazı) görseldeki pikselleri tutmazsa o parça
görseldeki biçimiyle (dış hattından) aynen çizilir. Böylece çıktı her zaman görseli izler.

Koordinatlar özgün görselin pikselidir: i. pikselin merkezi i'dedir. f kat büyütülmüş ızgarada
bir noktanın konumu (x + 0,5)·f − 0,5 olur.
"""
from __future__ import annotations

import math
import re

import cv2
import numpy as np

_TOK = re.compile(r"[MLCAZ]|-?\d+(?:\.\d+)?(?:[eE]-?\d+)?")


# ---------------------------------------------------------------- yol düzleştirme
def _arc_points(p0, rx, ry, rot, large, sweep, p1):
    """SVG yay komutunu nokta dizisine çevir (SVG belirtimi F.6.5)."""
    x1, y1 = p0
    x2, y2 = p1
    if rx < 1e-9 or ry < 1e-9 or (abs(x1 - x2) < 1e-9 and abs(y1 - y2) < 1e-9):
        return [p1]
    phi = math.radians(rot)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    xp = cp * dx + sp * dy
    yp = -sp * dx + cp * dy
    rx, ry = abs(rx), abs(ry)
    lam = (xp * xp) / (rx * rx) + (yp * yp) / (ry * ry)
    if lam > 1:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx * rx * ry * ry - rx * rx * yp * yp - ry * ry * xp * xp
    den = rx * rx * yp * yp + ry * ry * xp * xp
    co = math.sqrt(max(0.0, num / den)) if den > 1e-12 else 0.0
    if large == sweep:
        co = -co
    cxp = co * rx * yp / ry
    cyp = -co * ry * xp / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a

    t1 = ang(1, 0, (xp - cxp) / rx, (yp - cyp) / ry)
    dt = ang((xp - cxp) / rx, (yp - cyp) / ry, (-xp - cxp) / rx, (-yp - cyp) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    n = max(4, int(abs(dt) * max(rx, ry) / 1.5))
    out = []
    for i in range(1, n + 1):
        t = t1 + dt * i / n
        x = cx + rx * math.cos(t) * cp - ry * math.sin(t) * sp
        y = cy + rx * math.cos(t) * sp + ry * math.sin(t) * cp
        out.append((x, y))
    return out


def flatten(d: str) -> list:
    """SVG yol verisini [(noktalar N×2, kapalı mı)] listesine çevir."""
    toks = _TOK.findall(d)
    subs = []
    cur = []
    closed = False
    i = 0
    cmd = None
    pos = (0.0, 0.0)
    start = (0.0, 0.0)

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    while i < len(toks):
        t = toks[i]
        if t in "MLCAZ":
            cmd = t
            i += 1
            if cmd == "Z":
                closed = True
                if cur:
                    subs.append((np.array(cur, float), True))
                cur, closed = [], False
                pos = start
                continue
        if cmd == "M":
            if cur:
                subs.append((np.array(cur, float), closed))
            pos = (num(), num())
            start = pos
            cur, closed = [pos], False
            cmd = "L"
        elif cmd == "L":
            pos = (num(), num())
            cur.append(pos)
        elif cmd == "C":
            c1 = (num(), num())
            c2 = (num(), num())
            p = (num(), num())
            L = math.hypot(c1[0] - pos[0], c1[1] - pos[1]) + math.hypot(c2[0] - c1[0], c2[1] - c1[1]) + math.hypot(p[0] - c2[0], p[1] - c2[1])
            n = max(3, min(64, int(L / 1.0)))
            for k in range(1, n + 1):
                s = k / n
                ms = 1 - s
                x = ms ** 3 * pos[0] + 3 * ms * ms * s * c1[0] + 3 * ms * s * s * c2[0] + s ** 3 * p[0]
                y = ms ** 3 * pos[1] + 3 * ms * ms * s * c1[1] + 3 * ms * s * s * c2[1] + s ** 3 * p[1]
                cur.append((x, y))
            pos = p
        elif cmd == "A":
            rx, ry, rot = num(), num(), num()
            large, sweep = int(num()), int(num())
            p = (num(), num())
            cur.extend(_arc_points(pos, rx, ry, rot, large, sweep, p))
            pos = p
        else:
            i += 1
    if cur:
        subs.append((np.array(cur, float), closed))
    return [(p, c) for p, c in subs if len(p) >= 1]


def element_polys(e) -> tuple:
    """Elemanın çizimi: ("fill", [çokgenler]) ya da ("stroke", [(noktalar, kapalı)])."""
    p = e.prim
    if p:
        t = p["type"]
        if t == "rrect" or (t == "rect" and abs(p.get("rot", 0.0)) > 1e-6):
            from . import sekil
            return ("fill" if e.kind == "fill" else "stroke"), [(sekil.prim_points(p), True)]
        if t == "rect":
            x, y, w, h = p["x"], p["y"], p["w"], p["h"]
            poly = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], float)
            return ("fill" if e.kind == "fill" else "stroke"), [(poly, True)]
        if t == "circle":
            n = max(12, int(2 * math.pi * p["r"] / 1.0))
            a = np.linspace(0, 2 * math.pi, n, endpoint=False)
            poly = np.column_stack([p["cx"] + p["r"] * np.cos(a), p["cy"] + p["r"] * np.sin(a)])
            return ("fill" if e.kind == "fill" else "stroke"), [(poly, True)]
        if t == "ellipse":
            n = max(12, int(math.pi * (p["rx"] + p["ry"]) / 1.0))
            a = np.linspace(0, 2 * math.pi, n, endpoint=False)
            r = math.radians(p.get("rot", 0.0))
            x = p["rx"] * np.cos(a)
            y = p["ry"] * np.sin(a)
            poly = np.column_stack([p["cx"] + x * math.cos(r) - y * math.sin(r), p["cy"] + x * math.sin(r) + y * math.cos(r)])
            return ("fill" if e.kind == "fill" else "stroke"), [(poly, True)]
        if t in ("polygon", "path"):
            return ("fill" if e.kind == "fill" else "stroke"), [(np.array(p["pts"], float), True)]
        if t == "line":
            return "stroke", [(np.array([[p["x1"], p["y1"]], [p["x2"], p["y2"]]], float), False)]
    if e.d:
        return ("fill" if e.kind == "fill" else "stroke"), flatten(e.d)
    return e.kind, []


def _dashed(pts: np.ndarray, closed: bool, dash: list) -> list:
    """Kesikli çizgiyi parçalara böl."""
    if closed:
        pts = np.vstack([pts, pts[:1]])
    seg = np.diff(pts, axis=0)
    L = np.hypot(seg[:, 0], seg[:, 1])
    cum = np.concatenate([[0], np.cumsum(L)])
    total = cum[-1]
    if total <= 0 or not dash or sum(dash) <= 0:
        return [pts]
    out = []
    s, k, on = 0.0, 0, True
    while s < total:
        ln = max(dash[k % len(dash)], 0.01)
        e = min(total, s + ln)
        if on:
            ts = np.linspace(s, e, max(2, int((e - s) / 1.0) + 2))
            xs = np.interp(ts, cum, pts[:, 0])
            ys = np.interp(ts, cum, pts[:, 1])
            out.append(np.column_stack([xs, ys]))
        s = e
        k += 1
        on = not on
    return out


def rasterize(e, f: int, ox: float, oy: float, shape) -> np.ndarray:
    """Elemanı f kat büyütülmüş ızgarada (ox, oy özgün piksel ofsetiyle) 0/1 maske olarak çiz."""
    img = np.zeros(shape, np.uint8)
    kind, polys = element_polys(e)
    if not polys:
        return img
    S = 16  # cv2 alt-piksel kaydırması (4 bit)

    def tr(p):
        q = np.empty_like(p)
        q[:, 0] = ((p[:, 0] - ox + 0.5) * f - 0.5) * S
        q[:, 1] = ((p[:, 1] - oy + 0.5) * f - 0.5) * S
        return np.round(q).astype(np.int32)

    if kind == "fill":
        arr = [tr(p) for p, _ in polys if len(p) >= 3]
        if arr:
            cv2.fillPoly(img, arr, 1, lineType=cv2.LINE_8, shift=4)
        return img
    th = max(1, int(round(max(e.width, 0.3) * f)))
    for p, closed in polys:
        parts = _dashed(p, closed, e.dash) if e.dash else [np.vstack([p, p[:1]]) if closed else p]
        for q in parts:
            if len(q) == 1 or (len(q) >= 2 and np.ptp(q, axis=0).max() < 0.05):
                c = tr(q[:1])[0]
                cv2.circle(img, (int(c[0]), int(c[1])), max(1, th // 2) * S, 1, -1, lineType=cv2.LINE_8, shift=4)
                continue
            cv2.polylines(img, [tr(q)], False, 1, thickness=th, lineType=cv2.LINE_8, shift=4)
    return img


def bbox_of(e, pad: float = 0.0) -> tuple:
    kind, polys = element_polys(e)
    if not polys:
        return None
    allp = np.vstack([p for p, _ in polys])
    x0, y0 = allp.min(axis=0)
    x1, y1 = allp.max(axis=0)
    r = (e.width / 2 if kind == "stroke" else 0.0) + pad
    return x0 - r, y0 - r, x1 + r, y1 + r
