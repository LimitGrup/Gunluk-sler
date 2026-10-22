# İklim Grafiği Çizici

`iklim-grafigi-cizici.html` tarayıcıda çalışan tek dosyalık bir araçtır.
Çift tıklayıp aç; kurulum gerekmez. Ders kitaplarındaki **iklim** (sütun + çizgi,
iki eksen), **sütun** ve **çizgi** grafiklerini okur; türü kendisi anlar.

1. **Görsel aç** (ya da sürükle / Ctrl+V). Gerisini araç kendisi yapar:
   görseldeki grafikleri bulur (A, B, C… sekmeleri), eksenlerdeki sayıları ve
   yıl/ay etiketlerini okur, sütunları ve çizgiyi ölçer, grafiği sağda yeniden çizer.
2. Sağdaki yeni grafiği görselle karşılaştır. Bir eksen sayısı okunamadıysa
   görselin altındaki kutu kırmızı olur; o sayıyı yazıp **Grafiği oluştur**'a bas.
   Yanlış bir değeri tabloda düzelt ya da görseldeki işareti sürükle.
3. claude.ai'de açıldığında okunamayan yerleri Claude'a da sorabilir.
4. **Illustrator için kopyala** → Illustrator'da Ctrl+V (ya da SVG'yi indirip
   Dosya › Aç). Grafik gerçek ölçüsünde, düzenlenebilir vektör olarak gelir.

En üstteki "Sıradaki adım" kutusu her an ne yapman gerektiğini yazar.

En iyi sonuç için grafiğin kendi görselini (PNG ya da kaliteli JPG) ver; ekran
görüntüsü ya da çok sıkıştırılmış, bulanık görsellerde bazı sayılar okunamayabilir.
Aynı grafikte birden çok sütun ya da çizgi serisi henüz desteklenmiyor.

## Illustrator scripti

`../illustrator-scripts/iklim-grafigi.jsx` iklim grafiklerini doğrudan Illustrator
içinde, CMYK renklerle çizer (sütun ve çizgi grafikleri için "Illustrator için
kopyala"yı kullan). Araçta **Script için veri kopyala**'ya bas,
Illustrator'da Dosya › Komut Dosyaları › Diğer Komut Dosyası… ile scripti aç,
"Veri" sekmesine yapıştır ve **Grafiği çiz**'e bas.
