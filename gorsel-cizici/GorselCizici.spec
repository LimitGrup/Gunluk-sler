# -*- mode: python ; coding: utf-8 -*-
# PyInstaller tarifi:  pyinstaller --noconfirm GorselCizici.spec
import os
import sys

from PyInstaller.utils.hooks import collect_submodules

hidden = collect_submodules("skimage.morphology") + collect_submodules("skimage.measure") + ["scipy.ndimage"]
if sys.platform == "darwin":
    hidden += ["Vision", "Quartz", "Foundation", "AppKit", "objc"]

icon = None
if sys.platform == "darwin" and os.path.exists("simge.icns"):
    icon = "simge.icns"
elif sys.platform.startswith("win") and os.path.exists("simge.ico"):
    icon = "simge.ico"

a = Analysis(
    ["GorselCizici.py"],
    pathex=["."],
    datas=[("gorsel_cizici/veri", "gorsel_cizici/veri")],
    hiddenimports=hidden,
    excludes=["tkinter", "matplotlib", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtQuick",
              "PySide6.QtQml", "PySide6.QtMultimedia", "PySide6.Qt3DCore", "PySide6.QtCharts", "PySide6.QtPdf"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="GorselCizici", console=False, icon=icon)
coll = COLLECT(exe, a.binaries, a.datas, name="GorselCizici")
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="GorselCizici.app",
        icon=icon,
        bundle_identifier="com.limitgrup.gorselcizici",
        info_plist={
            "CFBundleName": "GorselCizici",
            "CFBundleDisplayName": "Görsel Çizici",
            "CFBundleShortVersionString": "1.1",
            "NSHighResolutionCapable": True,
            "NSAppleEventsUsageDescription": "Çizimi Illustrator'daki açık belgeye düzenlenebilir olarak aktarmak için.",
        },
    )
