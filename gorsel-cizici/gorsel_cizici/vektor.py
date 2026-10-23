"""Görseli temiz vektör şekillere çevirir.

Ders kitabı çizimleri az sayıda düz renkten oluşur. Adımlar:
  1. Renk paleti: düz (pürüzsüz) bölgelerin renkleri + ince çizgilerin renkleri.
  2. Her pikseli bir palet rengine ata; kenar yumuşatması (iki rengin karışımı) olan
     pikselleri karışımı oluşturan iki renkten yakın olanına ver.
  3. Her rengin ince kısımları çizgi (kontur), kalın kısımları dolgu olur.
  4. Çizgiler iskelet üzerinden tek çizgi olarak izlenir; kısa, aynı hizadaki parçalar
     kesikli çizgi olur. Dolgular konturlarından izlenir.
  5. Şekiller tanınır: düz çizgi, dikdörtgen, çember, elips, çember yayı; kalanlar
     Bézier eğrisi olur.
  6. Yazılar: yapay zekâ yazıları verirse yazı pikselleri şekillerden çıkarılır ve
     düzenlenebilir yazı olur; vermezse harfler dolgulu şekil olarak izlenir.
Bütün koordinatlar özgün görselin pikselleridir.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import cv2
import numpy as np
from scipy import ndimage
from skimage.measure import find_contours
from skimage.morphology import skeletonize

from . import egri, sadakat, sekil


# ---------------------------------------------------------------- veri yapıları
@dataclass
class Element:
    kind: str                       # "fill" | "stroke" | "text"
    color: tuple                    # (r, g, b)
    d: str = ""                     # SVG yol verisi (özgün piksel)
    prim: dict | None = None        # {"type": "rect" | "circle" | "ellipse" | "line" | "polygon", ...}
    width: float = 0.0              # çizgi kalınlığı (px)
    dash: list | None = None        # kesik deseni (px)
    cap: str = "butt"
    area: float = 0.0
    bbox: tuple = (0, 0, 0, 0)      # x0, y0, x1, y1
    layer: str = ""
    # yazı
    text: str = ""
    x: float = 0.0
    y: float = 0.0
    size: float = 0.0
    bold: bool = False
    anchor: str = "start"
    grad: dict | None = None        # renk geçişi: {"type": "linear"|"radial", ..., "stops": [(konum, (r,g,b))]}
    stroke: tuple | None = None     # dolgunun kenar çizgisi rengi (dikdörtgen + kontur tek nesne)
    stroke_width: float = 0.0
    join: str = "round"             # çizgi köşe birleşimi (bağlantı çizgilerinde "miter")


@dataclass
class Scene:
    width: int
    height: int
    elements: list = field(default_factory=list)
    background: tuple = (255, 255, 255)
    notes: list = field(default_factory=list)
    underlay: str = ""              # en altta çizilecek hazır SVG grubu (ör. tanınan haritanın kendisi)


# ---------------------------------------------------------------- renk
def _to_lab(rgb: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)


def _lab_to_rgb(lab: np.ndarray) -> tuple:
    px = cv2.cvtColor(np.asarray(lab, dtype=np.float32).reshape(1, 1, 3), cv2.COLOR_Lab2RGB)[0, 0]
    return tuple(int(round(float(v) * 255)) for v in np.clip(px, 0, 1))


def _peaks(lab_px: np.ndarray, min_count: int, radius: float, limit: int, pooled: bool = False) -> list:
    """Lab renk histogramında birbirinden uzak tepe renkleri seç.

    pooled: tepe, çevresindeki kutularla birlikte sayılır (gürültülü görsellerde küçük
    işaretlerin rengi birçok kutuya dağılır)."""
    if len(lab_px) == 0:
        return []
    q = np.round(lab_px / 2.5).astype(np.int32)
    keys, inv, counts = np.unique(q, axis=0, return_inverse=True, return_counts=True)
    inv = inv.reshape(-1)
    sums = np.zeros((len(keys), 3))
    np.add.at(sums, inv, lab_px)
    means = sums / counts[:, None]
    order = np.argsort(-counts)
    chosen = []
    # gürültülü (ör. JPEG) görsellerde bir renk birçok komşu kutuya dağılır: tepe, çevresindeki
    # kutularla birlikte sayılır
    for i in order[:600]:
        if len(chosen) >= limit or (not pooled and counts[i] < min_count):
            break
        c = means[i]
        if any(np.linalg.norm(c - p) < radius for p, _ in chosen):
            continue
        # bu tepenin çevresindeki bütün renkler
        near = np.linalg.norm(means - c, axis=1) < radius * 0.6
        tot = counts[near].sum()
        if tot < min_count:
            continue
        cc = (means[near] * counts[near, None]).sum(axis=0) / tot
        chosen.append((cc, int(tot)))
    return chosen


def _soluk_tonlar(lab: np.ndarray, flat: np.ndarray, pal: np.ndarray, n: int) -> list:
    """Beyaza (ya da başka bir renge) çok yakın ama ayrı, geniş ve düz dolgular (açık pembe kutu,
    açık mavi zemin). Renk tepeleri bunları yakındaki renge katar; burada büyük, tek renkli
    lekeler olarak aranır (JPEG gürültüsü dağınık olduğundan leke oluşturmaz)."""
    h, w = lab.shape[:2]
    px = lab.reshape(-1, 3)
    d = np.stack([np.linalg.norm(px - p, axis=1) for p in pal], axis=1)
    dmin = d.min(axis=1).reshape(h, w)
    cand = flat & (dmin >= 3.5) & (dmin < 12.0)
    if cand.sum() < 150:
        return []
    n_c, cc, st, _ = cv2.connectedComponentsWithStats(cand.astype(np.uint8), connectivity=4)
    min_area = max(150, int(0.0015 * n))
    blobs = []
    for i in range(1, n_c):
        if st[i, cv2.CC_STAT_AREA] < min_area:
            continue
        m = cc == i
        cols = lab[m]
        if float(cols.std(axis=0).max()) > 3.0:
            continue
        blobs.append((np.median(cols, axis=0), int(m.sum())))
    out = []
    for c, a in sorted(blobs, key=lambda t: -t[1]):
        if all(np.linalg.norm(c - q) >= 3.5 for q in list(pal) + out):
            out.append(c)
    return out[:6]


def build_palette(lab: np.ndarray, u: float, exclude: np.ndarray | None = None, small_marks: bool = False) -> np.ndarray:
    h, w = lab.shape[:2]
    k = np.ones((3, 3), np.float32) / 9
    mean = cv2.filter2D(lab, -1, k, borderType=cv2.BORDER_REPLICATE)
    sq = cv2.filter2D(lab * lab, -1, k, borderType=cv2.BORDER_REPLICATE)
    var = np.clip(sq - mean * mean, 0, None).sum(axis=2)
    flat = var < 6.0
    if exclude is not None:
        flat &= ~exclude
    n = h * w
    min_count = max(int(10 * u * u), int(n * 0.00004))
    peaks = _peaks(lab[flat], min_count, 11.0, 18)
    pal = [p for p, _ in peaks]
    if not pal:
        pal = [np.array([100.0, 0, 0])]
    pal += _soluk_tonlar(lab, flat, np.array(pal), n)
    pal_arr = np.array(pal)
    # İnce çizgilerin rengi düz bölgelerde görünmeyebilir: açıklanamayan koyu/renkli
    # pikselleri (yerel uç değerleri) ayrıca topla
    flatpx = lab.reshape(-1, 3)
    d = np.min(np.linalg.norm(flatpx[:, None, :] - pal_arr[None, :, :], axis=2), axis=1).reshape(h, w)
    Lc = lab[:, :, 0]
    mn = cv2.erode(Lc, np.ones((3, 3), np.uint8))
    mx = cv2.dilate(Lc, np.ones((3, 3), np.uint8))
    extreme = ((Lc <= mn + 0.01) | (Lc >= mx - 0.01)) & (d > 14)
    if exclude is not None:
        extreme &= ~exclude
    extra = _peaks(lab[extreme], max(int(6 * u * u), 12), 11.0, 8)
    # gürültülü görsellerde küçük renkli işaretler (nokta, harf) hiç tek kutuda toplanmaz:
    # açıklanamayan, belirgin renkli/koyu pikselleri komşu kutularla birlikte say
    chroma = np.hypot(lab[:, :, 1], lab[:, :, 2])
    base_ok = (d > 22) if small_marks else np.zeros_like(d, bool)
    if exclude is not None:
        base_ok &= ~exclude
    base = [p for p in pal_arr] + [c for c, _n in extra]

    def is_mix(c):
        # iki mevcut rengin karışımı (kenar yumuşatması) ise yeni renk değildir
        for i in range(len(base)):
            for j in range(i + 1, len(base)):
                A, B = base[i], base[j]
                AB = A - B
                nn = float(AB @ AB)
                if nn < 1e-6:
                    continue
                t = float(np.clip((c - B) @ AB / nn, 0, 1))
                if 0.08 < t < 0.92 and np.linalg.norm(c - (B + t * AB)) < 12:
                    return True
        return False

    # önce doygun renkli işaretler (kırmızı nokta…), sonra koyu harfler
    for sel, lim in ((base_ok & (chroma > 35), 3), (base_ok & (Lc < 35) & (chroma <= 35), 2)):
        if not sel.any():
            continue
        for c, cnt in _peaks(lab[sel], max(int(10 * u * u), 20), 14.0, lim, pooled=True):
            if all(np.linalg.norm(c - q) >= 14.0 for q in base) and not is_mix(c):
                extra.append((c, cnt))
                base.append(c)
    for c, cnt in extra:
        if np.min(np.linalg.norm(pal_arr - c, axis=1)) >= 11.0:
            pal_arr = np.vstack([pal_arr, c])
    return _drop_blends(lab, pal_arr)


def _drop_blends(lab: np.ndarray, pal: np.ndarray) -> np.ndarray:
    """Yalnız kenar yumuşatmasından doğan ara renkleri paletten çıkar.

    Bir renk C, başka iki rengin (A ile B) RGB karışımına denk geliyor, kendi başına dolu bir
    alan oluşturmuyor ve aynı ince yapının içinde A'ya daha yakın (daha koyu) pikseller de
    varsa, C yalnızca A renkli ince bir çizginin kısmen kapladığı pikseldir.
    """
    h, w = lab.shape[:2]
    rgb = cv2.cvtColor(lab.astype(np.float32), cv2.COLOR_Lab2RGB).reshape(-1, 3) * 255.0
    ker = np.ones((5, 5), np.uint8)
    for _ in range(len(pal)):
        if len(pal) <= 2:
            break
        P = np.array([_lab_to_rgb(p) for p in pal], dtype=np.float32)
        D = np.stack([np.linalg.norm(rgb - p, axis=1) for p in P], axis=1)
        lab0 = np.argmin(D, axis=1).reshape(h, w)
        counts = np.bincount(lab0.ravel(), minlength=len(pal))
        near = [cv2.dilate((lab0 == k).astype(np.uint8), ker) > 0 for k in range(len(pal))]
        drop = None
        for c in np.argsort(counts):
            if counts[c] == 0:
                drop = c
                break
            mc = lab0 == c
            dt = cv2.distanceTransform(np.pad(mc.astype(np.uint8), 1), cv2.DIST_L2, 3)[1:-1, 1:-1]
            if (dt >= 2).sum() > max(20, 0.05 * counts[c]):
                continue          # dolu alanı var: gerçek renk
            for b in range(len(pal)):
                if b == c or near[b][mc].mean() < 0.3:
                    continue
                for a in range(len(pal)):
                    if a in (b, c):
                        continue
                    A, B, C = P[a], P[b], P[c]
                    AB = A - B
                    nab = float(AB @ AB)
                    if nab < 1e-6:
                        continue
                    al_c = float(np.clip(((C - B) @ AB) / nab, 0, 1))
                    if not 0.12 < al_c < 0.88 or np.linalg.norm(C - (B + al_c * AB)) > 16.0:
                        continue
                    al = np.clip(((rgb - B) @ AB) / nab, 0, 1)
                    res = np.linalg.norm(rgb - (B + al[:, None] * AB), axis=1)
                    on = ((res < 18) & (al > 0.1)).reshape(h, w)
                    n, cc = cv2.connectedComponents(on.astype(np.uint8), connectivity=8)
                    darker = np.zeros(n, bool)
                    dk = (al.reshape(h, w) > al_c + 0.15) & on
                    darker[np.unique(cc[dk])] = True
                    darker[0] = False
                    frac = float(darker[cc[mc]].mean())
                    if frac > 0.5:
                        drop = c
                        break
                if drop is not None:
                    break
            if drop is not None:
                break
        if drop is None:
            break
        pal = np.delete(pal, drop, axis=0)
    return pal


# ---------------------------------------------------------------- iskelet izleme
_NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def _neighbors(skel: np.ndarray, y: int, x: int) -> list:
    """m-komşuluk: ortak bir 4-komşu üzerinden zaten bağlı köşegenleri sayma."""
    h, w = skel.shape
    out = []
    for dy, dx in _NB:
        yy, xx = y + dy, x + dx
        if not (0 <= yy < h and 0 <= xx < w) or not skel[yy, xx]:
            continue
        if dy and dx and (skel[y, xx] or skel[yy, x]):
            continue
        out.append((yy, xx))
    return out


def trace_skeleton(skel: np.ndarray) -> list:
    """İskeleti uçtan uca ya da kavşaktan kavşağa giden çizgilere böl. Noktalar (x, y)."""
    ys, xs = np.nonzero(skel)
    nb = {}
    for y, x in zip(ys.tolist(), xs.tolist()):
        nb[(y, x)] = _neighbors(skel, y, x)
    node = {p for p, n in nb.items() if len(n) != 2}
    seen = set()
    paths = []

    def walk(a, b):
        path = [a, b]
        seen.add((a, b)); seen.add((b, a))
        prev, cur = a, b
        while cur not in node:
            nxt = [q for q in nb[cur] if q != prev and (cur, q) not in seen]
            if not nxt:
                break
            q = nxt[0]
            seen.add((cur, q)); seen.add((q, cur))
            path.append(q)
            prev, cur = cur, q
            if cur == path[0]:
                break
        return path

    for p in node:
        for q in nb[p]:
            if (p, q) not in seen:
                paths.append(walk(p, q))
    # kapalı halkalar
    for p, n in nb.items():
        if p in node:
            continue
        for q in n:
            if (p, q) not in seen:
                paths.append(walk(p, q))
    # tek başına pikseller
    for p, n in nb.items():
        if not n:
            paths.append([p])
    return [np.array([[x, y] for y, x in pth], dtype=float) for pth in paths]


# ---------------------------------------------------------------- yol yazımı
def _f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"


def _seg_path(pts: np.ndarray, closed: bool, tol: float, u: float, k: int | None = None) -> str:
    """Noktaları köşelerden bölüp her parçayı doğru / yay / Bézier yaz (ölçek: /u)."""
    n = len(pts)
    if n < 2:
        return ""
    if k is None:
        k = max(2, int(round(2.5 * u)))
    cs = egri.corners(pts, closed, k, 38.0)
    if closed:
        if not cs:
            cs = [0]
        order = cs + [cs[0] + n]
        segs = [np.vstack([pts[i % n] for i in range(a, b + 1)]) for a, b in zip(order[:-1], order[1:])]
    else:
        idx = [0] + [c for c in cs if 0 < c < n - 1] + [n - 1]
        segs = [pts[a:b + 1] for a, b in zip(idx[:-1], idx[1:])]
    start = segs[0][0]
    d = [f"M{_f(start[0] / u)} {_f(start[1] / u)}"]
    for sg in segs:
        kind, val = egri.classify_segment(sg, tol)
        if kind == "L":
            d.append(f"L{_f(val[0] / u)} {_f(val[1] / u)}")
        elif kind == "A":
            cx, cy, r, p1, large, sweep, tot = val
            if abs(tot) > 2 * math.pi - 0.2:
                # neredeyse tam çember: iki yarım yay
                mid = sg[len(sg) // 2]
                d.append(f"A{_f(r / u)} {_f(r / u)} 0 0 {sweep} {_f(mid[0] / u)} {_f(mid[1] / u)}")
                d.append(f"A{_f(r / u)} {_f(r / u)} 0 0 {sweep} {_f(p1[0] / u)} {_f(p1[1] / u)}")
            else:
                d.append(f"A{_f(r / u)} {_f(r / u)} 0 {large} {sweep} {_f(p1[0] / u)} {_f(p1[1] / u)}")
        else:
            for c in val:
                d.append("C" + " ".join(f"{_f(p[0] / u)} {_f(p[1] / u)}" for p in c[1:]))
    if closed:
        d.append("Z")
    return "".join(d)


# ---------------------------------------------------------------- dolgular
def _shape_of(outer: np.ndarray, u: float):
    """Tek konturlu bölge için basit şekil tanı (dikdörtgen, çember, elips)."""
    if len(outer) < 8:
        return None
    x0, y0 = outer.min(axis=0)
    x1, y1 = outer.max(axis=0)
    w, h = x1 - x0, y1 - y0
    if w < 1 or h < 1:
        return None
    # dikdörtgen: konturun neredeyse hepsi kutunun kenarında
    dx = np.minimum(np.abs(outer[:, 0] - x0), np.abs(outer[:, 0] - x1))
    dy = np.minimum(np.abs(outer[:, 1] - y0), np.abs(outer[:, 1] - y1))
    on_edge = np.minimum(dx, dy) <= max(0.9, 0.55 * u)
    poly_area = 0.5 * abs(np.dot(outer[:, 0], np.roll(outer[:, 1], 1)) - np.dot(outer[:, 1], np.roll(outer[:, 0], 1)))
    if on_edge.mean() > 0.97 or (on_edge.mean() > 0.85 and poly_area > 0.97 * w * h):
        return {"type": "rect", "x": x0 / u, "y": y0 / u, "w": w / u, "h": h / u}
    fit = egri.circle_fit(outer)
    if fit is not None:
        cx, cy, r, rms = fit
        if rms < max(0.45 * u, 0.012 * r) and abs(w - h) < max(1.5 * u, 0.06 * w):
            return {"type": "circle", "cx": cx / u, "cy": cy / u, "r": r / u}
    if len(outer) >= 12:
        try:
            (ex, ey), (ea, eb), ang = cv2.fitEllipse(outer.astype(np.float32))
        except cv2.error:
            ex = None
        if ex is not None and ea > 2 and eb > 2:
            t = math.radians(ang)
            ct, st = math.cos(t), math.sin(t)
            px = (outer[:, 0] - ex) * ct + (outer[:, 1] - ey) * st
            py = -(outer[:, 0] - ex) * st + (outer[:, 1] - ey) * ct
            rr = np.sqrt((px / (ea / 2)) ** 2 + (py / (eb / 2)) ** 2)
            dev = np.abs(rr - 1)
            poly_area = 0.5 * abs(np.dot(outer[:, 0], np.roll(outer[:, 1], 1)) - np.dot(outer[:, 1], np.roll(outer[:, 0], 1)))
            ell_area = math.pi * ea * eb / 4
            ok_area = abs(poly_area - ell_area) < 0.03 * max(poly_area, 1e-6)
            if ok_area and dev.mean() < 0.02 and dev.max() < 0.07 and max(ea, eb) < 8 * min(ea, eb):
                return {"type": "ellipse", "cx": ex / u, "cy": ey / u, "rx": ea / 2 / u, "ry": eb / 2 / u, "rot": ang}
    return None


# ---------------------------------------------------------------- çizgiler
def _join_paths(items: list, u: float) -> list:
    """Kavşaklarda bölünmüş ama aynı doğrultuda devam eden çizgileri birleştir.

    Uçlar ızgaraya konur; yakın ve zıt yönlü uç çiftleri en düz olandan başlayarak eşlenir.
    """
    items = [(np.asarray(t[0], float), t[1], t[2], t[3] if len(t) > 3 else 1.0) for t in items]
    n = len(items)
    if n < 2:
        return items
    k = max(1, int(3 * u))
    ends = []   # (yol, uç) -> (nokta, yön)
    for i, (p, w, L, _a) in enumerate(items):
        if len(p) < 2:
            continue
        a = p[0] - p[min(len(p) - 1, k)]
        b = p[-1] - p[max(0, len(p) - 1 - k)]
        ends.append((i, 0, p[0], a))
        ends.append((i, 1, p[-1], b))
    cell = 2.5 * u
    grid = {}
    for e, (i, side, P, dvec) in enumerate(ends):
        grid.setdefault((int(P[0] // cell), int(P[1] // cell)), []).append(e)
    cands = []
    for e, (i, side, P, dvec) in enumerate(ends):
        gx, gy = int(P[0] // cell), int(P[1] // cell)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for f2 in grid.get((gx + dx, gy + dy), ()):
                    if f2 <= e:
                        continue
                    j, side2, Q, dvec2 = ends[f2]
                    if j == i or np.hypot(*(P - Q)) > cell:
                        continue
                    n1, n2 = np.hypot(*dvec), np.hypot(*dvec2)
                    if n1 < 1e-6 or n2 < 1e-6:
                        continue
                    cosang = float(np.dot(dvec, dvec2) / (n1 * n2))
                    wi, wj = items[i][1], items[j][1]
                    if cosang < -0.94 and abs(wi - wj) < max(1.2 * u, 0.5 * max(wi, wj)):
                        cands.append((cosang, e, f2))
    cands.sort()
    link = {}   # uç -> karşı uç
    for _, e, f2 in cands:
        if e in link or f2 in link:
            continue
        link[e] = f2
        link[f2] = e
    # zincirleri yürü: yol i'nin uçları 2i, 2i+1 değil; ends dizisindeki indeksler
    end_of = {}
    for e, (i, side, P, dvec) in enumerate(ends):
        end_of[(i, side)] = e
    used = [False] * n
    out = []
    for i in range(n):
        if used[i]:
            continue
        # zincirin başına git
        cur, side = i, 0
        seen = {i}
        while True:
            e = end_of.get((cur, side))
            if e is None or e not in link:
                break
            j, s2, _, _ = ends[link[e]]
            if j in seen:
                break
            seen.add(j)
            cur, side = j, 1 - s2
        # baştan sona birleştir
        start_i, start_side = cur, side
        pts, wsum, Lsum, amax = [], 0.0, 0.0, 0.0
        cur, side = start_i, start_side
        visited = set()
        while cur is not None and cur not in visited:
            visited.add(cur)
            used[cur] = True
            p, w, L, al = items[cur]
            seg = p if side == 0 else p[::-1]
            pts.append(seg if not pts else seg[1:])
            wsum += w * L
            Lsum += L
            amax = max(amax, al)
            e = end_of.get((cur, 1 - side))
            if e is None or e not in link:
                break
            j, s2, _, _ = ends[link[e]]
            cur, side = j, s2
        P = np.vstack(pts) if pts else items[i][0]
        out.append((P, wsum / Lsum if Lsum > 0 else items[i][1], Lsum, amax))
    return out


def _dash_groups(segs: list, u: float):
    """Aynı doğru üzerinde, düzenli aralıklı kısa parçaları kesikli çizgi yap.

    segs: [(p0, p1, kalınlık)] ; dönüş: (gruplar, kullanılan indeksler)
    """
    n = len(segs)
    if n < 3:
        return [], set()
    dirs, mids, lens = [], [], []
    for p0, p1, _ in segs:
        v = p1 - p0
        L = float(np.hypot(*v))
        dirs.append(v / L if L > 1e-6 else None)
        mids.append((p0 + p1) / 2)
        lens.append(L)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i in range(n):
        for j in range(i + 1, n):
            gap = np.hypot(*(mids[i] - mids[j])) - (lens[i] + lens[j]) / 2
            # noktalı çizgide soluk kalıp görünmeyen bir nokta aralığı iki katına çıkarır
            sinir = 9 * u if max(lens[i], lens[j]) <= 1.5 * u else max(6 * u, 2.5 * max(lens[i], lens[j], 2 * u))
            if gap > sinir or gap < -u:
                continue
            # doğrultu: iki parçanın orta noktalarını birleştiren doğru
            v = mids[j] - mids[i]
            vn = float(np.hypot(*v))
            if vn < 1e-6:
                continue
            v = v / vn
            ok = True
            for k in (i, j):
                if dirs[k] is not None and lens[k] > 2 * u and abs(float(np.dot(dirs[k], v))) < 0.97:
                    ok = False
            if ok and abs(segs[i][2] - segs[j][2]) < max(1.2 * u, 0.6 * max(segs[i][2], segs[j][2])):
                parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    def bol(g):
        # doğruya oturmayan karışık grup (yakındaki başka parçalarla birleşmiş): yatay ve dikey
        # sıralara ayrılır; sıra içinde bağlanma aralığından uzun boşlukta bölünür
        parcalar = []
        for ax in (1, 0):
            kisa = [i for i in g if dirs[i] is None or lens[i] <= 2 * u or abs(float(dirs[i][1 - ax])) >= 0.97]
            kisa.sort(key=lambda i: float(mids[i][ax]))
            sira = []
            for i in kisa:
                if sira and abs(float(mids[i][ax]) - float(mids[sira[-1]][ax])) > 1.2 * u:
                    parcalar.append(sira)
                    sira = []
                sira.append(i)
            if sira:
                parcalar.append(sira)
        out_ = []
        for sira in parcalar:
            ax2 = 0 if abs(float(np.ptp([mids[i][0] for i in sira]))) >= abs(float(np.ptp([mids[i][1] for i in sira]))) else 1
            sira.sort(key=lambda i: float(mids[i][ax2]))
            zn = [sira[0]]
            for a_, b_ in zip(sira[:-1], sira[1:]):
                gap = abs(float(mids[b_][ax2] - mids[a_][ax2])) - (lens[a_] + lens[b_]) / 2
                sinir = 9 * u if max(lens[a_], lens[b_]) <= 1.5 * u else max(6 * u, 2.5 * max(min(lens[a_], lens[b_]), 2 * u))
                if gap > sinir:
                    if len(zn) >= 3:
                        out_.append(zn)
                    zn = []
                zn.append(b_)
            if len(zn) >= 3:
                out_.append(zn)
        return out_
    def zincir(g):
        # doğru boyunca sırala; bağlanma aralığından uzun boşlukta böl (ayrı iki çizgi birleşmesin)
        pts = np.vstack([np.vstack([segs[i][0], segs[i][1]]) for i in g])
        c_, d_, _dv = egri.line_fit(pts)
        t_ = {i: float((mids[i] - c_) @ d_) for i in g}
        sira = sorted(g, key=lambda i: t_[i])
        out_, zn = [], [sira[0]]
        for a_, b_ in zip(sira[:-1], sira[1:]):
            gap = abs(t_[b_] - t_[a_]) - (lens[a_] + lens[b_]) / 2
            # (kısa parçanın boyuna göre: uzun iki parça arasındaki büyük boşluk köprülenmez)
            sinir = 9 * u if max(lens[a_], lens[b_]) <= 1.5 * u else max(6 * u, 2.5 * max(min(lens[a_], lens[b_]), 2 * u))
            if gap > sinir:
                if len(zn) >= 3:
                    out_.append(zn)
                zn = []
            zn.append(b_)
        if len(zn) >= 3:
            out_.append(zn)
        return out_
    work = []
    for g in groups.values():
        if len(g) < 3:
            continue
        pts = np.vstack([np.vstack([segs[i][0], segs[i][1]]) for i in g])
        if egri.line_fit(pts)[2] > 1.5 * u:
            work.extend(bol(g))
        else:
            work.extend(zincir(g))
    out, used = [], set()
    for g in work:
        if len(g) < 3 or any(i in used for i in g):
            continue
        pts = np.vstack([np.vstack([segs[i][0], segs[i][1]]) for i in g])
        c, d, dev = egri.line_fit(pts)
        if dev > 1.5 * u:
            continue
        t = (pts - c) @ d
        order = sorted(g, key=lambda i: float(((segs[i][0] + segs[i][1]) / 2 - c) @ d))
        spans = []
        for i in order:
            a, b = float((segs[i][0] - c) @ d), float((segs[i][1] - c) @ d)
            spans.append((min(a, b), max(a, b)))
        dashes = [b - a for a, b in spans]
        gaps = [spans[k + 1][0] - spans[k][1] for k in range(len(spans) - 1)]
        if not gaps or min(gaps) < -u:
            continue
        # kesikli çizgide kesik ve aralıklar düzenlidir; düzensizse (üstünden başka şekiller
        # geçtiği için bölünmüş düz çizgi) kesikli sayma
        dz, gz = np.array(dashes[1:-1] or dashes), np.array(gaps)
        if len(dz) >= 3 and float(np.median(gz)) > 0.8:
            # tek tük aykırı parça (çizginin geçtiği yerde birleşen iki kesik, şeklin örttüğü kesik)
            # deseni bozmaz; parçaların çoğu düzenli olmalı
            md_, mg_ = float(np.median(dz)), float(np.median(gz))
            ok_d = float((np.abs(dz - md_) <= 0.45 * max(md_, 1e-6)).mean())
            if float(np.max(dz)) <= 1.6 * u:
                ok_d = 1.0      # noktalı çizgi: noktanın ölçülen boyu (0-1 piksel) oynar, aralık düzenlidir
            ok_g = float((np.abs(gz - mg_) <= 0.45 * max(mg_, 1e-6)).mean())
            if ok_d < 0.7 or ok_g < 0.7:
                continue
        # kalınlık: boya göre ağırlıklı ortanca (uzun çizginin yanındaki kırıntılar kalınlığı belirlemez)
        ws_ = np.array([segs[i][2] for i in g], float)
        wl_ = np.array([max(1.0, float(np.hypot(*(segs[i][1] - segs[i][0])))) for i in g])
        o_ = np.argsort(ws_)
        w = float(ws_[o_][np.searchsorted(np.cumsum(wl_[o_]), 0.5 * float(wl_.sum()))])
        p0 = c + d * t.min()
        p1 = c + d * t.max()
        out.append((p0, p1, w, dashes, gaps))
        used.update(g)
    return out, used


def _dash_pattern(dashes: list, gaps: list, w: float, iskelet: bool = False):
    """Kesik desenini çıkar: düz kesik, nokta ya da kesik-nokta.

    Kesikler iskeletten ölçülür: uçları yarım kalınlık kadar içeride kalır. Desenin adımı
    (kesik + aralık) kesik ortalarının aralığından alınır; kayma birikmesin."""
    dash = np.array(dashes)
    gap = float(np.median(gaps))
    if iskelet and len(dash) >= 3 and len(dashes) == len(gaps) + 1:
        steps = [dashes[i] / 2 + gaps[i] + dashes[i + 1] / 2 for i in range(len(gaps))]
        period = float(np.median(steps))
        md0 = float(np.median(dash))
        if md0 > w * 1.4:
            md = min(md0 + w, period - 0.8)
            if not (len(dash) >= 4 and (dash > np.median(dash) * 1.6).sum() >= 2):
                return [md, period - md], "butt"
    if len(dash) >= 4:
        long_ = dash[dash > np.median(dash) * 1.6]
        short = dash[dash <= np.median(dash) * 1.6]
        if len(long_) >= 2 and len(short) >= 2 and np.median(long_) > 2.2 * max(np.median(short), w):
            return [float(np.median(long_)), gap, max(float(np.median(short)), 0.1), gap], "butt"
    md = float(np.median(dash))
    if md <= w * 1.4:
        # noktalı çizgi: yuvarlak uçlu sıfır uzunluklu kesikler
        return [0.01, gap + md], "round"
    return [md, gap], "butt"


# ---------------------------------------------------------------- kaplama (coverage)
def unmix(rgb: np.ndarray, pal: np.ndarray):
    """Her pikselde her rengin payı (0..1). Kenar pikselleri iki rengin karışımıdır
    (karışım görsellerde RGB'de olur, bu yüzden RGB'de çözülür).

    rgb: H×W×3 (0..255), pal: K×3 RGB. Dönüş: (cov: K×H×W float32, labels: H×W)
    """
    h, w = rgb.shape[:2]
    K = len(pal)
    pal = np.asarray(pal, dtype=np.float32)
    flat = rgb.reshape(-1, 3).astype(np.float32)
    N = flat.shape[0]
    D = np.empty((N, K), np.float32)
    for k in range(K):
        D[:, k] = np.linalg.norm(flat - pal[k], axis=1)
    near_lab = np.argmin(D, axis=1)
    dmin = D[np.arange(N), near_lab]
    cov = np.zeros((K, N), np.float32)
    cov[near_lab, np.arange(N)] = 1.0
    if K < 2:
        return cov.reshape(K, h, w), near_lab.reshape(h, w)
    sure = (dmin < 14.0).reshape(h, w)
    ker = np.ones((5, 5), np.uint8)
    lab0 = near_lab.reshape(h, w)
    near = np.zeros((N, K), bool)
    for k in range(K):
        # komşulukta en yakın rengi bu olan bir piksel varsa aday (ince yazılarda hiç "tam siyah" piksel olmayabilir)
        m = (lab0 == k).astype(np.uint8)
        near[:, k] = (cv2.dilate(m, ker) > 0).reshape(-1)
    idx = np.flatnonzero(~sure.reshape(-1))
    if not len(idx):
        return cov.reshape(K, h, w), lab0
    cand = near[idx]
    px = flat[idx]
    single = np.where(cand, D[idx], np.inf)
    s_lab = np.argmin(single, axis=1)
    s_res = single[np.arange(len(idx)), s_lab]
    best_res = np.where(np.isfinite(s_res), s_res, D[idx, near_lab[idx]])
    best_a = np.where(np.isfinite(s_res), s_lab, near_lab[idx])
    best_b = best_a.copy()
    best_al = np.ones(len(idx), np.float32)
    for a in range(K):
        for b in range(a + 1, K):
            # en az biri yakında olmalı: ince bir çizginin rengi hiçbir pikselde tam görünmeyebilir
            ok = cand[:, a] | cand[:, b]
            if not ok.any():
                continue
            A, B = pal[a], pal[b]
            AB = A - B
            nab = float(AB @ AB)
            if nab < 1e-6:
                continue
            sel = np.flatnonzero(ok)
            p = px[sel]
            al = np.clip(((p - B) @ AB) / nab, 0, 1)
            res = np.linalg.norm(p - (B + al[:, None] * AB), axis=1)
            better = res * 1.5 < best_res[sel]
            if better.any():
                ii = sel[better]
                best_res[ii] = res[better] * 1.5
                best_a[ii] = a
                best_b[ii] = b
                best_al[ii] = al[better]
    cov[:, idx] = 0.0
    cov[best_a, idx] += best_al
    cov[best_b, idx] += np.where(best_b != best_a, 1.0 - best_al, 0.0).astype(np.float32)
    cov = cov.reshape(K, h, w)
    labels = np.argmax(cov, axis=0).astype(np.int32)
    return cov, labels


def _up(a: np.ndarray, f: int) -> np.ndarray:
    if f == 1:
        return a.astype(np.float32)
    return np.clip(cv2.resize(a.astype(np.float32), (a.shape[1] * f, a.shape[0] * f), interpolation=cv2.INTER_CUBIC), 0, 1)


def _contours_of(c_up: np.ndarray, f: int, ox: float, oy: float, min_area: float):
    """Büyütülmüş kaplama haritasının 0,5 eş-çizgileri, özgün piksel koordinatında."""
    pad = np.pad(c_up, 1)
    out = []
    for c in find_contours(pad, 0.5):
        if len(c) < 4:
            continue
        # piksel merkezleri: büyütmede (i+0,5)/f-0,5 dönüşümü
        x = (c[:, 1] - 1 + 0.5) / f - 0.5 + ox
        y = (c[:, 0] - 1 + 0.5) / f - 0.5 + oy
        pts = np.column_stack([x, y])
        if np.allclose(pts[0], pts[-1]):
            pts = pts[:-1]
        if len(pts) < 3:
            continue
        area = 0.5 * abs(np.dot(pts[:, 0], np.roll(pts[:, 1], 1)) - np.dot(pts[:, 1], np.roll(pts[:, 0], 1)))
        if area < min_area:
            continue
        out.append((area, pts))
    out.sort(key=lambda t: -t[0])
    return out


def _fill_element(conts, color, tol, shapes=True, layer=""):
    if not conts:
        return None
    area = conts[0][0] - sum(a for a, _ in conts[1:])
    pts0 = conts[0][1]
    allp = np.vstack([p for _, p in conts])
    bbox = (*allp.min(axis=0), *allp.max(axis=0))
    if shapes and len(conts) == 1:
        outer = egri.resample(pts0, 0.5, True)
        prim = _shape_of(outer, 1.0)
        if prim is not None:
            return Element("fill", color, prim=prim, area=float(area), bbox=tuple(map(float, bbox)), layer=layer)
    d = []
    for _, pts in conts:
        rs = egri.resample(pts, 0.5, True)
        if len(rs) >= 4:
            d.append(_seg_path(rs, True, tol, 1.0, k=3))
    if not d:
        return None
    return Element("fill", color, d="".join(d), area=float(area), bbox=tuple(map(float, bbox)), layer=layer)


# ---------------------------------------------------------------- renk geçişleri
def _simplify_stops(pos, cols, tol=7.0):
    """Renk eğrisini az sayıda durakla temsil et (RDP benzeri)."""
    keep = [0, len(pos) - 1]
    stack = [(0, len(pos) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        worst, wi = 0.0, -1
        for i in range(a + 1, b):
            t = (pos[i] - pos[a]) / max(pos[b] - pos[a], 1e-9)
            pred = cols[a] + (cols[b] - cols[a]) * t
            e = float(np.linalg.norm(cols[i] - pred))
            if e > worst:
                worst, wi = e, i
        if worst > tol:
            keep.append(wi)
            stack += [(a, wi), (wi, b)]
    keep = sorted(set(keep))
    return [(float(pos[i]), tuple(int(round(v)) for v in cols[i])) for i in keep]


def _grad_fit(lab_px, rgb_px, xs, ys):
    """Bölgedeki rengin yatay, dikey ya da merkezden dışa değiştiğini bul ve durakları çıkar."""
    tot = float(((lab_px - lab_px.mean(axis=0)) ** 2).sum())
    if tot <= 0:
        return None
    best = None
    cx, cy = xs.mean(), ys.mean()
    rr = np.hypot(xs - cx, ys - cy)
    for kind, coord in (("x", xs.astype(float)), ("y", ys.astype(float)), ("r", rr)):
        lo, hi = float(coord.min()), float(coord.max())
        span = hi - lo
        if span < 3:
            continue
        nb = int(np.clip(span / 1.5, 3, 40))
        bins = np.clip(((coord - lo) / span * nb).astype(int), 0, nb - 1)
        cnt = np.bincount(bins, minlength=nb)
        if (cnt == 0).any():
            continue
        means = np.zeros((nb, 3))
        np.add.at(means, bins, lab_px)
        means /= cnt[:, None]
        ex = 1 - float(((lab_px - means[bins]) ** 2).sum()) / tot
        if best is None or ex > best[0]:
            rgbm = np.zeros((nb, 3))
            np.add.at(rgbm, bins, rgb_px)
            rgbm /= cnt[:, None]
            best = (ex, kind, lo, hi, (np.arange(nb) + 0.5) / nb, rgbm)
    if best is None or best[0] < 0.85:
        return None
    ex, kind, lo, hi, pos, rgbm = best
    stops = _simplify_stops(pos, rgbm)
    if kind == "x":
        mid = float(cy)
        return {"type": "linear", "x1": lo, "y1": mid, "x2": hi, "y2": mid, "stops": stops}
    if kind == "y":
        mid = float(cx)
        return {"type": "linear", "x1": mid, "y1": lo, "x2": mid, "y2": hi, "stops": stops}
    return {"type": "radial", "cx": float(cx), "cy": float(cy), "r": hi, "stops": stops}


def find_gradients(lab: np.ndarray, rgb: np.ndarray):
    """Renk geçişli (degrade) bölgeler.

    Komşu pikseller renkleri yakınsa (adım küçükse) aynı bölgeye bağlanır; böylece dik bir
    geçiş de tek bölge olur, ama koyu bir kenar çizgisi ya da iki düz renk arasındaki keskin
    kenar bölgeleri ayırır. Zeminle aynı renkteki düz pikseller bağlanmaz. Sonra her bölgenin
    rengi yatay, dikey ya da merkezden dışa düzgün değişiyor mu diye bakılır.
    """
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    h, w = lab.shape[:2]
    if h < 4 or w < 4:
        return []
    q = np.round(lab.reshape(-1, 3) / 3).astype(np.int32)
    keys, cnt = np.unique(q, axis=0, return_counts=True)
    bgc = keys[cnt.argmax()] * 3.0
    near_bg = (np.linalg.norm(lab - bgc, axis=2) < 3.0).astype(np.uint8)
    # yalnız asıl zemin (kenara değen ya da büyük zemin parçaları) ayrılır; bir şeklin içinde
    # kalan zemin renkli pikseller (ör. sütunun parlak orta şeridi) şekle dahildir
    nb, bl, bst, _ = cv2.connectedComponentsWithStats(near_bg, connectivity=4)
    main = np.zeros(nb, bool)
    for j in range(1, nb):
        x, y, ww, hh, area = bst[j]
        if x == 0 or y == 0 or x + ww >= w or y + hh >= h or area > 0.05 * h * w:
            main[j] = True
    node = ~main[bl]
    T = 24.0
    dh = np.linalg.norm(lab[:, 1:] - lab[:, :-1], axis=2)
    dv = np.linalg.norm(lab[1:] - lab[:-1], axis=2)
    eh = (dh < T) & node[:, 1:] & node[:, :-1]
    ev = (dv < T) & node[1:] & node[:-1]
    idx = np.arange(h * w, dtype=np.int64).reshape(h, w)
    r = np.concatenate([idx[:, :-1][eh], idx[:-1][ev]])
    c = np.concatenate([idx[:, 1:][eh], idx[1:][ev]])
    G = coo_matrix((np.ones(len(r), np.int8), (r, c)), shape=(h * w, h * w))
    ncomp, lab_cc = connected_components(G, directed=False)
    lab_cc = lab_cc.reshape(h, w)
    lab_cc[~node] = -1
    sizes = np.bincount(lab_cc[node].ravel(), minlength=ncomp)
    flat_lab = lab_cc.ravel()
    sel = np.flatnonzero(flat_lab >= 0)
    sel = sel[sizes[flat_lab[sel]] >= 12]
    order_px = sel[np.argsort(flat_lab[sel], kind="stable")]
    labs_sorted = flat_lab[order_px]
    bounds = np.flatnonzero(np.diff(labs_sorted)) + 1
    comps = []
    for chunk in np.split(order_px, bounds) if len(order_px) else []:
        if len(chunk) > 0.4 * h * w:
            continue
        ys, xs = chunk // w, chunk % w
        comps.append((ys, xs, xs.min(), ys.min(), xs.max(), ys.max()))
    # Parlak orta şeridi zemine değen sütun iki yarıya bölünür: yan yana, aynı boydaki
    # parçaları aradaki zemin renkli piksellerle birlikte tek bölge olarak da dene.
    near = ~node
    groups = []
    used = set()
    order = sorted(range(len(comps)), key=lambda j: comps[j][2])
    for ii, a_ in enumerate(order):
        if a_ in used:
            continue
        ys, xs, x0, y0, x1, y1 = comps[a_]
        grp = [a_]
        for b_ in order[ii + 1:]:
            if b_ in used:
                continue
            _, _, u0, v0, u1, v1 = comps[b_]
            gx0, gy0, gx1, gy1 = comps[grp[-1]][2:]
            gap = u0 - gx1
            if gap > 5:
                break
            ov = min(gy1, v1) - max(gy0, v0)
            if gap >= 0 and ov >= 0.8 * min(gy1 - gy0, v1 - v0) and abs((v1 - v0) - (gy1 - gy0)) <= 2:
                grp.append(b_)
        if len(grp) >= 2:
            groups.append(grp)

    def test(ys, xs):
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        # renk geçişi geniş bir alandır (harf, kenar yumuşatması değil)
        if len(ys) < max(150, int(0.0008 * h * w)) or min(y1 - y0, x1 - x0) < 10:
            return None
        m = np.zeros((h, w), bool)
        m[ys, xs] = True
        sub = m[y0:y1, x0:x1].astype(np.uint8)
        # çizgi değil, alan olmalı (kenarı yumuşatılmış çizgiler de renk değiştirir)
        if cv2.distanceTransform(np.pad(sub, 1), cv2.DIST_L2, 3).max() < 2.5:
            return None
        labv = lab[ys, xs]
        med = np.median(labv, axis=0)
        if (np.linalg.norm(labv - med, axis=1) < 5).mean() > 0.55:
            return None      # çoğu düz renk
        qq = np.round(labv / 4).astype(np.int32)
        _, qc = np.unique(qq, axis=0, return_counts=True)
        if np.sort(qc)[-2:].sum() > 0.7 * len(labv) or np.sort(qc)[-4:].sum() > 0.75 * len(labv):
            return None      # birkaç düz rengin yan yana gelmesi (ör. bitişik sütunlar)
        spread = float(np.linalg.norm(np.percentile(labv, 95, axis=0) - np.percentile(labv, 5, axis=0)))
        if spread < 15:
            return None
        g = _grad_fit(labv, rgb[ys, xs].astype(float), xs, ys)
        if g is None:
            return None
        return m, g

    out = []
    done = set()
    for grp in groups:
        m = np.zeros((h, w), bool)
        for j in grp:
            m[comps[j][0], comps[j][1]] = True
        # her satırda parçaların arasındaki zemin renkli pikselleri de kat
        y0 = min(comps[j][3] for j in grp)
        y1 = max(comps[j][5] for j in grp)
        for yy in range(y0, y1 + 1):
            row = np.flatnonzero(m[yy])
            if len(row) >= 2:
                seg = slice(row[0], row[-1] + 1)
                m[yy, seg] |= near[yy, seg]
        ys, xs = np.nonzero(m)
        r = test(ys, xs)
        if r is not None:
            out.append(r)
            done.update(grp)
    for j, (ys, xs, *_rest) in enumerate(comps):
        if j in done:
            continue
        r = test(ys, xs)
        if r is not None:
            out.append(r)
    return out


# ---------------------------------------------------------------- ana işlem
@dataclass
class Options:
    detail: float = 1.0          # 1 = normal; büyüdükçe daha çok ayrıntı
    thin_px: float = 2.6         # bu kalınlığa kadar çizgi say (özgün piksel)
    text_boxes: list | None = None   # [{"box": (x0,y0,x1,y1)}] özgün pikselde: bu pikseller şekle çevrilmez
    text_mask: np.ndarray | None = None  # özgün boyutta yazı pikselleri (doğrulanmış yazılar): şekle çevrilmez
    glyphs: bool = True          # harfleri dolgulu şekil olarak çiz
    gradients: bool = True       # renk geçişli bölgeleri degrade dolgu yap
    cizim: bool = True           # izlenen şekilleri çizim nesnelerine çevir (dikdörtgen, çizgi, kontur)
    small_marks: bool = False    # küçük renkli işaretlerin (harita üstü nokta, harf) rengini ayrıca ara
    yazisiz: bool = False        # yazıları hiç çizme (yalnız şekiller); yazı altındaki çizimler yine çizilir
    zemin: bool = True           # zemin beyaz değilse zemin rengini de dikdörtgen olarak çiz (harita
                                 # modunda kapalı: altta tanınan haritanın kendisi durur)


def _alt_piksel_yazi(rgb: np.ndarray) -> np.ndarray:
    """Ekran görüntüsündeki ClearType yazı: harf saplarının bir yanı turuncu, öbür yanı mavi
    saçaklıdır (her renk kanalı ayrı alt piksel). Bu saçaklar ayrı renkli çizgi kırıntılarına
    dönüşür. Saçaklı yazı bölgelerinde üç pikselin ortalaması alınarak sıradan (gri) kenar
    yumuşatmasına çevrilir; şekillerin kenarlarına dokunulmaz."""
    if rgb.ndim != 3 or rgb.shape[1] < 8:
        return rgb
    a = rgb.astype(np.float32)
    rb = a[..., 0] - a[..., 2]
    base = ndimage.median_filter(rb, size=(1, 7), mode="nearest")
    d = rb - base
    L = a.mean(axis=2)
    Lmax = ndimage.maximum_filter(L, size=(1, 5), mode="nearest")
    dark = (Lmax - L) > 40
    # saçak bir ya da (büyütülmüş ekran görüntüsünde) iki piksel yanda
    best = None
    for s_ in (1, 2):
        if d.shape[1] <= 2 * s_ + 1:
            continue
        c = dark[:, s_:-s_]
        rgb_o = (d[:, :-2 * s_] > 25) & (d[:, 2 * s_:] < -25) & c
        bgr_o = (d[:, :-2 * s_] < -25) & (d[:, 2 * s_:] > 25) & c
        n1, n2 = int(rgb_o.sum()), int(bgr_o.sum())
        if max(n1, n2) < 40 or max(n1, n2) < 3 * min(n1, n2):
            continue
        if best is None or max(n1, n2) > best[0]:
            best = (max(n1, n2), s_, rgb_o if n1 > n2 else bgr_o)
    if best is None:
        return rgb
    _n, s_, mm = best
    m = np.zeros(L.shape, bool)
    m[:, s_:-s_] = mm
    reg = cv2.dilate(m.astype(np.uint8), np.ones((5, 4 * s_ + 5), np.uint8)) > 0
    # açıklık (koyuluk) pikselin kendisinden; renk tonu birkaç pikselin ortalamasından: saçağın
    # turuncusu ile mavisi birbirini götürür, harf incelip açılmaz
    lab0 = cv2.cvtColor(a / 255.0, cv2.COLOR_RGB2Lab)
    box = cv2.blur(a, (2 * s_ + 1, 1), borderType=cv2.BORDER_REPLICATE)
    lab1 = cv2.cvtColor(box / 255.0, cv2.COLOR_RGB2Lab)
    lab1[..., 0] = lab0[..., 0]
    rgb1 = cv2.cvtColor(lab1.astype(np.float32), cv2.COLOR_Lab2RGB) * 255.0
    out = np.where(reg[..., None], rgb1, a)
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def vectorize(rgb: np.ndarray, opts: Options | None = None) -> Scene:
    opts = opts or Options()
    rgb = _alt_piksel_yazi(np.ascontiguousarray(rgb[..., :3]))
    H, W = rgb.shape[:2]
    side = max(H, W)
    # Büyütülmüş (ör. Retina ekran görüntüsü) görselleri normal ölçeğe, çok büyükleri 2200 piksele küçült
    shrink = 1.0
    th = stroke_width(rgb)
    if th > 2.6:
        # büyütülmüş (Retina) görseli normal ölçeğe getir; fazla küçültme yazıyı ve ince
        # çizgileri bozar (en çok yarıya)
        shrink = max(0.5, 2.2 / th)
    if side * shrink > 2200:
        shrink = 2200 / side
    if shrink < 0.95:
        rgb = cv2.resize(rgb, (int(round(W * shrink)), int(round(H * shrink))), interpolation=cv2.INTER_AREA)
    else:
        shrink = 1.0
    h, w = rgb.shape[:2]
    f = 3 if max(h, w) <= 1200 else 2
    lab = _to_lab(rgb)
    grads = find_gradients(lab, rgb) if opts.gradients else []
    gmask = np.zeros((h, w), bool)
    for m, _ in grads:
        gmask |= m
    pal = build_palette(lab, 1.0, gmask if grads else None, small_marks=opts.small_marks)
    colors = [_lab_to_rgb(p) for p in pal]
    cov, labels = unmix(rgb, np.array(colors, dtype=np.float32))
    K = len(pal)
    gk = -1
    if grads:
        # renk geçişli bölgeler ayrı bir "renk" olur: başka renkler oraya taşmaz, ayrıca çizilir
        cov = np.concatenate([cov * ~gmask[None], gmask[None].astype(np.float32)], axis=0)
        labels = labels.copy()
        labels[gmask] = K
        colors.append(tuple(int(v) for v in rgb[gmask].mean(axis=0)))
        pal = np.vstack([pal, lab[gmask].mean(axis=0)])
        gk = K
        K += 1
    # arka plan: en çok yer kaplayan renk (görselin kenarında çerçeve çizgisi olabilir)
    counts = np.bincount(labels.ravel(), minlength=K)
    border = np.concatenate([labels[3:-3, 3], labels[3:-3, -4], labels[3, 3:-3], labels[-4, 3:-3]]) if min(h, w) > 10 else labels.ravel()
    bcount = np.bincount(border, minlength=K)
    bg = int(counts.argmax())
    if bcount.argmax() != bg and bcount.max() > 0.8 * len(border) and counts[bcount.argmax()] > 0.5 * counts[bg]:
        bg = int(bcount.argmax())
    # zemin kâğıttır (beyaz): en çok yer kaplayan renk bir harita bloğu ya da kutu olabilir
    # (sokak krokisinde turuncu bloklar). Beyaz yeterince varsa zemin odur.
    def _whiteish(k):
        return k != gk and pal[k][0] >= 93 and math.hypot(pal[k][1], pal[k][2]) <= 6
    if opts.zemin and not _whiteish(bg):
        wk = [k for k in range(K) if _whiteish(k) and counts[k] >= 0.01 * h * w]
        if wk:
            bg = max(wk, key=lambda k: counts[k])
    scene = Scene(w, h, background=colors[bg])
    bg_rect = None
    if opts.zemin and not (pal[bg][0] >= 93 and math.hypot(pal[bg][1], pal[bg][2]) <= 6) and bg != gk:
        # beyaz yoksa zemin rengi de çizilir (renkli kâğıt / tam sayfa harita)
        bg_rect = Element("fill", colors[bg], prim={"type": "rect", "x": -0.5, "y": -0.5, "w": float(w), "h": float(h)},
                          area=float(w * h), bbox=(-0.5, -0.5, w - 0.5, h - 0.5), layer="alt")
    tol = 0.3 / max(opts.detail, 0.3)

    # --- yazı kutuları (dışarıdan verildiyse): kutunun içinde kalan mürekkep parçaları yazıdır
    present = cov >= 0.3
    text_mask = np.zeros((h, w), bool)
    if opts.text_boxes:
        for tb in opts.text_boxes:
            x0, y0, x1, y1 = [v * shrink for v in tb["box"]]
            bh = max(1.0, y1 - y0)
            m = max(1.0, 0.2 * bh)
            M = max(3.0, 0.9 * bh)
            a0, b0 = max(0, int(math.floor(x0 - M))), max(0, int(math.floor(y0 - M)))
            a1, b1 = min(w, int(math.ceil(x1 + M))), min(h, int(math.ceil(y1 + M)))
            if a1 - a0 < 3 or b1 - b0 < 3:
                continue
            # kutunun çevresindeki zemin rengi (beyaz sayfa ya da renkli bir alan)
            ia0, ib0 = max(0, int(math.floor(x0 - m))), max(0, int(math.floor(y0 - m)))
            ia1, ib1 = min(w, int(math.ceil(x1 + m))), min(h, int(math.ceil(y1 + m)))
            sub = labels[ib0:ib1, ia0:ia1]
            ring = np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]])
            under = int(np.bincount(ring, minlength=K).argmax())
            box_m = np.zeros((b1 - b0, a1 - a0), bool)
            box_m[ib0 - b0:ib1 - b0, ia0 - a0:ia1 - a0] = True
            bw, bhh = b1 - b0, a1 - a0
            # her renk ayrı: yazıya değen başka renkli çizgi (taban çizgisi, kıyı) yazıyla birleşmesin
            for c in range(K):
                if c == under or cov[c, ib0:ib1, ia0:ia1].sum() < 2.0:
                    continue
                inkw = (cov[c, b0:b1, a0:a1] >= 0.15).astype(np.uint8)
                n_i, cc_i, st_i, _ = cv2.connectedComponentsWithStats(inkw, connectivity=8)
                inside = np.bincount(cc_i[box_m].ravel(), minlength=n_i)
                for i in range(1, n_i):
                    x, y, ww, hh, area = st_i[i]
                    touches = x == 0 or y == 0 or x + ww >= bhh or y + hh >= bw
                    if inside[i] >= 0.6 * area and not (touches and inside[i] < area):
                        text_mask[b0:b1, a0:a1] |= cc_i == i
    if opts.text_mask is not None and opts.text_mask.any():
        tmk = opts.text_mask
        if tmk.shape[:2] != (h, w):
            tmk = cv2.resize(tmk.astype(np.float32), (w, h), interpolation=cv2.INTER_AREA) > 0.25
        # harflerin kenar yumuşatma pikselleri de gitsin
        text_mask |= cv2.dilate(tmk.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    # --- soluk eksen / ızgara çizgileri (paletin karşılamadığı açık gri çizgiler)
    soluk, soluk_m = _soluk_cizgiler(lab, rgb, pal, bg, max(24, int(0.06 * max(h, w))),
                                     max(80, int(0.2 * max(h, w))))
    # --- yazılar: harf çekirdekleri satırlara toplanır; satırdaki bütün mürekkep (ara renkler
    # dahil) şekillerden ayrılır. Tanınan (OCR) yazının pikselleri yazı olarak yerleşir; kalanlar
    # tek renkli harf şekli olarak çizilir (yazısız çizimde hiç çizilmez).
    ink_lines = []
    if opts.glyphs:
        ink, ink_lines = _yazi_murekkebi(lab, labels, present, pal, bg, gk,
                                         core_extra=text_mask if text_mask.any() else None,
                                         block=soluk_m if soluk else None)
    else:
        ink = np.zeros((h, w), bool)
    glyph = ink & ~text_mask
    if text_mask.any() and glyph.any():
        # tanınan yazıyla aynı parçaya ait harf kalıntıları da yazıdır
        n_g, cc_g = cv2.connectedComponents((glyph | text_mask).astype(np.uint8), connectivity=8)
        hit = np.zeros(n_g, bool)
        hit[np.unique(cc_g[text_mask])] = True
        hit[0] = False
        extra = hit[cc_g] & glyph
        text_mask |= extra
        glyph &= ~extra
    if soluk:
        # soluk çizgi pikselleri şekle çevrilmez (yazı gibi gizlenir); harflere dokunulmaz
        text_mask |= soluk_m
        glyph &= ~soluk_m

    # harflerin çevresindeki ara renkli pikseller ve harf içindeki boşluklar (a, e, o) şekil olmaz
    halo = (cv2.dilate(glyph.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) if glyph.any() else glyph
    for (a0, b0, a1, b1), _u, im in ink_lines:
        # harflerin çevresinde alttaki renkteki her şey (harf içleri, harf araları) dolgunun parçası;
        # eğik yazının kutusu geniştir, yalnız harflerin yakını
        yak = cv2.dilate(im.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))) > 0
        halo[b0:b1, a0:a1] |= ((labels[b0:b1, a0:a1] == _u) & yak) | (ndimage.binary_fill_holes(im) & ~im)
    # yazı satırlarının alttaki rengi: satırın hemen çevresinde o rengin dar kalan şeritleri
    # (yazı ile kutu kenarı arasındaki ince boşluk) çizgi değil, dolgunun parçasıdır
    yazi_cevre = {}
    for (a0, b0, a1, b1), _u, im in ink_lines:
        if _u == bg:
            continue
        yc = yazi_cevre.setdefault(_u, np.zeros((h, w), bool))
        yc[max(0, b0 - 3):b1 + 3, max(0, a0 - 3):a1 + 3] = True
    # --- her rengin ince (çizgi) ve kalın (dolgu) kısmı
    core_r = opts.thin_px / 2 + 0.45
    thin_by = {}
    thick_by = {}
    thin_all = np.zeros((h, w), bool)
    fringe_all = np.zeros((h, w), bool)
    for k in range(K):
        if k == bg or k == gk:
            continue
        m = (labels == k) & ~text_mask & ~glyph & ~halo
        if m.sum() < 1:
            continue
        mu = m.astype(np.uint8)
        dt = cv2.distanceTransform(np.pad(mu, 1), cv2.DIST_L2, 5)[1:-1, 1:-1]
        core = dt >= core_r
        if core.any():
            # ince bir çizginin üstünde, bulanıklıktan bir piksel kalınlaşmış birkaç nokta kalın
            # sayılmaz (çizgi orada kopup küçük bir leke olmasın): parçanın çok küçük bir kısmıysa
            # ve sınırı ancak geçiyorsa
            nl, ml = cv2.connectedComponents(mu, connectivity=8)
            ccnt = np.bincount(ml[core], minlength=nl)
            acnt = np.bincount(ml.ravel(), minlength=nl)
            weak = (ccnt < 0.05 * acnt)
            weak[0] = False
            if weak[ml[core]].any():
                nc, cl, cst, _ = cv2.connectedComponentsWithStats(core.astype(np.uint8), connectivity=8)
                cmax = np.zeros(nc)
                np.maximum.at(cmax, cl[core], dt[core])
                # çizginin olağan yarı kalınlığı (iskelet boyunca): ondan belirgin kalın yer (grafikteki
                # veri noktası) gerçek kalınlıktır, bulanıklık değil
                sk_ = skeletonize(m)
                ssum = np.bincount(ml[sk_], weights=dt[sk_], minlength=nl)
                scnt = np.bincount(ml[sk_], minlength=nl)
                half = ssum / np.maximum(scnt, 1)
                cl_ml = np.zeros(nc, np.int64)
                cl_ml[cl[core]] = ml[core]
                # uzunlamasına kalın çekirdek (bulanık çizgi boyunca) da çizgidir; yuvarlak çekirdek
                # (veri noktası) değil
                c_lo = np.minimum(cst[:, cv2.CC_STAT_WIDTH], cst[:, cv2.CC_STAT_HEIGHT])
                c_hi = np.maximum(cst[:, cv2.CC_STAT_WIDTH], cst[:, cv2.CC_STAT_HEIGHT])
                uzun = (c_hi >= 6) & (c_hi >= 4 * np.maximum(c_lo, 1))
                # en kalın yeri üç pikseli geçmeyen çekirdek de bulanıklıktır
                drop = (cmax < core_r + 0.55) & ((cmax <= 1.45 * np.maximum(half[cl_ml], 0.5)) | uzun
                                                 | (cmax <= 2.05))
                drop[0] = False
                core &= ~(drop[cl] & weak[ml])
            # merdiven basamağı: hafif eğimli çizgi basamak yaptığı yerde bir piksel kalınlaşır; uzun
            # çizginin ortasındaki tek sıralık 1-3 piksellik çekirdek kalınlık değildir (çizgi orada
            # kopup kesikli görünmesin). Küçük veri noktasının çekirdeği en az iki sıradır.
            nc2, cl2, cst2, _ = cv2.connectedComponentsWithStats(core.astype(np.uint8), connectivity=8)
            if nc2 > 1:
                cmax2 = np.zeros(nc2)
                np.maximum.at(cmax2, cl2[core], dt[core])
                own2 = np.zeros(nc2, np.int64)
                own2[cl2[core]] = ml[core]
                lo2 = np.minimum(cst2[:, cv2.CC_STAT_WIDTH], cst2[:, cv2.CC_STAT_HEIGHT])
                basamak = (lo2 == 1) & (cst2[:, cv2.CC_STAT_AREA] <= 3) & (cmax2 <= 2.05) \
                    & (cmax2 < core_r + 0.55) & (acnt[own2] >= 40)
                basamak[0] = False
                if basamak.any():
                    core &= ~basamak[cl2]
        if core.any():
            rr = int(math.ceil(core_r))
            ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rr + 1, 2 * rr + 1))
            thick = (cv2.dilate(core.astype(np.uint8), ker) > 0) & m
        else:
            thick = np.zeros_like(m)
        # ince kısım: rengin %30'dan fazla kapladığı (soluk kenarlı çizgiler kopmasın), kalın olmayan pikseller
        thick_g = cv2.dilate(thick.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        thin = present[k] & ~thick_g & ~text_mask & ~glyph & ~halo
        if k in yazi_cevre:
            thin &= ~(yazi_cevre[k] & (labels == k))
        # kalın şeklin kenarındaki 1-2 piksellik pürüzleri çizgi sayma
        if thin.any() and thick.any():
            n, cc, stats, _ = cv2.connectedComponentsWithStats(thin.astype(np.uint8), connectivity=8)
            near_thick = cv2.dilate(thick_g.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
            touch = np.zeros(n, bool)
            touch[np.unique(cc[near_thick & thin])] = True
            big = np.maximum(stats[:, cv2.CC_STAT_WIDTH], stats[:, cv2.CC_STAT_HEIGHT])
            drop = touch & (big <= 3)
            # ağırlıkla dolgu olan açık renk (krem zemin gibi): kalın kısma değen ince şeritler de
            # dolgunun parçasıdır, ayrı çizgi olmaz (koyu renklerde bu ince kısım gerçek çizgidir)
            if thick.sum() >= 3 * max(1, thin.sum()) and pal[k][0] >= 55:
                drop = touch.copy()
            drop[0] = False
            if drop.any():
                thin &= ~drop[cc]
        thin_by[k] = thin
        thick_by[k] = thick_g
        thin_all |= thin
        # çizginin soluk kenarı (aynı renge sayılmış ama çizgi sayılmayan pikseller): dolguyu yarmasın
        if thin.any():
            fringe_all |= (cv2.dilate(thin.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & m & ~thin & ~thick_g

    # --- dolgu etiketleri: çizgi, yazı ve harf piksellerinin altını çevredeki renkle doldur
    hide = thin_all | fringe_all | text_mask | glyph | halo
    fill_lab = labels.copy()
    iy = ix = None
    # yazı kutusunda alttaki renkteki pikseller (harf araları) çevrelerini doldurmaya kaynak olur:
    # yazının hemen altındaki kenar çizgisi yazının durduğu renkle de paylaşılsın
    src_hide = hide.copy()
    for (a0, b0, a1, b1), _u, _im in ink_lines:
        src_hide[b0:b1, a0:a1] &= ~((labels[b0:b1, a0:a1] == _u) & ~_im)
    if src_hide.any() and not src_hide.all():
        _, (iy, ix) = ndimage.distance_transform_edt(src_hide, return_indices=True)
        fill_lab[hide] = labels[iy[hide], ix[hide]]

    def _yazi_alti():
        # yazının altı, yazının üstünde durduğu renkle dolar (yandaki başka renkle değil)
        for (a0, b0, a1, b1), _u, _im in ink_lines:
            sub = fill_lab[b0:b1, a0:a1]
            yak = cv2.dilate(_im.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))) > 0
            sub[hide[b0:b1, a0:a1] & (labels[b0:b1, a0:a1] != _u) & ~(thin_all[b0:b1, a0:a1]) & yak] = _u
            sub[(labels[b0:b1, a0:a1] == _u)] = _u
            sub[_im] = _u
    _yazi_alti()
    near_hide = cv2.dilate(hide.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    # çizginin açık renkli hâlesi zemin rengine düşer ve dolguyu yarar: çizgi boyunca kalan dar
    # zemin şeritleri, çevresi (çizgi dışında) tümüyle tek bir dolgu ise o dolguya katılır.
    # Sütun aralığı gibi gerçek boşluklar bir uçta açık zemine değdiği için katılmaz.
    if thin_all.any():
        band = (cv2.dilate(thin_all.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & (fill_lab == bg) & ~hide
        if band.any():
            nb, ccb, stb, _ = cv2.connectedComponentsWithStats(band.astype(np.uint8), connectivity=8)
            changed = False
            for i in range(1, nb):
                x, y, ww, hh, _a = stb[i]
                a0, b0, a1, b1 = max(0, x - 1), max(0, y - 1), min(w, x + ww + 1), min(h, y + hh + 1)
                comp = ccb[b0:b1, a0:a1] == i
                ring = (cv2.dilate(comp.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & ~comp & ~hide[b0:b1, a0:a1]
                labs = fill_lab[b0:b1, a0:a1][ring]
                if len(labs) < 4:
                    continue
                cnt = np.bincount(labs, minlength=K + 1)
                if cnt[bg] > 0.15 * len(labs):
                    continue
                cnt[bg] = 0
                k2 = int(cnt.argmax())
                if k2 != gk and cnt[k2] >= 0.6 * len(labs):
                    # çizginin öbür yanı açık zeminse çizgi dolgunun sınırıdır: aradaki beyaz şerit
                    # (sütun ile eksen arasındaki boşluk) gerçek boşluktur
                    q = 5
                    c0, d0, c1, d1 = max(0, x - q), max(0, y - q), min(w, x + ww + q), min(h, y + hh + q)
                    cq = ccb[d0:d1, c0:c1] == i
                    # şeridin uzun kenarı boyunca komşu çizgi (uçlardaki dik çentikler değil)
                    kq = np.ones((1, 3), np.uint8) if hh >= ww else np.ones((3, 1), np.uint8)
                    cqd = cv2.dilate(cq.astype(np.uint8), kq) > 0
                    Lq = cqd & thin_all[d0:d1, c0:c1]
                    if Lq.any():
                        lq_l = labels[d0:d1, c0:c1]
                        Lq &= lq_l == int(np.bincount(lq_l[Lq]).argmax())
                        # çizginin şeride göre öbür yanı: çizgiye şeritten daha yakın pikseller
                        dL = cv2.distanceTransform((~Lq).astype(np.uint8), cv2.DIST_L2, 3)
                        dC = cv2.distanceTransform((~cq).astype(np.uint8), cv2.DIST_L2, 3)
                        far = (dL <= 5) & (dC > dL + 0.5) & ~Lq & ~band[d0:d1, c0:c1] & ~hide[d0:d1, c0:c1]
                        fl = fill_lab[d0:d1, c0:c1][far]
                        if len(fl) and np.count_nonzero(fl == bg) > np.count_nonzero(fl == k2):
                            continue
                    sub = fill_lab[b0:b1, a0:a1]
                    sub[comp] = k2
                    changed = True
            if changed and iy is not None:
                # çizgi altını güncellenen komşulardan yeniden doldur
                fill_lab[hide] = fill_lab[iy[hide], ix[hide]]
                _yazi_alti()

    elements = []
    # --- renk geçişli bölgeler
    for m, g in grads:
        conts = _contours_of(_up(cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.6), f), f, 0, 0, 2.0)
        el = _fill_element(conts, tuple(int(v) for v in g["stops"][len(g["stops"]) // 2][1]), tol, shapes=False)
        if el:
            el.grad = g
            el.layer = "alt"
            elements.append(el)
    # --- içi boş kutuların çerçeveleri (dolgu ve kontur tek nesne)
    if opts.cizim:
        for el, band, inner in _cerceveler(lab, rgb, pal, bg, glyph | text_mask, h, w):
            if not opts.zemin and el.grad is None and _de_rgb(el.color, colors[bg]) < 6:
                # harita modunda içi zemin olan çerçeve yalnız çizgidir (altındaki harita görünsün)
                el = Element("stroke", el.stroke, prim=el.prim, width=el.stroke_width, bbox=el.bbox,
                             join="miter", layer="cerceve")
            elements.append(el)
            ins = fill_lab[inner]
            kin = int(np.bincount(ins).argmax()) if ins.size else bg
            # yalnız çerçeve çizgisi ve iç dolgu rengi silinir: içindeki başka şekiller (nokta, simge) kalır
            fill_lab[band | (inner & ((fill_lab == kin) | (fill_lab == bg)))] = bg
            if kin != bg and kin != gk and el.prim is not None:
                # kutunun içindeki kendi dolgu rengi (kenara sıkışmış ince şeritler dahil) bu kutudur
                gp = sekil.grow(el.prim, (el.stroke_width or 0.0) / 2 + 1.0)
                reg = np.zeros((h, w), np.uint8)
                cv2.fillPoly(reg, [np.round((sekil.prim_points(gp) + 0.5) * 16).astype(np.int32)], 1, shift=4)
                reg = reg > 0
                fill_lab[reg & (fill_lab == kin)] = bg
                if kin in thin_by:
                    thin_by[kin] &= ~reg
            for kk in thin_by:
                if el.stroke is not None and _de_rgb(colors[kk], el.stroke) < 12:
                    thin_by[kk] &= ~band
                else:
                    _banttan_sil(thin_by[kk], band)
    # --- dolgular: büyükten küçüğe (panel önce kendi çerçevesini alsın, üstündekiler sonra)
    # görselin kenarına ulaşan açık zemin (kapalı kutu içleri değil)
    _nz, _cz = cv2.connectedComponents((labels == bg).astype(np.uint8), connectivity=4)
    _kenar = np.unique(np.concatenate([_cz[0], _cz[-1], _cz[:, 0], _cz[:, -1]]))
    bg_ana = np.isin(_cz, _kenar[_kenar > 0])
    per_k = {}
    comp_list = []
    for k in range(K):
        if k == bg or k == gk:
            continue
        m = fill_lab == k
        if not m.any():
            continue
        filled = ndimage.binary_fill_holes(m)
        holes = filled & ~m
        hole_fill = np.zeros_like(m)
        if holes.any():
            hl, hn = ndimage.label(holes)
            bgc = ndimage.sum(fill_lab == bg, hl, index=np.arange(1, hn + 1))
            keep_hole = np.zeros(hn + 1, bool)
            keep_hole[1:] = bgc > 0
            hole_fill = holes & ~keep_hole[hl]
            m = m | hole_fill
        # kaplama: normal yerlerde rengin payı, çizgi altı ve doldurulan deliklerde tam
        fc = np.where(near_hide | hole_fill, m.astype(np.float32), cov[k])
        n, cc, stats, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
        per_k[k] = (fc, cc)
        for i in range(1, n):
            x, y, ww, hh, area = (int(v) for v in stats[i])
            # çok küçük, soluk kırıntılar (kenar yumuşatmasından kalan) çizilmez
            if area < 3 or (area < 6 and cov[k, y:y + hh, x:x + ww][cc[y:y + hh, x:x + ww] == i].mean() < 0.75):
                continue
            comp_list.append((ww * hh, k, i, x, y, ww, hh, area))
    comp_list.sort(key=lambda t: (-t[0], t[1], t[2]))
    kontur_bandi = np.zeros((h, w), bool)
    # konturu çizilmiş şekillerin kenar bandı ve o konturun rengi: bu bantta kalan aynı renkli küçük
    # parçalar (kontura değen çizgilerin kalın birleşim yerleri) konturun kendisidir
    tuket = np.full((h, w), -1, np.int16)
    for _bb, k, i, x, y, ww, hh, area in comp_list:
        fc, cc = per_k[k]
        p = 2
        a0, b0, a1, b1 = max(0, x - p), max(0, y - p), min(w, x + ww + p), min(h, y + hh + p)
        comp = cc[b0:b1, a0:a1] == i
        if area <= 150 and float((tuket[b0:b1, a0:a1][comp] == k).mean()) >= 0.8:
            continue
        # içindeki zemin renkli boşluklar: harf gibi küçükler (kutudaki beyaz yazı) dolgunun
        # parçası sayılır, harfler üstte ayrıca çizilir; büyük pencereler ayrı beyaz şekil olur
        F = ndimage.binary_fill_holes(comp)
        win = F & ~comp
        glyph_win = np.zeros_like(comp)
        big_win = []
        if win.any():
            wl, wn = ndimage.label(win)
            fa = float(F.sum())
            for j in range(1, wn + 1):
                wm = wl == j
                ys_, xs_ = np.nonzero(wm)
                if wm.sum() <= 0.06 * fa and (np.ptp(ys_) + 1) <= max(6, 0.6 * hh):
                    glyph_win |= wm
                elif wm.sum() >= 12:
                    big_win.append(wm)
            if big_win and not opts.zemin:
                # harita modunda zemin altta duran haritadır: büyük boşluklar delik kalır
                for wm in big_win:
                    F = F & ~wm
                win = F & ~comp
                big_win = []
        fcc = fc[b0:b1, a0:a1]
        reach = cv2.dilate(F.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        c = np.where(reach, fcc, 0.0)
        if win.any():
            c = np.where((cv2.dilate(win.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & F, 1.0, c)
        prim = None
        sivri = False
        if opts.cizim and area <= 150 and k in thin_by:
            # çizgi üstündeki yuvarlak işaret (grafikteki veri noktası): çizgi uçları değdiği için
            # şekli düzgün değildir; içine sığan en büyük daire
            touch_t = (cv2.dilate(F.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & thin_by[k][b0:b1, a0:a1]
            # işaret dolu ve yuvarlaktır (küçük kutunun kenar halkası değil)
            # (iki yanında çizgi kökü kalabilir: içine sığan daire şeklin yarısından çoğunu kaplar,
            # kutu köşeleri boştur)
            yuvarlak = float(comp.sum()) >= 0.8 * float(F.sum())
            if yuvarlak:
                dmax = float(cv2.distanceTransform(np.pad(F.astype(np.uint8), 1), cv2.DIST_L2, 5).max())
                yuvarlak = math.pi * (dmax + 0.5) ** 2 >= 0.5 * float(F.sum())
            if yuvarlak:
                fy, fx = np.nonzero(F)
                ky0, ky1, kx0, kx1 = fy.min(), fy.max(), fx.min(), fx.max()
                dolu = sum(1 for yy_, xx_ in ((ky0, kx0), (ky0, kx1), (ky1, kx0), (ky1, kx1))
                           if float(c[yy_, xx_]) >= 0.6)
                yuvarlak = dolu < 3
            if yuvarlak and _ucgen_mi(c):
                yuvarlak = False        # okun ucu (üçgen) daire değildir
            if yuvarlak:
                # lekenin çekirdeği (kenardan uzak pikseller) yuvarlak bir öbek olmalı: kalın çizginin
                # parçasında çekirdek uzun bir şerittir (ince çizgi köklerinin çekirdeği yoktur)
                dtc = cv2.distanceTransform(np.pad(F.astype(np.uint8), 1), cv2.DIST_L2, 5)[1:-1, 1:-1]
                oy_, ox_ = np.nonzero(dtc >= max(1.0, 0.6 * float(dtc.max())))
                if len(oy_) >= 2:
                    ev_ = np.linalg.eigvalsh(np.cov(np.vstack([ox_, oy_]).astype(np.float64)))
                    yuvarlak = math.sqrt(max(ev_[1], 1e-6) / max(ev_[0], 0.08)) <= 2.6
            if yuvarlak and touch_t.any():
                # çizgi yalnız bir yandan değiyorsa öbür yan: okun ucu sivridir, işaretin ucu yuvarlak
                ty_, tx_ = np.nonzero(touch_t)
                fy_, fx_ = np.nonzero(F)
                mx_, my_ = float(fx_.mean()), float(fy_.mean())
                tv = np.stack([tx_ - mx_, ty_ - my_], axis=1).astype(np.float64)
                u_ = tv.mean(axis=0)
                tek_yan = float(np.hypot(*u_)) >= 0.6 * float(np.hypot(tv[:, 0], tv[:, 1]).mean())
                if tek_yan:
                    u_ = u_ / max(float(np.hypot(*u_)), 1e-9)
                    pr_ = -((fx_ - mx_) * u_[0] + (fy_ - my_) * u_[1])
                    dik_ = (fx_ - mx_) * (-u_[1]) + (fy_ - my_) * u_[0]
                    uc_ = pr_ >= pr_.max() - 2.0
                    gen_ = float(np.ptp(dik_[uc_])) + 1.0 if uc_.any() else 0.0
                    dm_ = float(cv2.distanceTransform(np.pad(F.astype(np.uint8), 1), cv2.DIST_L2, 5).max())
                    if gen_ <= 0.45 * 2 * (dm_ + 0.5):
                        yuvarlak = False
                        sivri = True
            if touch_t.any() and yuvarlak:
                dtF = cv2.distanceTransform(np.pad(F.astype(np.uint8), 1), cv2.DIST_L2, 5)[1:-1, 1:-1]
                dm = float(dtF.max())
                r_ = dm + 0.5
                if r_ >= 1.8 and float(F.sum()) <= 2.6 * math.pi * r_ * r_:
                    yy_, xx_ = np.nonzero(dtF >= dm - 0.35)
                    prim = {"type": "circle", "cx": float(xx_.mean() + a0), "cy": float(yy_.mean() + b0), "r": r_}
        if prim is None:
            # okun ucu: yuvarlak şekil (elips) oturtulmaz
            kinds_ = ("rect", "poly") if sivri else ("rect", "rrect", "ellipse", "poly")
            prim = sekil.uydur(c, a0, b0, kinds=kinds_) if area >= 30 and opts.cizim else None
        if prim is None and opts.cizim and 6 <= area < 30 and not sivri:
            prim = _kucuk_daire(c, a0, b0)
        U = F
        ayri_kontur = False
        if opts.cizim and area >= 60 and _karmasik(prim) > 1:
            # üstüne başka renkte şekil binmiş (köşedeki kare, kutudaki işaret, panelin
            # üstündeki adalar): onlarla birlikte temiz şekil oluyorsa alttaki tam şekildir,
            # üsttekiler (daha küçük oldukları için) zaten üstte çizilir
            ob = _ortulu_birlesim(F, c, a0, b0, x, y, ww, hh, k, fill_lab, cov, bg)
            if ob is not None:
                cu, occ = ob
                pu = sekil.uydur(cu, a0, b0)
                if pu is not None and _karmasik(pu) < _karmasik(prim):
                    prim, c = pu, cu
                    U = F | occ
                    # üsttekiler kenara değiyorsa kenar çizgisi onların da üstünde, ayrı çizilir
                    Uu = U.astype(np.uint8)
                    eU = (Uu > 0) & ~(cv2.erode(np.pad(Uu, 1), np.ones((3, 3), np.uint8))[1:-1, 1:-1] > 0)
                    ayri_kontur = float((eU & occ).sum()) > 0.35 * float(eU.sum())
        if opts.cizim and prim is None and area >= 40 and not win.any() and k in thin_by and not sivri:
            # ince veri çizgisine bağlı birkaç işaret ve aralarındaki çizgi tek parça kalmış: işaretler
            # daire, kalan ince kısım çizgi adımına (aynı renkteki çizgiyle birlikte çizilsin)
            yak = (cv2.dilate(F.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & thin_by[k][b0:b1, a0:a1]
            ay = _isaret_ayir(F, c) if yak.any() else None
            if ay is not None:
                dots, rest, disks = ay
                for ix, iy, r in dots:
                    cx, cy = ix + a0, iy + b0
                    elements.append(Element("fill", colors[k], prim={"type": "circle", "cx": float(cx), "cy": float(cy), "r": r},
                                            area=math.pi * r * r, bbox=(cx - r, cy - r, cx + r, cy + r)))
                thin_by[k][b0:b1, a0:a1] |= rest
                thick_by[k][b0:b1, a0:a1] &= ~(cv2.dilate(rest.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
                thick_by[k][b0:b1, a0:a1] |= disks
                continue
        if opts.cizim and prim is None and area >= 40 and not win.any():
            kc = _kalin_cizgi(F, a0, b0, colors[k])
            if kc:
                elements.extend(kc)
                continue
        if opts.cizim and prim is None and area >= 300:
            # iki elipsin birleşimi (Venn şeması): iki dolgu elips, konturları üstte tam elips
            ie = sekil.iki_elips(c, a0, b0)
            if ie is not None:
                Ur = cv2.dilate(F.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
                Ui = cv2.dilate(F.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
                outl = fill_lab[b0:b1, a0:a1][Ur & ~Ui]
                outl = outl[outl != k]
                dis = int(np.bincount(outl).argmax()) if len(outl) else bg
                ol = _outline_of(F, a0, b0, k, thin_by, cov, bg, area, pal, lab, rgb, dis=dis,
                                 skip=kontur_bandi[b0:b1, a0:a1])
                bbs = []
                for pr in ie:
                    pp = sekil.prim_points(pr)
                    bb = (float(pp[:, 0].min()), float(pp[:, 1].min()), float(pp[:, 0].max()), float(pp[:, 1].max()))
                    bbs.append((pp, bb))
                    ef = Element("fill", colors[k], prim=pr, area=float(c.sum()) / 2, bbox=bb)
                    ef.temiz = True
                    elements.append(ef)
                if ol is not None:
                    oc, ow, ring, ocol = ol
                    band = np.zeros((h, w), np.uint8)
                    for pr, (pp, bb) in zip(ie, bbs):
                        elements.append(Element("stroke", ocol or colors[oc], prim=dict(pr), width=ow, bbox=bb,
                                                layer="cerceve"))
                        q = np.round(np.vstack([pp, pp[:1]]) * 16).astype(np.int32)
                        cv2.polylines(band, [q], False, 1, thickness=max(1, int(round(ow + 4))), shift=4)
                    band = band > 0
                    for kk in thin_by:
                        if kk == oc:
                            thin_by[kk] &= ~band
                        elif kk != k:
                            _banttan_sil(thin_by[kk], band)
                    tuket[band] = oc
                continue
        wa0, wb0, wa1, wb1 = a0, b0, a1, b1
        if (opts.cizim and area >= 60 and not ayri_kontur and U is F and prim is not None
                and prim["type"] in ("rect", "rrect")):
            # kutunun bir kenarı boyunca başka renkte şerit (başlık bandı): dış çizgi şeridin de
            # çevresinden geçiyor, aralarında çizgi yoksa kutu şeritle birlikte tek şekildir
            sb = _serit_birlesim(F, c, a0, b0, k, fill_lab, cov, bg, thin_all, kontur_bandi, prim)
            if sb is not None:
                prim, c, U, (wa0, wb0, wa1, wb1) = sb
        ol = None
        if area >= 30:
            # komşu renk (kenarın dışı): kontur rengi dolgu–komşu karışımından ayrılarak ölçülür
            Ur = cv2.dilate(U.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
            Ui = cv2.dilate(U.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
            outl = fill_lab[wb0:wb1, wa0:wa1][Ur & ~Ui]
            outl = outl[outl != k]
            dis = int(np.bincount(outl).argmax()) if len(outl) else bg
            ol = _outline_of(U, wa0, wb0, k, thin_by, cov, bg, area, pal, lab, rgb, dis=dis,
                             skip=kontur_bandi[wb0:wb1, wa0:wa1])
        if prim is not None:
            pp = sekil.prim_points(prim)
            el = Element("fill", colors[k], prim=prim, area=float(c.sum()),
                         bbox=(*map(float, pp.min(axis=0)), *map(float, pp.max(axis=0))))
        else:
            conts = _contours_of(_up(c, f), f, a0, b0, 0.8)
            el = _fill_element(conts, colors[k], max(tol, 0.5) if ol else tol)
        # harf boşlukları: zemin renginde harf şekli (yazısız çizimde ya da yazı tanındıysa yok)
        if glyph_win.any() and not opts.yazisiz:
            gr = cv2.dilate(glyph_win.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
            gc = np.where(gr, cov[bg, b0:b1, a0:a1], 0.0)
            gel = _fill_element(_contours_of(_up(gc, f), f, a0, b0, 0.3), colors[bg], tol * 0.7,
                                shapes=False, layer="harf")
            if gel:
                elements.append(gel)
        for wm in big_win:
            wr = cv2.dilate(wm.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
            wc = np.where(wr, cov[bg, b0:b1, a0:a1], 0.0)
            wprim = sekil.uydur(wc, a0, b0) if opts.cizim else None
            if wprim is not None:
                pp = sekil.prim_points(wprim)
                wel = Element("fill", colors[bg], prim=wprim, area=float(wc.sum()),
                              bbox=(*map(float, pp.min(axis=0)), *map(float, pp.max(axis=0))))
            else:
                wel = _fill_element(_contours_of(_up(wc, f), f, a0, b0, 0.8), colors[bg], tol)
            if wel:
                elements.append(wel)
        if el:
            if ol is not None:
                oc, ow, ring, ocol = ol
                if ayri_kontur and el.prim is not None:
                    # panelin çerçevesi: üstündeki şekillerin de üstünde, kendi başına kapalı çizgi
                    elements.append(Element("stroke", ocol or colors[oc], prim=dict(el.prim), width=ow,
                                            bbox=el.bbox, join="miter", layer="cerceve"))
                    el.panel = True
                else:
                    el.stroke, el.stroke_width = (ocol or colors[oc]), ow
                # kontur artık bu şeklin parçası: kenar bandındaki bütün ince pikseller (konturun
                # açık/koyu tonları dahil) ayrıca çizgi olmasın
                Fu = U.astype(np.uint8)
                edge_b = (Fu > 0) & ~(cv2.erode(Fu, np.ones((3, 3), np.uint8)) > 0)
                rb = int(math.ceil(ow / 2 + 1.5))
                band = cv2.dilate(edge_b.astype(np.uint8), cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE, (2 * rb + 1, 2 * rb + 1))) > 0
                # şeklin yanından geçip açık zemine uzanan düz çizgi (grafiğin ekseni, taban
                # çizgisi, kutuya gelen bağlantı) konturla birlikte silinmez
                gecen = _gecen_cizgi(thin_by[oc], band | ring, wa0, wb0, bg_ana)
                thin_by[oc][wb0:wb1, wa0:wa1] &= ~(ring & ~gecen)
                for kk in thin_by:
                    if kk == oc:
                        thin_by[kk][wb0:wb1, wa0:wa1] &= ~(band & ~gecen)
                    elif kk != k:
                        _banttan_sil(thin_by[kk], band, wa0, wb0)
                tuket[wb0:wb1, wa0:wa1][band] = oc
                if ayri_kontur and el.prim is not None:
                    # üstteki şekillerin bu çerçeveye değen kenarları ayrıca kontur aramaz
                    kontur_bandi[wb0:wb1, wa0:wa1] |= band
            elements.append(el)

    # --- harfler: her yazı satırında mürekkep, alttaki renge göre tek renkli şekil
    if glyph.any() and not opts.yazisiz:
        for (a0, b0, a1, b1), under, im in ink_lines:
            gm = im & glyph[b0:b1, a0:a1]
            if not gm.any():
                continue
            d = np.linalg.norm(lab[b0:b1, a0:a1] - pal[under], axis=2)
            dd = d[gm]
            top = dd >= np.percentile(dd, 60)
            ink_col = np.median(rgb[b0:b1, a0:a1][gm][top], axis=0)
            full = float(np.percentile(dd, 85))
            if full < 10:
                continue
            if _de_rgb(tuple(int(v) for v in ink_col), colors[bg]) < 8 and _de_rgb(colors[under], colors[bg]) < 12:
                continue        # zeminde zemin renginde "yazı" (silik doku): görünmez, üstündekileri örter
            reach = cv2.dilate(gm.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
            c = np.where(reach, np.clip(d / full, 0, 1), 0.0)
            conts = _contours_of(_up(c, f), f, a0, b0, 0.15)
            if not conts:
                continue
            # her harf ayrı yol, hepsi aynı renk
            el = _fill_element(conts, tuple(int(v) for v in ink_col), tol * 0.7, shapes=False, layer="harf")
            if el:
                elements.append(el)

    # --- çizgiler: kaplamayı büyütüp iskeletini çıkar
    for k, thin in thin_by.items():
        if not thin.any():
            continue
        reach = cv2.dilate(thin.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        reach &= ~thick_by[k]
        sc = np.where(reach, cov[k], 0.0).astype(np.float32)
        n, cc, stats, _ = cv2.connectedComponentsWithStats(reach.astype(np.uint8), connectivity=8)
        items = []
        for i in range(1, n):
            x, y, ww, hh, area = stats[i]
            p = 2
            a0, b0, a1, b1 = max(0, x - p), max(0, y - p), min(w, x + ww + p), min(h, y + hh + p)
            part = np.where(cc[b0:b1, a0:a1] == i, sc[b0:b1, a0:a1], 0.0)
            if part.sum() < 0.3:
                continue
            items.extend(_stroke_items(part, f, a0, b0))
        if not items:
            continue
        items = _join_paths([(egri.smooth_open(t[0], 0.6) if len(t[0]) > 4 else t[0],) + tuple(t[1:]) for t in items], 1.0)

        def under(x, y, _fl=fill_lab):
            return colors[int(_fl[int(np.clip(round(y), 0, h - 1)), int(np.clip(round(x), 0, w - 1))])]
        sel = _stroke_elements(items, colors[k], tol, under)
        # görselle karşılaştır: tutmayan çizgiyi at, eksik kalan yeri görseldeki biçimiyle çiz
        elements.extend(_verify_strokes(sel, cov[k], cc, stats, f, colors[k], tol, w, h))

    if bg_rect is not None:
        elements.append(bg_rect)
    for x0, y0, x1, y1, col, wd, dash in soluk:
        elements.append(Element("stroke", col, prim={"type": "line", "x1": x0, "y1": y0, "x2": x1, "y2": y1},
                                width=wd, dash=dash, bbox=(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))))
    if opts.cizim:
        from . import duzen
        elements = duzen.cizimlestir(elements, colors[bg])
        elements = duzen.izgara_tamamla(elements, rgb, colors[bg])
        elements = duzen.koordinat_izgarasi(elements, rgb)
        elements = duzen.soluk_lekeler(elements, rgb, colors[bg])
    # --- çizim sırası: büyük dolgular altta; çizgiler; küçük dolgular (nokta, simge) ve harfler üstte
    diag = math.hypot(w, h)
    small_lim = (0.025 * diag) ** 2
    for e in elements:
        if e.kind == "fill" and e.layer == "" and e.area <= small_lim:
            e.layer = "ust"

    def zkey(e):
        if e.kind == "fill" and e.layer in ("", "alt"):
            return (0, -e.area)
        if e.kind == "stroke":
            # açık renkli kesikli ızgara çizgisi öbür çizgilerin (veri çizgisi, eksen) altında
            izgara = bool(e.dash) and float(np.mean(e.color)) >= 150
            return (1, 0 if izgara else 1, -(e.bbox[2] - e.bbox[0] + e.bbox[3] - e.bbox[1]))
        if e.layer == "ust":
            return (2, -e.area)
        return (3, 0)

    elements.sort(key=zkey)
    if shrink != 1.0:
        _rescale(elements, 1 / shrink)
        scene.width, scene.height = W, H
    scene.elements = elements
    scene.notes.append(f"{K} renk · {sum(e.kind == 'fill' for e in elements)} dolgu · {sum(e.kind == 'stroke' for e in elements)} çizgi")
    return scene


def _soluk_cizgiler(lab: np.ndarray, rgb: np.ndarray, pal: np.ndarray, bg: int, min_len: int,
                    long_len: int = 10 ** 9):
    """Paletin karşılamadığı soluk, uzun yatay/dikey çizgiler (açık gri eksen, ızgara çizgisi).

    Bu çizgiler siyahla beyazın karışımına benzediği için renk ayrımında kaybolur. Burada
    doğrudan görünen renkleriyle çizgi olarak çıkarılır. Dönüş: (çizgi listesi, pikselleri).
    Çizgi: (x0, y0, x1, y1, renk, kalınlık)
    """
    h, w = lab.shape[:2]
    bgc = pal[bg]
    d = np.linalg.norm(lab - bgc, axis=2).astype(np.float32)
    others = [pal[k] for k in range(len(pal)) if k != bg]
    lines, mask = [], np.zeros((h, w), bool)

    def faint_or_new(C):
        # paletteki bir rengin kenar yumuşatmalı (yarı kaplı) hâli değilse ya da çok soluksa bizim işimiz
        for P in others:
            AB = P - bgc
            nab = float(AB @ AB)
            if nab < 1e-6:
                continue
            al = float(np.clip((C - bgc) @ AB / nab, 0, 1))
            res = float(np.linalg.norm(C - (bgc + al * AB)))
            if res < 12 and al >= 0.42:
                return False
            if float(np.linalg.norm(C - P)) < 12:
                return False
        return True

    for orient in ("h", "v"):
        D = d if orient == "h" else d.T
        L = lab if orient == "h" else lab.transpose(1, 0, 2)
        R = rgb if orient == "h" else rgb.transpose(1, 0, 2)
        n_rows, n_cols = D.shape
        up = np.vstack([D[:1], D[:-1]])
        dn = np.vstack([D[1:], D[-1:]])
        up2 = np.vstack([D[:2], D[:-2]])
        dn2 = np.vstack([D[2:], D[-2:]])
        ridge = (D >= 8) & (D >= up) & (D >= dn) & ((D > up + 2) | (D > dn + 2))
        # iki yanı da zemin (ya da 2 piksellik çizginin öbür yarısı, sonra zemin) olmalı:
        # sütun kenarı gibi bir yanı dolgu olan çizgiler burada değil, dolgunun konturu olur
        lo = np.minimum(0.6 * D, 12.0)
        side_a = (up < lo) | ((up2 < lo) & (dn < lo))
        side_b = (dn < lo) | ((dn2 < lo) & (up < lo))
        ridge &= side_a & side_b
        same = np.zeros_like(ridge)
        same[:, :-1] = np.linalg.norm(L[:, 1:] - L[:, :-1], axis=2) < 12
        found = []
        for y in range(n_rows):
            r = ridge[y]
            if r.sum() < min_len:
                continue
            ok = r & np.concatenate([same[y, :-1] | np.roll(same[y], 1)[:-1], [False]]) if n_cols > 1 else r
            # ardışık parçalar (üstünden geçen kıyı gibi 1-4 piksellik kesintiler kapatılır)
            okc = ndimage.binary_closing(ok, structure=np.ones(5, bool)) | ok
            idx = np.flatnonzero(np.diff(np.concatenate([[0], okc.astype(np.int8), [0]])))
            for a, b in zip(idx[::2], idx[1::2]):
                if b - a < min_len:
                    continue
                dash = None
                if ok[a:b].mean() < 0.85:
                    # kesik çizgi (ızgara): düzenli kesik ve aralıklar
                    if ok[a:b].mean() < 0.45:
                        continue
                    rr = np.flatnonzero(np.diff(np.concatenate([[0], ok[a:b].astype(np.int8), [0]])))
                    dz = (rr[1::2] - rr[::2]).astype(float)
                    gz = (rr[2::2] - rr[1:-1:2]).astype(float)
                    if len(dz) < 4 or len(gz) < 3:
                        continue
                    dzi = dz[1:-1] if len(dz) > 4 else dz
                    if dzi.std() > 0.35 * dzi.mean() or gz.std() > 0.45 * gz.mean():
                        continue
                    dash = [float(np.median(dzi)), float(np.median(gz))]
                C = np.median(L[y, a:b][ok[a:b]], axis=0)
                # çok uzun düz çizgiler (eksen, harita paraleli) renkleri paletteyse de tek parça alınır
                if np.linalg.norm(C - bgc) < 8 or (b - a < long_len and not faint_or_new(C)):
                    continue
                found.append([y, a, b, C, dash])
        # aynı çizginin iki satırı (2 piksel kalın çizgi) tek çizgi olur
        found.sort(key=lambda t: (t[0], t[1]))
        merged = []
        for y, a, b, C, dash in found:
            for m in merged:
                if abs(m[0][-1] - y) <= 1 and min(b, m[2]) - max(a, m[1]) > 0.5 * min(b - a, m[2] - m[1]):
                    m[0].append(y)
                    m[1], m[2] = min(a, m[1]), max(b, m[2])
                    break
            else:
                merged.append([[y], a, b, C, dash])
        for ys, a, b, C, dash in merged:
            y0, y1 = max(0, min(ys) - 2), min(n_rows, max(ys) + 3)
            prof = D[y0:y1, a:b]
            core = float(np.median(D[ys, a:b]))
            if core < 1e-3:
                continue
            # iki ucu da aynı mürekkeple dönerek sürüyorsa (kutu, çerçeve kenarı) çizgi değildir
            def _goes_on(x_lo, x_hi):
                x_lo, x_hi = max(0, x_lo), min(n_cols, x_hi)
                if x_hi <= x_lo:
                    return False
                win = D[max(0, min(ys) - 4):min(n_rows, max(ys) + 5), x_lo:x_hi]
                off = np.ones(win.shape, bool)
                r0 = max(0, min(ys) - 4)
                for yy in ys:
                    if 0 <= yy - r0 < win.shape[0]:
                        off[yy - r0] = False
                return bool(((win >= 0.6 * core) & off).sum() >= 2)
            if _goes_on(a - 3, a + 2) and _goes_on(b - 2, b + 3):
                continue
            wts = np.clip(np.median(prof, axis=1) / core, 0, 1)
            wts[wts < 0.08] = 0
            width = float(np.clip(wts.sum(), 0.6, 3.0))
            yc = float((np.arange(y0, y1) * wts).sum() / max(wts.sum(), 1e-6))
            core_rows = slice(min(ys), max(ys) + 1)
            col = tuple(int(v) for v in np.median(R[core_rows, a:b].reshape(-1, 3), axis=0))
            # yalnız çizginin kendi pikselleri (ona değen daha koyu çentik/şekil değil)
            band = (prof > 3) & (prof <= core * 1.25 + 4)
            # çizgiye bir şey değiyorsa (harf, sütun, çentik) o sütunlar ayrılmaz: şekil bütün kalsın
            above = D[y0 - 1, a:b] if y0 >= 1 else np.zeros(b - a)
            below = D[y1, a:b] if y1 < n_rows else np.zeros(b - a)
            touch = (above > 0.35 * core) | (below > 0.35 * core)
            touch = ndimage.binary_dilation(touch, structure=np.ones(3, bool))
            band[:, touch] = False
            if orient == "h":
                lines.append((float(a) - 0.5, yc, float(b) - 0.5, yc, col, width, dash))
                mask[y0:y1, a:b] |= band
            else:
                lines.append((yc, float(a) - 0.5, yc, float(b) - 0.5, col, width, dash))
                mask[a:b, y0:y1] |= band.T
    return _izgara_birlestir(lines), mask


def _izgara_birlestir(lines: list) -> list:
    """Yazı ya da veri çizgisi yüzünden bölünmüş kesikli ızgara çizgisi parçalarını birleştir."""
    out, used = [], set()
    for i, (x0, y0, x1, y1, col, wd, dash) in enumerate(lines):
        if i in used:
            continue
        if not dash:
            out.append(lines[i])
            continue
        yatay = abs(y0 - y1) < 0.5
        grp = [i]
        for j in range(i + 1, len(lines)):
            if j in used:
                continue
            u0, v0, u1, v1, c2, w2, d2 = lines[j]
            if not d2 or (abs(v0 - v1) < 0.5) != yatay:
                continue
            same_pos = abs(v0 - y0) <= 1.0 if yatay else abs(u0 - x0) <= 1.0
            if same_pos and math.dist(col, c2) < 20 and abs(d2[0] - dash[0]) <= 1.5:
                grp.append(j)
        if len(grp) == 1:
            out.append(lines[i])
            continue
        if yatay:
            spans = [(lines[j][0], lines[j][2]) for j in grp]
        else:
            spans = [(lines[j][1], lines[j][3]) for j in grp]
        lo = min(a for a, _b in spans)
        hi = max(b for _a, b in spans)
        tot = sum(b - a for a, b in spans)
        if tot < 0.5 * (hi - lo):
            out.append(lines[i])
            continue
        used.update(grp)
        wm = float(np.median([lines[j][5] for j in grp]))
        if yatay:
            out.append((lo, y0, hi, y0, col, wm, dash))
        else:
            out.append((x0, lo, x0, hi, col, wm, dash))
    return out


def stroke_width(rgb: np.ndarray) -> float:
    """Görseldeki ince çizgi ve yazıların tipik kalınlığı (piksel). Büyütülmüş görselde büyüktür."""
    h, w = rgb.shape[:2]
    k = 1
    small = rgb
    if max(h, w) > 1600:
        k = max(h, w) / 1600
        small = cv2.resize(rgb, (int(w / k), int(h / k)), interpolation=cv2.INTER_AREA)
    lab = _to_lab(small)
    flat = lab.reshape(-1, 3)
    q = np.round(flat / 4).astype(np.int32)
    keys, cnt = np.unique(q, axis=0, return_counts=True)
    bgc = keys[cnt.argmax()] * 4.0
    ink = (np.linalg.norm(lab - bgc, axis=2) > 35).astype(np.uint8)
    if ink.sum() < 50:
        return 1.0
    dt = cv2.distanceTransform(np.pad(ink, 1), cv2.DIST_L2, 5)[1:-1, 1:-1]
    sk = skeletonize(ink > 0)
    vals = dt[sk]
    if len(vals) < 30:
        return 1.0
    # en ince yaygın çizgiler: iskeletteki kalınlıkların alt dilimi
    return float(np.percentile(vals, 30)) * 2 * k


def _stroke_items(part: np.ndarray, f: int, ox: int, oy: int):
    """Bir ince bileşenin kaplamasından çizgi(ler): [(noktalar, kalınlık, uzunluk)] özgün pikselde."""
    up = _up(part, f)
    mask = up >= 0.35
    if not mask.any():
        # çok soluk küçük nokta
        ys, xs = np.nonzero(part > 0.05)
        if not len(xs):
            return []
        c = np.array([[xs.mean() + ox, ys.mean() + oy]])
        return [(c, 2 * math.sqrt(float(part.sum()) / math.pi), 0.0, float(part.max()))]
    skel = skeletonize(mask)
    paths = trace_skeleton(skel)
    if not paths:
        return []
    pid = np.full(mask.shape, -1, np.int32)
    for i, p in enumerate(paths):
        pid[p[:, 1].astype(int), p[:, 0].astype(int)] = i
    _, (iy, ix) = ndimage.distance_transform_edt(pid < 0, return_indices=True)
    owner = pid[iy, ix]
    mass = np.bincount(owner.ravel(), weights=up.ravel(), minlength=len(paths))
    out = []
    for i, p in enumerate(paths):
        q = np.column_stack([(p[:, 0] + 0.5) / f - 0.5 + ox, (p[:, 1] + 0.5) / f - 0.5 + oy])
        L = float(np.hypot(*np.diff(q, axis=0).T).sum()) if len(q) > 1 else 0.0
        # çizginin en dolu yerindeki kaplama: hiç tam dolmuyorsa çizgi gerçekten daha açık renktir
        peak = float(np.percentile(up[p[:, 1].astype(int), p[:, 0].astype(int)], 90))
        if L < 0.8:
            # nokta: çapı kütleden
            width = 2 * math.sqrt(mass[i] / (f * f) / math.pi)
        else:
            # kalınlık = kaplama kütlesi / uzunluk (özgün piksel)
            width = mass[i] / (f * f) / max(L + 1.0 / f, 1.0 / f)
        out.append((q, float(width), L, min(1.0, peak)))
    return out


def _mix(c, under, a):
    return tuple(int(round(u + (v - u) * a)) for v, u in zip(c, under))


def _stroke_elements(items, color, tol, under=None):
    """Çizgileri doğru, kesikli doğru, nokta ya da eğri olarak yaz.

    Bir çizgi hiçbir yerinde tam dolmuyorsa (ör. gri noktalı kılavuz çizgisi siyahın yarısı gibi
    görünür) rengi o açıklıkta, kalınlığı da buna göre yazılır.
    """
    out = []
    straight, other = [], []

    def tone(wd, a, at, dot=False):
        if a >= 0.8 or under is None:
            return color, wd
        if not dot and a >= 0.6 and wd >= 1.1:
            # bir buçuk piksellik koyu çizgi bulanıklıktan hiçbir yerde tam dolmaz: rengi kendisi,
            # kalınlığı kütlesi kadar (açık renkli kalın çizgi değil)
            return color, wd
        a = max(a, 0.2)
        # çizgide kütle kalınlıkla, noktada alanla (çapın karesiyle) orantılı
        return _mix(color, under(*at), a), (wd / math.sqrt(a) if dot else wd / a)

    for p, wd, L, a in items:
        wd = max(wd, 0.35)
        if len(p) == 1 or L < 0.8:
            c = p.mean(axis=0)
            straight.append((c - [0.01, 0], c + [0.01, 0], wd, a))
            continue
        c, dvec, dev = egri.line_fit(p)
        if dev <= max(0.45, 0.012 * L):
            t = (p - c) @ dvec
            straight.append((c + dvec * t.min(), c + dvec * t.max(), wd, a))
        else:
            other.append((p, wd, L, a))
    groups, used = _dash_groups([(p0, p1, wd) for p0, p1, wd, a in straight], 1.0)
    for gi, (p0, p1, wd, dashes, gaps) in enumerate(groups):
        # grubun kaplaması: bu doğru üzerindeki üyelerin ortancası
        v = p1 - p0
        vn = max(float(np.hypot(*v)), 1e-6)
        al = []
        for i in used:
            m = (straight[i][0] + straight[i][1]) / 2 - p0
            if abs(v[0] * m[1] - v[1] * m[0]) / vn < 2:
                al.append(straight[i][3])
        a = float(np.median(al)) if al else 1.0
        dotted = float(np.median(dashes)) <= wd * 1.4
        col, wd2 = tone(wd, a, (p0 + p1) / 2, dot=dotted)
        pat, cap = _dash_pattern(dashes, gaps, wd2, iskelet=True)
        if float(np.median(gaps)) < 0.8:
            pat, cap = None, "butt"     # aralıksız parçalar: düz çizgi (araya giren şekiller bölmüş)
        elif cap == "butt":
            # iskelet uçları yarım kalınlık içeride: çizgi ilk kesiğin başından son kesiğin sonuna
            u_ = v / vn
            yeni = None
            if pat and len(pat) == 2 and len(dashes) >= 3 and len(dashes) == len(gaps) + 1:
                # kesik ortalarına doğru oturtulur: adım ve başlangıç birlikte ölçülür, tek tek
                # kesiklerin pikselden kaynaklı oynaması uzun çizgide kayma biriktirmez
                st_, cs = 0.0, []
                for i_, dl in enumerate(dashes):
                    cs.append(st_ + dl / 2)
                    if i_ < len(gaps):
                        st_ += dl + gaps[i_]
                cs = np.array(cs)
                P0 = pat[0] + pat[1]
                idx = np.concatenate([[0.0], np.cumsum(np.maximum(1.0, np.round(np.diff(cs) / max(P0, 1e-6))))])
                if len(np.unique(idx)) >= 3:
                    Pf, af = np.polyfit(idx, cs, 1)
                    if 0.7 * P0 <= Pf <= 1.3 * P0:
                        md = min(pat[0], Pf - 0.8)
                        pat = [md, Pf - md]
                        yeni = (p0 + u_ * (af - md / 2), p0 + u_ * (af + idx[-1] * Pf + md / 2))
            if yeni is not None:
                p0, p1 = yeni
            else:
                ext = u_ * (wd / 2)
                p0, p1 = p0 - ext, p1 + ext
        elif cap == "round" and pat and len(pat) == 2 and pat[0] < 0.1 and len(dashes) >= 3 \
                and len(dashes) == len(gaps) + 1:
            # noktalı çizgi: noktalar ortalarına doğru oturtulur (uzun çizgide kayma birikmesin)
            u_ = v / vn
            st_, cs = 0.0, []
            for i_, dl in enumerate(dashes):
                cs.append(st_ + dl / 2)
                if i_ < len(gaps):
                    st_ += dl + gaps[i_]
            cs = np.array(cs)
            # adımın ilk tahmini ardışık nokta ortaları arasından (aralık + ölçülen boy noktada eksik kalır)
            P0 = float(np.median(np.diff(cs)))
            # sıra numaraları ardışık farklardan (aradaki eksik nokta sayısı); toplu yuvarlama uzun
            # çizgide adım hatasıyla kayar
            idx = np.concatenate([[0.0], np.cumsum(np.maximum(1.0, np.round(np.diff(cs) / max(P0, 1e-6))))])
            if len(np.unique(idx)) >= 3:
                Pf, af = np.polyfit(idx, cs, 1)
                if 0.7 * P0 <= Pf <= 1.3 * P0:
                    pat = [0.01, Pf - 0.01]
                    p0, p1 = p0 + u_ * af, p0 + u_ * (af + idx[-1] * Pf)
        p0, p1 = _snap_axis(p0, p1, 1.0)
        out.append(Element("stroke", col, prim={"type": "line", "x1": p0[0], "y1": p0[1], "x2": p1[0], "y2": p1[1]},
                           width=wd2, dash=pat, cap=cap,
                           bbox=(min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1]))))
    for i, (p0, p1, wd, a) in enumerate(straight):
        if i in used:
            continue
        L = float(np.hypot(*(p1 - p0)))
        if L < 0.8:
            c = (p0 + p1) / 2
            if wd < 0.9:
                continue          # soluk tek piksel: gürültü
            col, d2 = tone(wd, a, c, dot=True)
            r = max(d2, 0.6) / 2
            out.append(Element("fill", col, prim={"type": "circle", "cx": c[0], "cy": c[1], "r": r},
                               area=math.pi * r * r, bbox=(c[0] - r, c[1] - r, c[0] + r, c[1] + r)))
            continue
        col, wd2 = tone(wd, a, (p0 + p1) / 2)
        p0, p1 = _snap_axis(p0, p1, 1.0)
        out.append(Element("stroke", col, prim={"type": "line", "x1": p0[0], "y1": p0[1], "x2": p1[0], "y2": p1[1]},
                           width=wd2, bbox=(min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1]))))
    for p, wd, L, a in other:
        closed = len(p) > 8 and np.hypot(*(p[0] - p[-1])) <= 1.0
        pts = egri.resample(p[:-1] if closed else p, 0.5, closed)
        prim = None
        if closed:
            fit = egri.circle_fit(pts)
            if fit and fit[3] < 0.25:
                prim = {"type": "circle", "cx": fit[0], "cy": fit[1], "r": fit[2]}
        d = ""
        if not prim:
            d = _polyline_d(pts, closed)
            if not d:
                # yumuşak eğri: titremeyi alıp az parçalı Bézier/yay yaz
                sg = 2.5 if L < 40 else 4.0
                sm = (egri.smooth_closed(pts, sg) if closed else egri.smooth_open(pts, sg)) if len(pts) > 8 else pts
                d = _seg_path(sm, closed, max(tol, 0.4), 1.0, k=4)
        x0, y0 = p.min(axis=0)
        x1, y1 = p.max(axis=0)
        col, wd2 = tone(wd, a, p[len(p) // 2])
        out.append(Element("stroke", col, d=d, prim=prim, width=wd2, cap="round",
                           bbox=(float(x0), float(y0), float(x1), float(y1))))
    return out


def _serit_birlesim(F, c, a0, b0, k, fill_lab, cov, bg, thin_all, kontur_bandi, prim):
    """Kutunun bir kenarına bitişik başka renkte şerit (başlık bandı) ile birleşik kutu.

    Şeritle kutu birlikte temiz bir dikdörtgense, dış kenar çizgisi şeridin de dışından geçiyor
    ve ikisinin arasında çizgi yoksa: (şekil, kaplama, maske, pencere); yoksa None."""
    Hi, Wi = fill_lab.shape
    Hh, Ww = F.shape
    ys, xs = np.nonzero(F)
    if not len(ys):
        return None
    fy0, fy1, fx0, fx1 = ys.min() + b0, ys.max() + b0, xs.min() + a0, xs.max() + a0
    mg = int(0.7 * max(fy1 - fy0, fx1 - fx0)) + 4
    X0, Y0 = max(0, fx0 - mg), max(0, fy0 - mg)
    X1, Y1 = min(Wi, fx1 + mg + 1), min(Hi, fy1 + mg + 1)
    if a0 < X0 or b0 < Y0 or a0 + Ww > X1 or b0 + Hh > Y1:
        return None
    big = fill_lab[Y0:Y1, X0:X1]
    oy, ox = b0 - Y0, a0 - X0
    Fb = np.zeros(big.shape, bool)
    Fb[oy:oy + Hh, ox:ox + Ww] = F
    cb = np.zeros(big.shape, np.float32)
    cb[oy:oy + Hh, ox:ox + Ww] = c
    ker3 = np.ones((3, 3), np.uint8)
    near = cv2.dilate(Fb.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    fa = float(Fb.sum())
    # bütün ince çizgiler (başka şekillere kontur olarak verilmiş olanlar dahil)
    t_any = thin_all[Y0:Y1, X0:X1]
    t_near = cv2.dilate(t_any.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    kb = kontur_bandi[Y0:Y1, X0:X1]

    def kenar(M_):
        Mu = np.pad(M_.astype(np.uint8), 1)
        return M_ & ~(cv2.erode(Mu, ker3)[1:-1, 1:-1] > 0)
    st_ = np.ones((3, 3), bool)
    for o in np.unique(big[near]):
        if o == k or o == bg:
            continue
        ol, on = ndimage.label(big == o, structure=st_)
        for j in np.unique(ol[near]):
            if j == 0:
                continue
            cm = ol == j
            if cm[0, :].any() or cm[-1, :].any() or cm[:, 0].any() or cm[:, -1].any():
                continue
            if float(cm.sum()) >= fa or float(cm.sum()) < 0.05 * fa:
                continue
            reach = cv2.dilate(cm.astype(np.uint8), ker3) > 0
            cu = np.clip(cb + np.where(cm, 1.0, np.where(reach & ~Fb, cov[o, Y0:Y1, X0:X1], 0.0)), 0, 1)
            pu = sekil.uydur(cu.astype(np.float32), X0, Y0)
            if pu is None or pu["type"] not in ("rect", "rrect") or pu["w"] * pu["h"] < 1.08 * prim["w"] * prim["h"]:
                continue
            Uc = Fb | cm
            shared = kenar(Fb) & reach
            outer = kenar(Uc) & reach & ~kb
            if shared.sum() < 6 or outer.sum() < 6:
                continue
            in_sh = float((shared & t_near).sum()) / float(shared.sum())
            on_out = float((outer & t_near).sum()) / float(outer.sum())
            if on_out >= 0.6 and in_sh <= 0.3:
                return pu, cu.astype(np.float32), Uc, (X0, Y0, X1, Y1)
    return None


def _isaret_ayir(F, c=None):
    """İnce çizgi parçalarıyla birleşik yuvarlak işaretler: [(x, y, r)], kalan ince kısım, işaret
    diskleri. İşaret çizgiden belirgin kalın ve yuvarlaktır; kalan kısım ince olmalı. Uymuyorsa None."""
    H, W = F.shape
    dt = cv2.distanceTransform(np.pad(F.astype(np.uint8), 1), cv2.DIST_L2, 5)[1:-1, 1:-1]
    sk = skeletonize(F)
    if sk.sum() < 6:
        return None
    med = float(np.median(dt[sk]))
    thr = max(2.6, 1.5 * med)
    blob = dt >= thr
    if not blob.any():
        return None
    if _ucgen_mi(F.astype(np.float32) if c is None else c):
        return None         # okun ucu (üçgen) işaret değil
    yy, xx = np.mgrid[0:H, 0:W]
    dots = []
    disks = np.zeros(F.shape, bool)
    nb, bl = cv2.connectedComponents(blob.astype(np.uint8), connectivity=8)
    for j in range(1, nb):
        m = bl == j
        dm = float(dt[m].max())
        ys_, xs_ = np.nonzero(m & (dt >= dm - 0.35))
        cx, cy = float(xs_.mean()), float(ys_.mean())
        r = dm + 0.5
        rr = np.hypot(yy - cy, xx - cx)
        ring = (rr >= r + 0.8) & (rr <= r + 2.5)
        if ring.sum() == 0 or float((F & ring).sum()) / float(ring.sum()) > 0.4:
            return None
        # işaret yuvarlak: diskinin içi dolu
        ic = rr <= r - 0.5
        if ic.sum() and float((F & ic).sum()) / float(ic.sum()) < 0.9:
            return None
        dots.append((cx, cy, r))
        disks |= rr <= r + 0.7
    rest = F & ~disks
    if rest.any():
        dr = cv2.distanceTransform(np.pad(rest.astype(np.uint8), 1), cv2.DIST_L2, 5)[1:-1, 1:-1]
        if float(dr.max()) > 2.3:
            return None
    return dots, rest, disks


def _kalin_cizgi(F, a0, b0, color):
    """Kalınca, eni boyunca aynı genişlikte uzun bir şekil (grafikteki veri çizgisi) ve üstündeki
    yuvarlak işaretler: dolgu yerine çizgi + daireler. Uymuyorsa None."""
    H, W = F.shape
    Fu = np.pad(F.astype(np.uint8), 1)
    dt = cv2.distanceTransform(Fu, cv2.DIST_L2, 5)[1:-1, 1:-1]
    sk = skeletonize(F)
    if sk.sum() < 12:
        return None
    wd_all = 2 * dt[sk]
    wl = float(np.percentile(wd_all, 40))
    if wl < 2.4 or wl > 9:
        return None
    if float(((wd_all >= 0.6 * wl) & (wd_all <= 1.5 * wl)).mean()) < 0.6:
        return None
    if sk.sum() < 8 * wl:
        return None
    # yuvarlak işaretler: çizgiden belirgin kalın, daire biçimli yerler
    thr = max(0.8 * wl, wl / 2 + 1.5)
    blob = dt >= thr
    dots = []
    disk_all = np.zeros(F.shape, bool)
    yy, xx = np.mgrid[0:H, 0:W]
    if blob.any():
        nb, bl = cv2.connectedComponents(blob.astype(np.uint8), connectivity=8)
        for j in range(1, nb):
            m = bl == j
            dm = np.where(m, dt, 0)
            iy, ix = np.unravel_index(int(np.argmax(dm)), dm.shape)
            r = float(dt[iy, ix]) + 0.5
            rr = np.hypot(yy - iy, xx - ix)
            ring = (rr >= r + 0.8) & (rr <= r + 2.5)
            if ring.sum() == 0 or float((F & ring).sum()) / float(ring.sum()) > 0.4:
                return None         # yuvarlak değil (ok ucu gibi): bu yol değil
            dots.append((ix, iy, r))
            disk_all |= rr <= r + 0.7
    # çizgi: iskelet, işaretlerin içinden geçerek
    paths = trace_skeleton(sk)
    if not paths:
        return None
    out = []
    lines = []
    for p in paths:
        q = p.astype(float)
        if len(q) < 2:
            continue
        L = float(np.hypot(*np.diff(q, axis=0).T).sum())
        # işaretin içinde kalan kısa dallar çizgi değildir
        inside = disk_all[q[:, 1].astype(int), q[:, 0].astype(int)].mean() if len(q) else 1
        if L < max(2.5 * wl, 6) and inside > 0.5:
            continue
        v = None
        if dots:
            # veri noktaları: çizgi işaretlerin merkezlerinden geçen kırık çizgidir
            seq = []
            for ix, iy, r in dots:
                dd = np.hypot(q[:, 0] - ix, q[:, 1] - iy)
                j = int(np.argmin(dd))
                if dd[j] <= r:
                    seq.append((j, (float(ix), float(iy))))
            seq.sort()
            cand = [c_ for _j, c_ in seq]
            if seq and seq[0][0] > 2:
                cand = [tuple(q[0])] + cand
            if seq and seq[-1][0] < len(q) - 3:
                cand = cand + [tuple(q[-1])]
            if len(cand) >= 2:
                cv_ = np.array(cand, float)
                # sapma: iskelet noktalarının kırık çizgiye uzaklığı
                dmin = np.full(len(q), np.inf)
                for p0_, p1_ in zip(cv_[:-1], cv_[1:]):
                    dv = p1_ - p0_
                    n2 = float(dv @ dv)
                    t_ = np.clip(((q - p0_) @ dv) / max(n2, 1e-9), 0, 1)
                    dmin = np.minimum(dmin, np.hypot(*(q - (p0_ + t_[:, None] * dv)).T))
                if float(np.percentile(dmin, 95)) <= max(1.5, 0.5 * wl):
                    v = cv_
        if v is None:
            v = np.array(egri.rdp(q, max(1.0, 0.4 * wl)), float)
        lines.append(v)
    if not lines:
        return None
    for v in lines:
        d = "M" + "L".join(f"{_f(x + a0)} {_f(y + b0)}" for x, y in v)
        pts = v + [a0, b0]
        bb = (float(pts[:, 0].min()), float(pts[:, 1].min()), float(pts[:, 0].max()), float(pts[:, 1].max()))
        e = Element("stroke", color, d=d, width=wl, cap="round", bbox=bb, layer="veri")
        e.join = "round"
        out.append(e)
    for ix, iy, r in dots:
        cx, cy = ix + a0, iy + b0
        out.append(Element("fill", color, prim={"type": "circle", "cx": float(cx), "cy": float(cy), "r": r},
                           area=math.pi * r * r, bbox=(cx - r, cy - r, cx + r, cy + r)))
    # doğrulama: çizilen, şekli karşılamalı
    R = np.zeros(F.shape, np.uint8)
    for v in lines:
        cv2.polylines(R, [np.round(v * 4).astype(np.int32)], False, 1, thickness=max(1, int(round(wl))),
                      lineType=cv2.LINE_8, shift=2)
    for ix, iy, r in dots:
        cv2.circle(R, (int(ix), int(iy)), int(round(r)), 1, -1)
    Rb = R > 0
    # ince şekilde örtüşme oranı yanıltıcı: iki yönde de 1,5 piksel içinde kalma oranı
    k5 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    Fd = cv2.dilate(F.astype(np.uint8), k5) > 0
    Rd = cv2.dilate(Rb.astype(np.uint8), k5) > 0
    if not Rb.any() or float((F & Rd).sum()) / float(F.sum()) < 0.96 or float((Rb & Fd).sum()) / float(Rb.sum()) < 0.96:
        return None
    return out


def _ucgen_mi(c: np.ndarray) -> bool:
    """Küçük leke üçgen mi (okun ucu): ince çizgi kökleri atıldıktan sonra şekli saran en küçük
    üçgen şeklin kendisine yakınsa (dairede üçgen alanı 1,65 katıdır)."""
    up = (cv2.resize(c.astype(np.float32), (c.shape[1] * 4, c.shape[0] * 4),
                     interpolation=cv2.INTER_LINEAR) >= 0.5).astype(np.uint8)
    up = cv2.morphologyEx(up, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    cs_, _h = cv2.findContours(up, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs_:
        return False
    hp_ = cv2.convexHull(max(cs_, key=cv2.contourArea))
    ah = cv2.contourArea(hp_)
    if ah < 20:
        return False
    at, _tri = cv2.minEnclosingTriangle(hp_.astype(np.float32))
    # (okun ucunda oran 1,04-1,14; çizgi kökleri kalan küçük yuvarlak işarette 1,23 ve üstü)
    return at / ah < 1.18

def _kucuk_daire(c: np.ndarray, a0: int, b0: int):
    """Birkaç piksellik yuvarlak leke (lejant noktası, harita noktası): köşeleri boş, eni boyu
    eşitse daire. Dönüş: daire ya da None."""
    ys, xs = np.nonzero(c > 0.5)
    if len(ys) < 4:
        return None
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    w_, h_ = x1 - x0 + 1, y1 - y0 + 1
    if max(w_, h_) < 3 or max(w_, h_) > 7 or abs(int(w_) - int(h_)) > 1:
        return None
    kose = [float(c[y0, x0]), float(c[y0, x1]), float(c[y1, x0]), float(c[y1, x1])]
    if max(kose) >= 0.6 or float(np.mean(kose)) >= 0.45:
        return None         # köşeleri dolu: küçük kare
    if _ucgen_mi(c):
        return None         # okun ucu
    A = float(c.sum())
    if A <= 0:
        return None
    H, W = c.shape
    cy = float(c.sum(axis=1) @ np.arange(H)) / A
    cx = float(c.sum(axis=0) @ np.arange(W)) / A
    return {"type": "circle", "cx": cx + a0, "cy": cy + b0, "r": math.sqrt(A / math.pi)}


def _banttan_sil(thin: np.ndarray, band: np.ndarray, x0: int = 0, y0: int = 0) -> None:
    """Şeklin kenar bandına düşen başka renkli ince parçaları siler (kenarın yumuşatma kırıntıları).
    Banttan dışarı uzanan gerçek çizgiler (kenarı kesen veri çizgisi, kutuya bağlanan ok) kalır.
    band, thin içinde (x0, y0) köşesinden başlayan yerel maskedir."""
    if not band.any():
        return
    if x0 == 0 and y0 == 0 and band.shape == thin.shape:
        ys, xs = np.nonzero(band)
        x0, y0 = int(xs.min()), int(ys.min())
        band = band[y0:int(ys.max()) + 1, x0:int(xs.max()) + 1]
    H, W = thin.shape
    bh, bw = band.shape
    m = 12
    a0, b0 = max(0, x0 - m), max(0, y0 - m)
    a1, b1 = min(W, x0 + bw + m), min(H, y0 + bh + m)
    sub = thin[b0:b1, a0:a1]
    if not sub.any():
        return
    bnd = np.zeros(sub.shape, bool)
    bnd[y0 - b0:y0 - b0 + bh, x0 - a0:x0 - a0 + bw] = band
    hit = sub & bnd
    if not hit.any():
        return
    n, cc = cv2.connectedComponents(sub.astype(np.uint8), connectivity=8)
    tot = np.bincount(cc.ravel(), minlength=n)
    inb = np.bincount(cc[hit], minlength=n)
    rm = (inb > 0) & (tot - inb <= np.maximum(8, 0.4 * tot))
    rm[0] = False
    sub[rm[cc]] = False


def _gecen_cizgi(thin: np.ndarray, band: np.ndarray, x0: int, y0: int, bg_ana: np.ndarray) -> np.ndarray:
    """Şeklin kenar bandına giren ama banttan dışarı, iki yanı açık zemin olan yere uzanan yatay ya da
    dikey ince çizgi (eksen, taban çizgisi, bağlantı). Dönüş: bandın penceresinde maske."""
    H, W = thin.shape
    bh, bw = band.shape
    keep = np.zeros((bh, bw), bool)
    m = 15
    a0, b0 = max(0, x0 - m), max(0, y0 - m)
    a1, b1 = min(W, x0 + bw + m), min(H, y0 + bh + m)
    T = thin[b0:b1, a0:a1].astype(np.uint8)
    if not T.any():
        return keep
    bnd = np.zeros(T.shape, bool)
    bnd[y0 - b0:y0 - b0 + bh, x0 - a0:x0 - a0 + bw] = band
    acik = bg_ana[b0:b1, a0:a1]
    hh_, ww_ = T.shape
    out_keep = np.zeros(T.shape, bool)
    for ker, yatay in (((1, 9), True), ((9, 1), False)):
        R = cv2.morphologyEx(T, cv2.MORPH_OPEN, np.ones(ker, np.uint8)) > 0
        if not (R & bnd).any():
            continue
        n, cc = cv2.connectedComponents(R.astype(np.uint8), connectivity=8)
        for i in np.unique(cc[R & bnd]):
            if i == 0:
                continue
            ci = cc == i
            dis = ci & ~bnd
            if int(dis.sum()) < 6:
                continue
            # dışarıdaki kısmın iki yanı (2 piksel öte) görselin açık zemini
            ys, xs = np.nonzero(dis)
            if yatay:
                p1 = (np.clip(ys - 2, 0, hh_ - 1), xs)
                p2 = (np.clip(ys + 2, 0, hh_ - 1), xs)
            else:
                p1 = (ys, np.clip(xs - 2, 0, ww_ - 1))
                p2 = (ys, np.clip(xs + 2, 0, ww_ - 1))
            if int((acik[p1] & acik[p2]).sum()) >= 4:
                out_keep |= ci
    keep[:] = out_keep[y0 - b0:y0 - b0 + bh, x0 - a0:x0 - a0 + bw]
    return keep


def _de_rgb(c1, c2) -> float:
    a = cv2.cvtColor(np.array([[c1, c2]], np.float32) / 255.0, cv2.COLOR_RGB2Lab)[0]
    return float(np.linalg.norm(a[0] - a[1]))


def _karmasik(p) -> float:
    """Şeklin karmaşıklığı: temel şekil 1, çokgen/yol parça sayısı; şekil yoksa çok büyük."""
    if p is None:
        return 1e9
    t = p["type"]
    if t == "polygon":
        return float(len(p["pts"]))
    if t == "path":
        return len(p["segs"]) + 0.5 * sum(g[0] == "A" for g in p["segs"])
    return 1.0


def _ortulu_birlesim(F, c, a0, b0, x, y, ww, hh, k, fill_lab, cov, bg):
    """Bölgenin üstüne binen, bütünüyle onun sınırları içinde kalan başka renkli şekillerle
    birleşik kaplaması (alttaki şeklin tamamı); yoksa None."""
    Hh, Ww = F.shape
    Hi, Wi = fill_lab.shape
    # komşu renklere taşma payı: kenar çizgisinin yarısı üstteki şekle düşmüş olabilir
    q = 5
    X0, Y0 = max(0, x - q), max(0, y - q)
    X1, Y1 = min(Wi, x + ww + q), min(Hi, y + hh + q)
    big = fill_lab[Y0:Y1, X0:X1]
    Fb = np.zeros(big.shape, bool)
    fy0, fx0 = b0 - Y0, a0 - X0
    Fb[fy0:fy0 + Hh, fx0:fx0 + Ww] = F
    fa = float(F.sum())
    occ_b = np.zeros(big.shape, bool)
    st = np.ones((3, 3), bool)
    comps = {}
    for o in np.unique(big):
        if o == k or o == bg:
            continue
        ol, on = ndimage.label(big == o, structure=st)
        if on == 0:
            continue
        # pencere kenarına değen (bölgenin dışına taşan) parçalar üstteki şekil değildir
        edge = np.zeros(on + 1, bool)
        for s_ in (ol[0, :], ol[-1, :], ol[:, 0], ol[:, -1]):
            edge[np.unique(s_)] = True
        sizes = np.bincount(ol.ravel(), minlength=on + 1)
        ok = ~edge & (sizes < fa)
        ok[0] = False
        # iki kutunun sınırına binen küçük işaret (simge): yalnız bu kutunun içindeki kısmı
        kirp = edge & (sizes < 0.12 * fa)
        kirp[0] = False
        comps[o] = (ol, ok, kirp)
    kutu = np.zeros(big.shape, bool)
    kutu[y - Y0:y - Y0 + hh, x - X0:x - X0 + ww] = True
    # üsttekinin üstündekiler de (kutudaki kare, karenin içindeki işaret): birkaç tur büyüt
    grown = Fb
    for _ in range(4):
        near = cv2.dilate(grown.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        add = np.zeros(big.shape, bool)
        for o, (ol, ok, kirp) in comps.items():
            touch = np.zeros(len(ok), bool)
            touch[np.unique(ol[near])] = True
            add |= (touch & ok)[ol]
            add |= (touch & kirp)[ol] & kutu
        add &= ~occ_b
        if not add.any():
            break
        occ_b |= add
        grown = Fb | occ_b
    occ = occ_b[fy0:fy0 + Hh, fx0:fx0 + Ww]
    if not occ.any() or fa < 0.5 * float((F | occ).sum()):
        return None
    win = fill_lab[b0:b0 + Hh, a0:a0 + Ww]
    so = np.zeros(F.shape, np.float32)
    for o in np.unique(win[occ]):
        so += cov[o, b0:b0 + Hh, a0:a0 + Ww]
    reach = cv2.dilate(occ.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    so = np.where(occ, 1.0, np.where(reach & ~F, np.clip(so, 0, 1), 0.0))
    return np.clip(c + so, 0.0, 1.0).astype(np.float32), occ


def _outline_of(comp, a0, b0, k, thin_by, cov, bg, area, pal=None, lab=None, rgb=None, dis=None,
                skip=None):
    """Dolgu bölgesinin çevresini başka renkte ince bir kenar çiziyor mu.

    Dönüş: (kenar rengi, kalınlık, kenar pikselleri) ya da None. Bölge sınırı (dolgu çizgi
    altına uzatıldığı için) kenar çizgisinin orta hattıdır.
    """
    H, W = comp.shape
    # dar yarıkları kapat: şeklin içinden geçen çizgi kenar sayılmasın
    cp = np.pad(comp.astype(np.uint8), 4)
    cu = cv2.morphologyEx(cp, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    cu = np.where(cv2.dilate(cp, np.ones((5, 5), np.uint8)) > 0, cu, 0).astype(np.uint8)
    er = cv2.erode(cu, np.ones((3, 3), np.uint8)) > 0
    cu = cu[4:-4, 4:-4]
    edge = (cu > 0) & ~er[4:-4, 4:-4]
    n_all = max(1, int(edge.sum()))
    if skip is not None and skip.any():
        # başka bir şeklin çerçevesinin altında kalan kenarlar (panelin kenarına dayanan blok)
        # kontur aranmaz; kalan kenarlar karar verir
        edge &= ~skip
    n_edge = int(edge.sum())
    if n_edge < 12:
        return None
    cs, _ = cv2.findContours(cu, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    perim = float(sum(cv2.arcLength(c, True) for c in cs)) or float(n_edge)
    perim *= n_edge / n_all       # yalnız bakılan kenarların uzunluğu
    best = None
    # küçük şekilde (kısa sütun) yakınlık payı dar: değen eksen bütün kenarı kaplamış sayılmasın
    ys_e, xs_e = np.nonzero(edge)
    kn = np.ones((3, 3), np.uint8) if min(np.ptp(ys_e), np.ptp(xs_e)) <= 12 else np.ones((5, 5), np.uint8)
    t_any = np.zeros((H, W), bool)
    for oc, thin in thin_by.items():
        if oc == k or oc == bg:
            continue
        t = thin[b0:b0 + H, a0:a0 + W]
        if not t.any():
            continue
        t_any |= t
        # kenar rengi dolgudan ve zeminden belirgin farklı olmalı (ara tonlar kenar değildir)
        if pal is not None and (np.linalg.norm(pal[oc] - pal[k]) < 20 or np.linalg.norm(pal[oc] - pal[bg]) < 20):
            continue
        near = cv2.dilate(t.astype(np.uint8), kn) > 0
        frac = float((edge & near).sum()) / n_edge
        if best is None or frac > best[0]:
            best = (frac, oc)
    if best is None:
        return None
    if best[0] < 0.6:
        # kontur birkaç palet rengine bölünmüş olabilir (açık/koyu tonlar): hepsi birlikte
        if lab is None or not t_any.any():
            return None
        near = cv2.dilate(t_any.astype(np.uint8), kn) > 0
        fa = float((edge & near).sum()) / n_edge
        if fa < 0.7:
            return None
        best = (fa, best[1])
    oc = best[1]
    t = t_any if lab is not None else thin_by[oc][b0:b0 + H, a0:a0 + W]
    band = cv2.dilate(edge.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))) > 0
    ring = t & band
    # kontur şeklin çevresini dolaşmalı: yalnız bir yanındaki düz çizgi (kısa sütunun altındaki
    # eksen) kontur değildir
    ro = thin_by[oc][b0:b0 + H, a0:a0 + W] & band
    if ro.any():
        ry_, rx_ = np.nonzero(ro)
        ey_, ex_ = np.nonzero(edge)
        if (np.ptp(ry_) <= 3 and np.ptp(ey_) > np.ptp(ry_) + 1) or (np.ptp(rx_) <= 3 and np.ptp(ex_) > np.ptp(rx_) + 1):
            return None
    # kalınlık: kenardaki renk kütlesi / çevre uzunluğu
    mass = float(cov[oc, b0:b0 + H, a0:a0 + W][ring].sum())
    width = float(np.clip(mass / max(1.0, perim * best[0]), 0.5, 6.0))
    color = None
    if lab is not None and rgb is not None and pal is not None:
        # rengin kendisi: kenar bandında dolgudan en belirgin ayrılan piksellerin ortancası;
        # kalınlık bu renge göre (ince ve açık bir çizgi paletteki koyu rengin yarısı sayılmasın)
        L_ = lab[b0:b0 + H, a0:a0 + W]
        bandp = band & (~cu.astype(bool) | edge | ring)
        # yalnız seçilen kontur renginin çevresi: değen başka çizgiler (panel çerçevesi) karışmasın
        to = thin_by[oc][b0:b0 + H, a0:a0 + W]
        if to.any():
            bandp &= cv2.dilate(to.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        # dolgu ile zeminin (ya da dıştaki komşu rengin) karışımı kenar yumuşatmasıdır, kontur
        # değil: o doğrulara uzaklık
        A_ = pal[k]

        def resid(X):
            out = None
            for ob in {bg, bg if dis is None else dis}:
                B_ = pal[ob]
                AB = A_ - B_
                nab = float(AB @ AB)
                if nab > 1e-6:
                    t_ = np.clip(((X - B_) @ AB) / nab, 0, 1)
                    d1 = np.linalg.norm(X - (B_ + t_[..., None] * AB), axis=-1)
                else:
                    d1 = np.linalg.norm(X - A_, axis=-1)
                out = d1 if out is None else np.minimum(out, d1)
            return out
        dd = resid(L_)
        vals = dd[bandp]
        if len(vals) >= 8:
            # en belirgin kontur pikselleri (çizginin özü); bulanık kenarın ara tonları değil
            peak = float(np.percentile(vals, 90))
            top = float(np.percentile(vals, 99))
            if peak >= 8:
                # bulanık ince çizgide en koyu pikseller bile azdır: çizginin rengi en belirgin uçtakiler
                core = bandp & (dd >= max(0.8 * peak, 0.9 * top))
                if core.sum() < 5:
                    core = bandp & (dd >= max(0.8 * peak, 0.85 * top))
                # seçilen kontur renginin kendisi görünüyorsa (keskin çizgi) o pikseller: değen başka
                # renkli çizgi (eksen) daha belirgin olsa da kontur o değildir
                kend = bandp & (np.linalg.norm(L_ - pal[oc], axis=2) < 20)
                if kend.sum() >= max(5, 0.25 * perim * best[0]):
                    core = kend
                color = tuple(int(v) for v in np.median(rgb[b0:b0 + H, a0:a0 + W][core], axis=0))
                full = max(8.0, float(np.median(dd[core])))
                # siyah/koyu gri çizgi bulanıklıktan hiçbir yerde tam koyulaşmıyorsa (yarım piksele
                # düşmüş ince çizgi): görülen renk o rengin dolguyla karışımıdır; rengi paletteki koyu
                # renk, kalınlığı ona göre
                P_ = pal[oc]
                if P_[0] < 30 and math.hypot(P_[1], P_[2]) < 15:
                    cl = np.median(L_[core], axis=0)
                    for ob in {bg, bg if dis is None else dis, k}:
                        Q_ = pal[ob]
                        PQ = P_ - Q_
                        nq = float(PQ @ PQ)
                        if nq < 1e-6:
                            continue
                        t_ = float(np.clip((cl - Q_) @ PQ / nq, 0, 1))
                        if t_ >= 0.35 and float(np.linalg.norm(cl - (Q_ + t_ * PQ))) < 9:
                            color = tuple(int(v) for v in _lab_to_rgb(P_))
                            full = max(8.0, float(resid(P_[None])[0]))
                            break
                # kalınlık: kenardaki toplam koyuluk / çizginin tam koyuluğu
                m2 = float(np.clip(dd[bandp] / full, 0, 1).sum())
                width = float(np.clip(m2 / max(1.0, perim * best[0]), 0.5, 6.0))
    return oc, width, ring, color


def _verify_strokes(els, covk, cc, stats, f, color, tol, W, H):
    """Çizgileri görselle karşılaştır.

    - Bir çizgi görselde o renk olmayan yere taşıyorsa (isabet < %75) atılır.
    - Bir parçanın görseldeki pikselleri çizgilerle karşılanmıyorsa: küçük parçalar (harf,
      simge) bütünüyle dış hattından çizilir; büyük parçalarda yalnız eksik kalan yer eklenir.
    """
    if not els:
        return els
    ker3 = np.ones((3, 3), np.uint8)
    rend = {}
    good = []
    for idx, e in enumerate(els):
        bb = sadakat.bbox_of(e, pad=1.5)
        if bb is None:
            continue
        a0, b0 = max(0, int(math.floor(bb[0]))), max(0, int(math.floor(bb[1])))
        a1, b1 = min(W, int(math.ceil(bb[2])) + 1), min(H, int(math.ceil(bb[3])) + 1)
        if a1 <= a0 or b1 <= b0:
            continue
        R = sadakat.rasterize(e, f, a0, b0, ((b1 - b0) * f, (a1 - a0) * f))
        if not R.any():
            continue
        S = _up(covk[b0:b1, a0:a1], f)
        Sd = cv2.dilate((S >= 0.22).astype(np.uint8), ker3) > 0
        prec = float(Sd[R > 0].mean())
        rend[idx] = (R, a0, b0)
        # kesikli çizgide kesik uçlarının yarım piksellik kayması isabeti düşürür
        if prec >= (0.65 if e.dash else 0.75):
            good.append(idx)
    good_set = set(good)
    drop = set(range(len(els))) - good_set
    extra = []
    n = len(stats)
    disk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * f + 1, 2 * f + 1))
    for i in range(1, n):
        x, y, ww, hh, area = stats[i]
        p = 2
        ca0, cb0, ca1, cb1 = max(0, x - p), max(0, y - p), min(W, x + ww + p), min(H, y + hh + p)
        compm = cc[cb0:cb1, ca0:ca1] == i
        S = _up(np.where(compm, covk[cb0:cb1, ca0:ca1], 0.0), f)
        src = S >= 0.5
        if not src.any():
            continue
        shp = S.shape
        Rg = np.zeros(shp, np.uint8)
        members = []
        for idx, (R, a0, b0) in rend.items():
            ox, oy = (a0 - ca0) * f, (b0 - cb0) * f
            y0, x0 = max(0, oy), max(0, ox)
            y1, x1 = min(shp[0], oy + R.shape[0]), min(shp[1], ox + R.shape[1])
            if y1 <= y0 or x1 <= x0:
                continue
            piece = R[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
            if not piece.any():
                continue
            inside = cv2.resize(compm.astype(np.uint8), (shp[1], shp[0]), interpolation=cv2.INTER_NEAREST)[y0:y1, x0:x1]
            frac = float((piece & inside).sum()) / max(1.0, float(R.sum()))
            members.append((idx, frac))
            if idx in good_set:
                Rg[y0:y1, x0:x1] |= piece
        miss = src & ~(cv2.dilate(Rg, disk) > 0)
        miss_area = miss.sum() / (f * f)
        src_area = src.sum() / (f * f)
        if miss_area <= max(1.0, 0.08 * src_area):
            continue
        small = max(ww, hh) <= 40 and area <= 400
        if small:
            region = S
            for idx, frac in members:
                if frac >= 0.5:
                    drop.add(idx)
        else:
            reg = cv2.dilate(miss.astype(np.uint8), disk) > 0
            region = np.where(reg, S, 0.0)
        conts = _contours_of(np.clip(region / 0.8, 0, 1), f, ca0, cb0, 0.3)
        el = _fill_element(conts, color, tol * 0.7, shapes=False, layer="ust")
        if el:
            extra.append(el)
    return [e for i, e in enumerate(els) if i not in drop] + extra


def _polyline_d(pts: np.ndarray, closed: bool) -> str:
    """Çizgi keskin köşeli birkaç düz parçadan oluşuyorsa (sütun kenarı, eksen) köşeli yol yaz.

    Her parça kendi noktalarına en küçük karelerle oturtulur, yatay/dikeye yakınsa tam
    yatay/dikey yapılır ve köşeler komşu doğruların kesişiminden bulunur. Köşeleri keskin
    değilse (yuvarlak eğri) boş döner.
    """
    n = len(pts)
    if n < 6:
        return ""
    P = np.vstack([pts, pts[:1]]) if closed else pts
    v = egri.rdp(P, 0.6)
    if len(v) < 3:
        return ""
    # RDP köşelerinin özgün indeksleri
    idx = [int(np.argmin(np.hypot(*(P - q).T))) for q in v]
    for i in range(1, len(idx)):
        if idx[i] <= idx[i - 1]:
            return ""
    # köşedeki 1-2 piksellik pahı (iki köşe arasındaki minik parça) at
    while len(idx) > 3:
        lens = [float(np.hypot(*(P[b] - P[a]))) for a, b in zip(idx[:-1], idx[1:])]
        j = int(np.argmin(lens[1:-1])) + 1 if len(lens) > 2 else -1
        if j < 1 or lens[j] >= 2.2:
            break
        mid = (idx[j] + idx[j + 1]) // 2
        idx = idx[:j] + [mid] + idx[j + 2:]
    cs = egri.corners(P, False, 4, 32.0)
    inner = idx[1:-1]
    if not inner:
        return ""
    sharp = sum(any(abs(c - i) <= 4 for c in cs) for i in inner)
    if sharp < 0.75 * len(inner):
        return ""
    lines = []
    for a, b in zip(idx[:-1], idx[1:]):
        seg = P[a:b + 1]
        if len(seg) >= 3:
            # köşe yuvarlaklığı doğruyu eğmesin: uçlardan birer parça at
            cut = max(0, min(4, (len(seg) - 3) // 3))
            core = seg[cut:len(seg) - cut] if cut else seg
            c, dvec, _ = egri.line_fit(core)
        else:
            c, dvec = (seg[0] + seg[-1]) / 2, seg[-1] - seg[0]
            nn = float(np.hypot(*dvec)) or 1.0
            dvec = dvec / nn
        ang = math.degrees(math.atan2(abs(dvec[1]), abs(dvec[0])))
        if ang < 2.5:
            dvec = np.array([1.0, 0.0])
            c = np.array([c[0], float(np.mean(seg[:, 1]))])
        elif ang > 87.5:
            dvec = np.array([0.0, 1.0])
            c = np.array([float(np.mean(seg[:, 0])), c[1]])
        lines.append((c, dvec))

    def meet(l1, l2, fallback):
        (c1, d1), (c2, d2) = l1, l2
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-6:
            return fallback
        t = ((c2[0] - c1[0]) * d2[1] - (c2[1] - c1[1]) * d2[0]) / den
        q = c1 + d1 * t
        return q if np.hypot(*(q - fallback)) < 4.0 else fallback

    def proj(l, q):
        c, dvec = l
        return c + dvec * float((q - c) @ dvec)

    if closed:
        m = len(lines)
        verts = [meet(lines[i - 1], lines[i], P[idx[i]]) for i in range(m)]
    else:
        verts = [proj(lines[0], P[idx[0]])]
        verts += [meet(lines[i - 1], lines[i], P[idx[i]]) for i in range(1, len(lines))]
        verts.append(proj(lines[-1], P[idx[-1]]))
    d = f"M{_f(verts[0][0])} {_f(verts[0][1])}" + "".join(f"L{_f(q[0])} {_f(q[1])}" for q in verts[1:])
    return d + ("Z" if closed else "")


def _rescale(elements, s):
    """Küçültülerek işlenen görselin sonuçlarını özgün ölçüye büyüt."""
    import re
    for e in elements:
        e.width *= s
        e.stroke_width *= s
        e.area *= s * s
        e.bbox = tuple(v * s for v in e.bbox)
        if e.dash:
            e.dash = [v * s for v in e.dash]
        if e.prim:
            for key in ("x", "y", "w", "h", "cx", "cy", "r", "rx", "ry", "x1", "y1", "x2", "y2"):
                if key in e.prim:
                    e.prim[key] *= s
            if "pts" in e.prim:
                e.prim["pts"] = [(x * s, y * s) for x, y in e.prim["pts"]]
            if "start" in e.prim:
                e.prim["start"] = (e.prim["start"][0] * s, e.prim["start"][1] * s)
                e.prim["segs"] = [(g[0], g[1] * s, g[2] * s) if g[0] == "L" else
                                  (g[0], g[1] * s, g[2], g[3], g[4] * s, g[5] * s) for g in e.prim["segs"]]
        if e.d:
            # yay komutlarının bayrakları (0/1) ölçeklenmemeli: A rx ry rot büyük yön x y
            out, toks = [], re.findall(r"[MLCAZ]|-?\d+(?:\.\d+)?", e.d)
            cmd, idx = None, 0
            for t in toks:
                if t in "MLCAZ":
                    cmd, idx = t, 0
                    out.append(t)
                    continue
                v = float(t)
                if cmd == "A" and idx % 7 in (2, 3, 4):
                    out.append(t)
                else:
                    out.append(_f(v * s))
                idx += 1
            e.d = " ".join(out).replace(" M", "M").replace(" L", "L").replace(" C", "C").replace(" A", "A").replace(" Z", "Z")


def _snap_axis(p0, p1, u):
    """Neredeyse yatay/dikey çizgileri tam yatay/dikey yap."""
    v = p1 - p0
    L = float(np.hypot(*v))
    if L < 1e-6:
        return p0, p1
    ang = math.degrees(math.atan2(abs(v[1]), abs(v[0])))
    p0, p1 = p0.copy(), p1.copy()
    if ang < 1.2:
        y = (p0[1] + p1[1]) / 2
        p0[1] = p1[1] = y
    elif ang > 88.8:
        x = (p0[0] + p1[0]) / 2
        p0[0] = p1[0] = x
    return p0, p1


def _yazi_murekkebi(lab, labels, present, pal, bg, gk, core_extra=None, block=None):
    """Yazı alanlarını bütün olarak bul.

    Her rengin küçük parçaları (harf boyunda) alttaki bölgenin (kutu rengi ya da zemin)
    rengiyle karşılaştırılır; belirgin farklı olanlar harf adayıdır. Adaylar satırlara
    toplanır; içinde en az bir harf biçimli parça bulunan satırlar yazıdır. Satırdaki bütün
    mürekkep (kenar yumuşatmasındaki ara renkler dahil) yazıya aittir.

    Dönüş: (mürekkep maskesi, satırlar [(kutu, alt renk indeksi, mürekkep maskesi)]).
    """
    h, w = labels.shape
    N = h * w
    K = len(pal)
    small_side = max(12, int(0.1 * max(h, w)))
    small_area = max(400, int(0.004 * N))
    small = np.zeros((h, w), bool)
    for k in range(K + 1):
        if k == gk:
            continue
        m = labels == k
        if not m.any():
            continue
        n, cc, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
        if n <= 1:
            continue
        sz = np.maximum(st[:, cv2.CC_STAT_WIDTH], st[:, cv2.CC_STAT_HEIGHT])
        ok = (sz <= small_side) & (st[:, cv2.CC_STAT_AREA] <= small_area)
        ok[0] = False
        if k == bg:
            # zemin renginin küçük parçası yalnız bir bölgenin içindeyse (kutudaki beyaz yazı)
            x, y = st[:, 0], st[:, 1]
            ok &= (x > 0) & (y > 0) & (x + st[:, 2] < w) & (y + st[:, 3] < h)
        small |= ok[cc]
    if block is not None:
        small &= ~block
    if not small.any():
        return np.zeros((h, w), bool), []

    def _hazirla(small):
        # alttaki bölge: küçük parçalar çevresindeki büyük bölgenin rengiyle doldurulur
        _, (iy, ix) = ndimage.distance_transform_edt(small, return_indices=True)
        under = labels[iy, ix]
        under = np.where(under >= K, bg, under)
        d_under = np.linalg.norm(lab - pal[np.clip(under, 0, K - 1)], axis=2)
        cand = small & (d_under > 22)
        if core_extra is not None:
            cand |= core_extra
        if not cand.any():
            return None
        n, cc, st, _ = cv2.connectedComponentsWithStats(cand.astype(np.uint8), connectivity=8)
        if n <= 1:
            return None
        hs = st[1:, cv2.CC_STAT_HEIGHT]
        big_enough = hs >= 4
        th = float(np.median(hs[big_enough])) if big_enough.any() else 8.0
        # harf biçimli mi (dolu yuvarlak/kare değil): doluluk ve dışbükeylik
        glyphish = np.zeros(n, bool)
        cizgisel = np.zeros(n, bool)
        leke = np.zeros(n, bool)
        isaret = np.zeros(n, bool)
        for i in range(1, n):
            x, y, ww, hh, area = st[i]
            if hh < 4 or hh > 3.5 * th:
                continue
            fillr = area / float(ww * hh)
            if fillr >= 0.82:
                continue
            comp = (cc[y:y + hh, x:x + ww] == i).astype(np.uint8)
            cs, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not cs:
                continue
            hp = cv2.convexHull(np.vstack(cs))
            # piksel merkezlerinden geçen zarf alanı küçük parçada çok eksik kalır: piksel alanına çevir
            hull = cv2.contourArea(hp) + 0.5 * cv2.arcLength(hp, True) + 1.0
            solid = area / max(hull, 1.0)
            if solid >= 0.93 and fillr >= 0.6:
                continue        # dolu nokta / kare: işaret, harf değil
            # seyrek, harften çok büyük çizgi ağı (ızgara çizgisine değen silik doku çizgileri): yazı değil
            if (fillr < 0.15 and max(ww, hh) > 2.5 * th) or (fillr < 0.25 and hh > 2.2 * th):
                continue
            # deliğinin içi alttaki renk değil, başka bir renkle dolu halka (konturlu nokta): işaret
            delik = ndimage.binary_fill_holes(comp) & (comp == 0)
            if int(delik.sum()) >= max(6, 0.15 * area):
                if float((labels[y:y + hh, x:x + ww][delik] != under[y:y + hh, x:x + ww][delik]).mean()) >= 0.7:
                    isaret[i] = True
                    continue
            # iki belirgin renkten oluşan parça (koyu konturlu kırmızı nokta): harf tek renktir
            lb_ = labels[y:y + hh, x:x + ww][comp > 0]
            ub_ = under[y:y + hh, x:x + ww][comp > 0]
            ay_ = lb_[(lb_ != ub_) & (lb_ < K)]
            if len(ay_):
                vals_, cnts_ = np.unique(ay_, return_counts=True)
                if len(vals_) >= 2:
                    o_ = np.argsort(-cnts_)
                    p1_, p2_ = pal[vals_[o_[0]]], pal[vals_[o_[1]]]
                    c1_, c2_ = float(np.hypot(p1_[1], p1_[2])), float(np.hypot(p2_[1], p2_[2]))
                    if cnts_[o_[1]] >= 0.25 * area and max(c1_, c2_) >= 30 and float(np.linalg.norm(p1_ - p2_)) > 40:
                        # renkli kısım içi dolu bir leke olmalı (konturlu nokta); iki renkli çizgi/yazı değil
                        kr_ = vals_[o_[0]] if c1_ >= c2_ else vals_[o_[1]]
                        ko_ = vals_[o_[1]] if c1_ >= c2_ else vals_[o_[0]]
                        lw_ = labels[y:y + hh, x:x + ww]
                        rm_ = ((lw_ == kr_) & (comp > 0)).astype(np.uint8)
                        dr_ = float(cv2.distanceTransform(np.pad(rm_, 1), cv2.DIST_L2, 5).max())
                        # (öbür renk onu çevreler: kontur)
                        kb_ = (cv2.dilate(np.pad(rm_, 2), np.ones((3, 3), np.uint8))[2:-2, 2:-2] > 0) & (rm_ == 0)
                        cev_ = float((lw_[kb_] == ko_).mean()) if kb_.any() else 0.0
                        # renkli kısım yuvarlak dolu leke (kalın harf değil)
                        ry2_, rx2_ = np.nonzero(rm_)
                        bw2_, bh2_ = (np.ptp(rx2_) + 1, np.ptp(ry2_) + 1) if len(rx2_) else (1, 1)
                        dolu_ = len(rx2_) / float(bw2_ * bh2_)
                        if dr_ >= max(2.5, 0.15 * th) and cev_ >= 0.5 and dolu_ >= 0.6 \
                                and max(bw2_, bh2_) <= 1.5 * min(bw2_, bh2_):
                            isaret[i] = True
                            continue
            if area >= 5:
                py_, px_ = np.nonzero(comp)
                P_ = np.vstack([px_, py_]).astype(np.float64)
                ev, evec = np.linalg.eigh(np.cov(P_))
                ax_ = evec[:, 1]
                Lp = math.sqrt(12.0 * max(ev[1], 0.0))
                ang = math.degrees(math.atan2(abs(ax_[1]), abs(ax_[0])))
                res = np.abs((P_ - P_.mean(axis=1, keepdims=True)).T @ evec[:, 0])
                if (math.sqrt(max(ev[0], 0.0)) <= 1.0 and float(res.max()) <= 1.8 and Lp >= max(6.0, 0.7 * th)
                        and 10.0 <= ang <= 72.0):
                    # eğik, düz, ince parça: satır yalnız bunlardan oluşuyorsa (sütunlar arasından
                    # geçen veri çizgisinin parçaları) yazı değildir; harflerin arasındaysa harftir
                    cizgisel[i] = True
                elif area >= 12 and Lp >= max(10.0, 1.2 * th) and 10.0 <= ang <= 72.0:
                    # uçlarında yuvarlak işaret duran düz çizgi parçası (ızgara çizgisinin böldüğü veri
                    # çizgisinin iki işaret arasındaki parçası): iskeleti tek düz çizgi, kalınlığı ince
                    sk_ = skeletonize(comp > 0)
                    sy_, sx_ = np.nonzero(sk_)
                    if len(sx_) >= 6:
                        S_ = np.vstack([sx_, sy_]).astype(np.float64)
                        sev, sevec = np.linalg.eigh(np.cov(S_))
                        sres = np.abs((S_ - S_.mean(axis=1, keepdims=True)).T @ sevec[:, 0])
                        dtk = cv2.distanceTransform(np.pad(comp, 1), cv2.DIST_L2, 5)[1:-1, 1:-1]
                        if float(sres.max()) <= 1.5 and 2.0 * float(np.median(dtk[sk_])) <= max(3.0, 0.35 * th):
                            cizgisel[i] = True
            if not cizgisel[i] and area >= 12:
                # harf çizgisinden çok kalın yuvarlak leke (çizgi kökleri değen veri noktası): harf değil
                # (lekenin kalınlığı ona değen çizgi köklerinin belirgin üstünde)
                dtb = cv2.distanceTransform(np.pad(comp, 1), cv2.DIST_L2, 5)[1:-1, 1:-1]
                skb = skeletonize(comp > 0)
                if skb.any() and float(dtb.max()) >= max(2.0, 0.25 * th) \
                        and float(dtb.max()) >= 1.6 * float(np.median(dtb[skb])):
                    leke[i] = True
            glyphish[i] = True
        return under, cand, n, cc, st, th, glyphish, cizgisel, leke, isaret

    r_ = _hazirla(small)
    if r_ is None:
        return np.zeros((h, w), bool), []
    th0, gl0, st0 = r_[5], r_[6], r_[4]
    # eksen çentiğine değen rakam (eksenle tek parça): düz çizgiler (eksen, çentik dışı) çıkarılınca
    # kalan, harf boyunda ve yanında başka harf bulunan parça yazıdır
    gi = np.flatnonzero(gl0)
    if len(gi):
        gx0, gy0 = st0[gi, 0], st0[gi, 1]
        gx1, gy1 = gx0 + st0[gi, 2], gy0 + st0[gi, 3]
        ek = np.zeros((h, w), bool)
        Lk = int(max(10, round(1.5 * th0)))
        for k in range(K):
            if k == bg or k == gk:
                continue
            bk = (labels == k) & ~small
            if not bk.any():
                continue
            bu = bk.astype(np.uint8)
            ln_ = (cv2.morphologyEx(bu, cv2.MORPH_OPEN, np.ones((1, Lk), np.uint8)) > 0) | \
                  (cv2.morphologyEx(bu, cv2.MORPH_OPEN, np.ones((Lk, 1), np.uint8)) > 0)
            if not ln_.any():
                continue
            res_ = bk & ~(cv2.dilate(ln_.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
            if not res_.any():
                continue
            nr, cr, sr, _ = cv2.connectedComponentsWithStats(res_.astype(np.uint8), connectivity=8)
            for j in range(1, nr):
                x, y, ww, hh, area = sr[j]
                if not (0.6 * th0 <= hh <= 1.4 * th0 and ww <= 1.3 * th0 and area >= 4):
                    continue
                if area / float(ww * hh) >= 0.82:
                    continue
                ov = np.minimum(gy1, y + hh) - np.maximum(gy0, y)
                gap = np.maximum(gx0 - (x + ww), x - gx1)
                if not ((ov >= 0.5 * np.minimum(gy1 - gy0, hh)) & (gap <= 0.7 * th0)).any():
                    continue
                ek[y:y + hh, x:x + ww] |= cr[y:y + hh, x:x + ww] == j
        if ek.any():
            small = small | ek
            r_ = _hazirla(small)
            if r_ is None:
                return np.zeros((h, w), bool), []
    under, cand, n, cc, st, th, glyphish, cizgisel, leke, isaret = r_
    # ince bir çizginin kestiği şekil parçası (sütunun kenar çizgisinin, eksenin üstünden geçen
    # veri çizgisiyle ayrılan ucu): çizginin öbür yanında aynı renk sürüyorsa harf değildir
    kesik = np.zeros(n, bool)
    uzun_ince = np.zeros((h, w), bool)
    ince_lab = np.full((h, w), -1, np.int32)
    ker5 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    for j in range(K):
        if j == bg or j == gk:
            continue
        mj = (labels == j).astype(np.uint8)
        if not mj.any():
            continue
        tj = (mj > 0) & ~(cv2.morphologyEx(mj, cv2.MORPH_OPEN, ker5) > 0)
        if not tj.any():
            continue
        nj, cj, sj, _ = cv2.connectedComponentsWithStats(tj.astype(np.uint8), connectivity=8)
        uz = np.maximum(sj[:, cv2.CC_STAT_WIDTH], sj[:, cv2.CC_STAT_HEIGHT]) >= max(12.0, 2.5 * th)
        uz[0] = False
        sel_ = uz[cj]
        uzun_ince |= sel_
        ince_lab[sel_] = j
    if uzun_ince.any():
        k3 = np.ones((3, 3), np.uint8)
        for i in range(1, n):
            x, y, ww, hh, area = st[i]
            if area < 3:
                continue
            a0, b0, a1, b1 = max(0, x - 5), max(0, y - 5), min(w, x + ww + 5), min(h, y + hh + 5)
            P = cc[b0:b1, a0:a1] == i
            lw = labels[b0:b1, a0:a1]
            kp = int(np.bincount(np.clip(lw[P], 0, K), minlength=K + 1).argmax())
            if kp >= K or kp == bg:
                continue
            # köprü, parçanın durduğu zeminin rengi olamaz (yazı ile kutu kenarı arasındaki dar zemin
            # şeridi çizgi değildir)
            ku = int(np.bincount(np.clip(under[b0:b1, a0:a1][P], 0, K - 1), minlength=K).argmax())
            il_ = ince_lab[b0:b1, a0:a1]
            kopru = uzun_ince[b0:b1, a0:a1] & (il_ != kp) & (il_ != ku) & ~P
            if not (cv2.dilate(P.astype(np.uint8), k3).astype(bool) & kopru).any():
                continue
            G = P.copy()
            for _it in range(3):
                G = (cv2.dilate(G.astype(np.uint8), k3) > 0) & (kopru | P)
            ote = (cv2.dilate((G & ~P).astype(np.uint8), k3) > 0) & (lw == kp) & ~P
            if ote.any():
                glyphish[i] = False
                kesik[i] = True
    kw = max(3, int(round(0.7 * th)) | 1)
    kh = max(1, int(round(0.2 * th)) | 1)
    lines_m = cv2.dilate(cand.astype(np.uint8), np.ones((kh, kw), np.uint8))
    ln, lcc, lst, _ = cv2.connectedComponentsWithStats(lines_m, connectivity=8)
    has_glyph = np.zeros(ln, bool)
    gl_lab = np.unique(lcc[glyphish[cc] & cand])
    has_glyph[gl_lab] = True
    has_glyph[0] = False
    # tek, çok küçük parçalı "satır" (çizgilerin kesiştiği yerdeki karışım renkli birkaç piksel) ve
    # harf biçimli parçalarının hepsi eğik düz çizgi parçası olan satır yazı değildir
    for i in np.flatnonzero(has_glyph):
        x, y, ww, hh, _a = lst[i]
        ids_ = np.unique(cc[y:y + hh, x:x + ww][(lcc[y:y + hh, x:x + ww] == i) & cand[y:y + hh, x:x + ww]])
        ids_ = ids_[ids_ > 0]
        if len(ids_) == 1 and (st[ids_[0], cv2.CC_STAT_HEIGHT] < 0.6 * th or st[ids_[0], cv2.CC_STAT_AREA] < 8):
            has_glyph[i] = False
            continue
        gl_ = ids_[glyphish[ids_]]
        # (birkaç piksellik parçalar karar vermez: kalın çizginin kenarındaki karışım renkli kırıntılar)
        gl_ = gl_[st[gl_, cv2.CC_STAT_AREA] >= 5]
        # (kalın yuvarlak leke ancak yanında böyle bir çizgi parçası varsa: çizginin üstündeki işaret)
        if len(gl_) and (cizgisel[gl_] | leke[gl_]).all() and cizgisel[gl_].any():
            has_glyph[i] = False
    # yalnız dik çubuklardan oluşan kısa satır (Romen rakamı I, II, III): harf biçimi aranmaz
    for i in range(1, ln):
        if has_glyph[i]:
            continue
        x, y, ww, hh, _a = lst[i]
        if hh < 0.6 * th or hh > 2.2 * th or ww > 1.8 * hh:
            continue
        ids = np.unique(cc[y:y + hh, x:x + ww][(lcc[y:y + hh, x:x + ww] == i) & cand[y:y + hh, x:x + ww]])
        ids = ids[ids > 0]
        if not (1 <= len(ids) <= 12):
            continue
        bw, bh = st[ids, cv2.CC_STAT_WIDTH], st[ids, cv2.CC_STAT_HEIGHT]
        # harf sapı incedir (dar sütun ya da kutu değil)
        bar = (bh >= np.maximum(6, 4 * bw)) & (bw <= max(3.0, 0.3 * th))
        if not bar.any():
            continue
        Hb = float(bh[bar].max())
        # en çok bir nokta (I. II. gibi madde numarası): çubuk kalınlığında, aynı renkte
        Wb = float(np.median(bw[bar]))
        lab_ids = np.array([int(np.bincount(labels[st[j, 1]:st[j, 1] + st[j, 3], st[j, 0]:st[j, 0] + st[j, 2]][
            cc[st[j, 1]:st[j, 1] + st[j, 3], st[j, 0]:st[j, 0] + st[j, 2]] == j]).argmax()) for j in ids])
        lb0 = int(np.bincount(lab_ids[bar]).argmax())
        ayni = np.array([np.linalg.norm(pal[min(lv, K - 1)] - pal[min(lb0, K - 1)]) < 25 for lv in lab_ids])
        dot = ~bar & (np.maximum(bw, bh) <= min(0.45 * Hb, 2.5 * Wb + 1)) & ayni
        if (bar | dot).all() and dot.sum() <= 1 and bh[bar].max() <= 1.25 * bh[bar].min() \
                and bh[bar].min() >= 0.6 * th:
            has_glyph[i] = True
    ink = np.zeros((h, w), bool)
    lines = []
    for i in range(1, ln):
        if not has_glyph[i]:
            continue
        x, y, ww, hh, _a = lst[i]
        p = 2
        a0, b0, a1, b1 = max(0, x - p), max(0, y - p), min(w, x + ww + p), min(h, y + hh + p)
        reg = lcc[b0:b1, a0:a1] == i
        cm = cand[b0:b1, a0:a1] & reg
        if not cm.any():
            continue
        # uzun ince parçalar (satırın içinden geçen çizginin kopuk parçaları) yazı değildir
        ids0 = np.unique(cc[b0:b1, a0:a1][cm])
        ids0 = ids0[ids0 > 0]
        if len(ids0):
            w0_, h0_ = st[ids0, cv2.CC_STAT_WIDTH], st[ids0, cv2.CC_STAT_HEIGHT]
            # (konturlu renkli nokta gibi iki renkli işaretler de yazı değildir)
            cizgi_p = ids0[((np.maximum(w0_, h0_) > 2.0 * th) & (np.minimum(w0_, h0_) <= 3)) | kesik[ids0] | isaret[ids0]]
            if len(cizgi_p):
                cm &= ~np.isin(cc[b0:b1, a0:a1], cizgi_p)
                if not cm.any():
                    continue
                if not glyphish[np.unique(cc[b0:b1, a0:a1][cm])].any():
                    continue
        # halka biçimli satır (bir dairenin kopuk konturu) yazı değildir
        rf = ndimage.binary_fill_holes(reg)
        if float(rf.sum()) > 1.4 * float(reg.sum()):
            continue
        # kesik çizgi (oku ile): parçaların çoğu satır yönünde uzamış ince çizgicikler
        ids = np.unique(cc[b0:b1, a0:a1][cm])
        ids = ids[ids > 0]
        horiz = ww >= hh
        sw_, sh_ = st[ids, cv2.CC_STAT_WIDTH], st[ids, cv2.CC_STAT_HEIGHT]
        if horiz:
            dash = (sw_ >= 1.4 * sh_) & (sh_ <= 3)
        else:
            dash = (sh_ >= 1.4 * sw_) & (sw_ <= 3)
        if dash.sum() >= 3 and dash.sum() >= 0.5 * len(ids):
            continue
        # yazının rengi: harf biçimli parçaların çoğunluk rengi; bu renkten belirgin farklı parçalar
        # (yazının yanındaki renkli işaret kutusu, lejant karesi) yazı değildir
        lab_w = labels[b0:b1, a0:a1]
        glm = cm & glyphish[cc[b0:b1, a0:a1]]
        if glm.any():
            L0 = int(np.bincount(np.clip(lab_w[glm], 0, K - 1), minlength=K).argmax())
            u0 = int(np.bincount(under[b0:b1, a0:a1][cm], minlength=K).argmax())
            # yazı rengi ya da yazı ile alttaki rengin karışımı (bulanık harf kenarı)
            AB = pal[L0] - pal[u0]
            nab = float(AB @ AB)
            if nab > 1e-6:
                t_ = np.clip((pal - pal[u0]) @ AB / nab, 0, 1)
                blend = (np.linalg.norm(pal - (pal[u0] + t_[:, None] * AB), axis=1) < 20) & (t_ >= 0.2)
            else:
                blend = np.zeros(K, bool)
            # yazı zeminden belirgin ayrışır: alttaki renge ve zemine çok yakın "yazı" silik dokudur
            if float(np.linalg.norm(pal[L0] - pal[u0])) < 20 and float(np.linalg.norm(pal[L0] - pal[bg])) < 25:
                continue
            okl = (np.linalg.norm(pal - pal[L0], axis=1) < 20) | blend
            okl = np.append(okl, False)
            cm = cm & okl[np.clip(lab_w, 0, K)]
            # harf biçimli olmayan, harflerden çok büyük parça (yazının yanındaki dolu kutu) yazı değil
            ids_ = np.unique(cc[b0:b1, a0:a1][cm])
            ids_ = ids_[ids_ > 0]
            ga = st[ids_[glyphish[ids_]], cv2.CC_STAT_AREA]
            if len(ga):
                big_ = ids_[~glyphish[ids_] & (st[ids_, cv2.CC_STAT_AREA] > 4 * float(np.median(ga)))]
                if len(big_):
                    cm &= ~np.isin(cc[b0:b1, a0:a1], big_)
            if not cm.any():
                continue
        u = under[b0:b1, a0:a1][cm]
        un = int(np.bincount(u, minlength=K).argmax())
        # ara renkler: harfe değen, alttaki renkten biraz da olsa farklı pikseller
        near = cv2.dilate(cm.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        dd = np.linalg.norm(lab[b0:b1, a0:a1] - pal[un], axis=2)
        im = cm | (near & (dd > 10) & small[b0:b1, a0:a1])
        ink[b0:b1, a0:a1] |= im
        lines.append(((a0, b0, a1, b1), un, im))
    # satırın hemen üstünde/altında kalan küçük işaretler (şapka, nokta, çengel): satıra katılır
    if lines:
        kalan = cand & ~ink
        if kalan.any():
            nk, ck, sk, _ = cv2.connectedComponentsWithStats(kalan.astype(np.uint8), connectivity=8)
            ekle = {}
            for j in range(1, nk):
                x, y, ww, hh, _a = sk[j]
                if max(ww, hh) > 0.6 * th:
                    continue
                cx, cy = x + ww / 2, y + hh / 2
                for li, ((a0, b0, a1, b1), un, im) in enumerate(lines):
                    if a0 <= cx <= a1 and b0 - 0.7 * th <= cy <= b1 + 0.7 * th and not (b0 <= cy <= b1):
                        ekle.setdefault(li, []).append(j)
                        break
            for li, js in ekle.items():
                (a0, b0, a1, b1), un, im = lines[li]
                sel = np.isin(ck, js)
                ys, xs = np.nonzero(sel)
                na0, nb0 = min(a0, int(xs.min()) - 1), min(b0, int(ys.min()) - 1)
                na1, nb1 = max(a1, int(xs.max()) + 2), max(b1, int(ys.max()) + 2)
                na0, nb0, na1, nb1 = max(0, na0), max(0, nb0), min(w, na1), min(h, nb1)
                im2 = np.zeros((nb1 - nb0, na1 - na0), bool)
                im2[b0 - nb0:b1 - nb0, a0 - na0:a1 - na0] = im
                im2 |= sel[nb0:nb1, na0:na1]
                ink[nb0:nb1, na0:na1] |= im2
                lines[li] = ((na0, nb0, na1, nb1), un, im2)
    return ink, lines


def _cerceveler(lab, rgb, pal, bg, ink, h, w):
    """İçi boş (zemin ya da çok açık renk) kutuların çerçeveleri.

    Çerçeve, iç boşluğu çevreleyen ince, belirgin bant olarak bulunur (bant boyunca renk
    değişebilir: üst kenar açık, yan kenar koyu olabilir). İç boşluğa temiz şekil oturtulur,
    çizginin ortasına taşınır. Dönüş: [(nesne, bant pikselleri, iç piksel)]
    """
    out = []
    d_bg = np.linalg.norm(lab - pal[bg], axis=2)
    R = (d_bg > 18) & ~ink
    if not R.any():
        return out
    dt = cv2.distanceTransform(np.pad(R.astype(np.uint8), 1), cv2.DIST_L2, 5)[1:-1, 1:-1]
    core = dt > 4.5
    big = (cv2.dilate(core.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))) > 0) & R
    Lthin = R & ~big
    if not Lthin.any():
        return out
    # boşluğu çevreleyen kalın şekiller de (ölçek çubuğunun dolu parçaları) kapatır; çerçeve
    # rengi ve kalınlığı yalnız ince çizgiden ölçülür
    L = R
    n, cc, st, _ = cv2.connectedComponentsWithStats(L.astype(np.uint8), connectivity=8)
    for i in range(1, n):
        x, y, ww, hh, area = st[i]
        if ww < 10 or hh < 8 or area < 30:
            continue
        p = 3
        a0, b0, a1, b1 = max(0, x - p), max(0, y - p), min(w, x + ww + p), min(h, y + hh + p)
        comp = cc[b0:b1, a0:a1] == i
        holes = ndimage.binary_fill_holes(comp) & ~comp
        if not holes.any():
            continue
        hl, hn = ndimage.label(holes)
        for j in range(1, hn + 1):
            inter = hl == j
            ia = int(inter.sum())
            if ia < 60:
                continue
            ys, xs = np.nonzero(inter)
            if np.ptp(xs) < 8 or np.ptp(ys) < 6:
                continue
            # iç boşluk zemin ya da çok açık renk olmalı (dolgulu kutunun konturu ayrıca bulunur)
            dsub = d_bg[b0:b1, a0:a1]
            isub = ink[b0:b1, a0:a1]
            inner = inter & ~(cv2.dilate(isub.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
            if inner.sum() < 0.5 * ia or (dsub[inner] < 15).mean() < 0.85:
                continue
            # iç sınır: çerçeveye bakan kenarda kısmi kaplama
            band_in = (cv2.dilate(inter.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & ~inter
            # çerçeve bandı: iç sınırın hemen dışındaki ince çizgi (değen bağlantı çizgileri ve
            # yanındaki kalın şekiller çerçeve değildir)
            far = cv2.dilate(inter.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
            ring = comp & far & Lthin[b0:b1, a0:a1]
            if ring.sum() < 8:
                continue
            ring_d = float(np.percentile(dsub[ring], 75))
            if ring_d < 20:
                continue
            soft = inter.astype(np.float32)
            soft[band_in] = np.clip(1.0 - dsub[band_in] / ring_d, 0, 1)
            prim = sekil.uydur(soft, a0, b0, kinds=("rect", "rrect", "ellipse"), tol_px=1.0, min_iou=0.95)
            if prim is None:
                continue
            # boşluğun çevresinin çoğu ince çizgi olmalı (iki sütun arasındaki boşluk çerçeve değil)
            kenar_in = band_in & (cv2.dilate(ring.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
            if kenar_in.sum() < 0.7 * band_in.sum():
                continue
            pts = sekil.prim_points(prim)
            # kenarların rengi aynı olmalı (açık/koyu farkı olabilir, renk tonu değil): ızgara
            # çizgileriyle başka renkte bir okun çevirdiği boşluk çerçeve değildir
            ry_, rx_ = np.nonzero(ring)
            rab = lab[b0:b1, a0:a1][ring][:, 1:3]
            # (yalnız belirgin kenar pikselleri: yumuşak kenar iç renkle karışır)
            gl_ = dsub[ring] >= np.percentile(dsub[ring], 60)
            ry_, rx_, rab = ry_[gl_], rx_[gl_], rab[gl_]
            px0, py0 = pts.min(axis=0) - [a0, b0]
            px1, py1 = pts.max(axis=0) - [a0, b0]
            dk = np.stack([np.abs(rx_ - px0), np.abs(rx_ - px1), np.abs(ry_ - py0), np.abs(ry_ - py1)], axis=1)
            yan = dk.argmin(axis=1)
            orta = [np.median(rab[yan == q], axis=0) for q in range(4) if (yan == q).sum() >= 4]
            if len(orta) >= 2 and max(float(np.linalg.norm(u - v)) for u in orta for v in orta) > 20:
                continue
            per = float(np.sum(np.hypot(*np.diff(np.vstack([pts, pts[:1]]), axis=0).T)))
            per_thin = per * float(kenar_in.sum()) / max(1.0, float(band_in.sum()))
            mass = float(np.clip(dsub[ring] / ring_d, 0, 1).sum())
            wd = float(np.clip(mass / max(per_thin, 1.0), 0.6, 6.0))
            cprim = sekil.grow(prim, wd / 2)
            # çerçeve kesintisiz mi: orta hat boyunca örnekle
            cp = sekil.prim_points(cprim)
            seg = np.vstack([cp, cp[:1]])
            samp = []
            for q0, q1 in zip(seg[:-1], seg[1:]):
                nseg = max(1, int(np.hypot(*(q1 - q0))))
                for t in np.linspace(0, 1, nseg, endpoint=False):
                    samp.append(q0 + (q1 - q0) * t)
            samp = np.array(samp)
            rr = int(math.ceil(wd / 2 + 1))
            hit = 0
            for qx, qy in samp:
                ix0, iy0 = int(round(qx)), int(round(qy))
                win = d_bg[max(0, iy0 - rr):iy0 + rr + 1, max(0, ix0 - rr):ix0 + rr + 1]
                if win.size and win.max() >= 0.5 * ring_d:
                    hit += 1
            if hit < 0.9 * len(samp):
                continue
            # renkler: çerçeve en belirgin piksellerin ortancası; iç: ortanca (ya da zemin)
            rs = rgb[b0:b1, a0:a1][ring]
            rd = dsub[ring]
            ring_col = tuple(int(v) for v in np.median(rs[rd >= np.percentile(rd, 60)], axis=0))
            ic = np.median(rgb[b0:b1, a0:a1][inner], axis=0)
            il = np.median(lab[b0:b1, a0:a1][inner], axis=0)
            fill_col = tuple(int(v) for v in ic) if np.linalg.norm(il - pal[bg]) >= 2.5 else _lab_to_rgb(pal[bg])
            el = Element("fill", fill_col, prim=cprim, area=float(ia),
                         bbox=(*map(float, cp.min(axis=0)), *map(float, cp.max(axis=0))))
            el.stroke, el.stroke_width = ring_col, wd
            # iç renk yavaşça değişiyorsa (açık maviden beyaza) iki duraklı geçiş
            g = _ic_gecis(lab[b0:b1, a0:a1], rgb[b0:b1, a0:a1], inner, a0, b0)
            if g is not None:
                el.grad = g
            # çizilen çerçevenin altında kalan her şey (kopuk köşe parçaları dahil) bu nesnenin
            band = np.zeros((h, w), np.uint8)
            q = np.round(np.vstack([cp, cp[:1]]) * 16).astype(np.int32)
            cv2.polylines(band, [q], False, 1, thickness=max(1, int(round(wd + 4))), lineType=cv2.LINE_8, shift=4)
            # yanındaki kalın şekillere (ölçek çubuğunun dolu parçası) dokunmaz
            band = band.astype(bool) & ~big
            full_in = np.zeros((h, w), bool)
            full_in[b0:b1, a0:a1] = inter
            out.append((el, band, full_in))
    return out


def _ic_gecis(lab, rgb, inner, a0, b0):
    """Kutunun içindeki yumuşak renk geçişi (doğrusal): yoksa None."""
    ys, xs = np.nonzero(inner)
    if len(xs) < 200:
        return None
    L = lab[inner]
    best = None
    for axis, coord in ((0, xs), (1, ys)):
        t = (coord - coord.min()) / max(1, np.ptp(coord))
        A = np.column_stack([t, np.ones_like(t)])
        coef, res, *_ = np.linalg.lstsq(A, L, rcond=None)
        span = float(np.linalg.norm(coef[0]))
        resid = float(np.sqrt(np.mean(np.sum((L - A @ coef) ** 2, axis=1))))
        if best is None or span > best[0]:
            best = (span, resid, axis, coord, coef)
    span, resid, axis, coord, coef = best
    if span < 3.0 or resid > 0.45 * span:
        return None
    lo, hi = coord.min(), coord.max()
    c0 = _lab_to_rgb(coef[1])
    c1 = _lab_to_rgb(coef[0] + coef[1])
    if axis == 0:
        g = {"type": "linear", "x1": float(lo + a0), "y1": float(b0), "x2": float(hi + a0), "y2": float(b0)}
    else:
        g = {"type": "linear", "x1": float(a0), "y1": float(lo + b0), "x2": float(a0), "y2": float(hi + b0)}
    g["stops"] = [(0.0, c0), (1.0, c1)]
    return g


def _glyph_mask2(present, labels, dark, h, w):
    """Harf benzeri bileşenler (yalnız koyu renklerde): boy, doluluk ve çizgi kalınlığına göre."""
    out = np.zeros((h, w), bool)
    for k in dark:
        m = present[k].astype(np.uint8)
        n, cc, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        if n <= 1:
            continue
        dt = cv2.distanceTransform(np.pad(m, 1), cv2.DIST_L2, 3)[1:-1, 1:-1]
        mx = ndimage.maximum(dt, cc, index=np.arange(n))
        for i in range(1, n):
            x, y, ww, hh, area = stats[i]
            if hh < 5 or hh > max(0.15 * h, 40) or ww > 10 * hh:
                continue
            fillr = area / float(ww * hh)
            thick = 2 * mx[i]
            if fillr > 0.8 or (fillr < 0.06 and ww > 3):
                continue
            if thick > 0.45 * hh:
                continue
            out[y:y + hh, x:x + ww] |= cc[y:y + hh, x:x + ww] == i
        # noktalar ve şapkalar (i, ö, ğ…): harfe yakın minik parçalar
        if out.any():
            near = cv2.dilate(out.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
            for i in range(1, n):
                x, y, ww, hh, area = stats[i]
                if area <= 12 and max(ww, hh) <= 5:
                    comp = cc[y:y + hh, x:x + ww] == i
                    if (near[y:y + hh, x:x + ww] & comp).any():
                        out[y:y + hh, x:x + ww] |= comp
    return out

