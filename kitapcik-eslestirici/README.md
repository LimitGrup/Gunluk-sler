# Kitapçık Eşleştirici (v2.20)

macOS uygulaması (`Kitapcik Eslestirici.app`). İki iş yapar:

| Düğme | Ne yapar | Çıktı |
|---|---|---|
| **EŞLEŞTİR** | A kitapçığındaki her sorunun B'de kaçıncı soru olduğunu bulur, kazanım tablosunu doldurur. | `kazanim_tablosu.xlsx` |
| **A–B KONTROL** *(yeni)* | B kitapçığını A'ya göre denetler: A'daki her soru B'de var mı, aynı mı, numaralar ve metne bağlı gruplar düzgün mü? | `kitapcik_kontrol_raporu.xlsx` + işaretli PDF'ler |

EŞLEŞTİR'in çalışma mantığı değiştirilmedi. Örnek kitapçıklarda Excel çıktısı v2.18 ile hücre hücre aynıdır (`testler/eslestir_sina.py`).

## A–B KONTROL: sorunsuz baskı kontrolü

Cevap kapalı **baskı PDF'leri** için tasarlandı; cevap açık PDF'lerle de çalışır. Cevap açık
PDF'lerde ek olarak A ve B'nin cevap harfleri de kıyaslanır.

Her kitapçık önce **kendi içinde**, sonra **A ile B karşılıklı** denetlenir.

1. **Açık kalan cevap:** Baskıda görünmemesi gereken renkli cevap harfi ya da soru kodu arar.
   Harf soru numarasının altında, şıkların solundaki boşlukta ya da magenta renkte olabilir.
   Şekil içindeki renkli etiketler (haritadaki kırmızı A, B, C gibi) cevap sayılmaz. Kitapçığın
   tamamı cevaplıysa tek bir "bu kitapçıkta cevaplar açık" uyarısı verilir.
2. **Numaralar branş branş düzgün mü (A ve B ayrı ayrı):** Her testte 1'den N'e eksiksiz gidiyor
   mu? Atlanan numara, mükerrer numara ("8." iki kez) ya da sırasız numaralı şıklı soru varsa
   yerini ve büyük olasılıkla doğru numarayı yazar. Bir sorunun içinde ikinci şık takımı varsa
   (numarası düşmüş soru) onu da bildirir.
3. **Metne bağlı grup başlıkları (A ve B ayrı ayrı):** "14 ve 15. soruları…", "1-4. soruları…",
   "12. ve 13. soruları…" gibi başlıklardaki numaralar altındaki sorularla aynı mı?
4. **A'daki her soru B'de var mı?** Soru metni ve şıklarıyla birlikte aranır. LGS düzeninde
   sorunun kendi metni sorunun parçası sayılır. Eşleştirme her testin içinde, dersler arasında
   yapılır; soru başka dersin aralığına kaymışsa yakalanır.
5. **Eşleşen her çift için:**
   - Metin ve şıklar birebir aynı mı? Fark kelime düzeyinde gösterilir.
   - Ders aynı mı?
   - Cevap harfi aynı mı? (cevap açık PDF'lerde)
   - Şekil ve resimler aynı mı? Sorudaki resim ve çizimler "şekil kutuları"na toplanır, her şekil
     kendi kutusunda görüntü olarak kıyaslanır. Satır aralığı ya da konum değişse de yalnızca
     gerçekten değişen şekil yakalanır.
6. **Metne bağlı gruplar A ↔ B:** A'daki grubun soruları B'de yine yan yana ve aynı başlık altında
   mı? Metin aynı mı? B'de bir grubun metni başka grubun sorularının üstüne düşmüşse açıkça yazar:
   "B'de metin ile altındaki sorular uyumsuz: B 5-8. soruların üstündeki metin, A'da 15-17.
   soruların metni".
7. **Aynı soru iki kez basılmış mı?**
8. **Otomatik yapıda (Lise / Ortaokul):** A ve B'nin test yapısı (test adları, soru sayıları)
   aynı mı?

Sayfa düzeni soru numaralarına göre çözülür. Her numaradan bir bölge başlar: soru tam
genişlikse sayfa boyu, değilse kendi sütunu. Böylece aynı sayfada tam genişlik soru (yan yana
A B C D şıklarıyla) ve iki sütun bir arada olsa da her satır kendi sorusunda kalır.

### Rapor

- **Özet:** Her kontrol için TEMİZ / HATA / KONTROL ET.
- **Sorunlar:** Her sorun için önem, kitapçık, test, ders, soru, sayfa ve açıklama.
- **Soru Eşleşmesi:** A no → B no, metin %, şekil/resim durumu, cevaplar ve durum.
- **Metne Bağlı Gruplar:** A grubu → B karşılığı, parça benzerliği ve durum.
- **İşaretli PDF:** Sorunlu yerler A ve B PDF'lerinin kopyasında çerçevelenir (kırmızı = hata,
  turuncu = elle bakılacak) ve not olarak açıklama eklenir. Sorun yoksa bu PDF oluşmaz.

