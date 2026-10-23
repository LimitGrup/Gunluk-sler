"""Bölge maskesine temiz geometrik şekil oturtma (şema, kroki, grafik kutuları).

Bir renk bölgesinin piksellerinden, bir tasarımcının çizeceği nesneyi bulur:
dikdörtgen, köşesi yuvarlatılmış dikdörtgen (hap biçimi dahil), daire, elips ya da
düz kenarlı çokgen. Kenarlar kaplama (yumuşak kenar) değerlerinden piksel altı
doğrulukla ölçülür. Şekil görselle örtüşmüyorsa None döner; o bölge serbest yol olarak
çizilir.

Koordinatlar özgün görselin pikselidir: i. pikselin merkezi i'dedir.
"""
from __future__ import annotations

import math

import cv2
import numpy as np
from scipy import ndimage

K = 4  # karşılaştırma için büyütme


def _up(soft: np.ndarray) -> np.ndarray:
    H, W = soft.shape
    return cv2.resize(soft.astype(np.float32), (W * K, H * K), interpolation=cv2.INTER_LINEAR)


def _to_up(x, y):
    """Özgün piksel koordinatını büyütülmüş ızgaraya çevir."""
    return (x + 0.5) * K - 0.5, (y + 0.5) * K - 0.5


def rrect_points(x, y, w, h, r, rot=0.0, n_arc=12) -> np.ndarray:
    """Yuvarlak köşeli dikdörtgenin kenar noktaları (r=0: dikdörtgen)."""
    r = max(0.0, min(r, w / 2, h / 2))
    if r < 1e-6:
        pts = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], float)
    else:
        pts = []
        for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0),
                           (x + r, y + h - r, 90), (x + r, y + r, 180)):
            for t in np.linspace(a0, a0 + 90, n_arc):
                a = math.radians(t)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        pts = np.array(pts, float)
    if abs(rot) > 1e-6:
        cx, cy = x + w / 2, y + h / 2
        a = math.radians(rot)
        c, s = math.cos(a), math.sin(a)
        d = pts - [cx, cy]
        pts = np.column_stack([cx + d[:, 0] * c - d[:, 1] * s, cy + d[:, 0] * s + d[:, 1] * c])
    return pts


def ellipse_points(cx, cy, rx, ry, rot=0.0, n=None) -> np.ndarray:
    n = n or max(24, int(math.pi * (rx + ry)))
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    a = math.radians(rot)
    x = rx * np.cos(t)
    y = ry * np.sin(t)
    return np.column_stack([cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)])


def prim_points(p: dict) -> np.ndarray:
    t = p["type"]
    if t == "rect":
        return rrect_points(p["x"], p["y"], p["w"], p["h"], 0.0, p.get("rot", 0.0))
    if t == "rrect":
        return rrect_points(p["x"], p["y"], p["w"], p["h"], p["r"], p.get("rot", 0.0))
    if t == "circle":
        return ellipse_points(p["cx"], p["cy"], p["r"], p["r"])
    if t == "ellipse":
        return ellipse_points(p["cx"], p["cy"], p["rx"], p["ry"], p.get("rot", 0.0))
    if t in ("polygon", "path"):
        return np.array(p["pts"], float)
    raise ValueError(t)


def _render(pts: np.ndarray, ox: float, oy: float, shape) -> np.ndarray:
    """Noktaları (özgün piksel) pencere (ox, oy) içinde büyütülmüş ızgarada doldur."""
    m = np.zeros(shape, np.uint8)
    q = np.empty_like(pts)
    q[:, 0], q[:, 1] = _to_up(pts[:, 0] - ox, pts[:, 1] - oy)
    cv2.fillPoly(m, [np.round(q * 16).astype(np.int32)], 1, lineType=cv2.LINE_8, shift=4)
    # fillPoly kenar hücrelerini iki yanda da doldurur (şekil bir hücre geniş çıkar): sağ ve alt
    # kenardaki bir hücrelik fazlalık atılır; küçük şekillerin örtüşmesi haksız yere düşmesin
    m[:, :-1] &= m[:, 1:]
    m[:, -1] = 0
    m[:-1, :] &= m[1:, :]
    m[-1, :] = 0
    return m


