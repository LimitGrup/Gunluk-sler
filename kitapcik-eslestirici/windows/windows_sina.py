# -*- coding: utf-8 -*-
"""
Windows derlemesinden önce motorun Windows'ta da Mac/Linux'taki gibi çalıştığını
sınar: testler/ klasöründeki örnek PDF testleri aynı anda çalıştırılır, her
birinin beklenen özet satırları aranır. Çıktıların tamamı da yazdırılır.

Kullanım:  python windows_sina.py <app.py> <çalışma_klasörü>
(PYTHONUTF8=1 ile çalıştırın: testler Türkçe yazdırır.)
"""
import os
import subprocess
import sys
from pathlib import Path

BEKLENEN = {
    "kontrol": ["=== ortaokul: 0 HATA", "=== tyt: 0 HATA", "=== tyt_nokta: 0 HATA",
                "=== ayni_dosya: 0 HATA", "=== hatali: 16 HATA",
                "=== hatali_iki_baski: 16 HATA", "Temiz çiftlerde toplam HATA: 0"],
    "eşleştir": ["ortaokul: 70/70 doğru eşleşme", "ortaokul_baski: 70/70 doğru eşleşme",
                 "tyt: 125/125 doğru eşleşme", "tyt_nokta: 125/125 doğru eşleşme"],
    "cevap": ["cevap 70/70, B numarası 70/70 doğru", "cevap 125/125, B numarası 125/125 doğru"],
    "tire": ["SONUÇ: temiz"],
    "kesir": ["kesir_B: 0 sorun (beklenen 0)", "yakalandı mı: True"],
    "düzen": ["SONUÇ: temiz"],
    "kds": ["temiz: 0 sorun", "SONUÇ: tamam"],
}


def main(app, kok):
    kok = Path(kok)
    kok.mkdir(parents=True, exist_ok=True)
    T = Path(__file__).resolve().parent.parent / "testler"
    py = sys.executable
    ornek = kok / "ornek"
    subprocess.run([py, str(T / "ornek_pdf_uret.py"), str(ornek)], check=True)
    isler = {
        "kontrol": [str(T / "kontrol_sina.py"), app, str(ornek)],
        "eşleştir": [str(T / "eslestir_sina.py"), app, str(ornek), str(kok / "esl.json")],
        "cevap": [str(T / "cevap_sina.py"), app, str(ornek)],
        "tire": [str(T / "tire_sina.py"), app, str(kok / "tire")],
        "kesir": [str(T / "kesir_sina.py"), app, str(kok / "kesir")],
        "düzen": [str(T / "duzen_sina.py"), app, str(kok / "duzen")],
        "kds": [str(T / "kds_sina.py"), app, str(ornek / "ortaokul_A_baski.pdf"),
                str(kok / "kds")],
    }
    ortam = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    calisan = {ad: subprocess.Popen([py] + arg, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, env=ortam)
               for ad, arg in isler.items()}
    hepsi = True
    for ad, p in calisan.items():
        cikti = p.communicate()[0].decode("utf-8", "replace")
        eksik = [b for b in BEKLENEN[ad] if b not in cikti]
        tamam = p.returncode == 0 and not eksik
        hepsi &= tamam
        print(f"\n######## {ad}: {'tamam' if tamam else 'SORUN'}"
              + (f" (çıkış kodu {p.returncode})" if p.returncode else "")
              + (f" — bulunamayan: {eksik}" if eksik else ""))
        print(cikti)
    print("WINDOWS SONUÇ:", "tamam" if hepsi else "SORUN")
    return 0 if hepsi else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
