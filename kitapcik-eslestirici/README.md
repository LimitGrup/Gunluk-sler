# Kitapçık Eşleştirici (v2.29)

macOS uygulaması (`Kitapcik Eslestirici.app`). İki iş yapar:

| Düğme | Ne yapar | Çıktı |
|---|---|---|
| **EŞLEŞTİR** | A kitapçığındaki her sorunun B'de kaçıncı soru olduğunu bulur, kazanım tablosunu doldurur. | `kazanim_tablosu.xlsx` |
| **A–B KONTROL** *(yeni)* | B kitapçığını A'ya göre denetler: A'daki her soru B'de var mı, aynı mı, numaralar ve metne bağlı gruplar düzgün mü? | `kitapcik_kontrol_raporu.xlsx` + sorunlu soruların A/B görüntüleri (PDF) |

## EŞLEŞTİR'deki düzeltmeler (v2.21, v2.27–v2.29)

EŞLEŞTİR'in eşleştirme mantığı aynen duruyor; üstüne iki düzeltme eklendi:

- **Ders adları:** Lise/Ortaokul (otomatik yapı) seçeneğinde test ve ders adı artık testin ilk
  sayfasındaki başlıktan okunuyor ("SÖZEL BÖLÜM - TÜRKÇE" → TÜRKÇE, "TÜRKÇE TESTİ" → TÜRKÇE).
  Önceden başlık satır sırasında geride kaldığında ya da önceki testin "… TESTİ BİTTİ" yazısı
  okunduğunda ad kayıyordu (ör. Türkçe soruları "Bölüm 1", İnkılap soruları "TÜRKÇE"). TYT/AYT'de
  sabit adlar kullanıldığı için değişiklik yok.
- **İçerik doğrulaması:** EŞLEŞTİR bittikten sonra her eşleşme A–B KONTROL'ün içerik
  karşılaştırmasıyla doğrulanır. Yalnızca kesin yanlış eşler düzeltilir: A sorusunun metni B'deki
  başka bir soruyla birebir (≥ %98) aynıyken EŞLEŞTİR'in seçtiği sorunun metni belirgin farklıysa
  (< %90). Her düzeltme Kontrol sayfasına ve günlüğe "DÜZELTİLDİ: … A-9 → B-4 (ilk eşleştirme B-3
  demişti …)" diye yazılır. Doğruluğu kanıtlanan eşlerin yersiz "DÜŞÜK BENZERLİK" uyarısı kalkar.
  Doğrulama bir nedenle yapılamazsa EŞLEŞTİR sonucu aynen kalır.
- **Cevap harfi (v2.27):** Cevap önce eskisi gibi soru bölümünde aranır; bulunduğu her durumda
  sonuç aynıdır. Bulunamazsa yedek olarak konuma bakılır: aynı sayfada, soru numarasının sol
  hizasında, numaranın altında ve bir sonraki sorudan önce duran renkli A–E harfi. Tam genişlik
  sayfalarda (ör. 8. sınıf MOBESE sayısal) numara satırı sağ yarıya düşünce numaranın altındaki
  cevap harfi okunmuyordu: A'da 36/40, B'de 39/40 → şimdi 40/40 ve 40/40, eşleşen 40 çiftin
  hepsinde A ile B'nin cevabı aynı.
- **Cevap harfi konumdan (v2.29):** Soru numarasının hizasında (sol boşlukta, numaranın altında,
  bir sonraki sorudan önce) renkli A–E harfi varsa cevap odur; eski sıra kuralı yalnızca böyle bir
  harf yoksa kullanılır. Eski kural sorunun içindeki ilk renkli harfi alıyordu: 8. sınıf Limit
  sayısal Matematik A-7'nin şeklindeki kırmızı "B" etiketi cevap sanılıyordu (doğrusu pembe "A";
  B kitapçığında aynı şekil olduğu için A–B cevap kıyası da yakalayamıyordu). Elimizdeki 5 cevaplı
  gerçek çiftte (376 soru, iki kitapçıkta 752 cevap) iki kural yalnızca 4 cevapta ayrışıyor ve 4'ünde de
  konumdan okunan harf doğru.
- **Başka sayfadan okunan cevap (v2.28):** Aynı nedenle soru bölümü bir sonraki sayfaya taşınca
  eski kural o sayfadaki başka bir sorunun cevabını alabiliyordu (7. sınıf MOBESE sayısal Fen
  A-16: C okunuyordu, doğrusu B). Cevap soru numarasından başka bir sayfadan okunduysa ve
  numaranın kendi sayfasında hizasında renkli harf varsa o kullanılır. Örnek ve gerçek
  kitapçıklardaki 536 soruda iki kural yalnızca bu soruda ayrışıyor. Cevaplar eşleştirmede de
  ipucu olduğu için düzeltme, iki yanlış eşi de kendiliğinden düzeltti.

