# Kitapçık Eşleştirici (v2.19)

macOS uygulaması (`Kitapcik Eslestirici.app`). İki iş yapar:

| Düğme | Ne yapar | Çıktı |
|---|---|---|
| **EŞLEŞTİR** | A kitapçığındaki her sorunun B'de kaçıncı soru olduğunu bulur, kazanım tablosunu doldurur. | `kazanim_tablosu.xlsx` |
| **A–B KONTROL** *(yeni)* | B kitapçığını A'ya göre denetler: A'daki her soru B'de var mı, aynı mı, numaralar ve metne bağlı gruplar düzgün mü? | `kitapcik_kontrol_raporu.xlsx` + işaretli PDF'ler |

EŞLEŞTİR'in çalışma mantığı değiştirilmedi. Örnek kitapçıklarda Excel çıktısı v2.18 ile hücre hücre aynıdır (`testler/eslestir_sina.py`).

## A–B KONTROL neye bakar?

Her kitapçık önce **kendi içinde**, sonra **A ile B karşılıklı** denetlenir.

1. **Numaralandırma (A ve B ayrı ayrı):** Her testte 1'den N'e eksiksiz gidiyor mu? Atlanan numara, mükerrer
   numara ("8." iki kez) ya da sırasız numaralı şıklı soru varsa yerini ve büyük olasılıkla doğru
   numarayı yazar. Bir sorunun içinde ikinci bir şık takımı varsa (numarası düşmüş soru) onu da bildirir.
2. **Metne bağlı grup başlıkları (A ve B ayrı ayrı):** "14 ve 15. soruları…", "1-4. soruları…",
   "12. ve 13. soruları…" gibi başlıklardaki numaralar, altındaki sorularla aynı mı?
3. **A'daki her soru B'de var mı?** Eşleştirme her testin içinde, dersler arasında yapılır
   (soru başka dersin aralığına kaymışsa yakalanır). Önce magenta soru kodu kullanılır; kod yoksa
   gövde + şıkların tam metni karşılaştırılır (Macar algoritması, birebir atama).
4. **Eşleşen her çift için:**
   - Metin ve şıklar birebir aynı mı? Farkı kelime düzeyinde gösterir.
   - Cevap harfi aynı mı? (renkli cevap ya da cevap anahtarı txt)
   - Ders aynı mı?
   - Görüntü aynı mı? (şekil, tablo, grafik farkı) Metinde görünmeyen şekil değişikliğini
     yakalamak için soru bölgesi A ve B'de görüntü olarak üst üste bindirilir.
5. **Metne bağlı gruplar A ↔ B:** A'daki grubun soruları B'de yine yan yana ve aynı başlık altında mı?
   Parça metni ve görüntüsü aynı mı?
6. **Aynı soru iki kez basılmış mı?** (bir kitapçıkta iki sorunun içeriği aynıysa)
7. **Otomatik yapıda (Lise / Ortaokul):** A ve B'nin test yapısı (test adları, soru sayıları) aynı mı?

### Rapor

- **Özet:** Her kontrol için TEMİZ / HATA / KONTROL ET.
- **Sorunlar:** Her sorun için önem, kitapçık, test, ders, soru, sayfa ve açıklama.
- **Soru Eşleşmesi:** A no → B no, metin %, görsel %, cevaplar ve durum.
- **Metne Bağlı Gruplar:** A grubu → B karşılığı, parça benzerliği ve durum.
- **İşaretli PDF:** Sorunlu sorular A ve B PDF'lerinin kopyasında çerçevelenir (kırmızı = hata,
  turuncu = elle bakılacak uyarı) ve not olarak açıklama eklenir.

### Bilinen sınırlar

- PDF'te **seçilebilir metin** olmalı. Yazılar eğriye çevrilmişse (outline) ya da taranmışsa önce
  OCR gerekir.
- B baskı PDF'i **sayfa sayfa** olmalı; montajlı (imposition, 2 sayfa yan yana) PDF desteklenmez.
- Baskı PDF'inde magenta cevaplar yoksa cevap kıyası yapılamaz. Bu durumda B cevap anahtarı
  txt'si verilebilir. Metin ve görüntü kıyası cevaplardan bağımsız çalışır.
- Görsel kıyas, A ve B'de düzeni farklı olan alanları (ör. A'da tam genişlik, B'de sütun içi parça)
  karşılaştırmaz. Bu alanlarda yalnızca metin kıyası yapılır.

## Testler

`testler/` klasöründeki betikler uygulamanın motorunu arayüzsüz çalıştırır:

```bash
pip install pymupdf numpy scipy openpyxl
python3 testler/ornek_pdf_uret.py /tmp/ornek          # gerçek dizgiye benzeyen A/B PDF'leri
python3 testler/eslestir_sina.py "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" /tmp/ornek /tmp/sonuc.json
python3 testler/kontrol_sina.py  "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" /tmp/ornek
```

Üretilen örnekler: iki sütunlu ve tek sütunlu (2x2 şıklı) sayfalar, metne bağlı gruplar, şekilli
sorular, magenta cevaplı ve cevapsız (baskı) B. `ortaokul_B_hatali.pdf` içine 9 tür bilinçli hata
eklenir: eksik soru, yanlış grup başlığı, mükerrer numara, kelime farkı, cevap farkı, şık farkı,
şekil farkı, parça farkı ve iki kez basılmış soru.

v2.19 sonuçları:

- Temiz çiftlerde 0 hata, 0 uyarı; eşleşme doğruluğu %100.
- Hatalı B'de 9 hatanın 9'u yakalanıyor.
