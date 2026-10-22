# İklim Grafiği Çizici

`iklim-grafigi-cizici.html` tarayıcıda çalışan tek dosyalık bir araçtır.
Çift tıklayıp aç; kurulum gerekmez.

1. **Görsel aç** (ya da sürükle / Ctrl+V). Görseldeki grafikler kendiliğinden
   bulunur; A, B, C… diye sekmelere ayrılır. Sütunlar ve sıcaklık çizgisi işaretlenir.
2. Görselin altındaki kutulara her eksenin **en alttaki ve en üstteki sayısını** yaz.
   Sayılar bütün grafiklerde aynıysa "Bu sayılar bütün grafiklerde aynı"yı işaretle.
   claude.ai'de açıldığında bu sayıları Claude kendisi okur.
3. Sağdaki yeni grafiği görselle karşılaştır. Yanlış bir değeri tabloda düzelt
   ya da görseldeki işareti sürükle.
4. **Illustrator için kopyala** → Illustrator'da Ctrl+V (ya da SVG'yi indirip
   Dosya › Aç). Grafik gerçek ölçüsünde, düzenlenebilir vektör olarak gelir.

En üstteki "Sıradaki adım" kutusu her an ne yapman gerektiğini yazar.

## Illustrator scripti

`../illustrator-scripts/iklim-grafigi.jsx` aynı grafikleri doğrudan Illustrator
içinde, CMYK renklerle çizer. Araçta **Script için veri kopyala**'ya bas,
Illustrator'da Dosya › Komut Dosyaları › Diğer Komut Dosyası… ile scripti aç,
"Veri" sekmesine yapıştır ve **Grafiği çiz**'e bas.
