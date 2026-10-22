"""Yazıları düzenlenebilir yazıya çevirme (internetsiz).

Mac'te işletim sisteminin kendi yazı tanıması (Apple Vision) kullanılır: internete gitmez,
anahtar istemez. Bulunamazsa (Windows, eski macOS) yazılar harf şekli olarak çizilir.

Akış:
  1. recognize(): yazı satırlarını ve kutularını bulur; Türkçe harfleri düzeltir (turkce.py).
  2. place(): her yazının görseldeki gerçek mürekkep sınırlarını ölçer; seçilen yazı tipinde
     aynı genişlik ve yükseklikte olacak puntoyu ve taban çizgisini hesaplar.
"""
from __future__ import annotations

import math
import sys

import numpy as np

from . import turkce


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
        handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, {})
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
        for line_no, obs in enumerate(req.results() or []):
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
                out.append({"text": turkce.duzelt(word), "raw": word, "box": box,
                            "conf": float(cand.confidence()), "line": line_no})
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


# ---------------------------------------------------------------- doğrulama
# Yazı tanıma bazen çizgileri, sütunları ya da birkaç ayrı harfi kelime sanır. Her kelime
# seçilen bir yazı tipiyle çizilip görseldeki mürekkeple karşılaştırılır; benzemiyorsa
# kullanılmaz ve o yer görseldeki gibi şekil olarak çizilir.
_OK_CHARS = set("abcçdefgğhıijklmnoöprsştuüvyzqwxâîûABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZQWXÂÎÛ"
                "0123456789.,:;!?%°()[]+-–—=/'’\"&*#<>")
_EDGE = "-–—_|+.,:;'’`\"~"

_FONTS = None