Gerçek kitapçıklarda sonuç:

| Çift | EŞLEŞTİR v2.18 | v2.21 |
|---|---|---|
| 8. sınıf Sözel 1A ↔ 1B (50 soru) | 48/50 doğru (İngilizce 9–10 yer değiştirmiş) | 50/50 |
| 8. sınıf Sayısal 1A ↔ 1B (40 soru) | 38/40 doğru (Matematik 17–18 yer değiştirmiş) | 40/40 |
| TYT Deneme 1 A ↔ B (125 soru) | 125/125 | 125/125 |
| AYT Deneme 1 A ↔ B (166 soru) | 166/166 | 166/166 |
| 10. sınıf Deneme 2 A ↔ B (100 soru) | 100/100 | 100/100 |
| 11. sınıf Deneme 2 A ↔ B (100 soru) | 98/100 | 100/100 |
| 5. sınıf Deneme 1 A ↔ B (75 soru) | 69/75 | 75/75 |
| 7. sınıf Deneme 1 A ↔ B (90 soru) | 85/90 (ders adı "Bölüm 1") | 90/90 |
| 8. sınıf MOBESE Sayısal 1 A ↔ B (40 soru, cevaplı) | 38/40, cevap A 36/40 · B 39/40 | 40/40, cevap 40/40 · 40/40 |
| 7. sınıf MOBESE Sayısal 1 A ↔ B (40 soru, cevaplı) | 34/40, cevap A 36/40 (1 yanlış) · B 36/40 | 40/40, cevap 40/40 · 40/40 |
| AYT LEK 1. Deneme A ↔ B (166 soru, cevaplı) | 166/166, cevap 166/166 · 166/166 | 166/166, cevap 166/166 · 166/166 |
| 7. sınıf Limit Deneme 1 A ↔ B (90 soru, cevaplı) | 90/90, cevap 85/90 · 86/90; Din soruları "SOSYAL BİLGİLER", Türkçe "Bölüm 1" | 90/90, cevap 90/90 · 90/90, 6 branş doğru adla |
| 8. sınıf Limit Sayısal 1 A ↔ B (40 soru, cevaplı) | 38/40, cevap 39/40 (1 yanlış) · 38/40; Matematik "Bölüm 1" | 40/40, cevap 40/40 · 40/40 |
| 7. sınıf Limit Sözel 1 A ↔ B (50 soru, cevaplı) | 48/50, cevap 47/50 · 48/50; Din soruları "SOSYAL BİLGİLER" | 50/50, cevap 50/50 · 50/50, 4 branş doğru adla |
| Finale Doğru Kurs TYT Deneme 1 A ↔ B (125 soru, cevaplı) | 125/125, cevap 125/125 · 125/125 | 125/125, cevap 125/125 · 125/125 |

TYT ya da AYT seçili olup dosyalar o düzene uymuyorsa (ör. 10. sınıf kitapçığı varsayılan TYT
seçiliyken çalıştırılırsa) önce diğer sınav türü denenir; o da uymazsa yapı kitapçığın kendisinden
çıkarılır (Lise/Ortaokul seçeneği gibi) ve günlükte "DİKKAT" ile belirtilir.

Örnek kitapçıklarda ana tablo (B numaraları) v2.18 ile aynıdır (`testler/eslestir_sina.py`).
Değişen tek yer, doğrulanan eşlerin Kontrol sayfasındaki benzerlik yüzdesidir.

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
   - Metin ve şıklar birebir aynı mı? Fark kelime düzeyinde gösterilir. Baskıda görünmeyen
     farklar sayılmaz: boşluklar, satır sonunda bölünen kelimeler, tirenin kodu ("-", yumuşak
     tire, Unicode tire), "ü"nün tek harf ya da "u"+"¨" yazılması, ﬁ gibi bitişik harfler.
     Görünen noktalama farkı (ör. virgül yalnızca A'da) sarı UYARI, kelime/harf farkı kırmızı
     HATA olur.
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
A B C D şıklarıyla) ve iki sütun bir arada olsa da her satır kendi sorusunda kalır. Numaranın
sağında ve onun hizasında duran satır, üst üste kesir (315/2) ya da büyük karakter yüzünden
numaranın biraz üstünden başlasa da o sorunun ilk satırı sayılır.

