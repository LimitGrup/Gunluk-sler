"""Görsel Çizici masaüstü uygulaması (PySide6).

Görsel seç (ekrandan kırp, aç, yapıştır ya da sürükle) → Çiz → Illustrator'a sürükle ya da gönder.
İnternet ya da API anahtarı gerekmez.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time

import numpy as np
from PySide6.QtCore import QByteArray, QMimeData, QRectF, QSettings, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDrag, QFont, QFontMetricsF, QGuiApplication, QImage, QPainter, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QColorDialog, QComboBox, QDoubleSpinBox, QFileDialog, QFontComboBox, QFormLayout,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
    QScrollArea, QSizePolicy, QTabWidget, QVBoxLayout, QWidget,
)

from . import cizim, harita, illustrator, metin
from .svg import Style, to_svg

APP_NAME = "Görsel Çizici"
VERSION = "1.0"
ACCENT = "#FFB000"

COLORS = [
    ("Görseldeki renkler", None),
    ("Siyah", "#000000"),
    ("Mavi", "#0070C0"),
    ("Kırmızı", "#E3262B"),
    ("Yeşil", "#2E9E44"),
    ("Mor", "#6B2C91"),
]

STYLE_SHEET = f"""
QWidget {{ background: #1f1f1f; color: #e8e8e8; font-size: 13px; }}
QLabel#title {{ color: {ACCENT}; font-size: 26px; font-weight: 700; }}
QLabel#sub {{ color: #a8a8a8; }}
QLabel.hint {{ color: #9a9a9a; font-size: 12px; }}
QLineEdit, QComboBox, QFontComboBox, QDoubleSpinBox, QPlainTextEdit {{
  background: #151515; border: 1px solid #3a3a3a; border-radius: 6px; padding: 5px 8px; }}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus {{ border-color: {ACCENT}; }}
QPushButton {{ background: #2d2d2d; border: 1px solid #444; border-radius: 6px; padding: 7px 12px; }}
QPushButton:hover {{ background: #383838; }}
QPushButton:disabled {{ color: #777; }}
QPushButton#primary {{ background: {ACCENT}; color: #1b1b1b; font-size: 16px; font-weight: 700; border: none; padding: 11px; }}
QPushButton#primary:hover {{ background: #ffc23d; }}
QPushButton#primary:disabled {{ background: #6d5a2a; color: #2a2a2a; }}
QTabWidget::pane {{ border: 1px solid #3a3a3a; border-radius: 6px; top: -1px; }}
QTabBar::tab {{ background: #2a2a2a; padding: 8px 18px; border: 1px solid #3a3a3a; border-bottom: none;
  border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; color: #bbb; }}
QTabBar::tab:selected {{ background: #1f1f1f; color: {ACCENT}; font-weight: 600; }}
QCheckBox {{ spacing: 7px; }}
QScrollArea {{ border: none; }}
"""


# ---------------------------------------------------------------- görüntü dönüşümleri
def qimage_to_rgb(img: QImage) -> np.ndarray:
    img = img.convertToFormat(QImage.Format.Format_RGBA8888)
    w, h = img.width(), img.height()
    ptr = img.constBits()
    arr = np.frombuffer(ptr, np.uint8, count=img.sizeInBytes()).reshape(h, img.bytesPerLine())[:, : w * 4]
    rgba = arr.reshape(h, w, 4).astype(np.float32)
    a = rgba[:, :, 3:4] / 255.0
    rgb = rgba[:, :, :3] * a + 255.0 * (1 - a)
    return np.clip(rgb + 0.5, 0, 255).astype(np.uint8)


def rgb_to_qpixmap(rgb: np.ndarray) -> QPixmap:
    h, w = rgb.shape[:2]
    img = QImage(np.ascontiguousarray(rgb).data, w, h, 3 * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(img.copy())


# ---------------------------------------------------------------- önizlemeler
class ImageView(QWidget):
    def __init__(self, placeholder: str):
        super().__init__()
        self.pix = None
        self.placeholder = placeholder
        self.setMinimumHeight(230)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_pixmap(self, pix):
        self.pix = pix
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = self.rect().adjusted(1, 1, -2, -2)
        if self.pix is None:
            pen = QPen(QColor("#555"), 2, Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.drawRoundedRect(r, 8, 8)
            p.setPen(QColor("#8a8a8a"))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.placeholder)
            return
        p.fillRect(r, QColor("#ffffff"))
        sz = self.pix.size()
        sz.scale(r.size(), Qt.AspectRatioMode.KeepAspectRatio)
        x = r.x() + (r.width() - sz.width()) // 2
        y = r.y() + (r.height() - sz.height()) // 2
        p.drawPixmap(x, y, sz.width(), sz.height(), self.pix)


class SvgView(QWidget):
    def __init__(self, placeholder: str):
        super().__init__()
        self.renderer = None
        self.placeholder = placeholder
        self.setMinimumHeight(230)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_svg(self, svg: str | None):
        self.renderer = QSvgRenderer(QByteArray(svg.encode("utf-8"))) if svg else None
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        r = self.rect().adjusted(1, 1, -2, -2)
        p.fillRect(r, QColor("#ffffff"))
        if not self.renderer or not self.renderer.isValid():
            p.setPen(QColor("#777"))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.placeholder)
            return
        vb = self.renderer.viewBoxF()
        if vb.width() <= 0 or vb.height() <= 0:
            return
        k = min(r.width() / vb.width(), r.height() / vb.height())
        w, h = vb.width() * k, vb.height() * k
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.renderer.render(p, QRectF(r.x() + (r.width() - w) / 2, r.y() + (r.height() - h) / 2, w, h))


class DragArea(QLabel):
    """Buradan tutup Illustrator'a sürüklenir: SVG dosyası olarak bırakılır."""

    def __init__(self, owner):
        super().__init__("⬆  Buradan tutup Illustrator'a sürükleyin")
        self.owner = owner
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(54)
        self.setStyleSheet("QLabel { border: 2px dashed #555; border-radius: 8px; color: #9a9a9a; font-size: 15px; font-weight: 600; }")
        self._start = None

    def set_ready(self, ready: bool):
        col = ACCENT if ready else "#555"
        txt = "#f0f0f0" if ready else "#9a9a9a"
        self.setStyleSheet(f"QLabel {{ border: 2px dashed {col}; border-radius: 8px; color: {txt}; font-size: 15px; font-weight: 600; }}")
        self.setCursor(Qt.CursorShape.OpenHandCursor if ready else Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, e):
        self._start = e.position().toPoint()

    def mouseMoveEvent(self, e):
        if self._start is None or not self.owner.current_svg:
            return
        if (e.position().toPoint() - self._start).manhattanLength() < 6:
            return
        path = self.owner.write_output_file()
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(path)])
        mime.setData("image/svg+xml", QByteArray(self.owner.current_svg.encode("utf-8")))
        drag = QDrag(self)
        drag.setMimeData(mime)
        if self.owner.out_pixmap is not None:
            drag.setPixmap(self.owner.out_pixmap.scaledToWidth(160, Qt.TransformationMode.SmoothTransformation))
        drag.exec(Qt.DropAction.CopyAction)
        self._start = None


# ---------------------------------------------------------------- arka plan işi
class Worker(QThread):
    done = Signal(object, object, float)
    failed = Signal(str)

    def __init__(self, rgb, use_text, detail):
        super().__init__()
        self.rgb, self.use_text, self.detail = rgb, use_text, detail

    def run(self):
        t = time.time()
        try:
            scene, texts = cizim.analyze(self.rgb, self.use_text, self.detail)
        except Exception as e:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            self.failed.emit(str(e))
            return
        self.done.emit(scene, texts, time.time() - t)


# ---------------------------------------------------------------- ana pencere
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {VERSION}")
        self.settings = QSettings("LimitGrup", "GorselCizici")
        self.rgb = None
        self.scene = None
        self.texts = []
        self.current_svg = ""
        self.out_pixmap = None
        self.worker = None
        self.waiting_clip = False
        self._loading = True
        self.out_dir = os.path.join(tempfile.gettempdir(), "GorselCizici")
        os.makedirs(self.out_dir, exist_ok=True)
        self.setAcceptDrops(True)
        self._build()
        self._load_settings()
        self._loading = False
        QGuiApplication.clipboard().dataChanged.connect(self._clipboard_changed)
        self.resize(640, 980)

    # ------------------------------------------------ arayüz
    def _build(self):
        root = QWidget()
        lay = QVBoxLayout(root)
        lay.setContentsMargins(18, 14, 18, 10)
        lay.setSpacing(10)
        title = QLabel(f"◆ {APP_NAME}")
        title.setObjectName("title")
        sub = QLabel("Görseli seç → Çiz → Illustrator'a sürükle. Ders kitabı grafikleri, şekiller ve haritalar düzenlenebilir vektör olur.")
        sub.setObjectName("sub")
        sub.setWordWrap(True)
        lay.addWidget(title)
        lay.addWidget(sub)

        # ayarlar
        g = QGridLayout()
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        self.font_box = QFontComboBox()
        self.font_box.setEditable(True)
        self.pt_box = QDoubleSpinBox()
        self.pt_box.setRange(0, 72)
        self.pt_box.setDecimals(1)
        self.pt_box.setSingleStep(0.5)
        self.pt_box.setSpecialValueText("görseldeki gibi")
        self.color_box = QComboBox()
        for name, _ in COLORS:
            self.color_box.addItem(name)
        self.stroke_box = QDoubleSpinBox()
        self.stroke_box.setRange(0, 10)
        self.stroke_box.setDecimals(2)
        self.stroke_box.setSingleStep(0.25)
        self.stroke_box.setSpecialValueText("görseldeki gibi")
        self.width_box = QDoubleSpinBox()
        self.width_box.setRange(0, 1000)
        self.width_box.setDecimals(0)
        self.width_box.setSuffix(" mm")
        self.width_box.setSpecialValueText("otomatik")
        g.addWidget(QLabel("Yazı tipi:"), 0, 0)
        g.addWidget(self.font_box, 0, 1)
        g.addWidget(QLabel("Punto:"), 0, 2)
        g.addWidget(self.pt_box, 0, 3)
        g.addWidget(QLabel("Renk:"), 1, 0)
        g.addWidget(self.color_box, 1, 1)
        g.addWidget(QLabel("Kontur (pt):"), 1, 2)
        g.addWidget(self.stroke_box, 1, 3)
        g.addWidget(QLabel("Genişlik:"), 2, 2)
        g.addWidget(self.width_box, 2, 3)
        hint = QLabel("Punto: yazıların ortalama boyu; çizim buna göre ölçeklenir.")
        hint.setProperty("class", "hint")
        hint.setStyleSheet("color:#9a9a9a;font-size:12px;")
        hint.setWordWrap(True)
        g.addWidget(hint, 2, 0, 1, 2)
        g.setColumnStretch(1, 1)
        g.setColumnStretch(3, 1)
        lay.addLayout(g)
        for w in (self.font_box, self.color_box):
            (w.currentFontChanged if w is self.font_box else w.currentIndexChanged).connect(self._style_changed)
        for w in (self.pt_box, self.stroke_box, self.width_box):
            w.valueChanged.connect(self._style_changed)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._image_tab(), "🖼  Görselden çiz")
        self.tabs.addTab(self._map_tab(), "🗺  Dilsiz harita")
        self.tabs.currentChanged.connect(self._tab_changed)
        lay.addWidget(self.tabs, 1)

        # çıktı
        self.drag = DragArea(self)
        lay.addWidget(self.drag)
        row = QHBoxLayout()
        self.send_btn = QPushButton("Illustrator'a gönder")
        self.save_btn = QPushButton("SVG kaydet…")
        self.copy_btn = QPushButton("Kopyala")
        for b in (self.send_btn, self.save_btn, self.copy_btn):
            b.setEnabled(False)
            row.addWidget(b)
        self.send_btn.clicked.connect(self.send_to_illustrator)
        self.save_btn.clicked.connect(self.save_svg)
        self.copy_btn.clicked.connect(self.copy_svg)
        lay.addLayout(row)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color:#b8b8b8;font-size:12px;")
        lay.addWidget(self.status)
        self.setCentralWidget(root)
        self.setStyleSheet(STYLE_SHEET)

    def _image_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(8)
        row = QHBoxLayout()
        b1 = QPushButton("✂  Ekrandan kırp")
        b2 = QPushButton("📂  Görsel aç…")
        b3 = QPushButton("📋  Yapıştır")
        b1.clicked.connect(self.capture_screen)
        b2.clicked.connect(self.open_image)
        b3.clicked.connect(self.paste_image)
        for b in (b1, b2, b3):
            row.addWidget(b)
        v.addLayout(row)
        self.ocr_chk = QCheckBox("Yazıları düzenlenebilir yazı yap (bilgisayarın kendi yazı tanıması)")
        self.ocr_chk.setChecked(True)
        if not metin.available():
            self.ocr_chk.setChecked(False)
            self.ocr_chk.setEnabled(False)
            self.ocr_chk.setText("Yazılar harf şekli olarak çizilir (yazı tanıma bu bilgisayarda yok)")
        v.addWidget(self.ocr_chk)
        pv = QHBoxLayout()
        self.in_view = ImageView("Görsel bekleniyor…\n\nEkrandan kırp, aç, yapıştır\nya da buraya sürükle")
        self.out_view = SvgView("Çizim önizlemesi\n(Çiz'e basınca burada görünür)")
        pv.addWidget(self.in_view, 1)
        pv.addWidget(self.out_view, 1)
        v.addLayout(pv, 1)
        self.draw_btn = QPushButton("✏️  Çiz")
        self.draw_btn.setObjectName("primary")
        self.draw_btn.setEnabled(False)
        self.draw_btn.clicked.connect(self.draw)
        v.addWidget(self.draw_btn)
        return w

    def _map_tab(self):
        w = QWidget()
        outer = QVBoxLayout(w)
        form = QFormLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(7)
        self.map_kind = QComboBox()
        self.map_kind.addItems(["Dünya", "Türkiye"])
        self.map_proj = QComboBox()
        for k, name in harita.PROJECTIONS.items():
            self.map_proj.addItem(name, k)
        self.map_center = QDoubleSpinBox()
        self.map_center.setRange(-180, 180)
        self.map_center.setDecimals(0)
        self.map_center.setValue(10)
        self.map_center.setSuffix("°")
        self.map_detail = QComboBox()
        self.map_detail.addItems(["Sade", "Ayrıntılı"])
        self.map_borders = QCheckBox("Ülke / il sınırları")
        self.map_neigh = QCheckBox("Komşu ülkeler (Türkiye)")
        self.map_neigh.setChecked(True)
        self.map_lon = QLineEdit("0, 45, 90, 135")
        self.map_lon.setPlaceholderText("ör. 0, 45, 90  ya da  her 30")
        self.map_lat = QLineEdit("")
        self.map_lat.setPlaceholderText("ör. 23.5, 66.5  ya da  her 30")
        self.map_eq = QCheckBox("Ekvator")
        self.map_eq.setChecked(True)
        self.map_labels = QCheckBox("Derece yazıları (45° D, 30° K…)")
        self.map_labels.setChecked(True)
        self.map_land = QPushButton("#CFCFCF")
        self.map_land.clicked.connect(lambda: self._pick_color(self.map_land))
        self.map_sea = QPushButton("yok")
        self.map_sea.clicked.connect(lambda: self._pick_color(self.map_sea, allow_none=True))
        self.map_points = QPlainTextEdit()
        self.map_points.setPlaceholderText("Her satıra bir nokta:  ad; boylam; enlem\nK; -14; 46\nL; 32; 35")
        self.map_points.setFixedHeight(76)
        form.addRow("Harita:", self.map_kind)
        form.addRow("İzdüşüm:", self.map_proj)
        form.addRow("Orta boylam:", self.map_center)
        form.addRow("Kıyı ayrıntısı:", self.map_detail)
        form.addRow("", self.map_borders)
        form.addRow("", self.map_neigh)
        form.addRow("Meridyenler:", self.map_lon)
        form.addRow("Paraleller:", self.map_lat)
        form.addRow("", self.map_eq)
        form.addRow("", self.map_labels)
        cl = QHBoxLayout()
        cl.addWidget(QLabel("Kara"))
        cl.addWidget(self.map_land)
        cl.addWidget(QLabel("Deniz"))
        cl.addWidget(self.map_sea)
        form.addRow("Renkler:", cl)
        form.addRow("Noktalar:", self.map_points)
        sc = QWidget()
        sc.setLayout(form)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setWidget(sc)
        area.setMaximumHeight(330)
        outer.addWidget(area)
        self.map_view = SvgView("Harita önizlemesi")
        outer.addWidget(self.map_view, 1)
        b = QPushButton("🗺  Haritayı oluştur")
        b.setObjectName("primary")
        b.clicked.connect(self.make_map)
        outer.addWidget(b)
        self.map_kind.currentIndexChanged.connect(self._map_kind_changed)
        self._map_kind_changed()
        return w

    # ------------------------------------------------ ayarlar
    def _load_settings(self):
        s = self.settings
        fam = s.value("font", "Helvetica Neue")
        self.font_box.setCurrentFont(QFont(fam))
        self.font_box.setEditText(fam)
        self.pt_box.setValue(float(s.value("punto", 8.0)))
        self.color_box.setCurrentIndex(int(s.value("renk", 0)))
        self.stroke_box.setValue(float(s.value("kontur", 0.0)))
        self.width_box.setValue(float(s.value("genislik", 0.0)))

    def _save_settings(self):
        s = self.settings
        s.setValue("font", self.font_family())
        s.setValue("punto", self.pt_box.value())
        s.setValue("renk", self.color_box.currentIndex())
        s.setValue("kontur", self.stroke_box.value())
        s.setValue("genislik", self.width_box.value())

    def font_family(self) -> str:
        return self.font_box.currentText().strip() or self.font_box.currentFont().family()

    # ------------------------------------------------ görsel alma
    def set_image(self, rgb: np.ndarray, source: str):
        if rgb is None or rgb.size == 0:
            return
        self.rgb = rgb
        self.scene = None
        self.texts = []
        self.in_view.set_pixmap(rgb_to_qpixmap(rgb))
        self.out_view.set_svg(None)
        self._set_output("")
        self.draw_btn.setEnabled(True)
        self.tabs.setCurrentIndex(0)
        self.set_status(f"{source}: {rgb.shape[1]}×{rgb.shape[0]} piksel. Çiziliyor…")
        QTimer.singleShot(50, self.draw)

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Görsel aç", self.settings.value("last_dir", os.path.expanduser("~")),
                                              "Görseller (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff)")
        if path:
            self.settings.setValue("last_dir", os.path.dirname(path))
            self.load_path(path)

    def load_path(self, path: str):
        try:
            rgb = cizim.load_rgb(path)
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, APP_NAME, f"Görsel açılamadı:\n{e}")
            return
        self.set_image(rgb, os.path.basename(path))

    def paste_image(self):
        cb = QGuiApplication.clipboard()
        md = cb.mimeData()
        if md.hasImage():
            img = cb.image()
            if not img.isNull():
                self.set_image(qimage_to_rgb(img), "Panodaki görsel")
                return
        if md.hasUrls():
            for u in md.urls():
                if u.isLocalFile():
                    self.load_path(u.toLocalFile())
                    return
        self.set_status("Panoda görsel yok. Önce bir görseli kopyalayın ya da Ekrandan kırp'ı kullanın.")

    def capture_screen(self):
        if sys.platform == "darwin":
            self.hide()
            QTimer.singleShot(350, self._capture_mac)
        elif sys.platform.startswith("win"):
            self.waiting_clip = True
            self.set_status("Ekrandan bir bölge seçin; seçince görsel kendiliğinden gelir.")
            try:
                subprocess.Popen(["explorer", "ms-screenclip:"])
            except Exception:  # noqa: BLE001
                self.set_status("Ekran kırpma açılamadı. Win+Shift+S ile kırpıp Yapıştır'a basın.")
        else:
            self.set_status("Bu sistemde ekrandan kırpma yok; görseli açın ya da yapıştırın.")

    def _capture_mac(self):
        path = os.path.join(self.out_dir, f"kirpma-{int(time.time())}.png")
        try:
            subprocess.run(["screencapture", "-i", "-x", path], timeout=300)
        except Exception as e:  # noqa: BLE001
            self.set_status(f"Ekran kırpılamadı: {e}")
        self.show()
        self.raise_()
        self.activateWindow()
        if os.path.exists(path) and os.path.getsize(path) > 0:
            self.load_path(path)
        else:
            self.set_status("Kırpma iptal edildi.")

    def _clipboard_changed(self):
        if self.waiting_clip and QGuiApplication.clipboard().mimeData().hasImage():
            self.waiting_clip = False
            self.paste_image()

    def dragEnterEvent(self, e):
        md = e.mimeData()
        if md.hasUrls() or md.hasImage():
            e.acceptProposedAction()

    def dropEvent(self, e):
        md = e.mimeData()
        if md.hasUrls():
            for u in md.urls():
                if u.isLocalFile():
                    self.load_path(u.toLocalFile())
                    return
        if md.hasImage():
            img = QImage(md.imageData())
            if not img.isNull():
                self.set_image(qimage_to_rgb(img), "Bırakılan görsel")

    # ------------------------------------------------ çizim
    def draw(self):
        if self.rgb is None or (self.worker and self.worker.isRunning()):
            return
        self.draw_btn.setEnabled(False)
        self.draw_btn.setText("Çiziliyor…")
        self.set_status("Görsel çiziliyor… (büyük görsellerde birkaç saniye sürebilir)")
        self.worker = Worker(self.rgb, self.ocr_chk.isChecked(), 1.0)
        self.worker.done.connect(self._draw_done)
        self.worker.failed.connect(self._draw_failed)
        self.worker.start()

    def _draw_failed(self, msg):
        self.draw_btn.setEnabled(True)
        self.draw_btn.setText("✏️  Çiz")
        self.set_status(f"Çizilemedi: {msg}")

    def _draw_done(self, scene, texts, secs):
        self.draw_btn.setEnabled(True)
        self.draw_btn.setText("✏️  Yeniden çiz")
        self.scene = scene
        self.texts = texts
        self._rebuild_image_svg()
        n_txt = sum(1 for e in scene.elements if e.kind == "text")
        extra = f" · {n_txt} yazı düzenlenebilir" if n_txt else ""
        self.set_status(f"Çizildi ({secs:.1f} sn): {scene.notes[-1] if scene.notes else ''}{extra}. "
                        "Önizlemeyi kontrol edip Illustrator'a sürükleyin.")

    def measure(self, text: str):
        f = QFont(self.font_family())
        f.setPointSizeF(100)
        r = QFontMetricsF(f).tightBoundingRect(text)
        return r.left(), r.top(), r.right(), r.bottom()

    def _style(self, svg_scene=None) -> Style:
        col = COLORS[self.color_box.currentIndex()][1]
        st = Style(font=self.font_family(), stroke_pt=self.stroke_box.value() or None, color=col)
        if self.width_box.value() > 0:
            st.width_mm = self.width_box.value()
        elif svg_scene is not None and self.pt_box.value() > 0:
            med = cizim.median_text_px(svg_scene)
            if med:
                # ortalama yazı istenen punto olsun: ölçek = punto / piksel
                st.width_mm = svg_scene.width * (self.pt_box.value() / med) * 25.4 / 72
        return st

    def _rebuild_image_svg(self):
        if self.scene is None:
            return
        cizim.add_texts(self.scene, self.rgb, self.texts, self.measure)
        svg = to_svg(self.scene, self._style(self.scene))
        self.out_view.set_svg(svg)
        self._set_output(svg)

    def _style_changed(self, *_):
        if self._loading:
            return
        self._save_settings()
        if self.tabs.currentIndex() == 0:
            self._rebuild_image_svg()
        elif self.current_svg:
            self.make_map()

    # ------------------------------------------------ harita
    def _map_kind_changed(self):
        world = self.map_kind.currentIndex() == 0
        for wdg in (self.map_proj, self.map_center, self.map_detail, self.map_eq):
            wdg.setEnabled(world)
        self.map_neigh.setEnabled(not world)
        if world and not self.map_lon.text().strip():
            self.map_lon.setText("0, 45, 90, 135")
        if not world and self.map_lon.text().strip() == "0, 45, 90, 135":
            self.map_lon.setText("")

    def _pick_color(self, btn, allow_none=False):
        cur = btn.text()
        c = QColorDialog.getColor(QColor(cur if cur.startswith("#") else "#ffffff"), self, "Renk seç")
        if c.isValid():
            btn.setText(c.name().upper())
        elif allow_none:
            btn.setText("yok")

    @staticmethod
    def _parse_grid(text: str):
        t = text.strip().lower().replace("°", "")
        if not t:
            return 0.0, []
        if t.startswith("her"):
            try:
                return float(t[3:].strip().replace(",", ".")), []
            except ValueError:
                return 0.0, []
        vals = []
        for part in t.replace(";", ",").split(","):
            p = part.strip()
            if not p:
                continue
            sign = 1
            if p.endswith(("b", "g", "w", "s")):
                sign, p = -1, p[:-1].strip()
            elif p.endswith(("d", "k", "e", "n")):
                p = p[:-1].strip()
            try:
                vals.append(sign * float(p))
            except ValueError:
                pass
        return 0.0, vals

    def make_map(self):
        world = self.map_kind.currentIndex() == 0
        glon, llon = self._parse_grid(self.map_lon.text())
        glat, llat = self._parse_grid(self.map_lat.text())
        pts = []
        for line in self.map_points.toPlainText().splitlines():
            parts = [p.strip() for p in line.replace(",", ";").split(";")]
            if len(parts) >= 3:
                try:
                    pts.append((parts[0], float(parts[1]), float(parts[2])))
                except ValueError:
                    pass
        sea = self.map_sea.text()
        st = harita.MapStyle(
            kind="dunya" if world else "turkiye",
            proj=self.map_proj.currentData(),
            center=self.map_center.value(),
            detail="50m" if self.map_detail.currentIndex() == 1 else "110m",
            width_mm=self.width_box.value() or (160.0 if world else 180.0),
            land=self.map_land.text(),
            sea=sea if sea.startswith("#") else "",
            borders=self.map_borders.isChecked(),
            neighbors=self.map_neigh.isChecked(),
            grid_lon=glon, lon_list=llon, grid_lat=glat, lat_list=llat,
            equator=self.map_eq.isChecked() and world,
            labels=self.map_labels.isChecked(),
            font=self.font_family(),
            font_pt=self.pt_box.value() or 8.0,
            outline_pt=self.stroke_box.value() or 0.4,
            points=pts,
        )
        col = COLORS[self.color_box.currentIndex()][1]
        if col:
            st.grid_color = col
            st.point_color = col
        try:
            svg = harita.build_svg(st)
        except Exception as e:  # noqa: BLE001
            self.set_status(f"Harita oluşturulamadı: {e}")
            return
        self.map_view.set_svg(svg)
        self._set_output(svg)
        self.set_status("Harita hazır. Illustrator'a sürükleyin ya da gönderin.")

    def _tab_changed(self, i):
        if i == 0:
            if self.scene is not None:
                self._rebuild_image_svg()
            else:
                self._set_output("")
        else:
            self._set_output("")
            self.make_map()

    # ------------------------------------------------ çıktı
    def _set_output(self, svg: str):
        self.current_svg = svg or ""
        ready = bool(self.current_svg)
        self.drag.set_ready(ready)
        for b in (self.send_btn, self.save_btn, self.copy_btn):
            b.setEnabled(ready)
        self.out_pixmap = None
        if ready:
            r = QSvgRenderer(QByteArray(self.current_svg.encode("utf-8")))
            vb = r.viewBoxF()
            if vb.width() > 0:
                k = 320 / vb.width()
                pm = QPixmap(int(vb.width() * k), max(1, int(vb.height() * k)))
                pm.fill(QColor("#ffffff"))
                p = QPainter(pm)
                r.render(p)
                p.end()
                self.out_pixmap = pm

    def write_output_file(self) -> str:
        name = "harita" if self.tabs.currentIndex() == 1 else "cizim"
        path = os.path.join(self.out_dir, f"{name}-{time.strftime('%H%M%S')}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + self.current_svg)
        return path

    def send_to_illustrator(self):
        if not self.current_svg:
            return
        path = self.write_output_file()
        self.set_status("Illustrator'a gönderiliyor…")
        QApplication.processEvents()
        ok, msg = illustrator.send(path)
        self.set_status("Illustrator'daki açık belgeye eklendi." if ok else f"Gönderilemedi: {msg} SVG'yi kaydedip açabilir ya da sürükleyebilirsiniz.")

    def save_svg(self):
        if not self.current_svg:
            return
        name = "harita.svg" if self.tabs.currentIndex() == 1 else "cizim.svg"
        path, _ = QFileDialog.getSaveFileName(self, "SVG kaydet", os.path.join(self.settings.value("save_dir", os.path.expanduser("~")), name), "SVG (*.svg)")
        if not path:
            return
        if not path.lower().endswith(".svg"):
            path += ".svg"
        with open(path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + self.current_svg)
        self.settings.setValue("save_dir", os.path.dirname(path))
        self.set_status(f"Kaydedildi: {path}")

    def copy_svg(self):
        if not self.current_svg:
            return
        path = self.write_output_file()
        md = QMimeData()
        md.setText(self.current_svg)
        md.setData("image/svg+xml", QByteArray(self.current_svg.encode("utf-8")))
        md.setUrls([QUrl.fromLocalFile(path)])
        QGuiApplication.clipboard().setMimeData(md)
        self.set_status("Kopyalandı. Illustrator'da Düzen › Yapıştır (Cmd+V) ile yapıştırın.")

    def set_status(self, msg: str):
        self.status.setText(msg)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    win = MainWindow()
    win.show()
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        win.load_path(sys.argv[1])
    sys.exit(app.exec())