def _fonts():
    """Karşılaştırma için düz ve kalın birer yazı tipi."""
    global _FONTS
    if _FONTS is not None:
        return _FONTS
    from PIL import ImageFont
    pairs = [
        ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    out = []
    for reg, bold in pairs:
        import os
        if os.path.exists(reg):
            try:
                out.append((ImageFont.truetype(reg, 64), False))
                if os.path.exists(bold):
                    out.append((ImageFont.truetype(bold, 64), True))
                break
            except Exception:
                out = []
    if not out:
        try:
            out = [(ImageFont.load_default(size=64), False)]
        except Exception:
            out = []
    _FONTS = out
    return out


def _render(text: str, font) -> np.ndarray | None:
    from PIL import Image, ImageDraw
    W = int(64 * (len(text) + 2) * 0.9) + 40
    im = Image.new("L", (W, 160), 0)
    ImageDraw.Draw(im).text((20, 40), text, font=font, fill=255)
    a = np.array(im) > 110
    if not a.any():
        return None
    ys, xs = np.nonzero(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def _score(K: np.ndarray, text: str, font) -> float:
    """Çizilen yazı ile mürekkep maskesinin benzerliği (0..1)."""
    import cv2
    R = _render(text, font)
    if R is None:
        return 0.0
    H, W = K.shape
    rh, rw = R.shape
    ar_k, ar_r = W / max(H, 1), rw / max(rh, 1)
    if not (0.62 < ar_k / ar_r < 1.6):
        return 0.0
    R = cv2.resize(R.astype(np.uint8) * 255, (W, H), interpolation=cv2.INTER_AREA) > 90
    r = max(1, int(round(0.09 * H)))
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    Kd = cv2.dilate(K.astype(np.uint8), ker) > 0
    Rd = cv2.dilate(R.astype(np.uint8), ker) > 0
    if not R.any() or not K.any():
        return 0.0
    prec = float((R & Kd).sum()) / float(R.sum())
    rec = float((K & Rd).sum()) / float(K.sum())
    return 2 * prec * rec / max(prec + rec, 1e-9)


def _thickness(M: np.ndarray) -> float:
    from skimage.morphology import skeletonize
    sk = int(skeletonize(M).sum())
    return float(M.sum()) / max(sk, 1)


def _is_bold(K: np.ndarray, text: str, fonts) -> bool:
    """Mürekkebin çizgi kalınlığı kalın yazı tipine açıkça daha yakınsa kalın say."""
    import cv2
    reg = [f for f, b in fonts if not b]
    bld = [f for f, b in fonts if b]
    if not reg or not bld:
        return False
    H, W = K.shape
    th = []
    for f in (reg[0], bld[0]):
        R = _render(text, f)
        if R is None:
            return False
        R = cv2.resize(R.astype(np.uint8) * 255, (W, H), interpolation=cv2.INTER_AREA) > 90
        th.append(_thickness(R))
    tk = _thickness(K)
    # küçük yazıda kalınlık ölçümü kaba: ancak kalın yazı tipi kadar kalınsa kalın say
    if H < 12:
        return False
    k = 0.75 if H >= 16 else 1.0
    return th[1] > th[0] and tk >= th[0] + k * (th[1] - th[0])


def _ink(rgb: np.ndarray, box):
    """Kutudaki yazının mürekkebi: yalnız kutunun içinde kalan parçalar.

    Dönüş: (maske, (x0, y0), renk, yabancı_oran) ya da None. Kutuya giren ama dışarı
    taşan büyük parçalar (eksen, sütun, çizgi) yazı sayılmaz; kutunun çoğunu bunlar
    kaplıyorsa yabancı_oran büyük olur.
    """
    import cv2
    H, W = rgb.shape[:2]
    x0, y0, x1, y1 = box
    bh = max(2.0, y1 - y0)
    pad = max(3, int(0.35 * bh))
    a0, b0 = max(0, int(math.floor(x0)) - pad), max(0, int(math.floor(y0)) - pad)
    a1, b1 = min(W, int(math.ceil(x1)) + pad), min(H, int(math.ceil(y1)) + pad)
    if a1 - a0 < 3 or b1 - b0 < 3:
        return None
    sub = rgb[b0:b1, a0:a1].astype(np.float32)
    ring = np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]])
    back = np.median(ring, axis=0)
    diff = np.linalg.norm(sub - back, axis=2)
    cand = diff > max(40.0, 0.35 * float(diff.max()))
    if cand.sum() < 3:
        return None
    strong = cand & (diff >= np.percentile(diff[cand], 70))
    col = np.median(sub[strong], axis=0)
    AB = col - back
    nab = float(AB @ AB) or 1.0
    al = np.clip(((sub - back) @ AB) / nab, 0, 1)
    res = np.linalg.norm(sub - (back + al[..., None] * AB), axis=2)
    ink = ((al >= 0.3) & (res < 45)).astype(np.uint8)
    n, cc, st, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    keep = np.zeros(n, bool)
    ix0, iy0 = x0 - a0, y0 - b0
    ix1, iy1 = x1 - a0, y1 - b0
    foreign = 0
    for i in range(1, n):
        x, y, ww, hh, area = st[i]
        touches = x == 0 or y == 0 or x + ww >= (a1 - a0) or y + hh >= (b1 - b0)
        cx, cy = x + ww / 2, y + hh / 2
        inside = ix0 - 1 <= cx <= ix1 + 1 and iy0 - 1 <= cy <= iy1 + 1
        if inside and not touches and hh <= bh * 1.5 + 2:
            keep[i] = True
        else:
            # kutunun içine düşen yabancı mürekkep
            bx0, by0 = max(x, int(ix0)), max(y, int(iy0))
            bx1, by1 = min(x + ww, int(math.ceil(ix1))), min(y + hh, int(math.ceil(iy1)))
            if bx1 > bx0 and by1 > by0:
                foreign += int((cc[by0:by1, bx0:bx1] == i).sum())
    K = keep[cc]
    if K.sum() < 3:
        return None
    ys, xs = np.nonzero(K)
    Kc = K[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    box_area = max(1.0, (x1 - x0) * (y1 - y0))
    return Kc, (a0 + int(xs.min()), b0 + int(ys.min())), tuple(int(v) for v in col), foreign / box_area, (K, a0, b0)


def _candidates(word: str, raw: str) -> list:
    from . import turkce
    out = []
    import re
    loose = turkce.duzelt_gevsek(raw)
    # sözlükte birebir karşılığı olan düzeltme önce ("Sicakllk" -> "Sıcaklık")
    base = ([loose] if loose != turkce.duzelt(raw) else []) + [word, raw, loose]
    # derece işareti sık yanlış okunur: 'C, oC, ºC -> °C
    for w in list(base):
        m = re.fullmatch(r"[\'`’o0ºª*]?([CF])", (w or "").strip())
        if m:
            base.insert(0, "°" + m.group(1))
    for w in base:
        if not w:
            continue
        for v in (w, w.strip(_EDGE), w.lstrip(_EDGE), w.rstrip(_EDGE)):
            if v and v not in out and any(ch.isalnum() for ch in v):
                out.append(v)
    return out


def validate(words: list, rgb: np.ndarray) -> list:
    """Tanınan kelimelerden görseldeki mürekkeple örtüşenleri seç.

    Dönüş: [{"text","box"(mürekkep sınırı),"color","bold","line","mask":(maske, x0, y0),"score"}]
    """
    fonts = _fonts()
    if not fonts:
        return []
    out = []
    for w in words:
        r = _ink(rgb, w["box"])
        if r is None:
            continue
        Kc, (kx, ky), col, foreign, full = r
        if foreign > 0.25:
            continue        # kutunun çoğunda çizgi/sütun var: bu bir kelime değil
        Hk = Kc.shape[0]
        if Hk < 4:
            continue
        scored = []
        for cand in _candidates(w["text"], w.get("raw", w["text"])):
            if any(ch not in _OK_CHARS for ch in cand.replace(" ", "")):
                continue    # başka alfabeden harf: yanlış okuma
            scored.append((max(_score(Kc, cand, font) for font, _b in fonts), cand))
        if not scored:
            continue
        top = max(sc for sc, _c in scored)
        # öncelik sırası: derece işareti, sözlükle düzeltilmiş, okunan, uçları kırpılmış
        sc, text = next((sc, c) for sc, c in scored if sc >= top - 0.03)
        if text is None:
            continue
        need = 0.8 if len(text.strip(_EDGE)) <= 1 else 0.7
        if sc < need:
            # aralıklı tek harfleri (ör. ay baş harfleri "H T A E") tek kelime sanmış olabilir
            out.extend(_split_letters(Kc, kx, ky, w, fonts, col, full))
            continue
        bold = _is_bold(Kc, text, fonts)
        K, a0, b0 = full
        out.append({"text": text, "box": (float(kx), float(ky), float(kx + Kc.shape[1]), float(ky + Kc.shape[0])),
                    "color": col, "bold": bold, "line": w.get("line"), "mask": (K, a0, b0), "score": sc})
    # aynı satırdakilerden çok farklı boydaki (ör. çizgiyi harf sanan) kelimeleri at
    if len(out) >= 3:
        hs = np.array([o["box"][3] - o["box"][1] for o in out])
        med = float(np.median(hs))
        out = [o for o, hh in zip(out, hs) if hh <= 3.0 * med]
    return out


def _split_letters(Kc, kx, ky, w, fonts, col, full) -> list:
    """Kelimeyi mürekkepteki boşluklardan harflere böl; her harf kendi parçasına benziyorsa kabul et."""
    word = (w.get("raw") or w["text"]).strip(_EDGE)
    if " " in word or not (2 <= len(word) <= 12):
        return []
    H = Kc.shape[0]
    cols = Kc.any(axis=0)
    gap_min = max(2, int(0.3 * H))
    spans, start, gap = [], None, 0
    for x, on in enumerate(cols):
        if on:
            if start is None:
                start = x
            gap = 0
            end = x
        elif start is not None:
            gap += 1
            if gap >= gap_min:
                spans.append((start, end + 1))
                start = None
    if start is not None:
        spans.append((start, end + 1))
    if len(spans) != len(word):
        return []
    K, a0, b0 = full
    res = []
    for ch, (s0, s1) in zip(word, spans):
        part = Kc[:, s0:s1]
        ys = np.flatnonzero(part.any(axis=1))
        part = part[ys.min():ys.max() + 1]
        if ch not in _OK_CHARS or part.shape[0] < 0.6 * H:
            continue
        sc = max(_score(part, ch, f) for f, _b in fonts)
        if sc < 0.8:
            continue        # bu harf benzemiyor: görseldeki gibi şekil kalır
        x0, y0 = kx + s0, ky + int(ys.min())
        m = np.zeros_like(K)
        m[y0 - b0:y0 - b0 + part.shape[0], x0 - a0:x0 - a0 + part.shape[1]] = part
        res.append({"text": ch, "box": (float(x0), float(y0), float(x0 + part.shape[1]), float(y0 + part.shape[0])),
                    "color": col, "bold": False, "line": None, "mask": (m, a0, b0), "score": sc})
    return res


def text_mask(accepted: list, shape) -> np.ndarray:
    """Kabul edilen yazıların pikselleri (bunlar şekle çevrilmez)."""
    m = np.zeros(shape[:2], bool)
    for o in accepted:
        K, a0, b0 = o["mask"]
        m[b0:b0 + K.shape[0], a0:a0 + K.shape[1]] |= K
    return m


# ---------------------------------------------------------------- yerleştirme
def place(texts: list, rgb: np.ndarray, measure, bg=None) -> list:
    """Yazıları görseldeki yerlerine oturt.

    texts: validate() çıktısı (mürekkep sınırı ve rengi hazır). measure(text) -> (sol, üst,
    sağ, alt): 100 puntoda sıkı sınırlar, taban çizgisine göre (üst negatif).
    Dönüş: [{"text","x","y","size","color","box","bold"}]
    """
    out = []
    for t in texts:
        if "mask" in t:
            (x0, y0, x1, y1), col = t["box"], t["color"]
        else:
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
        # tek harfte yükseklik, uzun yazıda genişlik daha güvenilir; ikisi çok ayrışıyorsa
        # (yazı tipi farkı) yüksekliğe güven
        n = len(t["text"])
        wt = min(0.8, 0.25 + 0.1 * n)
        if not (0.7 < sw / max(sh, 1e-6) < 1.4):
            wt = 0.2
        size = sw * wt + sh * (1 - wt)
        k = size / 100
        x = x0 - l * k
        y = y1 - bot * k
        out.append({"text": t["text"], "x": float(x), "y": float(y), "size": float(size), "bold": bool(t.get("bold")),
                    "color": col, "box": (float(x0), float(y0), float(x1), float(y1)), "line": t.get("line")})
    return _merge_lines(out)


def ink_box(rgb: np.ndarray, box, bg=None):
    """Kutudaki yazının sıkı sınırları ve rengi (eski yol; validate() kullanılmadığında)."""
    r = _ink(rgb, box)
    if r is None:
        return None
    Kc, (kx, ky), col, _f, _full = r
    return (kx, ky, kx + Kc.shape[1], ky + Kc.shape[0]), col


def _merge_lines(items: list) -> list:
    """Aynı satırdaki kelimeleri tek yazı yap (Illustrator'da satır satır düzenlenir)."""
    groups, rest = {}, []
    for it in items:
        if it.get("line") is None:
            rest.append(it)
        else:
            groups.setdefault(it["line"], []).append(it)
    out = list(rest)
    for words in groups.values():
        words.sort(key=lambda w: w["x"])
        cur = [words[0]]
        for w in words[1:]:
            prev = cur[-1]
            size = float(np.median([q["size"] for q in cur]))
            gap = w["box"][0] - prev["box"][2]
            same_base = abs(w["y"] - prev["y"]) < 0.25 * size
            if same_base and -0.1 * size < gap < 0.8 * size and abs(w["size"] - size) < 0.25 * size:
                cur.append(w)
            else:
                out.append(_join(cur))
                cur = [w]
        out.append(_join(cur))
    return out


def _join(words: list) -> dict:
    if len(words) == 1:
        return words[0]
    sizes = [w["size"] for w in words]
    return {
        "text": " ".join(w["text"] for w in words),
        "x": words[0]["x"],
        "y": float(np.median([w["y"] for w in words])),
        "size": float(np.median(sizes)),
        "color": words[0]["color"],
        "box": (words[0]["box"][0], min(w["box"][1] for w in words), words[-1]["box"][2], max(w["box"][3] for w in words)),
        "line": words[0].get("line"),
        "bold": sum(bool(w.get("bold")) for w in words) * 2 > len(words),
    }