def _score(M: np.ndarray, R: np.ndarray, P: np.ndarray, tol: float | None = None):
    """(örtüşme oranı, kenar sapmasının %85'i özgün pikselde). tol verilirse: kenarın uzunca bir
    parçası şekilden belirgin ayrılıyorsa (bir kenarı eğri, köşesi kırık) sapma çok büyük sayılır."""
    inter = np.count_nonzero(M & R)
    uni = np.count_nonzero(M | R)
    iou = inter / uni if uni else 0.0
    R8 = R.astype(np.uint8)
    edge = R & ~(cv2.erode(R8, np.ones((3, 3), np.uint8)) > 0)
    if not edge.any():
        return iou, 1e9
    dt = cv2.distanceTransform((~edge.astype(bool)).astype(np.uint8), cv2.DIST_L2, 3)
    ys = np.clip(P[:, 1].astype(int), 0, M.shape[0] - 1)
    xs = np.clip(P[:, 0].astype(int), 0, M.shape[1] - 1)
    d = dt[ys, xs] / K
    if tol is not None and len(d) > 8:
        over = d > max(2.0 * tol, 2.0)
        if over.any() and not over.all():
            # dairesel dizide en uzun ardışık aşım
            k0 = int(np.argmin(over))
            o = np.roll(over, -k0)
            run = best = 0
            for v in o:
                run = run + 1 if v else 0
                best = max(best, run)
            perim = len(d) / K
            if best / K > max(8.0, 0.06 * perim):
                return iou, 1e9
        elif over.all():
            return iou, 1e9
    # kenar sapması: tek piksellik pürüz ve değen çizgi uçları sayılmasın diye %85'lik dilim
    return iou, float(np.percentile(d, 85))


def _profile_extent(soft: np.ndarray, axis: int, lo: int, hi: int) -> float:
    """Ortadaki satır/sütunlarda bölgenin genişliği (kaplama toplamı)."""
    if axis == 0:   # genişlik: satırlar boyunca topla
        band = soft[lo:hi, :]
        return float(np.median(band.sum(axis=1))) if band.size else 0.0
    band = soft[:, lo:hi]
    return float(np.median(band.sum(axis=0))) if band.size else 0.0


def _edge_pos(profile: np.ndarray, rising: bool) -> float | None:
    """Kaplama profilinden kenarın yeri (piksel altı): tam dolu ilk/son piksel ve
    önündeki/arkasındaki kısmi kaplamalar."""
    p = np.asarray(profile, float)
    idx = np.flatnonzero(p >= 0.85)
    if not len(idx):
        return None
    if rising:
        j = idx[0]
        part = float(np.clip(p[max(0, j - 2):j], 0, 1).sum())
        return j - 0.5 - part
    j = idx[-1]
    part = float(np.clip(p[j + 1:j + 3], 0, 1).sum())
    return j + 0.5 + part


