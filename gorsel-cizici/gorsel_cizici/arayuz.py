"""Görsel Çizici masaüstü uygulaması (PySide6).

Görsel ver (ekrandan kırp, aç, yapıştır ya da pencereye bırak) → çizim kendiliğinden hazırlanır →
"Illustrator'a aktar" ile açık belgeye düzenlenebilir vektör olarak yapıştırılır.
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
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QGuiApplication, QImage, QPainter, QPalette, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QColorDialog, QComboBox, QDoubleSpinBox, QFileDialog, QFontComboBox, QFormLayout,
    QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox,
    QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QToolButton, QVBoxLayout, QWidget,
)

from . import cizim, harita, illustrator, metin
from .svg import Style, to_svg

APP_NAME = "Görsel Çizici"
VERSION = "1.1"

# Açık tema: beyaz/açık gri zemin, tek vurgu rengi (deniz yeşili)
ACCENT = "#0F766E"
ACCENT_DARK = "#115E59"
ACCENT_SOFT = "#E0F2EF"
INK = "#1F2937"
MUTED = "#6B7280"
LINE = "#D7DCE2"
PANEL = "#F4F6F8"

PAGE_IMAGE, PAGE_MAP = 0, 1
CMD = "Cmd" if sys.platform == "darwin" else "Ctrl"

COLORS = [
    ("Görseldeki renkler", None),
    ("Siyah", "#000000"),
    ("Mavi", "#0070C0"),
    ("Kırmızı", "#E3262B"),
    ("Yeşil", "#2E9E44"),
    ("Mor", "#6B2C91"),
]

STYLE_SHEET = f"""
QMainWindow, QWidget#root, QWidget#form, QWidget#formviewport {{ background: #FFFFFF; }}
QWidget {{ color: {INK}; font-size: 13px; }}
QFrame#sidebar {{ background: {PANEL}; border-right: 1px solid {LINE}; }}
QLabel#appname {{ font-size: 17px; font-weight: 700; color: {INK}; }}
QLabel#appdesc {{ color: {MUTED}; font-size: 12px; }}
QLabel#version {{ color: #9CA3AF; font-size: 11px; }}
QListWidget#nav {{ background: transparent; border: none; outline: 0; font-size: 14px; }}
QListWidget#nav::item {{ padding: 10px 12px; border-radius: 8px; margin: 2px 0; color: {INK}; }}
QListWidget#nav::item:hover {{ background: #E9EDF1; }}
QListWidget#nav::item:selected {{ background: {ACCENT_SOFT}; color: {ACCENT_DARK}; font-weight: 600; }}
QLabel#pagetitle {{ font-size: 20px; font-weight: 700; }}
QLabel#pagedesc {{ color: {MUTED}; }}
QLabel#caption {{ color: {MUTED}; font-size: 12px; font-weight: 600; }}
QLabel#section {{ color: {ACCENT_DARK}; font-size: 12px; font-weight: 700; padding-top: 6px; }}
QLabel#hint {{ color: {MUTED}; font-size: 11px; }}
QLabel#status {{ color: {MUTED}; font-size: 12px; }}
QFrame#settings {{ background: {PANEL}; border-left: 1px solid {LINE}; }}
QLabel#settingstitle {{ font-size: 14px; font-weight: 700; }}
QFrame#actionbar {{ background: #FFFFFF; border-top: 1px solid {LINE}; }}
QLineEdit, QComboBox, QFontComboBox, QDoubleSpinBox, QPlainTextEdit {{
  background: #FFFFFF; border: 1px solid {LINE}; border-radius: 6px; padding: 4px 7px; }}
QLineEdit:focus, QComboBox:focus, QFontComboBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus {{ border-color: {ACCENT}; }}
QPushButton, QToolButton {{ background: #FFFFFF; border: 1px solid {LINE}; border-radius: 6px; padding: 6px 12px; }}
QPushButton:hover, QToolButton:hover {{ border-color: {ACCENT}; color: {ACCENT_DARK}; }}
QPushButton:disabled, QToolButton:disabled {{ color: #A0A7B0; background: #F7F8F9; }}
QPushButton#accent {{ background: {ACCENT}; color: #FFFFFF; border: none; font-weight: 600; padding: 8px 18px; }}
QPushButton#accent:hover {{ background: {ACCENT_DARK}; color: #FFFFFF; }}
QPushButton#accent:disabled {{ background: #9CC7C2; color: #F4FBFA; }}
QPushButton#outline {{ border: 1px solid {ACCENT}; color: {ACCENT_DARK}; font-weight: 600; }}
QPushButton#outline:disabled {{ border-color: {LINE}; color: #A0A7B0; }}
QToolButton::menu-indicator {{ image: url(@ARROW_DOWN@); width: 9px; height: 9px;
  subcontrol-position: right center; right: 8px; }}
QToolButton {{ padding-right: 24px; }}
QDoubleSpinBox {{ padding-right: 20px; }}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ subcontrol-origin: border; width: 18px; border: none;
  background: transparent; }}
QDoubleSpinBox::up-button {{ subcontrol-position: top right; }}
QDoubleSpinBox::down-button {{ subcontrol-position: bottom right; }}
QDoubleSpinBox::up-arrow {{ image: url(@ARROW_UP@); width: 8px; height: 8px; }}
QDoubleSpinBox::down-arrow {{ image: url(@ARROW_DOWN@); width: 8px; height: 8px; }}
QComboBox {{ padding-right: 24px; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: center right; width: 22px; border: none; }}
QComboBox::down-arrow {{ image: url(@ARROW_DOWN@); width: 9px; height: 9px; }}
QComboBox QAbstractItemView {{ background: #FFFFFF; border: 1px solid {LINE}; selection-background-color: {ACCENT_SOFT};
  selection-color: {INK}; }}
QMenu {{ background: #FFFFFF; border: 1px solid {LINE}; padding: 4px; }}
QMenu::item {{ padding: 6px 16px; border-radius: 4px; }}
QMenu::item:selected {{ background: {ACCENT_SOFT}; color: {ACCENT_DARK}; }}
QCheckBox {{ spacing: 7px; }}
QScrollArea {{ border: none; background: transparent; }}
"""


def _arrow_images(folder: str) -> tuple[str, str]:
    """Açılır kutu ve sayı kutusu okları (stil dosyası resim ister)."""
    paths = []
    for name, pts in (("ok-asagi.png", [(3, 6), (9, 12), (15, 6)]), ("ok-yukari.png", [(3, 12), (9, 6), (15, 12)])):
        path = os.path.join(folder, name)
        img = QImage(18, 18, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(MUTED), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            p.drawLine(x0, y0, x1, y1)
        p.end()
        img.save(path)
        paths.append(path.replace("\\", "/"))
    return paths[0], paths[1]


def style_sheet(folder: str) -> str:
    down, up = _arrow_images(folder)
    return STYLE_SHEET.replace("@ARROW_DOWN@", down).replace("@ARROW_UP@", up)


def light_palette() -> QPalette:
    """Mac karanlık modda da açık renkli, okunaklı arayüz."""
    pal = QPalette()
    roles = {
        QPalette.ColorRole.Window: "#FFFFFF", QPalette.ColorRole.WindowText: INK,
        QPalette.ColorRole.Base: "#FFFFFF", QPalette.ColorRole.AlternateBase: PANEL,
        QPalette.ColorRole.Text: INK, QPalette.ColorRole.Button: "#FFFFFF",
        QPalette.ColorRole.ButtonText: INK, QPalette.ColorRole.Highlight: ACCENT,
        QPalette.ColorRole.HighlightedText: "#FFFFFF", QPalette.ColorRole.ToolTipBase: "#FFFFFF",
        QPalette.ColorRole.ToolTipText: INK, QPalette.ColorRole.PlaceholderText: "#9CA3AF",
        QPalette.ColorRole.Link: ACCENT,
    }
    for role, col in roles.items():
        pal.setColor(role, QColor(col))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText, QPalette.ColorRole.WindowText):
        pal.setColor(QPalette.ColorGroup.Disabled, role, QColor("#A0A7B0"))
    return pal


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
def _paint_empty(p: QPainter, r, text: str):
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(LINE), 1))
    p.setBrush(QColor("#FAFBFC"))
    p.drawRoundedRect(QRectF(r), 10, 10)
    p.setPen(QColor(MUTED))
    p.drawText(r, Qt.AlignmentFlag.AlignCenter, text)


def _paint_frame(p: QPainter, r):
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(LINE), 1))
    p.setBrush(QColor("#FFFFFF"))
    p.drawRoundedRect(QRectF(r), 10, 10)


class ImageView(QWidget):
    def __init__(self, placeholder: str):
        super().__init__()
        self.pix = None
        self.placeholder = placeholder
        self.setMinimumSize(220, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_pixmap(self, pix):
        self.pix = pix
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        r = self.rect().adjusted(1, 1, -2, -2)
        if self.pix is None:
            _paint_empty(p, r, self.placeholder)
            return
        _paint_frame(p, r)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        inner = r.adjusted(10, 10, -10, -10)
        sz = self.pix.size()
        sz.scale(inner.size(), Qt.AspectRatioMode.KeepAspectRatio)
        x = inner.x() + (inner.width() - sz.width()) // 2
        y = inner.y() + (inner.height() - sz.height()) // 2
        p.drawPixmap(x, y, sz.width(), sz.height(), self.pix)


class SvgView(QWidget):
    def __init__(self, placeholder: str):
        super().__init__()
        self.renderer = None
        self.placeholder = placeholder
        self.setMinimumSize(220, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_svg(self, svg: str | None):
        self.renderer = QSvgRenderer(QByteArray(svg.encode("utf-8"))) if svg else None
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        r = self.rect().adjusted(1, 1, -2, -2)
        if not self.renderer or not self.renderer.isValid():
            _paint_empty(p, r, self.placeholder)
            return
        _paint_frame(p, r)
        vb = self.renderer.viewBoxF()
        if vb.width() <= 0 or vb.height() <= 0:
            return
        inner = r.adjusted(10, 10, -10, -10)
        k = min(inner.width() / vb.width(), inner.height() / vb.height())
        w, h = vb.width() * k, vb.height() * k
        self.renderer.render(p, QRectF(inner.x() + (inner.width() - w) / 2, inner.y() + (inner.height() - h) / 2, w, h))


def _card(caption: str, view: QWidget) -> QWidget:
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(6)
    c = QLabel(caption.upper())
    c.setObjectName("caption")
    v.addWidget(c)
    v.addWidget(view, 1)
    return w


# ---------------------------------------------------------------- arka plan işi
class Worker(QThread):
    done = Signal(object, object, float)
    failed = Signal(str)

    def __init__(self, rgb, use_text, detail, yazisiz=False):
        super().__init__()
        self.rgb, self.use_text, self.detail, self.yazisiz = rgb, use_text, detail, yazisiz

    def run(self):
        t = time.time()
        try:
            scene, texts = cizim.analyze(self.rgb, self.use_text, self.detail, self.yazisiz)
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
        self.setWindowTitle(APP_NAME)
        self.settings = QSettings("LimitGrup", "GorselCizici")
        self.rgb = None
        self.scene = None
        self.texts = []
        self.current_svg = ""
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
        self.resize(1180, 740)
        self.setMinimumSize(900, 560)

    # ------------------------------------------------ arayüz
    def _build(self):
        root = QWidget()
        root.setObjectName("root")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._sidebar())
        self.pages = QStackedWidget()
        self.pages.addWidget(self._image_page())
        self.pages.addWidget(self._map_page())
        body.addWidget(self.pages, 1)
        body.addWidget(self._settings_panel())
        outer.addLayout(body, 1)
        outer.addWidget(self._action_bar())
        self.setCentralWidget(root)
        self.setStyleSheet(style_sheet(self.out_dir))
        self.nav.currentRowChanged.connect(self._page_changed)

    def _sidebar(self) -> QWidget:
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(200)
        v = QVBoxLayout(side)
        v.setContentsMargins(16, 18, 12, 14)
        v.setSpacing(4)
        name = QLabel(APP_NAME)
        name.setObjectName("appname")
        desc = QLabel("Görseldeki çizimi düzenlenebilir vektöre çevirir.")
        desc.setObjectName("appdesc")
        desc.setWordWrap(True)
        v.addWidget(name)
        v.addWidget(desc)
        v.addSpacing(14)
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        for text in ("Görselden çizim", "Dilsiz harita"):
            QListWidgetItem(text, self.nav)
        self.nav.setCurrentRow(PAGE_IMAGE)
        self.nav.setFixedHeight(100)
        v.addWidget(self.nav)
        v.addStretch(1)
        ver = QLabel(f"Sürüm {VERSION} · internetsiz çalışır")
        ver.setObjectName("version")
        ver.setWordWrap(True)
        v.addWidget(ver)
        return side

    def _page_header(self, title: str, desc: str) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("pagetitle")
        d = QLabel(desc)
        d.setObjectName("pagedesc")
        d.setWordWrap(True)
        v.addWidget(t)
        v.addWidget(d)
        return w

    def _image_page(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(22, 18, 22, 14)
        v.setSpacing(12)
        v.addWidget(self._page_header(
            "Görselden çizim",
            "Grafik, şekil ya da harita görselini verin; aynısı vektör olarak yeniden çizilir."))
        row = QHBoxLayout()
        row.setSpacing(8)
        b1 = QPushButton("Ekrandan kırp")
        b2 = QPushButton("Dosyadan aç…")
        b3 = QPushButton("Panodan yapıştır")
        b1.setToolTip("Ekranda bir bölge seçin; seçtiğiniz kısım çizilir.")
        b1.clicked.connect(self.capture_screen)
        b2.clicked.connect(self.open_image)
        b3.clicked.connect(self.paste_image)
        for b in (b1, b2, b3):
            row.addWidget(b)
        row.addStretch(1)
        self.draw_btn = QPushButton("Çiz")
        self.draw_btn.setObjectName("outline")
        self.draw_btn.setEnabled(False)
        self.draw_btn.clicked.connect(self.draw)
        row.addWidget(self.draw_btn)
        v.addLayout(row)
        self.ocr_chk = QCheckBox("Yazıları düzenlenebilir yazıya çevir (Mac'in yazı tanıması)")
        self.ocr_chk.setChecked(True)
        if not metin.available():
            self.ocr_chk.setChecked(False)
            self.ocr_chk.setEnabled(False)
            self.ocr_chk.setText("Yazılar harf şekli olarak çizilir (bu bilgisayarda yazı tanıma yok)")
        v.addWidget(self.ocr_chk)
        self.notext_chk = QCheckBox("Yazıları atla, yalnız şekilleri çiz (yazı altındaki çizimler yine çizilir)")
        self.notext_chk.toggled.connect(self._notext_toggled)
        v.addWidget(self.notext_chk)
        pv = QHBoxLayout()
        pv.setSpacing(14)
        self.in_view = ImageView("Henüz görsel yok\n\nEkrandan kırpın, dosyadan açın,\nyapıştırın ya da dosyayı bu pencereye bırakın")
        self.out_view = SvgView("Vektör çizim burada görünecek")
        pv.addWidget(_card("Kaynak görsel", self.in_view), 1)
        pv.addWidget(_card("Vektör çizim", self.out_view), 1)
        v.addLayout(pv, 1)
        return w

    def _map_page(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(22, 18, 22, 14)
        v.setSpacing(12)
        v.addWidget(self._page_header(
            "Dilsiz harita",
            "Dünya ya da Türkiye haritasını yazısız, temiz vektör olarak oluşturur (Natural Earth verisi)."))
        row = QHBoxLayout()
        row.setSpacing(16)
        form = QFormLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(7)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
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
        self.map_points.setFixedHeight(80)
        form.addRow("Harita", self.map_kind)
        form.addRow("İzdüşüm", self.map_proj)
        form.addRow("Orta boylam", self.map_center)
        form.addRow("Kıyı ayrıntısı", self.map_detail)
        form.addRow("", self.map_borders)
        form.addRow("", self.map_neigh)
        form.addRow("Meridyenler", self.map_lon)
        form.addRow("Paraleller", self.map_lat)
        form.addRow("", self.map_eq)
        form.addRow("", self.map_labels)
        self.map_land.setToolTip("Kara rengini seçin")
        self.map_sea.setToolTip("Deniz rengini seçin (iptal: renksiz)")
        form.addRow("Kara rengi", self.map_land)
        form.addRow("Deniz rengi", self.map_sea)
        form.addRow("Noktalar", self.map_points)
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        sc = QWidget()
        sc.setObjectName("form")
        form.setContentsMargins(0, 0, 8, 0)
        sc.setLayout(form)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        area.viewport().setObjectName("formviewport")
        area.setWidget(sc)
        lv.addWidget(area, 1)
        b = QPushButton("Haritayı oluştur")
        b.setObjectName("outline")
        b.clicked.connect(self.make_map)
        lv.addWidget(b)
        left.setFixedWidth(360)
        row.addWidget(left)
        self.map_view = SvgView("Harita burada görünecek")
        row.addWidget(_card("Harita önizlemesi", self.map_view), 1)
        v.addLayout(row, 1)
        for cb in (self.map_kind, self.map_proj, self.map_detail):
            cb.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            cb.setMinimumContentsLength(12)
        self._show_color(self.map_land)
        self._show_color(self.map_sea)
        self.map_kind.currentIndexChanged.connect(self._map_kind_changed)
        self._map_kind_changed()
        return w

    def _settings_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("settings")
        panel.setFixedWidth(250)
        v = QVBoxLayout(panel)
        v.setContentsMargins(16, 18, 16, 14)
        v.setSpacing(6)
        t = QLabel("Çıktı ayarları")
        t.setObjectName("settingstitle")
        v.addWidget(t)
        info = QLabel("Değişiklikler çizime hemen uygulanır.")
        info.setObjectName("hint")
        info.setWordWrap(True)
        v.addWidget(info)

        def section(text):
            lab = QLabel(text.upper())
            lab.setObjectName("section")
            v.addWidget(lab)

        def field(text, widget):
            lab = QLabel(text)
            v.addWidget(lab)
            v.addWidget(widget)

        self.font_box = QFontComboBox()
        self.font_box.setEditable(True)
        self.pt_box = QDoubleSpinBox()
        self.pt_box.setRange(0, 72)
        self.pt_box.setDecimals(1)
        self.pt_box.setSingleStep(0.5)
        self.pt_box.setSuffix(" pt")
        self.pt_box.setSpecialValueText("görseldeki gibi")
        self.stroke_box = QDoubleSpinBox()
        self.stroke_box.setRange(0, 10)
        self.stroke_box.setDecimals(2)
        self.stroke_box.setSingleStep(0.25)
        self.stroke_box.setSuffix(" pt")
        self.stroke_box.setSpecialValueText("görseldeki gibi")
        self.color_box = QComboBox()
        for name, _ in COLORS:
            self.color_box.addItem(name)
        self.width_box = QDoubleSpinBox()
        self.width_box.setRange(0, 1000)
        self.width_box.setDecimals(0)
        self.width_box.setSuffix(" mm")
        self.width_box.setSpecialValueText("otomatik")

        section("Yazı")
        field("Yazı tipi", self.font_box)
        field("Punto", self.pt_box)
        hint = QLabel("Yazıların ortalama boyu; çizim buna göre ölçeklenir.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        v.addWidget(hint)
        section("Çizgi")
        field("Kalınlık", self.stroke_box)
        field("Renk", self.color_box)
        section("Boyut")
        field("Genişlik", self.width_box)
        v.addStretch(1)

        self.font_box.currentFontChanged.connect(self._style_changed)
        self.color_box.currentIndexChanged.connect(self._style_changed)
        for wdg in (self.pt_box, self.stroke_box, self.width_box):
            wdg.valueChanged.connect(self._style_changed)
        return panel

    def _action_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("actionbar")
        h = QHBoxLayout(bar)
        h.setContentsMargins(18, 10, 18, 10)
        h.setSpacing(8)
        self.status = QLabel("Başlamak için bir görsel verin.")
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        h.addWidget(self.status, 1)
        self.save_btn = QToolButton()
        self.save_btn.setText("Kaydet")
        self.save_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self.save_btn)
        menu.addAction("PDF olarak kaydet…", self.save_pdf)
        menu.addAction("SVG olarak kaydet…", self.save_svg)
        self.save_btn.setMenu(menu)
        self.copy_btn = QPushButton("Kopyala (vektör)")
        self.copy_btn.setToolTip(f"Illustrator'da {CMD}+V ile yapıştırın; düzenlenebilir çizim olarak gelir.")
        self.send_btn = QPushButton("Illustrator'a aktar")
        self.send_btn.setObjectName("accent")
        self.send_btn.setToolTip("Açık Illustrator belgesine düzenlenebilir çizim olarak yapıştırır.")
        for b in (self.save_btn, self.copy_btn, self.send_btn):
            b.setEnabled(False)
            h.addWidget(b)
        self.send_btn.clicked.connect(self.send_to_illustrator)
        self.copy_btn.clicked.connect(self.copy_vector)
        return bar

    def _page(self) -> int:
        return self.pages.currentIndex()

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
        self.notext_chk.setChecked(str(s.value("yazisiz", "false")).lower() in ("true", "1"))

    def _save_settings(self):
        s = self.settings
        s.setValue("font", self.font_family())
        s.setValue("punto", self.pt_box.value())
        s.setValue("renk", self.color_box.currentIndex())
        s.setValue("kontur", self.stroke_box.value())
        s.setValue("genislik", self.width_box.value())
        s.setValue("yazisiz", self.notext_chk.isChecked())

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
        self.nav.setCurrentRow(PAGE_IMAGE)
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
                self.set_status("Ekran kırpma açılamadı. Win+Shift+S ile kırpıp Panodan yapıştır'a basın.")
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
        self.worker = Worker(self.rgb, self.ocr_chk.isChecked(), 1.0, self.notext_chk.isChecked())
        self.worker.done.connect(self._draw_done)
        self.worker.failed.connect(self._draw_failed)
        self.worker.start()

    def _notext_toggled(self, on):
        self.ocr_chk.setEnabled(not on and metin.available())
        if not self._loading:
            self._save_settings()

    def _draw_failed(self, msg):
        self.draw_btn.setEnabled(True)
        self.draw_btn.setText("Çiz")
        self.set_status(f"Çizilemedi: {msg}")

    def _draw_done(self, scene, texts, secs):
        self.draw_btn.setEnabled(True)
        self.draw_btn.setText("Yeniden çiz")
        self.scene = scene
        self.texts = texts
        self._rebuild_image_svg()
        n_txt = sum(1 for e in scene.elements if e.kind == "text")
        extra = f" · {n_txt} yazı düzenlenebilir" if n_txt else ""
        self.set_status(f"Çizildi ({secs:.1f} sn): {' · '.join(scene.notes) if scene.notes else ''}{extra}. "
                        "Kontrol edip “Illustrator'a aktar”a basın.")

    def measure(self, text: str):
        f = QFont(self.font_family())
        f.setPixelSize(100)          # piksel: ekran çözünürlüğünden bağımsız
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
        if self._page() == PAGE_IMAGE:
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
        self._show_color(btn)

    @staticmethod
    def _show_color(btn):
        """Renk düğmesi seçilen rengi gösterir."""
        t = btn.text()
        if t.startswith("#"):
            c = QColor(t)
            fg = "#111827" if c.lightness() > 140 else "#FFFFFF"
            btn.setStyleSheet(f"QPushButton {{ background: {t}; color: {fg}; border: 1px solid {LINE}; }}")
        else:
            btn.setStyleSheet("")

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
        self.set_status("Harita hazır. “Illustrator'a aktar”a basın ya da kopyalayın.")

    def _page_changed(self, i):
        if i < 0:
            return
        self.pages.setCurrentIndex(i)
        if i == PAGE_IMAGE:
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
        for b in (self.send_btn, self.save_btn, self.copy_btn):
            b.setEnabled(ready)

    def _out_name(self) -> str:
        return "harita" if self._page() == PAGE_MAP else "cizim"

    def write_output_file(self) -> str:
        path = os.path.join(self.out_dir, f"{self._out_name()}-{time.strftime('%H%M%S')}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + self.current_svg)
        return path

    def send_to_illustrator(self):
        if not self.current_svg:
            return
        path = self.write_output_file()
        self.set_status("Illustrator'a aktarılıyor…")
        QApplication.processEvents()
        ok, msg = illustrator.send(path)
        if ok:
            self.set_status("Illustrator'a aktarıldı: açık belgeye düzenlenebilir çizim olarak yapıştırıldı "
                            "(belge açık değilse yeni belge olarak açıldı).")
        else:
            self.set_status(f"Aktarılamadı: {msg} “Kopyala (vektör)”a basıp Illustrator'da {CMD}+V ile yapıştırabilirsiniz.")

    def _ask_save_path(self, title: str, ext: str) -> str | None:
        start = os.path.join(self.settings.value("save_dir", os.path.expanduser("~")), f"{self._out_name()}.{ext}")
        path, _ = QFileDialog.getSaveFileName(self, title, start, f"{ext.upper()} (*.{ext})")
        if not path:
            return None
        if not path.lower().endswith("." + ext):
            path += "." + ext
        self.settings.setValue("save_dir", os.path.dirname(path))
        return path

    def save_svg(self):
        if not self.current_svg:
            return
        path = self._ask_save_path("SVG olarak kaydet", "svg")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + self.current_svg)
        self.set_status(f"Kaydedildi: {path}")

    def save_pdf(self):
        if not self.current_svg:
            return
        path = self._ask_save_path("PDF olarak kaydet", "pdf")
        if not path:
            return
        try:
            data = illustrator.svg_to_pdf(self.current_svg)
            with open(path, "wb") as f:
                f.write(data)
        except Exception as e:  # noqa: BLE001
            self.set_status(f"PDF kaydedilemedi: {e}")
            return
        self.set_status(f"Kaydedildi: {path} (Illustrator'da açınca düzenlenebilir)")

    def copy_vector(self):
        if not self.current_svg:
            return
        if not illustrator.copy_vector(self.current_svg):
            # Mac panosu kullanılamadı: Qt ile kopyala (SVG + dosya; Windows'ta PDF de)
            path = self.write_output_file()
            md = QMimeData()
            md.setData("image/svg+xml", QByteArray(self.current_svg.encode("utf-8")))
            md.setUrls([QUrl.fromLocalFile(path)])
            if sys.platform.startswith("win"):
                try:
                    pdf = illustrator.svg_to_pdf(self.current_svg)
                    md.setData('application/x-qt-windows-mime;value="Portable Document Format"', QByteArray(pdf))
                except Exception:  # noqa: BLE001
                    md.setText(self.current_svg)
            else:
                md.setText(self.current_svg)
            QGuiApplication.clipboard().setMimeData(md)
        self.set_status(f"Kopyalandı. Illustrator'da {CMD}+V ile yapıştırın — düzenlenebilir çizim olarak gelir.")

    def set_status(self, msg: str):
        self.status.setText(msg)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")          # her sistemde aynı, açık renkli görünüm
    app.setPalette(light_palette())
    win = MainWindow()
    win.show()
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        win.load_path(sys.argv[1])
    sys.exit(app.exec())
