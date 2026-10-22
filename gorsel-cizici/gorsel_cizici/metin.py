"""Yazıları düzenlenebilir yazıya çevirme (internetsiz).

Mac'te işletim sisteminin kendi yazı tanıması (Apple Vision) kullanılır: internete gitmez,
anahtar istemez. Bulunamazsa (Windows, eski macOS) yazılar harf şekli olarak çizilir.

Akış:
  1. recognize(): yazı satırlarını ve kutularını bulur.
  2. place(): her yazının görseldeki gerçek mürekkep sınırlarını ölçer; seçilen yazı tipinde
     aynı genişlik ve yükseklikte olacak puntoyu ve taban çizgisini hesaplar.
"""
from __future__ import annotations

import math
import sys

import numpy as np


def available() -> bool:
    if sys.platform != "darwin":
        return False
    try:
        import Vision  # noqa: F401
        import Quartz  # noqa: F401
        return True
    except Exception:
        return False


def recognize(png_path: str, width: int, height: int) -> list[dict]:
    """Görseldeki yazı satırları: [{"text", "box": (x0, y0, x1, y1), "conf"}] piksel cinsinden."""
    if not available():
        return []
    try:
        import Quartz
        import Vision
        from Foundation import NSURL

        url = NSURL.fileURLWithPath_(png_path)
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, None)
        req = Vision.VNRecognizeTextRequest.alloc().init()
        req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        req.setUsesLanguageCorrection_(False)
        try:
            req.setMinimumTextHeight_(0.0)
        except Exception:
            pass
        langs = ["tr-TR", "en-US"]
        try:
            supported = list(req.supportedRecognitionLanguagesAndReturnError_(None)[0] or [])
            langs = [l for l in langs if l in supported] or ["en-US"]
        except Exception:
            pass
        try:
            req.setRecognitionLanguages_(langs)
        except Exception:
            pass
        ok = handler.performRequests_error_([req], None)
        if isinstance(ok, tuple):
            ok = ok[0]
        out = []
        for obs in (req.results() or []):
            cands = obs.topCandidates_(1)
            if not cands:
                continue
            cand = cands[0]
            text = str(cand.string()).strip()
            if not text:
                continue
            # kelime kelime kutular (konumlandırma kelime başına daha doğru olur)
            words = _split_words(text)
            for w0, w1, word in words:
                box = None
                try:
                    rng = (w0, w1 - w0)
                    r = cand.boundingBoxForRange_error_(rng, None)
                    if isinstance(r, tuple):
                        r = r[0]
                    if r is not None:
                        bb = r.boundingBox()
                        box = _to_px(bb, width, height)
                except Exception:
                    box = None
                if box is None:
                    if len(words) > 1:
                        continue
                    box = _to_px(obs.boundingBox(), width, height)
                out.append({"text": word, "box": box, "conf": float(cand.confidence())})
        return out
    except Exception:
        return []


def _split_words(text: str):
    out, i = [], 0
    for part in text.split(" "):
        if part:
            out.append((i, i + len(part), part))
        i += len(part) + 1
    return out


def _to_px(bb, W, H):
    """Vision kutusu (0..1, sol alt köşe) -> piksel (x0, y0, x1, y1), sol üst köşe."""
    x, y = bb.origin.x, bb.origin.y
    w, h = bb.size.width, bb.size.height
    return (x * W, (1 - y - h) * H, (x + w) * W, (1 - y) * H)


# ---------------------------------------------------------------- yerleştirme
def ink_box(rgb: np.ndarray, box, bg=None):
    """Kutudaki yazının sıkı sınırları ve rengi.

    Zemin kutunun kenarından, yazı rengi en güçlü piksellerden bulunur; yalnız zemin ile yazı
    renginin karışımı olan pikseller yazı sayılır (yanındaki renkli şekiller sayılmaz).
    """
    import cv2
    H, W = rgb.shape[:2]
    x0, y0, x1, y1 = box
    pad = max(2, int(0.2 * (y1 - y0)))
    a0, b0 = max(0, int(math.floor(x0)) - pad), max(0, int(math.floor(y0)) - pad)
    a1, b1 = min(W, int(math.ceil(x1)) + pad), min(H, int(math.ceil(y1)) + pad)
    if a1 - a0 < 2 or b1 - b0 < 2:
        return None
    sub = rgb[b0:b1, a0:a1].astype(np.float32)
    ring = np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]])
    back = np.median(ring, axis=0) if bg is None else np.array(bg, np.float32)
    diff = np.linalg.norm(sub - back, axis=2)
    cand = diff > max(40.0, 0.35 * diff.max())
    if cand.sum() < 3:
        return None
    strong = cand & (diff >= np.percentile(diff[cand], 70))
    col = np.median(sub[strong], axis=0)
    # zemin–yazı rengi doğrusuna yakın ve en az %35 yazı rengi olan pikseller
    AB = col - back
    nab = float(AB @ AB) or 1.0
    al = np.clip(((sub - back) @ AB) / nab, 0, 1)
    res = np.linalg.norm(sub - (back + al[..., None] * AB), axis=2)
    ink = (al >= 0.35) & (res < 45)
    # kutunun dışına taşan parçaları (çizgi, şekil) at
    n, cc, st, _ = cv2.connectedComponentsWithStats(ink.astype(np.uint8), connectivity=8)
    keep = np.zeros(n, bool)
    ix0, iy0 = int(x0) - a0, int(y0) - b0
    ix1, iy1 = int(math.ceil(x1)) - a0, int(math.ceil(y1)) - b0
    for i in range(1, n):
        x, y, ww, hh, area = st[i]
        cx, cy = x + ww / 2, y + hh / 2
        if ix0 - 1 <= cx <= ix1 + 1 and iy0 - 1 <= cy <= iy1 + 1 and hh <= (y1 - y0) * 1.6 + 2:
            keep[i] = True
    ink = keep[cc]
    if ink.sum() < 3:
        return None
    ys, xs = np.nonzero(ink)
    return (a0 + xs.min(), b0 + ys.min(), a0 + xs.max() + 1, b0 + ys.max() + 1), tuple(int(v) for v in col)


def place(texts: list, rgb: np.ndarray, measure, bg=None) -> list:
    """Yazıları görseldeki yerlerine oturt.

    measure(text) -> (sol, üst, sağ, alt): 100 puntoda sıkı sınırlar, taban çizgisine göre
    (üst negatif). Dönüş: [{"text","x","y","size","color","box"}]
    """
    out = []
    for t in texts:
        r = ink_box(rgb, t["box"], bg)
        if r is None:
            continue
        (x0, y0, x1, y1), col = r
        l, top, rt, bot = measure(t["text"])
        w100, h100 = rt - l, bot - top
        if w100 <= 0 or h100 <= 0:
            continue
        sw = (x1 - x0) / w100 * 100
        sh = (y1 - y0) / h100 * 100
        # tek harfte yükseklik, uzun yazıda genişlik daha güvenilir
        n = len(t["text"])
        wt = min(0.8, 0.25 + 0.1 * n)
        size = sw * wt + sh * (1 - wt)
        k = size / 100
        x = x0 - l * k
        y = y1 - bot * k
        out.append({"text": t["text"], "x": float(x), "y": float(y), "size": float(size),
                    "color": col, "box": (float(x0), float(y0), float(x1), float(y1))})
    return out
