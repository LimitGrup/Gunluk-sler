# FINALE DOĞRU KURS — AYT DENEME 1A · Baskı Öncesi Kontrol

Bu klasör, `FINALE DOGRU KURS AYT DENEME 1A.pdf` kitapçığının baskı öncesi
akademik çözüm ve redaksiyon kontrolünün çıktılarını içerir.

## Nihai çıktı

**`DENEME_SINAVI_BASKI_ONCESI_KONTROL_RAPORU.pdf`** — 33 sayfa, Türkçe, tablo
başlıkları sayfa geçişlerinde tekrar eden, sayfa numaralı rapor.

## Sonuç özeti

| Kontrol alanı | Sonuç |
|---|---:|
| Toplam soru | 166 |
| Bağımsız çözülen soru (2 geçiş) | 166 / 166 |
| Anahtarla uyumlu | 164 |
| **Kesin cevap anahtarı hatası** | **2** |
| Hatalı / tartışmalı soru | 0 |
| Doğrulanmış redaksiyon bulgusu | 97 (9 YÜKSEK, 57 ORTA, 31 DÜŞÜK) |
| Elenen yanlış pozitif | 161 / 249 |
| TDK ile doğrulanan yazım hatası | 0 — TDK erişimi engelli |
| TDK doğrulaması bekleyen madde | 12 |

**Baskı kararı: 🔴 BASKIYA UYGUN DEĞİL** — engel, iki sorudaki cevap anahtarı
hatasıdır:

- Türk Dili ve Edebiyatı-Sosyal Bilimler-1, **soru 3**: anahtar `D` → doğru `A`
- Türk Dili ve Edebiyatı-Sosyal Bilimler-1, **soru 4**: anahtar `C` → doğru `B`

Bu iki harf düzeltildikten ve YÜKSEK önemli 9 redaksiyon maddesi giderildikten
sonra kitapçık "düzeltme sonrası baskıya uygun" duruma gelir.

## Yöntem

Ayrı bir cevap anahtarı PDF'si verilmemiştir; anahtar kitapçığın içine 7,2 punto
magenta (`#EC008C`) metin olarak gömülüdür. Bağımsızlığı korumak için bu katman,
çözümde kullanılan tüm materyalden (metin ve 260 dpi soru görselleri) beyaz
dikdörtgenlerle silinmiştir (288 alan). Anahtar yalnızca bağımsız cevaplar
kaydedildikten sonra karşılaştırmada kullanılmıştır.

1. **Bağımsız çözüm** — 166 soru × 2 geçiş (farklı gruplama, farklı yöntem).
2. **Karşılaştırma** — anahtarla eşleştirme; 12 soru ikinci incelemeye alındı.
3. **Kör yeniden çözüm** — her tartışmalı soru için anahtardan ve önceki
   çözümlerden habersiz 2 çözüm, ardından hakem kararı.
4. **Redaksiyon** — 40 sayfanın tamamı görsel üzerinden tarandı; 249 ham bulgu
   birebir alıntı denetimiyle adversaryal olarak doğrulandı.
5. **Deterministik kontroller** — seçenek harfi bütünlüğü, numaralandırma,
   seçenek/soru tekrarı, Unicode tutarlılığı betiklerle denetlendi.

## TDK notu

Görev tanımı, yazım kararlarında yalnızca <https://sozluk.gov.tr> kullanılmasını
şart koşar. Bu ortamda adrese erişim ağ çıkış politikası tarafından engellendiği
için (`CONNECT tunnel failed, 403`) **hiçbir kelime hakkında kesin yazım hükmü
verilmemiştir**. 12 yazım maddesi raporda `KONTROL BEKLİYOR` olarak
işaretlenmiştir ve baskı kararında "kesin yazım hatası" olarak sayılmamıştır.

## Klasör içeriği

- `veri/` — soru envanteri, çıkarılan cevap anahtarı, çözüm ve doğrulama
  sonuçları, deterministik bulgular, insan denetimli düzeltmeler (`overrides.json`).
- `betikler/` — PDF çıkarımı, görsel kırpma, deterministik kontroller ve rapor
  üretimi (WeasyPrint) betikleri.
