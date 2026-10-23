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

from . import egri, sadakat


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
            if gap > max(6 * u, 2.5 * max(lens[i], lens[j], 2 * u)) or gap < -u:
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
    out, used = [], set()
    for g in groups.values():
        if len(g) < 3:
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
        if len(dz) >= 3 and (dz.std() > 0.45 * max(dz.mean(), 1e-6) or gz.std() > 0.45 * max(gz.mean(), 1e-6)) \
                and float(np.median(gz)) > 0.8:
            continue
        w = float(np.median([segs[i][2] for i in g]))
        p0 = c + d * t.min()
        p1 = c + d * t.max()
        out.append((p0, p1, w, dashes, gaps))
        used.update(g)
    return out, used


def _dash_pattern(dashes: list, gaps: list, w: float):
    """Kesik desenini çıkar: düz kesik, nokta ya da kesik-nokta."""
    dash = np.array(dashes)
    gap = float(np.median(gaps))
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
    bbox = (*pts0.min(axis=0), *pts0.max(axis=0))
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
        if len(ys) < 40 or min(y1 - y0, x1 - x0) < 4:
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


def vectorize(rgb: np.ndarray, opts: Options | None = None) -> Scene:
    opts = opts or Options()
    H, W = rgb.shape[:2]
    side = max(H, W)
    # Büyütülmüş (ör. Retina ekran görüntüsü) görselleri normal ölçeğe, çok büyükleri 2200 piksele küçült
    shrink = 1.0
    th = stroke_width(rgb)
    if th > 2.6:
        shrink = 1.6 / th
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
    scene = Scene(w, h, background=colors[bg])
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
    dark = [k for k in range(K) if k != bg and pal[k][0] < 55]
    glyph = _glyph_mask2(present, labels, dark, h, w) & ~text_mask if opts.glyphs else np.zeros((h, w), bool)
    if text_mask.any() and glyph.any():
        # yazı kutusundaki harflerle aynı parçaya ait harf kalıntılarını da yazı say
        n_g, cc_g = cv2.connectedComponents((glyph | text_mask).astype(np.uint8), connectivity=8)
        hit = np.zeros(n_g, bool)
        hit[np.unique(cc_g[text_mask])] = True
        hit[0] = False
        extra = hit[cc_g] & glyph
        text_mask |= extra
        glyph &= ~extra

    # --- her rengin ince (çizgi) ve kalın (dolgu) kısmı
    core_r = opts.thin_px / 2 + 0.45
    thin_by = {}
    thick_by = {}
    thin_all = np.zeros((h, w), bool)
    for k in range(K):
        if k == bg or k == gk:
            continue
        m = (labels == k) & ~text_mask & ~glyph
        if m.sum() < 1:
            continue
        mu = m.astype(np.uint8)
        dt = cv2.distanceTransform(np.pad(mu, 1), cv2.DIST_L2, 5)[1:-1, 1:-1]
        core = dt >= core_r
        if core.any():
            rr = int(math.ceil(core_r))
            ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rr + 1, 2 * rr + 1))
            thick = (cv2.dilate(core.astype(np.uint8), ker) > 0) & m
        else:
            thick = np.zeros_like(m)
        # ince kısım: rengin %30'dan fazla kapladığı (soluk kenarlı çizgiler kopmasın), kalın olmayan pikseller
        thick_g = cv2.dilate(thick.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        thin = present[k] & ~thick_g & ~text_mask & ~glyph
        # kalın şeklin kenarındaki 1-2 piksellik pürüzleri çizgi sayma
        if thin.any() and thick.any():
            n, cc, stats, _ = cv2.connectedComponentsWithStats(thin.astype(np.uint8), connectivity=8)
            near_thick = cv2.dilate(thick.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
            touch = np.zeros(n, bool)
            touch[np.unique(cc[near_thick & thin])] = True
            big = np.maximum(stats[:, cv2.CC_STAT_WIDTH], stats[:, cv2.CC_STAT_HEIGHT])
            drop = touch & (big <= 3)
            drop[0] = False
            if drop.any():
                thin &= ~drop[cc]
        thin_by[k] = thin
        thick_by[k] = thick_g
        thin_all |= thin

    # --- dolgu etiketleri: çizgi, yazı ve harf piksellerinin altını çevredeki renkle doldur
    hide = thin_all | text_mask | glyph
    fill_lab = labels.copy()
    if hide.any() and not hide.all():
        _, (iy, ix) = ndimage.distance_transform_edt(hide, return_indices=True)
        fill_lab[hide] = labels[iy[hide], ix[hide]]
    near_hide = cv2.dilate(hide.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0

    elements = []
    # --- renk geçişli bölgeler
    for m, g in grads:
        conts = _contours_of(_up(cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.6), f), f, 0, 0, 2.0)
        el = _fill_element(conts, tuple(int(v) for v in g["stops"][len(g["stops"]) // 2][1]), tol, shapes=False)
        if el:
            el.grad = g
            el.layer = "alt"
            elements.append(el)
    # --- dolgular
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
        for i in range(1, n):
            x, y, ww, hh, area = stats[i]
            # çok küçük, soluk kırıntılar (kenar yumuşatmasından kalan) çizilmez
            if area < 3 or (area < 6 and cov[k, y:y + hh, x:x + ww][cc[y:y + hh, x:x + ww] == i].mean() < 0.75):
                continue
            p = 2
            a0, b0, a1, b1 = max(0, x - p), max(0, y - p), min(w, x + ww + p), min(h, y + hh + p)
            comp = cc[b0:b1, a0:a1] == i
            reach = cv2.dilate(comp.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
            c = np.where(reach, fc[b0:b1, a0:a1], 0.0)
            conts = _contours_of(_up(c, f), f, a0, b0, 0.8)
            el = _fill_element(conts, colors[k], tol)
            if el:
                elements.append(el)

    # --- harfler: kendi kaplamalarından, köşeleri koruyarak
    if glyph.any():
        for k in range(K):
            gm = glyph & present[k]
            if not gm.any():
                continue
            n, cc, stats, _ = cv2.connectedComponentsWithStats(gm.astype(np.uint8), connectivity=8)
            for i in range(1, n):
                x, y, ww, hh, area = stats[i]
                p = 2
                a0, b0, a1, b1 = max(0, x - p), max(0, y - p), min(w, x + ww + p), min(h, y + hh + p)
                comp = cc[b0:b1, a0:a1] == i
                reach = cv2.dilate(comp.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
                c = np.where(reach, cov[k, b0:b1, a0:a1], 0.0)
                # 1 pikselden ince, kenarı yumuşatılmış harfler 0,5 eşiğinde kopar: onlarda eşik düşük
                sk = int(skeletonize(comp).sum())
                lev = 0.5 if float(c.sum()) / max(sk, 1) >= 1.4 else 0.4
                conts = _contours_of(np.clip(_up(c, f) * (0.5 / lev), 0, 1), f, a0, b0, 0.15)
                el = _fill_element(conts, colors[k], tol * 0.7, shapes=False, layer="harf")
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

    if opts.cizim:
        from . import duzen
        elements = duzen.cizimlestir(elements, colors[bg])
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
            return (1, -(e.bbox[2] - e.bbox[0] + e.bbox[3] - e.bbox[1]))
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
        pat, cap = _dash_pattern(dashes, gaps, wd2)
        if float(np.median(gaps)) < 0.8:
            pat, cap = None, "butt"     # aralıksız parçalar: düz çizgi (araya giren şekiller bölmüş)
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
        if prec >= 0.75:
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

