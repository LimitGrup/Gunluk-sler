#!/bin/bash
# Görsel Çizici'yi kaynaktan çalıştırır; ilk seferde gerekli paketleri kurar.
cd "$(dirname "$0")" || exit 1
V="$HOME/Library/Application Support/GorselCizici/venv"
if [ ! -x "$V/bin/python" ]; then
  echo "İlk çalıştırma: gerekli paketler kuruluyor (birkaç dakika sürebilir)…"
  python3 -m venv "$V" || { echo "Python 3 bulunamadı."; read -r; exit 1; }
  "$V/bin/pip" install --upgrade pip
  "$V/bin/pip" install -r requirements.txt || { echo "Paketler kurulamadı."; read -r; exit 1; }
fi
exec "$V/bin/python" GorselCizici.py "$@"
