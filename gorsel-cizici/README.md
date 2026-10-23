# Görsel Çizici

Ders kitabındaki basit çizimlerin görselini verirsiniz; uygulama aynısını
**düzenlenebilir vektör** olarak yeniden çizer ve Illustrator'a aktarır.
İnternet ya da API anahtarı gerekmez, her şey bilgisayarınızda çalışır.

- **Grafikler**: sütun, çizgi, iklim grafikleri; renk geçişli (degrade) sütunlar; veri çizgisi
  tek kırık çizgi, veri noktaları daire; kesikli ızgara çizgileri
- **Koordinat ızgaraları**: ızgara çizgileri uçtan uca kesintisiz, gri alan tek parça, noktalar ve
  oklar; silik doku zemini (eş yükselti deseni gibi) atılır
- **Şemalar**: kutular (köşesi yuvarlak olanlar dahil), bağlantı çizgileri, Venn şeması (iki elips)
- **Krokiler**: sokak/yapı adası krokileri, çerçeveli paneller, ölçek çubukları, eş yükselti kareleri
- **Şekiller**: güneş/ufuk çizimleri, yaylar, çemberler, oklar, kesikli çizgiler, bir kenarı kavisli
  şekiller (düz kenar + yay)
- **Haritalar**: görseldeki haritayı çizer; ayrıca **dilsiz dünya ve Türkiye haritası** oluşturur
- **Yazılar**: Mac'in kendi yazı tanımasıyla düzenlenebilir yazı olur
  (tanınamazsa harf şekli olarak çizilir)

Çıktıda düz çizgiler gerçek doğru, yuvarlak şekiller gerçek çember/elips/yay,
dikdörtgenler gerçek dikdörtgen olur; renkler ve kalınlıklar görseldeki gibidir.
Her şekil tek nesnedir: dolgusu ve konturu birlikte (ayrıca üstüne çizilmiş kenar çizgisi
olmaz). Görseldeki gölgeler şekle katılır, ayrı çizilmez. Katmanlar ayrıdır: Dolgular,
Çizgiler, Üstteki şekiller, Yazılar.

Çizim bir tasarımcının çizeceği gibi kurulur: köşesine kare oturan blok tam dikdörtgen olur
ve kare üstüne konur; benzer kutular aynı boyut ve hizaya, yakın renkler ve kalınlıklar tek
renge ve kalınlığa getirilir; aynı simge (güneş, veri noktası) her yerde aynı boyda ve konturda
çizilir; çerçeveli panelin çerçevesi üstteki şekillerin de üstünde kalır.
Ekran görüntüsündeki renkli kenarlı (ClearType) yazılar önce sadeleştirilir.

## İndirme

Tek tıkla indirin (GitHub hesabı gerekmez):

- **Mac – Apple çipli (M1, M2, M3, M4):**
  https://github.com/LimitGrup/Gunluk-sler/releases/download/gorsel-cizici/GorselCizici-mac-apple-silicon.dmg
- **Mac – Intel:**
  https://github.com/LimitGrup/Gunluk-sler/releases/download/gorsel-cizici/GorselCizici-mac-intel.dmg
- **Windows:**
  https://github.com/LimitGrup/Gunluk-sler/releases/download/gorsel-cizici/GorselCizici-windows.zip

(Hangisi olduğunu  › Bu Mac Hakkında'da "Çip" ya da "İşlemci" satırı söyler.)

Chrome "Tehlikeli indirme işlemi engellendi" diyebilir: uygulama Apple'a parayla kayıtlı
(imzalı) olmadığı için böyle der, dosyada sorun yoktur. İndirme balonundaki **›** okuna
basıp **"Yine de indir"**i seçin ya da Safari ile indirin.

## Mac'te ilk açılış

1. **GorselCizici-….dmg** dosyasını açın, **GorselCizici**'yi yanındaki **Applications
   (Uygulamalar)** klasörüne sürükleyin.
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
   - **Yazıları atla, yalnız şekilleri çiz** seçilirse yazılar hiç çizilmez; yazının
     altındaki ya da yanındaki çizimler yine çizilir.
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

Soldan **Dilsiz harita**'yı seçin; dünya ya da Türkiye haritası sıfırdan, temiz vektör olarak
oluşturulur (Natural Earth verisi, görsel gerekmez). Ayarları seçip **Haritayı oluştur**'a basın,
önizlemede kontrol edin, sonra **Illustrator'a aktar**:

- **İzdüşüm**: Miller (ders kitaplarındaki gibi), eşdikdörtgen, Mercator, Robinson
- **Orta boylam**: haritanın ortasındaki boylam
- **Ülke / il sınırları**, Türkiye için **komşu ülkeler**
- **Meridyenler / Paraleller**: `0, 45, 90, 135` gibi tek tek ya da `her 30` gibi aralıkla
  (batı ve güney için eksi değer ya da `30B`, `20G` yazın)
- **Noktalar**: her satıra `ad; boylam; enlem`, ör. `K; -14; 46`
- **Kara rengi / Deniz rengi**: düğmeye basıp renk seçin (deniz için iptal: renksiz)

Görselden çizim bölümüne dilsiz harita üstüne işaretleme yapılmış bir görsel verirseniz
uygulama haritayı tanır: haritayı bu temiz veriden çizer, yalnız görseldeki işaretlemeleri
(nokta, çizgi, harf) üstüne ekler. Tanıdığında durum satırında "Dünya haritası tanındı" yazar.

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