### Rapor

- **Özet:** Her kontrol için TEMİZ / HATA / KONTROL ET. Hatalar kırmızı zemin üzerinde beyaz,
  açıklamaları koyu kırmızı yazılır; uyarılar sarıdır. Altında **"NEREYE BAKMALI?"** listesi:
  her sorun sıra numarası, testi, soru numarası (A-7 / B-2), **A ve B sayfası** ve ne bulunduğuyla.
  Liste kitapçıktaki sıraya göredir (önce hatalar, sonra uyarılar).
- **Sorun kartları PDF'i** (`kitapcik_kontrol_raporu_sorunlar.pdf`): Her sorun için bir sayfa.
  Üstte ne bulunduğu ve sayfası, altta sorunun **A ve B kitapçığındaki görüntüsü yan yana**:
  - farklı kelimeler sarıyla boyanır;
  - farklı şekil kırmızı çerçeveyle, en farklı küçük bölgesi ayrıca işaretlenir;
  - açık kalan cevap harfi çerçevelenir;
  - bulunamayan sorunun yerine önceki ve sonraki soru gösterilir.

  İlk sayfa tıklanır içindekiler listesidir. Böylece her uyarı PDF'leri açıp aramadan,
  birkaç saniyede doğrulanır. Sorun yoksa bu dosya oluşmaz; önceki kontrolden kalan eski dosya
  da silinir.
- **Sorunlar:** Her sorun için sıra no, önem, kitapçık, test, ders, soru, sayfa ve açıklama.
- **Soru Eşleşmesi:** A no → B no, metin %, şekil/resim durumu, cevaplar ve durum.
- **Metne Bağlı Gruplar:** A grubu → B karşılığı, parça benzerliği ve durum.
- **İşaretli PDF:** Sorunlu yerler A ve B PDF'lerinin kopyasında çerçevelenir (kırmızı = hata,
  turuncu = elle bakılacak), farklı kelimeler vurgulanır ve not olarak açıklama eklenir. Sorun
  yoksa bu PDF oluşmaz.

Uygulamada kontrol bitince "Excel ve görüntüler açılsın mı?" sorusuna Evet denirse ikisi birlikte
açılır. Günlükte de her sorun sayfasıyla yazılır.

### Farklı şablonlar

Uygulama belirli bir kitapçığa göre ayarlanmadı; genel kurallarla çalışır:
- Soru numaraları sütun kenarına hizalı "12." biçiminde aranır, sıraları test test izlenir.
- Testler numaranın 1'e dönmesinden, adları sayfa üstündeki başlıktan ("… TESTİ",
  "… BÖLÜM - …"), ders dağılımı "Bu testte sırasıyla, Tarih (1-10), …" yönergesinden okunur.
- Sayfa düzeni (tek sütun, iki sütun, ikisinin karışımı) her sayfada soru numaralarına göre
  ayrıca çözülür.
- Sayfa üst/alt bilgileri sabit metinden değil, sayfalarda aynı yerde tekrar etmelerinden tanınır.

10. ve 11. sınıf kitapçıkları bu kurallarla ilk denemede tanındı; yalnızca iki genel kusur
düzeltildi (alt satıra kayan şık parçasının soru numarası sanılması, yakın iki tablonun şekil
kutusunda birleşmesi). 5. ve 7. sınıfta da 75/75 ve 90/90 soru ilk denemede bulundu. Düzeltilen
genel kusurlar: renkli içerik metninin ("81 ilde") soru kodu sanılması; kırpılmış vektör
resimlerin görünmeyen parçalarının şekil sayılması (artık her çizim parçası PDF'teki kırpma
alanıyla kesiliyor); ortalı sayfa numarasının ("1" ile "12") sayfa bilgisi olarak tanınmaması;
kalıp sayfadan kalıp üstü örtülmüş eski başlığın test adı sanılması.

