# İklim Grafiği Çizici

`iklim-grafigi-cizici.html` tarayıcıda çalışan tek dosyalık bir araçtır.
Çift tıklayıp aç; kurulum gerekmez. Ders kitaplarındaki **iklim** (sütun + çizgi,
iki eksen), **sütun**, **çizgi** ve **gruplu sütun** (her kategoride yan yana renkli
sütunlar, bir ya da iki eksen) grafiklerini okur; türü kendisi anlar. Eksenleri
çentiksiz (yalnız kılavuz çizgili) ve sayıları renkli basılmış grafikleri de okur.

1. **Görsel aç** (ya da sürükle / Ctrl+V). Gerisini araç kendisi yapar:
   görseldeki grafikleri bulur (A, B, C… sekmeleri), eksenlerdeki sayıları ve
   yıl/ay etiketlerini okur, sütunları ve çizgiyi ölçer, grafiği sağda yeniden çizer.
2. Sağdaki yeni grafiği görselle karşılaştır. Bir eksen sayısı okunamadıysa
   görselin altındaki kutu kırmızı olur; o sayıyı yazıp **Grafiği oluştur**'a bas.
   Yanlış bir değeri tabloda düzelt ya da görseldeki işareti sürükle.
   Gruplu sütun grafiğinde serilerin adlarını "Seriler" satırına yaz; lejantta görünür.
3. claude.ai'de açıldığında Claude da okur: seri adlarını ve eksen başlıklarını kendisi doldurur.
4. **Illustrator için kopyala** → Illustrator'da Ctrl+V (ya da SVG'yi indirip
   Dosya › Aç). Grafik gerçek ölçüsünde, düzenlenebilir vektör olarak gelir.

En üstteki "Sıradaki adım" kutusu her an ne yapman gerektiğini yazar.

En iyi sonuç için grafiğin kendi görselini (PNG ya da kaliteli JPG) ver; ekran
görüntüsü ya da çok sıkıştırılmış, bulanık görsellerde bazı sayılar okunamayabilir.
Üst üste yığılmış sütunlar ve birden çok çizgi serisi henüz desteklenmiyor.

## Illustrator scripti

`../illustrator-scripts/iklim-grafigi.jsx` iklim grafiklerini doğrudan Illustrator
içinde, CMYK renklerle çizer (sütun ve çizgi grafikleri için "Illustrator için
kopyala"yı kullan). Araçta **Script için veri kopyala**'ya bas,
Illustrator'da Dosya › Komut Dosyaları › Diğer Komut Dosyası… ile scripti aç,
"Veri" sekmesine yapıştır ve **Grafiği çiz**'e bas.