### Bilinen sınırlar

- PDF'te **seçilebilir metin** olmalı. Yazılar eğriye çevrilmişse (outline) ya da taranmışsa önce
  OCR gerekir.
- B baskı PDF'i **sayfa sayfa** olmalı; montajlı (imposition, 2 sayfa yan yana) PDF desteklenmez.
- Bir şeklin parçaları arasındaki boşluk A ve B'de çok farklıysa "şekil sayısı farklı" uyarısı
  çıkabilir. Bu uyarılar "elle bakın" düzeyindedir.

### Gerçek kitapçıklarla deneme (8. sınıf Limit denemesi, sözel + sayısal, baskı PDF'leri)

| Çift | Soru | Sonuç | Süre |
|---|---|---|---|
| Sözel 1A ↔ 1B | 50 | 50/50 birebir eşleşme, 0 hata, 0 uyarı | ~2 sn |
| Sayısal 1A ↔ 1B | 40 | 40/40 birebir eşleşme, 0 hata, 0 uyarı | ~25 sn |

Sözel 1B'nin bir kopyasına üç hata eklendi: bir soru numarası değiştirildi, bir kelime silindi,
bir soruya magenta cevap harfi kondu. Üçü de doğru soruda yakalandı ("6. soru bulunamadı" ile
"'7.' yazıyor, beklenen numara büyük olasılıkla 6", "Metin farklı: «stratejik»", "Açık kalan
cevap harfi: 'C'").

## Testler

`testler/` klasöründeki betikler uygulamanın motorunu arayüzsüz çalıştırır:

```bash
pip install pymupdf numpy scipy openpyxl
python3 testler/ornek_pdf_uret.py /tmp/ornek          # gerçek dizgiye benzeyen A/B PDF'leri
python3 testler/eslestir_sina.py "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" /tmp/ornek /tmp/sonuc.json
python3 testler/kontrol_sina.py  "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" /tmp/ornek
```

Üretilen örnekler: iki sütunlu ve tek sütunlu (2x2 şıklı) sayfalar, metne bağlı gruplar, şekilli
sorular, magenta cevaplı ve cevapsız (baskı) A ile B. `ortaokul_B_hatali.pdf` içine 10 tür bilinçli
hata eklenir: eksik soru, yanlış grup başlığı, mükerrer numara, kelime farkı, cevap farkı, şık farkı,
şekil farkı, parça farkı, iki kez basılmış soru, metni yer değiştirmiş iki grup. Baskı varyantında
(`ortaokul_B_hatali_baski.pdf`) ayrıca bir soruda cevap harfi açık bırakılır.

v2.19 sonuçları:

- Temiz çiftlerde 0 hata; eşleşme doğruluğu %100. Cevap açık örneklerde yalnızca "bu kitapçıkta
  cevaplar açık" bilgisi çıkar.
- Hatalı B'de 10 hatanın 10'u yakalanıyor.
- İki kitapçık da cevapsız baskıyken cevap farkı dışındaki 9 hatanın 9'u ve açık kalan cevap
  yakalanıyor (cevap baskıda görünmediği için kıyaslanamaz).