def _axis_box(soft: np.ndarray):
    """Eksene paralel kutunun piksel altı kenarları (pencere koordinatı): x0, y0, x1, y1.

    Her satırın (sütunun) kenarı kaplama profilinden ölçülür; ortadaki satırların en dıştaki
    kenarı alınır (yuvarlak uçlu hap biçiminde yalnız orta satır tam genişliktedir)."""
    H, W = soft.shape
    rows = np.flatnonzero(soft.max(axis=1) >= 0.5)
    cols = np.flatnonzero(soft.max(axis=0) >= 0.5)
    if len(rows) < 2 or len(cols) < 2:
        return None
    r0, r1 = rows[0], rows[-1]
    c0, c1 = cols[0], cols[-1]
    rr = range(r0 + (r1 - r0) // 4, r1 - (r1 - r0) // 4 + 1)
    cc = range(c0 + (c1 - c0) // 4, c1 - (c1 - c0) // 4 + 1)
    Ls = [v for v in (_edge_pos(soft[i, :], True) for i in rr) if v is not None]
    Rs = [v for v in (_edge_pos(soft[i, :], False) for i in rr) if v is not None]
    Ts = [v for v in (_edge_pos(soft[:, j], True) for j in cc) if v is not None]
    Bs = [v for v in (_edge_pos(soft[:, j], False) for j in cc) if v is not None]
    if not (Ls and Rs and Ts and Bs):
        return None
    # bir iki satırlık sivri çıkıntılar (kenara değen çizgi ucu) kenar sayılmaz
    def duz(v):
        v = np.asarray(v, float)
        return ndimage.median_filter(v, size=5, mode="nearest") if len(v) >= 5 else v
    Ls, Rs, Ts, Bs = duz(Ls), duz(Rs), duz(Ts), duz(Bs)

    # en dıştaki kenarlar, tek piksellik pürüze karşı en uçtaki birkaç satırın ortası
    def lo(v):
        v = np.sort(v)
        return float(np.median(v[:max(1, len(v) // 10)]))

    def hi(v):
        v = np.sort(v)[::-1]
        return float(np.median(v[:max(1, len(v) // 10)]))
    return lo(Ls), lo(Ts), hi(Rs), hi(Bs)


def uydur(soft: np.ndarray, ox: float, oy: float, kinds=("rect", "rrect", "ellipse", "poly"),
          tol_px: float = 1.1, min_iou: float = 0.955):
    """Yumuşak bölge maskesine (0..1) şekil oturt. ox, oy: pencerenin özgün piksel ofseti.

    Dönüş: prim sözlüğü (özgün piksel koordinatında) ya da None.
    """
    H, W = soft.shape
    if H < 3 or W < 3 or soft.max() < 0.5:
        return None
    soft = np.clip(soft.astype(np.float32), 0, 1)
    up = _up(soft)
    M = (up >= 0.5).astype(np.uint8)
    # bir pikselden ince çıkıntılar (değen çizgi ucu, kenar pürüzü) şeklin parçası değil
    M = cv2.morphologyEx(M, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (K + 1, K + 1)))
    cs, _ = cv2.findContours(M, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        return None
    c = max(cs, key=cv2.contourArea)
    if len(c) < 12:
        return None
    M = np.zeros_like(M)
    cv2.drawContours(M, [c], -1, 1, -1)
    P = c[:, 0, :].astype(float)
    area = float(soft[soft >= 0.02].sum())
    size = max(H, W)
    tol = max(tol_px, 0.008 * size)
    cands = []

    def test(prim, rank):
        pts = prim_points(prim)
        R = _render(pts, ox, oy, M.shape)
        iou, err = _score(M.astype(bool), R.astype(bool), P, tol)
        if iou >= min_iou and err <= tol:
            cands.append((rank, -iou, prim, iou, err))
        return iou, err

    # --- eksene paralel dikdörtgen / yuvarlak köşeli dikdörtgen
    box = _axis_box(soft)
    if box is not None and ("rect" in kinds or "rrect" in kinds):
        L, T, R_, B = box
        w, h = R_ - L, B - T
        if w > 1.5 and h > 1.5:
            x, y = L + ox, T + oy
            deficit = max(0.0, w * h - area)
            r = math.sqrt(deficit / (4 - math.pi)) if deficit > 0 else 0.0
            r = min(r, w / 2, h / 2)

            def sc(prim):
                Rm = _render(prim_points(prim), ox, oy, M.shape)
                return _score(M.astype(bool), Rm.astype(bool), P, tol)
            rect_p = {"type": "rect", "x": x, "y": y, "w": w, "h": h}
            ri, re = sc(rect_p) if "rect" in kinds else (0.0, 1e9)
            best = None
            if "rrect" in kinds and r >= 1.2:
                for rr in (r, r * 0.85, r * 1.15, min(w, h) / 2):
                    rr = min(rr, w / 2, h / 2)
                    prim = {"type": "rrect", "x": x, "y": y, "w": w, "h": h, "r": rr}
                    iou, err = sc(prim)
                    if best is None or (err, -iou) < (best[0], -best[1]):
                        best = (err, iou, prim)
            rect_ok = ri >= min_iou and re <= tol
            rr_ok = best is not None and best[1] >= min_iou and best[0] <= tol
            if rr_ok:
                # yuvarlak köşe dördünde de görülmeli (yalnız iki köşesi kırık sütun dikdörtgendir)
                s_ = max(1, int(math.ceil(r)))
                # kutunun piksel aralığı (bitiş hariç): i. piksel [i-0.5, i+0.5]
                xa, xb = int(round(L + 0.5)), int(round(R_ + 0.5))
                ya, yb = int(round(T + 0.5)), int(round(B + 0.5))
                eks = []
                for (yy0, xx0) in ((ya, xa), (ya, xb - s_), (yb - s_, xa), (yb - s_, xb - s_)):
                    blk = soft[max(0, yy0):max(0, yy0) + s_, max(0, xx0):max(0, xx0) + s_]
                    eks.append(float(blk.size) - float(blk.sum()))
                # (köşelerden biri neredeyse tam doluysa: yalnız bazı köşeleri kırık dikdörtgen)
                if max(eks) > 0.3 and min(eks) < 0.15 * max(eks):
                    rr_ok = False
            # yuvarlak köşe belirgin daha iyi oturuyorsa yuvarlak köşeli
            if rr_ok and best[2]["r"] >= 0.47 * min(w, h) and abs(w - h) <= 0.05 * max(w, h):
                pass        # dört köşesi de tam yuvarlak kare: daire olarak aşağıda
            elif rr_ok and (not rect_ok or best[0] + 0.25 < re or best[1] > ri + 0.004):
                cands.append((0, -best[1], best[2], best[1], best[0]))
            elif rect_ok:
                cands.append((0, -ri, rect_p, ri, re))
    # --- döndürülmüş dikdörtgen
    if "rect" in kinds and not cands:
        (rcx, rcy), (rw, rh), ang = cv2.minAreaRect(c[:, 0, :].astype(np.float32))
        if 1.5 < abs(ang) % 90 < 88.5 and rw > 4 and rh > 4:
            rw, rh = rw / K, rh / K
            cx, cy = (rcx + 0.5) / K - 0.5 + ox, (rcy + 0.5) / K - 0.5 + oy
            test({"type": "rect", "x": cx - rw / 2, "y": cy - rh / 2, "w": rw, "h": rh, "rot": ang}, 2)
    # --- daire / elips
    if "ellipse" in kinds and len(P) >= 20:
        try:
            (ex, ey), (ea, eb), ang = cv2.fitEllipse(P.astype(np.float32))
        except cv2.error:
            ex = None
        if ex is not None and ea > 6 and eb > 6:
            cx, cy = (ex + 0.5) / K - 0.5 + ox, (ey + 0.5) / K - 0.5 + oy
            rx, ry = ea / 2 / K, eb / 2 / K
            if abs(rx - ry) <= 0.04 * max(rx, ry):
                test({"type": "circle", "cx": cx, "cy": cy, "r": (rx + ry) / 2}, 1)
            else:
                rot = ang
                if abs(rot) < 1.0 or abs(rot - 180) < 1.0:
                    rot = 0.0
                elif abs(rot - 90) < 1.0:
                    rot, rx, ry = 0.0, ry, rx
                test({"type": "ellipse", "cx": cx, "cy": cy, "rx": rx, "ry": ry, "rot": rot}, 2)
    # --- düz kenarlı çokgen (L biçimli blok, üçgen, ok…): yalnız temel şekiller tutmazsa ve
    # köşeleri kırpılmış dikdörtgen (yuvarlak köşenin kaba hâli) değilse
    if "poly" in kinds and not cands:
        prim = _polygon(P, ox, oy, size)
        if prim is not None and not _kirpik_kose(prim["pts"]):
            pts = prim_points(prim)
            R = _render(pts, ox, oy, M.shape)
            iou, err = _score(M.astype(bool), R.astype(bool), P, tol)
            if iou >= 0.975 and err <= min(tol, 0.9) and len(prim["pts"]) <= 10:
                cands.append((3, -iou, prim, iou, err))
    # --- düz kenarlar ve çember yaylarından oluşan şekil (bir yanı kavisli bina, kesilmiş hap):
    # çokgenden az parçalıysa yay ile (kavis kırık çizgiyle değil)
    if "poly" in kinds and (not cands or cands[0][2]["type"] == "polygon"):
        prim = _parcali(P, ox, oy, size, tol)
        if prim is not None:
            R = _render(prim_points(prim), ox, oy, M.shape)
            iou, err = _score(M.astype(bool), R.astype(bool), P, tol)
            if iou >= 0.975 and err <= min(tol, 0.9):
                if not cands:
                    cands.append((4, -iou, prim, iou, err))
                elif len(prim["segs"]) < len(cands[0][2]["pts"]):
                    cands = [(3, -iou, prim, iou, err)]
    if not cands:
        return None
    cands.sort(key=lambda t: (t[0], t[1]))
    return cands[0][2]


def _kirpik_kose(pts) -> bool:
    """Çokgen, köşeleri kısa çapraz kenarlarla kırpılmış bir dikdörtgen mi."""
    P = np.array(pts, float)
    n = len(P)
    if n < 6:
        return False
    E = np.roll(P, -1, axis=0) - P
    L = np.hypot(E[:, 0], E[:, 1])
    ang = np.degrees(np.arctan2(E[:, 1], E[:, 0])) % 90
    diag = (ang > 15) & (ang < 75)
    short = L < 0.25 * L.max()
    return bool((diag & short).sum() >= 3)


def _polygon(P: np.ndarray, ox: float, oy: float, size: float):
    """Konturu az köşeli çokgene indir; eksene yakın kenarları tam yatay/dikey yap."""
    eps = max(1.2, 0.006 * size) * K
    ap = cv2.approxPolyDP(P.astype(np.float32).reshape(-1, 1, 2), eps, True)[:, 0, :].astype(float)
    n = len(ap)
    if n < 3 or n > 12:
        return None
    # her kenarı kontur noktalarına doğru olarak oturt (köşeler kesişimden)
    idx = [int(np.argmin(np.hypot(P[:, 0] - q[0], P[:, 1] - q[1]))) for q in ap]
    lines = []
    for i in range(n):
        a, b = idx[i], idx[(i + 1) % n]
        seg = P[a:b + 1] if a <= b else np.vstack([P[a:], P[:b + 1]])
        if len(seg) >= 6:
            seg = seg[len(seg) // 8: len(seg) - len(seg) // 8]
        if len(seg) < 2:
            return None
        cc = seg.mean(axis=0)
        u, s, vt = np.linalg.svd(seg - cc)
        d = vt[0]
        ang = math.degrees(math.atan2(d[1], d[0])) % 180
        if min(ang, 180 - ang) < 3.0:
            d = np.array([1.0, 0.0])
            cc = np.array([cc[0], float(np.median(seg[:, 1]))])
        elif abs(ang - 90) < 3.0:
            d = np.array([0.0, 1.0])
            cc = np.array([float(np.median(seg[:, 0])), cc[1]])
        lines.append((cc, d))
    pts = []
    for i in range(n):
        (c1, d1), (c2, d2) = lines[i - 1], lines[i]
        A = np.array([d1, -d2]).T
        if abs(np.linalg.det(A)) < 1e-6:
            q = ap[i]
        else:
            t = np.linalg.solve(A, c2 - c1)
            q = c1 + d1 * t[0]
        pts.append(((q[0] + 0.5) / K - 0.5 + ox, (q[1] + 0.5) / K - 0.5 + oy))
    return {"type": "polygon", "pts": [(float(x), float(y)) for x, y in pts]}


def _daire(pts: np.ndarray):
    """En küçük kareler çemberi: (cx, cy, r, sapmalar)."""
    x, y = pts[:, 0], pts[:, 1]
    A = np.column_stack([x, y, np.ones_like(x)])
    sol = np.linalg.lstsq(A, x * x + y * y, rcond=None)[0]
    cx, cy = sol[0] / 2, sol[1] / 2
    r = math.sqrt(max(sol[2] + cx * cx + cy * cy, 0.0))
    return cx, cy, r, np.abs(np.hypot(x - cx, y - cy) - r)


def _dogru(seg: np.ndarray):
    """Noktalara doğru: (bir nokta, birim yön); eksene yakınsa tam yatay/dikey."""
    if len(seg) >= 6:
        seg = seg[len(seg) // 10: len(seg) - len(seg) // 10]
    c = seg.mean(axis=0)
    d = np.linalg.svd(seg - c)[2][0]
    ang = math.degrees(math.atan2(d[1], d[0])) % 180
    if min(ang, 180 - ang) < 2.5:
        return np.array([c[0], float(np.median(seg[:, 1]))]), np.array([1.0, 0.0])
    if abs(ang - 90) < 2.5:
        return np.array([float(np.median(seg[:, 0])), c[1]]), np.array([0.0, 1.0])
    return c, d


def _kesisim(g1, g2, near):
    """İki parçanın (doğru ya da çember) birleşme noktası: kesişimlerden birleşme yerine en yakını;
    kesişmiyorlarsa teğet noktası ya da birleşme yeri."""
    def line_circle(c, d, cx, cy, r):
        f = c - [cx, cy]
        b = float(f @ d)
        q = float(f @ f) - r * r
        disc = b * b - q
        if disc < 0:
            t = -b      # en yakın nokta (teğete yakın)
            return [c + d * t]
        sq = math.sqrt(disc)
        return [c + d * (-b - sq), c + d * (-b + sq)]
    if g1[0] == "L" and g2[0] == "L":
        (c1, d1), (c2, d2) = g1[1:3], g2[1:3]
        A = np.array([d1, -d2]).T
        if abs(np.linalg.det(A)) < 1e-6:
            return near
        t = np.linalg.solve(A, c2 - c1)
        return c1 + d1 * t[0]
    if g1[0] == "A" and g2[0] == "A":
        x1, y1, r1 = g1[1:4]
        x2, y2, r2 = g2[1:4]
        dd = math.hypot(x2 - x1, y2 - y1)
        if dd < 1e-6 or dd > r1 + r2 or dd < abs(r1 - r2):
            return near
        a = (r1 * r1 - r2 * r2 + dd * dd) / (2 * dd)
        hh = math.sqrt(max(r1 * r1 - a * a, 0.0))
        mx, my = x1 + a * (x2 - x1) / dd, y1 + a * (y2 - y1) / dd
        cands = [np.array([mx + hh * (y2 - y1) / dd, my - hh * (x2 - x1) / dd]),
                 np.array([mx - hh * (y2 - y1) / dd, my + hh * (x2 - x1) / dd])]
    else:
        L, A_ = (g1, g2) if g1[0] == "L" else (g2, g1)
        cands = line_circle(L[1], L[2], *A_[1:4])
    return min(cands, key=lambda q: float(np.hypot(*(q - near))))


def _parcali(P: np.ndarray, ox: float, oy: float, size: float, tol: float):
    """Konturu en az sayıda düz kenar ve çember yayına böl (dinamik programlama); temiz yol
    olarak döndür, olmazsa None. Kırılma yerleri az köşeli yaklaşık çokgenin köşeleridir."""
    ap = cv2.approxPolyDP(P.astype(np.float32).reshape(-1, 1, 2), 0.5 * K, True)[:, 0, :]
    idx = sorted({int(np.argmin(np.hypot(P[:, 0] - q[0], P[:, 1] - q[1]))) for q in ap})
    m = len(idx)
    if m < 3 or m > 80:
        return None
    N = len(P)
    lim = 0.75 * K

    # başlangıç: en keskin köşe (orada kesin kırılma vardır)
    def turn(i):
        p0, p1, p2 = P[idx[i - 1]], P[idx[i]], P[idx[(i + 1) % m]]
        v1, v2 = p1 - p0, p2 - p1
        n1, n2 = np.hypot(*v1), np.hypot(*v2)
        if n1 < 1e-6 or n2 < 1e-6:
            return 0.0
        return abs(math.degrees(math.atan2(v1[0] * v2[1] - v1[1] * v2[0], float(v1 @ v2))))
    st = max(range(m), key=turn)
    order = [idx[(st + i) % m] + (N if st + i >= m else 0) for i in range(m)] + [idx[st] + N]
    PP = np.vstack([P, P])

    def piece(i, j):
        return PP[order[i]:order[j] + 1]
    memo = {}

    def fit(i, j):
        key = (i, j)
        if key in memo:
            return memo[key]
        seg = piece(i, j)
        res = None
        v = seg[-1] - seg[0]
        L = float(np.hypot(*v))
        if L > 1e-6:
            nrm = np.array([-v[1], v[0]]) / L
            if float(np.abs((seg - seg[0]) @ nrm).max()) <= lim:
                res = ("L",)
        if res is None and len(seg) >= 8:
            cx, cy, r, dev = _daire(seg)
            if r < 3 * size * K and float(dev.max()) <= lim * 1.3 and float(np.percentile(dev, 90)) <= lim:
                a0 = math.atan2(seg[0][1] - cy, seg[0][0] - cx)
                a1 = math.atan2(seg[-1][1] - cy, seg[-1][0] - cx)
                span = abs(math.degrees((a1 - a0 + math.pi) % (2 * math.pi) - math.pi))
                if L < 1e-6 or span >= 12 or len(seg) > 3.2 * r:
                    res = ("A", cx, cy, r)
        memo[key] = res
        return res
    INF = 10 ** 9
    best = [INF] * (m + 1)
    back = [-1] * (m + 1)
    best[0] = 0
    for j in range(1, m + 1):
        for i in range(max(0, j - 40), j):
            if best[i] >= INF:
                continue
            f = fit(i, j)
            if f is None:
                continue
            c = best[i] + (1.0 if f[0] == "L" else 1.05)
            if c < best[j]:
                best[j], back[j] = c, i
    if best[m] >= INF:
        return None
    cuts = [m]
    while cuts[-1] > 0:
        cuts.append(back[cuts[-1]])
    cuts = cuts[::-1]
    geo = []
    for i, j in zip(cuts[:-1], cuts[1:]):
        f = fit(i, j)
        seg = piece(i, j)
        if f[0] == "L":
            c, d = _dogru(seg)
            geo.append(("L", c, d, seg))
        else:
            geo.append(("A", f[1], f[2], f[3], seg))
    n = len(geo)
    if n < 2 or n > 14 or not any(g[0] == "A" for g in geo):
        return None
    verts = []
    for i in range(n):
        verts.append(_kesisim(geo[i - 1], geo[i], geo[i][-1][0]))

    def to_px(q):
        return (float(q[0]) + 0.5) / K - 0.5 + ox, (float(q[1]) + 0.5) / K - 0.5 + oy
    segs, pts = [], []
    for i in range(n):
        g = geo[i]
        q0, q1 = verts[i], verts[(i + 1) % n]
        pts.append(to_px(q0))
        if g[0] == "L":
            segs.append(("L",) + to_px(q1))
            continue
        cx, cy, r = g[1:4]
        seg = g[4]
        mid = seg[len(seg) // 2]
        a0 = math.atan2(q0[1] - cy, q0[0] - cx)
        a1 = math.atan2(q1[1] - cy, q1[0] - cx)
        am = math.atan2(mid[1] - cy, mid[0] - cx)
        d1 = (a1 - a0) % (2 * math.pi)
        dm = (am - a0) % (2 * math.pi)
        if dm < d1:
            sweep, delta = 1, d1
        else:
            sweep, delta = 0, -((2 * math.pi) - d1)
        large = 1 if abs(delta) > math.pi else 0
        segs.append(("A", r / K, large, sweep) + to_px(q1))
        nseg = max(4, int(abs(delta) * r / K))
        for t in np.linspace(0, 1, nseg, endpoint=False)[1:]:
            a = a0 + delta * t
            pts.append(to_px((cx + r * math.cos(a), cy + r * math.sin(a))))
    return {"type": "path", "start": to_px(verts[0]), "segs": segs, "pts": [(float(x), float(y)) for x, y in pts]}


def _elips_uzaklik(P: np.ndarray, el) -> np.ndarray:
    """Noktaların elipse yaklaşık uzaklığı (büyütülmüş ızgarada)."""
    (ex, ey), (ea, eb), ang = el
    a, b = ea / 2, eb / 2
    t = math.radians(ang)
    c, s = math.cos(t), math.sin(t)
    x = (P[:, 0] - ex) * c + (P[:, 1] - ey) * s
    y = -(P[:, 0] - ex) * s + (P[:, 1] - ey) * c
    r = np.sqrt((x / max(a, 1e-6)) ** 2 + (y / max(b, 1e-6)) ** 2)
    return np.abs(r - 1) * min(a, b)


def iki_elips(soft: np.ndarray, ox: float, oy: float, tol_px: float = 1.0):
    """Bölge iki elipsin birleşimi mi (Venn şeması): [elips1, elips2] ya da None."""
    H, W = soft.shape
    up = _up(np.clip(soft, 0, 1))
    M = (up >= 0.5).astype(np.uint8)
    cs, _ = cv2.findContours(M, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        return None
    c = max(cs, key=cv2.contourArea)
    P = c[:, 0, :].astype(np.float64)
    if len(P) < 60:
        return None
    M = np.zeros_like(M)
    cv2.drawContours(M, [c], -1, 1, -1)
    tol = max(tol_px, 0.006 * max(H, W)) * K
    rng = np.random.default_rng(0)

    def fit_best(Q, iters=400):
        best = None
        m = len(Q)
        if m < 20:
            return None
        for _ in range(iters):
            # birbirine yakın olmayan beş nokta: aynı yayın farklı yerlerinden
            i0 = int(rng.integers(m))
            span = int(rng.integers(m // 6, m // 2 + 1))
            idx = [(i0 + span * j // 4) % m for j in range(5)]
            try:
                el = cv2.fitEllipse(Q[idx].astype(np.float32))
            except cv2.error:
                continue
            (ex, ey), (ea, eb), _a = el
            if not (np.isfinite(ex) and np.isfinite(ea)) or min(ea, eb) < 20 or max(ea, eb) > 4 * max(H, W) * K:
                continue
            inl = _elips_uzaklik(Q, el) <= tol
            k_ = int(inl.sum())
            if best is None or k_ > best[0]:
                best = (k_, el, inl)
        if best is None:
            return None
        # içteki noktalarla yeniden oturt
        k_, el, inl = best
        try:
            el = cv2.fitEllipse(Q[inl].astype(np.float32))
        except cv2.error:
            pass
        return el, _elips_uzaklik(Q, el) <= tol
    r1 = fit_best(P)
    if r1 is None:
        return None
    e1, in1 = r1
    if in1.mean() > 0.9 or in1.mean() < 0.3:
        return None         # tek elips (ya da hiç) — bu işlev değil
    r2 = fit_best(P[~in1])
    if r2 is None:
        return None
    e2, in2 = r2
    rest = ~in1
    rest_idx = np.flatnonzero(rest)
    covered = in1.copy()
    covered[rest_idx[in2]] = True
    if covered.mean() < 0.95:
        return None
    R = np.zeros_like(M)
    for el in (e1, e2):
        cv2.ellipse(R, el, 1, -1)
    inter = np.count_nonzero(M & R)
    uni = np.count_nonzero(M | R)
    if not uni or inter / uni < 0.975:
        return None
    out = []
    for (ex, ey), (ea, eb), ang in (e1, e2):
        cx, cy = (ex + 0.5) / K - 0.5 + ox, (ey + 0.5) / K - 0.5 + oy
        rx, ry, rot = ea / 2 / K, eb / 2 / K, ang
        if abs(rot) < 1.0 or abs(rot - 180) < 1.0:
            rot = 0.0
        elif abs(rot - 90) < 1.0:
            rot, rx, ry = 0.0, ry, rx
        if abs(rx - ry) <= 0.02 * max(rx, ry):
            out.append({"type": "circle", "cx": cx, "cy": cy, "r": (rx + ry) / 2})
        else:
            out.append({"type": "ellipse", "cx": cx, "cy": cy, "rx": rx, "ry": ry, "rot": rot})
    return out


def path_d(p: dict) -> str:
    """'path' şeklinin SVG yol verisi."""
    def f(v):
        s = f"{v:.2f}".rstrip("0").rstrip(".")
        return s if s not in ("-0", "") else "0"
    out = [f"M{f(p['start'][0])} {f(p['start'][1])}"]
    for sg in p["segs"]:
        if sg[0] == "L":
            out.append(f"L{f(sg[1])} {f(sg[2])}")
        else:
            out.append(f"A{f(sg[1])} {f(sg[1])} 0 {sg[2]} {sg[3]} {f(sg[4])} {f(sg[5])}")
    return "".join(out) + "Z"


def halka(ring: np.ndarray, interior: np.ndarray, cov: np.ndarray, ox: float, oy: float):
    """İnce kapalı çizgi (kutu çerçevesi): iç boşluğa şekil oturt, çizgi ortasına taşı.

    ring: çizginin pikselleri (bool), interior: içteki boşluk (bool), cov: çizgi renginin
    kaplaması. Dönüş: (prim, kalınlık) ya da None.
    """
    soft = interior.astype(np.float32)
    # içe bakan kenar pikselleri kısmen boştur: kaplamadan piksel altı sınır
    edge = (cv2.dilate(interior.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & ~interior
    soft[edge] = np.clip(1.0 - cov[edge], 0, 1) * 0.999
    prim = uydur(soft, ox, oy, kinds=("rect", "rrect", "ellipse"), tol_px=0.9, min_iou=0.95)
    if prim is None:
        return None
    # kalınlık: halkanın kaplama kütlesi / çevre
    pts = prim_points(prim)
    per = float(np.sum(np.hypot(*np.diff(np.vstack([pts, pts[:1]]), axis=0).T)))
    mass = float(cov[ring].sum())
    wd = float(np.clip(mass / max(per, 1.0), 0.5, 8.0))
    return grow(prim, wd / 2), wd


def grow(prim: dict, d: float) -> dict:
    """Şekli her yönde d kadar büyüt (çizgi ortasına taşımak için)."""
    p = dict(prim)
    t = p["type"]
    if t in ("rect", "rrect"):
        p["x"] -= d
        p["y"] -= d
        p["w"] += 2 * d
        p["h"] += 2 * d
        if t == "rrect":
            p["r"] = max(0.0, p["r"] + d)
    elif t == "circle":
        p["r"] += d
    elif t == "ellipse":
        p["rx"] += d
        p["ry"] += d
    return p
