"""Görselden çizim akışı (arayüzden bağımsız): yazı tanıma + vektörleştirme + yazı yerleştirme."""
from __future__ import annotations

import os
import tempfile

import numpy as np
from PIL import Image

from . import metin
from .vektor import Element, Options, Scene, vectorize


def load_rgb(path: str) -> np.ndarray:
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        im = bg
    return np.array(im.convert("RGB"))


def analyze(rgb: np.ndarray, use_text: bool = True, detail: float = 1.0, yazisiz: bool = False):
    """Ağır iş (arka planda çalıştırılabilir). Dönüş: (sahne, tanınan yazılar).

    yazisiz: yazılar hiç çizilmez, yalnız şekiller. Yazı tanıma yine çalışır (varsa): yazı
    pikselleri şekle karışmasın diye; yazıların arkasındaki çizimler çizilir.
    """
    if yazisiz:
        use_text = True
    texts = []
    if use_text and metin.available():
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        try:
            Image.fromarray(rgb).save(path)
            texts = metin.recognize(path, rgb.shape[1], rgb.shape[0])
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
    # Tanınan her kelime görseldeki mürekkeple karşılaştırılır; yalnız tutanlar yazı olur ve
    # yalnız onların pikselleri şekle çevrilmez. Tutmayanlar görseldeki gibi şekil olarak kalır.
    texts = metin.validate(texts, rgb) if texts else []
    tm = metin.text_mask(texts, rgb.shape) if texts else None
    # Dilsiz harita mı: öyleyse harita temiz veriden çizilir, yalnız işaretlemeler görselden
    esl = None
    try:
        from . import harita_tani
        esl = harita_tani.tani(rgb)
    except Exception:  # noqa: BLE001
        esl = None
    if esl is not None:
        from . import harita_tani
        harita_tani.hazirla(rgb, esl)
        kalan = harita_tani.harita_kalintisi(rgb, esl)
        scene = vectorize(kalan, Options(detail=detail, text_mask=tm, small_marks=True, yazisiz=yazisiz,
                                         zemin=False))
        scene.underlay = harita_tani.harita_cizimi(rgb, esl)
        scene.notes = esl.notes + scene.notes
    else:
        scene = vectorize(rgb, Options(detail=detail, text_mask=tm, yazisiz=yazisiz))
    if yazisiz:
        texts = []
    return scene, texts


def add_texts(scene: Scene, rgb: np.ndarray, texts: list, measure) -> Scene:
    """Tanınan yazıları seçilen yazı tipinin ölçüleriyle yerlerine koy."""
    placed = metin.place(texts, rgb, measure)
    scene.elements = [e for e in scene.elements if e.kind != "text"]
    for p in placed:
        scene.elements.append(Element("text", p["color"], text=p["text"], x=p["x"], y=p["y"], size=p["size"],
                                      bbox=p["box"], bold=bool(p.get("bold"))))
    return scene


def median_text_px(scene: Scene) -> float | None:
    sizes = [e.size for e in scene.elements if e.kind == "text" and e.size > 0]
    return float(np.median(sizes)) if sizes else None