Şekil kararı: şekil sayısı ve boyutları A ile B'de tutuyorsa her şekil görüntü olarak kıyaslanır
(fark varsa HATA). Tutmuyorsa (aynı şekiller satır aralığı yüzünden farklı birleşmiş olabilir)
sorudaki toplam şekil mürekkebi kıyaslanır; yalnızca belirgin fark varsa (%6'dan fazla) UYARI. Hiç görülmemiş bir şablonda yine de beklenmedik bir durum çıkabilir;
öyle bir çiftte rapor şüpheli bir sonuç verirse o çift gönderilip kural genelleştirilmelidir.

### Bilinen sınırlar

- PDF'te **seçilebilir metin** olmalı. Yazılar eğriye çevrilmişse (outline) ya da taranmışsa önce
  OCR gerekir.
- PDF küçültülürken ya da Distiller / "PDF olarak yazdır" ile yeniden kaydedilirken yazı
  tiplerinin harf eşlemesi kaybolabilir: görüntü doğru, metin anlamsız ("Bu testte" →
  "%X WHVWWH"). Uygulama bunu fark edip "yazılar okunamıyor" diye durur; özgün PDF
  kullanılmalıdır. Küçültmek gerekirse Acrobat'ta Dosya > Farklı Kaydet > Küçültülmüş Boyutlu
  PDF yazıları korur.
- B baskı PDF'i **sayfa sayfa** olmalı; montajlı (imposition, 2 sayfa yan yana) PDF desteklenmez.
- Bir şeklin parçaları arasındaki boşluk A ve B'de çok farklıysa "şekil sayısı farklı" uyarısı
  çıkabilir. Bu uyarılar "elle bakın" düzeyindedir.

### Gerçek kitapçıklarla deneme (8. sınıf Limit denemesi, sözel + sayısal, baskı PDF'leri)

| Çift | Soru | Sonuç | Süre |
|---|---|---|---|
| Sözel 1A ↔ 1B | 50 | 50/50 birebir eşleşme, 0 hata, 0 uyarı | ~2 sn |
| Sayısal 1A ↔ 1B | 40 | 40/40 birebir eşleşme, 0 hata, 0 uyarı | ~25 sn |
| TYT Deneme 1 A ↔ B | 125 | 125/125 birebir, 3 metin grubu aynı, 0 hata, 0 uyarı | ~35 sn |
| AYT Deneme 1 A ↔ B | 166 | 166/166 birebir, 0 hata, 0 uyarı | ~5 sn |
| 10. sınıf Deneme 2 A ↔ B | 100 | 100/100 birebir, 0 hata, 0 uyarı | ~14 sn |
| 11. sınıf Deneme 2 A ↔ B | 100 | 100/100 birebir, 0 hata, 0 uyarı | ~4 sn |
| 5. sınıf Deneme 1 A ↔ B | 75 | 75/75 birebir, 0 hata, 0 uyarı | ~16 sn |
| 7. sınıf Deneme 1 A ↔ B | 90 | 90/90 birebir, 0 hata, 0 uyarı | ~50 sn |
| 7. sınıf MOBESE Sayısal 1 A ↔ B (cevaplı) | 40 | 40/40 birebir, 2 metin grubu aynı, 0 hata (yalnız "cevaplar açık" uyarısı) | ~20 sn |
| 8. sınıf MOBESE Sayısal 1 A ↔ B (cevaplı) | 40 | 40/40 birebir, 0 hata (yalnız "cevaplar açık" uyarısı) | ~20 sn |
| AYT LEK 1. Deneme A ↔ B (cevaplı) | 166 | 166/166 birebir, 0 hata (yalnız "cevaplar açık" uyarısı) | ~60 sn |
| 7. sınıf Limit Sözel 1 A ↔ B (cevaplı) | 50 | 50/50 birebir, 4 metin grubu aynı, 0 hata | ~15 sn |
| Finale Doğru Kurs TYT Deneme 1 A ↔ B (cevaplı) | 125 | 124/125 birebir, 3 metin grubu aynı, **1 gerçek fark yakalandı** (Türkçe A-11 / B-10: V. deyim A'da "kolları sıvamak", B'de "kol gezmek") | ~60 sn |

TYT'de B kitapçığı metne bağlı grubun sorularını ters sırayla diziyor (A 35-36 → B 38-37).
Bu yayınevi düzeni hata sayılmaz; soruların yan yana ve aynı metnin altında olması denetlenir.
"16-20. soruları Din Kültürü … cevaplayacaktır" gibi seçmeli ders yönergeleri metin grubu
sayılmaz.

TYT B'nin bir kopyasına iki hata eklendi (Sosyal'de bir soru numarası kaydırıldı, bir metin
grubunun parçasından bir kelime silindi); ikisi de yakalandı.

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
python3 testler/cevap_sina.py    "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" /tmp/ornek  # EŞLEŞTİR: cevap harfi ve B numarası gerçek değerle aynı mı
python3 testler/kesir_sina.py    "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" /tmp/kesir  # ilk satır numaranın üstünden başlıyor: kaybolmamalı
python3 testler/tire_sina.py     "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" /tmp/tire   # A ve B'de farklı tire karakteri: sahte uyarı olmamalı
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
