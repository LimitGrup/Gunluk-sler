# Görsel Çizici

Ders kitabındaki basit çizimlerin görselini verirsiniz; uygulama aynısını
**düzenlenebilir vektör** olarak yeniden çizer ve Illustrator'a aktarır.
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
4. **Illustrator'a aktar** ilk kullanımda "Adobe Illustrator'ı denetlemek istiyor" diye sorar: **İzin Ver**.

## Kullanım

Pencerenin solunda iki bölüm vardır: **Görselden çizim** ve **Dilsiz harita**.
Sağdaki **Çıktı ayarları** ikisinde de geçerlidir.

1. **Görselden çizim**'de görseli verin: **Ekrandan kırp** (soruyu ekranda seçersiniz),
   **Dosyadan aç**, **Panodan yapıştır** ya da görsel dosyasını pencereye bırakın.
   Çizim kendiliğinden başlar.
2. **Kaynak görsel** ile **Vektör çizim** önizlemelerini yan yana karşılaştırın.
3. Çizimi Illustrator'a alın (alttaki çubuk):
   - **Illustrator'a aktar**: açık belgeye düzenlenebilir çizim olarak yapıştırır;
     açık belge yoksa çizimi yeni belge olarak açar.
   - **Kopyala (vektör)**: sonra Illustrator'da **Cmd+V** — düzenlenebilir çizim olarak gelir.
   - **Kaydet**: PDF ya da SVG. İkisi de Illustrator'da **Dosya › Aç** ile düzenlenebilir açılır.

   Not: Dosyayı Illustrator'a sürüklemeyin ya da "Yerleştir" ile koymayın; Illustrator onu
   bağlı resim olarak koyar ve düzenlenemez.

**Çıktı ayarları** çizime hemen uygulanır, görseli yeniden çizmeye gerek yoktur:

| Ayar | Ne yapar |
|---|---|
| Yazı tipi | Tanınan yazıların yazı tipi (ör. Helvetica Neue) |
| Punto | Yazıların ortalama boyu; çizim buna göre ölçeklenir |
| Kalınlık | Bütün çizgilerin kalınlığı (görseldeki gibi: değiştirmez) |
| Renk | Çizgi ve yazıları tek renge çevirir (Görseldeki renkler: değiştirmez) |
| Genişlik | Çizimin mm cinsinden genişliği (otomatik: puntoya göre) |

## Dilsiz harita

Soldan **Dilsiz harita**'yı seçin; dünya ya da Türkiye haritası oluşturulur (Natural Earth verisi).
Ayarları değiştirip **Haritayı oluştur**'a basın, sonra **Illustrator'a aktar**:

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
