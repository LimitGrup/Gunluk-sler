# Görsel Çizici

Ders kitabındaki basit çizimlerin görselini verirsiniz; uygulama aynısını
**düzenlenebilir vektör** olarak yeniden çizer ve Illustrator'a gönderir.
İnternet ya da API anahtarı gerekmez, her şey bilgisayarınızda çalışır.

- **Grafikler**: sütun, çizgi, iklim grafikleri; renk geçişli (degrade) sütunlar
- **Şekiller**: güneş/ufuk çizimleri, yaylar, çemberler, oklar, kesikli çizgiler
- **Haritalar**: görseldeki haritayı çizer; ayrıca **dilsiz dünya ve Türkiye haritası** oluşturur
- **Yazılar**: Mac'in kendi yazı tanımasıyla düzenlenebilir yazı olur
  (tanınamazsa harf şekli olarak çizilir)

Çıktıda düz çizgiler gerçek doğru, yuvarlak şekiller gerçek çember/yay,
dikdörtgenler gerçek dikdörtgen olur; renkler ve kalınlıklar görseldeki gibidir.
Katmanlar ayrıdır: Dolgular, Çizgiler, Üstteki şekiller, Yazılar.

## İndirme

1. GitHub'da bu depoda **Actions** sekmesine girin.
2. Soldan **Görsel Çizici uygulaması**'nı seçin, en üstteki (yeşil tikli) çalıştırmaya tıklayın.
3. Sayfanın altındaki **Artifacts** bölümünden indirin:
   - `GorselCizici-mac-apple-silicon` → M1, M2, M3, M4 işlemcili Mac'ler
   - `GorselCizici-mac-intel` → Intel işlemcili Mac'ler
   - `GorselCizici-windows` → Windows

   (Hangisi olduğunu  › Bu Mac Hakkında'da "Çip" ya da "İşlemci" satırı söyler.)

## Mac'te ilk açılış

1. İndirilen zip'i açın, **GorselCizici.app**'i **Uygulamalar** klasörüne taşıyın.
2. Uygulama Apple'a kayıtlı olmadığı için ilk açılışta uyarı çıkar:
   **Sistem Ayarları › Gizlilik ve Güvenlik**'te en altta **"Yine de Aç"**'a basın.
   "Hasarlı" derse Terminal'de bir kez şunu çalıştırın:

   ```
   xattr -cr /Applications/GorselCizici.app
   ```
3. **Ekrandan kırp** ilk kullanımda ekran kaydı izni ister:
   Sistem Ayarları › Gizlilik ve Güvenlik › **Ekran ve Sistem Ses Kaydı** › GorselCizici'yi açın.
4. **Illustrator'a gönder** ilk kullanımda "Adobe Illustrator'ı denetlemek istiyor" diye sorar: **İzin Ver**.

## Kullanım

1. Görseli verin: **Ekrandan kırp** (soruyu ekranda seçersiniz), **Görsel aç**,
   **Yapıştır** ya da görseli pencereye sürükleyin. Çizim kendiliğinden başlar.
2. Sağdaki önizlemeyi görselle karşılaştırın.
3. Çizimi Illustrator'a alın:
   - **Buradan tutup Illustrator'a sürükleyin** alanından belgeye sürükleyin, ya da
   - **Illustrator'a gönder**: açık belgenin ortasına düzenlenebilir grup olarak ekler, ya da
   - **SVG kaydet** / **Kopyala**.

Üstteki ayarlar çıktıya uygulanır, görseli yeniden çizmeye gerek yoktur:

| Ayar | Ne yapar |
|---|---|
| Yazı tipi | Tanınan yazıların yazı tipi (ör. Helvetica Neue) |
| Punto | Yazıların ortalama boyu; çizim buna göre ölçeklenir |
| Renk | Çizgi ve yazıları tek renge çevirir (Görseldeki renkler: değiştirmez) |
| Kontur (pt) | Bütün çizgilerin kalınlığı (görseldeki gibi: değiştirmez) |
| Genişlik | Çizimin mm cinsinden genişliği (otomatik: puntoya göre) |

## Dilsiz harita

**Dilsiz harita** sekmesinde dünya ya da Türkiye haritası oluşturulur (Natural Earth verisi):

- **İzdüşüm**: Miller (ders kitaplarındaki gibi), eşdikdörtgen, Mercator, Robinson
- **Orta boylam**: haritanın ortasındaki boylam
- **Ülke / il sınırları**, Türkiye için **komşu ülkeler**
- **Meridyenler / Paraleller**: `0, 45, 90, 135` gibi tek tek ya da `her 30` gibi aralıkla
  (batı ve güney için eksi değer ya da `30B`, `20G` yazın)
- **Noktalar**: her satıra `ad; boylam; enlem`, ör. `K; -14; 46`

## İpuçları

- En iyi sonuç için yalnız çizimi kırpın (soru metnini dahil etmeyin).
- Görsel ne kadar netse çizim o kadar temiz olur; çok küçük ya da bulanık görsellerde
  ince ayrıntılar kaybolabilir.
- Yazı tanıma Mac'te macOS'un kendi özelliğidir ve ı, ş, ğ gibi harfleri düşürür
  ("Batı" yerine "Bati"). Uygulama ders kitaplarında sık geçen kelimeleri (yönler, aylar,
  iklim ve harita terimleri, 81 il, ülke adları) kendisi düzeltir; listede olmayan bir
  kelimeyi Illustrator'da düzeltmeniz gerekebilir.

## Kaynaktan çalıştırma

Mac'te Python 3 varsa **Baslat.command** dosyasına çift tıklayın (ilk seferde gerekli
paketleri kurar). Ya da Terminal'de:

```
python3 -m venv venv && venv/bin/pip install -r requirements.txt
venv/bin/python GorselCizici.py
```

Arayüzsüz çevirme: `python GorselCizici.py --svg gorsel.png cizim.svg`
