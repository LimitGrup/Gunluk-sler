"""Çizimi Illustrator'a düzenlenebilir vektör olarak aktarma ve panoya vektör kopyalama.

Bir SVG dosyasını Illustrator'a sürüklemek ya da "yerleştirmek" onu bağlı (linked) bir
öğe yapar: fotoğraf gibi davranır, düzenlenemez. Bu yüzden:

- send(): Illustrator SVG'yi kendi belgesi olarak açar (her şey düzenlenebilir olur),
  hepsini kopyalar, belgeyi kapatır ve açık belgenize yapıştırıp gruplar.
- copy_vector(): Mac'te panoya PDF verisi koyar; Illustrator'da Cmd+V ile yapıştırılınca
  düzenlenebilir çizim olarak gelir.
- svg_to_pdf(): SVG'yi vektör PDF'e çevirir (yazılar, degrade ve çizgiler vektör kalır).
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

# Illustrator içinde çalışan ExtendScript. {path}: SVG dosyasının tam yolu.
_JS = (
    '(function(){{'
    'var f=new File("{path}");'
    'var lvl=app.userInteractionLevel;'
    'app.userInteractionLevel=UserInteractionLevel.DONTDISPLAYALERTS;'
    'try{{'
    'if(app.documents.length==0){{app.open(f);return;}}'
    'var hedef=app.activeDocument;'
    'var kaynak=app.open(f);'
    'app.executeMenuCommand("selectall");'
    'app.copy();'
    'kaynak.close(SaveOptions.DONOTSAVECHANGES);'
    'hedef.activate();'
    'app.executeMenuCommand("deselectall");'
    'app.paste();'
    'try{{if(hedef.selection.length>1){{app.executeMenuCommand("group");}}}}catch(e){{}}'
    '}}finally{{app.userInteractionLevel=lvl;}}'
    '}})();'
)


def send(svg_path: str) -> tuple[bool, str]:
    """SVG'yi Illustrator'daki açık belgeye düzenlenebilir çizim olarak yapıştır.

    Belge açık değilse SVG kendi belgesi olarak açılır (o da düzenlenebilirdir).
    """
    path = os.path.abspath(svg_path).replace("\\", "/")
    js = _JS.format(path=path.replace('"', '\\"'))
    if sys.platform == "darwin":
        script = (
            'tell application id "com.adobe.illustrator"\n'
            "activate\n"
            f"do javascript \"{js.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))}\"\n"
            "end tell"
        )
        try:
            r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=120)
        except Exception as e:  # noqa: BLE001
            return False, str(e)
        if r.returncode != 0:
            err = (r.stderr or r.stdout or "").strip()
            if "-1728" in err or "Can’t get application" in err or "can't get application" in err.lower():
                return False, "Adobe Illustrator bulunamadı."
            if "-1743" in err:
                return False, ("Illustrator'ı denetleme izni yok: Sistem Ayarları › Gizlilik ve Güvenlik › "
                               "Otomasyon'da GorselCizici için Adobe Illustrator'ı açın.")
            return False, err or "Illustrator'a aktarılamadı."
        return True, ""
    if sys.platform.startswith("win"):
        ps = (
            "$ai = New-Object -ComObject Illustrator.Application;"
            f"$ai.DoJavaScript('{js.replace(chr(39), chr(39) * 2)}')"
        )
        try:
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=120)
        except Exception as e:  # noqa: BLE001
            return False, str(e)
        if r.returncode != 0:
            return False, (r.stderr or "Illustrator'a aktarılamadı.").strip()
        return True, ""
    return False, "Bu işletim sisteminde doğrudan aktarma yok; PDF ya da SVG kaydedip Illustrator'da açın."


# ---------------------------------------------------------------- PDF
def _size_pt(svg: str) -> tuple[float, float]:
    """SVG kökündeki width/height (pt); yoksa viewBox."""
    head = svg[: svg.find(">") + 1] if ">" in svg else svg
    def num(attr):
        m = re.search(attr + r'="\s*([\d.]+)\s*(pt|px|mm)?\s*"', head)
        if not m:
            return None
        v = float(m.group(1))
        unit = m.group(2) or "px"
        return v * {"pt": 1.0, "px": 0.75, "mm": 72 / 25.4}[unit]
    w, h = num("width"), num("height")
    if not w or not h:
        m = re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', head)
        if m:
            w, h = float(m.group(1)) * 0.75, float(m.group(2)) * 0.75
    return (w or 595.0), (h or 842.0)


def svg_to_pdf(svg: str) -> bytes:
    """SVG'yi tek sayfalık vektör PDF'e çevir (sayfa = çizim boyu, kenar boşluğu yok)."""
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QMarginsF, QRectF, QSizeF
    from PySide6.QtGui import QPageLayout, QPageSize, QPainter, QPdfWriter
    from PySide6.QtSvg import QSvgRenderer

    w, h = _size_pt(svg)
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    writer = QPdfWriter(buf)
    writer.setCreator("Görsel Çizici")
    writer.setTitle("Görsel Çizici çizimi")
    writer.setResolution(72)  # 1 birim = 1 pt
    writer.setPageLayout(QPageLayout(QPageSize(QSizeF(w, h), QPageSize.Unit.Point, "Cizim",
                                               QPageSize.SizeMatchPolicy.ExactMatch),
                                     QPageLayout.Orientation.Portrait, QMarginsF(0, 0, 0, 0)))
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    p = QPainter(writer)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(p, QRectF(0, 0, w, h))
    p.end()
    buf.close()
    return bytes(buf.data())


# ---------------------------------------------------------------- pano
def copy_vector(svg: str) -> bool:
    """Panoya vektör çizim koy. Mac'te PDF (Illustrator Cmd+V ile düzenlenebilir yapıştırır).

    Dönüş: Mac'in kendi panosu kullanıldıysa True; değilse False (çağıran Qt ile kopyalar).
    """
    if sys.platform != "darwin":
        return False
    try:
        from AppKit import NSPasteboard, NSPasteboardTypePDF
        from Foundation import NSData
    except Exception:  # noqa: BLE001
        return False
    try:
        pdf = svg_to_pdf(svg)
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        svg_type = "public.svg-image"
        pb.declareTypes_owner_([NSPasteboardTypePDF, svg_type], None)
        pb.setData_forType_(NSData.dataWithBytes_length_(pdf, len(pdf)), NSPasteboardTypePDF)
        raw = svg.encode("utf-8")
        pb.setData_forType_(NSData.dataWithBytes_length_(raw, len(raw)), svg_type)
        return True
    except Exception:  # noqa: BLE001
        return False
