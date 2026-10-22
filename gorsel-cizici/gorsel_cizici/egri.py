"""Eğri uydurma: noktalardan düz çizgi, çember yayı ve Bézier eğrisi çıkarma.

Bütün fonksiyonlar (N, 2) biçiminde numpy dizileriyle çalışır (x, y).
"""
from __future__ import annotations

import math

import numpy as np


# ---------------------------------------------------------------- yardımcılar
def rdp(pts: np.ndarray, eps: float) -> np.ndarray:
    """Ramer–Douglas–Peucker sadeleştirmesi (açık çizgi)."""
    pts = np.asarray(pts, dtype=float)
    if len(pts) < 3:
        return pts
    keep = np.zeros(len(pts), dtype=bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        p, q = pts[a], pts[b]
        seg = pts[a + 1:b]
        d = q - p
        n = math.hypot(*d)
        if n < 1e-9:
            dist = np.hypot(*(seg - p).T)
        else:
            dist = np.abs(d[0] * (seg[:, 1] - p[1]) - d[1] * (seg[:, 0] - p[0])) / n
        i = int(np.argmax(dist))
        if dist[i] > eps:
            k = a + 1 + i
            keep[k] = True
            stack.append((a, k))
            stack.append((k, b))
    return pts[keep]


def line_fit(pts: np.ndarray):
    """En küçük kareler doğrusu: (merkez, yön, en büyük sapma)."""
    pts = np.asarray(pts, dtype=float)
    c = pts.mean(axis=0)
    u, s, vt = np.linalg.svd(pts - c, full_matrices=False)
    d = vt[0]
    n = np.array([-d[1], d[0]])
    dev = np.abs((pts - c) @ n)
    return c, d, float(dev.max()) if len(dev) else 0.0


def circle_fit(pts: np.ndarray):
    """Çember uydur (Kasa + birkaç Gauss–Newton adımı). (cx, cy, r, rms)"""
    pts = np.asarray(pts, dtype=float)
    if len(pts) < 3:
        return None
    x, y = pts[:, 0], pts[:, 1]
    A = np.column_stack([x, y, np.ones_like(x)])
    b = x * x + y * y
    try:
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    except np.linalg.LinAlgError:
        return None
    cx, cy = sol[0] / 2, sol[1] / 2
    r2 = sol[2] + cx * cx + cy * cy
    if not np.isfinite(r2) or r2 <= 0:
        return None
    r = math.sqrt(r2)
    for _ in range(5):
        dx, dy = x - cx, y - cy
        di = np.hypot(dx, dy)
        di[di < 1e-9] = 1e-9
        res = di - r
        J = np.column_stack([-dx / di, -dy / di, -np.ones_like(di)])
        try:
            step, *_ = np.linalg.lstsq(J, -res, rcond=None)
        except np.linalg.LinAlgError:
            break
        cx, cy, r = cx + step[0], cy + step[1], r + step[2]
        if np.abs(step).max() < 1e-4:
            break
    rms = float(np.sqrt(np.mean((np.hypot(x - cx, y - cy) - r) ** 2)))
    return float(cx), float(cy), float(abs(r)), rms


def smooth_closed(pts: np.ndarray, sigma: float) -> np.ndarray:
    """Kapalı konturu Gauss ile yumuşat (köşeler korunmaz; köşe bulmadan önce kullan)."""
    if sigma <= 0 or len(pts) < 5:
        return pts.astype(float)
    r = int(max(1, round(sigma * 3)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    out = np.empty_like(pts, dtype=float)
    for j in range(2):
        v = np.concatenate([pts[-r:, j], pts[:, j], pts[:r, j]]).astype(float)
        out[:, j] = np.convolve(v, k, mode="valid")
    return out


def smooth_open(pts: np.ndarray, sigma: float) -> np.ndarray:
    """Açık çizgiyi uçları sabit tutarak yumuşat."""
    if sigma <= 0 or len(pts) < 5:
        return pts.astype(float)
    r = int(max(1, round(sigma * 3)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    out = np.empty_like(pts, dtype=float)
    for j in range(2):
        v = np.concatenate([np.full(r, pts[0, j]), pts[:, j], np.full(r, pts[-1, j])]).astype(float)
        out[:, j] = np.convolve(v, k, mode="valid")
    out[0], out[-1] = pts[0], pts[-1]
    return out


def resample(pts: np.ndarray, step: float, closed: bool) -> np.ndarray:
    """Noktaları eşit aralıklı yeniden örnekle."""
    p = np.asarray(pts, dtype=float)
    if closed:
        p = np.vstack([p, p[:1]])
    d = np.hypot(*np.diff(p, axis=0).T)
    s = np.concatenate([[0], np.cumsum(d)])
    total = s[-1]
    if total < step * 2:
        return np.asarray(pts, dtype=float)
    n = max(3, int(round(total / step)))
    t = np.linspace(0, total, n + (0 if closed else 1), endpoint=not closed)
    x = np.interp(t, s, p[:, 0])
    y = np.interp(t, s, p[:, 1])
    return np.column_stack([x, y])


# ---------------------------------------------------------------- köşeler
def corners(pts: np.ndarray, closed: bool, k: int, angle_deg: float) -> list[int]:
    """Yön değişiminin keskin olduğu noktalar (eşit aralıklı noktalarda)."""
    n = len(pts)
    if n < 2 * k + 1:
        return []
    idx = np.arange(n)
    if closed:
        a = pts[(idx - k) % n]
        b = pts[(idx + k) % n]
    else:
        a = pts[np.clip(idx - k, 0, n - 1)]
        b = pts[np.clip(idx + k, 0, n - 1)]
    v1 = pts - a
    v2 = b - pts
    n1 = np.hypot(*v1.T) + 1e-9
    n2 = np.hypot(*v2.T) + 1e-9
    cosang = np.clip((v1 * v2).sum(axis=1) / (n1 * n2), -1, 1)
    ang = np.degrees(np.arccos(cosang))
    if not closed:
        ang[:k] = 0
        ang[n - k:] = 0
    out = []
    for i in range(n):
        if ang[i] < angle_deg:
            continue
        lo, hi = i - k, i + k
        window = [ang[j % n] if closed else ang[j] for j in range(lo, hi + 1) if closed or 0 <= j < n]
        if ang[i] >= max(window) - 1e-9:
            if not out or (i - out[-1]) > k:
                out.append(i)
    if closed and len(out) > 1 and (out[0] + n - out[-1]) <= k:
        out.pop()
    return out


# ---------------------------------------------------------------- Bézier (Schneider)
def _bezier(ctrl, t):
    t = t[:, None]
    mt = 1 - t
    return (mt ** 3) * ctrl[0] + 3 * (mt ** 2) * t * ctrl[1] + 3 * mt * (t ** 2) * ctrl[2] + (t ** 3) * ctrl[3]


def _bezier_d1(ctrl, t):
    t = t[:, None]
    mt = 1 - t
    return 3 * (mt ** 2) * (ctrl[1] - ctrl[0]) + 6 * mt * t * (ctrl[2] - ctrl[1]) + 3 * (t ** 2) * (ctrl[3] - ctrl[2])


def _bezier_d2(ctrl, t):
    t = t[:, None]
    return 6 * (1 - t) * (ctrl[2] - 2 * ctrl[1] + ctrl[0]) + 6 * t * (ctrl[3] - 2 * ctrl[2] + ctrl[1])


def _chord_params(pts):
    d = np.hypot(*np.diff(pts, axis=0).T)
    u = np.concatenate([[0], np.cumsum(d)])
    return u / u[-1] if u[-1] > 0 else np.linspace(0, 1, len(pts))


def _generate(pts, u, t1, t2):
    p0, p3 = pts[0], pts[-1]
    A1 = t1[None, :] * (3 * (1 - u) ** 2 * u)[:, None]
    A2 = t2[None, :] * (3 * (1 - u) * u ** 2)[:, None]
    C = np.array([[np.sum(A1 * A1), np.sum(A1 * A2)], [np.sum(A1 * A2), np.sum(A2 * A2)]])
    base = _bezier(np.array([p0, p0, p3, p3]), u)
    tmp = pts - base
    X = np.array([np.sum(A1 * tmp), np.sum(A2 * tmp)])
    det = C[0, 0] * C[1, 1] - C[0, 1] * C[1, 0]
    seg = math.hypot(*(p3 - p0))
    if abs(det) > 1e-12:
        a1 = (X[0] * C[1, 1] - X[1] * C[0, 1]) / det
        a2 = (C[0, 0] * X[1] - C[1, 0] * X[0]) / det
    else:
        a1 = a2 = seg / 3
    eps = 1e-6 * seg
    if a1 < eps or a2 < eps:
        a1 = a2 = seg / 3
    return np.array([p0, p0 + t1 * a1, p3 + t2 * a2, p3])


def _reparam(ctrl, pts, u):
    d = _bezier(ctrl, u) - pts
    d1 = _bezier_d1(ctrl, u)
    d2 = _bezier_d2(ctrl, u)
    num = (d * d1).sum(axis=1)
    den = (d1 * d1).sum(axis=1) + (d * d2).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        nu = u - np.where(np.abs(den) > 1e-12, num / den, 0)
    return np.clip(nu, 0, 1)


def _max_err(ctrl, pts, u):
    d = np.hypot(*(_bezier(ctrl, u) - pts).T)
    i = int(np.argmax(d))
    return float(d[i]), i


def _unit(v):
    n = math.hypot(*v)
    return v / n if n > 1e-12 else v


def fit_bezier(pts: np.ndarray, err: float, t1=None, t2=None, depth=0) -> list[np.ndarray]:
    """Noktalara kübik Bézier parçaları uydur. Her parça 4 kontrol noktası."""
    pts = np.asarray(pts, dtype=float)
    if len(pts) == 2:
        d = math.hypot(*(pts[1] - pts[0])) / 3
        t1 = _unit(pts[1] - pts[0]) if t1 is None else t1
        t2 = _unit(pts[0] - pts[1]) if t2 is None else t2
        return [np.array([pts[0], pts[0] + t1 * d, pts[1] + t2 * d, pts[1]])]
    if t1 is None:
        t1 = _unit(pts[min(2, len(pts) - 1)] - pts[0])
    if t2 is None:
        t2 = _unit(pts[max(-3, -len(pts))] - pts[-1])
    u = _chord_params(pts)
    ctrl = _generate(pts, u, t1, t2)
    e, split = _max_err(ctrl, pts, u)
    if e <= err:
        return [ctrl]
    if e < err * 4:
        for _ in range(4):
            u = _reparam(ctrl, pts, u)
            ctrl = _generate(pts, u, t1, t2)
            e, split = _max_err(ctrl, pts, u)
            if e <= err:
                return [ctrl]
    if depth > 30 or len(pts) < 4:
        return [ctrl]
    split = int(np.clip(split, 1, len(pts) - 2))
    tc = _unit(pts[split - 1] - pts[split + 1])
    left = fit_bezier(pts[:split + 1], err, t1, tc, depth + 1)
    right = fit_bezier(pts[split:], err, -tc, t2, depth + 1)
    return left + right


# ---------------------------------------------------------------- parça sınıflandırma
def classify_segment(pts: np.ndarray, tol: float):
    """Bir kontur parçasını düz çizgi, çember yayı ya da Bézier olarak tanı.

    Dönüş: ("L", uç) | ("A", (cx, cy, r, uç, büyük_yay, yön)) | ("C", [kontrol dizileri])
    """
    pts = np.asarray(pts, dtype=float)
    p0, p1 = pts[0], pts[-1]
    if len(pts) <= 2:
        return ("L", p1)
    c, d, dev = line_fit(pts)
    chord = math.hypot(*(p1 - p0))
    if dev <= tol * 1.1:
        return ("L", p1)
    # Çember yayı: yeterince uzun ve çember iyi oturuyorsa
    fit = circle_fit(pts) if (chord > max(4 * tol, 4.0) and len(pts) >= 8) else None
    if fit is not None:
        cx, cy, r, rms = fit
        if rms <= tol * 0.55 and r < chord * 40:
            # yay boyunca açısal ilerleme tek yönlü mü
            ang = np.unwrap(np.arctan2(pts[:, 1] - cy, pts[:, 0] - cx))
            dang = np.diff(ang)
            if len(dang) and (np.all(dang >= -1e-3) or np.all(dang <= 1e-3)):
                sweep_total = ang[-1] - ang[0]
                large = 1 if abs(sweep_total) > math.pi else 0
                sweep = 1 if sweep_total > 0 else 0
                return ("A", (cx, cy, r, p1, large, sweep, sweep_total))
    return ("C", fit_bezier(pts, tol))
